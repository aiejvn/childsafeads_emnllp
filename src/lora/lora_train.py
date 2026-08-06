"""Train a LoRA-adapted BERT-family encoder (roBERTa/legal-bert) with three heads
(st1/st2/st3) on the ChildSafeAds task.

Usage (run from the repo root):
    python src/lora/lora_train.py public_data_dev/train.jsonl public_data_dev/dev.jsonl \\
        --model FacebookAI/roberta-base --epochs 5 --batch-size 16 --output-dir runs/lora_roberta
    python src/lora/lora_train.py public_data_dev/train.jsonl public_data_dev/dev.jsonl \\
        --sample-size 16 --epochs 1 --batch-size 4 --output-dir runs/lora_smoke  # smoke test

Saves the best-dev-macro-F1 adapter+heads to <output-dir>/best and the final epoch's
to <output-dir>/last (both loadable with lora_predict.py).
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

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # so `import lora` resolves src/lora as a package
from lora import ST1_LABELS, ST2_LABELS, ST3_LABELS, evaluate, sanitize_st3, setup_logging  # noqa: E402
from lora.lora_data import Collator, ClassificationDataset, load_split  # noqa: E402
from lora.lora_model import build_peft_model  # noqa: E402


def to_device(batch: dict, device: str) -> dict:
    return {k: (v.to(device) if torch.is_tensor(v) else v) for k, v in batch.items()}


def compute_pos_weight(instances: list, labels_key: str, label_list: list) -> torch.Tensor:
    """Inverse-frequency BCE pos_weight per label, from training-set label counts."""
    pos = torch.zeros(len(label_list))
    for inst in instances:
        for flag in inst["labels"][labels_key]:
            if flag in label_list:
                pos[label_list.index(flag)] += 1
    total = len(instances)
    neg = total - pos
    return (neg / pos.clamp(min=1)).clamp(max=50.0)


@torch.no_grad()
def decode(logits_st1, logits_st2, logits_st3, threshold: float) -> list:
    st1_idx = logits_st1.argmax(dim=-1).tolist()
    st2_probs = torch.sigmoid(logits_st2)
    st3_probs = torch.sigmoid(logits_st3)
    preds = []
    for i in range(len(st1_idx)):
        st2 = [ST2_LABELS[j] for j in range(len(ST2_LABELS)) if st2_probs[i, j] >= threshold]
        st3 = sanitize_st3([ST3_LABELS[j] for j in range(len(ST3_LABELS)) if st3_probs[i, j] >= threshold])
        preds.append({"st1": ST1_LABELS[st1_idx[i]], "st2": st2, "st3": st3})
    return preds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("train", help="training split, e.g. public_data_dev/train.jsonl")
    ap.add_argument("dev", help="dev split for per-epoch evaluation, e.g. public_data_dev/dev.jsonl")
    ap.add_argument("--model", default="FacebookAI/roberta-base")
    ap.add_argument("--context", choices=["transcript", "full"], default="full")
    ap.add_argument("--max-length", type=int, default=512) # 512?! seems a bit short, if this is sequence length
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--grad-accum-steps", type=int, default=1)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--warmup-ratio", type=float, default=0.06)
    ap.add_argument("--lora-r", type=int, default=8)
    ap.add_argument("--lora-alpha", type=int, default=16)
    ap.add_argument("--lora-dropout", type=float, default=0.1)
    ap.add_argument("--target-modules", default="query,value", help="comma-separated module names to LoRA-adapt")
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

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    train_ds = ClassificationDataset(train_instances, tokenizer, args.context, args.max_length)
    dev_ds = ClassificationDataset(dev_instances, tokenizer, args.context, args.max_length)
    collate = Collator(tokenizer)
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, collate_fn=collate)
    dev_loader = DataLoader(dev_ds, batch_size=args.batch_size, shuffle=False, collate_fn=collate)

    model = build_peft_model(
        args.model, len(ST1_LABELS), len(ST2_LABELS), len(ST3_LABELS),
        lora_r=args.lora_r, lora_alpha=args.lora_alpha, lora_dropout=args.lora_dropout,
        target_modules=args.target_modules.split(","),
    ).to(device)
    model.print_trainable_parameters()

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

        preds = []
        model.eval()
        with torch.no_grad():
            for batch in dev_loader:
                batch = to_device(batch, device)
                out = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"])
                preds.extend(decode(out["st1_logits"], out["st2_logits"], out["st3_logits"], args.threshold))
        gold = [inst["labels"] for inst in dev_instances]
        metrics = evaluate(gold, preds)
        log.info(f"epoch {epoch + 1} dev metrics: " + ", ".join(f"{k}={v:.3f}" for k, v in metrics.items()))
        wandb.log({"epoch": epoch + 1, "train_loss": train_loss, **{f"dev_{k}": v for k, v in metrics.items()}})

        if metrics["mean_macro_f1"] > best_f1:
            best_f1 = metrics["mean_macro_f1"]
            model.save_pretrained(os.path.join(args.output_dir, "best"))
            log.info(f"epoch {epoch + 1}: new best mean_macro_f1={best_f1:.3f}, saved to {args.output_dir}/best")

    model.save_pretrained(os.path.join(args.output_dir, "last"))
    log.info(f"saved final epoch adapter to {args.output_dir}/last (best dev mean_macro_f1={best_f1:.3f})")
    wandb.summary.update({f"final_dev_{k}": v for k, v in metrics.items()})
    wandb.summary["best_mean_macro_f1"] = best_f1
    wandb.finish()


if __name__ == "__main__":
    main()
