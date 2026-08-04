# Final validation: original prompt (v0) vs. final tuned prompt (v5)

Same fresh, unseeded n=100 sample (`validation_batch.jsonl`), run with each prompt in turn via
monkey-patching `baseline_gpt.SYSTEM_PROMPT` from the snapshot file before calling the module's
real, unmodified `main()` (chosen over manually re-editing the large taxonomy-embedding source
block twice, to guarantee byte-exact fidelity to each snapshot; see `agent_report.md` deviations
section). `--max-concurrency 15` was used to keep n=100 runs fast; this does not affect predictions
(same per-instance calls, just more parallel).

## Headline metrics

| | st1_macro_f1 | st2_macro_f1 | st3_macro_f1 | st3_family_macro_f1 | **mean_macro_f1** |
|---|---|---|---|---|---|
| **v0 (original)** | 0.733 | 0.627 | 0.444 | 0.582 | **0.601** |
| **v5 (final tuned)** | 0.810 | 0.735 | 0.314 | 0.419 | **0.620** |
| delta | +0.077 | +0.108 | **-0.130** | **-0.163** | +0.019 |

Runs: v0 -> `runs/submission_gpt_20260803_193706.jsonl` (log `runs/run_20260803_193706_full_gpt-5.4.log`),
77/100 instances had an error. v5 -> `runs/submission_gpt_20260803_193723.jsonl` (log
`runs/run_20260803_193723_full_gpt-5.4.log`), 82/100 instances had an error. Error jsonls aggregated to
`validation_error_summary_v0.md` and `validation_error_summary_v5.md` in this directory.

## Headline result

mean_macro_f1 improved narrowly (0.601 -> 0.620), driven entirely by st1 (+0.077) and st2
(+0.108) -- both plausible, if not directly targeted (st1 got one explicit edit, the
physical_services human-performed test in iteration 1; st2 got no accepted edit all run, so its
improvement here is likely a side effect of the st3 prompt restructuring, or batch composition, or
noise, consistent with the cross-tier interaction observed all through the loop).

**st3_macro_f1 -- the tier every accepted edit this run specifically targeted, and the dominant
error surface per the original manual analysis -- regressed by a large margin (0.444 -> 0.314,
family score 0.582 -> 0.419).** This is the one number that matters most for judging whether the
tuning worked on its own terms, and at n=100 it says no, net negative.

## Why: a recall/precision overshoot, visible only at this larger scale

Comparing the aggregated error breakdowns (`validation_error_summary_v0.md` vs. `_v5.md`) shows
exactly what happened:

| st3 flag pattern | v0 (original) | v5 (tuned) |
|---|---|---|
| `misleading_claim` missing (recall miss) | 40x | 3x |
| `misleading_claim` extra (false positive) | 1x | 28x |
| `inadequate_disclosure` missing | 16x | 2x |
| `inadequate_disclosure` extra | 10x | 25x |
| `direct_exhortation` missing | 6x | 2x |
| `direct_exhortation` extra | 5x | 32x |
| `no_flag` missing (gold clean, model flagged it anyway) | 7x | **24x** |
| `undisclosed_advertising` extra (precision failure on that flag specifically) | 16x | 4x |

The tuning worked exactly as designed on **recall**: the three flags targeted by accepted edits
(misleading_claim, inadequate_disclosure/undisclosed_advertising, direct_exhortation) all show
large drops in missed-gold-label counts, confirming the original under-flagging bias documented in
the prior manual analysis (memory `project_gpt_baseline_error_analysis`) was real and the fixes
addressed it. `undisclosed_advertising` extra also dropped sharply (16x -> 4x), showing the
disclosure-type confusion fix worked as intended too.

But **precision collapsed on the same three flags**: extra (false-positive) counts on
misleading_claim, inadequate_disclosure, and direct_exhortation all rose sharply, and critically,
`no_flag` misses (truly clean content the model now flags anyway) more than tripled (7 -> 24). The
net effect on macro-F1, which penalizes both false negatives and false positives, is negative for
st3 even though several individual sub-patterns improved.

This matches a pattern visible but not fully legible during the loop itself: iterations 2, 3, 5,
and 8 each showed the *same* tension in miniature (fixing an under-flagging pattern shows up as an
st3 improvement on a 10-example batch, but small-n noise on st2 obscured whether st3's own
precision was moving in the wrong direction at the same time). The n=10 batches were good at
surfacing individual missed-label patterns (which the manual per-iteration diagnosis correctly
identified and fixed one at a time) but too small and noisy to catch that three separate,
individually-reasonable recall fixes, applied together, would compound into an aggressive
over-flagging prompt once combined. That compounding effect only becomes visible at n=100, which
is exactly why the final validation step exists per the plan.

## Bottom line

- The specific, well-evidenced individual diagnoses were correct (verified independently across
  2-3 batches each): the original prompt under-flagged misleading_claim, mishandled the
  undisclosed_advertising/inadequate_disclosure distinction, and under-detected urgency-driven
  direct_exhortation appeals.
- The fixes for all three were effective at raising recall (large reduction in missed-gold-label
  counts for exactly those flags).
- But stacked together, the three fixes overshot into over-flagging, and st3_macro_f1 -- the
  primary target -- is net worse on the trustworthy n=100 number, dragged down by a large rise in
  false positives on content gold calls clean (`no_flag` misses more than tripled).
- st1 and st2 improved, keeping the blended mean_macro_f1 narrowly positive, but this should not be
  read as validating the st3-focused tuning effort on its own terms.

See `agent_report.md` for the full writeup, including what a corrective next iteration would
target (tightening precision on the same three flags without giving back the recall gains, e.g. a
calibration pass specifically using a batch balanced toward clean/no_flag instances so the accept/
revert gate can actually see the false-positive cost that n=10 samples mostly missed).
