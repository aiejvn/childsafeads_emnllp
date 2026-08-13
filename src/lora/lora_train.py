"""Train a LoRA-adapted BERT-family encoder (roBERTa/legal-bert) with three heads
(st1/st2/st3) on the ChildSafeAds task.

Usage (run from the repo root):
    python src/lora/lora_train.py public_data_dev/train.jsonl public_data_dev/dev.jsonl \\
        --model FacebookAI/roberta-base --epochs 5 --batch-size 16 --output-dir runs/lora_roberta
    python src/lora/lora_train.py public_data_dev/train.jsonl public_data_dev/dev.jsonl \\
        --sample-size 16 --epochs 1 --batch-size 4 --output-dir runs/lora_smoke  # smoke test

Saves the best-dev-macro-F1 adapter+heads to <output-dir>/best and the final epoch's
to <output-dir>/last (both loadable with lora_predict.py). <output-dir>/best also gets
that epoch's dev submission.jsonl and submission_error.jsonl (see baseline_gpt.py).
"""
import argparse
import os
import random
import sys
from datetime import datetime

import torch
import wandb
from torch.utils.data import DataLoader, WeightedRandomSampler
from tqdm import tqdm
from transformers import AutoTokenizer, get_linear_schedule_with_warmup

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # so `import lora` resolves src/lora as a package
from common.dialog_flow import df_pre_context  # noqa: E402
from common.predict_utils import save_thresholds, tune_and_decode, write_submission  # noqa: E402
from common.train_utils import compute_pos_weight, to_device  # noqa: E402
from lora import CONTEXT_CHOICES, ST1_LABELS, ST2_LABELS, ST3_LABELS, evaluate, setup_logging  # noqa: E402
from lora.lora_data import Collator, ClassificationDataset, load_split  # noqa: E402
from lora.lora_model import build_peft_model  # noqa: E402


def flatten_label_f1(per_label_f1: dict) -> dict:
    """Merges the st1/st2/st3 per-label F1 maps `evaluate()` returns into one lookup
    keyed by label name (st3_family is derived from st3, not a label an instance
    carries directly, so it's left out)."""
    merged = {}
    for tier in ("st1", "st2", "st3"):
        merged.update(per_label_f1[tier])
    return merged


def instance_difficulty(instance: dict, label_f1: dict) -> float:
    """Mean (1 - dev F1) over an instance's gold labels: how poorly the model is
    currently doing, on last epoch's dev pass, on the labels this instance carries."""
    gold = instance["labels"]
    labels = [gold["st1"]] + gold["st2"] + gold["st3"]
    return sum(1.0 - label_f1[label] for label in labels) / len(labels)


def curriculum_sampler(train_instances: list, label_f1: dict, epoch: int, total_epochs: int,
                        floor: float) -> WeightedRandomSampler:
    """Self-paced sampler: instances whose gold labels the model is currently weak on
    (low dev F1 from the previous epoch) are downweighted and progressively
    reintroduced at full weight as `epoch` advances toward `total_epochs` -- so the
    curriculum tracks the model's own per-label weak spots each epoch, rather than a
    fixed a-priori difficulty order."""
    pace = epoch / max(1, total_epochs - 1)  # 0.0 at epoch 0 -> 1.0 at the final epoch
    weights = [
        1.0 if instance_difficulty(inst, label_f1) <= pace else floor
        for inst in train_instances
    ]
    return WeightedRandomSampler(weights, num_samples=len(train_instances), replacement=True)


