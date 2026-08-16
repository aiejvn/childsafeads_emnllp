"""Dialog-flow baseline: predicts ST1, ST2, ST3 by running each instance through the
OpenJustice dialog flow exported to emnllp-dialog-flow-dialog-flow.json (repo root),
then normalizing the flow's own conclusions into this repo's strict st1/st2/st3
submission schema.

The dialog flow does its own reasoning (assessability check, commercial type, product
categories, disclosure/claims, product risk) via OpenJustice's hosted dialog-flow-executions
API -- see oj-eval/src/flowchart.py's df_execution(). The export doesn't carry the flow's
id (OpenJustice only shows that in the platform's edit URL), so it must be supplied via
--df-id or the OJ_EMNLLP_DF_ID env var.

The flow's final output is parsed as JSON first (its outcome nodes are configured with
responseType "structured"). If that fails -- not JSON, or the labels it contains don't
validate against this repo's label sets (e.g. the flow's Insufficient Context branch emits
"insufficient_context" for ST1, which isn't a valid ST1 label) -- a follow-up GPT
structured-output call reads the flow's own stated conclusions off its raw output and maps
them onto the Prediction schema from baseline_gpt.py. Either way, the dialog flow does the
actual classification; the fallback only normalizes its output, it does not re-classify.

Requires OPENAI_API_KEY (for the fallback extraction call) and OJ_API_KEY (for the
dialog-flow API) in the environment (or a .env file next to this script).

Writes predictions to runs/submission_df_<timestamp>.jsonl.

Usage:
    python baseline_df.py ../public_data_dev/dev.jsonl --df-id <uuid>
    python baseline_df.py ../public_data_dev/dev.jsonl --df-id <uuid> --sample-size 20  # smoke test

Prints the same macro-F1 metrics as baseline_gpt.py whenever the target split carries gold
"labels", and writes misclassified instances (with a diff against gold) to --error-out.
"""
import argparse
import json
import os
import random
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

sys.path.insert(0, os.path.dirname(__file__))
from baseline_gpt import (
    ST1, ST2, ST3, ST1_LABELS, ST2_LABELS, ST3_LABELS, Prediction, sanitize_st3,
    setup_logging, log_gold_label_inventory, evaluate, prediction_errors,
    CONTEXT_CHOICES, no_product_page,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "starting_kit"))
from load_data import full_context, load_split, transcript_only

# oj-eval submodule: reuse its dialog-flow execution loop and OpenJustice backend as-is.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "oj-eval", "src"))
import flowchart as oj_flowchart

from dotenv import load_dotenv
load_dotenv()

EXTRACTION_SYSTEM_PROMPT = """You are normalizing the output of a compliance-classification \
dialog flow into a strict labeled schema. You are given the segment that was classified and \
the dialog flow's own final output (its stated ST1/ST2/ST3 conclusions and rationale, in \
whatever free-text or structured form it used). Read off the flow's own conclusions -- do \
not re-classify the segment yourself -- and map them onto the fixed label sets: ST1 is \
exactly one of {st1_labels}; ST2 is one or more of {st2_labels}; ST3 is one or more of \
{st3_labels}. If the flow's own ST1 value is not one of the allowed ST1 labels (e.g. it says \
"insufficient_context" for ST1, which is not a valid ST1 label), fall back to "other" for \
ST1 and make sure "insufficient_context" is reflected in ST3 instead."""


def build_extraction_messages(segment_text: str, df_output: str) -> list:
    system = EXTRACTION_SYSTEM_PROMPT.format(
        st1_labels=ST1_LABELS, st2_labels=ST2_LABELS, st3_labels=ST3_LABELS,
    )
    human = f"SEGMENT:\n\n{segment_text}\n\nDIALOG FLOW OUTPUT:\n\n{df_output}"
    return [SystemMessage(system), HumanMessage(human)]


def _normalize_labels(value, allowed: set) -> list:
    """Pull every allowed label mentioned in `value` (str, list, or None), tolerant of
    underscore/space variants (e.g. "misleading claim" still matches "misleading_claim")."""
    if value is None:
        return []
    items = value if isinstance(value, list) else [value]
    text = " ".join(str(v) for v in items).lower()
    return [label for label in allowed if label in text or label.replace("_", " ") in text]


