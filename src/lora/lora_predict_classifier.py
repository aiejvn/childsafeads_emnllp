"""Run one of the single-task st1/st2/st3 LoRA classifiers (trained by
lora_train_st1_classifier.py / lora_train_st2_classifier.py / lora_train_st3_classifier.py)
over a target split and write a submission.jsonl fragment carrying only that tier --
{"instanceID": ..., "st1": "..."} for st1, {"instanceID": ..., "st2": [...]} / {"st3": [...]}
for the multi-label tiers.

Sibling of lora_predict.py, which loads the older joint MultiTaskEncoder checkpoint (one
adapter, three heads). These single-task classifiers instead save a plain
AutoModelForSequenceClassification + LoRA adapter with ONE head per stage, so they need
their own loader. Rather than reimplement tokenization/decoding, this imports each stage's
own training script as a module and calls its Dataset/Collator/run_inference/load_thresholds
directly -- guarantees inference matches that script's own dev/test-holdout eval exactly
(same truncation side/page-token-budget handling, same st2 no-fallback-on-empty behavior,
same st3 resolve_disclosure_conflict+sanitize_st3 post-processing).

Feed the three stages' output files into src/combine_submissions.py to build one merged
submission and get the combined mean_macro_f1 (see that script's docstring).

Usage (run from the repo root):
    python src/lora/lora_predict_classifier.py st1 public_data_test/test.jsonl \\
        --model allenai/longformer-base-4096 --local \\
        --adapter-dir $SCRATCH/runs/st1-classifier-longformer-r16a32/best \\
        --context full --max-length 4096 --truncation-side left \\
        --out runs/submission_st1.jsonl

    # against a labeled split, prints a sanity-check macro_f1 for that tier alone:
    python src/lora/lora_predict_classifier.py st2 public_data_dev/dev.jsonl \\
        --model allenai/longformer-base-4096 --local \\
        --adapter-dir $SCRATCH/runs/st2-classifier-longformer/best \\
        --out runs/submission_st2_dev.jsonl
"""
import argparse
import importlib
import json
import os
import sys
from datetime import datetime

import torch
from torch.utils.data import DataLoader
from transformers import AutoModelForSequenceClassification, AutoTokenizer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # so `import lora`/`import common` resolve
from peft import PeftModel  # noqa: E402
from common import evaluate, load_split, setup_logging  # noqa: E402
from common.predict_utils import log_evaluation  # noqa: E402
from lora import CONTEXT_CHOICES  # noqa: E402

STAGE_MODULES = {
    "st1": "lora_train_st1_classifier",
    "st2": "lora_train_st2_classifier",
    "st3": "lora_train_st3_classifier",
}
STAGE_DATASET_ATTR = {"st1": "ST1Dataset", "st2": "ST2Dataset", "st3": "ST3Dataset"}
STAGE_LABELS_ATTR = {"st1": "ST1_LABELS", "st2": "ST2_LABELS", "st3": "ST3_LABELS"}


def decode_st1(mod, model, loader, device) -> dict:
    ids, pred_idx, _ = mod.run_inference(model, loader, device)
    labels = getattr(mod, STAGE_LABELS_ATTR["st1"])
    return {iid: labels[p] for iid, p in zip(ids, pred_idx.tolist())}


def decode_st2(mod, model, loader, device, thresholds: torch.Tensor) -> dict:
    """No empty-prediction fallback -- matches lora_train_st2_classifier.py's own
    evaluate_split, which just thresholds (st2_fallback is only used by the joint
    MultiTaskEncoder path, common/predict_utils.py's decode())."""
    ids, probs = mod.run_inference(model, loader, device)
    labels = mod.ST2_LABELS
    preds = {}
    for i, iid in enumerate(ids):
        preds[iid] = [labels[j] for j in range(len(labels)) if probs[i, j] >= thresholds[j]]
    return preds


