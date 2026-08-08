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
from transformers import AutoTokenizer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # so `import lora` resolves src/lora as a package
from common.predict_utils import decode, load_thresholds, multi_hot_matrix, run_inference, tune_per_label_thresholds  # noqa: E402
from lora import ST1_LABELS, ST2_LABELS, ST3_LABELS, evaluate, prediction_errors, setup_logging  # noqa: E402
from lora.lora_data import Collator, ClassificationDataset, load_split  # noqa: E402
from lora.lora_model import load_peft_model  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="split to predict on, e.g. public_data_dev/dev.jsonl")
    ap.add_argument("--model", default="FacebookAI/roberta-base", help="must match the base model used in training")
    ap.add_argument("--adapter-dir", required=True, help="e.g. runs/lora_roberta/best")
    ap.add_argument("--context", choices=["transcript", "full"], default="full")
    ap.add_argument("--max-length", type=int, default=512)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument(
        "--threshold", type=float, default=0.5,
        help="flat sigmoid threshold, used only if neither --tune-thresholds-on nor a saved thresholds.json applies",
    )
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
    else:
        loaded_st2, loaded_st3 = load_thresholds(args.adapter_dir)
        if loaded_st2 is not None:
            st2_threshold, st3_threshold = loaded_st2, loaded_st3
            log.info(f"loaded tuned thresholds saved during training from {args.adapter_dir}/thresholds.json")

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
