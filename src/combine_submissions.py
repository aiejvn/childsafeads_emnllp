"""Combine independently-generated submission files into one, picking which source
produces each subtask's (st1/st2/st3) predictions -- e.g. a Qwen LoRA adapter's own
predictions for st1/st2 (see lora/lora_predict_generative.py) and the LLM baseline's
dialog-flow-tuned st3-only run (baseline_gpt.py --st3-only, which writes
submission_gpt_st3.jsonl) for st3.

Usage (from repo root):
    python src/combine_submissions.py public_data_dev/dev.jsonl \\
        --st1 submission_lora_qwen.jsonl --st2 submission_lora_qwen.jsonl \\
        --st3 submission_gpt_st3.jsonl \\
        --out runs/submission_hybrid.jsonl

    # or, one source as the default for any tier not overridden:
    python src/combine_submissions.py public_data_dev/dev.jsonl \\
        --all submission_lora_qwen.jsonl --st3 submission_gpt_st3.jsonl \\
        --out runs/submission_hybrid.jsonl

Each source file must be a valid submission.jsonl (one line per instance:
{"instanceID": ..., "st1": ..., "st2": [...], "st3": [...]}) that carries every
instanceID in the target split, at least for the tier(s) it's assigned to. Sources
are looked up independently per tier and per instance, so nothing about how a tier
was produced needs to match another tier's source -- different models, different
prompts, encoder vs. generative decoding, doesn't matter, they're merged as plain
dicts keyed by instanceID.

Validates the merged file with starting_kit/check_submission.py, then -- if the
target split carries gold labels -- evaluates it with the same macro-F1 harness
every other baseline uses (src/baseline_gpt.py's evaluate()), plus each source's
own solo score on only the tier(s) it was assigned here, so a regression from
combining (e.g. a stale source file, or a tier that doesn't actually generalize
past its own eval run) is visible immediately rather than hiding inside one
blended mean_macro_f1.
"""
import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from common import evaluate, load_split, setup_logging  # noqa: E402
from common.predict_utils import log_evaluation  # noqa: E402

TIERS = ("st1", "st2", "st3")


def load_submission(path: str) -> dict:
    """instanceID -> record dict, as written by any of this repo's predict scripts."""
    records = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rec = json.loads(line)
                records[rec["instanceID"]] = rec
    return records


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", help="split whose instanceIDs (and gold labels, if present) drive the merge, "
                                    "e.g. public_data_dev/dev.jsonl")
    ap.add_argument("--all", dest="default_source",
                     help="submission file to use for any tier not given its own --st1/--st2/--st3 override")
    ap.add_argument("--st1", help="submission file to pull st1 from")
    ap.add_argument("--st2", help="submission file to pull st2 from")
    ap.add_argument("--st3", help="submission file to pull st3 from")
    ap.add_argument("--out", default=os.path.join("runs", "submission_hybrid.jsonl"))
    args = ap.parse_args()

    sources = {"st1": args.st1 or args.default_source,
               "st2": args.st2 or args.default_source,
               "st3": args.st3 or args.default_source}
    active_tiers = [t for t in TIERS if sources[t]]
    if not active_tiers:
        raise SystemExit("no source given for any tier -- pass --all and/or --st1/--st2/--st3")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log = setup_logging("runs", "combine_submissions", "hybrid", timestamp)
    log.info(f"sources: st1<-{sources['st1']}  st2<-{sources['st2']}  st3<-{sources['st3']}")

    cache = {}
    for path in set(sources.values()):
        if path:
            cache[path] = load_submission(path)
            log.info(f"loaded {len(cache[path])} predictions from {path}")

    instances = list(load_split(args.target))
    predictions, gold = [], []
    missing = defaultdict(list)
    for inst in instances:
        iid = inst["instanceID"]
        pred = {"instanceID": iid}
        for tier in active_tiers:
            record = cache[sources[tier]].get(iid)
            if record is None or tier not in record:
                missing[tier].append(iid)
                continue
            pred[tier] = record[tier]
        predictions.append(pred)
        if inst.get("labels"):
            gold.append(inst["labels"])

    for tier, iids in missing.items():
        raise SystemExit(f"{sources[tier]} is missing {tier} for {len(iids)} target instance(s), "
                          f"e.g. {iids[:5]} -- regenerate that source over the full target split")

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        for pred in predictions:
            f.write(json.dumps(pred) + "\n")
    log.info(f"wrote {len(predictions)} merged predictions to {args.out}")

    checker = os.path.join(os.path.dirname(__file__), "..", "starting_kit", "check_submission.py")
    result = subprocess.run([sys.executable, checker, args.out, args.target])
    if result.returncode != 0:
        raise SystemExit(f"{args.out} failed validation")

    if gold and len(gold) == len(predictions):
        metrics = evaluate(gold, predictions, tiers=tuple(active_tiers))
        log.info("=== combined submission ===")
        log_evaluation(log, metrics)

        for path in cache:
            tiers_from_this_source = tuple(t for t in active_tiers if sources[t] == path)
            solo_preds = [cache[path][inst["instanceID"]] for inst in instances]
            solo_metrics = evaluate(gold, solo_preds, tiers=tiers_from_this_source)
            log.info(f"=== solo (as scored on {tiers_from_this_source}): {path} ===")
            log_evaluation(log, solo_metrics)
    else:
        log.info("target has no gold labels (or only partial coverage) -- skipping evaluation")


if __name__ == "__main__":
    main()
