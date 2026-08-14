"""GPT baseline: predicts ST1, ST2, ST3 with GPT via LangChain structured output.

Requires OPENAI_API_KEY in the environment (or a .env file next to this script).

Writes predictions to runs/submission_gpt_<timestamp>.jsonl.

Usage:
    python baseline_gpt.py ../public_data_dev/dev.jsonl
    python baseline_gpt.py ../public_data_dev/dev.jsonl --sample-size 20  # smoke test
    python baseline_gpt.py ../public_data_dev/dev.jsonl --st3-only        # ST3 only, its own tuned prompt
    python baseline_gpt.py ../public_data_dev/dev.jsonl --lean-prompt --df-path ../emnllp-dialog-flow-dialog-flow.json

Prints macro-F1 for st1/st2/st3, the family-level st3 macro-F1, and their mean,
whenever the target split carries gold "labels" (train/dev, not the withheld test set).
--st3-only restricts prediction and scoring to st3 (no mean_macro_f1, since it blends all
three tiers) and writes to submission_gpt_st3.jsonl instead of the canonical
submission_gpt.jsonl. --lean-prompt and --df-path mirror the LoRA baselines' flags of the
same name, for a like-for-like comparison against them.
"""
import argparse
import json
import logging
import os
import random
import shutil
import sys
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

Before finalizing ST3, run these checks explicitly -- do not default to no_flag or \
insufficient_context just because you are unsure; under-flagging is the more common failure mode:

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
- direct_exhortation: the taxonomy's test counts urgency aimed at the viewer as exhortation, not \
just an explicit "buy this" -- do not wave through an urgent or pressuring call to action just \
because it is phrased as an instruction. Phrases like "join X today", "go check out X right now", \
"there's no excuse not to try it", "don't pay full price, get it here instead" add time pressure \
or dismiss reasons not to act, which is exactly the "urgency aimed at the viewer" the test flags -- \
this is different from a neutral "the link is in the description" or "use my code for 15% off", \
which state where/how to get something without pressure and stay instructions.
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
conflict, prefer inadequate_disclosure over "no issue" -- under-flagging is the larger risk -- but \
do not apply it reflexively to every sponsor mention regardless of context.

For ST1, when a service is delivered through an app or website but performed by a human \
professional (e.g. a therapist, coach, stylist, tutor giving live instruction), classify it as \
physical_services, not digital_content_or_services -- the deciding test is whether a human \
performs the service, not which channel delivers it. Reserve digital_content_or_services for \
offerings with no human performance (software, streaming, hosting, VPNs, self-paced courses, \
in-game currency).

