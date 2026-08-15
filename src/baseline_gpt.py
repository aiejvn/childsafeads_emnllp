"""GPT baseline: predicts ST1, ST2, ST3 with GPT via LangChain structured output.

Requires OPENAI_API_KEY in the environment (or a .env file next to this script).

Writes predictions to runs/submission_gpt_<timestamp>.jsonl.

Usage:
    python baseline_gpt.py ../public_data_dev/dev.jsonl
    python baseline_gpt.py ../public_data_dev/dev.jsonl --sample-size 20  # smoke test
    python baseline_gpt.py ../public_data_dev/dev.jsonl --st3-only        # ST3 only, its own tuned prompt
    python baseline_gpt.py ../public_data_dev/dev.jsonl --st3-only --few-shot  # + live train.jsonl examples
    python baseline_gpt.py ../public_data_dev/dev.jsonl --lean-prompt --df-path ../emnllp-dialog-flow-dialog-flow.json

Prints macro-F1 for st1/st2/st3, the family-level st3 macro-F1, and their mean,
whenever the target split carries gold "labels" (train/dev, not the withheld test set).
--st3-only restricts prediction and scoring to st3 (no mean_macro_f1, since it blends all
three tiers) and writes to submission_gpt_st3.jsonl instead of the canonical
submission_gpt.jsonl. --lean-prompt and --df-path mirror the LoRA baselines' flags of the
same name, for a like-for-like comparison against them. --few-shot (st3-only only) appends
1-2 real train.jsonl examples each for direct_exhortation, inadequate_disclosure, and
insufficient_context to the system prompt, pairing each label's definition with a live
example.
"""
import argparse
import json
import logging
import os
import random
import shutil
import sys
from collections import Counter
from datetime import datetime
from typing import List, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "starting_kit"))
from check_submission import ST1, ST2, ST3
from load_data import full_context, load_split, transcript_only

# common/__init__.py imports names from this file, so importing the `common` package here
# would be circular. Import dialog_flow.py directly (as a top-level module, bypassing
# common/__init__.py) instead.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "common"))
from dialog_flow import df_pre_context

from dotenv import load_dotenv
load_dotenv()

LABELS_TAXONOMY_PATH = os.path.join(
    os.path.dirname(__file__), "..", "public_data_dev", "labels_taxonomy.md"
)
with open(LABELS_TAXONOMY_PATH, encoding="utf-8") as _f:
    LABELS_TAXONOMY = _f.read()

TRAIN_PATH = os.path.join(os.path.dirname(__file__), "..", "public_data_dev", "train.jsonl")

# --few-shot pairs each of these labels' definition with a live train.jsonl example. Definitions
# are parsed out of the `| T1.x | \`label\` | definition | ... |` rows in LABELS_TAXONOMY rather
# than duplicated here, so they can't drift from the taxonomy file.
FEW_SHOT_LABELS = ("direct_exhortation", "inadequate_disclosure", "insufficient_context",
                    "age_restricted_or_prohibited_product", "hfss_food_marketing", "undisclosed_advertising")

# Worst-performing labels get extra exemplars beyond the --few-shot-n default. For n>1, the
# first exemplar is always a "solo" instance (that flag is the ONLY st3 label -- see the
# set(st3) != {label} check below); the rest come from any instance carrying the flag, solo
# or not, since solo instances are scarce for some of these (13 for age_restricted_or_
# prohibited_product, 9 for hfss_food_marketing, out of ~500 train instances that carry the flag).
FEW_SHOT_N_OVERRIDES = {
    "inadequate_disclosure": 2,
    "age_restricted_or_prohibited_product": 2,
    "hfss_food_marketing": 2,
    "undisclosed_advertising": 2,
}


def parse_taxonomy_defs(taxonomy_text: str, labels) -> dict:
    """Pull {label: definition} for `labels` out of LABELS_TAXONOMY's `| T1.x | \`label\` | def | ... |` rows."""
    defs = {}
    for line in taxonomy_text.splitlines():
        if not line.startswith("| T1."):
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        label = cols[1].strip("`")
        if label in labels:
            defs[label] = cols[2]
    missing = set(labels) - set(defs)
    if missing:
        raise ValueError(f"couldn't find taxonomy definitions for {missing} in {LABELS_TAXONOMY_PATH}")
    return defs

