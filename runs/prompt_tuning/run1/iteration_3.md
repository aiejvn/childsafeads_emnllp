# Iteration 3

**Batch**: `runs/prompt_tuning/run1/batch_iter3.jsonl` (n=10), same file for before/after.

## Metrics

| | st1 | st2 | st3 | st3_family | mean |
|---|---|---|---|---|---|
| before (prompt_v1) | 0.458 | 0.633 | 0.297 | 0.460 | 0.463 |
| after (candidate edit) | 0.641 | 0.311 | 0.375 | 0.603 | 0.443 |

## Error summary read (before)

`error_summary_iter3_before.md`, on a fresh batch, independently reproduces iteration 2's
diagnosis: `misleading_claim` extra 5x, substituting for `no_flag` (2x), `inadequate_disclosure`,
`insufficient_context`, and `undisclosed_advertising`. Traced each false positive back to the full
instance text:
- "Use gift code ... get 30 Faction Scrolls and 3,000 Diamonds free!" -- a promo/gift-code detail,
  not a performance claim.
- "get 25% off your own server's first month" -- a discount detail, not a performance claim.
- "scammed out of one hundred thousand dollars" (unrelated aside) + "good movement... pretty high
  skill ceiling" (subjective opinion) for a game segment with a plain sponsor mention.
None of these are unsubstantiated claims about what the product *does*; the v1 prompt's
"quantified claim" trigger is matching on the mere presence of a number (discount %, gift amount,
unrelated dollar figure) rather than on a specific performance/characteristic assertion.

## Rationale for the candidate edit

This time edited *only* the misleading_claim bullet (left inadequate_disclosure/undisclosed_
advertising untouched) to isolate the effect, per the note carried forward from iteration 2. Added
two explicit exclusions: (1) discounts/promo codes/gift-with-purchase offers are transactional
details, not performance claims -- do not flag just because a number is present; (2) vague
subjective puffery with no attached fact is not a claim either. Kept the DO-flag side narrowly on
specific/quantified/factual-sounding assertions about what the product itself does or how well it
performs, plus the taxonomy's blanket health/fitness/skincare/supplement rule.

## Result and decision

st1 improved (0.458 -> 0.641), st3 improved (0.297 -> 0.375), st3_family improved (0.460 -> 0.603)
-- all in the intended direction and with no disclosure-wording change this time, so the effect is
attributable to the misleading_claim edit specifically. But **st2_macro_f1 dropped again**
(0.633 -> 0.311), on a batch with almost no note overlap with iteration 2's regression and touching
a completely different part of the prompt. `mean_macro_f1` dropped 0.463 -> 0.443.

**Reverted**, again per the mean_macro_f1 rule. Verified `SYSTEM_PROMPT` byte-identical to
`prompt_v1.txt` after reverting.

## Observation for the final report

Two iterations in a row now show a real, reproducible st3 improvement from narrowing the
misleading_claim trigger, undone by an st2 swing that appears unrelated to the edited text (this
time the edit touched zero st2-adjacent wording, ruling out the "entangled edits" theory from
iteration 2). The likely explanation: with n=10 and structured multi-label output generated in one
joint call, st2 macro-F1 is highly sensitive to single-instance label flips (few labels are
present in any 10-example sample, so one flip swings the macro average sharply), and GPT-5.4
appears to not be perfectly deterministic at temperature=0 across otherwise-unrelated prompt
edits. This makes the per-iteration accept/revert gate, as specified, a high bar for any edit that
doesn't also improve st2 by luck on that particular batch -- consistent with the plan's own caveat
that 10-example deltas are noisy and the real signal is the n=100 final validation. Continuing to
follow the mechanism exactly as specified rather than overriding it; flagging this pattern for
whoever reads the final report, and revisiting the misleading_claim fix as a candidate again in a
later iteration in case a future batch happens not to trigger the st2 swing.
