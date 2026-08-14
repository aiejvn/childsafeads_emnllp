"""Train stage 2 of the disclosure pipeline (src/disclosure_pipeline.py): a token-
classification model that tags which words in TRANSCRIPT + DESCRIPTION are part of a
disclosure-relevant span (a sponsor/affiliate acknowledgment, or its absence made
concrete by the surrounding pitch), from BIO labels built out of gold st3_evidence
quotes for undisclosed_advertising/inadequate_disclosure (see disclosure_data.py).

Usage (run from the repo root):
    python src/disclosure_tagger_train.py public_data_dev/train.jsonl public_data_dev/dev.jsonl \\
        --output-dir runs/disclosure_tagger
    python src/disclosure_tagger_train.py public_data_dev/train.jsonl public_data_dev/dev.jsonl \\
        --sample-size 32 --epochs 1 --output-dir runs/disclosure_tagger_smoke  # smoke test

Saves the best-dev-F1 checkpoint to <output-dir>/best and the final epoch's to
<output-dir>/last, both loadable by disclosure_pipeline.py --tagger-dir.
"""
import argparse
import os
import random
import sys
from datetime import datetime

import torch
from torch.utils.data import DataLoader
from tqdm import tqdm
from transformers import AutoModelForTokenClassification, AutoTokenizer, get_linear_schedule_with_warmup

sys.path.insert(0, os.path.dirname(__file__))
from disclosure_data import Collator, DisclosureSpanDataset, LABEL_LIST, has_disclosure_flag, load_split, taggable_instances


def to_device(batch: dict, device: str) -> dict:
    return {k: (v.to(device) if torch.is_tensor(v) else v) for k, v in batch.items()}


@torch.no_grad()
def evaluate_tagger(model, loader, device, instances_by_id: dict) -> dict:
    """Two views of the same predictions, both useful for a stage-2 tagger whose only
    job is to hand stage 3 a trimmed candidate span:
    - token-level P/R/F1 on the DISC tag (B-DISC/I-DISC collapsed), the standard span
      metric.
    - instance-level recall/false-positive rate: on flagged instances, did the tagger
      find *any* span (what stage 3 needs to even get a look); on clean instances, did
      it wrongly find one anyway.
    """
    model.eval()
    tp = fp = fn = 0
    flagged_hit = flagged_total = 0
    clean_fp = clean_total = 0
    for batch in loader:
        gpu_batch = to_device(batch, device)
        logits = model(input_ids=gpu_batch["input_ids"], attention_mask=gpu_batch["attention_mask"]).logits
        pred_ids = logits.argmax(dim=-1).cpu()
        for i, iid in enumerate(batch["instanceID"]):
            gold_ids = batch["labels"][i]
            mask = gold_ids != -100
            p = pred_ids[i][mask]
            g = gold_ids[mask]
            p_disc = p != 0  # LABEL_LIST[0] == "O"
            g_disc = g != 0
            tp += int((p_disc & g_disc).sum())
            fp += int((p_disc & ~g_disc).sum())
            fn += int((~p_disc & g_disc).sum())

            inst = instances_by_id[iid]
            has_pred = bool(p_disc.any())
            if has_disclosure_flag(inst):
                flagged_total += 1
                flagged_hit += int(has_pred)
            else:
                clean_total += 1
                clean_fp += int(has_pred)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall + 1e-6) if (precision + recall) else 0.0
    return {
        "token_precision": precision,
        "token_recall": recall,
        "token_f1": f1,
        "flagged_recall": flagged_hit / flagged_total if flagged_total else 0.0,
        "clean_false_positive_rate": clean_fp / clean_total if clean_total else 0.0,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("train", help="training split, e.g. public_data_dev/train.jsonl")
    ap.add_argument("dev", help="dev split for per-epoch evaluation, e.g. public_data_dev/dev.jsonl")
    ap.add_argument("--model", default="FacebookAI/roberta-base")
    ap.add_argument("--max-length", type=int, default=512)
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--warmup-ratio", type=float, default=0.06)
    ap.add_argument("--sample-size", type=int, default=None,
                     help="sample N train and N dev instances (seeded smoke test)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--device", default=None)
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")

    train_instances = taggable_instances(list(load_split(args.train)))
    dev_instances = taggable_instances(list(load_split(args.dev)))
    if args.sample_size:
        rng = random.Random(args.seed)
        train_instances = rng.sample(train_instances, min(args.sample_size, len(train_instances)))
        dev_instances = rng.sample(dev_instances, min(args.sample_size, len(dev_instances)))
    dev_by_id = {inst["instanceID"]: inst for inst in dev_instances}
    print(f"train={len(train_instances)} (taggable) dev={len(dev_instances)} (taggable) device={device}")

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    train_ds = DisclosureSpanDataset(train_instances, tokenizer, args.max_length)
    dev_ds = DisclosureSpanDataset(dev_instances, tokenizer, args.max_length)
    collate = Collator(tokenizer)
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, collate_fn=collate)
    dev_loader = DataLoader(dev_ds, batch_size=args.batch_size, shuffle=False, collate_fn=collate)

    model = AutoModelForTokenClassification.from_pretrained(
        args.model, num_labels=len(LABEL_LIST),
        id2label=dict(enumerate(LABEL_LIST)), label2id={l: i for i, l in enumerate(LABEL_LIST)},
    ).to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)
    total_steps = len(train_loader) * args.epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=int(args.warmup_ratio * total_steps), num_training_steps=total_steps
    )

    best_f1 = -1.0
    os.makedirs(args.output_dir, exist_ok=True)
    for epoch in range(args.epochs):
        model.train()
        running_loss = 0.0
        for batch in tqdm(train_loader, desc=f"epoch {epoch + 1}/{args.epochs}"):
            batch = to_device(batch, device)
            out = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"], labels=batch["labels"])
            out.loss.backward()
            running_loss += out.loss.item()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()
        print(f"epoch {epoch + 1}: mean train loss = {running_loss / len(train_loader):.4f}")

        metrics = evaluate_tagger(model, dev_loader, device, dev_by_id)
        print(f"epoch {epoch + 1} dev: " + ", ".join(f"{k}={v:.3f}" for k, v in metrics.items()))

        if metrics["token_f1"] > best_f1:
            best_f1 = metrics["token_f1"]
            best_dir = os.path.join(args.output_dir, "best")
            model.save_pretrained(best_dir)
            tokenizer.save_pretrained(best_dir)
            print(f"epoch {epoch + 1}: new best token_f1={best_f1:.3f}, saved to {best_dir}")

    last_dir = os.path.join(args.output_dir, "last")
    model.save_pretrained(last_dir)
    tokenizer.save_pretrained(last_dir)
    print(f"saved final epoch to {last_dir} (best dev token_f1={best_f1:.3f})")


if __name__ == "__main__":
    main()