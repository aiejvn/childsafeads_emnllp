# Results summary by category

Best `mean_macro_f1` per approach on the 504-example public dev set, unless noted otherwise. Generated 2026-08-10 from logs/checkpoints under `runs/`.

| Category | Best config | mean_macro_f1 | st1 / st2 / st3 / st3_fam | Where |
|---|---|---|---|---|
| **GPT-5.4 zero/few-shot (v0 baseline prompt)** | full context, no RAG | **0.641** | 0.716 / 0.716 / 0.493 / 0.625 | [run_20260801_205209...log](run_20260801_205209_full_gpt-5.4.log) |
| **GPT-5.4 + agentic RAG** | full context | 0.637 | 0.723 / 0.726 / 0.463 / 0.616 | [run_20260802_004514...log](run_20260802_004514_agentic_rag_full_gpt-5.4.log) |
| **GPT-5.4 tuned prompt (v5, currently live)** | full context, post prompt-tuning loop | 0.579 | 0.605 / 0.708 / 0.422 / 0.585 | [run_20260803_202246...log](run_20260803_202246_full_gpt-5.4.log) |
| **RoBERTa last-layer tuning** (partial unfreeze, no LoRA) | 200 epochs, tuned thresholds | **0.618** | 0.587 / 0.635 / 0.513 / 0.621 | [runs/last_layer_roberta/best](last_layer_roberta/best) |
| **LoRA RoBERTa — exp02 (standing default)** | r=64, target=q,k,v,dense (adapts FFN too), pos-weight | **0.613** | 0.676 / 0.659 / 0.503 / 0.556 | [runs/lora_exp02_r64broad/best](lora_exp02_r64broad/best) |
| LoRA RoBERTa — exp03 (attn-only ablation, discarded) | r=64, q,k,v + attn.output.dense only | 0.588 | 0.620 / 0.653 / 0.494 / 0.592 | [runs/lora_exp03_attnonly](lora_exp03_attnonly) |
| LoRA RoBERTa — exp01 (pos-weight ablation) | r=256, q,v, +pos-weight | 0.574 | 0.615 / 0.636 / 0.470 / 0.534 | [runs/lora_exp01_posweight](lora_exp01_posweight) |
| LoRA RoBERTa — baseline defaults | r=256, q,v, no pos-weight | 0.567 | 0.637 / 0.605 / 0.460 / 0.526 | [runs/lora_roberta/best](lora_roberta/best) (checkpoint on disk is stale, see notes) |
| **LoRA LegalBERT** | r=256, q,v, 200 epochs | 0.536 | — | log only; **checkpoint on disk is overwritten, see notes** |
| **GreaseLM (GNN + KG, combined KG)** | 200 epochs, sample_size=300 (subsampled train/dev, not full 504) | 0.489 | ~0.62-0.67 / ~0.41 / ~0.23 / ~0.41 (noisy across epochs) | [run_20260809_202020...log](run_20260809_202020_greaselm_train_combined.log) — hub-assignment concern, still unvalidated |
| ⏳ LoRA RoBERTa — exp04 (r=32) | in progress | — | — | [run_20260810_133403...log](run_20260810_133403_lora_train_FacebookAI_roberta-base.log), epoch 1/10 running as of writing |

## Notes / caveats

1. **`runs/lora_legalbert/best` and `/last` are stale/wrong on disk.** The good LegalBERT run (200 epochs, 0.536) finished 2026-08-08, but a later run on 2026-08-10 (with an autoDF-prepended prompt, only 5 epochs) wrote to the same `output_dir` and overwrote it with a much worse checkpoint (best 0.125). That run isn't in `results.tsv` and doesn't show up in `git status` as modified — it looks like an uncommitted local overwrite of a previously-committed good checkpoint (commit `fdd5255 Legalbert run`). The 0.536 weights may be recoverable from git history.
2. **GreaseLM's 0.489 isn't apples-to-apples** — it trained/evaluated on a 300-example subsample of train and dev, not the full 2353/504 split the LoRA and last-layer runs use, so direct ranking against the others is soft (matches the existing KG hub-assignment concern).
3. GPT-5.4 full-dev numbers exclude smoke-test/small-batch runs in `runs/run_2026*_full_gpt-5.4.log` that scored on 10-100 examples instead of the full 504 (e.g. the 0.845 outlier was a 10-example batch).