def decode_st3(mod, model, loader, device, thresholds: torch.Tensor) -> dict:
    ids, probs = mod.run_inference(model, loader, device)
    flags = mod.decode(probs, thresholds)  # applies resolve_disclosure_conflict + sanitize_st3
    return dict(zip(ids, flags))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=("st1", "st2", "st3"))
    ap.add_argument("target", help="split to predict on, e.g. public_data_test/test.jsonl")
    ap.add_argument("--model", default="allenai/longformer-base-4096", help="must match the base model used in training")
    ap.add_argument("--local", action="store_true", help="load --model from ./models/{model} instead of the HF hub")
    ap.add_argument("--adapter-dir", required=True, help="e.g. $SCRATCH/runs/st1-classifier-longformer-r16a32/best")
    ap.add_argument("--context", choices=CONTEXT_CHOICES, default="full")
    ap.add_argument("--max-length", type=int, default=4096)
    ap.add_argument("--truncation-side", choices=["left", "right"], default="left")
    ap.add_argument("--page-token-budget", type=int, default=None)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument(
        "--threshold", type=float, default=0.5,
        help="flat st2/st3 fallback threshold, only used if --adapter-dir has no saved thresholds.json",
    )
    ap.add_argument("--device", default=None)
    ap.add_argument("--out", help="defaults to runs/submission_<stage>_<timestamp>.jsonl")
    args = ap.parse_args()

    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log = setup_logging("runs", "lora_predict_classifier", f"{args.stage}_{args.model.replace('/', '_')}", timestamp)

    mod = importlib.import_module(STAGE_MODULES[args.stage])
    labels = getattr(mod, STAGE_LABELS_ATTR[args.stage])

    model_path = args.model
    if args.local:
        local_path = os.path.join("models", args.model)
        if not os.path.isdir(local_path):
            raise FileNotFoundError(f"--local set but {local_path} does not exist")
        model_path = local_path

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    tokenizer.truncation_side = args.truncation_side
    base = AutoModelForSequenceClassification.from_pretrained(model_path, num_labels=len(labels))
    model = PeftModel.from_pretrained(base, args.adapter_dir).to(device)
    model.eval()
    log.info(f"loaded {args.stage} adapter from {args.adapter_dir} (base model {model_path})")

    instances = list(load_split(args.target))
    dataset_cls = getattr(mod, STAGE_DATASET_ATTR[args.stage])
    dataset = dataset_cls(instances, tokenizer, args.context, args.max_length, args.page_token_budget)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=False, collate_fn=mod.Collator(tokenizer))

    if args.stage == "st1":
        preds = decode_st1(mod, model, loader, device)
    else:
        thresholds = mod.load_thresholds(args.adapter_dir)
        if thresholds is None:
            log.info(f"no thresholds.json under {args.adapter_dir} -- falling back to flat --threshold={args.threshold}")
            thresholds = torch.full((len(labels),), args.threshold)
        else:
            log.info(f"loaded tuned thresholds from {args.adapter_dir}/thresholds.json")
        decode_fn = decode_st2 if args.stage == "st2" else decode_st3
        preds = decode_fn(mod, model, loader, device, thresholds)

    out = args.out or os.path.join("runs", f"submission_{args.stage}_{timestamp}.jsonl")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    pred_dicts = []
    with open(out, "w", encoding="utf-8") as f:
        for inst in instances:
            iid = inst["instanceID"]
            rec = {"instanceID": iid, args.stage: preds[iid]}
            pred_dicts.append(rec)
            f.write(json.dumps(rec) + "\n")
    log.info(f"wrote {len(instances)} {args.stage} predictions to {out}")

    if all(inst.get("labels") for inst in instances):
        gold = [inst["labels"] for inst in instances]
        metrics = evaluate(gold, pred_dicts, tiers=(args.stage,))
        log.info(f"=== sanity check: {args.stage} vs. gold in {args.target} ===")
        log_evaluation(log, metrics)


if __name__ == "__main__":
    main()
