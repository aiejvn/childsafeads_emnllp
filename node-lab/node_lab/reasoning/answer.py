"""Step 3 — the final answer(s).

Parse the rationale into the node's declared shape (`dataType`, plus
`customEnumValues` when present). A node may yield more than one candidate,
hence "answer(s)".

SOURCE: lib/reasoning-node/prediction-parse.ts, prediction-range.ts
        lib/reasoning-node/synthesis-pipeline.ts :: generatePrediction
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from ..llm import UTILITY_MODEL, AbortSignal, GenerateConfig, LLMClient
from ..prompts.reasoning_node import (
    REASONING_PREDICTION_SYSTEM_PROMPT,
    build_prediction_message,
)
from ..schemas import PREDICTION_RESULT_SCHEMA
from ..types import (
    FactDataType,
    PredictionCandidate,
    PriorAnswer,
    ReasoningNodeConfig,
    TokenUsage,
)


def parse_prediction_value(
    value: str, data_type: FactDataType
) -> str | float | bool | None:
    """SOURCE: prediction-parse.ts :: parsePredictionValue

    The prediction schema uses required strings (with `""`, `"null"`, `"NULL"`
    as null sentinels) to dodge Claude's 16-union-type limit; coerce here.

    NOTE: a CUSTOM enum may legitimately contain the literal string "null" as a
    member (the Worker Classification flow does). The sentinel check runs
    first, exactly as in the TS — such a value parses to None, and the raw
    string stays available on the candidate.
    """
    if value in ("", "null", "NULL"):
        return None

    if data_type in (
        FactDataType.NUMBER,
        FactDataType.PERCENTAGE,
        FactDataType.CONFIDENCE,
    ):
        try:
            return float(value)
        except ValueError:
            return value

    if data_type is FactDataType.BOOLEAN:
        lower = value.lower().strip()
        if lower == "true":
            return True
        if lower == "false":
            return False
        return value

    return value


def build_prediction_range(
    predictions: Sequence[PredictionCandidate], data_type: FactDataType
) -> dict[str, float] | None:
    """SOURCE: prediction-range.ts :: buildPredictionRange

    Display-only min/max across candidate values, NOT keyed by probability.
    Returns None when there is no meaningful range: non-NUMBER data type,
    fewer than two numeric candidates, or all candidates share one value.
    """
    if data_type is not FactDataType.NUMBER:
        return None

    values = [
        parsed
        for parsed in (
            parse_prediction_value(p.prediction, data_type) for p in predictions
        )
        if isinstance(parsed, float)
    ]
    if len(values) < 2:
        return None

    low, high = min(values), max(values)
    if low == high:
        return None
    return {"min": low, "max": high}


@dataclass
class AnswerResult:
    candidates: list[PredictionCandidate] = field(default_factory=list)
    prompt: str = ""
    usage: TokenUsage = field(default_factory=TokenUsage)

    @property
    def top(self) -> PredictionCandidate | None:
        if not self.candidates:
            return None
        return max(self.candidates, key=lambda c: c.probability)


async def generate_answer(
    *,
    config: ReasoningNodeConfig,
    prior_answers: Mapping[str, PriorAnswer],
    rationale: str,
    llm: LLMClient,
    model: str = UTILITY_MODEL,
    abort_signal: AbortSignal | None = None,
) -> AnswerResult:
    prompt = build_prediction_message(
        config=config, prior_answers=prior_answers, rationale=rationale
    )

    result = await llm.generate_object(
        # Prediction is structured-only; the analysis model is overkill. The TS
        # pins this to UTILITY_MODEL for the same reason.
        model=model,
        system=REASONING_PREDICTION_SYSTEM_PROMPT,
        prompt=prompt,
        schema=PREDICTION_RESULT_SCHEMA,
        schema_name="reasoning_predictions",
        schema_description="Predict candidate answers with probabilities.",
        # Greedy decode so an identical rationale gives identical top-K
        # ordering across runs. On a GPT-5 nano model `reasoningEffort: "none"`
        # is required or `temperature` is dropped.
        config=GenerateConfig(temperature=0, reasoning_effort="none"),
        abort_signal=abort_signal,
    )

    raw = (result.object or {}).get("predictions") or []
    candidates = [
        PredictionCandidate(
            prediction=str(item.get("prediction", "")),
            probability=float(item.get("probability", 0.0)),
        )
        for item in raw
    ]
    return AnswerResult(candidates=candidates, prompt=prompt, usage=result.usage)


__all__ = [
    "AnswerResult",
    "build_prediction_range",
    "generate_answer",
    "parse_prediction_value",
]
