
# Handoff — childsafeads_emnllp, autoresearch/aug13-qwen06b

**2026-08-17, ~21:15.** Session pivoted mid-stream from the Qwen3-0.6B generative-LLM st1
track to a new, much cheaper LoRA-adapted-encoder track per explicit user redirect. Both
tracks are live; this doc covers current state, confirmed results, and the queue.

## Currently running

**Nothing.** GPU is free. The hyperparameter sweep on the roberta-base 5-way st1 classifier
(Track 2, HANDOFF next-candidates item #2) ran and finished 2026-08-17 ~21:20-21:28 — both
directions **discarded**, r8/a16/single-LR remains the standing default:
1. Capacity bump `--lora-r 16 --lora-alpha 32`: dev macro_f1=0.586 (best@epoch3), test=0.537,
   test none_f1=0.261 — below the r8/a16 baseline's replicates on both macro and none. Confirms
   Track 1's inverted-U capacity finding extends to Track 2, and bites one step earlier (already
   regressing at r16, not just r32).
2. Separate head LR `--head-lr 1e-3` (LoRA stays at `--lr 2e-4`): dev macro_f1=0.587
   (best@epoch4), dev none_f1=0.519 (best none score ever seen for this classifier) but **test
   none_f1 collapsed to 0.200** — the faster-learning head overfits the none class to dev
   specifically, a real generalization failure masked by a fine-looking macro gap. Do not adopt.

Both logged to `runs/results_st1_classifiers.csv` (rows 6-7) and `runs/runs.log`, committed.
Remaining untried sweep axes from next-candidates item #2: `--oversample-rare-st1` factor
(currently fixed at 3), and combinations aren't likely worth it given both single-axis moves
regressed.

Prior job (`legal-bert-base-uncased` 5-way st1 classifier) finished and was logged/committed
(`281facb`): clearly worse than roberta-base at the same untuned hyperparameters — dev
macro_f1=0.394 (still climbing, no plateau by epoch 5), test macro_f1=0.339 with **test none F1
collapsed to 0.000** (a real generalization failure, not just slow convergence). Discarded for
now; would need its own LR sweep to get a fair shot. roberta-base remains the standing encoder
choice for this track.

## The big picture: two parallel tracks

### Track 1 — Qwen3-0.6B generative LLM, st1-only (`src/lora/lora_train_generative.py`)
Results in `runs/lora-qwen/results.csv`. Memory: `feedback_st1_focus.md`,
`feedback_rotating_test_holdout.md`, `project_minority_select_resume_adapter.md`.

**Standing config, in priority order (per updated "prefer dev>=test among agreeing runs"
rule):**
1. **PRIMARY**: `--st1-only --pos-weight --oversample-rare-st1 3`, r=8/alpha=16, `--context
   full`. Confirmed reproducible: dev/test st1_macro_f1 = 0.791/0.781 (replicate), dev/test
   agree closely, dev>=test. This is the safest default to cite.
2. Secondary candidate: same + `--lora-r 16 --lora-alpha 32`. Confirmed real via replicate
   (test 0.834, 0.804) but ranks below #1 because test>dev in its replicate (less trustworthy
   per the dev>=test preference), even though both configs individually look strong.
