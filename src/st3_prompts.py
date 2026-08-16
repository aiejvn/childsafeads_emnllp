"""ST3 (and joint ST1/ST2/ST3) prompt content: taxonomy loading, the SYSTEM_PROMPT /
ST3_SYSTEM_PROMPT strings, few-shot example assembly, and per-instance message building.

Split out of baseline_gpt.py (which re-exports SYSTEM_PROMPT for its existing external
consumers) so the ~900-line prompt text is not sitting alongside CLI/scoring logic.
"""
import logging
import os
import sys

from langchain_core.messages import HumanMessage, SystemMessage

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "starting_kit"))
from load_data import full_context, transcript_only

LABELS_TAXONOMY_PATH = os.path.join(
    os.path.dirname(__file__), "..", "public_data_dev", "labels_taxonomy.md"
)
with open(LABELS_TAXONOMY_PATH, encoding="utf-8") as _f:
    LABELS_TAXONOMY = _f.read()

TRAIN_PATH = os.path.join(os.path.dirname(__file__), "..", "public_data_dev", "train.jsonl")

# --few-shot pairs each of these labels' definition with a hand-picked, baked-in example (see
# GOLDEN_FEW_SHOT_EXAMPLES below) -- no longer built live from train.jsonl each run. Definitions
# are still parsed out of the `| T1.x | \`label\` | definition | ... |` rows in LABELS_TAXONOMY
# rather than duplicated here, so they can't drift from the taxonomy file; only the examples/
# why-lines/contrastive notes are hand-authored.
FEW_SHOT_LABELS = (
    "direct_exhortation",
    "undisclosed_advertising",
    "inadequate_disclosure",
    "misleading_claim",
    "no_flag",
    "insufficient_context",
)

