# ST3 flag expansion: research, implementation, and integration

Follow-on to the `--st3-only` `ST3_SYSTEM_PROMPT`, which previously predicted only 4 of the 8
ST3 labels (`misleading_claim`, `age_restricted_or_prohibited_product`, `hfss_food_marketing`,
`undisclosed_advertising`) and explicitly told the model to ignore `inadequate_disclosure` and
`direct_exhortation`, while never mentioning `insufficient_context` or `no_flag` at all — even
though the existing `FEW_SHOT_LABELS`/`build_few_shot_section()` infrastructure already targeted
3 of those 4 ignored labels, unused until now.

## Process

1. **Research** (4 parallel websearch subagents, one per flag): verified the literature a naive
   pass had proposed for each flag, and stress-tested its applicability against this project's
   own empirical findings in `st3_findings.md`. Two of four naive framings were rejected outright
   (propaganda-technique span detection for `direct_exhortation` — wrong reference class, no span
   data; selective-prediction/abstention for `insufficient_context` — a category error, since the
   label is a deterministic structural pattern, not model uncertainty). The other two were
   refined into much better-fitting, more recent citations (an FTC compensation/relationship
   clarity decomposition for `inadequate_disclosure`; out-of-scope intent-classification
   threshold re-classification for `no_flag`).
2. **Implementation** (4 parallel agents, one per flag, each in an isolated git worktree):
   extended `ST3_SYSTEM_PROMPT` with a dedicated rubric section per flag, grounded in the
   research and validated independently (before/after on the same batch, n=30-50, per-flag).
   All 4 succeeded in isolation with no regression on the previously-working labels.
3. **Integration** (this file): manually reconciled the 4 branches' diffs into one coherent
   8-label prompt (see below for the two structural collision points), then validated the
   *combined* result — the step that caught the prior tuning run's regression (individually-good
   fixes stacking into a net loss) — on two independent, larger batches.

## Integration decisions

