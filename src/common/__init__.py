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

# The SFT-trimmed taxonomy, sibling to SYSTEM_PROMPT's full one. Meant to be paired with
# the stripped dialog flow (common.dialog_flow.flow_prompt_text) rather than with
# public_data_dev/labels_taxonomy.md; see the file's own header for what it drops.
SFT_TAXONOMY_PATH = os.path.join(os.path.dirname(__file__), "labels_taxonomy_sft.md")
SFT_TAXONOMY_MARKER = "<!-- PROMPT CONTENT BELOW -->"
with open(SFT_TAXONOMY_PATH, encoding="utf-8") as _f:
    _sft_doc = _f.read()
# The file explains its own trimming decisions to a human maintainer; only the part
# after the marker is prompt content. Splitting here keeps that rationale out of the
# token budget -- and out of reach of a model that would otherwise read the names of
# labels the "Dropped" table exists to exclude.
if SFT_TAXONOMY_MARKER not in _sft_doc:
    raise ValueError(f"{SFT_TAXONOMY_PATH} is missing its {SFT_TAXONOMY_MARKER} marker")
SFT_TAXONOMY = _sft_doc.split(SFT_TAXONOMY_MARKER, 1)[1].strip() + "\n"

# That file is hand-trimmed, so nothing keeps its label lists in sync with the ones
# check_submission defines. Fail at import rather than let a run train against a prompt
# that quietly stopped naming a label the model is still scored on.
_unnamed = [label for label in ST1_LABELS + ST2_LABELS + ST3_LABELS if f"`{label}`" not in SFT_TAXONOMY]
if _unnamed:
    raise ValueError(f"{SFT_TAXONOMY_PATH} no longer names these labels: {_unnamed}")

# The rungs of an instance a model is allowed to see. starting_kit/load_data.py ships
# the two ends -- transcript_only (rung 1) and full_context (everything) -- and
# no_product_page is the step between them.
CONTEXT_CHOICES = ["transcript", "no_product_page", "full"]


def no_product_page(instance: dict) -> str:
    """full_context minus its trailing PAGE block: transcript plus video metadata, with
    OFFICIAL_DISCLOSURE kept. Mirrors full_context's first two rungs verbatim, so
    --context full and --context no_product_page differ by exactly the page.

    The page is the largest rung (a median 38% of full_context's tokens, up to 92%) and
    the one furthest from the segment: it is the destination of a link in the
    description, not something the viewer is known to have seen. Only 0.9% of train
    instances carry a sponsorship/affiliate cue there and nowhere else, so it is cheap
    to test whether it earns its budget -- though ST2 may well need it, since the
    product category is often clearer on the page than in the read.
    """
    v = instance["video_context"]
    return (f"TRANSCRIPT:\n{instance['transcript']['text']}\n\n"
            f"VIDEO: {v['title']}\nDESCRIPTION:\n{v['description']}\n"
            f"OFFICIAL_DISCLOSURE: {v['official_disclosure']}")


def render_context(instance: dict, context: str = "full") -> str:
    """Single resolver for --context, so a new rung cannot be silently mishandled: the
    `full_context(x) if context == "full" else transcript_only(x)` idiom this replaces
    quietly degrades every unrecognised value to transcript-only."""
    if context == "full":
        return full_context(instance)
    if context == "no_product_page":
        return no_product_page(instance)
    if context == "transcript":
        return transcript_only(instance)
    raise ValueError(f"unknown context {context!r}, expected one of {CONTEXT_CHOICES}")


__all__ = [
    "ST1_LABELS", "ST2_LABELS", "ST3_LABELS", "Prediction", "SYSTEM_PROMPT",
    "SFT_TAXONOMY", "SFT_TAXONOMY_PATH",
    "evaluate", "prediction_errors", "sanitize_st3", "setup_logging",
    "full_context", "load_split", "transcript_only",
    "CONTEXT_CHOICES", "no_product_page", "render_context",
]