# Hand-picked exemplars, one set per FEW_SHOT_LABELS, each pulled from train.jsonl and vetted
# against a rubric (prototypical, isolates the label's actual trigger, no cross-label confound,
# length-matched to real segments, no overlap with dev.jsonl) before being baked in here.
#
# inadequate_disclosure note: the previous exemplars here were plain "thank you to today's
# sponsor X" quotes -- spoken aloud, first thing said, plain language. Dropped after a spot
# check found gold labels are genuinely inconsistent about that exact pattern: identical
# phrasing shows up as both inadequate_disclosure and no_flag within the same channel, across
# at least four different channels, with no textual feature distinguishing the two. Baking in
# an exemplar that contradicts this file's own stated adequate-disclosure worked example (see
# ST3_SYSTEM_PROMPT below) risked re-teaching the over-flagging regression a past tuning round
# already had to walk back -- see feedback_check_prompt_examples_for_leakage-adjacent notes.
# The replacement below (buried + adult-jargon disclosure, not a plain sponsor mention) is
# defensible under the taxonomy's own stated failure modes without leaning on that unresolved
# inconsistency. Two other candidates were tried and rejected first: one where the disclosed
# link was a generic tools list unrelated to what the segment was actually about, and one where
# the same channel used identical phrasing in 8+ other segments labeled no_flag.
GOLDEN_FEW_SHOT_EXAMPLES = {
    "direct_exhortation": {
        "examples": [
            {
                "quote": "so if you have a game or franchise that you really like definitely "
                         "pick one of these up",
                "why": "direct imperative (\"pick one up\") aimed at the viewer with no "
                       "accompanying product claim -- the exhortation is the whole content of "
                       "the sentence.",
            },
            {
                "quote": "please get yourself a PC you deserve the link to Star Forge systems "
                         "will be in the description go and check out their PCS today",
                "why": "two stacked imperatives (\"get yourself,\" \"go and check out\") plus a "
                       "direct instruction to use the link -- a textbook appeal to act now.",
            },
        ],
        "contrastive": {
            "quote": "This laptop has a 12-hour battery and a way better screen than my old "
                     "one, use the code in the description if you want it.",
            "note": "the first clause is a product claim (goes to misleading_claim if the "
                    "claim is false/unverifiable, otherwise no flag on its own); the "
                    "imperative is a discount-code mechanic, not a direct appeal to buy. Do "
                    "not tag direct_exhortation just because a link or code is mentioned -- "
                    "the imperative has to be the \"go get this\" act itself, not incidental "
                    "transactional detail.",
        },
    },
    "undisclosed_advertising": {
        "examples": [
            {
                "quote": "bring your setup to the next level with cablemod's all-new custom "
                         "coiled keyboard cables available in a variety of colors and connector "
                         "types utilizing best-in-class connectors the keyboard cables give "
                         "your setup a look and feel it deserves to see the complete lineup of "
                         "custom keyboard cables available from cablemod click the link in the "
                         "description below",
                "why": "the product (CableMod custom keyboard cables) is named, described, and "
                       "linked with unambiguous commercial intent, yet neither the transcript "
                       "nor the rest of the video description (which also lists merch and "
                       "Amazon links) contains any acknowledgment of a commercial/compensation "
                       "relationship anywhere -- no \"sponsor,\" \"ad,\" \"paid,\" or "
                       "\"affiliate\" language at all.",
            },
        ],
    },
    "inadequate_disclosure": {
        "examples": [
            {
                "quote": "Buy the MSI 342C on Amazon [PAID LINK]: https://geni.us/D5qtPe",
                "why": "the transcript segment is entirely a spec pitch for this exact monitor "
                       "and never once says sponsor/ad/paid/affiliate -- the ONLY disclosure "
                       "anywhere is this terse \"[PAID LINK]\" tag next to the matching product "
                       "link, backed by FTC-style legal boilerplate (\"...an affiliate "
                       "advertising programme designed to provide a means for sites to earn "
                       "advertising fees...\") buried under two dozen other tagged links "
                       "further down the description. Buried and adult-jargon at once, with no "
                       "plain \"this video is sponsored by X\" statement to fall back on.",
            },
        ],
    },
    "misleading_claim": {
        "examples": [
            {
                "quote": "Like Tininoan, the gold standard for anti-aging skin care, Tininoan "
                         "is 20 times stronger than over-the-counter retinols.",
                "why": "asserts a specific, falsifiable multiplier (\"20 times stronger\") "
                       "against a named comparator as flat fact, not opinion -- a quantified "
                       "skincare efficacy claim the segment gives no support for.",
            },
        ],
    },
    "no_flag": {
        "examples": [
            {
                "quote": "Before we get into this, I just want to say a massive thank you to "
                         "PCB way for sponsoring this video. PCB Way is your one-stop solution "
                         "for all of your DIY needs... It's an absolutely fantastic service. I "
                         "recently used it to make a bracket for my kiosk... So, check out PCB "
                         "Way through the link in the description below.",
                "why": "disclosure is plain, spoken, and the very first thing said in the "
                       "segment; every claim about the product stays at the level of "
                       "subjective puffery (\"one-stop solution,\" \"fantastic service\") "
                       "rather than a specific/quantified assertion; and the closing CTA is a "
                       "bare instruction with no added pressure -- so despite having both a "
                       "sponsor pitch AND a link-based CTA (the surface features that make a "
                       "segment look risky), nothing here crosses into a flaggable claim or "
                       "exhortation.",
            },
        ],
    },
    "insufficient_context": {
        "kind": "transcript excerpt",
        "examples": [
            {"quote": "[Music] [Music] [Music] do [Music] so [Music] [Music] [Music] [Music] "
                      "um [Music] [Music] [Music] [Music] [Music] [Music] [Music] [Music] "
                      "[Music] do [Music] [Music] [Music] [Music] hey hey people oh"},
            {"quote": "*outro* *but can you this?* *outro* *bye* *broderfist*"},
            {"quote": "[Music] oh [Music] last time on game groups oh please let"},
        ],
    },
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

Predict any of these eight ST3 labels that apply:

- `misleading_claim` (T1.4)
- `age_restricted_or_prohibited_product` (T1.5)
- `hfss_food_marketing` (T1.6)
- `undisclosed_advertising` (T1.1)
- `inadequate_disclosure` (T1.2)
- `direct_exhortation` (T1.3)
- `insufficient_context` (T1.9)
- `no_flag` (T1.8)

Ignore Tier 2 flags and `undisclosed_synthetic_content` -- not covered in this release.

Multiple labels may apply, EXCEPT `no_flag` and `insufficient_context`: each of those two is
exclusive of every other label -- if either applies, it is the ONLY label you predict for the
instance.

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

Do NOT flag routine transactional/promotional facts that carry no claim about the product's own
performance, quality, or results. A discount percentage, promo code, or plain price mention that
is simply being offered ("15% off your order", "use code X for 5% off", "get 25% off your first
month") is an ordinary commercial term, not a claim requiring substantiation -- UNLESS it is
framed as an unbeatable or guaranteed deal ("the cheapest anywhere", "guaranteed lowest price"),
which IS the kind of price claim this flag covers. Likewise, a plain count or spec the product
straightforwardly has ("300 characters to collect", "10-hour battery", "13+ to use this app") is
NOT misleading_claim by itself, unless it is also presented as evidence of superior performance or
an outcome the segment gives no support for.

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

## T1.1 / T1.2 — undisclosed_advertising vs. inadequate_disclosure

These two labels are MUTUALLY EXCLUSIVE (taxonomy rule 2): an instance gets at most one of
them, never both. Decide with the two-step procedure below rather than judging each in
isolation.

### Step 1 — Clarity of Compensation: is it disclosed ANYWHERE, in any form?

Search the ENTIRE given text -- spoken transcript AND video description AND supplied
metadata/platform label -- for any acknowledgment that this segment involves a commercial
relationship:
- "sponsored by X", "this video is sponsored", "paid partnership", "advertisement"/"ad";
- "affiliate links", "I receive a commission", "using my code supports the channel";
- equivalent language clearly identifying a commercial relationship, spoken OR written.

A bare product link, promo code, "check it out", "my links", or shopping URL is NOT a
disclosure by itself -- none of these say anything about payment.

IMPORTANT: `OFFICIAL_DISCLOSURE: true` in the supplied metadata is ITSELF a qualifying
acknowledgment -- it represents the platform's own paid-promotion label, one of the disclosure
channels the taxonomy recognizes, even when neither the transcript nor the description contains
an explicit sponsor/ad phrase. Treat `OFFICIAL_DISCLOSURE: true` alone as sufficient to pass
Step 1 and move to Step 2 -- do NOT conclude `undisclosed_advertising` just because you can't
find matching textual language, when the platform label itself says the relationship is
disclosed.

- If NO such acknowledgment exists ANYWHERE (transcript, description, metadata, or the platform
  label) ->
  `undisclosed_advertising`. Stop; do not also apply Step 2.
- If SOME such acknowledgment exists somewhere -> compensation is disclosed; move to Step 2
  to judge whether it's disclosed adequately. Do NOT flag `undisclosed_advertising` once any
  acknowledgment exists, even a weak one -- weak-but-present disclosures are
  `inadequate_disclosure`'s job, not `undisclosed_advertising`'s.

### Step 2 — Clarity of Relationship/Position: would a child viewer actually encounter it?

Compensation is disclosed somewhere (Step 1 passed). Now judge whether its POSITION and
DELIVERY put it where a child watching/listening would actually notice and understand it --
not just where it technically exists in the text. Weigh these signals together; no single one
is decisive on its own:

Leans ADEQUATE (no disclosure flag):
- spoken aloud in the video, not only written;
- appears early -- before or alongside the pitch -- not only after it's already over;
- plain language ("this video is sponsored by X") rather than only legal/affiliate boilerplate;
- reinforced in more than one place (both spoken and in the description).

Leans INADEQUATE (`inadequate_disclosure`):
- disclosure language appears ONLY in the written description, never spoken -- about half of
  real inadequate_disclosure cases are exactly this: a viewer who only watches/listens would
  never encounter it at all;
- the ONLY spoken/written mention comes only AFTER the persuasive pitch has already finished
  (e.g. tacked on at the very end, once the sell is over) -- lateness, not mention count, is
  the signal;
- the ONLY disclosure channel present is generic affiliate-link legal boilerplate ("as an
  Amazon Associate I earn from qualifying purchases") with no plain-language sponsor/ad
  statement anywhere;
- OFFICIAL_DISCLOSURE is a meaningful but non-decisive signal: `false` leans toward inadequate,
  `true` leans toward adequate, but `true` does NOT settle it by itself -- plenty of
  `OFFICIAL_DISCLOSURE: true` instances still have a disclosure buried, written-only, or
  boilerplate-only in the actual text, and that text is what you're grading.

If the disclosure clears this bar -> no disclosure flag on this dimension. If it doesn't ->
`inadequate_disclosure`.

IMPORTANT -- a single mention is NOT by itself a defect. A disclosure spoken once, early,
in plain language ("today's episode is sponsored by X") is ADEQUATE even if it is never
repeated and even if the description doesn't also mention it. Do not apply
`inadequate_disclosure` reflexively to every sponsor mention, and do not penalize a
disclosure merely for occurring only once -- judge WHERE and HOW clearly that one mention
lands, not how many times it repeats. The flag is for disclosures a child would plausibly
miss or fail to understand (buried, late, written-only, or boilerplate-only), not for every
commercial acknowledgment that exists.

Worked example -- ADEQUATE, do NOT flag: transcript opens "hey everyone, quick shoutout -- this
video is sponsored by a company called Glowpeak, they make portable phone chargers" before the
segment moves on to unrelated content. This is spoken, is the very first thing said, and names
the sponsor in plain language -- that is adequate on its own. The fact that it is short, said
only once, and not the focus of the rest of the segment does NOT make it inadequate. Only flag
`inadequate_disclosure` here if this sentence were ABSENT from the transcript and the
sponsorship appeared only in the written description.

Worked example -- INADEQUATE, DO flag: the transcript never mentions any commercial
relationship; the only disclosure is a hashtag ("#ad") or a legal boilerplate line ("as an
Amazon Associate I earn from qualifying purchases") sitting in the written description below
several other unrelated links. A viewer who only watches/listens encounters no disclosure at
all -- that is `inadequate_disclosure`, not `undisclosed_advertising` (Step 1 passed because
the written acknowledgment exists somewhere), and not adequate (Step 2 fails because it's
written-only and easy to miss).

## T1.3 — direct_exhortation

Flag a direct appeal to the viewer to buy the product (or to get a parent/adult to buy it),
but only when the delivery carries real pressure beyond a bare instruction. Work through this
checklist in order:

(a) Is there a purchase-directed imperative or appeal anywhere at all (buy, get, order, ask for,
download, use this code, go to the link, etc.)? If there is none, this does NOT apply -- stop
here.

(b) If yes, is it a bare transactional instruction with no added pressure -- it only states
where/how to obtain the product, or that a discount exists ("download the app from the link
below", "click the link in the description", "use my code for 15% off", "go give it a try")?
If so, this does NOT count, even though it is phrased as an imperative.

(c) Does the delivery add pressure on top of the instruction -- a parasocial appeal ("if you
love us, please download it"), pleading or repetition, urgency aimed squarely at the viewer, or
child-directed hyped/pressuring register? If so, COUNT it, even though the surface form is an
instruction.

(d) If the wording is genuinely ambiguous between (b) and (c) -- you cannot tell whether it's a
plain instruction or a pressuring appeal -- do NOT flag it. The taxonomy's own rule for this
boundary is to not flag ambiguous cases.

The test is the pressure placed on the viewer to make the purchase happen, not the mere presence
of an imperative verb or a link/code. Ordinary, unadorned sponsor-read CTA phrasing ("check it
out", "grab yours", "link in the description", "use code X at checkout") is common in almost
every sponsored segment and is NOT enough by itself -- most segments that contain a CTA at all
still do not carry this flag. Reserve it for CTAs that carry real added pressure per (c), not for
CTA presence in general.

Do not require literal child-directed phrasing like "ask your parents" to flag this -- that exact
wording is rare in real positives. Judge the register/pressure of the appeal itself, whoever it
is nominally addressed to.

## T1.9 — insufficient_context

Flag when the segment is too short or ambiguous to assess. In practice this means BOTH of the
following are true:

- the transcript carries essentially no real speech/ad content -- empty, or only filler such as
  "[Music]", "[Applause]", or a few short interjections; AND
- the video description is ALSO not specifically promotional -- generic channel boilerplate,
  unrelated content, social/merch links -- rather than an explicit sponsor statement, promo
  code, or "X% off" style pitch.

If the transcript is empty/filler-only but the description clearly promotes a specific product
(an explicit sponsor mention, promo code, or discount pitch), that is NOT insufficient_context --
judge the visible commercial content normally (e.g. `undisclosed_advertising`) using the
description as your evidence, even though the spoken transcript itself is silent.

`insufficient_context` is exclusive of every other flag: if it applies, it is the ONLY label for
this segment.

This is a rare, structural pattern (near-empty segment), not a hedge for uncertainty -- do not
reach for it just because you are unsure how to judge a segment that actually has real
transcript or description content to work with.

## T1.8 — no_flag

After working through every check above, if NONE of them triggered, you must explicitly conclude
the segment is compliant and predict `st3: ["no_flag"]`. Treat "none of the checks above apply"
as a specific, positive finding you state on purpose -- not a default you land on by leaving st3
empty, and not something you skip because nothing else seemed worth flagging.

Before emitting `no_flag`, re-confirm `undisclosed_advertising` specifically by name, in addition
to the other checks: `no_flag` requires that you can point to actual disclosure language
somewhere in the supplied material (transcript, description, or metadata) -- a plain link, promo
code, or "free trial" mention is NOT disclosure language. If you cannot point to it, the correct
label is `undisclosed_advertising`, not `no_flag`, regardless of how clean everything else about
the segment looks.

`no_flag` is exclusive of every other label above: if it applies, predict it alone.

A mild, non-decisive prior: content in the `education` and `apps` categories tends to skew
compliant, while `health`, `food`, and gambling-adjacent categories tend to skew toward
violations. Do not use this as a shortcut or a reason to skip a check -- judge every segment on
the specific evidence in its own text. A "usually clean" category can still contain a real
violation, and a "usually risky" category can still be genuinely clean; the checks above, not the
category, decide the outcome.

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
- For `misleading_claim`, is there a concrete factual/product claim rather than puffery, or a
  routine promo code/discount/price mention with no performance claim attached?
- For `age_restricted_or_prohibited_product`, is the restricted product actually being promoted?
- For `hfss_food_marketing`, is this clearly HFSS rather than borderline?
- For `undisclosed_advertising`, did I search the entire supplied disclosure material, and
  confirm there is truly NO acknowledgment anywhere (not even a weak one)?
- For `inadequate_disclosure`, did I confirm Step 1 passed first (some acknowledgment exists),
  and is the inadequacy genuinely about position/clarity (written-only, late, single-mention,
  boilerplate-only) rather than just "a sponsor mention exists so I flagged it"?
- Did I apply at most one of `undisclosed_advertising` / `inadequate_disclosure`, never both?
- For `direct_exhortation`, is there real appeal-level pressure on the viewer (parasocial,
  pleading, urgency, hyped register), not just an imperative verb or a bare "link/code below"
  instruction? If it's only a plain CTA, drop the flag.
- For `insufficient_context`, are BOTH the transcript and the description actually thin -- not
  just one of them?
- If no flag survives this pass, did I explicitly predict `no_flag` rather than leaving st3
  empty?

Drop flags that fail the precise test.

Respond with the structured prediction ONLY."""

# --cot inline: appended to ST3_SYSTEM_PROMPT only when --cot inline is set (see
# ST3PredictionCoT in st3_schemas.py -- the reasoning field it adds to the structured-output
# schema is what this text is instructing the model to actually use).
COT_INSTRUCTIONS = """The structured prediction has a `reasoning` field before `st3` -- use
it to actually work through the checks above against the specific evidence in this segment
before committing to labels, rather than stating a conclusion first and justifying it after.
Name which checks you evaluated, what evidence (or absence of
evidence) drove each one, and, where two labels are commonly confused (e.g.
`undisclosed_advertising` vs. `inadequate_disclosure`), which side of that specific line this
segment fell on and why. Do not restate the taxonomy definitions -- reason about this
segment's actual text."""

def build_few_shot_section(train_path: str = None, log: logging.Logger = None, n_per_label: int = 1) -> str:
    """Assembles the FEW-SHOT EXAMPLES section from GOLDEN_FEW_SHOT_EXAMPLES -- hand-picked,
    rubric-vetted exemplars baked in above -- paired with each label's taxonomy definition
    (still parsed from LABELS_TAXONOMY so definitions can't drift). No longer scans train.jsonl
    at call time; train_path/n_per_label are accepted for backward compatibility with existing
    callers but otherwise unused now that example counts are fixed by hand per label."""
    if log is not None and n_per_label != 1:
        log.warning(f"build_few_shot_section: n_per_label={n_per_label} has no effect -- "
                    "examples are baked in now (see GOLDEN_FEW_SHOT_EXAMPLES), not scanned "
                    "live from train.jsonl")
    defs = parse_taxonomy_defs(LABELS_TAXONOMY, FEW_SHOT_LABELS)

    sections = ["## FEW-SHOT EXAMPLES\n\nHand-picked examples from the training data, pairing "
                "each label's definition with real evidence that earned it. Each example "
                "includes a one-line rationale -- read the rationale, not just the quote. The "
                "quote alone is not the pattern; two segments can share surface vocabulary (a "
                "discount, a sponsor mention, an urgent tone) and still take different labels "
                "depending on what the segment is actually doing."]
    for label in FEW_SHOT_LABELS:
        spec = GOLDEN_FEW_SHOT_EXAMPLES[label]
        kind = spec.get("kind", "evidence quote")
        lines = [f"### `{label}`", f"Definition: {defs[label]}"]
        if "test" in spec:
            lines.append(f"Test: {spec['test']}")
        for i, ex in enumerate(spec["examples"], 1):
            lines.append(f'Example {i} ({kind}): "{ex["quote"]}"')
            if ex.get("why"):
                lines.append(f"Why this qualifies: {ex['why']}")
        if "contrastive" in spec:
            c = spec["contrastive"]
            lines.append(f'Contrastive non-example: "{c["quote"]}" -- {c["note"]}')
        sections.append("\n".join(lines))
    return "\n\n".join(sections)

def build_messages(instance: dict, context: str, system_prompt: str) -> list:
    if context == "full":
        text = full_context(instance)
    elif context == "no_product_page":
        text = no_product_page(instance)
    else:
        text = transcript_only(instance)
    return [SystemMessage(system_prompt), HumanMessage(f"SEGMENT DATA:\n\n{text}")]

