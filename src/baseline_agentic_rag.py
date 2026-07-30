"""Agentic-RAG baseline: predicts ST1, ST2, ST3 with GPT, grounded in legal/case-law
material retrieved from OpenJustice's hosted vector DB via an iterative
query/retrieve/sufficiency-check loop.

The retrieval loop is imported and reused unmodified from the oj-eval submodule
(Flowchart.agentic_retrieval_execution in oj-eval/src/flowchart.py) and hits the same
backend as oj-eval/src/flowcharts/public_oj_llm_agentic_rag.json: generate a query, search
OpenJustice's file/vector store (api.openjustice.ai/files/search), ask the LLM
whether the retrieved material is sufficient, and repeat. Only the query_gen/sufficiency
instructions are retargeted here, from "legal question" framing to child-safety ad
compliance framing. The final classification call uses this repo's strict Pydantic
Prediction schema (as in baseline_gpt.py) so the output is guaranteed to be a valid,
label-constrained submission.

Requires OPENAI_API_KEY and OJ_API_KEY in the environment (or a .env file next to this
script) -- the former for classification, the latter for the OpenJustice retrieval API.

Usage:
    python baseline_agentic_rag.py ../public_data_dev/dev.jsonl --out submission_agentic_rag.jsonl
    python baseline_agentic_rag.py ../public_data_dev/dev.jsonl --sample-size 20  # smoke test

Prints the same macro-F1 metrics as baseline_gpt.py whenever the target split carries gold
"labels", and writes misclassified instances (with a diff against gold) to --error-out.
"""
import argparse
import json
import os
import random
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

sys.path.insert(0, os.path.dirname(__file__))
from baseline_gpt import (
    SYSTEM_PROMPT, Prediction, sanitize_st3, setup_logging,
    log_gold_label_inventory, evaluate, prediction_errors,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "starting_kit"))
from load_data import full_context, load_split, transcript_only

# oj-eval submodule: reuse its agentic-retrieval loop and OpenJustice vector-DB backend as-is.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "oj-eval", "src"))
import flowchart as oj_flowchart

from dotenv import load_dotenv
load_dotenv()

QUERY_GEN_INSTRUCTIONS = """You are a compliance research assistant monitoring commercial \
content that reaches minors on video platforms. Generate a focused search query to retrieve \
legal/regulatory grounding (statutes, case law, codes of conduct) most relevant to assessing \
the commercial segment below for child-safety compliance risks: undisclosed advertising, \
inadequate disclosure, direct exhortation, misleading claims, age-restricted products, HFSS \
food marketing.

Segment:
[input]

Write a 1-3 sentence search query using precise legal/regulatory terminology, focused on the \
specific compliance issue(s) this segment raises."""

SUFFICIENCY_INSTRUCTIONS = """You are deciding whether the legal/regulatory material \
retrieved so far is sufficient to fully assess the compliance risk flags for the segment \
below, or whether a more targeted search is needed.

Segment:
[input]

Material retrieved so far:
[ACCUMULATED_RESULTS]

Ask yourself: are all plausible compliance risk categories for this segment covered? Is \
there a gap in the applicable law or guidance?

If sufficient, set done to true and leave next_query empty.
If not, identify the specific gap and write a targeted query to address it."""


def build_agentic_node(max_iterations: int, top_k: int) -> "oj_flowchart.FlowchartTask":
    """Same node config/backend as the AGENTIC_RAG node in
    oj-eval/src/flowcharts/public_oj_llm_agentic_rag.json (OpenJustice's hosted vector DB
    via api.openjustice.ai/files/search); only the instructions are retargeted from
    legal Q&A to ad-compliance classification."""
    # oj-eval's db_retrieval parses k from the *last character* of output_strat
    # ("top5" -> 5), so it only supports single-digit k -- see globals.py's
    # `elif output_strat.startswith('top'): # top k, where k is < 10`. Clamp here
    # rather than silently mis-parsing "top12" as k=2.
    output_strat_k = min(top_k, 9)
    return oj_flowchart.FlowchartTask({
        "type": "agentic_retrieval",
        "name": "AGENTIC_RAG",
        "max_iterations": max_iterations,
        "retrieval": {
            "url": "api.openjustice.ai",
            "endpoint": "/files/search",
            "api_key": "OJ_API_KEY",
            "metadata": {
                "output_strat": f"top{output_strat_k}",
                "dedup_key": "fileId",
                "query": {"scope": "all", "limit": top_k},
            },
        },
        "query_gen_instructions": QUERY_GEN_INSTRUCTIONS,
        "sufficiency_instructions": SUFFICIENCY_INSTRUCTIONS,
    })