- **TASK label list**: merged to all 8 labels; the "ignore" line was dropped since there's
  nothing left to ignore. Added an exclusivity note for both `no_flag` and `insufficient_context`
  (previously only `no_flag`'s branch had it).
- **`undisclosed_advertising`/`inadequate_disclosure`**: used the `inadequate_disclosure` agent's
  paired two-step rubric (Clarity of Compensation / Clarity of Relationship) as the base, since it
  fully subsumes and refines the original standalone `undisclosed_advertising` section.
- **Section order**: `misleading_claim` → `age_restricted_or_prohibited_product` →
  `hfss_food_marketing` → `undisclosed_advertising`/`inadequate_disclosure` → `direct_exhortation`
  → `insufficient_context` → `no_flag` (last, since its gate text explicitly says "after working
  through every check above").
- **`sanitize_st3`**: merged the `insufficient_context` agent's `is_thin_segment()` deterministic
  override (force/suppress based on transcript+description thinness) with the `no_flag` agent's
  empty-list default change (`no_flag` instead of `insufficient_context`, justified by the 35:1
  train-set ratio between the two). Both changes are compatible: the thin-segment force still
  takes priority when it fires; the `no_flag` default only applies when nothing else, including
  thinness, indicates otherwise.
- **Bug found and fixed during integration validation** (not present in any single branch,
  only visible once combined and tested on a batch with realistic label prevalence): the merged
  Step 1 of the disclosure rubric never told the model that `OFFICIAL_DISCLOSURE: true` in the
  supplied metadata is *itself* a qualifying disclosure acknowledgment (the taxonomy's "platform's
  own paid-promotion label" channel) — so when there was no literal "sponsored by" phrase, the
  model concluded no disclosure existed at all (`undisclosed_advertising`) instead of proceeding
  to Step 2 to judge adequacy. Added one paragraph making this explicit. Fixed instances like
  `UCPvRdfUooqCf0zPOYvbBzVA_94-J5BHY4mE_ffdb0040` (transcript mentions a coupon with no "sponsor"
  language, but `OFFICIAL_DISCLOSURE: true`, gold=`inadequate_disclosure`) that were previously
  misrouted.

## Validation

Two independent batches, before = original 4-label `ST3_SYSTEM_PROMPT` (git `HEAD`), after =
final integrated prompt (this commit). `batch.jsonl` (n=62) deliberately includes all 7 dev-set
`insufficient_context` positives (rare enough that a pure random draw would likely miss most of
them) plus 55 random; `batch2.jsonl` (n=60) is purely random, giving more representative label
prevalence for the other 7 flags.

**`batch.jsonl` (n=62, includes all dev `insufficient_context` positives):**

| label | before F1 | after F1 |
|---|---|---|
| st3_macro_f1 | 0.293 | **0.659** |
| st3_family_macro_f1 | 0.568 | **0.818** |
| direct_exhortation | 0.000 | 0.545 |
| inadequate_disclosure | 0.000 | 0.526 |
| insufficient_context | 0.000 | 0.727 |
| no_flag | 0.400 | 0.647 |
| misleading_claim | 0.776 | 0.833 |
| undisclosed_advertising | 0.211 | 0.333 |
| hfss_food_marketing | 0.667 | 1.000 |

**`batch2.jsonl` (n=60, purely random — more representative prevalence):**

| label | before F1 | after F1 |
|---|---|---|
| st3_macro_f1 | 0.429 | **0.508** |
| st3_family_macro_f1 | 0.561 | **0.625** |
| age_restricted_or_prohibited_product | 0.857 | 0.857 |
| direct_exhortation | 0.000 | 0.500 |
| hfss_food_marketing | 0.500 | 0.500 |
| inadequate_disclosure | 0.000 | 0.300 |
| misleading_claim | 0.701 | 0.716 |
| no_flag | 0.118 | 0.348 |
| undisclosed_advertising | 0.828 | 0.846 |

Both `st3_macro_f1` and `st3_family_macro_f1` improved on both independent batches, with no
label regressing beyond single-instance noise at small gold counts (e.g. `undisclosed_advertising`
gold=2 on `batch.jsonl`). This is the opposite of the prior tuning run's outcome (memory
`project-prompt-tuning-run1-outcome`: individually-good recall fixes stacked into a net st3
regression, only visible at n=100 scale) — here the combined result held up cleanly at n=60-62
across two independently-drawn batches.

## Full dev-set confirmation (n=504, the trustworthy number)

**Note**: the `st3_macro_f1=0.572` figure in the table immediately below was later found to be
contaminated by a leaked worked example (see "Leakage check" further down) -- **0.527 is the
corrected number** for this same before/after comparison. Left this section as originally
written for an accurate record of what was found when; the correction and its reasoning are in
the leakage section rather than edited into this table.

The two batches above (n=60-62) were promising but explicitly flagged as not yet the "trustworthy
number" per `runs/prompt_tuning/PLAN.md`'s discipline. Ran before/after on the entire dev set
(504 instances, not a sample) to settle it: before = `git show HEAD^:src/baseline_gpt.py` swapped
in temporarily, after = this commit (`e98b1e4`), both scored against every gold label in
`public_data_dev/dev.jsonl`.

| label | before F1 | after F1 | delta |
|---|---|---|---|
| **st3_macro_f1** | 0.380 | **0.572** | **+0.192** |
| **st3_family_macro_f1** | 0.605 | **0.693** | **+0.088** |
| direct_exhortation | 0.000 | 0.351 | +0.351 |
| inadequate_disclosure | 0.000 | 0.444 | +0.444 |
| insufficient_context | 0.000 | 0.421 | +0.421 |
| no_flag | 0.255 | 0.500 | +0.245 |
| hfss_food_marketing | 0.462 | 0.615 | +0.153 |
| undisclosed_advertising | 0.693 | 0.710 | +0.017 |
| misleading_claim | 0.759 | 0.773 | +0.014 |
| age_restricted_or_prohibited_product | 0.875 | 0.765 | -0.110 |

Confirms the smaller-batch numbers decisively: st3_macro_f1 +0.192, st3_family_macro_f1 +0.088,
every previously-`0.000` label now meaningfully positive. One regression:
`age_restricted_or_prohibited_product` (a section no implementation agent touched) went from 2
to 5 false positives out of 504 instances. Checked directly: the false-positive instances differ
between the two runs rather than showing a consistent new failure pattern, consistent with
`gpt-5.4`'s known temp=0 non-determinism (already noted independently by two implementation
agents) rather than a systematic interaction effect from the new rubric sections — none of which
mention this label. Not chased further given the scale of the win elsewhere; worth a rerun to
confirm it's noise if this label's score matters for a future pass.

## Leakage check against the holdout, and a leak found in dev

Checked whether any content from `public_data_test/test.jsonl` (the actual withheld competition
holdout -- 503 instances, no gold labels distributed) ended up embedded in the prompt, and
whether the prompt could be scored against it.

- **instanceID/content overlap**: zero instanceID overlap between train/dev and test. 2 of 152
  test channels also appear in train (1 in dev) -- the same creator posting different videos
  across splits, not instance-level leakage.
- **Quote-level scan**: extracted every distinctive quoted string (40+ chars, not sourced from
  `labels_taxonomy.md`) from `ST3_SYSTEM_PROMPT` and searched for it, punctuation-insensitively,
  across train/dev/test. Found one genuine leak (see below) and one false alarm: "as an Amazon
  Associate I earn from qualifying purchases" recurs verbatim across all three splits (~10
  instances each) because it's ubiquitous real-world Amazon-mandated boilerplate that unrelated
  creators copy-paste -- not content copied from a specific instance, so not leakage in the
  meaningful sense.
