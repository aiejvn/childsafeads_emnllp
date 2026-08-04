"""Run a trained LoRA encoder adapter over a split and write a submission.jsonl.

Usage (run from the repo root):
    python src/lora/lora_predict.py public_data_dev/dev.jsonl \\
        --model FacebookAI/roberta-base --adapter-dir runs/lora_roberta/best \\
        --out runs/submission_lora.jsonl
    python src/lora/lora_predict.py public_data_dev/dev.jsonl --adapter-dir ... \\
        --tune-thresholds-on public_data_dev/dev.jsonl  # per-label thresholds, tuned for F1

Prints the same macro-F1 metrics as baseline_gpt.py whenever the target split carries
gold "labels". Beyond sanitize_st3 (shared with the LLM baselines), this also resolves
two constraint violations that independent per-label sigmoids -- unlike an LLM's joint
generation -- can produce: undisclosed_advertising/inadequate_disclosure both firing
(kept: the higher-probability one), and an empty st2 (fallback: its top-1 label).
"""
import argparse
import json
import os
import random
import shutil
import sys
from datetime import datetime

import torch
from torch.utils.data import DataLoader
from tqdm import tqdm
from transformers import AutoTokenizer

from lora import ST1_LABELS, ST2_LABELS, ST3_LABELS, evaluate, prediction_errors, sanitize_st3, setup_logging  # noqa: E402
from lora.lora_data import Collator, ClassificationDataset, load_split  # noqa: E402
from lora.lora_model import load_peft_model  # noqa: E402

UNDISCLOSED, INADEQUATE = "undisclosed_advertising", "inadequate_disclosure"
UNDISCLOSED_IDX, INADEQUATE_IDX = ST3_LABELS.index(UNDISCLOSED), ST3_LABELS.index(INADEQUATE)


def to_device(batch: dict, device: str) -> dict:
    return {k: (v.to(device) if torch.is_tensor(v) else v) for k, v in batch.items()}


@torch.no_grad()
def run_inference(model, loader, device):
    """Returns (instanceIDs, st1_idx, st2_probs, st3_probs) stacked across the whole split."""
    ids, st1_idx, st2_probs, st3_probs = [], [], [], []
    for batch in tqdm(loader, desc="predicting"):
        batch = to_device(batch, device)
        out = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"])
        ids.extend(batch["instanceID"])
        st1_idx.append(out["st1_logits"].argmax(dim=-1).cpu())
        st2_probs.append(torch.sigmoid(out["st2_logits"]).cpu())
        st3_probs.append(torch.sigmoid(out["st3_logits"]).cpu())
    return ids, torch.cat(st1_idx), torch.cat(st2_probs), torch.cat(st3_probs)


def tune_per_label_thresholds(probs: torch.Tensor, gold_multihot: torch.Tensor, grid=None) -> torch.Tensor:
    """Sweep a threshold grid per label, picking the one maximizing that label's F1."""
    grid = grid or [i / 20 for i in range(1, 20)]
    thresholds = torch.full((probs.shape[1],), 0.5)
    for j in range(probs.shape[1]):
        best_f1, best_t = -1.0, 0.5
        col_probs, col_gold = probs[:, j], gold_multihot[:, j]
        for t in grid:
            pred = (col_probs >= t).float()
            tp = (pred * col_gold).sum().item()
            fp = (pred * (1 - col_gold)).sum().item()
            fn = ((1 - pred) * col_gold).sum().item()
            if tp == 0 and fp == 0 and fn == 0:
                continue
            precision = tp / (tp + fp) if (tp + fp) else 0.0
            recall = tp / (tp + fn) if (tp + fn) else 0.0
            f1 = 2 * precision * recall / (precision + recall + 1e-6)
            if f1 > best_f1:
                best_f1, best_t = f1, t
        thresholds[j] = best_t
    return thresholds


def multi_hot_matrix(instances: list, labels_key: str, label_list: list) -> torch.Tensor:
    mat = torch.zeros(len(instances), len(label_list))
    for i, inst in enumerate(instances):
        for flag in inst["labels"][labels_key]:
            if flag in label_list:
                mat[i, label_list.index(flag)] = 1.0
    return mat


def resolve_disclosure_conflict(st3_flags: list, st3_prob_row: torch.Tensor) -> list:
    if UNDISCLOSED in st3_flags and INADEQUATE in st3_flags:
        drop = INADEQUATE if st3_prob_row[UNDISCLOSED_IDX] >= st3_prob_row[INADEQUATE_IDX] else UNDISCLOSED
        return [f for f in st3_flags if f != drop]
    return st3_flags


def st2_fallback(st2_flags: list, st2_prob_row: torch.Tensor) -> list:
    return st2_flags if st2_flags else [ST2_LABELS[int(st2_prob_row.argmax())]]