3. `--lora-r 32 --lora-alpha 64`: confirmed REGRESSION (dev=0.758/test=0.686, both below #1
   and #2). Capacity sweep is an inverted-U — don't go past r16 without a strong reason.
4. `--few-shot` alone (no pos-weight/oversample): real standalone gain (dev/test
   0.740/0.770) but smaller than #1, and **do NOT stack** `--few-shot` with
   `--pos-weight --oversample-rare-st1` — confirmed they interfere (0.728/0.726, worse than
   either alone).
5. `--context transcript` (cheapest context rung): confirmed clear regression (dev/test
   0.574/0.573) — st1 needs the full product-page/dialog-flow context, keep `--context full`.
6. `--minority-select` (new flag, see below): first attempt's default
   `--majority-f1-tolerance 0.02` was too strict and degenerated to a worse pick than the
   default selection metric. A wider-tolerance retry (`--majority-f1-tolerance 0.12`) was
   **killed mid-run** (epoch 2/5) to free the GPU for the encoder pivot — never finished, no
   conclusion. Could be resumed/rerun if this track becomes the priority again.

**Critical gotcha**: `ST1_LABELS` has a real 5th value, `other` (~2 train instances,
essentially unlearnable). It's also the parse-failure fallback value in
`lora_generative.py`'s `_fallback()`. When it appears in a small eval sample it forces a
spurious ~0.000 term into the macro average, swinging the headline score by ~0.15-0.2 from a
SINGLE instance. Always check the per-label breakdown for an unexpected `other` before trusting
a surprisingly low `st1_macro_f1`.

**VRAM reality check**: this recipe (full context, max-length=4096) uses **~16-18GB solo**, not
the ~10GB an older memory note assumed. Two separate attempts to pair a second job alongside it
both OOM-crashed tonight. Check `nvidia-smi` before ever trying to pair a job with this recipe.

### Track 2 — LoRA-adapted encoder + MLP head, st1-only (NEW, this session)
Results in `runs/results_st1_classifiers.csv` (separate file, different schema from Track 1's
results.csv — do not conflate them). Memory: `feedback_encoder_mlp_pivot.md`.

Two scripts:
- `src/lora/lora_train_st1_none.py` — binary none-vs-not-none. **User's own script**,
  committed directly (317559a), not built by this session (this session added it to git
  along with an uncommitted `--test-holdout` addition already sitting in the user's working
  tree).
- `src/lora/lora_train_st1_classifier.py` — **NEW, built this session**, generalizes the
  above to the full 5-way st1 taxonomy. Smoke-tested before real runs. Argmax decoding
  (no threshold tuning needed, unlike the binary script).

**Standing config for both**: `--model FacebookAI/roberta-base --context full --max-length 512
--epochs 5 --batch-size 16 --lr 2e-4 --lora-r 8 --lora-alpha 16 --target-modules query,value
--class-weight --oversample-none 3` (or `--oversample-rare-st1 3` for the 5-way script)
`--test-holdout 500`.

**Confirmed results (both replicated on fresh splits):**
| approach | dev macro_f1 | dev none_f1 | test macro_f1 | test none_f1 |
|---|---|---|---|---|
| binary none-vs-not, run 1 | 0.759 | 0.526 | 0.611 | 0.235 |
| binary none-vs-not, replicate | 0.759 (exact match) | 0.526 (exact match) | 0.663 | 0.333 |
| 5-way st1, run 1 | 0.598 | 0.452 | 0.559 | 0.381 |
| 5-way st1, replicate | 0.559 | 0.370 | 0.553 | 0.286 |

**Headline finding: the 5-way classifier does NOT collapse on `none`**, and has the best
dev/test agreement of anything in this entire session (both tracks) — gaps of -0.039 and
-0.006 across the two replicates, both dev>=test. `other` stays at 0.000 in every run
(near-zero train instances, consistent across both architectures — not an
architecture-specific failure).

**Massive speed/cost win**: ~4.5 min per full run (train + dev-eval-every-epoch +
test-holdout) vs Track 1's 60-90 min. ~1-5GB VRAM vs ~16-18GB. **Both jobs fit in the GPU
simultaneously** (only ~5GB combined) — always run replicates/comparisons in parallel on this
track, no need to serialize like Track 1.

**New flags to know about** (`--minority-select`, `--resume-adapter`, both added by the user
directly to `lora_train_generative.py` mid-session, commits `e61b805`/`c14b044`) — see
`project_minority_select_resume_adapter.md` for full detail. `--minority-select` picks the
best checkpoint by rare-label F1 within a majority-F1 tolerance instead of the default metric;
`--resume-adapter` continues training from an existing LoRA checkpoint.

## Next candidates (not yet started)
1. `src/last_layer/last_layer_train.py` — frozen-encoder + last-N-layers, no LoRA at all, an
   even cheaper baseline. Currently trains st1/st2/st3 jointly with no `--st1-only` mode; would
   need that flag added (mirror how it was added to `lora_train_generative.py` — see
   `feedback_st1_focus.md` history for that precedent).
2. Hyperparameter sweep on the roberta-base 5-way classifier now that iteration is cheap:
   `lora_r`, `--oversample-rare-st1` factor, `--head-lr` (separate LR for the classifier head).
3. If legal-bert is worth a second look, retry with a higher LR (e.g. 5e-4 to 1e-3) before
   fully writing off the architecture — it was never tuned, just run at roberta's LR.
4. A peer Claude Code session was also active on this repo earlier (helping debug the same
   none-class problem via a different angle) — the user said "stopping that agent" before
   redirecting this session. Unclear if that peer session is still around; check
   `ListAgents` if coordination matters again.

## Housekeeping notes
- `git status` will show several **untracked, intentionally-uncommitted** directories: leftover
  `epoch_N/` checkpoint subdirs from the `--minority-select` runs (only `best/` gets committed
  by convention, not every per-epoch checkpoint), and a partial `...-minority-select-wide/`
  output dir from a job that was killed mid-run (epoch 2/5) to free the GPU. Safe to ignore or
  `rm -rf` if you want a clean tree — nothing valuable is in them that isn't already in the
  committed `results.csv` rows or logs.
- `.gitignore` excludes `**/*.safetensors` — adapter weights never get committed, only
  `best/README.md`, `adapter_config.json`, `predictions.jsonl`/`submission*.jsonl`,
  `thresholds.json` where applicable.
- Always `tee -a runs/runs.log` when launching anything (never `> /dev/null`), and log every
  run's result to the appropriate results file + commit, per standing practice all session.
- Push is broken in this environment (no git credentials) — all work is local commits only.