def parse_df_json_output(raw: str):
    """Try to read the dialog flow's final output as JSON with st1/st2/st3-shaped keys.
    Returns None if it isn't JSON, or the labels it contains don't validate -- callers
    should fall back to the LLM extraction pass in that case."""
    try:
        obj = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(obj, dict):
        return None
    lower = {k.lower(): v for k, v in obj.items()}

    st1_candidates = _normalize_labels(lower.get("st1"), ST1)
    st2 = _normalize_labels(lower.get("st2"), ST2)
    st3 = _normalize_labels(lower.get("st3"), ST3)
    if not st1_candidates or not st3:
        return None  # not enough to trust; let the LLM fallback handle it
    return {"st1": st1_candidates[0], "st2": st2, "st3": sanitize_st3(st3)}


def build_df_node(df_id: str, base_url: str) -> "oj_flowchart.FlowchartTask":
    return oj_flowchart.FlowchartTask({
        "type": "dialog_flow",
        "name": "EMNLLP_DIALOG_FLOW",
        "base_url": base_url,
        "df_id": df_id,
        "api_key": "OJ_API_KEY",
        "inline_docs": True,
    })


def process_instance(inst: dict, context: str, flowchart_engine, node, model, llm_extract, log) -> dict:
    """Returns {"pred": ..., "df": ...} -- pred is the st1/st2/st3 prediction written to
    --out; df is this instance's dialog-flow execution trace written to the runs/df/ dump."""
    if context == "full":
        text = full_context(inst)
    elif context == "no_product_page":
        text = no_product_page(inst)
    else:
        text = transcript_only(inst)
    df_record = {"instanceID": inst["instanceID"]}
    try:
        local_input = {
            "input": oj_flowchart.FlowchartTaskResult(value=text, executionDetails={}),
            "supporting_docs": oj_flowchart.FlowchartTaskResult(value=[], executionDetails={}),
        }
        result = flowchart_engine.df_execution(node, local_input, model)
        details = result.executionDetails
        df_record.update({
            "status": details.get("status"),
            "facts": details.get("facts"),
            "final_output": result.value,
        })
        if details.get("status") != "completed":
            raise RuntimeError(f"dialog flow did not complete (status={details.get('status')}, "
                                f"error={details.get('error')})")

        pred = parse_df_json_output(result.value)
        df_record["extraction_fallback"] = pred is None
        if pred is None:
            extracted = llm_extract.invoke(build_extraction_messages(text, result.value))
            pred = {"st1": extracted.st1, "st2": extracted.st2, "st3": sanitize_st3(extracted.st3)}
    except Exception as e:
        log.warning(f"{inst['instanceID']} failed ({e})")
        pred = {"st1": "other", "st2": [], "st3": [f"error:{e}"]}
        df_record["error"] = str(e)
    return {"pred": pred, "df": df_record}