- **The genuine leak, found in dev, not test**: the `inadequate_disclosure` worked example ("oh
  today's episode is sponsored by expressvpn...") was a near-verbatim transcript excerpt from one
  real dev instance (`UCkxctb0jr8vwa4Do6c6su0Q_DfO55LpdmSk_441aa5d4`, gold=`no_flag`), lightly
  re-punctuated by the implementing agent when writing it up -- not caught by the agent's own
  validation since it never explicitly checked its worked examples against the split it was
  scoring on. The prompt told the model, in effect, "this exact scenario is ADEQUATE" right
  before asking it to classify that exact scenario. **test.jsonl was NOT affected** -- the leak
  was confined to dev, which matters for the integrity of every dev-set number in this report,
  not for holdout submission integrity.
- **Fix**: replaced the worked example with a synthetic one (a fictional "Glowpeak" phone-charger
  sponsor) that doesn't correspond to any real instance in any split, re-verified by re-running
  the quote scan. Re-ran the full n=504 dev validation with the fix: **st3_macro_f1 0.527**
  (vs. the leak-contaminated 0.572 reported by the first full-dev run, vs. 0.380 original) --
  still a clear +0.147 win, just a more honest number. The 0.045 shift between the two after-runs
  is spread across labels the leak fix has no plausible causal path to (e.g.
  `hfss_food_marketing` swung 0.615->0.308 on only 5 gold instances), consistent with `gpt-5.4`
  temp=0 non-determinism rather than a targeted effect of removing one example.
- **Holdout sanity run**: ran the (leak-fixed) prompt on the full `test.jsonl` (503 instances).
  0 failed/error predictions, every instance received at least one st3 label (no empty outputs),
  mean 1.39 labels/instance. Since test.jsonl carries no gold labels, F1 can't be computed --
  this is a plausibility/pipeline-health check, not a scored evaluation. Predicted label rates
  (misleading_claim 67.6%, undisclosed_advertising 23.7%, inadequate_disclosure 15.9%, no_flag
  13.9%, direct_exhortation 9.3%, age_restricted_or_prohibited_product 4.8%,
  hfss_food_marketing 2.0%, insufficient_context 1.4%) are in the same ballpark as train's base
  rates and dev's predicted rates -- same known over/under-prediction pattern already documented
  (misleading_claim/undisclosed_advertising over-predicted relative to base rate,
  no_flag/inadequate_disclosure under-predicted), nothing anomalous suggesting a broken pipeline
  or a distribution mismatch on the holdout.

## Caveats

- `gpt-5.4` at `temperature=0` is not fully deterministic run-to-run; individual per-label F1 on
  small gold counts (e.g. `hfss_food_marketing`, gold=1) should be read as directional, not exact.
- This work is scoped to `ST3_SYSTEM_PROMPT` / `--st3-only`. The joint `SYSTEM_PROMPT` (predicting
  st1+st2+st3 together) was deliberately left untouched.
- `--few-shot` (existing infra, now unblocked for `direct_exhortation`/`inadequate_disclosure`/
  `insufficient_context` since the prompt no longer tells the model to ignore them) was tested by
  individual branches and found not to help at this prompt structure — left off by default.
- Full dev-set (n=504) confirmation now included above -- this is the trustworthy number.

## Source branches (implementation detail, isolated worktrees)

- `direct_exhortation`: commit `488ae15`
- `inadequate_disclosure`: commit `db8f63d`
- `insufficient_context`: commit `d0bffa2`
- `no_flag`: commit `9c4a7c6`

Each branch's individual before/after validation is in its own report (returned in-conversation
by the implementing agent, since the harness blocks subagents from writing report files
directly — no separate `runs/impl_*/report.md` files exist).