#  python src/lora/lora_train.py public_data_dev/train.jsonl public_data_dev/dev.jsonl --model nlpaueb/legal-bert-base-uncased --epochs 200 --output-dir runs/lora_legalbert --no-wandb
#  bash slurm_wrapper.sh 1 src/lora/lora_train.py public_data_dev/train.jsonl public_data_dev/dev.jsonl --epochs 200 --output-dir runs/lora_legalbert --no-wandb --local --grad-accum-steps 0 --lora-r 64 --lora-alpha 128  --target-modules "query,key,value,dense" --st3-loss-weight 2 --pos-weight
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("train", help="training split, e.g. public_data_dev/train.jsonl")
    ap.add_argument("dev", help="dev split for per-epoch evaluation, e.g. public_data_dev/dev.jsonl")
    ap.add_argument("--model", default="FacebookAI/roberta-base")
    ap.add_argument(
        "--local", action="store_true",
        help="load --model from ./models/{model} instead of the HF hub (must already be downloaded there)",
    )
    ap.add_argument("--context", choices=CONTEXT_CHOICES, default="full",
                    help="which rungs of the instance the model sees. no_product_page drops the linked page "
                         "entirely (a median 38%% of full_context's tokens); st2_page keeps only its "
                         "ST2-bearing lines, see common/page_filter.py")
    ap.add_argument(
        "--df-path", default=None,
        help="path to an autoDF-generated dialog-flow JSON (e.g. emnllp-dialog-flow-dialog-flow.json) to "
        "prepend before each instance's text, so its tokens come first; omit to train without it",
    )
    ap.add_argument("--lean-prompt", action="store_true", help="render --df-path as stripped text "
                     "(943 tokens) instead of the raw editor export (4,003, of which 81%% is UUIDs, "
                     "canvas positions and CSS classes). No effect without --df-path: this path has "
                     "no system prompt to trim")
    ap.add_argument("--max-length", type=int, default=512) # 512?! seems a bit short, if this is sequence length
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--grad-accum-steps", type=int, default=1)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument(
        "--head-lr", type=float, default=None,
        help="separate LR for the randomly-initialized st1/st2/st3 heads (modules_to_save), which start from "
        "scratch unlike the LoRA adapters that nudge an already-pretrained encoder; defaults to --lr (i.e. "
        "one param group, previous behavior) when omitted",
    )
    ap.add_argument("--warmup-ratio", type=float, default=0.06)
    ap.add_argument("--lora-r", type=int, default=256)
    ap.add_argument("--lora-alpha", type=int, default=16)
    ap.add_argument("--lora-dropout", type=float, default=0.1)
    ap.add_argument("--target-modules", default="query,value", help="comma-separated module names to LoRA-adapt")
    ap.add_argument("--st2-loss-weight", type=float, default=1.0)
    ap.add_argument("--st3-loss-weight", type=float, default=1.0)
    ap.add_argument("--pos-weight", action="store_true", help="reweight st2/st3 BCE by inverse train-set frequency")
    ap.add_argument(
        "--threshold", type=float, default=0.5,
        help="fallback st2/st3 threshold for labels tune_per_label_thresholds can't tune (see common/predict_utils.py)",
    )
    ap.add_argument("--no-curriculum", action="store_true", help="disable self-paced curriculum sampling "
                     "(by default, from epoch 2 on, training instances whose gold labels scored low dev "
                     "F1 last epoch are downweighted, then progressively reintroduced at full weight as "
                     "training approaches --epochs)")
    ap.add_argument("--curriculum-floor", type=float, default=0.1, help="sampling weight given to "
                     "still-weak instances early in the curriculum, relative to a weight of 1.0 for "
                     "already-easy ones; no effect with --no-curriculum")
    ap.add_argument("--sample-size", type=int, default=None, help="sample N train and N dev instances (seeded smoke test)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--device", default=None, help="defaults to cuda if available, else cpu")
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--no-wandb", action="store_true", help="disable W&B logging")
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")

    model_path = args.model
    if args.local:
        local_path = os.path.join("models", args.model)
        if not os.path.isdir(local_path):
            raise FileNotFoundError(f"--local set but {local_path} does not exist")
        model_path = local_path

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log = setup_logging("runs", "lora_train", args.model.replace("/", "_"), timestamp)
    log.info(f"config: {vars(args)} device={device}")

    wandb.init(
        project="childsafeads-emnllp",
        name=f"lora_{args.model.replace('/', '_')}_{timestamp}",
        config=vars(args),
        mode="disabled" if args.no_wandb else "online",
    )

    train_instances = list(load_split(args.train))
    dev_instances = list(load_split(args.dev))
    if args.sample_size:
        rng = random.Random(args.seed)
        train_instances = rng.sample(train_instances, min(args.sample_size, len(train_instances)))
        dev_instances = rng.sample(dev_instances, min(args.sample_size, len(dev_instances)))
    log.info(f"train={len(train_instances)} dev={len(dev_instances)}")

    df_text = None
    if args.df_path:
        df_text = df_pre_context(args.df_path, lean=args.lean_prompt)
        form = "stripped dialog flow" if args.lean_prompt else "raw autoDF JSON"
        log.info(f"prepending {form} from {args.df_path} ({len(df_text)} chars) before each instance's text")

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    train_ds = ClassificationDataset(train_instances, tokenizer, args.context, args.max_length, df_text)
    dev_ds = ClassificationDataset(dev_instances, tokenizer, args.context, args.max_length, df_text)
    collate = Collator(tokenizer)
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, collate_fn=collate)
    dev_loader = DataLoader(dev_ds, batch_size=args.batch_size, shuffle=False, collate_fn=collate)

    model = build_peft_model(
        model_path, len(ST1_LABELS), len(ST2_LABELS), len(ST3_LABELS),
        lora_r=args.lora_r, lora_alpha=args.lora_alpha, lora_dropout=args.lora_dropout,
        target_modules=args.target_modules.split(","),
    ).to(device)
    model.print_trainable_parameters()

    st2_pos_weight = compute_pos_weight(train_instances, "st2", ST2_LABELS).to(device) if args.pos_weight else None
    st3_pos_weight = compute_pos_weight(train_instances, "st3", ST3_LABELS).to(device) if args.pos_weight else None

    trainable = [p for p in model.parameters() if p.requires_grad]
    head_lr = args.head_lr if args.head_lr is not None else args.lr
    if head_lr == args.lr:
        optimizer = torch.optim.AdamW(trainable, lr=args.lr)
    else:
        # st1_head/st2_head/st3_head (PEFT's modules_to_save) start from random init, unlike the LoRA
        # adapters which nudge an already-pretrained encoder -- named-parameter split lets them use a
        # different (usually higher) LR. "head" only appears in these three modules' qualified names
        # (verified against a built model: encoder LoRA params are named *.lora_A/lora_B.default.weight,
        # heads are *.st{1,2,3}_head.modules_to_save.default.{weight,bias}), never in encoder LoRA names.
        head_params = [p for n, p in model.named_parameters() if p.requires_grad and "head" in n]
        lora_params = [p for n, p in model.named_parameters() if p.requires_grad and "head" not in n]
        optimizer = torch.optim.AdamW([
            {"params": lora_params, "lr": args.lr},
            {"params": head_params, "lr": head_lr},
        ])
        log.info(f"using separate LRs: lora={args.lr} head={head_lr} ({len(lora_params)} lora tensors, {len(head_params)} head tensors)")
    steps_per_epoch = -(-len(train_loader) // args.grad_accum_steps)  # ceil div
    total_steps = steps_per_epoch * args.epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=int(args.warmup_ratio * total_steps), num_training_steps=total_steps
    )

    best_f1 = -1.0
    label_f1 = None  # populated after the first dev pass; drives the curriculum sampler from epoch 2 on
    os.makedirs(args.output_dir, exist_ok=True)
    for epoch in range(args.epochs):
        if label_f1 is not None and not args.no_curriculum:
            sampler = curriculum_sampler(train_instances, label_f1, epoch, args.epochs, args.curriculum_floor)
            train_loader = DataLoader(train_ds, batch_size=args.batch_size, sampler=sampler, collate_fn=collate)

        model.train()
        running_loss = 0.0
        for step, batch in enumerate(tqdm(train_loader, desc=f"epoch {epoch + 1}/{args.epochs}")):
            batch = to_device(batch, device)
            out = model(
                input_ids=batch["input_ids"], attention_mask=batch["attention_mask"],
                st1_labels=batch["st1_labels"], st2_labels=batch["st2_labels"], st3_labels=batch["st3_labels"],
                st2_loss_weight=args.st2_loss_weight, st3_loss_weight=args.st3_loss_weight,
                st2_pos_weight=st2_pos_weight, st3_pos_weight=st3_pos_weight,
            )
            loss = out["loss"] / args.grad_accum_steps
            loss.backward()
            running_loss += out["loss"].item()
            if (step + 1) % args.grad_accum_steps == 0 or step + 1 == len(train_loader):
                torch.nn.utils.clip_grad_norm_(trainable, 1.0)
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()
        train_loss = running_loss / len(train_loader)
        log.info(f"epoch {epoch + 1}: mean train loss = {train_loss:.4f}")

        model.eval()
        preds, st2_threshold, st3_threshold = tune_and_decode(
            model, dev_loader, device, dev_instances, default_threshold=args.threshold,
        )
        gold = [inst["labels"] for inst in dev_instances]
        metrics = evaluate(gold, preds)
        scalar_metrics = {k: v for k, v in metrics.items() if k != "per_label_f1"}
        log.info(f"epoch {epoch + 1} dev metrics (tuned thresholds): "
                 + ", ".join(f"{k}={v:.3f}" for k, v in scalar_metrics.items()))
        for tier, per_label in metrics["per_label_f1"].items():
            log.info(f"epoch {epoch + 1} dev {tier} per-label F1: "
                     + ", ".join(f"{label}={f1:.3f}" for label, f1 in sorted(per_label.items())))
        wandb.log({
            "epoch": epoch + 1, "train_loss": train_loss,
            **{f"dev_{k}": v for k, v in scalar_metrics.items()},
            **{f"dev_{tier}_f1/{label}": f1
               for tier, per_label in metrics["per_label_f1"].items() for label, f1 in per_label.items()},
        })
        label_f1 = flatten_label_f1(metrics["per_label_f1"])

        if metrics["mean_macro_f1"] > best_f1:
            best_f1 = metrics["mean_macro_f1"]
            best_dir = os.path.join(args.output_dir, "best")
            model.save_pretrained(best_dir)
            save_thresholds(best_dir, st2_threshold, st3_threshold)
            dev_ids = [inst["instanceID"] for inst in dev_instances]
            write_submission(
                os.path.join(best_dir, "submission.jsonl"), os.path.join(best_dir, "submission_error.jsonl"),
                dev_ids, dev_instances, preds,
            )
            log.info(f"epoch {epoch + 1}: new best mean_macro_f1={best_f1:.3f}, saved to {args.output_dir}/best")

    last_dir = os.path.join(args.output_dir, "last")
    model.save_pretrained(last_dir)
    save_thresholds(last_dir, st2_threshold, st3_threshold)
    log.info(f"saved final epoch adapter to {args.output_dir}/last (best dev mean_macro_f1={best_f1:.3f})")
    wandb.summary.update({f"final_dev_{k}": v for k, v in metrics.items()})
    wandb.summary["best_mean_macro_f1"] = best_f1
    wandb.finish()


if __name__ == "__main__":
    main()
