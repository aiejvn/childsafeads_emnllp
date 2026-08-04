# Iteration 5

**Batch**: `runs/prompt_tuning/run1/batch_iter5.jsonl` (n=10), same file for before/after.

## Metrics

| | st1 | st2 | st3 | st3_family | mean |
|---|---|---|---|---|---|
| before (prompt_v2) | 0.922 | 0.590 | 0.393 | 0.502 | 0.635 |
| after (prompt_v3)  | 0.922 | 0.421 | 0.568 | 0.625 | 0.637 |

## Error summary read (before)

`error_summary_iter5_before.md` showed the prompt_v2 disclosure edit had overcorrected hard the
other way: `inadequate_disclosure` predicted as extra in **7/8** error instances -- almost every
error this iteration. Traced several to full instance text and OFFICIAL_DISCLOSURE values to find
the actual discriminator gold seems to use (since the surface phrasing of "adequate" and
"inadequate" cases looked nearly identical, e.g. "today's video is brought to you by X" (adequate,
official_disclosure=true) vs. "shout out to the sponsors of this video, X" (inadequate,
official_disclosure=false) vs. "thanks to X for sponsoring this video" appearing only once, late,
with zero disclosure language anywhere in the description (inadequate, official_disclosure=true
despite that)):
- OFFICIAL_DISCLOSURE=true correlated with adequate in 3/4 cases in this evidence set, but was not
  sufficient by itself (one true-but-inadequate case where the only in-content mention was a single
  late, brief aside with no reinforcement in the description).
- OFFICIAL_DISCLOSURE=false correlated consistently with inadequate across both this iteration's
  and iteration 2's evidence.
- Adequate cases tended to have the sponsor named plainly in *both* the transcript and the
  description; the one inadequate case with official_disclosure=true had it in neither channel
  clearly (transcript: one late aside; description: no sponsor language, just a bare promo link).

This directly contradicted iteration 4's instruction to treat OFFICIAL_DISCLOSURE as non-decisive
and to default to inadequate_disclosure whenever any acknowledgment exists -- that rule was too
blunt and cost precision broadly.

## Rationale for the edit

Rewrote step 2 of the disclosure procedure to weigh multiple signals instead of applying a blanket
default: OFFICIAL_DISCLOSURE=true as a meaningful-but-not-decisive positive signal (reversing
iteration 4's "do not treat it as decisive either way" into "weigh it, don't treat it as proof by
itself" -- a softer, more accurate framing given the new evidence); an early, plain,
multiply-reinforced (spoken + written) sponsor statement leaning adequate; a single, late, or
single-channel-only acknowledgment (especially a bare promo code with no "sponsor"/"ad" language,
or affiliate-boilerplate with no plain-language statement) leaning inadequate. Kept the
"conflicting signals -> prefer inadequate_disclosure over no-issue" tiebreak and the affiliate-link
recognition from iteration 4, since neither was implicated in this iteration's overcorrection.

## Result and decision

st3_macro_f1 improved substantially (0.393 -> 0.568) and st3_family improved (0.502 -> 0.625),
confirming the recalibration reduced the false-positive rate on inadequate_disclosure. st1 held
(0.922). st2_macro_f1 dropped again (0.590 -> 0.421) -- the same cross-tier noise pattern observed
in iterations 2 and 3, on an edit that touches no st2 wording. mean_macro_f1 improved narrowly
(0.635 -> 0.637).

**Accept** (mean_macro_f1 improved, if only slightly; per the plan's mechanical rule this is a
keep, not a judgment call). Snapshotted to `prompt_v3.txt`.

## Note

This is the second and third disclosure-only edit this run (iterations 4 and 5), both landing on
the accept side despite iteration 5's edit largely walking back iteration 4's most aggressive
clause. This is expected: the search space is being explored by trial and error against small,
noisy batches, exactly as the plan anticipates -- the n=100 final validation is what will show
whether the net effect of all these back-and-forth adjustments actually holds up.
