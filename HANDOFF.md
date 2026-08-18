
# Handoff — childsafeads_emnllp, autoresearch/aug13-qwen06b

**2026-08-17, ~21:15.** Session pivoted mid-stream from the Qwen3-0.6B generative-LLM st1
track to a new, much cheaper LoRA-adapted-encoder track per explicit user redirect. Both
tracks are live; this doc covers current state, confirmed results, and the queue.

## Currently running

**One job: `allenai/longformer-base-4096` 5-way st1 classifier**, `runs/st1-classifier-longformer`,
launched 2026-08-18 ~01:24. First test of a genuinely-long-context encoder (4096 native position
embeddings, vs roberta-base's 512 ceiling that motivated the truncation-side fix below) — user
provided the model locally at `./models/allenai/longformer-base-4096`. Config: `--context full
--max-length 4096 --truncation-side left` (still set for the rare >4096-token tail, but at this
length only ~14/2857 instances (0.5%) need any truncation at all — see the context-window sizing
note below), r8/a16 LoRA on `query,value` only (Longformer's *global* attention projections,
`query_global`/`value_global`/`key_global`, are NOT LoRA-adapted this round — a candidate
follow-up if this run looks promising). `--batch-size 2` (batch=4 OOM'd, batch=1 and 2 both fit;
picked 2 for throughput — Longformer's HF eager sliding-window attention implementation is much
more memory-hungry than its "linear attention" reputation suggests, no flash-attention kernel
available for it). ~1.3-1.5 it/s, 956 steps/epoch, ETA ~50-60 min for all 5 epochs + evals —
check `runs/run_20260818_012406_lora_train_st1_classifier_longformer.log` or `ps -p 1220782` for
status. **This is the most important pending result — report it before starting anything else.**

**Context-window sizing (answers "how much context would we need for everything"):** measured
across all 2857 train+dev instances tokenized with `full_context`: median 1253 tokens, mean
1484, max 14624. Coverage by cap: 512→2.5%, 1024→32.3%, 2048→79.0%, **4096→99.51%** (14
instances still truncated), 6144→99.93%, 8192→99.965% (1 instance left). RoBERTa cannot exceed
512 regardless of `--max-length` (hard architectural ceiling from its position embeddings) —
this is *why* the truncation-side bug below existed in the first place and why a different
architecture (Longformer, 4096; ModernBERT, 8192) is needed to actually use more context.

**Also ran (2026-08-18, before Longformer): a `--max-length` sweep within RoBERTa's 512 ceiling**
(128, 256, vs standing 512, all with `--truncation-side left`) to characterize the
context-length-vs-performance curve while waiting for a longer-context model. Non-monotonic and
likely mostly noise given the small test-holdout none-counts: 128→dev=0.616/test=0.577(best seen
all-time, but low-transcript-signal at this length), 256→dev=0.595/test=0.509, 512→dev=0.622-0.645/
test=0.538-0.546. Logged (`runs/results_st1_classifiers.csv`), not a strong standalone
conclusion either way — filed as data points for the eventual longer-context comparison.

**MAJOR FINDING 2026-08-18, CONFIRMED + PROMOTED: `--truncation-side left` is the new standing
default for `lora_train_st1_classifier.py`.** roberta-base's 512-token position-embedding
ceiling silently drops the product PAGE block for ~78%% of instances: `render_context(...,
"full")` puts TRANSCRIPT first and PAGE last (`src/common/__init__.py`), and at `--max-length
512`, HF's default right-truncation (keep start, drop end) cuts the PAGE block entirely for
234/300 (78%) of a sampled train set (median full-context length: 1268 tokens vs the 512
budget). The PAGE block was already confirmed decisive for st1 in Track 1 (full context vs
transcript-only, `feedback_st1_focus.md`) — every Track-2 roberta run all session has silently
been running closer to transcript-only than genuine "full" context. Added `--truncation-side
{left,right}` (`left` keeps the END of the text instead, preserving PAGE at the cost of the
transcript's tail). Two fresh-split replicates, standing recipe otherwise unchanged:
| run | dev macro_f1 | dev none_f1 | test macro_f1 | test none_f1 |
|---|---|---|---|---|
| left, run 1 | 0.622 | 0.500 | 0.546 | 0.316 |
| left, run 2 (replicate) | **0.645** | 0.562 | 0.538 | 0.222 |
| right (this session's control run) | 0.543 | 0.276 | 0.491 | 0.190 |
| right (original historical baseline, 2 replicates) | 0.598 / 0.559 | 0.452 / 0.370 | 0.559 / 0.553 | 0.381 / 0.286 |

Both `left` dev scores (0.622, 0.645) clear every other config tried in this classifier's
history (previous best 0.598) with good dev>=test agreement both times (gaps 0.076, 0.107).
Test macro_f1 (0.546, 0.538) lands roughly in/near the historical baseline test band
(0.553-0.559) — not a test-side win the way dev is, but not a regression either, and dev is the
cleaner/less noisy signal per `feedback_rotating_test_holdout.md`. **New standing config**:
`--model FacebookAI/roberta-base --context full --max-length 512 --truncation-side left
--lora-r 8 --lora-alpha 16 --target-modules query,value --class-weight --oversample-rare-st1 3`.
Logged to `runs/results_st1_classifiers.csv`, committed (`937c5ae`).

**Follow-up 1 (closed): re-tested capacity + oversample factor on top of `--truncation-side
left`.** Neither previously-discarded lever changes verdict once the model can see the page:
capacity bump (`--lora-r 16 --lora-alpha 32`) still underperforms r8/a16 (dev=0.630/test=0.516,
test none_f1=0.000 — a collapse) and `--oversample-rare-st1 2` still doesn't beat the standing
`3` (dev=0.612/test=0.541, test none_f1=0.182 vs `3`'s 0.222-0.316). Both discarded again —
confirms the inverted-U capacity finding and the oversample-factor-doesn't-matter finding are
independent of the truncation fix, not artifacts of it.

**Follow-up 2 (closed, negative result): token-budgeted context split does NOT beat plain
left-truncation.** Diagnostic found that even `--truncation-side left` still loses PAGE's own
START (product title/category) for 42%% of instances, when the PAGE block alone exceeds the
remaining ~510-token budget. Built `--page-token-budget N` (reserves N tokens for PAGE
specifically, kept from PAGE's start; gives the rest to the transcript+metadata prefix, kept
from the prefix's end) — verified correct via a standalone decode check before running. Tried
N=300 (dev=0.578/test=0.560) and N=400 (dev=0.616/test=0.558): both land BELOW the plain
left-truncation baseline's dev range (0.622-0.645, the cleaner/more trustworthy signal) despite
a marginal test-side edge that's within this task's established noise band. Likely cause: the
fixed split forces prefix truncation on every instance regardless of need, while plain
whole-string left-truncation only truncates when an instance actually exceeds 512 tokens (many
don't). **Standing config is confirmed as plain `--truncation-side left`, no
`--page-token-budget`** — the flag exists in the script (harmless, opt-in, default `None`) but
isn't recommended. This closes out the truncation investigation thread.

Prior state (superseded by the above): the hyperparameter sweep on the roberta-base 5-way st1 classifier
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

**Follow-up: `--oversample-rare-st1` factor sweep (2 vs 5, vs standing 3) — initial lead did
NOT replicate.** Ran 2026-08-17 ~21:32-21:40, fresh splits, r8/a16/single-LR held fixed:
- `--oversample-rare-st1 2`, run 1: dev=0.580 (none=0.500), test macro_f1=0.568/none_f1=0.400 —
  looked like it beat the oversample=3 baseline. **Replicate (fresh split) came back
  test macro_f1=0.532/none_f1=0.160** — a big swing on none specifically (same
  rotating-test-holdout small-none-count noise flagged elsewhere). Averaged across both
  replicates (0.568, 0.532), oversample=2 lands in the SAME band as oversample=3's replicates
  (0.559, 0.553) — **not a confirmed win, do not promote.**
- `--oversample-rare-st1 5`: dev=0.553, test macro_f1=0.525/none_f1=0.296 — below baseline,
  discarded, no replicate needed (clear single-direction regression).

Logged to `runs/results_st1_classifiers.csv` (rows 8-10) and `runs/runs.log`, committed
(`effde85`, `adeceaf`). **Standing default remains `--oversample-rare-st1 3` (unreplaced) —
oversample factor is a closed question for now, all three values tried land in the same noisy
band once replicated.**

**Follow-up 2: new `--undersample-majority-st1` lever + before/after order ablation — clean
negative result, standing default UNCHANGED.** User asked to try undersampling the majority
classes (`digital_content_or_services`, `physical_goods`) instead of/alongside oversampling the
rare ones. Added `undersample_majority()` + `--undersample-majority-st1 FACTOR` to
`lora_train_st1_classifier.py` (drops majority-label instances to 1/FACTOR, same 5% rare/majority
split point as `oversample_rare`), plus `--oversample-first` to control which of the two levers
runs first when combined (default: undersample first, matching the order already tested).
Smoke-tested on GPU (CPU smoke-testing hung past 120s on a full training step — use GPU for this
script's smoke tests going forward, not CPU). Four fresh-split runs, r8/a16/class-weight held
fixed:
| config | dev macro_f1 | dev none_f1 | test macro_f1 | test none_f1 |
|---|---|---|---|---|
| undersample=2 alone | 0.574 | 0.378 | 0.476 | 0.214 |
| undersample=3 alone | 0.518 | 0.316 | 0.521 | 0.222 |
| undersample=2 + oversample=3, undersample-first | 0.542 | 0.340 | 0.474 | 0.190 |
| undersample=2 + oversample=3, oversample-first | 0.567 | 0.400 | 0.515 | 0.143 |

**All four land below the oversample-only baseline** (test macro_f1 0.553-0.559) — shrinking
majority-class training data is a net loss even though it nominally rebalances the label ratio,
since majority classes count equally toward macro F1. Order DOES have a real, mechanistic effect
when combining both levers (confirmed, not noise): oversampling first means `none` gets tripled
before the majority-threshold check runs, so `none` itself crosses 5% and gets swept into the
undersample step too — oversample-first wins on macro F1 (+0.025 dev, +0.041 test) but loses on
test none_f1 (0.143 vs 0.190), i.e. the macro gain comes from the majority classes, not the rare
one either order was meant to help. **Conclusion: don't use `--undersample-majority-st1` for this
classifier, either alone or combined, in either order.** Logged to
`runs/results_st1_classifiers.csv` (rows 11-14), committed. Standing default remains
`--class-weight --oversample-rare-st1 3`, no undersampling.

**Multi-agent coordination note**: 2+ peer Claude Code sessions were confirmed active on this
same repo/branch during this round (via `ListAgents`) — one caused a real output-dir collision
(`runs/st1-classifier-roberta-undersample2`, two processes writing the same `best/` checkpoint
simultaneously; resolved when the peer killed their own duplicate after I flagged it, no
corruption). Divided the remaining queue by direct message to avoid further collisions: **this
session covers the oversample/undersample lever space on `lora_train_st1_classifier.py`; the
peer session ("Pick up handoff documentation") is taking `last_layer_train.py`'s `--st1-only`
baseline and the legal-bert LR retune** (items 1 and 3 below) — check `ListAgents` /
message that peer before starting either of those to avoid duplicate work.

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
4. **CONFIRMED (see coordination note above): 2+ peer sessions are active as of 2026-08-17
   ~22:00.** Items 1 and 3 above are claimed by peer "Pick up handoff documentation" — don't
   start them without checking `ListAgents`/messaging first. Item 2 (hyperparameter sweep) is
   substantially done as of this update (r16a32, head-lr=1e-3, oversample factor 2/3/5,
   undersample-majority factor 2/3, undersample+oversample order ablation — all tried, all
   discarded or inconclusive except the standing oversample=3-only default). Remaining
   unexplored angles if this track continues: `--lora-dropout` sweep, alternate
   `--target-modules` (e.g. adding key/dense to query,value), or accept the current standing
   config as final and move to `last_layer_train.py`/legal-bert once the peer's results land.

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
