"""Train a LoRA-adapted causal LM (e.g. Qwen3.5-4B/2B/0.8B) generatively on the
ChildSafeAds task: given the same zero-shot prompt used for the GPT baseline
(SYSTEM_PROMPT + "SEGMENT DATA:\\n\\n{text}", src/baseline_gpt.py), the model is fine-tuned
via next-token cross-entropy to generate the gold st1/st2/st3 label as JSON matching
baseline_gpt.py's `Prediction` schema -- loss is masked to the completion tokens only.

This is the generative counterpart to lora_train.py, which LoRA-adapts encoder (BERT-family)
models via classification heads instead; use that script for roberta-base/legal-bert.

Usage (run from the repo root):
    python src/lora/lora_train_generative.py public_data_dev/train.jsonl public_data_dev/dev.jsonl \\
        --model Qwen/Qwen3.5-4B --epochs 3 --batch-size 4 --output-dir runs/lora_qwen
    python src/lora/lora_train_generative.py public_data_dev/train.jsonl public_data_dev/dev.jsonl \\
        --model Qwen/Qwen3.5-0.8B --sample-size 8 --epochs 1 --batch-size 2 \\
        --output-dir runs/lora_smoke_qwen  # smoke test

    uv run --with-requirements requirements.txt src/lora/lora_train_generative.py public_data_dev/train.jsonl public_data_dev/dev.jsonl --model Qwen/Qwen3.5-4B --epochs 3 --batch-size 4 --output-dir runs/lora_qwen

Per-epoch dev eval decodes via freeform generation, parsing the JSON completion against the
same schema (see lora_generative.py); a completion that fails to parse is regenerated up to
3 times before falling back to a default prediction.

Saves the best-dev-macro-F1 adapter to <output-dir>/best and the final epoch's to
<output-dir>/last (both loadable with lora_predict_generative.py). Pass --checkpoint-save-path
to write the best/last checkpoints elsewhere (e.g. a scratch disk) while --output-dir still
anchors the run's logs. The best checkpoint's dev submission.jsonl and submission_error.jsonl
(see baseline_gpt.py) are written alongside it.

To download a model:

hf download {author}/{model name} --local-dir ./models/{author}/{model name}
"""
import argparse
import logging
import os
import random
import sys
from datetime import datetime

import torch
from torch.utils.data import DataLoader
from tqdm import tqdm
from transformers import AutoTokenizer, get_linear_schedule_with_warmup

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # so `import lora` resolves src/lora as a package
from common.dialog_flow import df_pre_context  # noqa: E402
from common.predict_utils import log_prediction_diagnostics, write_submission  # noqa: E402
from lora import CONTEXT_CHOICES, SFT_TAXONOMY, SYSTEM_PROMPT, evaluate, load_split, setup_logging  # noqa: E402
from lora.lora_data import GenerativeCollator, GenerativeDataset  # noqa: E402
from lora.lora_generative import generate_predictions  # noqa: E402
from lora.lora_model import PARALLELISM_CHOICES, build_peft_model_causal, load_peft_model_causal  # noqa: E402


def to_device(batch: dict, device: str) -> dict:
    return {k: (v.to(device) if torch.is_tensor(v) else v) for k, v in batch.items()}

# bash slurm_wrapper.sh 4 src/lora/lora_train_generative.py public_data_dev/train.jsonl public_data_dev/dev.jsonl --epochs 200 --parallelism pipeline --model Qwen/Qwen3-8B --df-path emnllp-dialog-flow-dialog-flow.json --lean-prompt --batch-size 1 --output-dir runs/lora_qwen3-8B --checkpoint-save-path $SCRATCH/8-13/Qwen3-8B-batch-size-1 --split-seed 42

