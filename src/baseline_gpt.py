"""GPT baseline: predicts ST1, ST2, ST3 with GPT via LangChain structured output.

Requires OPENAI_API_KEY in the environment (or a .env file next to this script).

Usage:
    python baseline_gpt.py ../public_data_dev/dev.jsonl --out submission_gpt.jsonl
    python baseline_gpt.py ../public_data_dev/dev.jsonl --out submission_gpt.jsonl --sample-size 20  # smoke test

Prints macro-F1 for st1/st2/st3, the family-level st3 macro-F1, and their mean,
whenever the target split carries gold "labels" (train/dev, not the withheld test set).
"""
import argparse
import json
import logging
import os
import random
import sys
from datetime import datetime
from typing import List, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "starting_kit"))
from check_submission import ST1, ST2, ST3
from load_data import full_context, load_split, transcript_only

from dotenv import load_dotenv
load_dotenv()

LABELS_TAXONOMY_PATH = os.path.join(
    os.path.dirname(__file__), "..", "public_data_dev", "labels_taxonomy.md"
)
with open(LABELS_TAXONOMY_PATH, encoding="utf-8") as _f:
    LABELS_TAXONOMY = _f.read()

ST1_LABELS = sorted(ST1)
ST2_LABELS = sorted(ST2)
ST3_LABELS = sorted(ST3)

ST3_FAMILY = {
    "undisclosed_advertising": "disclosure",
    "inadequate_disclosure": "disclosure",
    "direct_exhortation": "content",
    "misleading_claim": "content",
    "age_restricted_or_prohibited_product": "product",
    "hfss_food_marketing": "product",
    "no_flag": "housekeeping",
    "insufficient_context": "housekeeping",
}
FAMILY_LABELS = ["disclosure", "content", "product", "housekeeping"]
assert set(ST3_FAMILY) == ST3

SYSTEM_PROMPT = """You are a compliance analyst at an authority monitoring commercial content \
that reaches minors on video platforms. You are given one sponsored segment (transcript, the \
host video's metadata, and the product page its description links to). It is a GIVEN FACT that \
the segment is commercial and that the channel is child-facing; do not re-assess either.

Predict three sub-tasks -- ST1 (commercial type, exactly one label), ST2 (product category, one \
or more labels), and ST3 (compliance risk flags, one or more labels) -- using the label taxonomy \
below, which gives the full definitions, examples, and legal basis for each label. Base every \
judgment only on the text given. Respond with the structured prediction only.

""" + LABELS_TAXONOMY


class Prediction(BaseModel):
    st1: Literal[tuple(ST1_LABELS)] = Field(description="Single commercial-type label")
    st2: List[Literal[tuple(ST2_LABELS)]] = Field(description="One or more product-category labels")
    st3: List[Literal[tuple(ST3_LABELS)]] = Field(description="One or more compliance risk flags")


def sanitize_st3(flags: List[str]) -> List[str]:
    """Enforce the 'no_flag'/'insufficient_context' stand-alone rule."""
    standalone = [f for f in flags if f in ("no_flag", "insufficient_context")]
    if standalone and len(flags) > 1:
        return [standalone[0]]
    return flags or ["insufficient_context"]


def setup_logging(log_dir: str, method: str, model: str) -> logging.Logger:
    """Log everything (config, warnings, gold-label inventory, results) to console + a run file."""
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(log_dir, f"run_{timestamp}_{method}_{model}.log")

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(fmt)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"logging to {log_path}")
    return logger


def log_gold_label_inventory(logger: logging.Logger, gold: List[dict]) -> None:
    """Log the distinct gold labels observed in this run, one line per tier."""
    st1_seen = {g["st1"] for g in gold}
    st2_seen = {label for g in gold for label in g["st2"]}
    st3_seen = {label for g in gold for label in g["st3"]}
    logger.info("=== Distinct gold labels observed, by tier ===")
    logger.info(f"[ST1 - commercial type]     {sorted(st1_seen)}")
    logger.info(f"[ST2 - product category]    {sorted(st2_seen)}")
    logger.info(f"[ST3 - compliance flags]    {sorted(st3_seen)}")


def build_messages(instance: dict, context: str) -> list:
    text = full_context(instance) if context == "full" else transcript_only(instance)
    return [SystemMessage(SYSTEM_PROMPT), HumanMessage(f"SEGMENT DATA:\n\n{text}")]


def macro_f1(y_true: List[list], y_pred: List[list], labels: List[str]) -> float:
    """Macro-F1 over multi-label sets, averaged across `labels`."""
    scores = []
    # Iterate over labels to avoid having to O(n^2) loop over every y_true and check if it is in y_pred (or vice-versa)
    for label in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if label in t and label in p)
        fp = sum(1 for t, p in zip(y_true, y_pred) if label not in t and label in p)
        fn = sum(1 for t, p in zip(y_true, y_pred) if label in t and label not in p)
        if tp == 0 and fp == 0 and fn == 0:
            continue  # label absent from both gold and predictions; skip like sklearn does
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall + 10e-6)
        scores.append(f1)
    return sum(scores) / len(scores) if scores else 0.0


