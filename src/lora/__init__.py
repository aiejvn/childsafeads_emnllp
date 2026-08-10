"""Barrel: re-exports the shared labels/eval/logging/data-loading pieces from
`common/` (which itself re-exports from `baseline_gpt.py` and
`starting_kit/load_data.py`) that the LoRA pipeline reuses, so label orderings, input
framing, and eval/logging stay identical across baselines.

Scripts under `src/lora/` are run from the repo root, e.g.
`python src/lora/lora_train.py public_data_dev/train.jsonl public_data_dev/dev.jsonl ...`
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common import (  # noqa: E402
    ST1_LABELS, ST2_LABELS, ST3_LABELS, Prediction, SYSTEM_PROMPT, SFT_TAXONOMY,
    evaluate, prediction_errors, sanitize_st3, setup_logging,
    full_context, load_split, transcript_only,
    CONTEXT_CHOICES, no_product_page, render_context,
)

__all__ = [
    "ST1_LABELS", "ST2_LABELS", "ST3_LABELS", "Prediction", "SYSTEM_PROMPT", "SFT_TAXONOMY",
    "evaluate", "prediction_errors", "sanitize_st3", "setup_logging",
    "full_context", "load_split", "transcript_only",
    "CONTEXT_CHOICES", "no_product_page", "render_context",
]
