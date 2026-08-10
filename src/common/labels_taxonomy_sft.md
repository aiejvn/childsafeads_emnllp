# ChildSafeAds Label Taxonomy — SFT variant

Companion to the stripped dialog flow (`src/common/dialog_flow.py`), for supervised
fine-tuning. Pair it with that flow, **not** with `public_data_dev/labels_taxonomy.md` —
the two overlap heavily and the full taxonomy costs 2,452 tokens against a 4,096-token
budget that has to hold the segment text too.

Under SFT the label definitions are learned from the labelled targets, so this keeps
only what a model cannot recover that way:

- the **complete ST2 label set**, because the flow's Product Categories node enumerates
  only `other` (1 of 12) and its instructions refer to "the listed categories" without
  listing them — nothing else in the prompt names the other 11;
- the **exclusivity constraints**, which are hard rules, not tendencies, and which the
  flow cannot express: it reaches `no_flag` per-branch ("the output may be `no_flag` for
  this branch only"), so merging its two flag branches can yield `no_flag` alongside a
  substantive flag unless the rule is stated;
- the two **given facts**, so the model spends no capacity re-deciding them.

Dropped, with reasons:

| Dropped | Why |
|---|---|
| ST1 and ST3 definitions | the flow's reasoning nodes carry definition-grade instructions for all of them |
| The direct exhortation test (T1.3) | the sharpest boundary in the task, but prose priors are what 2,353 labelled examples replace — the one cut worth an ablation |
| Severity, legal instruments, `legal_provisions.json` grounding | fixed attributes of a flag; "systems predict flags, not severities" |
| The Tier 2 bonus track, and the unlabelled synthetic-content flag | never labelled or scored, so never emitted — 8 label names the model should not learn to produce, and therefore not named anywhere below this line either |
| Scoring and ST3 families | evaluation-side; the model emits flags, not families |

Everything above the marker is for whoever maintains this file. `common.SFT_TAXONOMY`
exposes only what follows it, so the rationale costs no prompt tokens.

<!-- PROMPT CONTENT BELOW -->

## Given

The channel is child-facing and the segment is commercial. Both are facts of the
dataset. Do not re-assess either.

## ST1 — Commercial Type (exactly one)

`physical_goods`, `digital_content_or_services`, `physical_services`, `none`, `other`

## ST2 — Product Category (one or more)

One offer often carries several: a mobile game with paid loot boxes is `apps` **and**
`gambling_adjacent`.

| Label | Definition |
|-------|------------|
| `toys` | Toys and games (physical) |
| `food` | Food and beverages |
| `apps` | Apps and digital games |
| `hardware_electronics` | Consumer electronics: phones, PCs, peripherals, audio, cameras, gadgets |
| `fashion` | Fashion and apparel |
| `health` | Health and wellness: supplements, fitness, skincare, mental health |
| `education` | Education and learning |
| `financial` | Financial products and services |
| `gambling` | Gambling: casinos, sports betting, poker, lotteries |
| `gambling_adjacent` | Gambling-like mechanics: loot boxes, gacha, mystery boxes, skins markets |
| `creator_community` | Fan and creator community: merchandise, memberships, Patreon |
| `other` | None of the above; name the category you see |

## ST3 — Compliance Risk Flags (one or more)

`undisclosed_advertising`, `inadequate_disclosure`, `direct_exhortation`,
`misleading_claim`, `age_restricted_or_prohibited_product`, `hfss_food_marketing`,
`no_flag`, `insufficient_context`

### Constraints

1. Emit every flag that applies.
2. `no_flag` and `insufficient_context` are each exclusive of all other flags.
3. `undisclosed_advertising` and `inadequate_disclosure` are mutually exclusive: either
   there is no disclosure, or there is one that is inadequate.