# Same file common/__init__.py exposes as SFT_TAXONOMY, reloaded here rather than
# imported for the same reason as df_pre_context above.
SFT_TAXONOMY_PATH = os.path.join(os.path.dirname(__file__), "common", "labels_taxonomy_sft.md")
SFT_TAXONOMY_MARKER = "<!-- PROMPT CONTENT BELOW -->"
with open(SFT_TAXONOMY_PATH, encoding="utf-8") as _f:
    _sft_doc = _f.read()
if SFT_TAXONOMY_MARKER not in _sft_doc:
    raise ValueError(f"{SFT_TAXONOMY_PATH} is missing its {SFT_TAXONOMY_MARKER} marker")
SFT_TAXONOMY = _sft_doc.split(SFT_TAXONOMY_MARKER, 1)[1].strip() + "\n"

# Same rung common/__init__.py exposes as no_product_page(), reloaded here rather than
# imported for the same reason as df_pre_context above. Default --context: the product
# page is the largest rung and the one furthest from the segment (the destination of a
# link, not something the viewer is known to have seen), so this baseline reads only
# what the video itself carries.
CONTEXT_CHOICES = ["transcript", "no_product_page", "full"]


def no_product_page(instance: dict) -> str:
    v = instance["video_context"]
    return (f"TRANSCRIPT:\n{instance['transcript']['text']}\n\n"
            f"VIDEO: {v['title']}\nDESCRIPTION:\n{v['description']}\n"
            f"OFFICIAL_DISCLOSURE: {v['official_disclosure']}")

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

SYSTEM_PROMPT = """You are a compliance analyst at an authority monitoring commercial content \
that reaches minors on video platforms. You are given one sponsored segment (transcript, the \
host video's metadata, and the product page its description links to). It is a GIVEN FACT that \
the segment is commercial and that the channel is child-facing; do not re-assess either.

Predict three sub-tasks -- ST1 (commercial type, exactly one label), ST2 (product category, one \
or more labels), and ST3 (compliance risk flags, one or more labels) -- using the label taxonomy \
below, which gives the full definitions, examples, and legal basis for each label. Base every \
judgment only on the text given. Respond with the structured prediction only.

Before finalizing ST3, run these checks explicitly. Two failure modes are equally live: missing \
a real concern (do not default to no_flag or insufficient_context just because you are unsure) \
and inventing one the text doesn't support (do not pad out flags to be safe, or apply a check \
reflexively once you've decided the segment is commercial). Work through each check below on the \
specific evidence in front of you:

- misleading_claim: you are NOT verifying whether a claim is true, only identifying claims of \
the kind the taxonomy covers -- an unsubstantiated or high-risk claim about the product's own \
characteristics, performance, or results (or any health/fitness/skincare/supplement efficacy \
claim, always flag those). Distinguish two things that sound similar: (a) vague subjective \
opinion/puffery with no specific fact attached ("amazing", "the best", "insane refresh speeds", \
"won't break the bank", "high-quality", "you really should [try it]") is normal ad talk and is NOT \
misleading_claim by itself; (b) a specific, quantified, or factual-sounding assertion presented as \
fact ("30% more breathability", "reduces hip pressure by 20%", "without slowing your internet \
speeds down whatsoever", a named certification/study/guarantee, a specific price/discount claimed \
to be unbeatable) IS misleading_claim, because it reads as a verifiable factual claim the segment \
gives no support for. This applies even when delivered in ordinary, polished sponsor-read style --\
 confident language about what the product concretely *does*, with a specific fact attached, is \
what this flag is for; confident language that stays at the level of opinion/hype is not.
- direct_exhortation: apply the taxonomy's own three-part test below (Counts as exhortation / \
Does not count / Boundary) in full, not just its permissive half. Urgency or pressure aimed at \
the viewer counts even when phrased as an instruction -- "join X today", "there's no excuse not \
to try it", "don't pay full price, get it here instead" add time pressure or dismiss reasons not \
to act. But a neutral instruction that only states where/how to get something, with no pressure, \
stays an instruction -- "the link is in the description", "use my code for 15% off", "go give it \
a try" -- and where the wording is genuinely ambiguous between the two, the taxonomy's own rule \
is to not flag it.
- undisclosed_advertising vs. inadequate_disclosure: these are mutually exclusive, and mixing \
them up is a common error, so use this two-step procedure. Step 1: search the ENTIRE given text \
-- transcript and video description -- for ANY acknowledgment that the segment involves a \
commercial relationship: sponsorship ("sponsor of this video", "sponsored by", "thanks to X for \
sponsoring"), a paid partnership/ad label, or an affiliate-link disclaimer ("contains affiliate \
links", "using affiliate links supports us", "I'll receive a commission"). If there is truly none \
anywhere, that is undisclosed_advertising. Step 2: if you found such an acknowledgment, judge \
whether it is clear and prominent enough for a child to understand this content is paid for (no \
disclosure issue) or buried, brief, generic legal/affiliate boilerplate, or otherwise unclear to a \
child (inadequate_disclosure) -- weigh several signals together rather than any single one \
decisively: OFFICIAL_DISCLOSURE being true is a meaningful positive signal (not proof by itself) \
and false leans toward inadequate; an explicit plain-language sponsor/ad statement made early, \
before or alongside the pitch, and repeated in more than one place (both spoken and in the \
description) leans toward adequate; a disclosure mentioned only once, only briefly, only after the \
persuasive pitch is already over, or that is the ONLY channel to mention it at all (e.g. a bare \
promo code/link with no explicit "sponsor"/"ad" language, or an affiliate-link legal disclaimer \
with no plain-language sponsor statement) leans toward inadequate. When the signals genuinely \
conflict, weigh the totality of them rather than defaulting to either outcome -- do not apply \
inadequate_disclosure reflexively to every sponsor mention regardless of context, and do not wave \
one through just because some disclosure language appears somewhere in the text.

For ST1, when a service is delivered through an app or website but performed by a human \
professional (e.g. a therapist, coach, stylist, tutor giving live instruction), classify it as \
physical_services, not digital_content_or_services -- the deciding test is whether a human \
performs the service, not which channel delivers it. Reserve digital_content_or_services for \
offerings with no human performance (software, streaming, hosting, VPNs, self-paced courses, \
in-game currency).

""" + LABELS_TAXONOMY

