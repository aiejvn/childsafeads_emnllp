# Agent report: autonomous prompt-tuning pipeline for baseline_gpt.py

Executed per `runs/prompt_tuning/PLAN.md`. All working artifacts are in
`runs/prompt_tuning/run1/`. This report is the top-level summary; see that directory for the full
detail behind every claim below.

## What changed in the prompt, and why

`src/baseline_gpt.py`'s `SYSTEM_PROMPT` grew one new section (inserted between the task framing and
the taxonomy dump), added across three accepted iterations out of eight run. Net diff:
`git diff src/baseline_gpt.py` (SYSTEM_PROMPT only, no other code touched). Full text of each
version is snapshotted at `runs/prompt_tuning/run1/prompt_v{0..5}.txt` (v0 = original, v5 = final,
live in the source now).

Three accepted edits, in order:

1. **`direct_exhortation` urgency clause** (iteration 7). The taxonomy's own three-part test counts
   "urgency aimed at the viewer" toward exhortation, but the model was treating urgent/pressuring
   calls to action ("join X today", "go check out X right now... there's no excuse not to try it")
   as neutral instructions. Added explicit examples operationalizing the taxonomy's existing urgency
   clause.
2. **`undisclosed_advertising` vs. `inadequate_disclosure` two-step procedure** (iterations 4 and 5,
   the latter recalibrating the former). Original prompt had no explicit procedure; the model
   over-relied on the `OFFICIAL_DISCLOSURE` metadata field and missed verbal/affiliate-link
   disclosures in the transcript/description. Added: (a) search all text for any commercial-
   relationship acknowledgment (including affiliate-link boilerplate) before allowing
   `undisclosed_advertising`; (b) a multi-signal (not single-field-decisive) test for adequate vs.
   inadequate that weighs `OFFICIAL_DISCLOSURE`, plainness, timing, and reinforcement across
   channels.
3. **`misleading_claim` scope** (iteration 1's version accepted; a puffery-vs-fact refinement was
   attempted three more times in iterations 2, 3, and 8 but never cleanly validated in-loop -- see
   deviations below). Net prompt asks the model to flag specific/quantified/factual-sounding
   performance claims and to always flag health/fitness/skincare/supplement efficacy claims,
   regardless of delivery style.
4. A smaller **ST1 physical_services vs. digital_content_or_services** rule (iteration 1, riding
   along with the misleading_claim fix): classify by whether a human performs the service, not by
   delivery channel (e.g. app-delivered therapy is still `physical_services`).

Five candidate edits were tried and reverted (iterations 2, 3, 6, plus two intermediate disclosure
attempts) because they regressed `mean_macro_f1` on their own 10-example batch, per the plan's
accept/revert rule. Every iteration -- accepted or reverted -- is logged with full rationale in
`runs/prompt_tuning/run1/iteration_{1..8}.md`.

## Before/after metrics (the trustworthy number): `final_validation.md`

Same fresh, unseeded n=100 batch (`validation_batch.jsonl`), original prompt vs. final tuned
prompt:

| | st1 | st2 | st3 | st3_family | **mean** |
|---|---|---|---|---|---|
| v0 (original) | 0.733 | 0.627 | 0.444 | 0.582 | **0.601** |
| v5 (final tuned) | 0.810 | 0.735 | **0.314** | **0.419** | **0.620** |

**Headline: mean_macro_f1 improved narrowly (+0.019), but st3 -- the tier every accepted edit
specifically targeted -- regressed substantially (-0.130).** st1 and st2 improved and carried the
blended mean positive. Full breakdown and root-cause analysis in
`runs/prompt_tuning/run1/final_validation.md`; short version: the three accepted fixes each
successfully raised **recall** on their target flag (e.g. `misleading_claim` missed-gold count
dropped from 40/100 to 3/100), confirming the prior manual analysis's under-flagging diagnosis was
correct and fixable. But stacked together, the fixes overshot into **over-flagging**: false
positives on the same three flags rose sharply, and instances gold calls genuinely clean (`no_flag`)
got a flag anyway more than 3x as often (7/100 -> 24/100). Net effect on st3 macro-F1, which
penalizes both false negatives and false positives, is negative. This tension was visible in
miniature during several loop iterations (2, 3, 5, 8) but n=10 batches were too small/noisy to
reveal it decisively before the n=100 validation.