# From repo root:
# python src/baseline_df.py public_data_dev/dev.jsonl --df-id <uuid> --sample-size 10
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="split file to predict on, e.g. dev.jsonl")
    ap.add_argument("--df-id", default=os.environ.get("OJ_EMNLLP_DF_ID"),
                     help="emnllp-dialog-flow's id (from its OpenJustice edit URL); "
                          "defaults to the OJ_EMNLLP_DF_ID env var")
    ap.add_argument("--base-url", default="https://api.staging.openjustice.ai")
    ap.add_argument("--model", default="gpt-5.4",
                     help="model the dialog flow runs on, and the fallback extraction model")
    ap.add_argument("--context", choices=CONTEXT_CHOICES, default="full",
                     help="how much of the instance to show the dialog flow. no_product_page drops "
                          "the linked page entirely -- transcript + video title/description/disclosure only")
    ap.add_argument("--sample-size", type=int, default=None,
                     help="only run on a random sample of N instances (seeded, for smoke tests)")
    ap.add_argument("--max-concurrency", type=int, default=8)
    args = ap.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log = setup_logging("runs", f"df_{args.context}", args.model, timestamp)
    out = os.path.join("runs", f"submission_df_{timestamp}.jsonl")
    error_out = os.path.join("runs", f"submission_df_error_{timestamp}.jsonl")
    log.info(f"config: target={args.target} model={args.model} context={args.context} "
             f"base_url={args.base_url} sample_size={args.sample_size} "
             f"max_concurrency={args.max_concurrency} out={out}")

    # oj_flowchart.logger ("flowchart") is a separate named logger from ours
    # ("baseline_gpt") with no handlers of its own, so its per-call debug/warning logs
    # (including raw API responses on a malformed reply) would otherwise vanish into
    # the unconfigured root logger. Route it through the same file+console handlers.
    oj_flowchart.logger.handlers = log.handlers
    oj_flowchart.logger.setLevel(log.level)
    oj_flowchart.logger.propagate = False

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("Set OPENAI_API_KEY in the environment (or a .env file) first.")
    if not os.environ.get("OJ_API_KEY"):
        raise SystemExit("Set OJ_API_KEY in the environment (or a .env file) first "
                          "-- required to run the OpenJustice dialog flow.")
    if not args.df_id:
        raise SystemExit("Set --df-id or OJ_EMNLLP_DF_ID -- the emnllp-dialog-flow export "
                          "doesn't carry its own id; find it in the flow's OpenJustice edit URL.")

    instances = list(load_split(args.target))
    if args.sample_size:
        instances = random.Random(42).sample(instances, min(args.sample_size, len(instances)))

    flowchart_engine = oj_flowchart.Flowchart([])
    node = build_df_node(args.df_id, args.base_url)

    llm_extract = ChatOpenAI(model=args.model, temperature=0).with_structured_output(
        Prediction, method="json_schema", strict=True
    )

    with ThreadPoolExecutor(max_workers=args.max_concurrency) as pool:
        outcomes = list(pool.map(
            lambda inst: process_instance(inst, args.context, flowchart_engine, node,
                                           args.model, llm_extract, log),
            instances,
        ))
    predictions = [o["pred"] for o in outcomes]
    df_records = [o["df"] for o in outcomes]

    df_dir = "runs/df"
    os.makedirs(df_dir, exist_ok=True)
    df_path = os.path.join(df_dir, f"{timestamp}.json")
    with open(df_path, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "target": args.target,
                "model": args.model,
                "context": args.context,
                "df_id": args.df_id,
                "base_url": args.base_url,
                "sample_size": args.sample_size,
                "max_concurrency": args.max_concurrency,
                "n_instances": len(instances),
            },
            "results": df_records,
        }, f, indent=2)
    log.info(f"wrote {len(df_records)} dialog-flow trace(s) to {df_path}")

    gold = []
    gold_predictions = []
    n_errors = 0
    with open(out, "w", encoding="utf-8") as f, \
         open(error_out, "w", encoding="utf-8") as f_err:
        for inst, pred, df_record in zip(instances, predictions, df_records):
            f.write(json.dumps({"instanceID": inst["instanceID"], **pred}) + "\n")
            if not inst.get("labels"):
                continue
            if "error" in df_record:
                log.warning(f"skipped (dialog flow error): {inst['instanceID']}")
                continue
            gold.append(inst["labels"])
            gold_predictions.append(pred)
            errors = prediction_errors(inst["labels"], pred)
            if errors:
                n_errors += 1
                f_err.write(json.dumps({
                    "instanceID": inst["instanceID"], "gold": inst["labels"],
                    "pred": pred, "errors": errors,
                }) + "\n")
    log.info(f"wrote {len(predictions)} predictions to {out}")

    canonical = "submission_df.jsonl"
    shutil.copyfile(out, canonical)
    log.info(f"copied predictions to {canonical} (canonical submission file)")

    if gold:
        log.info(f"wrote {n_errors} misclassified instance(s) to {error_out}")
        log_gold_label_inventory(log, gold)
        metrics = evaluate(gold, gold_predictions)
        log.info("Evaluation:")
        for k, v in metrics.items():
            log.info(f"  {k}: {v:.3f}")
    else:
        log.info("target has no gold labels -- skipping evaluation")


if __name__ == "__main__":
    main()
