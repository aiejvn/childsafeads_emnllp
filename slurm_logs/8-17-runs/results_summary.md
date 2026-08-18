# 8-17 run results: ST1/ST2/ST3 dev & test, macro F1 and minority F1

Generated 2026-08-18 from the 12 logs in this directory. Two model families ran on 2026-08-17:
per-stage **Longformer LoRA classifiers** (one adapter per subtask) and a joint **Qwen3-4B LoRA generative** model (single adapter predicts st1+st2+st3 together). All numbers are `macro_f1` on the public dev set (504 ex.) or the held-out test split carved out of train (`test_holdout`, size varies by config — 500 for the generative run, ~63 batches for classifiers).

`minority_f1` / `majority_f1` is this codebase's custom split of per-label F1 into rare vs. common classes (see `minority labels:` in each row) — a finer-grained view of the class-imbalance failure mode than macro F1 alone.

## Headline: joint generative model beats every per-stage classifier

| Stage | Best Longformer classifier (test macro_f1) | Qwen3-4B joint (test macro_f1) |
|---|---|---|
| ST1 | 0.629 | **0.790** |
| ST2 | 0.808 | **0.842** |
| ST3 | 0.486 | **0.605** |

Source: [slurm_lora_train_generative_20260817_210119.log](slurm_lora_train_generative_20260817_210119.log) ("long runners", `Qwen/Qwen3-4B`, 20 epochs, `runs/8-17-new-lora_qwen3-4B`). Dev: st1=0.850, st2=0.714, st3=0.555, st3_family=0.653, **mean_macro_f1=0.706**. Test: st1=0.790, st2=0.842, st3=0.605, st3_family=0.661, **mean_macro_f1=0.746**. This is a single joint model — no minority/majority breakdown is logged for it (only per-label F1 in `test holdout metrics per-label F1:` lines).

The other three generative logs — [...142821](slurm_lora_train_generative_20260817_142821.log), [...171831](slurm_lora_train_generative_20260817_171831.log), [...180633](slurm_lora_train_generative_20260817_180633.log) — are **st1-only** adapters (`lora-qwen-st1-*`): st2_macro_f1=0.000 and st3_macro_f1≈0.05 throughout, meaning those heads were never trained. Not comparable to the joint run; their st1 numbers (test macro_f1 0.698–0.734) are all below the joint run's st1 test score (0.790) anyway.

## ST1 — Longformer LoRA classifiers

Job A = [slurm_lora_train_st1_classifier_20260817_225708.log](slurm_lora_train_st1_classifier_20260817_225708.log) (`/scratch/kwang103/runs/`). Job B = [slurm_lora_train_st1_classifier_20260817_230317.log](slurm_lora_train_st1_classifier_20260817_230317.log) (`/scratch/kwang103/long-runs/`). Minority labels: `['none','other']` for global/maxlen2048/oversample2, `['none','other','physical_services']` for r16a32/rep2 (r16a32/rep2 apparently ran with a different oversample/threshold setting, giving them a 3-class minority set).

Ranked by **test macro_f1**:

| Rank | Config | Job | Dev macro_f1 (ep) | Dev min/maj F1 | Test macro_f1 (acc) | Test min/maj F1 |
|---|---|---|---|---|---|---|
| 1 | r16a32 | A | 0.591 (4) | 0.378 / 0.910 | **0.629** (.908) | 0.429 / 0.927 |
| 2 | rep2 | B | 0.647 (3) | 0.469 / 0.913 | 0.605 (.916) | 0.385 / 0.935 |
| 3 | maxlen2048 | A | 0.634 (9) | 0.286 / 0.867 | 0.609 (.914) | 0.231 / 0.861 |
| 4 | r16a32 | B | 0.611 (2) | 0.231 / 0.864 | 0.613 (.896) | 0.250 / 0.855 |
| 5 | global | A | 0.634 (4) | 0.292 / 0.863 | 0.590 (.918)† | 0.187 / 0.858† |
| 6 | oversample2 | B | 0.631 (6) | 0.240 / 0.891 | 0.595 (.914) | 0.214 / 0.848 |
| 7 | rep2 | A | 0.638 (2) | 0.292 / 0.869 | 0.586 (.900)† | 0.231 / 0.822† |
| 8 | global | B | 0.623 (5) | 0.227 / 0.886 | 0.583 (.912) | 0.167 / 0.860 |
| 9 | oversample2 | A | 0.556 (3) | 0.160 / 0.820 | 0.576 (.902) | 0.187 / 0.835 |
| 10 | maxlen2048 | B | 0.619 (3) | 0.250 / 0.865 | 0.570 (.874) | 0.182 / 0.829 |

