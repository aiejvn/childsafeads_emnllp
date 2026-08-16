"""Step 2 — optional self-reflection over the rationale.

SOURCE: lib/reasoning-node/reflect-rationale.ts

Pure text, no tools. On a missing object the draft is returned unchanged so a
failed pass never corrupts the rationale.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ..llm import AbortSignal, GenerateConfig, LLMClient
from ..prompts.reflect_rationale import (
    RATIONALE_REFLECTION_SYSTEM_PROMPT,
    build_rationale_reflection_message,
)
from ..schemas import RATIONALE_REFLECTION_SCHEMA
from ..types import PriorAnswer, TokenUsage

# SOURCE: reflect-rationale.ts :: MAX_RATIONALE_REFLECTION_PASSES
# One pass clears most defects; the second catches anything the first rewrite
# introduced.
MAX_RATIONALE_REFLECTION_PASSES = 2


@dataclass
class ReflectionResult:
    text: str
    passes: int = 0
    findings: list[str] = field(default_factory=list)
    prompts: list[str] = field(default_factory=list)
    usage: TokenUsage = field(default_factory=TokenUsage)


async def reflect_rationale_loop(
    *,
    draft: str,
    question: str,
    instructions: str,
    prior_answers: Mapping[str, PriorAnswer],
    llm: LLMClient,
    model: str,
    abort_signal: AbortSignal | None = None,
) -> ReflectionResult:
    """Run passes until the critic reports the rationale clean, capped.

    Guards against a critic that flags defects but returns no usable rewrite
    (empty or byte-identical text) — such a pass is terminal so the loop cannot
    churn.
    """
    out = ReflectionResult(text=draft)

    for _ in range(MAX_RATIONALE_REFLECTION_PASSES):
        prompt = build_rationale_reflection_message(
            draft=out.text,
            question=question,
            instructions=instructions,
            prior_answers=prior_answers,
        )
        result = await llm.generate_object(
            model=model,
            # Same model that drafted, per the citation-repair precedent — the
            # critic shares the drafter's competence.
            system=RATIONALE_REFLECTION_SYSTEM_PROMPT,
            prompt=prompt,
            schema=RATIONALE_REFLECTION_SCHEMA,
            schema_name="rationale_reflection",
            schema_description=(
                "Review a drafted rationale, fix consistency and discipline "
                "defects, and return the corrected rationale with a list of fixes."
            ),
            # "medium" to match the outcome critic: cross-section defects (a
            # figure contradicting its own characterisation, one case read two
            # ways) need real reasoning to catch.
            config=GenerateConfig(temperature=0, reasoning_effort="medium"),
            abort_signal=abort_signal,
        )

        out.passes += 1
        out.prompts.append(prompt)
        out.usage = out.usage.add(result.usage)

        obj = result.object
        if not obj:
            return out

        out.findings.extend(obj.get("findings") or [])
        if obj.get("clean"):
            return out

        revised = obj.get("revisedText") or ""
        if not revised or revised == out.text:
            return out
        out.text = revised

    return out


__all__ = [
    "MAX_RATIONALE_REFLECTION_PASSES",
    "ReflectionResult",
    "reflect_rationale_loop",
]
