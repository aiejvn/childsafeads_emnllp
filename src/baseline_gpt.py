"""GPT baseline: predicts ST1, ST2, ST3 with GPT via LangChain structured output.

Requires OPENAI_API_KEY in the environment (or a .env file next to this script).

Writes predictions to runs/submission_gpt_<timestamp>.jsonl.

Usage:
    python baseline_gpt.py ../public_data_dev/dev.jsonl
    python baseline_gpt.py ../public_data_dev/dev.jsonl --sample-size 20  # smoke test
    python baseline_gpt.py ../public_data_dev/dev.jsonl --st3-only        # ST3 only, its own tuned prompt
    python baseline_gpt.py ../public_data_dev/dev.jsonl --st3-only --few-shot  # + hand-picked baked-in examples
    python baseline_gpt.py ../public_data_dev/dev.jsonl --st3-only --cot inline  # + inline reasoning field
    python baseline_gpt.py ../public_data_dev/dev.jsonl --lean-prompt --df-path ../emnllp-dialog-flow-dialog-flow.json

Prints macro-F1 for st1/st2/st3, the family-level st3 macro-F1, and their mean,
whenever the target split carries gold "labels" (train/dev, not the withheld test set).
--st3-only restricts prediction and scoring to st3 (no mean_macro_f1, since it blends all
three tiers) and writes to submission_gpt_st3.jsonl instead of the canonical
submission_gpt.jsonl. --lean-prompt and --df-path mirror the LoRA baselines' flags of the
same name, for a like-for-like comparison against them. --few-shot (st3-only only) appends
a FEW-SHOT EXAMPLES section to the system prompt with hand-picked, rubric-vetted train.jsonl
examples (baked in, not rescanned per run -- see GOLDEN_FEW_SHOT_EXAMPLES in st3_prompts.py)
for direct_exhortation, undisclosed_advertising, inadequate_disclosure, misleading_claim,
no_flag, and insufficient_context, pairing each label's definition with real evidence and a
one-line rationale. --cot (st3-only only) switches on chain-of-thought: "inline" adds a `reasoning`
field to the structured-output schema (one call, model reasons before committing to
labels); "flow" walks the local dialog-flow graph node by node (see st3_flow_executor.py).

This module is also imported as a shared library by several other baselines in this
directory (baseline_df.py, baseline_agentic_rag.py, baseline_mlp_pytorch.py,
baseline_two_label_focus.py, baseline_per_label_ensemble.py, baseline_decision_tree.py,
disclosure_pipeline.py) and by common/__init__.py -- the actual prompt/schema/scoring
content lives in st3_prompts.py / st3_schemas.py / st3_eval.py (split out because this file
was becoming a 1000-line mix of prompt text, schemas, scoring, and CLI orchestration); the
imports below re-export everything those callers use, so none of them need to change.
"""
import argparse
import json
import os
import random
import shutil
import sys
from datetime import datetime

from langchain_openai import ChatOpenAI

# common/__init__.py imports names from this file, so importing the `common` package here
# would be circular. Import dialog_flow.py directly (as a top-level module, bypassing
# common/__init__.py) instead.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "common"))
from dialog_flow import df_pre_context

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "starting_kit"))
from load_data import load_split

from st3_schemas import (  # noqa: F401 (ST1/ST2/ST3/ST1_LABELS/ST2_LABELS/ST3_FAMILY/FAMILY_LABELS/
    ST1, ST2, ST3, ST1_LABELS, ST2_LABELS, ST3_LABELS, ST3_FAMILY, FAMILY_LABELS,
    Prediction, ST3Prediction, ST3PredictionCoT, sanitize_st3,
)
from st3_prompts import (  # noqa: F401 (LABELS_TAXONOMY/CONTEXT_CHOICES/no_product_page re-exported
    LABELS_TAXONOMY, TRAIN_PATH, SFT_TAXONOMY, CONTEXT_CHOICES, no_product_page, build_messages,
    SYSTEM_PROMPT, ST3_SYSTEM_PROMPT, COT_INSTRUCTIONS, build_few_shot_section,
)
from st3_eval import (  # noqa: F401 (setup_logging/log_gold_label_inventory/evaluate/prediction_errors/
    setup_logging, log_gold_label_inventory, log_prediction_diagnostics,
    evaluate, prediction_errors, macro_f1,
)

from dotenv import load_dotenv
load_dotenv()

COT_CHOICES = ["off", "inline", "flow"]