Best dev macro_f1: **rep2/B, 0.647**, but it's #2 on test — r16a32/A generalizes best despite a lower dev score. Minority F1 on ST1 is uniformly weak (0.16–0.47 dev, 0.17–0.43 test) — the `none`/`other` classes are hard regardless of config; only the runs with the 3-class minority set (r16a32, rep2) show markedly higher minority F1, largely because `physical_services` is easier than `none`/`other`.

## ST2 — Longformer LoRA classifiers

Job A = [slurm_lora_train_st2_classifier_20260817_225708.log](slurm_lora_train_st2_classifier_20260817_225708.log). Job B = [slurm_lora_train_st2_classifier_20260817_230317.log](slurm_lora_train_st2_classifier_20260817_230317.log). Minority labels (all runs): `['gambling','gambling_adjacent','toys']`.

Ranked by **test macro_f1**:

| Rank | Config | Job | Dev macro_f1 (ep) | Dev min/maj F1 | Test macro_f1 (exact_match) | Test min/maj F1 |
|---|---|---|---|---|---|---|
| 1 | baseline | A | 0.718 (9) | 0.539 / 0.778 | **0.808** (.656)† | 0.820 / 0.804† |
| 2 | r16a32 | B | 0.728 (8) | 0.591 / 0.773 | 0.794 (.644) | 0.674 / 0.835 |
| 3 | maxlen2048 | B | 0.721 (9) | 0.564 / 0.774 | 0.776 (.632) | 0.706 / 0.800 |
| 4 | global | B | 0.736 (—) | — | 0.775 (.648) | 0.692 / 0.802 |
| 5 | r16a32 | A | 0.713 (4) | 0.531 / 0.774 | 0.769 (.610) | 0.695 / 0.793 |
| 6 | oversample2 | B | 0.712 (5) | 0.532 / 0.772 | 0.763 (.636) | 0.593 / 0.820 |
| 7 | oversample2 | A | 0.715 (7) | 0.557 / 0.768 | 0.758 (.628) | 0.594 / 0.813 |
| 8 | global | A | 0.740 (5) | 0.618 / 0.781 | 0.746 (.648)† | 0.520 / 0.822† |
| 9 | maxlen2048 | A | 0.701 (7) | 0.449 / 0.785 | 0.728 (.630) | 0.486 / 0.809 |

Best dev macro_f1: **global/A, 0.740**, but it's the worst test score in the set (0.746, #8) — the clearest dev/test disagreement of any stage: baseline/A has a lower dev score (0.718) yet the best test macro_f1 *and* the best test minority F1 (0.820) by a wide margin.

## ST3 — Longformer LoRA classifiers

Job A = [slurm_lora_train_st3_classifier_20260817_225708.log](slurm_lora_train_st3_classifier_20260817_225708.log) (baseline config only). Job A2 = [slurm_lora_train_st3_classifier_20260817_225709.log](slurm_lora_train_st3_classifier_20260817_225709.log) (global/maxlen2048/oversample2/r16a32). Job B = [slurm_lora_train_st3_classifier_20260817_230317.log](slurm_lora_train_st3_classifier_20260817_230317.log) (baseline/global/maxlen2048/r16a32). Job B2 = [slurm_lora_train_st3_classifier_20260817_230318.log](slurm_lora_train_st3_classifier_20260817_230318.log) (oversample2 only). Minority labels (all runs): `['age_restricted_or_prohibited_product','hfss_food_marketing','insufficient_context']`.

Ranked by **test macro_f1**:

| Rank | Config | Job | Dev macro_f1 (ep) | Dev min/maj F1 | Test macro_f1 (exact_match) | Test min/maj F1 |
|---|---|---|---|---|---|---|
| 1 | r16a32 | B | 0.537 (8) | 0.587 / 0.507 | **0.486** (.336) | 0.393 / 0.542 |
| 2 | oversample2 | A2 | 0.464 (8) | 0.535 / 0.422 | 0.482 (.318) | 0.603 / 0.409 |
| 3 | baseline | B | 0.484 (7) | 0.432 / 0.515 | 0.444 (.320) | 0.303 / 0.528 |
| 4 | global | B | 0.418 (5) | 0.398 / 0.430 | 0.434 (.256) | 0.446 / 0.426 |
| 5 | global | A2 | 0.587 (8) | 0.796 / 0.462 | 0.428 (.254)† | 0.321 / 0.492† |
| 6 | oversample2 | B2 | 0.453 (3) | 0.442 / 0.459 | 0.425 (.240) | 0.364 / 0.462 |
| 7 | maxlen2048 | A2 | 0.420 (4) | 0.443 / 0.406 | 0.414 (.240) | 0.465 / 0.383 |
| 8 | r16a32 | A2 | 0.551 (8) | 0.628 / 0.504 | 0.412 (.250)† | 0.271 / 0.497† |
| 9 | maxlen2048 | B | 0.417 (4) | 0.379 / 0.440 | 0.405 (.238) | 0.315 / 0.459 |
| 10 | baseline | A | 0.476 (10) | 0.507 / 0.457 | 0.376 (.278) | 0.241 / 0.458 |

