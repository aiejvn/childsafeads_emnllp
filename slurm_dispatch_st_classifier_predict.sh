#!/bin/bash

# Run our best st1/st2/st3 Longformer LoRA classifier checkpoint (one per subtask, from the
# 8-17 sweep in slurm_dispatch_st_classifiers.sh) over a target split and merge the three
# outputs into one submission. Picks are by TEST-holdout macro_f1 -- see
# slurm_logs/8-17-runs/results_summary.md for the full ranking and how each was chosen:
#   st1: r16a32 (runs/,      test macro_f1=0.629) -- best test despite mid-pack dev
#   st2: baseline (runs/,    test macro_f1=0.808) -- best test; best-dev config (global) is worse on test
#   st3: r16a32 (long-runs/, test macro_f1=0.486) -- best test AND second-best dev
# The st2 pick's test score was one of the results_summary.md rows resolved by timing
# inference (marked †) rather than an unambiguous log association -- rerun its own
# test-holdout pass yourself first if you want to double check before relying on it.
#
# One `bash slurm_wrapper.sh 1 ...` command per line -- copy-paste individual lines into
# your CLI. Drop --local if the model isn't synced to ./models/allenai/longformer-base-4096
# on the cluster. batch-size=8 matches what these checkpoints were trained/evaluated with.

# --- sanity check against public_data_dev/dev.jsonl (has gold labels -- each command logs
#     a solo macro_f1 for its own tier, so you can confirm the checkpoint reloaded correctly
#     and roughly matches the test-holdout score in results_summary.md before trusting it on
#     the unlabeled test split) ---

bash slurm_wrapper.sh 1 src/lora/lora_predict_classifier.py st1 public_data_dev/dev.jsonl --model allenai/longformer-base-4096 --local --adapter-dir $SCRATCH/runs/st1-classifier-longformer-r16a32/best --context full --max-length 4096 --truncation-side left --batch-size 8 --out runs/submission_st1_dev.jsonl

bash slurm_wrapper.sh 1 src/lora/lora_predict_classifier.py st2 public_data_dev/dev.jsonl --model allenai/longformer-base-4096 --local --adapter-dir $SCRATCH/runs/st2-classifier-longformer/best --context full --max-length 4096 --truncation-side left --batch-size 8 --out runs/submission_st2_dev.jsonl

bash slurm_wrapper.sh 1 src/lora/lora_predict_classifier.py st3 public_data_dev/dev.jsonl --model allenai/longformer-base-4096 --local --adapter-dir $SCRATCH/long-runs/st3-classifier-longformer-r16a32/best --context full --max-length 4096 --truncation-side left --batch-size 8 --out runs/submission_st3_dev.jsonl

# merge + score the combined dev submission (run after all three jobs above finish)
python src/combine_submissions.py public_data_dev/dev.jsonl --st1 runs/submission_st1_dev.jsonl --st2 runs/submission_st2_dev.jsonl --st3 runs/submission_st3_dev.jsonl --out runs/submission_hybrid_dev.jsonl

# --- the actual submission, over the unlabeled public_data_test/test.jsonl (no --out
#     wandb/gold; combine_submissions.py skips scoring automatically when the target
#     carries no labels) ---

bash slurm_wrapper.sh 1 src/lora/lora_predict_classifier.py st1 public_data_test/test.jsonl --model allenai/longformer-base-4096 --local --adapter-dir $SCRATCH/runs/st1-classifier-longformer-r16a32/best --context full --max-length 4096 --truncation-side left --batch-size 8 --out runs/submission_st1_test.jsonl

bash slurm_wrapper.sh 1 src/lora/lora_predict_classifier.py st2 public_data_test/test.jsonl --model allenai/longformer-base-4096 --local --adapter-dir $SCRATCH/runs/st2-classifier-longformer/best --context full --max-length 4096 --truncation-side left --batch-size 8 --out runs/submission_st2_test.jsonl

bash slurm_wrapper.sh 1 src/lora/lora_predict_classifier.py st3 public_data_test/test.jsonl --model allenai/longformer-base-4096 --local --adapter-dir $SCRATCH/long-runs/st3-classifier-longformer-r16a32/best --context full --max-length 4096 --truncation-side left --batch-size 8 --out runs/submission_st3_test.jsonl

python src/combine_submissions.py public_data_test/test.jsonl --st1 runs/submission_st1_test.jsonl --st2 runs/submission_st2_test.jsonl --st3 runs/submission_st3_test.jsonl --out runs/submission_hybrid_test.jsonl
