# Iteration 6

**Batch**: `runs/prompt_tuning/run1/batch_iter6.jsonl` (n=10), same file for before/after.

## Metrics

| | st1 | st2 | st3 | st3_family | mean |
|---|---|---|---|---|---|
| before (prompt_v3) | 1.000 | 0.307 | 0.520 | 0.677 | 0.609 |
| after (candidate edit) | 1.000 | 0.404 | 0.335 | 0.446 | 0.580 |

## Error summary read (before)

`error_summary_iter6_before.md`: for the first time this run, st2 is the dominant error tier
(6/7 instances) rather than st3. `other` missing 3x, `creator_community` both missing 2x and extra
2x. This is the same under-use-of-`other` pattern flagged but deferred in iterations 1, 3, and 4
(weak single-batch evidence each time) -- across 4 iterations it's now missing 5 times total, a
real recurring pattern. Traced the clearest case: a podcast ad ("30 morbid minutes... Subscribe
now on Spotify, Apple Podcasts...") -- gold `other`, predicted `creator_community`. Per the
taxonomy, `creator_community` is specifically merchandise/paid-membership/Patreon, not a bare
"subscribe to my content" call; the model appears to pattern-match "fan engagement" language to
`creator_community` even when nothing is actually being sold as a membership/merch product.

## Rationale for the edit

Added one ST2 paragraph: don't force-fit the nearest keyword-associated category when nothing \
specific genuinely matches -- use `other`; and sharpened `creator_community` to require actual \
merch/membership/Patreon being sold, not just a subscribe call-to-action.

## Result and decision

st2_macro_f1 improved as intended (0.307 -> 0.404). But **st3_macro_f1 dropped sharply**
(0.520 -> 0.335) even though the edit touched zero st3 wording -- the same cross-tier noise seen
in iterations 2, 3, and 5, this time running the other direction (an st2 edit perturbing st3
instead of an st3 edit perturbing st2). `mean_macro_f1` dropped 0.609 -> 0.580.

**Reverted.** Verified `SYSTEM_PROMPT` byte-identical to `prompt_v3.txt` after reverting.

## Observation

This is now the fourth iteration (2, 3, 5-adjacent, 6) showing a metric swing in a tier the edit
didn't touch, in both directions (st3-edit -> st2 swing, and now st2-edit -> st3 swing). This looks
like a structural property of this pipeline at n=10 with joint single-call structured output,
not something addressable by choosing which tier to edit more carefully. The `other`/
`creator_community` fix is well-evidenced across 4 iterations and worth retrying on a future batch,
or reassessing directly at the n=100 final-validation scale where this noise averages out.