# From repo root:
# python src/baseline_gpt.py public_data_dev/dev.jsonl --sample-size 10

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="split file to predict on, e.g. dev.jsonl")
    ap.add_argument("--model", default="gpt-5.4")
    ap.add_argument("--context", choices=CONTEXT_CHOICES, default="full",
                     help="how much of the instance to show the model. no_product_page drops the "
                          "linked page entirely -- transcript + video title/description/disclosure only")
    ap.add_argument("--sample-size", type=int, default=None,
                     help="only run on a random sample of N instances (seeded, for smoke tests)")
    ap.add_argument("--max-concurrency", type=int, default=8)
    ap.add_argument("--st3-only", action="store_true",
                     help="predict only ST3 (compliance risk flags), with ST3_SYSTEM_PROMPT -- a "
                          "copy of the system prompt tuned for st3 alone -- instead of the full "
                          "st1/st2/st3 prompt. Output rows and scoring both drop st1/st2 (no "
                          "mean_macro_f1); writes to submission_gpt_st3.jsonl instead of the "
                          "canonical submission_gpt.jsonl so it can't clobber a full run's output")
    ap.add_argument("--lean-prompt", action="store_true",
                     help="use common.SFT_TAXONOMY in place of the full system prompt (whichever "
                          "of SYSTEM_PROMPT/ST3_SYSTEM_PROMPT --st3-only selects), for an apples-to"
                          "-apples comparison against the LoRA baselines' --lean-prompt. It drops "
                          "the ST1/ST3 definitions the dialog flow would otherwise supply, so pair "
                          "it with --df-path")
    ap.add_argument("--df-path", default=None,
                     help="path to a dialog-flow export (e.g. emnllp-dialog-flow-dialog-flow.json), "
                          "rendered and appended to the system prompt -- for compatibility with the "
                          "LoRA baselines' --df-path; rendering (lean text vs. raw JSON) follows "
                          "--lean-prompt")
    ap.add_argument("--few-shot", action="store_true",
                     help="st3-only only: append a FEW-SHOT EXAMPLES section to the system prompt "
                          "-- hand-picked, baked-in train.jsonl examples (see "
                          "GOLDEN_FEW_SHOT_EXAMPLES in st3_prompts.py) for direct_exhortation, "
                          "undisclosed_advertising, inadequate_disclosure, misleading_claim, "
                          "no_flag, and insufficient_context, pairing each label's taxonomy "
                          "definition with real evidence and a one-line rationale")
    ap.add_argument("--few-shot-n", type=int, default=1,
                     help="deprecated/no-op: examples are baked in now (see "
                          "GOLDEN_FEW_SHOT_EXAMPLES), no longer scanned live from train.jsonl, "
                          "so this no longer has any effect -- kept only so old invocations "
                          "don't break")
    ap.add_argument("--cot", choices=COT_CHOICES, default="off",
                     help="st3-only only: off = today's one-shot call (default); inline = adds a "
                          "`reasoning` field to the structured-output schema (ST3PredictionCoT) so "
                          "the model reasons through the prompt's checklists before committing to "
                          "labels, still one call; flow = walks the local dialog-flow graph "
                          "(emnllp-dialog-flow-dialog-flow.json) node by node via node-lab, one "
                          "structured call per check -- see st3_flow_executor.py")
    ap.add_argument("--seed", type=int, default=None, help="for example, 42.")
    args = ap.parse_args()

    if args.few_shot and not args.st3_only:
        raise SystemExit("--few-shot only applies to --st3-only")
    if args.cot != "off" and not args.st3_only:
        raise SystemExit("--cot only applies to --st3-only")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log = setup_logging("runs", args.context, args.model, timestamp)
    out = os.path.join("runs", f"submission_gpt_{timestamp}.jsonl")
    error_out = os.path.join("runs", f"submission_gpt_error_{timestamp}.jsonl")
    log.info(f"config: target={args.target} model={args.model} context={args.context} "
             f"sample_size={args.sample_size} max_concurrency={args.max_concurrency} "
             f"st3_only={args.st3_only} lean_prompt={args.lean_prompt} df_path={args.df_path} "
             f"few_shot={args.few_shot} few_shot_n={args.few_shot_n} cot={args.cot} "
             f"out={out} seed={args.seed}")

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("Set OPENAI_API_KEY in the environment (or a .env file) first.")

    tiers = ("st3",) if args.st3_only else ("st1", "st2", "st3")
    if args.st3_only:
        prediction_schema = ST3PredictionCoT if args.cot == "inline" else ST3Prediction
    else:
        prediction_schema = Prediction

    base_prompt = SFT_TAXONOMY if args.lean_prompt else (ST3_SYSTEM_PROMPT if args.st3_only else SYSTEM_PROMPT)
    if args.few_shot:
        few_shot_text = build_few_shot_section(TRAIN_PATH, log, n_per_label=args.few_shot_n)
        log.info(f"appending few-shot examples ({len(few_shot_text)} chars) to the system prompt")
        base_prompt = f"{base_prompt}\n\n{few_shot_text}"
    df_text = None
    if args.df_path:
        df_text = df_pre_context(args.df_path, lean=args.lean_prompt)
        form = "stripped dialog flow" if args.lean_prompt else "raw autoDF JSON"
        log.info(f"appending {form} from {args.df_path} ({len(df_text)} chars) to the system prompt")
    system_prompt = f"{base_prompt}\n\n{df_text}" if df_text else base_prompt
    if args.cot == "inline":
        log.info("appending CoT instructions to the system prompt")
        system_prompt = f"{system_prompt}\n\n{COT_INSTRUCTIONS}"
    log.info(f"system prompt: {'lean' if args.lean_prompt else 'full'}"
             f"{' st3-only' if args.st3_only else ''}{' few-shot' if args.few_shot else ''}"
             f"{' cot=' + args.cot if args.cot != 'off' else ''} "
             f"({len(system_prompt)} chars)")
    log.info(f"system prompt used: {system_prompt}")

    instances = list(load_split(args.target))
    if args.sample_size:
        instances = random.Random(args.seed).sample(instances, min(args.sample_size, len(instances)))

    if args.cot == "flow":
        from st3_flow_executor import run_flow_st3_batch
        results_by_id = run_flow_st3_batch(
            instances, model=args.model, max_concurrency=args.max_concurrency,
            trace_dir=os.path.join("runs", "cot_flow", timestamp), log=log,
            context=args.context,
        )
        results = [results_by_id[inst["instanceID"]] for inst in instances]
    else:
        llm = ChatOpenAI(model=args.model, temperature=0).with_structured_output(
            prediction_schema, method="json_schema", strict=True
        )
        batch_inputs = [build_messages(inst, args.context, system_prompt) for inst in instances]

        # Parallel batch requests to AI API
        # Returns output in a list, each elem maps to 1 query
        results = llm.batch(batch_inputs, config={"max_concurrency": args.max_concurrency},
                             return_exceptions=True)

    predictions, gold = [], []
    n_errors = 0
    with open(out, "w", encoding="utf-8") as f, \
         open(error_out, "w", encoding="utf-8") as f_err:
        for inst, result in zip(instances, results):
            if isinstance(result, Exception):
                log.warning(f"{inst['instanceID']} failed ({result})")
                pred = {"st3": [f"error:{result}"]} if args.st3_only \
                    else {"st1": "other", "st2": [], "st3": [f"error:{result}"]}
            elif args.cot == "flow":
                pred = {"st3": result["st3"]}
            elif args.st3_only:
                pred = {"st3": sanitize_st3(result.st3, inst, use_thin_override=True)}
                if args.cot == "inline":
                    pred["reasoning"] = result.reasoning
            else:
                pred = {"st1": result.st1, "st2": result.st2, "st3": sanitize_st3(result.st3)}
            predictions.append(pred)
            f.write(json.dumps({"instanceID": inst["instanceID"], **pred}) + "\n")
            if inst.get("labels"):
                gold.append(inst["labels"])
                errors = prediction_errors(inst["labels"], pred, tiers=tiers)
                if errors:
                    n_errors += 1
                    f_err.write(json.dumps({
                        "instanceID": inst["instanceID"], "gold": inst["labels"],
                        "pred": pred, "errors": errors,
                    }) + "\n")
    log.info(f"wrote {len(predictions)} predictions to {out}")

    canonical = "submission_gpt_st3.jsonl" if args.st3_only else "submission_gpt.jsonl"
    shutil.copyfile(out, canonical)
    log.info(f"copied predictions to {canonical} (canonical submission file)")

    if gold:
        log.info(f"wrote {n_errors} misclassified instance(s) to {error_out}")

    if len(gold) == len(predictions) and gold:
        log_gold_label_inventory(log, gold)
        metrics = evaluate(gold, predictions, tiers=tiers)
        log.info("Evaluation:")
        for k, v in metrics.items():
            if k == "per_label_f1":
                continue
            log.info(f"  {k}: {v:.3f}")
        for tier, per_label in metrics["per_label_f1"].items():
            log.info(f"  {tier} per-label F1: " + ", ".join(f"{l}={f:.3f}" for l, f in sorted(per_label.items())))
        log_prediction_diagnostics(log, gold, predictions, tiers=tiers)
    else:
        log.info("target has no gold labels (or a partial mismatch) -- skipping evaluation")


if __name__ == "__main__":
    main()