def build_final_messages(segment_text: str, grounding_text: str) -> list:
    system = (f"{SYSTEM_PROMPT}\n\nYou are additionally given legal/regulatory grounding "
              f"retrieved for this segment via an agentic retrieval loop over OpenJustice's "
              f"legal corpus. Use it to inform ST1, ST2, and ST3 wherever it bears on the "
              f"classification -- e.g. regulatory definitions of a product category or "
              f"age-restricted/HFSS status can affect ST2, and statutory definitions of "
              f"advertising/commercial content can affect ST1, not just ST3's compliance "
              f"flags and their severity. Base the final decision on the segment content "
              f"itself, not the grounding alone.\n\n"
              f"RETRIEVED LEGAL GROUNDING:\n{grounding_text}")
    return [SystemMessage(system), HumanMessage(f"SEGMENT DATA:\n\n{segment_text}")]


def process_instance(inst: dict, context: str, flowchart_engine, node, llm_final, log) -> dict:
    """Returns {"pred": ..., "retrieval": ...} -- pred is the st1/st2/st3 prediction written to
    --out; retrieval is this instance's agentic-retrieval trace (queries, doc counts, grounding
    text) written to the runs/rag/ JSON dump."""
    text = full_context(inst) if context == "full" else transcript_only(inst)
    retrieval_record = {"instanceID": inst["instanceID"]}
    try:
        local_input = {"input": oj_flowchart.FlowchartTaskResult(value=text, executionDetails={})}
        retrieval = flowchart_engine.agentic_retrieval_execution(node, local_input)
        log.debug(f"{inst['instanceID']} retrieval: {retrieval.executionDetails['total_items']} "
                  f"docs over {retrieval.executionDetails['iterations']} iteration(s)")
        retrieval_record.update({
            "iterations": retrieval.executionDetails.get("iterations"),
            "total_items": retrieval.executionDetails.get("total_items"),
            "iter_evals": retrieval.executionDetails.get("iter_evals"),
            "grounding": retrieval.value,
        })
        result = llm_final.invoke(build_final_messages(text, retrieval.value))
        pred = {"st1": result.st1, "st2": result.st2, "st3": sanitize_st3(result.st3)}
    except Exception as e:
        log.warning(f"{inst['instanceID']} failed ({e})")
        pred = {"st1": "other", "st2": [], "st3": [f"error:{e}"]}
        retrieval_record["error"] = str(e)
    return {"pred": pred, "retrieval": retrieval_record}


