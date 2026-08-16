"""ST1/ST2/ST3 label sets, Pydantic structured-output schemas, and st3 postprocessing
(the thin-segment override and the no_flag/insufficient_context exclusivity rule).

Split out of baseline_gpt.py (which re-exports the names below for its existing external
consumers).
"""
import os
import re
import sys
from typing import List, Literal

from pydantic import BaseModel, Field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "starting_kit"))
from check_submission import ST1, ST2, ST3

ST1_LABELS = sorted(ST1)
ST2_LABELS = sorted(ST2)
ST3_LABELS = sorted(ST3)

ST3_FAMILY = {
    "undisclosed_advertising": "disclosure",
    "inadequate_disclosure": "disclosure",
    "direct_exhortation": "content",
    "misleading_claim": "content",
    "age_restricted_or_prohibited_product": "product",
    "hfss_food_marketing": "product",
    "no_flag": "housekeeping",
    "insufficient_context": "housekeeping",
}
FAMILY_LABELS = ["disclosure", "content", "product", "housekeeping"]
assert set(ST3_FAMILY) == ST3

class Prediction(BaseModel):
    st1: Literal[tuple(ST1_LABELS)] = Field(description="Single commercial-type label")
    st2: List[Literal[tuple(ST2_LABELS)]] = Field(description="One or more product-category labels")
    st3: List[Literal[tuple(ST3_LABELS)]] = Field(description="One or more compliance risk flags")

class ST3Prediction(BaseModel):
    st3: List[Literal[tuple(ST3_LABELS)]] = Field(description="One or more compliance risk flags")

class ST3PredictionCoT(BaseModel):
    """--cot inline variant: `reasoning` comes before `st3` so the model generates it first
    (structured output is autoregressive -- field order is generation order), forcing it to
    work through the prompt's own checklists against this segment's specific text before
    committing to labels, instead of jumping straight to a conclusion. See COT_INSTRUCTIONS
    in st3_prompts.py for the guidance text that tells the model how to use this field."""
    reasoning: str = Field(description=(
        "Work through the checks relevant to this segment (see the system prompt) against its "
        "actual text -- which checks apply, what evidence (or absence of it) drove each "
        "conclusion, and for commonly-confused label pairs, which side of the line this segment "
        "fell on and why. A few sentences; do not restate the taxonomy definitions."
    ))
    st3: List[Literal[tuple(ST3_LABELS)]] = Field(description="One or more compliance risk flags")

# insufficient_context (T1.9) calibration -- see runs/impl_insufficient_context/ for the source
# agent's derivation. Direct inspection of every train+dev gold insufficient_context row (22
# total, a very rare label) shows it's a near-deterministic structural pattern, not a semantic
# judgment call: the transcript segment is degenerate ([Music]/[Applause]/filler words/empty)
# *and* the video description isn't specifically promotional (no explicit sponsor/promo-code
# language) -- matching the taxonomy's own framing ("too short or ambiguous to assess") and
# st3_findings.md's context-rung note that this label needs BOTH the transcript and description
# to be thin. Transcript length alone is necessary but not sufficient: of the 72 train+dev rows
# with a near-empty transcript, only 14 are actually gold insufficient_context -- the rest carry
# a real violation flag, and the description is what discriminates them (sponsor/promo-code
# language is absent from 100% of a 15-row train sample of genuine insufficient_context rows, vs.
# present in ~31% of the "thin transcript but really a different flag" rows). Requiring both
# raises standalone train+dev precision/recall/F1 from best-transcript-alone (P=0.194, R=0.636,
# F1=0.298 at this same length threshold) to P=0.350, R=0.636, F1=0.452 -- the best of several
# transcript-length x description-filter combinations tried empirically.
THIN_TRANSCRIPT_MAX_LEN = 35  # chars of "real" transcript content remaining after stripping noise
_THIN_BRACKET_RE = re.compile(r"\[[^\]]*\]|\*[^*]*\*")  # [Music]/[Applause]/*outro* tokens
_THIN_FILLER_WORD_RE = re.compile(
    r"\b(um|uh|oh|so|do|hey|okay|ok|bye|yes|no|good|well|hmm|foreign|people)\b", re.I
)
_THIN_PROMO_RE = re.compile(
    r"sponsor|partnered? with|paid partnership|#ad\b|% ?off|promo ?code|discount ?code|"
    r"use code|coupon",
    re.I,
)


