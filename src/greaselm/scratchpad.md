# GreaseLM implementation — autonomous session log

Working unattended for ~3-5h. Goal: finish the GreaseLM port, verify it, then launch a
200-epoch baseline training run. Concise, append-only log of decisions/reasoning as I go
(not a design doc — see `/home/k6/.claude/plans/parallel-juggling-rabin.md` for that).

## State at session start

Already built & smoke-tested (previous session): `graph_schema.py`, `kg/build_kg.py`
(legal/flow/combined graphs on disk), `modeling/modeling_gnn.py` (GATConvE),
`modeling/modeling_greaselm.py` (GreaseLMGNNLayers/GreaseLMTextKGEncoder/LMGNN),
n_ntype=4 QA-shaped design (one LMGNN forward per candidate label). Not yet built:
`kg_embeddings.py`, `greaselm_model.py` (the batching/orchestration layer),
`greaselm_smoke.py`, any training script.

Environment check: CUDA available, RTX 4060 8.6GB. train.jsonl=2353, dev.jsonl=504.

## Decisions made this session

**kg_embeddings.py scope-cut**: dropped the disk-caching wrapper
(`load_or_train_transe`) I'd drafted last session. Reasoning: `greaselm_model.py` needs
to mint isolated placeholder nodes for candidate labels missing from a given KG variant
(see next point) *before* embedding training, so the trained table depends on
model-construction-time graph state, not just the on-disk JSON — an mtime-keyed cache
would silently go stale. Our graphs are tens of nodes; TransE training is sub-second.
Not worth the staleness risk. Just `train_transe(graph, dim, epochs, ...) -> Tensor`,
called fresh in `GreaseLMForClassification.__init__`.

**Missing candidate nodes across KG variants**: the QA-shaped design needs, for every
ST1/ST2/ST3 candidate label, some node in the graph to mark `node_type=1` (answer-entity)
and read a concept embedding from. Only the *combined* graph mints `st1_label:*`/
`st2_label:*` nodes and links to `st3_flag:*`; the *legal* graph only has `st3_flag:*`
(so st1/st2 candidates have nothing); the *flow* graph has no label nodes at all. Rather
than special-case this per kg_mode, `greaselm_model.py` mints any missing candidate node
as an isolated node (no edges but the GATConvE self-loop) on a deep copy of the loaded
graph at construction time. This makes all three kg_modes structurally runnable with
identical code, and turns "legal-only"/"flow-only" into an honest ablation: those modes
still get *some* real graph signal for the label types they do cover (st3 under legal;
none under flow-only beyond the reasoning skeleton), everything else degrades gracefully
to "LM + isolated node embedding", never crashes. Documented in
`greaselm_model.py`'s docstring, not just here.

**Context node has no graph edges**: matches `LMGNN`'s own convention (row 0 of node
features gets zeroed every forward pass; the interaction only happens via MInt, not
message passing) — node 0 keeps only the self-loop GATConvE already adds unconditionally
to every node. Not adding synthetic context-to-everything edges.

