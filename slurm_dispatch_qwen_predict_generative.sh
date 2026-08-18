#!/bin/bash

# lora_predict_generative.py follow-ups to slurm_dispatch_qwen_generative.sh's 8-18 sweep --
# runs each of the 6 trained adapters there over the unlabeled public_data_test/test.jsonl
# (no gold labels -- each command logs "target has no gold labels -- skipping evaluation").
# One `bash slurm_wrapper.sh 1 ...` command per line -- copy-paste individual lines into
# your CLI, once the matching training run's <checkpoint-save-path>/best exists.
#
# --model/--lean-prompt/--df-path must match training (all 6 runs used the same three), so
# they're identical across every line below; only --adapter-dir and --out vary. --batch-size
# 16 matches the 8-18 predict run of the prior (8-17) adapter
# (slurm_logs/8-17-runs/slurm_lora_predict_generative_20260818_111234.log).

# 1. eval-cadence control
bash slurm_wrapper.sh 1 src/lora/lora_predict_generative.py public_data_test/test.jsonl --model Qwen/Qwen3-4B --lean-prompt --df-path emnllp-dialog-flow-dialog-flow.json --batch-size 16 --adapter-dir $SCRATCH/8-18-qwen-improve/qwen3-4B-evalevery2/best --out runs/submission-8-18-qwen-improve-evalevery2.jsonl

# 2. oversample-rare-st3 3
bash slurm_wrapper.sh 1 src/lora/lora_predict_generative.py public_data_test/test.jsonl --model Qwen/Qwen3-4B --lean-prompt --df-path emnllp-dialog-flow-dialog-flow.json --batch-size 16 --adapter-dir $SCRATCH/8-18-qwen-improve/qwen3-4B-oversample-st3-3/best --out runs/submission-8-18-qwen-improve-oversample-st3-3.jsonl

# 3. grad-accum 8
bash slurm_wrapper.sh 1 src/lora/lora_predict_generative.py public_data_test/test.jsonl --model Qwen/Qwen3-4B --lean-prompt --df-path emnllp-dialog-flow-dialog-flow.json --batch-size 16 --adapter-dir $SCRATCH/8-18-qwen-improve/qwen3-4B-gradaccum8/best --out runs/submission-8-18-qwen-improve-gradaccum8.jsonl

# 4. lower LR + more LoRA dropout
bash slurm_wrapper.sh 1 src/lora/lora_predict_generative.py public_data_test/test.jsonl --model Qwen/Qwen3-4B --lean-prompt --df-path emnllp-dialog-flow-dialog-flow.json --batch-size 16 --adapter-dir $SCRATCH/8-18-qwen-improve/qwen3-4B-lr1e-4-dropout0.2/best --out runs/submission-8-18-qwen-improve-lr1e-4-dropout0.2.jsonl

# 5. st3-loss-weight 2x + oversample-rare-st3 3
bash slurm_wrapper.sh 1 src/lora/lora_predict_generative.py public_data_test/test.jsonl --model Qwen/Qwen3-4B --lean-prompt --df-path emnllp-dialog-flow-dialog-flow.json --batch-size 16 --adapter-dir $SCRATCH/8-18-qwen-improve/qwen3-4B-st3weight2-oversample3/best --out runs/submission-8-18-qwen-improve-st3weight2-oversample3.jsonl

# 6. combined best-guess
bash slurm_wrapper.sh 1 src/lora/lora_predict_generative.py public_data_test/test.jsonl --model Qwen/Qwen3-4B --lean-prompt --df-path emnllp-dialog-flow-dialog-flow.json --batch-size 16 --adapter-dir $SCRATCH/8-18-qwen-improve/qwen3-4B-combined/best --out runs/submission-8-18-qwen-improve-combined.jsonl
