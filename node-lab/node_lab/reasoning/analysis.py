"""Step 1 — the analysis, with RAG as a tool.

This is the heart of the distilled node. The model receives the node's
question + instructions (plus the annotation context when the node has one),
calls `rag_search` as many times as it wants, and writes the rationale when it
judges it has enough.

SOURCE (call semantics): lib/reasoning-node/synthesis-pipeline.ts ::
synthesizeAnalysis — same system prompt, same cache breakpoint, same
`temperature: 0` + `reasoningEffort: "low"` config.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from ..llm import (
    AbortSignal,
    GenerateConfig,
    LLMClient,
    ToolExecution,
    cached_system_message,
)
from ..prompts.reasoning_node import (
    REASONING_ANALYSIS_SYSTEM_PROMPT,
    build_analysis_message,
)
from ..schemas import ANALYSIS_SCHEMA
from ..tools.rag_search import RagSearchTool
from ..types import PriorAnswer, ReasoningNodeConfig, TokenUsage


@dataclass
class AnalysisResult:
    rationale: str
    prompt: str
    usage: TokenUsage = field(default_factory=TokenUsage)
    steps: int = 0
    hit_step_cap: bool = False
    tool_executions: list[ToolExecution] = field(default_factory=list)
    rag_calls: list[dict[str, Any]] = field(default_factory=list)


async def run_analysis(
    *,
    config: ReasoningNodeConfig,
    prior_answers: Mapping[str, PriorAnswer],
    llm: LLMClient,
    model: str,
    rag: RagSearchTool | None,
    annotation_block: str | None = None,
    abort_signal: AbortSignal | None = None,
) -> AnalysisResult:
    prompt = build_analysis_message(
        question=config.question,
        instructions=config.instructions,
        prior_answers=prior_answers,
        annotation_block=annotation_block,
    )

    # A node whose vectorSearchConfig resolves to "retrieval disabled" gets NO
    # tool at all — not an empty one. That is what drops the step budget from
    # 10 to 2 (client.ts:105) and is the behaviour SemanticFileSearchTool.load
    # produces by returning null.
    tools = [rag.spec()] if rag is not None and rag.enabled else None

    result = await llm.generate_object(
        model=model,
        # Cache the large static analysis system prompt — identical across
        # every reasoning node in a flow.
        system=cached_system_message(REASONING_ANALYSIS_SYSTEM_PROMPT),
        prompt=prompt,
        schema=ANALYSIS_SCHEMA,
        schema_name="reasoning_rationale",
        schema_description="Write the structured legal rationale for this question.",
        tools=tools,
        # Rationale synthesis benefits from reasoning, so allow "low" on GPT-5
        # models — trades exact-token determinism for better quality.
        # `temperature: 0` still applies on Claude; on GPT-5 it is dropped
        # because reasoningEffort != "none" (intentional API behaviour).
        config=GenerateConfig(temperature=0, reasoning_effort="low"),
        abort_signal=abort_signal,
    )

    rationale = (result.object or {}).get("rationale", "") or ""
    return AnalysisResult(
        rationale=rationale,
        prompt=prompt,
        usage=result.usage,
        steps=result.steps,
        hit_step_cap=result.hit_step_cap,
        tool_executions=result.tool_executions,
        rag_calls=[call.to_dict() for call in (rag.calls if rag else [])],
    )


__all__ = ["AnalysisResult", "run_analysis"]