# A dedicated copy for --st3-only, rather than reusing SYSTEM_PROMPT with st1/st2 ignored.
ST3_SYSTEM_PROMPT = """You are a compliance analyst monitoring commercial content that reaches minors on video platforms.

You are given one sponsored segment: its transcript, video metadata, and the product-page description
linked from the video.

It is GIVEN that:
- the channel is child-facing;
- the segment is commercial.

Do not reassess either fact.

## TASK

Predict ONLY these four ST3 labels:

- `misleading_claim` (T1.4)
- `age_restricted_or_prohibited_product` (T1.5)
- `hfss_food_marketing` (T1.6)
- `undisclosed_advertising` (T1.1)

Ignore all other taxonomy categories, including `inadequate_disclosure`,
`direct_exhortation`, Tier 2 flags, and `undisclosed_synthetic_content`.

Multiple labels may apply.

Base judgments only on the supplied material. Do not verify claims against the outside world
and do not invent missing facts.

## DETECTION STANDARD

Use a HIGH-RECALL, ADVERSARIAL reading. Modern advertising may deliberately avoid obvious
trigger phrases by disguising claims as personal experiences, testimonials, demonstrations,
storytelling, humor, recommendations, lifestyle content, or casual creator speech.

Look for the underlying meaning, not just keywords.

In particular, search for:
- factual claims hidden inside anecdotes or testimonials;
- outcomes implied by demonstrations or before/after framing;
- claims split across multiple sentences;
- comparisons or price claims expressed indirectly;
- health/fitness/skincare/supplement claims framed as personal experience;
- age-restricted products marketed through euphemisms or lifestyle branding;
- HFSS products marketed through gaming, sports, entertainment, or youth culture;
- sponsorship disclosures hidden in descriptions or metadata.

Do not flag merely because something sounds promotional. The evidence must satisfy the
specific category test.

## T1.4 — misleading_claim

Flag unsubstantiated or high-risk claims about a product's characteristics, performance,
results, or price.

You are identifying claims of this type, NOT determining whether they are true.

Flag concrete factual-sounding claims whether they are:
- explicit or implied;
- quantified or qualitative;
- comparative;
- presented as personal experience/testimonial;
- communicated through a demonstration;
- about price, savings, guarantees, certifications, or performance.

Examples of the underlying type:
"lasts twice as long", "reduces pressure by 20%", "cheapest option",
"this fixed my acne", "this helps me lose weight", "better than X".

Health, weight, fitness, skincare, and supplement efficacy claims directed at children
are ALWAYS in scope.

Do NOT flag ordinary subjective puffery alone:
"amazing", "the best", "insane", "high-quality", "I love it", etc.
unless surrounding context gives it a concrete factual meaning.

## T1.5 — age_restricted_or_prohibited_product

Flag when the promoted product/service itself is clearly age-gated or prohibited, including:

- alcohol;
- tobacco/nicotine/vaping;
- gambling/betting/casinos;
- weapons/firearms;
- similar clearly age-restricted products.

Identify the actual promoted product using the transcript, metadata, and product description.

Do not flag incidental mentions, mature themes, or unrelated products appearing alongside
an age-restricted item.

Be alert to euphemistic branding that disguises what the product actually is.

## T1.6 — hfss_food_marketing

Flag CLEAR marketing of food high in fat, salt, or sugar.

Clear examples include:
- energy drinks;
- confectionery/candy/chocolate;
- sugary soft drinks when clearly identifiable;
- fast food such as burgers, fries, or comparable products.

Use HIGH PRECISION here. Do not perform speculative nutrient profiling or flag borderline
foods merely because they could contain substantial fat, salt, or sugar.

The HFSS product must be what is being promoted, not merely something incidentally consumed
or shown.

## T1.1 — undisclosed_advertising

Flag if the commercial nature of the segment is NOT identified anywhere available to the viewer:

- spoken content;
- video description;
- supplied metadata;
- platform paid-promotion label.

Search ALL of these before deciding.

Disclosures include clear statements such as:
- "sponsored by X";
- "this video is sponsored";
- "paid partnership";
- "advertisement"/"ad";
- "affiliate links";
- "I receive a commission";
- equivalent language clearly identifying a commercial relationship.

A product link, promo code, "check it out", "my links", or shopping URL is NOT by itself
a disclosure.

IMPORTANT: `inadequate_disclosure` is OUT OF SCOPE. If a disclosure exists but is buried,
brief, jargon-heavy, or otherwise inadequate, do NOT convert it into another label.
For this task, the only question is whether the commercial nature is identified at all:

NO disclosure anywhere -> `undisclosed_advertising`
ANY meaningful disclosure -> no `undisclosed_advertising`

## FINAL ADVERSARIAL PASS

Before finalizing, assume the advertiser may be deliberately staying just below obvious
detection thresholds.

Re-check for:
- claims disguised as opinions or anecdotes;
- implied product outcomes;
- euphemistic restricted products;
- obvious HFSS products disguised by lifestyle/entertainment branding;
- disclosures hidden outside the spoken sponsor segment.

Then perform a precision check on every proposed flag:

- Does the exact evidence satisfy the category?
- Am I flagging the underlying behavior rather than a keyword?
- For `misleading_claim`, is there a concrete factual/product claim rather than puffery?
- For `age_restricted_or_prohibited_product`, is the restricted product actually being promoted?
- For `hfss_food_marketing`, is this clearly HFSS rather than borderline?
- For `undisclosed_advertising`, did I search the entire supplied disclosure material?

Drop flags that fail the precise test.

Respond with the structured prediction ONLY."""


