# Autonomous prompt-tuning pipeline for baseline_gpt.py

## Context

`src/baseline_gpt.py` predicts ST1/ST2/ST3 with a single hardcoded `SYSTEM_PROMPT`
(persona/instructions + `public_data_dev/labels_taxonomy.md` appended verbatim).
There is no prompt-tuning infrastructure in the repo today — the prompt has only
been hand-edited (see git history: "Updating prompts to use label_taxonomy.md").
A prior manual error-analysis pass (memory `project_gpt_baseline_error_analysis`,
run on `runs/submission_gpt_error_20260801_205209.jsonl`) found concrete,
fixable failure patterns — st3 dominates errors, systematic under-flagging bias,
`misleading_claim` misses, `undisclosed_advertising`/`inadequate_disclosure`
confusion, physical-vs-digital ST1 confusion, ST2 `other` under-use — which is
exactly the kind of signal this pipeline should discover and act on, every run,
instead of by hand.

Goal: an iterative loop that samples a fresh, unseeded random batch of ~10 dev
examples each round, runs the current prompt on it, and revises `SYSTEM_PROMPT`
to fix the observed failures — then confirms the edit didn't regress before
keeping it. After N rounds, a larger confirmation run compares the original
prompt vs. the final tuned prompt on a fresh, bigger sample, so results aren't
just noise from tiny 10-example batches.

**Revision (this version of the plan):** the prompt-rewriting step is done by
the Claude Code agent itself — reading run output/stderr and an aggregated
error report and editing `SYSTEM_PROMPT` directly — **not** by a script that
calls out to an LLM API as a separate "optimizer." Scripts are only used for
the mechanical, non-judgment parts: sampling and error aggregation.

## Design decisions (confirmed with user)

- **Tunable scope**: the whole `SYSTEM_PROMPT` is editable, including the
  taxonomy wording appended to it — not just a preamble.
- **Who tunes it**: the agent reasons about each iteration's errors and edits
  the prompt directly via the Edit tool. No optimizer-LLM API call, no
  `prompt_tune.py` orchestrator script.
- **Sampling**: unseeded (`random.sample()` with no fixed seed) — a different
  ~10 examples every round, not the existing seeded `random.Random(42)`
  smoke-test path already in `baseline_gpt.py` (that path is untouched).

## Helper scripts

Only mechanical, non-judgment work goes in scripts — error extraction/
aggregation and batch sampling, per the user's steer. No script performs the
actual prompt rewrite.

### 1. `src/sample_dev.py`

```
python src/sample_dev.py public_data_dev/dev.jsonl --n 10 --out runs/prompt_tuning/<run>/batch_iter{N}.jsonl
```

- Loads instances via the existing `starting_kit/load_data.py:load_split`.
- Draws an **unseeded** `random.sample` of `--n` instances.
- Writes them verbatim to `--out` as a standalone JSONL file. Because
  `baseline_gpt.py`'s `target` argument is just a path to any release-format
  JSONL file, this sampled file can be fed straight into `baseline_gpt.py`
  unmodified, and reused for both the "before" and "after" run within one
  iteration so the comparison is apples-to-apples (same batch, not a fresh
  draw each time).

### 2. `src/aggregate_errors.py`

```
python src/aggregate_errors.py runs/submission_gpt_error_<ts>.jsonl \
    [--dev public_data_dev/dev.jsonl] [--max-detailed 15] \
    --out runs/prompt_tuning/<run>/error_summary_iter{N}.md
```

- Reads the `{instanceID, gold, pred, errors}` rows that `baseline_gpt.py`
  already writes to `runs/submission_gpt_error_*.jsonl` — no changes needed
  to `baseline_gpt.py` to produce this input.
- Aggregates: per-tier error counts (st1/st2/st3), missing/extra label
  frequency tables, and inferred missing→extra substitution pairs — the same
  kind of breakdown already done by hand in memory
  `project_gpt_baseline_error_analysis` (st3 dominance, under-flagging bias,
  `misleading_claim` misses, disclosure-type confusion, etc.), now produced
  automatically every iteration instead of once by hand.
- For up to `--max-detailed` of the most illustrative error instances, looks
  up the full instance text (transcript/video/product page) from `--dev` by
  `instanceID` and includes it verbatim, so the agent reading the report can
  see *why* a call was wrong, not just the label diff.
- Writes one markdown report. This report is the feedback the agent reads
  each iteration — it replaces what would otherwise have been an optimizer
  LLM's input.

No snapshot script is needed: prompt versions are saved by having the agent
`Read` the current `SYSTEM_PROMPT` block and `Write` it to
`runs/prompt_tuning/<run>/prompt_v{N}.txt` directly.

