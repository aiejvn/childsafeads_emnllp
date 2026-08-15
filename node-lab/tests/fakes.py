"""A scripted LLM so the pipeline can be exercised with no network."""

from __future__ import annotations

from typing import Any

from node_lab.llm import GenerateResult, LLMClient, ToolExecution
from node_lab.types import TokenUsage


class FakeLLM(LLMClient):
    """Records every call and answers each schema with a canned object.

    `rag_queries` drives the analysis step: for each query in the list the
    fake calls the `rag_search` tool once, which is how a real model-driven
    loop reaches the tool. An empty list means "never search".
    """

    def __init__(
        self,
        *,
        rag_queries: list[str] | None = None,
        rationale: str = "## Facts\nf\n\n## Analysis\na",
        predictions: list[dict[str, Any]] | None = None,
        reflection: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(anthropic_api_key="test", openai_api_key="test")
        self.rag_queries = rag_queries or []
        self.rationale = rationale
        self.predictions = predictions or [
            {"prediction": "2 - No", "probability": 0.8},
            {"prediction": "1 - Yes", "probability": 0.2},
        ]
        self.reflection = reflection or {
            "findings": [],
            "revisedText": rationale,
            "clean": True,
        }
        self.calls: list[dict[str, Any]] = []

    async def generate_object(  # type: ignore[override]
        self,
        *,
        model: str,
        system: Any,
        prompt: str,
        schema: dict[str, Any],
        schema_name: str,
        schema_description: str = "",
        tools: Any = None,
        config: Any = None,
        abort_signal: Any = None,
    ) -> GenerateResult:
        tool_names = [t.name for t in (tools or [])]
        self.calls.append(
            {
                "schema": schema_name,
                "model": model,
                "prompt": prompt,
                "tools": tool_names,
                "system": system,
                "config": config,
            }
        )
        result = GenerateResult(
            usage=TokenUsage(input_tokens=10, output_tokens=5), steps=1
        )

        if schema_name == "reasoning_rationale":
            by_name = {t.name: t for t in (tools or [])}
            rag = by_name.get("rag_search")
            if rag is not None:
                for query in self.rag_queries:
                    output = await rag.execute({"query": query})
                    result.tool_executions.append(
                        ToolExecution("rag_search", {"query": query}, output)
                    )
                result.steps = 1 + len(self.rag_queries)
            result.object = {"rationale": self.rationale}
        elif schema_name == "rationale_reflection":
            result.object = dict(self.reflection)
        elif schema_name == "reasoning_predictions":
            result.object = {"predictions": self.predictions}
        return result