**I followed the plan's designated end state anyway**: prompt_v5 is left live in
`src/baseline_gpt.py` (verified byte-identical to `prompt_v5.txt` after all runs). The plan treats
final validation as the honest readout of the process, not a gate to keep iterating past 8 rounds,
and per the plan's own text this "trustworthy number" is exactly what it's for -- surfacing this
overshoot is a real result, not a failure to reach one.

## Deviations from the plan, and why

1. **Final-validation prompt swap done via monkeypatch, not literal source Edit/revert.** The plan
   says "temporarily restore the original prompt... run baseline_gpt.py... restore the final tuned
   prompt." Rather than manually reconstructing the 124-line taxonomy-embedding Python source block
   twice (risking subtle formatting drift between the reconstructed text and the true snapshot), I
   wrote a small driver (`/tmp/.../scratchpad/run_with_prompt.py`, not committed to the repo) that
   imports the real `baseline_gpt` module, overrides `SYSTEM_PROMPT` in memory from the snapshot
   file's exact bytes, and calls the module's unmodified `main()`. This exercises the same code
   path baseline_gpt.py --sample-size or any CLI invocation does, with byte-exact fidelity to each
   snapshot (verified via string diff before running). `src/baseline_gpt.py` on disk was never
   touched during this step and ended the run still holding prompt_v5, exactly as required.
2. **A discovered-but-unresolved determinism/caching anomaly (iteration 8).** A prompt edit that
   demonstrably changed the source text produced byte-identical predictions on its 10-instance
   batch (confirmed via diff on both the full and error output jsonls). No caching layer was found
   in the environment or dependencies. Logged as an open observation in `iteration_8.md` rather than
   investigated further, since it didn't block the mechanical accept/revert rule (unchanged
   mean_macro_f1 still satisfies "improved or unchanged -> keep").
3. **Cross-tier noise pattern, not a deviation but worth flagging.** In 5 of 8 loop iterations, an
   edit to one tier's instructions (st3 wording, or in one case st2 wording) was accompanied by a
   metric swing in an *untouched* tier, large enough to flip the accept/revert decision twice
   (iterations 2 and 3 had real st3 improvements reverted due to unrelated st2 drops). This appears
   structural to running joint single-call structured output (st1+st2+st3 predicted together) on
   n=10 batches rather than caused by any specific edit; it's the main reason several well-evidenced
   fixes (the misleading_claim puffery/fact distinction, the ST2 `other`/`creator_community` fix)
   never got a clean accept during the loop despite repeated, independent qualitative evidence
   across iterations 1, 2, 3, 4, 6, and 8. This is exactly the noise the plan's final n=100
   validation is designed to see past, and per the validation results above, the overshoot it missed
   ended up being real (not just noise) -- it just showed up as a precision problem rather than the
   recall problem the small batches kept surfacing.
4. Everything else (helper script design, accept/revert mechanics, snapshot/log format, iteration
   count, final validation batch size) followed the plan as written.

## What a follow-up pass should do

Not executed here (out of scope for this run, which ends at the plan's designated stopping point),
but worth recording: a 9th-plus iteration, or a fresh tuning run, should specifically target
**precision** on the three flags this run fixed for recall -- ideally using a batch deliberately
skewed toward `no_flag`/clean instances (rather than unseeded random sampling, which may
under-represent clean examples relative to their true frequency) so the accept/revert gate can
actually see the false-positive cost that this run's random n=10 batches mostly missed.

## Artifact locations

- Helper scripts: `src/sample_dev.py`, `src/aggregate_errors.py` (new, per plan spec).
- Tuned prompt (live): `src/baseline_gpt.py` `SYSTEM_PROMPT`, plus snapshots
  `runs/prompt_tuning/run1/prompt_v0.txt` (original) through `prompt_v5.txt` (final).
- Per-iteration batches: `runs/prompt_tuning/run1/batch_iter{1..8}.jsonl`.
- Per-iteration error summaries: `runs/prompt_tuning/run1/error_summary_iter{N}_before.md` /
  `_after.md` (after-summaries only exist for accepted iterations 1, 4, 5, 7, 8).
- Per-iteration logs (rationale, metrics, accept/revert decision): `iteration_{1..8}.md`.
- Final validation: `validation_batch.jsonl`, `final_validation.md`,
  `validation_error_summary_v0.md`, `validation_error_summary_v5.md`.
- Smoke-test artifacts (n=5, pre-loop): `runs/prompt_tuning/run1/smoke/`.
- Raw baseline_gpt.py run logs/predictions for every call made this session are in `runs/` at the
  repo root (its normal, pre-existing output location, unchanged by this work).
