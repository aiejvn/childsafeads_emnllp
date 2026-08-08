"""Barrel: re-exports the pieces of the LLM baseline (`baseline_gpt.py`) and the
starting-kit data loader (`starting_kit/load_data.py`) that the shared encoder utilities
(`classification_data.py`, `multitask_encoder.py`) and their consumers (`src/lora`,
`src/last_layer`) rely on, so label orderings, input framing, and eval/logging stay
identical across baselines. This is the single place that imports from `baseline_gpt`/
`starting_kit`; other packages re-export from here instead of importing those directly.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from baseline_gpt import (  # noqa: E402
    ST1_LABELS, ST2_LABELS, ST3_LABELS, Prediction, SYSTEM_PROMPT,
    evaluate, prediction_errors, sanitize_st3, setup_logging,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "starting_kit"))
from load_data import full_context, load_split, transcript_only  # noqa: E402

__all__ = [
    "ST1_LABELS", "ST2_LABELS", "ST3_LABELS", "Prediction", "SYSTEM_PROMPT",
    "evaluate", "prediction_errors", "sanitize_st3", "setup_logging",
    "full_context", "load_split", "transcript_only",
]
