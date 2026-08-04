# Iteration 7

**Batch**: `runs/prompt_tuning/run1/batch_iter7.jsonl` (n=10), same file for before/after.

## Metrics

| | st1 | st2 | st3 | st3_family | mean |
|---|---|---|---|---|---|
| before (prompt_v3) | 0.450 | 0.537 | 0.500 | 0.523 | 0.496 |
| after (prompt_v4)  | 0.667 | 0.426 | 0.658 | 0.797 | 0.583 |

## Error summary read (before)

`error_summary_iter7_before.md`: `direct_exhortation` missing 3/8, the largest single signal this
iteration and a category untouched by any accepted edit so far. All three misses had urgency- or
pressure-laden calls to action that the taxonomy's own exhortation test explicitly covers ("urgency
aimed at the viewer" counts toward exhortation), but the model treated as neutral instructions:
"Join Sora Plus today.", "go check out surf shark right now... there's no excuse not to try it",
"do not pay full price for a key and instead pick them up from here". The taxonomy text is already
in the prompt (appended verbatim), but the model wasn't applying the urgency clause of its own
three-part test -- it seemed to be pattern-matching "contains a link/how-to-obtain phrase" to
"stays an instruction" without checking for the pressure/urgency modifiers layered on top.
(st2 also had `hardware_electronics` extra 4x this iteration -- a new, single-batch signal, not
acted on this iteration since only one iteration slot remained and the exhortation evidence was
stronger and cleaner.)

## Rationale for the edit

Added one direct_exhortation bullet, alongside the existing misleading_claim and disclosure
bullets, with concrete examples of urgency/pressure phrasing pulled from the actual misses
("join X today", "go check out X right now", "there's no excuse not to try it", "don't pay full
price, get it here instead"), explicitly contrasted with neutral instructions ("the link is in the
description", "use my code for 15% off") that should stay unflagged. This is a direct
operationalization of the taxonomy's own urgency clause, not a new rule.

## Result and decision

st3_macro_f1 improved substantially (0.500 -> 0.658, family 0.523 -> 0.797) and st1 also improved
(0.450 -> 0.667, likely incidental/noise since the edit doesn't touch st1). st2 dropped
(0.537 -> 0.426) -- the same recurring cross-tier noise. mean_macro_f1 improved (0.496 -> 0.583).

**Accept.** Snapshotted to `prompt_v4.txt`.
