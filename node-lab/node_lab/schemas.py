"""JSON Schemas for the three structured calls the distilled node makes.

SOURCE: apps/backend/src/node-execution/runners/lib/reasoning-node/reasoning-node.schemas.ts
        apps/backend/src/node-execution/runners/lib/reasoning-node/reflect-rationale.ts

Written as plain dicts rather than pydantic-generated so they satisfy OpenAI's
strict json_schema mode as-is: every property required, `additionalProperties`
false everywhere. `subAgentAnswerSchema` is not ported (stage dropped).
"""

from __future__ import annotations

ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "rationale": {
            "type": "string",
            "description": "The rationale in Markdown with `## Facts` / `## Analysis` sections.",
        }
    },
    "required": ["rationale"],
    "additionalProperties": False,
}

RATIONALE_REFLECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "findings": {
            "type": "array",
            "items": {"type": "string"},
            "description": "The specific defects fixed this pass, each naming the issue and where. Empty when the rationale was already clean.",
        },
        "revisedText": {
            "type": "string",
            "description": "The full corrected rationale. Preserve the draft verbatim except where a defect required a change. When clean, the input unchanged.",
        },
        "clean": {
            "type": "boolean",
            "description": "True only when no substantive change was made and nothing was found to fix.",
        },
    },
    "required": ["findings", "revisedText", "clean"],
    "additionalProperties": False,
}

# `prediction` is a required string (not a union) so Claude never sees a union
# exceeding its 16-type limit; `answer.py` coerces to the node's dataType.
# Empty string, "null", and "NULL" are the null sentinels.
PREDICTION_RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "predictions": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "properties": {
                    "prediction": {"type": "string"},
                    "probability": {"type": "number", "minimum": 0, "maximum": 1},
                },
                "required": ["prediction", "probability"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["predictions"],
    "additionalProperties": False,
}

__all__ = [
    "ANALYSIS_SCHEMA",
    "PREDICTION_RESULT_SCHEMA",
    "RATIONALE_REFLECTION_SCHEMA",
]