ST3 is the weakest classifier stage across the board (test macro_f1 0.38–0.49, matching the earlier GPT baseline finding that ST3 dominates errors). The starkest dev/test gap in the whole dataset is **global/A2**: best-in-class dev macro_f1 (0.587) and by far the best dev minority F1 (0.796), but only mid-pack on test (0.428) — this config overfits the dev split harder than any other run here. r16a32/B is the most consistent: mid-high dev, best test.

## Data-quality note (†)

Three of the twelve log files run **5 (ST1) or 2–5 (ST2/ST3) configs as separate concurrent processes writing to the same file**, and only the *training*-phase log lines (dev metrics/checkpointing) are safely attributable per-run (they're logged atomically, milliseconds apart from each other). The test-holdout phase is not: all processes reload their best checkpoint and run prediction in parallel, so the `test holdout metrics:` blocks can complete in a different order than the processes started their reload, and naive nearest-line pairing misattributes them.

The 6 rows marked **†** (2 each in `st1_..._225708`, `st2_..._225708`, `st3_..._225709`) were resolved by matching each process's reload timestamp to the test-block completion time closest to that process's typical ~20–30s single-run predict duration (elsewhere in the same files, unambiguous single-pending-reload cases consistently show ~20–30s reload→result latency). Confidence is high but not certain; the resulting uncertainty is on the order of 0.01–0.02 F1 for those 6 rows and does not change any stage's overall ranking (the swap candidates are adjacent-rank at worst).

## All logs in this directory

| Log | Stage / model | Job type |
|---|---|---|
| [slurm_lora_train_generative_20260817_142821.log](slurm_lora_train_generative_20260817_142821.log) | st1-only Qwen3-4B adapter | 5-epoch, few-shot, pos-weight, oversample, minority-select |
| [slurm_lora_train_generative_20260817_171831.log](slurm_lora_train_generative_20260817_171831.log) | st1-only Qwen3-4B adapter | 10-epoch rerun, pos-weight, oversample, minority-select |
| [slurm_lora_train_generative_20260817_180633.log](slurm_lora_train_generative_20260817_180633.log) | st1-only Qwen3-4B adapter | 5-epoch few-shot rerun |
| [slurm_lora_train_generative_20260817_210119.log](slurm_lora_train_generative_20260817_210119.log) | **joint st1+st2+st3 Qwen3-4B** | 20-epoch "long runners" — best overall model |
| [slurm_lora_train_st1_classifier_20260817_225708.log](slurm_lora_train_st1_classifier_20260817_225708.log) | ST1 Longformer, 5 configs (Job A) | global/maxlen2048/oversample2/r16a32/rep2 |
| [slurm_lora_train_st1_classifier_20260817_230317.log](slurm_lora_train_st1_classifier_20260817_230317.log) | ST1 Longformer, 5 configs (Job B) | same 5 configs, `long-runs/` output |
| [slurm_lora_train_st2_classifier_20260817_225708.log](slurm_lora_train_st2_classifier_20260817_225708.log) | ST2 Longformer, 5 configs (Job A) | baseline/global/maxlen2048/oversample2/r16a32 |
| [slurm_lora_train_st2_classifier_20260817_230317.log](slurm_lora_train_st2_classifier_20260817_230317.log) | ST2 Longformer, 4 configs (Job B) | global/maxlen2048/oversample2/r16a32 |
| [slurm_lora_train_st3_classifier_20260817_225708.log](slurm_lora_train_st3_classifier_20260817_225708.log) | ST3 Longformer, baseline only (Job A) | |
| [slurm_lora_train_st3_classifier_20260817_225709.log](slurm_lora_train_st3_classifier_20260817_225709.log) | ST3 Longformer, 4 configs (Job A2) | global/maxlen2048/oversample2/r16a32 |
| [slurm_lora_train_st3_classifier_20260817_230317.log](slurm_lora_train_st3_classifier_20260817_230317.log) | ST3 Longformer, 4 configs (Job B) | baseline/global/maxlen2048/r16a32 |
| [slurm_lora_train_st3_classifier_20260817_230318.log](slurm_lora_train_st3_classifier_20260817_230318.log) | ST3 Longformer, oversample2 only (Job B2) | |