def decode(st1_idx, st2_probs, st3_probs, st2_threshold, st3_threshold) -> list:
    preds = []
    for i in range(len(st1_idx)):
        st2 = [ST2_LABELS[j] for j in range(len(ST2_LABELS)) if st2_probs[i, j] >= st2_threshold[j]]
        st3 = [ST3_LABELS[j] for j in range(len(ST3_LABELS)) if st3_probs[i, j] >= st3_threshold[j]]
        st3 = sanitize_st3(resolve_disclosure_conflict(st3, st3_probs[i]))
        st2 = st2_fallback(st2, st2_probs[i])
        preds.append({"st1": ST1_LABELS[st1_idx[i]], "st2": st2, "st3": st3})
    return preds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="split to predict on, e.g. public_data_dev/dev.jsonl")
    ap.add_argument("--model", default="FacebookAI/roberta-base", help="must match the base model used in training")
    ap.add_argument("--adapter-dir", required=True, help="e.g. runs/lora_roberta/best")
    ap.add_argument("--context", choices=["transcript", "full"], default="full")
    ap.add_argument("--max-length", type=int, default=512)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--threshold", type=float, default=0.5, help="flat sigmoid threshold if not tuning")
    ap.add_argument("--tune-thresholds-on", help="split (e.g. dev.jsonl) to sweep per-label st2/st3 thresholds on")
    ap.add_argument("--sample-size", type=int, default=None, help="predict on a random sample only (smoke test)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--device", default=None)
    ap.add_argument("--out", help="defaults to runs/submission_lora_<timestamp>.jsonl")
    args = ap.parse_args()

    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log = setup_logging("runs", "lora_predict", args.model.replace("/", "_"), timestamp)

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = load_peft_model(args.model, len(ST1_LABELS), len(ST2_LABELS), len(ST3_LABELS), args.adapter_dir)
    model.to(device).eval()

    st2_threshold = torch.full((len(ST2_LABELS),), args.threshold)
    st3_threshold = torch.full((len(ST3_LABELS),), args.threshold)
    if args.tune_thresholds_on:
        tune_instances = list(load_split(args.tune_thresholds_on))
        tune_loader = DataLoader(
            ClassificationDataset(tune_instances, tokenizer, args.context, args.max_length),
            batch_size=args.batch_size, shuffle=False, collate_fn=Collator(tokenizer),
        )
        _, _, st2_probs, st3_probs = run_inference(model, tune_loader, device)
        st2_threshold = tune_per_label_thresholds(st2_probs, multi_hot_matrix(tune_instances, "st2", ST2_LABELS))
        st3_threshold = tune_per_label_thresholds(st3_probs, multi_hot_matrix(tune_instances, "st3", ST3_LABELS))
        log.info(f"tuned st2 thresholds: {dict(zip(ST2_LABELS, st2_threshold.tolist()))}")
        log.info(f"tuned st3 thresholds: {dict(zip(ST3_LABELS, st3_threshold.tolist()))}")

    instances = list(load_split(args.target))
    if args.sample_size:
        instances = random.Random(args.seed).sample(instances, min(args.sample_size, len(instances)))
    loader = DataLoader(
        ClassificationDataset(instances, tokenizer, args.context, args.max_length),
        batch_size=args.batch_size, shuffle=False, collate_fn=Collator(tokenizer),
    )
    ids, st1_idx, st2_probs, st3_probs = run_inference(model, loader, device)
    predictions = decode(st1_idx, st2_probs, st3_probs, st2_threshold, st3_threshold)

    out = args.out or os.path.join("runs", f"submission_lora_{timestamp}.jsonl")
    error_out = os.path.join("runs", f"submission_lora_error_{timestamp}.jsonl")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    gold = []
    n_errors = 0
    with open(out, "w", encoding="utf-8") as f, open(error_out, "w", encoding="utf-8") as f_err:
        for iid, inst, pred in zip(ids, instances, predictions):
            f.write(json.dumps({"instanceID": iid, **pred}) + "\n")
            if inst.get("labels"):
                gold.append(inst["labels"])
                errors = prediction_errors(inst["labels"], pred)
                if errors:
                    n_errors += 1
                    f_err.write(json.dumps({"instanceID": iid, "gold": inst["labels"], "pred": pred, "errors": errors}) + "\n")
    log.info(f"wrote {len(predictions)} predictions to {out}")

    canonical = "submission_lora.jsonl"
    shutil.copyfile(out, canonical)
    log.info(f"copied predictions to {canonical} (canonical submission file)")

    if gold:
        log.info(f"wrote {n_errors} misclassified instance(s) to {error_out}")
        metrics = evaluate(gold, predictions)
        log.info("Evaluation:")
        for k, v in metrics.items():
            log.info(f"  {k}: {v:.3f}")
    else:
        log.info("target has no gold labels -- skipping evaluation")


if __name__ == "__main__":
    main()