def weighted_lm_loss(logits: torch.Tensor, labels: torch.Tensor, loss_weight: torch.Tensor) -> torch.Tensor:
    """Next-token cross-entropy, per-token weighted by `loss_weight` (see --st3-loss-weight
    and GenerativeDataset/GenerativeCollator, which build it as 1.0 everywhere except the
    completion's "st3":[...] span). Reduces to plain HF-style mean CE (identical to
    `model(..., labels=...).loss`) whenever loss_weight is 1.0 on every non-masked token, so
    passing --st3-loss-weight 1.0 (the default) reproduces prior runs exactly."""
    shift_logits = logits[:, :-1, :].contiguous()
    shift_labels = labels[:, 1:].contiguous()
    shift_weight = loss_weight[:, 1:].contiguous()
    per_token = torch.nn.functional.cross_entropy(
        shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1),
        ignore_index=-100, reduction="none",
    ).view(shift_labels.shape)
    mask = (shift_labels != -100).float()
    weighted = per_token * shift_weight * mask
    return weighted.sum() / (shift_weight * mask).sum().clamp_min(1e-6)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("train", help="training split, e.g. public_data_dev/train.jsonl")
    ap.add_argument("dev", help="dev split for per-epoch evaluation, e.g. public_data_dev/dev.jsonl")
    ap.add_argument("--model", default="Qwen/Qwen3.5-4B")
    ap.add_argument("--model-path", default=None, help="load the model/tokenizer from this local "
                     "directory instead of models/{--model}; --model is still used for logging/checkpoint "
                     "naming")
    ap.add_argument("--context", choices=CONTEXT_CHOICES, default="full",
                    help="which rungs of the instance the model sees. no_product_page drops the linked page "
                         "entirely (a median 38%% of full_context's tokens); st2_page keeps only its "
                         "ST2-bearing lines, see common/page_filter.py")
    ap.add_argument("--lean-prompt", action="store_true", help="swap the GPT baseline's zero-shot "
                     "SYSTEM_PROMPT (3,533 tokens of instructions + full taxonomy, which leaves 467 "
                     "of 4,096 for the segment and truncates 98%% of instances) for common.SFT_TAXONOMY "
                     "(440), and render --df-path as stripped text rather than the raw export. Pair "
                     "with --df-path: the lean taxonomy drops the ST1/ST3 definitions on the "
                     "understanding that the dialog flow carries them")
    ap.add_argument(
        "--df-path", default=None,
        help="path to the autoDF-generated dialog-flow JSON (e.g. emnllp-dialog-flow-dialog-flow.json) "
        "to add to the system message, ahead of the segment text; omit to train without it",
    )
    ap.add_argument("--max-length", type=int, default=4096, help="prompt includes the system "
                     "prompt/taxonomy and any --df-path flow, not just the segment text, so this is "
                     "much larger than lora_train.py's default")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--eval-batch-size", type=int, default=None, help="batch size for the per-epoch dev "
                     "generate() eval; defaults to --batch-size. Decoupled because training's per-token "
                     "loss forward pass (logits.float() over the full sequence x vocab) is far more "
                     "memory-hungry than generate()'s one-token-at-a-time decode, so eval can usually run "
                     "at a much larger batch size than training without risking OOM")
    ap.add_argument("--grad-accum-steps", type=int, default=4)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--warmup-ratio", type=float, default=0.06)
    ap.add_argument("--lora-r", type=int, default=8)
    ap.add_argument("--lora-alpha", type=int, default=16)
    ap.add_argument("--lora-dropout", type=float, default=0.1)
    ap.add_argument("--target-modules", default="q_proj,v_proj", help="comma-separated module names to LoRA-adapt")
    ap.add_argument("--st3-loss-weight", type=float, default=1.0, help="multiply the next-token "
                     "CE loss on the completion's \"st3\":[...] span by this factor (st1/st2 "
                     "tokens are unaffected). st3 is this task's weakest, most class-imbalanced "
                     "subtask (insufficient_context/hfss_food_marketing/age_restricted are all "
                     "under 3%% of train); default 1.0 reproduces the unweighted loss exactly")
    ap.add_argument("--load-in-4bit", action="store_true", help="QLoRA via bitsandbytes (must be installed separately)")
    ap.add_argument("--parallelism", choices=PARALLELISM_CHOICES, default="none", help="split the model "
                     "across GPUs (requires >=2): \"pipeline\" shards layers via device_map=\"auto\"; \"tensor\" "
                     "shards weight matrices via tp_plan=\"auto\" (must launch with torchrun); \"none\" keeps "
                     "everything on --device")
    ap.add_argument("--max-new-tokens", type=int, default=128, help="generation budget for the JSON completion during dev eval")
    ap.add_argument("--sample-size", type=int, default=None, help="sample N train and N dev instances (seeded smoke test)")
    ap.add_argument("--test-holdout", type=int, default=500, help="hold out this many instances from "
                     "`train`, split off before training, as a generalization check separate from "
                     "dev (which is used for per-epoch model selection and must stay untouched -- "
                     "the ground-truth harness). Evaluated once at the end against the best-dev "
                     "checkpoint. Pass 0 to disable")
    ap.add_argument("--split-seed", type=int, default=None, help="seed for the train/test-holdout "
                     "split; omit for a fresh random split each run (the default and recommended "
                     "setting -- a fixed holdout would just become a second dev set that "
                     "experiments quietly overfit to across many runs). Pass a fixed value only to "
                     "reproduce a specific run's split")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--device", default=None, help="defaults to cuda if available, else cpu")
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--checkpoint-save-path", default=None, help="directory under which to save "
                     "the best/last adapter checkpoints (<checkpoint-save-path>/best, "
                     "<checkpoint-save-path>/last); defaults to --output-dir")
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    is_main = int(os.environ.get("RANK", "0")) == 0  # only rank 0 logs/saves under --parallelism tensor

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if is_main:
        log = setup_logging("runs", "lora_train_generative", args.model.replace("/", "_"), timestamp)
    else:
        log = logging.getLogger("lora_train_generative_worker")
        log.addHandler(logging.NullHandler())
        log.propagate = False
    log.info(f"config: {vars(args)} device={device}")

    train_instances = list(load_split(args.train))
    dev_instances = list(load_split(args.dev))

    split_seed = args.split_seed if args.split_seed is not None else random.SystemRandom().randint(0, 2**31 - 1)
    shuffled = train_instances[:]
    random.Random(split_seed).shuffle(shuffled)
    test_holdout_instances = shuffled[:args.test_holdout]
    train_instances = shuffled[args.test_holdout:]
    log.info(f"train/test-holdout split (fresh random split every run unless --split-seed is "
             f"pinned): split_seed={split_seed} train={len(train_instances)} "
             f"test_holdout={len(test_holdout_instances)}")

    if args.sample_size:
        rng = random.Random(args.seed)
        train_instances = rng.sample(train_instances, min(args.sample_size, len(train_instances)))
        dev_instances = rng.sample(dev_instances, min(args.sample_size, len(dev_instances)))
    log.info(f"train={len(train_instances)} dev={len(dev_instances)}")

    model_path = args.model_path or os.path.join("models", args.model)
    if not os.path.isdir(model_path):
        raise FileNotFoundError(
            f"expected local model at {model_path!r} "
            + (f"(from --model-path {args.model_path!r})" if args.model_path else
               f"(from --model {args.model!r}); download it first with "
               f"`hf download {args.model} --local-dir {model_path}`")
        )
    log.info(f"loading model/tokenizer from local path {model_path} (no remote download)")

    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = build_peft_model_causal(
        model_path, lora_r=args.lora_r, lora_alpha=args.lora_alpha, lora_dropout=args.lora_dropout,
        target_modules=args.target_modules.split(","), load_in_4bit=args.load_in_4bit, device=device,
        local_files_only=True, parallelism=args.parallelism,
    )
    if args.parallelism == "none" and not args.load_in_4bit:
        model = model.to(device)
    model.print_trainable_parameters()

    system_prompt = SFT_TAXONOMY if args.lean_prompt else SYSTEM_PROMPT
    df_text = df_pre_context(args.df_path, lean=args.lean_prompt) if args.df_path else None
    if args.lean_prompt and not args.df_path:
        log.warning("--lean-prompt without --df-path: the lean taxonomy gives bare ST1/ST3 label "
                    "lists because the dialog flow is expected to supply their definitions, so "
                    "nothing in this prompt defines them. Intended only as an ablation.")
    log.info(f"system prompt: {'lean' if args.lean_prompt else 'full'} ({len(system_prompt)} chars)"
             + (f" + dialog flow from {args.df_path} ({len(df_text)} chars)" if df_text else ""))

    collate = GenerativeCollator(tokenizer)
    train_ds = GenerativeDataset(train_instances, tokenizer, args.context, args.max_length,
                                 system_prompt, df_text, st3_loss_weight=args.st3_loss_weight)
    dev_ds = GenerativeDataset(dev_instances, tokenizer, args.context, args.max_length,
                               system_prompt, df_text)
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, collate_fn=collate)
    eval_batch_size = args.eval_batch_size or args.batch_size
    dev_loader = DataLoader(dev_ds, batch_size=eval_batch_size, shuffle=False, collate_fn=collate)

    trainable = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(trainable, lr=args.lr)
    steps_per_epoch = -(-len(train_loader) // args.grad_accum_steps)  # ceil div
    total_steps = steps_per_epoch * args.epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=int(args.warmup_ratio * total_steps), num_training_steps=total_steps
    )

    checkpoint_dir = args.checkpoint_save_path or args.output_dir
    best_f1 = -1.0
    os.makedirs(checkpoint_dir, exist_ok=True)
    for epoch in range(args.epochs):
        model.train()
        tokenizer.padding_side = "right"  # loss-masked labels must line up token-for-token
        running_loss = 0.0
        for step, batch in enumerate(tqdm(train_loader, desc=f"epoch {epoch + 1}/{args.epochs}", disable=not is_main)):
            batch = to_device(batch, model.device)
            out = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"])
            raw_loss = weighted_lm_loss(out.logits, batch["labels"], batch["loss_weight"])
            loss = raw_loss / args.grad_accum_steps
            loss.backward()
            running_loss += raw_loss.item()
            if (step + 1) % args.grad_accum_steps == 0 or step + 1 == len(train_loader):
                torch.nn.utils.clip_grad_norm_(trainable, 1.0)
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()
        log.info(f"epoch {epoch + 1}: mean train loss = {running_loss / len(train_loader):.4f}")

        tokenizer.padding_side = "left"  # batched model.generate() needs left-padding
        ids, preds = generate_predictions(model, dev_loader, tokenizer, args.max_new_tokens)
        gold = [inst["labels"] for inst in dev_instances]
        metrics = evaluate(gold, preds)
        scalar_metrics = {k: v for k, v in metrics.items() if k != "per_label_f1"}
        log.info(f"epoch {epoch + 1} dev metrics: " + ", ".join(f"{k}={v:.3f}" for k, v in scalar_metrics.items()))
        for tier, per_label in metrics["per_label_f1"].items():
            log.info(f"epoch {epoch + 1} dev {tier} per-label F1: "
                     + ", ".join(f"{label}={f1:.3f}" for label, f1 in sorted(per_label.items())))
        log_prediction_diagnostics(log, gold, preds)

        if metrics["mean_macro_f1"] > best_f1:
            best_f1 = metrics["mean_macro_f1"]
            best_dev_scalar_metrics = scalar_metrics
            if is_main:  # avoid every rank racing to write the same adapter dir under --parallelism tensor
                best_dir = os.path.join(checkpoint_dir, "best")
                model.save_pretrained(best_dir)
                write_submission(
                    os.path.join(best_dir, "submission.jsonl"), os.path.join(best_dir, "submission_error.jsonl"),
                    ids, dev_instances, preds,
                )
                log.info(f"epoch {epoch + 1}: new best mean_macro_f1={best_f1:.3f}, saved to {checkpoint_dir}/best")

    if is_main:
        model.save_pretrained(os.path.join(checkpoint_dir, "last"))
        log.info(f"saved final epoch adapter to {checkpoint_dir}/last (best dev mean_macro_f1={best_f1:.3f})")
        log.info("best dev metrics: " + ", ".join(f"{k}={v:.3f}" for k, v in best_dev_scalar_metrics.items()))

        if test_holdout_instances:
            best_dir = os.path.join(checkpoint_dir, "best")
            log.info(f"reloading best-dev checkpoint from {best_dir} for the test-holdout pass "
                     f"(generalization check, not used for model selection)")
            test_model = load_peft_model_causal(
                model_path, best_dir, load_in_4bit=args.load_in_4bit, device=device,
                local_files_only=True, parallelism=args.parallelism,
            )
            if args.parallelism == "none" and not args.load_in_4bit:
                test_model = test_model.to(device)
            test_model.eval()
            tokenizer.padding_side = "left"
            test_loader = DataLoader(
                GenerativeDataset(test_holdout_instances, tokenizer, args.context, args.max_length,
                                  system_prompt, df_text),
                batch_size=eval_batch_size, shuffle=False, collate_fn=collate,
            )
            test_ids, test_preds = generate_predictions(test_model, test_loader, tokenizer, args.max_new_tokens)
            test_gold = [inst["labels"] for inst in test_holdout_instances]
            test_metrics = evaluate(test_gold, test_preds)
            test_scalar_metrics = {k: v for k, v in test_metrics.items() if k != "per_label_f1"}
            log.info("test holdout metrics: " + ", ".join(f"{k}={v:.3f}" for k, v in test_scalar_metrics.items()))
            for tier, per_label in test_metrics["per_label_f1"].items():
                log.info(f"{tier} per-label F1: "
                        + ", ".join(f"{label}={f1:.3f}" for label, f1 in sorted(per_label.items())))
            log_prediction_diagnostics(log, test_gold, test_preds)
            write_submission(
                os.path.join(best_dir, "test_submission.jsonl"),
                os.path.join(best_dir, "test_submission_error.jsonl"),
                test_ids, test_holdout_instances, test_preds,
            )


if __name__ == "__main__":
    main()
