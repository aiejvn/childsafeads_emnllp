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
the segment is commercial and that the channel is child-facing; do not re-assess either. Predict \
three sub-tasks.

ST1 - commercial type (exactly one label). Decide from what the buyer receives, not how it is \
marketed:
- physical_goods: tangible items shipped/handed to the buyer
- digital_content_or_services: content/services delivered digitally, no physical delivery, no \
human performance (games, apps, software, streaming, in-game currency)
- physical_services: services performed by humans or in the physical world (therapy, haircuts, \
travel, live events, repairs)
- none: no identifiable commercial offer
- other: genuinely none of the above

ST2 - product category (one or more labels): toys, food, apps, hardware_electronics, fashion, \
health, education, financial, gambling, gambling_adjacent, creator_community, other.

ST3 - compliance risk flags (one or more labels). Emit every flag that applies:
- undisclosed_advertising: the commercial nature is not identified anywhere available to the \
viewer (not spoken, not in the description, not via the platform's paid-promotion label)
- inadequate_disclosure: a disclosure exists but is not clear and comprehensible to a child \
(buried, adult jargon, etc.) -- mutually exclusive with undisclosed_advertising
- direct_exhortation: a direct appeal to children to buy, or to get their parents to buy, using \
personal/hyped/pressuring/parasocial language ("if you love us, buy it", pleading, urgency \
aimed at the viewer). Plain transactional instructions ("link in description", "use my code") \
are NOT exhortation. If genuinely ambiguous, do not flag.
- misleading_claim: unsubstantiated or high-risk claims about characteristics, performance, \
results, or price; includes any health/weight/fitness/skincare/supplement claim aimed at children
- age_restricted_or_prohibited_product: alcohol, tobacco/vaping, gambling, weapons, or similar
- hfss_food_marketing: clear cases of food high in fat, salt or sugar (energy drinks, \
confectionery, fast food)
- no_flag: commercial content that appears compliant -- must stand alone, no other flags
- insufficient_context: segment too short/ambiguous to assess -- must stand alone, no other flags

Base every judgment only on the text given. Respond with the structured prediction only."""


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
    with open(args.out, "w", encoding="utf-8") as f:
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
    log.info(f"wrote {len(predictions)} predictions to {args.out}")

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