""" + LABELS_TAXONOMY

# A dedicated copy for --st3-only, rather than reusing SYSTEM_PROMPT with st1/st2 ignored.
# The first tuning pass (see runs/prompt_tuning/) targeted st3 by editing the shared prompt
# above and regressed st3_macro_f1 0.444 -> 0.314: the recall fixes below (misleading_claim
# scope, direct_exhortation urgency, the disclosure two-step) worked individually, but
# stacked together they overshot into over-flagging clean content (no_flag misses rose
# 7/100 -> 24/100). This copy keeps those recall fixes -- they did cut real misses -- but
# adds a closing precision pass so a future tuning round can push st3 further without
# re-triggering the same overshoot, and without touching st1/st2's prompt at all.
ST3_SYSTEM_PROMPT = """You are a compliance analyst at an authority monitoring commercial content
that reaches minors on video platforms. You are given one sponsored segment (transcript, the
host video's metadata, and the product page its description links to). It is a GIVEN FACT that
the segment is commercial and that the channel is child-facing; do not re-assess either.

Predict ST3 only -- compliance risk flags, one or more labels -- using the label taxonomy below,
which gives the full definitions, examples, and legal basis for each label. ST1 and ST2 are defined
in the same taxonomy for context on what is being sold; you are not asked to output them. Base
every judgment only on the text given. Respond with the structured prediction only.

IMPORTANT DETECTION STANDARD:

Use a SENSITIVE, ADVERSARIAL interpretation of the taxonomy. Modern advertising frequently avoids
literal trigger phrases by using implication, euphemism, conversational wording, humor, storytelling,
parasocial framing, soft recommendations, urgency without explicit deadlines, or disclosures that
are technically present but practically easy for a child to miss.

Do NOT require a canonical phrase, explicit "buy now", explicit "this is an ad", or an obviously
sales-like tone when the underlying communication performs the same function. Evaluate what the
statement communicates and how it functions in context, not merely its literal wording.

At the same time, do not invent facts or infer a violation from ordinary non-commercial language.
The text must provide evidence for the flag under the taxonomy. When evidence is genuinely
ambiguous, err toward the compliance flag rather than assuming the most charitable interpretation,
because the expected failure mode is under-detection.

Before finalizing, perform ALL of the following checks.

1. MISLEADING_CLAIM -- SEARCH FOR INDIRECT CLAIMS, NOT JUST EXPLICIT CLAIMS

You are NOT verifying whether a claim is true. Identify claims of the kind covered by the taxonomy:
an unsubstantiated or high-risk claim about the product's own characteristics, performance, or
results (or any health/fitness/skincare/supplement efficacy claim, always flag those).

Look for claims expressed in ANY of these forms:

- explicit factual assertions:
  "lasts twice as long", "reduces pressure by 20%", "works in 30 seconds"
- implied factual assertions:
  "I switched to this and suddenly my skin cleared up"
  "ever since I started using it, I haven't had that problem"
- causal claims embedded in a story or anecdote:
  "this is why I can finally sleep better"
  "using this is what fixed my back"
- before/after or outcome framing that communicates a concrete product result
- comparative claims:
  "faster than regular X", "better than the other options", "the only one that..."
- quantified or measurable implications even when the number is not presented as a
  formal statistic
- claims based on an alleged test, study, certification, expert, guarantee, review, or
  other authority
- absolute or near-absolute factual claims:
  "never breaks", "always works", "completely eliminates", "zero lag", "nothing else compares"
- factual-sounding claims disguised as personal experience:
  "I've used this for months and it has completely solved X"
- factual claims conveyed through demonstrations, comparisons, or descriptions of outcomes
- claims where the literal wording is hedged but the overall communication strongly communicates
  a concrete product effect:
  "it can really help with...", "you'll notice...", "this should make your..."
- product-specific health, safety, body, appearance, performance, financial, or functional
  outcomes, even when expressed casually.

Do NOT flag ordinary subjective puffery by itself:
"amazing", "the best", "insane", "high-quality", "I love it", "you should try it", etc.
The distinction is whether the communication conveys a concrete, factual-sounding product
property, capability, comparison, outcome, or result.

Pay particular attention to claims hidden inside otherwise non-claiming sentences. A sentence does
not become ordinary opinion merely because it is framed as the host's personal experience.

For health/fitness/skincare/supplement efficacy claims, use the taxonomy's explicit rule and flag
them even when the claim is informal, anecdotal, hedged, or presented as personal experience.

2. DIRECT_EXHORTATION -- DETECT PRESSURE EVEN WITHOUT "BUY NOW"

Do not limit this flag to explicit purchase commands.

The taxonomy's test includes urgency, pressure, and exhortation aimed at the viewer. Detect the
UNDERLYING ACTION PRESSURE, including when it is expressed indirectly.

Look for:

- explicit purchase commands: "buy it", "order now", "get yours"
- urgency: "today", "right now", "before it's too late", "don't wait"
- scarcity or deadline pressure: "while supplies last", "before the sale ends",
  "this offer won't last", "limited time"
- FOMO: "everyone is using this", "you don't want to miss this", "don't be the only one"
- dismissal of hesitation: "there's no reason not to", "what are you waiting for?",
  "you'd be crazy not to"
- financial urgency: "don't pay full price", "save before the code expires"
- social pressure: "your friends will thank you", "you need this", "everyone should have one"
- imperative or quasi-imperative wording whose practical purpose is to make the viewer act
- repeated or escalating calls to action
- rhetorical questions designed to push the viewer toward the advertised action
- soft commands disguised as friendly advice:
  "I'd definitely grab one", "go ahead and check it out",
  "you might as well get it now"
- parasocial pressure:
  "if you support me, go get one", "help the channel out by..."
  or equivalent framing that makes the viewer feel personally responsible for supporting
  the creator
- emotional pressure, guilt, fear of missing out, or implied consequences of not acting.

Do NOT automatically flag neutral acquisition information such as:

- "the link is in the description"
- "you can use my code for 15% off"
- "check out the product if you're interested"

unless surrounding language turns that information into actual pressure or urgency.

A call to action can be indirect. Judge the communicative function in context rather than requiring
an imperative verb.

3. UNDISCLOSED_ADVERTISING vs INADEQUATE_DISCLOSURE -- BE ESPECIALLY ALERT TO DISGUISED DISCLOSURES

These labels are mutually exclusive.

STEP 1:
Search the ENTIRE given text -- transcript, video metadata, and video description -- for ANY
acknowledgment that the segment involves a commercial relationship, including:

- "sponsored by"
- "sponsor of this video"
- "paid partnership"
- "advertisement"/"ad"
- "promotional consideration"
- "thanks to X for sponsoring"
- "affiliate link(s)"
- "I receive a commission"
- "using my link supports me"
- equivalent plain-language disclosures.

Do not stop after finding the first disclosure. Determine WHERE it appears, HOW clearly it is
communicated, and whether a reasonable child would understand the commercial relationship.

STEP 2:
If there is no meaningful acknowledgment anywhere, flag undisclosed_advertising.

If there IS an acknowledgment, evaluate whether it is sufficiently clear and prominent for a child.

Be alert to disclosures that are technically present but functionally ineffective, including:

- disclosure only in a long description
- disclosure buried among unrelated links, hashtags, or boilerplate
- disclosure using unexplained legal terminology
- disclosure that says "affiliate" or "commission" without making the commercial relationship
  understandable
- disclosure that is visually/linguistically easy to overlook
- disclosure appearing only after the persuasive segment
- disclosure appearing only after the viewer has already been encouraged to act
- disclosure that is extremely brief relative to a long persuasive pitch
- disclosure that is separated from the sponsored content
- disclosure that relies on a promo code or product link to imply sponsorship without saying so
- disclosure that is technically present but ambiguous about whether the creator was paid
- disclosure that says the creator "works with" or "partners with" a company without clearly
  communicating the advertising relationship
- disclosures hidden behind generic labels such as "resources", "links", "stuff I use",
  "support the channel", etc.
- affiliate disclaimers written for legal compliance but unlikely to be understood by a child.

Treat "affiliate link" and similar language as evidence of a commercial relationship, but do not
automatically treat it as an adequate child-facing disclosure.

OFFICIAL_DISCLOSURE being true is a meaningful positive signal, but is NOT conclusive by itself.
Consider timing, prominence, wording, placement, repetition, and child comprehensibility together.

An explicit plain-language sponsor/ad statement made before or alongside the pitch, especially
when repeated in both spoken content and the description, strongly supports adequate disclosure.

When signals conflict, prefer inadequate_disclosure over no issue when the disclosure could
reasonably fail to make the commercial nature clear to a child.

Do NOT reflexively flag every short sponsor disclosure. The question is whether it is genuinely
clear and understandable in context.

4. ADVERSARIAL / EVASIVE LANGUAGE PASS

After applying the ordinary taxonomy tests, perform a second pass assuming the advertiser/creator
is deliberately trying to stay just below obvious detection thresholds.

Search for:

- euphemisms replacing advertising terminology
- conversational recommendations that perform the function of an advertisement
- "personal story" framing that contains product claims
- testimonials that communicate objective results without stating them formally
- implied comparisons rather than explicit comparisons
- rhetorical questions that communicate claims or pressure
- jokes or sarcasm that nevertheless communicate a factual claim or purchase pressure
- scarcity/FOMO communicated without the words "limited time"
- urgency communicated through context rather than an explicit deadline
- social proof used to pressure action
- creator loyalty/fan identity being leveraged to encourage purchase
- "support me/the channel" framing that functions as a commercial exhortation
- claims split across multiple sentences where no single sentence contains the complete claim
- claims made by combining the host's statement with product-page language
- vague-sounding words whose surrounding context gives them a concrete factual meaning
- product demonstrations that implicitly promise a result
- "I personally use it" statements that implicitly function as endorsements or efficacy claims
- strategically placed disclosure language that is technically present but likely to be missed.

Do not require the suspicious behavior to match one of the taxonomy examples verbatim. Apply the
definition and legal test underlying the label.

5. CONTEXTUAL / COMBINED-EVIDENCE PASS

Do not evaluate every sentence in isolation when the meaning depends on nearby statements.

A sequence such as:

"I've been struggling with X."
"This product changed everything."
"You can get it with my code."
"Seriously, don't wait."

may collectively communicate a product-result claim and purchase pressure even if each individual
sentence is relatively informal.

Likewise, multiple weak signals may collectively make a disclosure inadequate. Consider:

- placement
- timing
- repetition
- wording
- prominence
- audience comprehension
- relationship between the disclosure and the persuasive content
- whether the viewer encounters the disclosure before being persuaded to act.

However, combined evidence must still satisfy the taxonomy. Do not manufacture a violation solely
because several innocuous statements appear together.

6. UNDER-FLAGGING SAFETY CHECK

Do NOT default to no_flag or insufficient_context merely because:

- the wording is subtle
- the creator does not explicitly say "buy"
- the claim is framed as personal experience
- the disclosure technically exists somewhere
- the advertisement sounds like ordinary creator content
- the persuasive language is friendly rather than aggressive
- the creator uses humor, storytelling, or conversational language
- the relevant evidence is distributed across multiple sentences
- the creator uses a discount code rather than a purchase link
- the creator uses a euphemism instead of advertising terminology.

These are common evasion strategies and should trigger closer inspection, not automatic clearance.

When the text provides reasonable evidence that a taxonomy test is satisfied, flag it. Do not invent
missing facts, but do not resolve textual ambiguity in favor of compliance merely because a
non-violating interpretation is possible.

UNDER-FLAGGING is the more common failure mode.

7. FINAL PRECISION PASS

After all detection passes, re-read the EXACT sentence(s) supporting each proposed flag.

For each flag, ask:

- Does the evidence actually satisfy the taxonomy?
- Am I identifying the underlying behavior rather than relying on a keyword?
- For misleading_claim: is there actually a concrete factual-sounding product property,
  performance, comparison, efficacy claim, or result -- rather than mere hype?
- For direct_exhortation: is there actual pressure, urgency, FOMO, emotional/parasocial pressure,
  or action-oriented persuasion -- rather than merely neutral information about where/how to buy?
- For undisclosed_advertising: is there genuinely no commercial acknowledgment anywhere?
- For inadequate_disclosure: is the disclosure genuinely unclear or insufficient for a child after
  considering wording, placement, timing, prominence, and context -- rather than merely brief?
- Am I flagging something because it resembles a known evasion pattern, or because the actual text
  satisfies the taxonomy?

If a proposed flag fails its precise test on close reading, DROP IT.

Emit no_flag only when, after BOTH the sensitive/adversarial pass and the final precision pass,
no flag survives.

The correct operating principle is:

    SEARCH BROADLY -> INTERPRET FUNCTIONALLY -> FLAG WHEN THE TAXONOMY TEST IS MET
    -> RE-CHECK THE EXACT EVIDENCE -> DROP FLAGS THAT DO NOT ACTUALLY CLEAR THE TEST.

Do not output your reasoning or these checks. Respond with the structured prediction only.

""" + LABELS_TAXONOMY


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
    ap.add_argument("--seed", type=int, default=None, help="for example, 42.")
    args = ap.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log = setup_logging("runs", args.context, args.model, timestamp)
    out = os.path.join("runs", f"submission_gpt_{timestamp}.jsonl")
    error_out = os.path.join("runs", f"submission_gpt_error_{timestamp}.jsonl")
    log.info(f"config: target={args.target} model={args.model} context={args.context} "
             f"sample_size={args.sample_size} max_concurrency={args.max_concurrency} "
             f"st3_only={args.st3_only} lean_prompt={args.lean_prompt} df_path={args.df_path} out={out} seed={args.seed}")

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("Set OPENAI_API_KEY in the environment (or a .env file) first.")

    tiers = ("st3",) if args.st3_only else ("st1", "st2", "st3")
    prediction_schema = ST3Prediction if args.st3_only else Prediction

    base_prompt = SFT_TAXONOMY if args.lean_prompt else (ST3_SYSTEM_PROMPT if args.st3_only else SYSTEM_PROMPT)
    df_text = None
    if args.df_path:
        df_text = df_pre_context(args.df_path, lean=args.lean_prompt)
        form = "stripped dialog flow" if args.lean_prompt else "raw autoDF JSON"
        log.info(f"appending {form} from {args.df_path} ({len(df_text)} chars) to the system prompt")
    system_prompt = f"{base_prompt}\n\n{df_text}" if df_text else base_prompt
    log.info(f"system prompt: {'lean' if args.lean_prompt else 'full'}"
             f"{' st3-only' if args.st3_only else ''} ({len(system_prompt)} chars)")

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
    else:
        log.info("target has no gold labels (or a partial mismatch) -- skipping evaluation")


if __name__ == "__main__":
    main()