# From repo root:
# python src/baseline_agentic_rag.py public_data_dev/dev.jsonl --sample-size 10
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="split file to predict on, e.g. dev.jsonl")
    ap.add_argument("--out", default="submission_agentic_rag.jsonl", help="output predictions jsonl")
    ap.add_argument("--error-out", default="submission_agentic_rag_error.jsonl",
                     help="instances with a wrong st1/st2/st3 prediction, with a diff against gold")
    ap.add_argument("--model", default="gpt-5.4")
    ap.add_argument("--context", choices=["transcript", "full"], default="full",
                     help="how much of the instance to show the model")
    ap.add_argument("--sample-size", type=int, default=None,
                     help="only run on a random sample of N instances (seeded, for smoke tests)")
    ap.add_argument("--max-concurrency", type=int, default=8,
                     help="instances processed concurrently (each runs its own retrieval loop)")
    ap.add_argument("--max-iterations", type=int, default=3,
                     help="max query/retrieve/sufficiency-check rounds per instance")
    ap.add_argument("--top-k", type=int, default=5, choices=range(1, 10), metavar="[1-9]",
                     help="documents retrieved per query (oj-eval's output_strat parsing "
                          "only supports single-digit k)")
    args = ap.parse_args()

    log = setup_logging("runs", f"agentic_rag_{args.context}", args.model)

    # oj_flowchart.logger ("flowchart") is a separate named logger from ours ("baseline_gpt")
    # with no handlers of its own, so its per-iteration [Agentic] logs would otherwise vanish
    # into the unconfigured root logger. Route it through the same file+console handlers so
    # the retrieval loop's logging lands in this run's log file.
    oj_flowchart.logger.handlers = log.handlers
    oj_flowchart.logger.setLevel(log.level)
    oj_flowchart.logger.propagate = False

    log.info(f"config: target={args.target} model={args.model} context={args.context} "
             f"sample_size={args.sample_size} max_concurrency={args.max_concurrency} "
             f"max_iterations={args.max_iterations} top_k={args.top_k} out={args.out}")

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("Set OPENAI_API_KEY in the environment (or a .env file) first.")
    if not os.environ.get("OJ_API_KEY"):
        raise SystemExit("Set OJ_API_KEY in the environment (or a .env file) first "
                          "-- required to query OpenJustice's retrieval API.")

    instances = list(load_split(args.target))
    if args.sample_size:
        instances = random.Random(42).sample(instances, min(args.sample_size, len(instances)))

    oj_flowchart.init(args.model, t=0)  # sets oj-eval's shared llm used by the retrieval loop
    flowchart_engine = oj_flowchart.Flowchart([])
    node = build_agentic_node(args.max_iterations, args.top_k)

    llm_final = ChatOpenAI(model=args.model, temperature=0).with_structured_output(
        Prediction, method="json_schema", strict=True
    )

    with ThreadPoolExecutor(max_workers=args.max_concurrency) as pool:
        outcomes = list(pool.map(
            lambda inst: process_instance(inst, args.context, flowchart_engine, node,
                                           llm_final, log),
            instances,
        ))
    predictions = [o["pred"] for o in outcomes]
    retrieval_records = [o["retrieval"] for o in outcomes]

    rag_dir = "runs/rag"
    os.makedirs(rag_dir, exist_ok=True)
    rag_path = os.path.join(rag_dir, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(rag_path, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "target": args.target,
                "model": args.model,
                "context": args.context,
                "sample_size": args.sample_size,
                "max_concurrency": args.max_concurrency,
                "max_iterations": args.max_iterations,
                "top_k": args.top_k,
                "n_instances": len(instances),
            },
            "results": retrieval_records,
        }, f, indent=2)
    log.info(f"wrote {len(retrieval_records)} retrieval trace(s) to {rag_path}")

    gold = []
    gold_predictions = []
    n_errors = 0
    with open(args.out, "w", encoding="utf-8") as f, \
         open(args.error_out, "w", encoding="utf-8") as f_err:
        for inst, pred, retrieval in zip(instances, predictions, retrieval_records):
            f.write(json.dumps({"instanceID": inst["instanceID"], **pred}) + "\n")
            if not inst.get("labels"):
                continue
            if "error" in retrieval:
                print(f"skipped: {inst['instanceID']}")
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
    log.info(f"wrote {len(predictions)} predictions to {args.out}")

    if gold:
        log.info(f"wrote {n_errors} misclassified instance(s) to {args.error_out}")
        log_gold_label_inventory(log, gold)
        metrics = evaluate(gold, gold_predictions)
        log.info("Evaluation:")
        for k, v in metrics.items():
            log.info(f"  {k}: {v:.3f}")
    else:
        log.info("target has no gold labels -- skipping evaluation")


if __name__ == "__main__":
    main()