## Tuning loop (agent-driven, not a script)

For `i = 1..iterations` (default 8):

1. `python src/sample_dev.py public_data_dev/dev.jsonl --n 10 --out runs/prompt_tuning/<run>/batch_iter{i}.jsonl` — fresh unseeded batch.
2. `python src/baseline_gpt.py runs/prompt_tuning/<run>/batch_iter{i}.jsonl` — run the *current* `SYSTEM_PROMPT` on the batch; note `mean_macro_f1` etc. from the run log/stdout and the error jsonl path.
3. `python src/aggregate_errors.py <error_jsonl> --out runs/prompt_tuning/<run>/error_summary_iter{i}_before.md` — compact feedback.
4. Snapshot the current `SYSTEM_PROMPT` text to `runs/prompt_tuning/<run>/prompt_v{i-1}.txt` (pre-edit version, for revert).
5. **Agent reads the error summary + current prompt and edits `SYSTEM_PROMPT` in `src/baseline_gpt.py` directly** (Edit tool) to address the observed failure patterns, reasoning about root cause rather than pattern-matching on label names.
6. Re-run `python src/baseline_gpt.py runs/prompt_tuning/<run>/batch_iter{i}.jsonl` on the **same** batch file with the edited prompt → new metrics.
7. Compare `mean_macro_f1` (tiebreak on `st3_macro_f1`, since st3 is the dominant error surface per the prior analysis):
   - Improved or unchanged → keep the edit; snapshot to `prompt_v{i}.txt`.
   - Regressed → revert `SYSTEM_PROMPT` via Edit back to the `prompt_v{i-1}.txt` snapshot.
8. Log the iteration to `runs/prompt_tuning/<run>/iteration_{i}.md`: batch instanceIDs, before/after metrics, the prompt diff, rationale, accept/reject decision.

## Final validation

After all iterations:

1. `python src/sample_dev.py public_data_dev/dev.jsonl --n 100 --out runs/prompt_tuning/<run>/validation_batch.jsonl` — larger, fresh, unseeded sample.
2. Temporarily restore the **original** prompt from `prompt_v0.txt`, run `baseline_gpt.py` on the validation batch, record metrics.
3. Restore the **final tuned** prompt, run `baseline_gpt.py` on the same validation batch, record metrics.
4. Write both side by side to `runs/prompt_tuning/<run>/final_validation.md` — this is the trustworthy number; per-iteration 10-example deltas are just the search signal and are expected to be noisy.
5. Leave the tuned prompt live in `src/baseline_gpt.py` as the end state.

## Cost/time note

Each iteration = 2 `baseline_gpt.py` runs of size `--n` (before + after edit) —
no separate optimizer-LLM billing, since the agent does that reasoning itself.
Default `--iterations 8 --n 10` ≈ 160 predictor calls, plus `2 * 100 = 200` for
final validation ≈ ~360 predictor calls total.

## Execution mode

**I (this Claude Code session) will launch the implementation agent myself**
right after this plan is finalized — this is not a description for the user
to act on later. I will call the Agent tool (full file/tool access, e.g.
`subagent_type: claude`) with this plan as its brief, so it can build the two
helper scripts and then run the full tuning loop end-to-end (it involves many
repeated tool calls across iterations, well suited to a background agent
rather than doing every step inline here). It will run in the background and
save its final report (what changed, before/after metrics, any deviations
from plan) to `runs/prompt_tuning/agent_report.md`, which I'll summarize back
here once it completes.

## Files touched

- `src/sample_dev.py` — new helper (unseeded batch sampler).
- `src/aggregate_errors.py` — new helper (error report generator).
- `src/baseline_gpt.py` — **no refactor**; only its `SYSTEM_PROMPT` constant
  is edited iteratively during tuning. It already accepts any JSONL path as
  `target`, so the sampled batch files work with it unmodified.
- `runs/prompt_tuning/<run>/` — batch files, error summaries, prompt
  snapshots (`prompt_v*.txt`), per-iteration logs, `final_validation.md`.

## Verification

1. Smoke test the helpers: `sample_dev.py --n 5`, run `baseline_gpt.py` on the sample, run `aggregate_errors.py` on the resulting error jsonl, confirm the report is readable and actually useful for deciding a prompt edit.
2. Do one full manual iteration end-to-end to confirm the accept/revert/logging mechanics work as designed.
3. Confirm `final_validation.md` shows original vs. tuned metrics on the same held-out batch.
4. Full run: 8 iterations, `--n 10`.
5. Confirm `baseline_gpt.py`'s existing CLI (`python src/baseline_gpt.py public_data_dev/dev.jsonl --sample-size 10`) still behaves exactly as before (seeded smoke-test path untouched).