def _transcript_content_len(text: str) -> int:
    """What's left of a transcript after stripping bracketed noise tokens and a short list of
    English filler words. Near-zero for the degenerate windows insufficient_context's gold rows
    are drawn from; substantial for real speech (including non-Latin-script transcripts, which
    this counts by character length rather than English word-splitting)."""
    stripped = _THIN_BRACKET_RE.sub(" ", text)
    stripped = _THIN_FILLER_WORD_RE.sub(" ", stripped)
    return len(re.sub(r"\s+", " ", stripped).strip())


def is_thin_segment(instance: dict) -> bool:
    """True when the transcript is near-empty/filler-only AND the video description carries no
    explicit sponsor/promo-code language -- the empirical pattern behind insufficient_context
    (see the calibration note above THIN_TRANSCRIPT_MAX_LEN). Deliberately requires both: an
    empty transcript paired with a promo-heavy description ("sponsored by X, code Y for 15%
    off") usually means a real violation flag applies and the description alone carries enough
    evidence to judge it, not that the segment is unassessable.
    This heuristic is intentionally imperfect (standalone F1 ~0.45 against train+dev gold) --
    it's meant to correct a specific, confirmed model failure (see sanitize_st3), not to be a
    complete classifier on its own; a handful of genuine insufficient_context rows have either a
    longer transcript than this threshold or promo-style language in an unrelated, boilerplate
    channel-wide description block, and this function will not catch those."""
    transcript_text = instance["transcript"]["text"]
    if _transcript_content_len(transcript_text) > THIN_TRANSCRIPT_MAX_LEN:
        return False
    description = instance["video_context"]["description"]
    return not _THIN_PROMO_RE.search(description)


def sanitize_st3(flags: List[str], instance: dict = None, use_thin_override: bool = False) -> List[str]:
    """Enforce the 'no_flag'/'insufficient_context' stand-alone rule.

    Empty-list default is `no_flag`, not `insufficient_context`: empirically no_flag
    (529/2353 = 22.5% of train) outnumbers insufficient_context (15/2353 = 0.6%) roughly 35:1, so
    no_flag is the far more probable read of "the model didn't pick anything" even with zero
    other signal. ST3_SYSTEM_PROMPT's own TASK section requires no_flag to be emitted explicitly
    whenever no other check fires, so a genuinely empty list from that prompt is a compliance
    slip against an instruction pointing at no_flag, not a sign of thin content.

    `use_thin_override` (only set True on the --st3-only path -- see main(), since
    ST3_SYSTEM_PROMPT and is_thin_segment()'s calibration are both scoped to st3-only prediction;
    the joint st1/st2/st3 SYSTEM_PROMPT path is untouched by this override) additionally applies
    the is_thin_segment() deterministic backstop:

    insufficient_context turns out not to be something the model reliably self-reports: on a
    held-out validation batch, GPT predicted a real violation flag -- never insufficient_context,
    and never an empty list -- on every single genuine insufficient_context instance, apparently
    driven by promotional links elsewhere in the description even when the transcript segment
    itself carried no real content. A prompt-only fix (asking nicely) doesn't reach that;
    is_thin_segment() is a cheap, deterministic backstop:

    - if the segment is thin, insufficient_context wins outright, regardless of what the LLM
      predicted (the "force" direction -- this is what actually fixes the failure above);
    - if the segment is NOT thin, insufficient_context is stripped from the LLM's output even if
      it predicted it (the "suppress" direction, for the rarer case of the model guessing this
      label on a segment that isn't actually thin)."""
    if use_thin_override:
        if is_thin_segment(instance):
            return ["insufficient_context"]
        flags = [f for f in flags if f != "insufficient_context"]
        standalone = [f for f in flags if f == "no_flag"]
        if standalone and len(flags) > 1:
            return [standalone[0]]
        return flags or ["no_flag"]

    standalone = [f for f in flags if f in ("no_flag", "insufficient_context")]
    if standalone and len(flags) > 1:
        return [standalone[0]]
    return flags or ["no_flag"]

