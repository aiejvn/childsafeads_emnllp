"""--cot flow: predict ST3 by walking emnllp-dialog-flow-dialog-flow.json node by node,
via node-lab's per-node reasoning runner (node-lab/node_lab/reasoning/runner.py), instead
of baseline_gpt.py's single one-shot structured-output call.

The flow has, in order: Assessability (routes to insufficient_context or continues) -> 6
single-answer yes/no reasoning nodes, one per substantive ST3 flag -- Undisclosed
Advertising?, Inadequate Disclosure?, Direct Exhortation?, Misleading Claim?,
Age-Restricted/Prohibited Product?, HFSS Food Marketing?. node-lab's run_node produces a
ranked single-value answer per node (not multi-select), which is why the flow was split
into one node per flag rather than the two multi-label nodes it started as -- see the
dialog flow's own edges (python src/common/dialog_flow.py) for the current shape.

Each node genuinely sees the prior nodes' answers (via `prior_answers`, node-lab's
PriorAnswer dict), which is what makes this "more iterative" than a single call: the
Inadequate Disclosure? node's own instructions tell it to answer "no" if Undisclosed
Advertising? already answered "yes", and it can actually see that answer to act on it.

RAG and self-reflection are off by default (RunOptions(rag=False, reflect=False)) -- our
flow has no annotations, so RAG would be a no-op anyway; reflection is a straightforward
cost/latency lever to revisit if analysis quality needs it.

IMPORTANT parsing caveat: node-lab's answer schema (node_lab/schemas.py) declares
`"prediction": {"type": "string"}` with no `enum` constraint -- the customEnumValues
["yes", "no"] on our new nodes are prompt-level guidance, not a hard schema constraint. The
model can and sometimes will answer with something other than a literal "yes"/"no" (e.g.
"of course", "exactly", "yes, clearly"). Every node's raw prediction is logged (at INFO) so
this is visible during a run, and any prediction that doesn't cleanly parse as
yes/no/assessable/insufficient_context is logged as a WARNING rather than silently
defaulting one way or the other.
"""
import asyncio
import json
import logging
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "node-lab"))
from node_lab.backend_client import BackendClient
from node_lab.documents import DocumentResolver
from node_lab.flow import Flow, load_flow
from node_lab.llm import LLMClient
from node_lab.reasoning.runner import RunDeps, RunOptions, run_node
from node_lab.types import PriorAnswer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "starting_kit"))
from load_data import full_context, transcript_only

from st3_prompts import no_product_page
from st3_schemas import sanitize_st3

FLOW_PATH = os.path.join(os.path.dirname(__file__), "..", "emnllp-dialog-flow-dialog-flow.json")

# The node's actual name in the flow -- "is this segment assessable enough to classify",
# not a disability-accessibility check. Used with flow.resolve() to look the node up.
ASSESSABILITY_LABEL = "Assessability"

# Node label -> ST3 flag name, in the order they should run (later nodes' instructions
# reference earlier ones, e.g. Inadequate Disclosure? checking Undisclosed Advertising?'s
# answer -- see the module docstring).
FLOW_FLAG_NODES = {
    "Undisclosed Advertising?": "undisclosed_advertising",
    "Inadequate Disclosure?": "inadequate_disclosure",
    "Direct Exhortation?": "direct_exhortation",
    "Misleading Claim?": "misleading_claim",
    "Age-Restricted/Prohibited Product?": "age_restricted_or_prohibited_product",
    "HFSS Food Marketing?": "hfss_food_marketing",
}

# Tolerant yes/no matching, since node-lab's schema doesn't hard-enforce customEnumValues
# (see module docstring). Matches a leading affirmative/negative token so "yes, clearly" or
# "no -- nothing here" still parse, without trying to be a general sentiment classifier.
_YES_RE = re.compile(r"^\s*(yes|of course|clearly|definitely|correct|true)\b", re.I)
_NO_RE = re.compile(r"^\s*(no|none|false|not\b)", re.I)


def _parse_yes_no(raw: str, node_label: str, instance_id: str, log: logging.Logger) -> bool:
    if _YES_RE.match(raw):
        return True
    if _NO_RE.match(raw):
        return False
    log.warning(f"{instance_id}: {node_label} answered {raw!r} -- doesn't cleanly parse as "
                f"yes/no, treating as no. Check the trace for what the model actually meant.")
    return False


