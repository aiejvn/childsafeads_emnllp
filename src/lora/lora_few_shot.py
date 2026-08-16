"""--few-shot prompt content for lora_train_generative.py/lora_predict_generative.py: hand-picked,
rubric-vetted exemplars (one set per label, pulled from train.jsonl) pasted into the system
prompt as a prose "FEW-SHOT EXAMPLES" section -- the same shape as src/st3_prompts.py's
GOLDEN_FEW_SHOT_EXAMPLES/build_few_shot_section for the GPT baseline's --st3-only --few-shot,
adapted here to ST1's commercial-type taxonomy and to this pipeline's --st1-only/--st12-only/
--st3-only tiers.

Only --st1-only has a curated example set so far (the current research focus, see
feedback_st1_focus.md in project memory); FEW_SHOT_BUILDERS is the single source of truth both
lora_train_generative.py and lora_predict_generative.py check before honoring --few-shot, so a
future st12_only/st3_only set only has to be added here to light up in both scripts.
"""
import os

from . import ST1_LABELS  # noqa: F401 (documents which labels GOLDEN_ST1_FEW_SHOT_EXAMPLES must cover)

TAXONOMY_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "public_data_dev", "labels_taxonomy.md")
with open(TAXONOMY_PATH, encoding="utf-8") as _f:
    _TAXONOMY = _f.read()

# Hand-picked exemplars, one set per ST1_LABELS value, each pulled from train.jsonl and vetted
# against the same rubric st3_prompts.py's GOLDEN_FEW_SHOT_EXAMPLES uses: prototypical, isolates
# the label's actual trigger, no cross-label confound, no overlap with dev.jsonl.
#
# `none` note: skimming train.jsonl's 35 `none` instances turns up plenty that read as an
# ordinary sponsor pitch for a real product (a VPN, a coffee subscription, a $1M creator
# challenge) -- inconsistent with the taxonomy's own "no identifiable commercial offer" wording.
# Baking one of those in as the exemplar would actively teach the model to reach for `none`
# whenever a pitch feels underspecified, which is the opposite of what --pos-weight/oversampling
# on this same rare label is trying to fix (feedback_st1_focus.md: dev gains on `none` haven't
# generalized to test). The two examples below are the genuinely clean pattern instead: the
# segment's own text carries no offer at all -- empty/near-empty or off-topic banter -- even
# though the source video is tagged commercial elsewhere.
GOLDEN_ST1_FEW_SHOT_EXAMPLES = {
    "physical_goods": {
        "examples": [
            {
                "quote": "hellofresh sends everything you need to get dinner on the table no "
                         "meal planning all deliciousness get 16 free meals plus three gifts",
                "why": "a meal-kit box shipped to the buyer -- the taxonomy's own worked example "
                       "for this label -- with nothing digital or human-performed about the "
                       "delivery.",
            },
        ],
    },
    "digital_content_or_services": {
        "examples": [
            {
                "quote": "thank you again to Midas Merge for sponsoring. If you want to check "
                         "it out, I have that linked down below. It's free to download and "
                         "it's pretty fun.",
                "why": "a mobile game downloaded to the buyer's device -- no physical delivery, "
                       "no human performing anything on the buyer's behalf.",
            },
            {
                "quote": "brilliant has thousands of lessons in math data analysis programming "
                         "and Ai and all of them are interactive which is the most effective "
                         "way to learn",
                "why": "a self-paced online course platform -- content delivered digitally, not "
                       "a live human instructor (contrast physical_services below).",
            },
        ],
    },
    "physical_services": {
        "examples": [
            {
                "quote": "if you don't have a good law firm to represent you, you could be "
                         "cooked. That's where Morgan and Morgan comes in... Morgan and Morgan "
                         "is America's largest injury law firm.",
                "why": "legal representation is a service performed by a human professional (a "
                       "lawyer), not a product handed over or content delivered -- the ST1 test "
                       "is whether a human performs the service, not which channel advertises "
                       "it (see the SYSTEM_PROMPT's app/website-delivered-by-a-human rule).",
            },
        ],
    },
    "none": {
        "examples": [
            {"quote": "Heat. [Music]"},
            {"quote": "at you and says oh wow that was a close one wasn't it [Music]"},
        ],
        "why": "the segment's own text names no product, service, or offer at all -- filler or "
               "off-topic banter -- even though the source video carries a sponsor elsewhere. "
               "Use this only when there is truly nothing identifiable in THIS text, not as a "
               "hedge for a pitch that is merely vague or underspecified: a real, if thin, "
               "product pitch (\"use my code for a discount on X\") still gets a real label, "
               "not `none`.",
        "contrastive": {
            "quote": "(any segment that names a sponsor and what they sell, however briefly)",
            "note": "do not default to `none` just because the pitch is short or you're unsure "
                    "which of the other four labels fits -- `none` is for the absence of any "
                    "identifiable offer, not a catch-all for ambiguity.",
        },
    },
    "other": {
        "examples": [
            {
                "quote": "Donate $10, and get this, you're entered for a chance to win an "
                         "original restored DeLorean.",
                "why": "a sweepstakes/raffle entry -- money changes hands but the buyer "
                       "receives a chance at a prize, not a good, digital product, or "
                       "performed service.",
            },
            {
                "quote": "I bought one square foot of land in scotland which makes me a "
                         "scottish landowner and according to scottish custom this makes me "
                         "able to have the title of lord or lady",
                "why": "a novelty legal/ceremonial title, not a tangible good, digital product, "
                       "or human-performed service -- genuinely none of the other four.",
            },
        ],
    },
}