class Prediction(BaseModel):
    st1: Literal[tuple(ST1_LABELS)] = Field(description="Single commercial-type label")
    st2: List[Literal[tuple(ST2_LABELS)]] = Field(description="One or more product-category labels")
    st3: List[Literal[tuple(ST3_LABELS)]] = Field(description="One or more compliance risk flags")


class ST3Prediction(BaseModel):
    st3: List[Literal[tuple(ST3_LABELS)]] = Field(description="One or more compliance risk flags")


def sanitize_st3(flags: List[str]) -> List[str]:
    """Enforce the 'no_flag'/'insufficient_context' stand-alone rule."""
    standalone = [f for f in flags if f in ("no_flag", "insufficient_context")]
    if standalone and len(flags) > 1:
        return [standalone[0]]
    return flags or ["insufficient_context"]


MAX_FEW_SHOT_EXAMPLE_LEN = 300  # skip, don't truncate -- a chopped quote/excerpt reads as garbled


def build_few_shot_section(train_path: str, log: logging.Logger, n_per_label: int = 1) -> str:
    """n_per_label live examples per FEW_SHOT_LABELS (overridable per label via
    FEW_SHOT_N_OVERRIDES), pulled from train.jsonl gold labels. Most labels use the quote in
    labels.st3_evidence that earned the flag; insufficient_context has no evidence quote
    (there's nothing to point at), so it uses a transcript excerpt instead.
    For the evidence-quote labels, the FIRST exemplar collected is always a "solo" instance --
    that flag is the SOLE st3 label on it, so it's a clean example of the boundary the flag is
    testing rather than a mixed case. Once a label has its solo exemplar, further slots (for
    labels with n>1) accept a quote from any instance carrying the flag, solo or not, since solo
    instances are scarce for some labels.
    Candidates longer than MAX_FEW_SHOT_EXAMPLE_LEN are skipped rather than truncated, so every
    example shown is a complete, unmutilated quote/excerpt."""
    defs = parse_taxonomy_defs(LABELS_TAXONOMY, FEW_SHOT_LABELS)
    target_n = {label: FEW_SHOT_N_OVERRIDES.get(label, n_per_label) for label in FEW_SHOT_LABELS}
    evidence_labels = tuple(label for label in FEW_SHOT_LABELS if label != "insufficient_context")
    examples = {label: [] for label in FEW_SHOT_LABELS}
    has_solo = {label: False for label in evidence_labels}
    for inst in load_split(train_path):
        if all(len(v) >= target_n[label] for label, v in examples.items()):
            break
        labels = inst.get("labels")
        if not labels:
            continue
        st3 = labels.get("st3", [])
        if "insufficient_context" in st3 and len(examples["insufficient_context"]) < target_n["insufficient_context"]:
            text = transcript_only(inst).strip()
            if text and len(text) <= MAX_FEW_SHOT_EXAMPLE_LEN:
                examples["insufficient_context"].append(text)
        evidence = {ev["flag"]: ev["quote"] for ev in labels.get("st3_evidence", [])}
        for label in evidence_labels:
            if len(examples[label]) >= target_n[label]:
                continue
            quote = evidence.get(label)
            if not quote or len(quote) > MAX_FEW_SHOT_EXAMPLE_LEN:
                continue
            is_solo = set(st3) == {label}
            if not is_solo and not has_solo[label]:
                continue  # keep looking for a solo exemplar before accepting a mixed one
            examples[label].append(quote)
            has_solo[label] = has_solo[label] or is_solo

    missing = [label for label, exs in examples.items() if not exs]
    if missing:
        raise ValueError(f"found no train.jsonl examples for {missing} in {train_path}")

    log.info("few-shot examples collected: " +
             ", ".join(f"{label}={len(exs)}" for label, exs in examples.items()))

    sections = ["## FEW-SHOT EXAMPLES\n\nLive examples from the training data, pairing each "
                "label's definition with real evidence that earned it."]
    for label in FEW_SHOT_LABELS:
        kind = "transcript excerpt" if label == "insufficient_context" else "evidence quote"
        lines = [f"### `{label}`", f"Definition: {defs[label]}"]
        lines += [f'Example {i} ({kind}): "{ex}"' for i, ex in enumerate(examples[label], 1)]
        sections.append("\n".join(lines))
    return "\n\n".join(sections)