def prediction_errors(gold: dict, pred: dict) -> dict:
    """Diff a prediction against gold, tier by tier. Returns {} if fully correct;
    otherwise one entry per wrong tier describing exactly what was wrong."""
    errors = {}
    if pred["st1"] != gold["st1"]:
        errors["st1"] = {"gold": gold["st1"], "pred": pred["st1"]}
    for tier in ("st2", "st3"):
        missing = sorted(set(gold[tier]) - set(pred[tier]))  # gold labels the prediction missed
        extra = sorted(set(pred[tier]) - set(gold[tier]))    # predicted labels not in gold
        if missing or extra:
            errors[tier] = {"missing": missing, "extra": extra}
    return errors


def evaluate(gold: List[dict], pred: List[dict]) -> dict:
    st1_f1 = macro_f1([[g["st1"]] for g in gold], [[p["st1"]] for p in pred], ST1_LABELS)
    st2_f1 = macro_f1([g["st2"] for g in gold], [p["st2"] for p in pred], ST2_LABELS)
    st3_f1 = macro_f1([g["st3"] for g in gold], [p["st3"] for p in pred], ST3_LABELS)
    fam = lambda flags: [ST3_FAMILY[f] for f in flags]
    st3_fam_f1 = macro_f1([fam(g["st3"]) for g in gold], [fam(p["st3"]) for p in pred], FAMILY_LABELS)
    return {
        "st1_macro_f1": st1_f1,
        "st2_macro_f1": st2_f1,
        "st3_macro_f1": st3_f1,
        "st3_family_macro_f1": st3_fam_f1,
        "mean_macro_f1": (st1_f1 + st2_f1 + st3_f1) / 3,
    }

# From repo root:
# python src/baseline_gpt.py public_data_dev/dev.jsonl --sample-size 10 

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="split file to predict on, e.g. dev.jsonl")
    ap.add_argument("--out", default="submission_gpt.jsonl", help="output predictions jsonl")
    ap.add_argument("--error-out", default="submission_gpt_error.jsonl",
                     help="instances with a wrong st1/st2/st3 prediction, with a diff against gold")
    ap.add_argument("--model", default="gpt-5.4")
    ap.add_argument("--context", choices=["transcript", "full"], default="full",
                     help="how much of the instance to show the model")
    ap.add_argument("--sample-size", type=int, default=None,
                     help="only run on a random sample of N instances (seeded, for smoke tests)")
    ap.add_argument("--max-concurrency", type=int, default=8)
    args = ap.parse_args()

    log = setup_logging("runs", args.context, args.model)
    log.info(f"config: target={args.target} model={args.model} context={args.context} "
             f"sample_size={args.sample_size} max_concurrency={args.max_concurrency} out={args.out}")

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("Set OPENAI_API_KEY in the environment (or a .env file) first.")

    instances = list(load_split(args.target))
    if args.sample_size:
        instances = random.Random(42).sample(instances, min(args.sample_size, len(instances)))

    llm = ChatOpenAI(model=args.model, temperature=0).with_structured_output(
        Prediction, method="json_schema", strict=True
    )
    batch_inputs = [build_messages(inst, args.context) for inst in instances]

    # Parallel batch requests to AI API
    # Returns output in a list, each elem maps to 1 query
    results = llm.batch(batch_inputs, config={"max_concurrency": args.max_concurrency},
                         return_exceptions=True)

    predictions, gold = [], []
    n_errors = 0
    with open(args.out, "w", encoding="utf-8") as f, \
         open(args.error_out, "w", encoding="utf-8") as f_err:
        for inst, result in zip(instances, results):
            if isinstance(result, Exception):
                log.warning(f"{inst['instanceID']} failed ({result})")
                pred = {"st1": "other", "st2": [], "st3": [f"error:{result}"]}
            else:
                pred = {"st1": result.st1, "st2": result.st2, "st3": sanitize_st3(result.st3)}
            predictions.append(pred)
            f.write(json.dumps({"instanceID": inst["instanceID"], **pred}) + "\n")
            if inst.get("labels"):
                gold.append(inst["labels"])
                errors = prediction_errors(inst["labels"], pred)
                if errors:
                    n_errors += 1
                    f_err.write(json.dumps({
                        "instanceID": inst["instanceID"], "gold": inst["labels"],
                        "pred": pred, "errors": errors,
                    }) + "\n")
    log.info(f"wrote {len(predictions)} predictions to {args.out}")
    if gold:
        log.info(f"wrote {n_errors} misclassified instance(s) to {args.error_out}")

    if len(gold) == len(predictions) and gold:
        log_gold_label_inventory(log, gold)
        metrics = evaluate(gold, predictions)
        log.info("Evaluation:")
        for k, v in metrics.items():
            log.info(f"  {k}: {v:.3f}")
    else:
        log.info("target has no gold labels (or a partial mismatch) -- skipping evaluation")


if __name__ == "__main__":
    main()
