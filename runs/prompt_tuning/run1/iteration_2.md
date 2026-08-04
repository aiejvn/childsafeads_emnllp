# Iteration 2

**Batch**: `runs/prompt_tuning/run1/batch_iter2.jsonl` (n=10), same file for before/after.

## Metrics

| | st1 | st2 | st3 | st3_family | mean |
|---|---|---|---|---|---|
| before (prompt_v1) | 0.641 | 0.884 | 0.179 | 0.222 | 0.568 |
| after (candidate edit) | 0.641 | 0.619 | 0.292 | 0.368 | 0.517 |

## Error summary read (before)

`error_summary_iter2_before.md`: 7/9 instances had an st3 error, but this time in the *opposite*
direction from iteration 1 -- the v1 edit's misleading_claim trigger list was overcorrecting:
- `misleading_claim` predicted as extra 4x, all substituting for gold `no_flag`. Inspecting the
  four instances: the model was flagging ordinary marketing puffery/opinion language ("Flex adjust
  technology... perfectly adjust to your face", "top rated VPN service", "cooking at home is
  better than anything you could do when you order in") as misleading_claim. These are subjective/
  superlative claims, not specific factual assertions -- the v1 prompt's "superlatives" trigger was
  too broad and caught puffery that EU ad-law treatment (and this dataset's gold labels) does not
  treat as actionable.
- `inadequate_disclosure` missing 2x: both instances had a plain "thanks to X for sponsoring"-style
  mention (one with OFFICIAL_DISCLOSURE=true, one with it false) and gold still called it
  `inadequate_disclosure`, not "no issue." This shows OFFICIAL_DISCLOSURE correlates weakly with
  actual adequacy, and that ordinary "thanks to sponsor" phrasing should default to
  inadequate_disclosure rather than being read as sufficient.
- 1 `direct_exhortation` extra ("make sure you sign up for X" -- basic instruction, gold no_flag);
  single occurrence, not acted on this iteration.

## Rationale for the candidate edit

Rewrote the misleading_claim bullet to explicitly separate (a) vague subjective puffery/opinion
("the best", "amazing", "perfectly", superlatives with no attached fact) -- NOT to be flagged --
from (b) specific/quantified/factual-sounding assertions presented as fact (percentages, named
guarantees, "median salary of 175k") -- DO flag, plus the taxonomy's blanket rule for health/
fitness/skincare/supplement efficacy claims.

Rewrote the disclosure bullet into an explicit two-step procedure: search for any acknowledgment
first; if found, treat it as `inadequate_disclosure` *by default* rather than "fine," since
ordinary creator sponsor-mentions use adult register a child won't parse as an ad disclosure.
Explicitly told the model not to treat `OFFICIAL_DISCLOSURE` as decisive in either direction, since
the evidence showed it correlates poorly with actual adequacy in this dataset.

## Result and decision

st3_macro_f1 improved (0.179 -> 0.292) and st3_family improved too (0.222 -> 0.368), consistent
with the intended fix. But **st2_macro_f1 dropped sharply (0.884 -> 0.619)** even though the edit
did not touch any ST2-related wording -- this is most likely cross-tier noise from the joint
single-call structured-output generation (editing the ST3 guidance shifts the model's overall
reasoning trace enough to perturb ST2 answers too) combined with small-n (10) variance. Whatever
the cause, `mean_macro_f1` dropped 0.568 -> 0.517.

**Reverted.** Per the plan's accept/revert rule (compare `mean_macro_f1` first), this edit
regressed the primary metric, so `SYSTEM_PROMPT` was reverted to `prompt_v1.txt` via Edit and
verified byte-identical afterward. No `prompt_v2.txt` snapshot is produced for a reverted
iteration -- the live prompt stays at v1.

## Carried forward

The diagnosis is still valuable even though the edit was reverted:
- The puffery-vs-specific-claim distinction for `misleading_claim` is worth reintroducing later,
  ideally tested on a batch that also has clean `no_flag` instances with puffery language in it, to
  directly check for regained precision without the confound seen here.
- The "sponsor mention defaults to inadequate_disclosure, ignore OFFICIAL_DISCLOSURE" finding is
  well evidenced twice now (iter1's undisclosed_advertising misses and iter2's inadequate_disclosure
  misses) and is a good candidate to reintroduce in a future iteration, possibly isolated from the
  misleading_claim change so the two effects don't get entangled in one accept/revert decision.