def setup_logging(log_dir: str, method: str, model: str, timestamp: str) -> logging.Logger:
    """Log everything (config, warnings, gold-label inventory, results) to console + a run file."""
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"run_{timestamp}_{method}_{model}.log")

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(threadName)s | %(message)s")
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(fmt)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"logging to {log_path}")
    return logger


def log_gold_label_inventory(logger: logging.Logger, gold: List[dict]) -> None:
    """Log the distinct gold labels observed in this run, one line per tier."""
    st1_seen = {g["st1"] for g in gold}
    st2_seen = {label for g in gold for label in g["st2"]}
    st3_seen = {label for g in gold for label in g["st3"]}
    logger.info("=== Distinct gold labels observed, by tier ===")
    logger.info(f"[ST1 - commercial type]     {sorted(st1_seen)}")
    logger.info(f"[ST2 - product category]    {sorted(st2_seen)}")
    logger.info(f"[ST3 - compliance flags]    {sorted(st3_seen)}")


# Dedicated copies of common/predict_utils.py's log_label_diagnostics/log_prediction_diagnostics
# (used by the LoRA/last_layer baselines) rather than importing them -- common/__init__.py does
# `from baseline_gpt import ...`, so importing back from common here would be circular.
def log_label_diagnostics(logger: logging.Logger, tier: str, gold_labels: list, pred_labels: list) -> None:
    """Logs `tier`'s label distribution -- how often each label appears in gold vs. how often
    the model predicts it, overall -- and the gold-label x predicted-label cross-product
    counts: the co-occurrence of every (gold, pred) label pair within the same instance,
    tallied over `zip(gold_labels, pred_labels)`. Surfaces systematic confusions (e.g. an
    inadequate_disclosure gold flag consistently landing next to an undisclosed_advertising
    prediction) and under/over-flagging bias that per-label F1 alone doesn't show.
    `gold_labels`/`pred_labels` are parallel lists, one label collection (a list, even a
    singleton one for a single-label tier) per instance."""
    gold_counts = Counter(f for flags in gold_labels for f in flags)
    pred_counts = Counter(f for flags in pred_labels for f in flags)
    labels = sorted(set(gold_counts) | set(pred_counts))
    logger.info(f"[{tier}] label distribution (gold / pred):")
    for label in labels:
        logger.info(f"  {label}: gold={gold_counts[label]}, pred={pred_counts[label]}")

    cross = Counter()
    for g_flags, p_flags in zip(gold_labels, pred_labels):
        for g in g_flags:
            for p in p_flags:
                cross[(g, p)] += 1
    logger.info(f"[{tier}] gold x pred cross-product counts (gold -> pred: count):")
    for (g, p), count in sorted(cross.items(), key=lambda kv: (-kv[1], kv[0])):
        logger.info(f"  {g} -> {p}: {count}")


