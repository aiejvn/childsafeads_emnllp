"""Train a last-layer-only BERT-family encoder (roBERTa/legal-bert) with three heads
(st1/st2/st3) on the ChildSafeAds task. Unlike src/lora, this does NOT use LoRA/PEFT:
the entire encoder is frozen except its last --num-unfrozen-layers transformer blocks,
plus the three heads, which train fully.

Usage (run from the repo root):
    python src/last_layer/last_layer_train.py public_data_dev/train.jsonl public_data_dev/dev.jsonl \\
        --model FacebookAI/roberta-base --epochs 5 --batch-size 16 --output-dir runs/last_layer_roberta
    python src/last_layer/last_layer_train.py public_data_dev/train.jsonl public_data_dev/dev.jsonl \\
        --sample-size 16 --epochs 1 --batch-size 4 --output-dir runs/last_layer_smoke  # smoke test

Saves the best-dev-macro-F1 checkpoint to <output-dir>/best and the final epoch's to
<output-dir>/last (both loadable with last_layer_predict.py).
"""
import argparse
import os
import random
import sys
from datetime import datetime

import torch
import wandb
from torch.utils.data import DataLoader
from tqdm import tqdm
from transformers import AutoTokenizer, get_linear_schedule_with_warmup

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # so `import last_layer`/`import common` resolve
from common.classification_data import Collator, ClassificationDataset  # noqa: E402
from common.predict_utils import log_prediction_diagnostics, save_thresholds, tune_and_decode  # noqa: E402
from common.train_utils import compute_pos_weight, to_device  # noqa: E402
from last_layer import CONTEXT_CHOICES, ST1_LABELS, ST2_LABELS, ST3_LABELS, evaluate, load_split, setup_logging  # noqa: E402
from last_layer.last_layer_model import build_frozen_model, count_trainable_parameters, save_frozen_model  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("train", help="training split, e.g. public_data_dev/train.jsonl")
    ap.add_argument("dev", help="dev split for per-epoch evaluation, e.g. public_data_dev/dev.jsonl")
    ap.add_argument("--model", default="FacebookAI/roberta-base")
    ap.add_argument("--context", choices=CONTEXT_CHOICES, default="full",
                    help="which rungs of the instance the model sees. no_product_page drops the linked page "
                         "entirely (a median 38%% of full_context's tokens); st2_page keeps only its "
                         "ST2-bearing lines, see common/page_filter.py")
    ap.add_argument("--max-length", type=int, default=512)
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--grad-accum-steps", type=int, default=1)
    ap.add_argument("--lr", type=float, default=2e-5, help="full-finetune LR for the unfrozen block(s)+heads")
    ap.add_argument("--warmup-ratio", type=float, default=0.06)
    ap.add_argument(
        "--num-unfrozen-layers", type=int, default=1,
        help="number of trailing transformer blocks to unfreeze, in addition to the three classification heads",
    )
    ap.add_argument("--st2-loss-weight", type=float, default=1.0)
    ap.add_argument("--st3-loss-weight", type=float, default=1.0)
    ap.add_argument("--pos-weight", action="store_true", help="reweight st2/st3 BCE by inverse train-set frequency")
    ap.add_argument("--threshold", type=float, default=0.5, help="sigmoid threshold for st2/st3 during dev eval")
    ap.add_argument("--sample-size", type=int, default=None, help="sample N train and N dev instances (seeded smoke test)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--device", default=None, help="defaults to cuda if available, else cpu")
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--no-wandb", action="store_true", help="disable W&B logging")
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log = setup_logging("runs", "last_layer_train", args.model.replace("/", "_"), timestamp)
    log.info(f"config: {vars(args)} device={device}")

    wandb.init(
        project="childsafeads-emnllp",
        name=f"last_layer_{args.model.replace('/', '_')}_{timestamp}",
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

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    train_ds = ClassificationDataset(train_instances, tokenizer, args.context, args.max_length)
    dev_ds = ClassificationDataset(dev_instances, tokenizer, args.context, args.max_length)
    collate = Collator(tokenizer)
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, collate_fn=collate)
    dev_loader = DataLoader(dev_ds, batch_size=args.batch_size, shuffle=False, collate_fn=collate)

    model = build_frozen_model(
        args.model, len(ST1_LABELS), len(ST2_LABELS), len(ST3_LABELS),
        num_unfrozen_layers=args.num_unfrozen_layers,
    ).to(device)
    trainable_n, total_n = count_trainable_parameters(model)
    log.info(f"trainable params: {trainable_n}/{total_n} ({trainable_n / total_n:.2%})")

    st2_pos_weight = compute_pos_weight(train_instances, "st2", ST2_LABELS).to(device) if args.pos_weight else None
    st3_pos_weight = compute_pos_weight(train_instances, "st3", ST3_LABELS).to(device) if args.pos_weight else None

    trainable = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(trainable, lr=args.lr)
    steps_per_epoch = -(-len(train_loader) // args.grad_accum_steps)  # ceil div
    total_steps = steps_per_epoch * args.epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=int(args.warmup_ratio * total_steps), num_training_steps=total_steps
    )

    best_f1 = -1.0
    os.makedirs(args.output_dir, exist_ok=True)
    for epoch in range(args.epochs):
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
        log.info(f"epoch {epoch + 1} dev metrics (tuned thresholds): " + ", ".join(f"{k}={v:.3f}" for k, v in scalar_metrics.items()))
        log_prediction_diagnostics(log, gold, preds)
        wandb.log({"epoch": epoch + 1, "train_loss": train_loss, **{f"dev_{k}": v for k, v in scalar_metrics.items()}})

        if metrics["mean_macro_f1"] > best_f1:
            best_f1 = metrics["mean_macro_f1"]
            best_dir = os.path.join(args.output_dir, "best")
            save_frozen_model(
                model, best_dir,
                args.model, len(ST1_LABELS), len(ST2_LABELS), len(ST3_LABELS), args.num_unfrozen_layers,
            )
            save_thresholds(best_dir, st2_threshold, st3_threshold)
            log.info(f"epoch {epoch + 1}: new best mean_macro_f1={best_f1:.3f}, saved to {args.output_dir}/best")

    last_dir = os.path.join(args.output_dir, "last")
    save_frozen_model(
        model, last_dir,
        args.model, len(ST1_LABELS), len(ST2_LABELS), len(ST3_LABELS), args.num_unfrozen_layers,
    )
    save_thresholds(last_dir, st2_threshold, st3_threshold)
    log.info(f"saved final epoch checkpoint to {args.output_dir}/last (best dev mean_macro_f1={best_f1:.3f})")
    wandb.summary.update({f"final_dev_{k}": v for k, v in metrics.items()})
    wandb.summary["best_mean_macro_f1"] = best_f1
    wandb.finish()


if __name__ == "__main__":
    main()