**Candidate framing as text pairs**: tokenize `(full_context(instance), label.replace('_',
' '))` as a sentence pair (tokenizer's native two-segment encoding), not a hand-written
question template per subtask. Cheap and consistent; a fancier per-subtask question
string (mirroring the dialog-flow's actual `config.question` text) is a reasonable
follow-up but not required for a first correctness pass.

**"mentioned in text" (node_type=0) heuristic**: case-insensitive substring match of each
non-candidate node's `label` against the instance's `full_context` text. Same
lightweight stand-in for entity-linking already agreed in the plan.

## Built: kg_embeddings.py, greaselm_model.py, greaselm_smoke.py

`GreaseLMForClassification` (greaselm_model.py): loads+mints the graph, trains TransE
concept embeddings, wraps `LMGNN`. `forward_subtask(texts, subtask)` tokenizes each
(instance, candidate) pair, builds per-row node_type_ids (candidate node -> type 1,
text-substring matches -> type 0, else 2, context -> 3), batches edge_index like
`GreaseLM.batch_graph`, returns `[bs, num_candidates]` logits. `forward()` runs all
three subtasks and composes CE (st1) + BCE (st2) + BCE (st3) loss, same composition as
`MultiTaskEncoder`. Barrel `__init__.py` now also exports `GreaseLMForClassification`.

**Found a real memory-budget issue, not a code bug**: this box has only 7.6GB RAM (WSL2)
with swap already full, separate from the RTX 4060's 8.6GB VRAM. CPU forward+backward
through even one subtask (roberta-base, 10 rows, seqlen~256) OOM-killed the process
(confirmed via `dmesg`: oom-kill, anon-rss 5GB). Isolated it precisely: a bare
`AutoModel` layer-by-layer forward+backward (same calling convention `GreaseLMGNNLayers`
uses) grows ~230MB of peak RSS *per layer* under grad tracking vs ~10-30MB/layer under
`no_grad` -- this matches normal eager-attention training memory scaling (SDPA's
memory-efficient kernel path isn't reachable here since we drive `RobertaLayer` directly
with a dense additive float mask instead of through `RobertaEncoder`'s normal
boolean-mask path), it's just more than 7.6GB can hold across 12 layers x 25 candidates.
**Conclusion: CPU is not viable for this model on this box even for smoke tests -- always
`--device cuda`.** All three kg_modes (legal/flow/combined) smoke-tested clean on GPU:
loss finite, every GATConvE/MInt/pooler/fc/emb_node_type/emb_score parameter gets a
real gradient, `concept_emb.emb` correctly shows no gradient (frozen by design).

## Built: greaselm_train.py

Standalone train/eval loop (own Dataset -- raw texts, not pre-tokenized, since GreaseLM
tokenizes per-candidate inside the model). Reuses `common/predict_utils.py`'s threshold
tuning/decode/post-processing (generic over any st1/st2/st3-logit model) and
`common/train_utils.py`'s `compute_pos_weight`. Freezes all but the last
`--num-unfrozen-layers` LM blocks by default (see module docstring: with n_ntype=4
per-candidate scoring, one training instance = 25 LMGNN forward passes, so
full-finetuning 12 blocks isn't tractable here -- a tractability decision, not a claim
it's the right long-run recipe). Saves a "last" checkpoint at every eval point (not just
at the very end), so an interrupted multi-hour unattended run always has a recoverable
checkpoint.

## Sizing the baseline run to the compute budget

Timed real steps on GPU (RTX 4060) before committing to a config: combined KG, bs=4,
num_unfrozen_layers=2 -> ~1.0s/step steady-state, ~3.7GB peak VRAM (bs=8 -> ~1.9s/step,
~6.6GB peak -- roughly linear, i.e. this workload is compute-bound, not overhead-bound,
so batch size barely changes total wall-clock for a fixed instance count x epoch count).

Full dataset (2353 train) x 200 epochs x ~1s/step at bs=4 -> 2353/4=588 steps/epoch x
200 = 117,600 steps -> **~32 hours**. Not remotely close to the 3-5h budget, regardless
of batch size (confirmed via the bs=8 timing above scaling the same way). Rather than
silently cut epochs (which the user explicitly asked for -- "200 epoch run") or silently
cut something else without saying so, cut the *dataset size* instead: seeded sample of
300 train / 300 dev (`--sample-size 300`, same seed=42 samples both splits -- dev ended
up equal to train size as a side effect of reusing one flag for both, not deliberately
chosen; a real ablation run later should decouple them). 300 instances is enough to
exercise every component of the architecture and produce a real learning curve over 200
epochs (small-sample regimes generally benefit from *more* epochs, so 200 is actually a
reasonable match for this sample size, not just "the biggest N that fits").

Estimated total: 300/4=75 steps/epoch x 200 x ~1.0s = ~4.2h training + dev eval every 5
epochs (75 steps/eval, forward-only so faster than a train step, x 40 evals) ~= 0.5h ->
**~4.7h total**, landing inside the stated 3-5h window (upper-middle, not lower). If
still running when the user returns, checkpoints in runs/greaselm_baseline_combined/last
are current as of the most recent eval (every 5 epochs), never more than ~19min stale.

**kg_mode=combined** chosen as the single baseline (not legal/flow) because it's the
only variant where every ST1/ST2/ST3 candidate gets a real, non-isolated graph node
(see the missing-candidate-node note above) -- the most faithful test of whether the
GNN mechanism helps at all. legal-only and flow-only runs are natural follow-ups with
the same script (`--kg-mode legal` / `--kg-mode flow`), not run tonight due to time.

Launched: `python src/greaselm/greaselm_train.py public_data_dev/train.jsonl
public_data_dev/dev.jsonl --kg-mode combined --sample-size 300 --epochs 200
--batch-size 4 --num-unfrozen-layers 2 --eval-every 5 --lr 2e-5 --device cuda --no-wandb
--output-dir runs/greaselm_baseline_combined`, in background, log at
`src/greaselm/baseline_run.log` (also duplicated to `runs/run_<timestamp>_greaselm_train_combined.log`
by `setup_logging`, matching every other training script's convention).

Confirmed healthy ~40s after launch: steady 1.02-1.04s/step, matching the timing test
exactly. First `epoch 1` still in progress at that check. Everything from here on is
just waiting -- no more open implementation questions. Will append final dev metrics
(mean_macro_f1 and the st1/st2/st3/st3_family breakdown) below once training finishes
or once I next check in.

## Status: DONE -- implementation complete, baseline run finished clean

Files on disk: `graph_schema.py`, `kg/build_kg.py` (+3 output JSONs), `kg_embeddings.py`,
`modeling/modeling_gnn.py`, `modeling/modeling_greaselm.py`, `greaselm_model.py`,
`greaselm_smoke.py`, `greaselm_train.py`, `__init__.py` barrel. All smoke-tested on GPU
for all 3 kg_modes. No predict.py / harness integration built (out of scope per the
plan, not requested this session either).

## Baseline run results (combined KG, 300-instance sample, 200 epochs)

Ran 2026-08-09 20:20 -> 2026-08-10 01:15 (~4h55m, matching the ~4.7h estimate), exit
code 0, no errors. Full per-eval history in
`runs/run_20260809_202020_greaselm_train_combined.log`; checkpoints + tuned
thresholds in `runs/greaselm_baseline_combined/{best,last}/`.

**Best: epoch 75, mean_macro_f1=0.489** (st1=0.671, st2=0.450, st3=0.346,
st3_family=0.491) -- this is what's saved to `.../best`.

Shape of the curve, worth knowing before reading anything into the number: loss/F1
climbed fairly steadily through ~epoch 75, then mean_macro_f1 oscillated in the
0.40-0.45 band for the remaining 125 epochs without a clear further upward trend
(epoch 200 final = 0.419, close to but below the epoch-75 peak). Reads as this small
(300-instance) sample saturating/overfitting well before epoch 200, not as a broken
run -- st1 in particular bounces between ~0.44 and ~0.68 epoch-to-epoch in the back
half, consistent with a small, fixed dev-eval sample rather than genuine instability
in what's learned. Not a claim that combined-KG GreaseLM is "worth ~0.49 macro F1" in
any general sense -- this is one seeded 300/300 train/dev subsample, one kg_mode, no
hyperparameter search. It's a first correctness+signal check, exactly the scope asked
for tonight.

## Natural next steps (not done, flagging for follow-up)

- Same run for `--kg-mode legal` and `--kg-mode flow`, for the actual 3-way ablation
  ("we will ablate" -- this session only ran combined, due to time).
- Full train/dev split instead of the 300-sample subsample (full-dataset x 200 epochs
  measured at ~32h on this GPU -- would need either far fewer epochs, a much longer
  time budget, or both).
- No predict.py/submission-format script exists yet for GreaseLM checkpoints (last_layer/lora
  each have one) -- would be needed to actually score this against the real eval pipeline.
- decoupling train/dev `--sample-size` in greaselm_train.py (currently one flag sizes
  both, which is why dev landed at 300 instead of something smaller/faster to eval).