def log_prediction_diagnostics(logger: logging.Logger, gold: list, pred: list,
                                tiers: tuple = ("st1", "st2", "st3")) -> None:
    """st1/st2/st3-shaped wrapper around `log_label_diagnostics`: `gold`/`pred` are the
    same {"st1": str, "st2": [...], "st3": [...]} dicts `evaluate()` uses. `tiers`
    restricts the diagnostics to the tiers `pred` actually carries (e.g. --st3-only)."""
    logger.info("=== Prediction diagnostics ===")
    for tier in tiers:
        gold_labels = [[g["st1"]] for g in gold] if tier == "st1" else [g[tier] for g in gold]
        pred_labels = [[p["st1"]] for p in pred] if tier == "st1" else [p[tier] for p in pred]
        log_label_diagnostics(logger, tier, gold_labels, pred_labels)


def build_messages(instance: dict, context: str, system_prompt: str) -> list:
    if context == "full":
        text = full_context(instance)
    elif context == "no_product_page":
        text = no_product_page(instance)
    else:
        text = transcript_only(instance)
    return [SystemMessage(system_prompt), HumanMessage(f"SEGMENT DATA:\n\n{text}")]


def macro_f1(y_true: List[list], y_pred: List[list], labels: List[str]) -> tuple:
    """Macro-F1 over multi-label sets, averaged across `labels`. Returns (macro_f1, per_label_f1)."""
    per_label = {}
    # Iterate over labels to avoid having to O(n^2) loop over every y_true and check if it is in y_pred (or vice-versa)
    for label in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if label in t and label in p)
        fp = sum(1 for t, p in zip(y_true, y_pred) if label not in t and label in p)
        fn = sum(1 for t, p in zip(y_true, y_pred) if label in t and label not in p)
        if tp == 0 and fp == 0 and fn == 0:
            continue  # label absent from both gold and predictions; skip like sklearn does
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall + 10e-6)
        per_label[label] = f1
    macro = sum(per_label.values()) / len(per_label) if per_label else 0.0
    return macro, per_label


def prediction_errors(gold: dict, pred: dict, tiers: tuple = ("st1", "st2", "st3")) -> dict:
    """Diff a prediction against gold, tier by tier. Returns {} if fully correct;
    otherwise one entry per wrong tier describing exactly what was wrong. `tiers`
    restricts the diff to the tiers `pred` actually carries (e.g. --st3-only)."""
    errors = {}
    if "st1" in tiers and pred["st1"] != gold["st1"]:
        errors["st1"] = {"gold": gold["st1"], "pred": pred["st1"]}
    for tier in ("st2", "st3"):
        if tier not in tiers:
            continue
        missing = sorted(set(gold[tier]) - set(pred[tier]))  # gold labels the prediction missed
        extra = sorted(set(pred[tier]) - set(gold[tier]))    # predicted labels not in gold
        if missing or extra:
            errors[tier] = {"missing": missing, "extra": extra}
    return errors


