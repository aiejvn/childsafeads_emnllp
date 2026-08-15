"""The four-step node.

    build analysis prompt from the node's config
      -> analysis (LLM tool loop; the model calls RAG until it has enough)
      -> self-reflection (optional)
      -> final answer(s)
      -> pass those answers to the children

No `NodeExecutionContext` port: progress goes to a callable sink, `abortSignal`
is a `threading.Event`, and there is no rate limiter, Redis, or event emitter.
The transcript is a plain dict — no `NodeExecutionResultCompleted` mirror.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from ..backend_client import BackendClient
from ..documents import DocumentResolver, build_annotation_context
from ..flow import Flow
from ..llm import UTILITY_MODEL, AbortSignal, LLMClient
from ..prompts.reasoning_node import format_annotation_context_block
from ..tools.rag_search import RagSearchTool
from ..types import FlowNode, PriorAnswer, TokenUsage
from .analysis import run_analysis
from .answer import build_prediction_range, generate_answer, parse_prediction_value
from .children import execute_graph_children, execute_inline_children
from .reflect import reflect_rationale_loop

ChildrenMode = Literal["inline", "graph", "both", "none"]


@dataclass
class RunOptions:
    model: str
    answer_model: str = UTILITY_MODEL
    reflect: bool = True
    rag: bool = True
    children: ChildrenMode = "inline"
    rag_fixture: Path | None = None
    text_dir: Path | None = None
    cache_dir: Path = Path(".cache")


@dataclass
class RunDeps:
    flow: Flow
    llm: LLMClient
    backend: BackendClient
    resolver: DocumentResolver
    options: RunOptions
    on_progress: Callable[[str], None] = lambda _msg: None
    abort_signal: AbortSignal | None = None
    #: Guards against a cycle in `childNodeIds` or converging graph edges
    #: re-entering a node that is still running.
    _running: set[str] = field(default_factory=set)


async def run_node(
    node: FlowNode,
    prior_answers: Mapping[str, PriorAnswer],
    deps: RunDeps,
    *,
    expand_children: bool = True,
) -> dict[str, Any]:
    """Run one reasoning node and return its transcript."""
    if node.id in deps._running:
        return {
            "node": {"id": node.id, "label": node.label, "type": node.type},
            "skipped": "cycle",
            "note": "Node is already running higher in this call stack.",
        }
    deps._running.add(node.id)
    try:
        return await _run_node_inner(
            node, prior_answers, deps, expand_children=expand_children
        )
    finally:
        deps._running.discard(node.id)


async def _run_node_inner(
    node: FlowNode,
    prior_answers: Mapping[str, PriorAnswer],
    deps: RunDeps,
    *,
    expand_children: bool,
) -> dict[str, Any]:
    options = deps.options
    config = node.reasoning_config()
    deps.on_progress(f"[{node.label or node.id}] analysis")

    # -- annotation context ------------------------------------------------
    annotation_block: str | None = None
    annotation_files: list[str] = []
    if config.annotations:
        ctx = await build_annotation_context(
            config.annotations, deps.resolver, on_warning=deps.on_progress
        )
        if ctx.files or ctx.excerpts:
            annotation_block = format_annotation_context_block(ctx)
            annotation_files = [f.file_id for f in ctx.files]

    # -- RAG tool ----------------------------------------------------------
    # A fresh tool per node: `seen_ids` is scoped to ONE analysis loop, so a
    # child re-searching the same corpus is not starved by its parent's hits.
    rag: RagSearchTool | None = None
    if options.rag:
        rag = RagSearchTool(
            backend=deps.backend,
            vector_config=config.vector_search_config,
            fixture=options.rag_fixture,
            on_progress=deps.on_progress,
        )
        if not rag.enabled:
            rag = None

    # -- step 1: analysis --------------------------------------------------
    analysis = await run_analysis(
        config=config,
        prior_answers=prior_answers,
        llm=deps.llm,
        model=options.model,
        rag=rag,
        annotation_block=annotation_block,
        abort_signal=deps.abort_signal,
    )
    usage = TokenUsage().add(analysis.usage)

    # -- step 2: self-reflection (optional) --------------------------------
    reflection: dict[str, Any] | None = None
    rationale = analysis.rationale
    reflection_prompts: list[str] = []
    if options.reflect and rationale:
        deps.on_progress(f"[{node.label or node.id}] reflection")
        result = await reflect_rationale_loop(
            draft=rationale,
            question=config.question,
            instructions=config.instructions,
            prior_answers=prior_answers,
            llm=deps.llm,
            model=options.model,
            abort_signal=deps.abort_signal,
        )
        usage = usage.add(result.usage)
        reflection_prompts = result.prompts
        reflection = {
            "passes": result.passes,
            "findings": result.findings,
            "revised": result.text != rationale,
            "text": result.text,
        }
        # The revised text is what feeds the answer step; both versions stay in
        # the transcript.
        rationale = result.text

    # -- step 3: final answer(s) -------------------------------------------
    deps.on_progress(f"[{node.label or node.id}] answer")
    answer = await generate_answer(
        config=config,
        prior_answers=prior_answers,
        rationale=rationale,
        llm=deps.llm,
        model=options.answer_model,
        abort_signal=deps.abort_signal,
    )
    usage = usage.add(answer.usage)

    top = answer.top
    answers_out: dict[str, PriorAnswer] = {}
    if top is not None:
        answers_out[node.id] = PriorAnswer(
            label=node.label or node.id,
            prediction=top.prediction,
            # Production persists the rationale alongside the prediction and
            # quotes it into every downstream <Conversation_Facts>; keep that.
            rationale=rationale,
        )

    transcript: dict[str, Any] = {
        "node": {
            "id": node.id,
            "label": node.label,
            "type": node.type,
            "config": node.data.config,
        },
        "prompts": {
            "analysis": analysis.prompt,
            "reflection": reflection_prompts,
            "answer": answer.prompt,
        },
        "annotationFiles": annotation_files,
        "ragCalls": analysis.rag_calls,
        "analysis": {
            "rationale": analysis.rationale,
            "steps": analysis.steps,
            "hitStepCap": analysis.hit_step_cap,
            "toolsOffered": ["rag_search"] if rag is not None else [],
        },
        "reflection": reflection,
        "answers": [c.model_dump() for c in answer.candidates],
        "answerRange": build_prediction_range(answer.candidates, config.data_type),
        "answerParsed": (
            parse_prediction_value(top.prediction, config.data_type)
            if top is not None
            else None
        ),
        "answersOut": {k: v.model_dump() for k, v in answers_out.items()},
        "childResults": [],
        "tokenUsage": usage.model_dump(),
    }

    # -- step 4: children ---------------------------------------------------
    if not expand_children or options.children == "none":
        return transcript

    downstream: dict[str, PriorAnswer] = {**prior_answers, **answers_out}

    async def run_child(
        child: FlowNode, answers: Mapping[str, PriorAnswer]
    ) -> dict[str, Any]:
        # Inline children may themselves have inline children; graph children
        # never expand (one hop only) — `execute_graph_children` is the only
        # caller that passes expand_children=False, via the wrapper below.
        return await run_node(child, answers, deps)

    child_results: list[dict[str, Any]] = []

    if options.children in ("inline", "both"):
        child_results.extend(
            await execute_inline_children(
                parent=node, flow=deps.flow, answers=downstream, run_fn=run_child
            )
        )

    if options.children in ("graph", "both"):

        async def run_graph_child(
            child: FlowNode, answers: Mapping[str, PriorAnswer]
        ) -> dict[str, Any]:
            # One hop only: a graph child runs its own analysis but does not
            # fan out further, so a lab run never turns into a flow run.
            return await run_node(child, answers, deps, expand_children=False)

        child_results.extend(
            await execute_graph_children(
                parent=node, flow=deps.flow, answers=downstream, run_fn=run_graph_child
            )
        )

    transcript["childResults"] = child_results
    for result in child_results:
        child_usage = result.get("tokenUsage")
        if child_usage:
            usage = usage.add(TokenUsage.model_validate(child_usage))
    transcript["tokenUsage"] = usage.model_dump()
    return transcript


__all__ = ["ChildrenMode", "RunDeps", "RunOptions", "run_node"]