def _parse_st1_defs() -> dict:
    """Pull {label: definition} for ST1_LABELS out of labels_taxonomy.md's ST1 table (`|
    \\`label\\` | definition | examples |` rows -- no T1.x code column, unlike ST3's table that
    st3_prompts.py's parse_taxonomy_defs handles). Parsed at call time rather than hand-copied
    so the wording can't drift from the taxonomy file."""
    lines = _TAXONOMY.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("## ST1"))
    defs = {}
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        if not line.startswith("| `"):
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        defs[cols[0].strip("`")] = cols[1]
    missing = set(GOLDEN_ST1_FEW_SHOT_EXAMPLES) - set(defs)
    if missing:
        raise ValueError(f"couldn't find ST1 taxonomy definitions for {missing} in {TAXONOMY_PATH}")
    return defs


def build_st1_few_shot_section() -> str:
    """Assembles the '## ST1 FEW-SHOT EXAMPLES' prose section from GOLDEN_ST1_FEW_SHOT_EXAMPLES,
    pairing each label's taxonomy definition with its hand-picked exemplar(s) -- same shape as
    src/st3_prompts.py's build_few_shot_section for --st3-only."""
    defs = _parse_st1_defs()
    sections = ["## ST1 FEW-SHOT EXAMPLES\n\nHand-picked examples from the training data, pairing "
                "each ST1 label's definition with real evidence that earned it. Decide from what "
                "the buyer actually receives, not from how the offer is marketed."]
    for label, spec in GOLDEN_ST1_FEW_SHOT_EXAMPLES.items():
        lines = [f"### `{label}`", f"Definition: {defs[label]}"]
        for i, ex in enumerate(spec["examples"], 1):
            lines.append(f'Example {i}: "{ex["quote"]}"')
            if ex.get("why"):
                lines.append(f"Why this qualifies: {ex['why']}")
        if "why" in spec:  # label-level rationale shared across all its examples (see `none`)
            lines.append(f"Why these qualify: {spec['why']}")
        if "contrastive" in spec:
            c = spec["contrastive"]
            lines.append(f'Contrastive non-example: "{c["quote"]}" -- {c["note"]}')
        sections.append("\n".join(lines))
    return "\n\n".join(sections)


# Single source of truth for which --st{n}-only tiers have a curated --few-shot example set;
# lora_train_generative.py/lora_predict_generative.py both validate --few-shot against this dict
# rather than hand-coding "only st1_only" in two places, so adding a st12_only/st3_only builder
# here is what it takes to light up --few-shot for those tiers in both scripts.
FEW_SHOT_BUILDERS = {"st1_only": build_st1_few_shot_section}