def evaluate(gold: List[dict], pred: List[dict], tiers: tuple = ("st1", "st2", "st3")) -> dict:
    """`tiers` restricts scoring to the tiers `pred` actually carries (e.g. --st3-only,
    where pred has no st1/st2 to score, and mean_macro_f1 -- a blend of all three -- is
    meaningless)."""
    metrics, per_label = {}, {}
    if "st1" in tiers:
        metrics["st1_macro_f1"], per_label["st1"] = macro_f1(
            [[g["st1"]] for g in gold], [[p["st1"]] for p in pred], ST1_LABELS
        )
    if "st2" in tiers:
        metrics["st2_macro_f1"], per_label["st2"] = macro_f1(
            [g["st2"] for g in gold], [p["st2"] for p in pred], ST2_LABELS
        )
    if "st3" in tiers:
        metrics["st3_macro_f1"], per_label["st3"] = macro_f1(
            [g["st3"] for g in gold], [p["st3"] for p in pred], ST3_LABELS
        )
        fam = lambda flags: [ST3_FAMILY[f] for f in flags]
        metrics["st3_family_macro_f1"], per_label["st3_family"] = macro_f1(
            [fam(g["st3"]) for g in gold], [fam(p["st3"]) for p in pred], FAMILY_LABELS
        )
    if set(("st1", "st2", "st3")) <= set(tiers):
        metrics["mean_macro_f1"] = (metrics["st1_macro_f1"] + metrics["st2_macro_f1"] + metrics["st3_macro_f1"]) / 3
    metrics["per_label_f1"] = per_label
    return metrics