def _segment_text(instance: dict, context: str) -> str:
    if context == "full":
        return full_context(instance)
    if context == "no_product_page":
        return no_product_page(instance)
    return transcript_only(instance)


async def run_flow_st3(flow: Flow, instance: dict, deps: RunDeps, log: logging.Logger,
                        context: str = "full"):
    """Walk the flow for one instance. Returns (st3_labels, transcript_dict)."""
    instance_id = instance["instanceID"]
    text = _segment_text(instance, context)
    prior_answers = {"user_message_0": PriorAnswer(label="User message", prediction=text)}
    node_transcripts = []

    def fold_answer(node, result: dict) -> str | None:
        """Log and record `node`'s raw prediction string into `prior_answers` (so later
        nodes see it), returning it (or None if the node produced no answer)."""
        answer_out = result.get("answersOut", {}).get(node.id)
        if not answer_out:
            log.warning(f"{instance_id}: {node.label} produced no answer")
            return None
        raw = answer_out["prediction"]
        log.info(f"{instance_id}: {node.label} -> {raw!r}")
        prior_answers[node.id] = PriorAnswer.model_validate(answer_out)
        return raw

    assessability = flow.resolve(ASSESSABILITY_LABEL)
    result = await run_node(assessability, prior_answers, deps, expand_children=False)
    node_transcripts.append(result)
    top = fold_answer(assessability, result)

    if top is not None and "insufficient" in top.lower():
        return ["insufficient_context"], {"nodes": node_transcripts}

    flags = []
    for label, flag_name in FLOW_FLAG_NODES.items():
        node = flow.resolve(label)
        result = await run_node(node, prior_answers, deps, expand_children=False)
        node_transcripts.append(result)
        top = fold_answer(node, result)
        if top is not None and _parse_yes_no(top, label, instance_id, log):
            flags.append(flag_name)

    st3 = sanitize_st3(flags, instance, use_thin_override=False)
    return st3, {"nodes": node_transcripts}


async def _run_all(instances, model: str, max_concurrency: int, trace_dir: str,
                    log: logging.Logger, context: str) -> dict:
    os.makedirs(trace_dir, exist_ok=True)
    flow = load_flow(FLOW_PATH)
    options = RunOptions(model=model, answer_model=model, reflect=False, rag=False, children="none")
    semaphore = asyncio.Semaphore(max_concurrency)

    async with BackendClient() as backend:
        resolver = DocumentResolver(backend=backend, cache_dir=Path(".cache"))
        llm = LLMClient()

        async def run_one(inst: dict):
            async with semaphore:
                # A fresh RunDeps per instance: its `_running` cycle-guard set must not be
                # shared across concurrently-running instances, which would otherwise see
                # each other's in-flight calls to the SAME node id as a false cycle.
                deps = RunDeps(flow=flow, llm=llm, backend=backend, resolver=resolver, options=options)
                try:
                    st3, transcript = await run_flow_st3(flow, inst, deps, log, context=context)
                except Exception as e:  # noqa: BLE001 -- mirrors llm.batch(return_exceptions=True)
                    log.warning(f"{inst['instanceID']} failed ({e})")
                    return inst["instanceID"], e
                trace_path = os.path.join(trace_dir, f"{inst['instanceID']}.json")
                with open(trace_path, "w", encoding="utf-8") as f:
                    json.dump(transcript, f, indent=2, ensure_ascii=False, default=str)
                return inst["instanceID"], {"st3": st3}

        pairs = await asyncio.gather(*(run_one(inst) for inst in instances))

    return dict(pairs)


def run_flow_st3_batch(instances, model: str, max_concurrency: int, trace_dir: str,
                        log: logging.Logger, context: str = "full") -> dict:
    """Sync entry point for baseline_gpt.py's main(). Returns {instanceID: {"st3": [...]}}
    on success or {instanceID: Exception} on failure, matching the shape main() already
    expects from `llm.batch(..., return_exceptions=True)` on the off/inline paths."""
    return asyncio.run(_run_all(instances, model, max_concurrency, trace_dir, log, context))
