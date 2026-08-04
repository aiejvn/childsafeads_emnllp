# Iteration 4

**Batch**: `runs/prompt_tuning/run1/batch_iter4.jsonl` (n=10), same file for before/after.

## Metrics

| | st1 | st2 | st3 | st3_family | mean |
|---|---|---|---|---|---|
| before (prompt_v1) | 1.000 | 0.735 | 0.175 | 0.250 | 0.636 |
| after (prompt_v2)  | 1.000 | 0.915 | 0.244 | 0.343 | 0.720 |

7/10 instances had errors before and after (error *count* unchanged, but the errors shrank in
kind/severity -- see below); all four metrics improved or held.

## Error summary read (before)

`error_summary_iter4_before.md`: `inadequate_disclosure` missing 3/7 -- the dominant signal this
iteration, and a fresh, independent confirmation of the pattern first seen in iteration 2 (reverted
there only because it was bundled with a misleading_claim change that caused unrelated st2 noise).
Two new details surfaced:
- One miss was an **affiliate-link disclaimer** ("— Shopping Links (Using Affiliate Links Supports
  Us!) —", "This video and description contains affiliate links... I'll receive a small
  commission") -- gold treats this as a disclosure-family flag too (inadequate_disclosure), but the
  v1 prompt's acknowledgment list only mentioned sponsor/paid/ad/partnership language, not
  affiliate-link boilerplate, so the model didn't recognize it as a disclosure signal at all.
- One miss was the by-now-familiar plain "shout out to the sponsors of this video X" pattern,
  again predicted as `no_flag`-adjacent (model predicted `misleading_claim` instead, missing
  `inadequate_disclosure` entirely).
- (Also 3x `misleading_claim` extra, 1x `age_restricted_or_prohibited_product` missed for a
  weapons-adjacent tactical shooter game -- both single-batch signals already tracked from prior
  iterations or too thin to act on; not addressed this iteration, see rationale below.)

## Rationale for the edit

Edited *only* the undisclosed_advertising/inadequate_disclosure bullet -- deliberately left
misleading_claim untouched this time, to get a second isolated read on whether the
sponsor-defaults-to-inadequate_disclosure fix survives the accept/revert gate on its own (it was
never tested in isolation before: iteration 2 bundled it with a misleading_claim rewrite and was
reverted for unrelated st2 noise). Two changes: (1) added "affiliate-link disclaimer" phrasing
(e.g. "contains affiliate links", "I'll receive a commission") to the list of acknowledgments to
search for, alongside sponsor/paid/ad/partnership language; (2) kept the "defaults to
inadequate_disclosure unless plainly child-clear" rule and the "don't treat OFFICIAL_DISCLOSURE as
decisive" instruction from the iteration-2 draft, since two independent batches now support it.

Did not act on the `misleading_claim` extra-3x or `age_restricted_or_prohibited_product` miss this
iteration -- misleading_claim over-triggering is being tracked separately (iterations 2 and 3) and
mixing it into this edit would reintroduce the confound this iteration was designed to avoid; the
age-restricted miss (weapons-adjacent shooter game) is a single occurrence and a genuinely
judgment-call case, not enough evidence to act on yet.

## Result and decision

**Accept.** mean_macro_f1 improved 0.636 -> 0.720 (st3_macro_f1 also improved 0.175 -> 0.244, so
no tiebreak needed). st1 held at a perfect 1.000 and st2 improved too (0.735 -> 0.915) -- unlike
iterations 2 and 3, this isolated edit did not trigger an st2 regression, suggesting the earlier
st2 swings really were incidental noise rather than a systematic side effect of touching the
disclosure bullet. Kept; snapshotted to `prompt_v2.txt`.