# From repo root:
# python src/baseline_gpt.py public_data_dev/dev.jsonl --sample-size 10 

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="split file to predict on, e.g. dev.jsonl")
    ap.add_argument("--model", default="gpt-5.4")
    ap.add_argument("--context", choices=CONTEXT_CHOICES, default="full",
                     help="how much of the instance to show the model. no_product_page drops the "
                          "linked page entirely -- transcript + video title/description/disclosure only")
    ap.add_argument("--sample-size", type=int, default=None,
                     help="only run on a random sample of N instances (seeded, for smoke tests)")
    ap.add_argument("--max-concurrency", type=int, default=8)
    ap.add_argument("--st3-only", action="store_true",
                     help="predict only ST3 (compliance risk flags), with ST3_SYSTEM_PROMPT -- a "
                          "copy of the system prompt tuned for st3 alone -- instead of the full "
                          "st1/st2/st3 prompt. Output rows and scoring both drop st1/st2 (no "
                          "mean_macro_f1); writes to submission_gpt_st3.jsonl instead of the "
                          "canonical submission_gpt.jsonl so it can't clobber a full run's output")
    ap.add_argument("--lean-prompt", action="store_true",
                     help="use common.SFT_TAXONOMY in place of the full system prompt (whichever "
                          "of SYSTEM_PROMPT/ST3_SYSTEM_PROMPT --st3-only selects), for an apples-to"
                          "-apples comparison against the LoRA baselines' --lean-prompt. It drops "
                          "the ST1/ST3 definitions the dialog flow would otherwise supply, so pair "
                          "it with --df-path")
    ap.add_argument("--df-path", default=None,
                     help="path to a dialog-flow export (e.g. emnllp-dialog-flow-dialog-flow.json), "
                          "rendered and appended to the system prompt -- for compatibility with the "
                          "LoRA baselines' --df-path; rendering (lean text vs. raw JSON) follows "
                          "--lean-prompt")
    ap.add_argument("--few-shot", action="store_true",
                     help="st3-only only: append a FEW-SHOT EXAMPLES section to the system prompt "
                          "-- for direct_exhortation, inadequate_disclosure, and insufficient_context, "
                          "--few-shot-n live train.jsonl example(s) each, pairing the label's "
                          "taxonomy definition with real evidence that earned it")
    ap.add_argument("--few-shot-n", type=int, default=1,
                     help="live train.jsonl examples per label to include when --few-shot is set")
    ap.add_argument("--seed", type=int, default=None, help="for example, 42.")
    args = ap.parse_args()

    if args.few_shot and not args.st3_only:
        raise SystemExit("--few-shot only applies to --st3-only")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log = setup_logging("runs", args.context, args.model, timestamp)
    out = os.path.join("runs", f"submission_gpt_{timestamp}.jsonl")
    error_out = os.path.join("runs", f"submission_gpt_error_{timestamp}.jsonl")
    log.info(f"config: target={args.target} model={args.model} context={args.context} "
             f"sample_size={args.sample_size} max_concurrency={args.max_concurrency} "
             f"st3_only={args.st3_only} lean_prompt={args.lean_prompt} df_path={args.df_path} "
             f"few_shot={args.few_shot} few_shot_n={args.few_shot_n} out={out} seed={args.seed}")

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("Set OPENAI_API_KEY in the environment (or a .env file) first.")

    tiers = ("st3",) if args.st3_only else ("st1", "st2", "st3")
    prediction_schema = ST3Prediction if args.st3_only else Prediction

    base_prompt = SFT_TAXONOMY if args.lean_prompt else (ST3_SYSTEM_PROMPT if args.st3_only else SYSTEM_PROMPT)
    if args.few_shot:
        few_shot_text = build_few_shot_section(TRAIN_PATH, log, n_per_label=args.few_shot_n)
        log.info(f"appending few-shot examples ({len(few_shot_text)} chars) to the system prompt")
        base_prompt = f"{base_prompt}\n\n{few_shot_text}"
    df_text = None
    if args.df_path:
        df_text = df_pre_context(args.df_path, lean=args.lean_prompt)
        form = "stripped dialog flow" if args.lean_prompt else "raw autoDF JSON"
        log.info(f"appending {form} from {args.df_path} ({len(df_text)} chars) to the system prompt")
    system_prompt = f"{base_prompt}\n\n{df_text}" if df_text else base_prompt
    log.info(f"system prompt: {'lean' if args.lean_prompt else 'full'}"
             f"{' st3-only' if args.st3_only else ''}{' few-shot' if args.few_shot else ''} "
             f"({len(system_prompt)} chars)")

    instances = list(load_split(args.target))
    if args.sample_size:
        instances = random.Random(args.seed).sample(instances, min(args.sample_size, len(instances)))

    llm = ChatOpenAI(model=args.model, temperature=0).with_structured_output(
        prediction_schema, method="json_schema", strict=True
    )
    batch_inputs = [build_messages(inst, args.context, system_prompt) for inst in instances]

    # Parallel batch requests to AI API
    # Returns output in a list, each elem maps to 1 query
    results = llm.batch(batch_inputs, config={"max_concurrency": args.max_concurrency},
                         return_exceptions=True)

    predictions, gold = [], []
    n_errors = 0
    with open(out, "w", encoding="utf-8") as f, \
         open(error_out, "w", encoding="utf-8") as f_err:
        for inst, result in zip(instances, results):
            if isinstance(result, Exception):
                log.warning(f"{inst['instanceID']} failed ({result})")
                pred = {"st3": [f"error:{result}"]} if args.st3_only \
                    else {"st1": "other", "st2": [], "st3": [f"error:{result}"]}
            elif args.st3_only:
                pred = {"st3": sanitize_st3(result.st3)}
            else:
                pred = {"st1": result.st1, "st2": result.st2, "st3": sanitize_st3(result.st3)}
            predictions.append(pred)
            f.write(json.dumps({"instanceID": inst["instanceID"], **pred}) + "\n")
            if inst.get("labels"):
                gold.append(inst["labels"])
                errors = prediction_errors(inst["labels"], pred, tiers=tiers)
                if errors:
                    n_errors += 1
                    f_err.write(json.dumps({
                        "instanceID": inst["instanceID"], "gold": inst["labels"],
                        "pred": pred, "errors": errors,
                    }) + "\n")
    log.info(f"wrote {len(predictions)} predictions to {out}")

    canonical = "submission_gpt_st3.jsonl" if args.st3_only else "submission_gpt.jsonl"
    shutil.copyfile(out, canonical)
    log.info(f"copied predictions to {canonical} (canonical submission file)")

    if gold:
        log.info(f"wrote {n_errors} misclassified instance(s) to {error_out}")

    if len(gold) == len(predictions) and gold:
        log_gold_label_inventory(log, gold)
        metrics = evaluate(gold, predictions, tiers=tiers)
        log.info("Evaluation:")
        for k, v in metrics.items():
            if k == "per_label_f1":
                continue
            log.info(f"  {k}: {v:.3f}")
        for tier, per_label in metrics["per_label_f1"].items():
            log.info(f"  {tier} per-label F1: " + ", ".join(f"{l}={f:.3f}" for l, f in sorted(per_label.items())))
        log_prediction_diagnostics(log, gold, predictions, tiers=tiers)
    else:
        log.info("target has no gold labels (or a partial mismatch) -- skipping evaluation")


if __name__ == "__main__":
    main()
