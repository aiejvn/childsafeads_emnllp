#!/bin/bash

# Post-training (predict-side only -- no retraining) follow-ups to the 8-18
# --oversample-rare-st3/--grad-accum-steps/--lr sweep in slurm_dispatch_qwen_generative.sh.
# All three scripts here only run inference (model.generate()) against checkpoints that
# already exist under $SCRATCH/8-18-qwen-improve/<name>/best -- none of them touch
# lora_train_generative.py or start a new fine-tune. One `bash slurm_wrapper.sh 1 ...`
# command per line -- copy-paste individual lines into your CLI.
#
# Recommended order: 1 (soup) first -- cheapest, reuses checkpoints you already have, and its
# output is a single merged adapter you can hand straight to lora_predict_generative.py like
# any other checkpoint. Then 2 (self-consistency) on whichever single checkpoint currently
# looks best (soup or the plain oversample-st3-3 winner) to see if it fixes the fragile st3
# labels without regressing anything else. 3 (threshold calibration) is the most expensive of
# the three (a full k-sample pass over all of dev.jsonl, not just a fragile-label subset) --
# only worth running once you've settled on which single checkpoint you're shipping, since its
# output (thresholds.json) is meant to be reused by --thresholds-dir on every future predict
# run against that checkpoint, not regenerated per submission.
#
# Every line validates against public_data_dev/dev.jsonl (dev has gold labels, so each script
# logs a real solo/before-after/tune-vs-check score) -- do not trust any of these outputs on
# the unlabeled public_data_test/test.jsonl until the dev-side run shows an improvement over
# the plain single-checkpoint baseline.

# 1. Greedy soup over all six 8-18 checkpoints -- ranks each by its own dev score, then only
#    folds a candidate into the merge if the trial average doesn't drop the running score.
#    Re-scores the saved-to-disk adapter at the end so what's on disk is confirmed to match
#    what was validated.
bash slurm_wrapper.sh 1 src/lora/lora_soup_generative.py public_data_dev/dev.jsonl --model Qwen/Qwen3-4B --lean-prompt --df-path emnllp-dialog-flow-dialog-flow.json --batch-size 16 --candidate $SCRATCH/8-18-qwen-improve/qwen3-4B-evalevery2/best --candidate $SCRATCH/8-18-qwen-improve/qwen3-4B-oversample-st3-3/best --candidate $SCRATCH/8-18-qwen-improve/qwen3-4B-gradaccum8/best --candidate $SCRATCH/8-18-qwen-improve/qwen3-4B-lr1e-4-dropout0.2/best --candidate $SCRATCH/8-18-qwen-improve/qwen3-4B-st3weight2-oversample3/best --candidate $SCRATCH/8-18-qwen-improve/qwen3-4B-combined/best --out $SCRATCH/8-18-qwen-improve/soup-greedy

# 2a. Selective self-consistency on the oversample-st3-3 checkpoint (the one that won st1/st2
#    in the hybrid submission) against dev, to see whether it actually helps the fragile st3
#    labels or drags them down (see the escalated-subset before/after log lines).
bash slurm_wrapper.sh 1 src/lora/lora_predict_generative_selfconsistent.py public_data_dev/dev.jsonl --model Qwen/Qwen3-4B --lean-prompt --df-path emnllp-dialog-flow-dialog-flow.json --batch-size 16 --adapter-dir $SCRATCH/8-18-qwen-improve/qwen3-4B-oversample-st3-3/best --k 5 --temperature 0.7 --out runs/submission_selfconsistent_oversample-st3-3_dev.jsonl

# 2b. Same, on the greedy-soup checkpoint from #1 (run after #1 finishes) -- compare its
#    escalated-subset score against 2a's before deciding which single checkpoint to ship.
bash slurm_wrapper.sh 1 src/lora/lora_predict_generative_selfconsistent.py public_data_dev/dev.jsonl --model Qwen/Qwen3-4B --lean-prompt --df-path emnllp-dialog-flow-dialog-flow.json --batch-size 16 --adapter-dir $SCRATCH/8-18-qwen-improve/soup-greedy --k 5 --temperature 0.7 --out runs/submission_selfconsistent_soup_dev.jsonl

# 3. Per-label threshold calibration on whichever checkpoint wins #1/#2 -- expensive (full
#    k-sample pass over all of dev.jsonl to get a per-label vote-frequency "probability" for
#    every st2/st3 label, not just the fragile subset), so run once and reuse the resulting
#    thresholds.json via --thresholds-dir on every future predict call against this
#    checkpoint, rather than re-running this per submission. Writes thresholds.json straight
#    into the checkpoint dir (--out) so --thresholds-dir can point at the same path.
bash slurm_wrapper.sh 1 src/lora/lora_calibrate_thresholds_generative.py public_data_dev/dev.jsonl --model Qwen/Qwen3-4B --lean-prompt --df-path emnllp-dialog-flow-dialog-flow.json --batch-size 16 --adapter-dir $SCRATCH/8-18-qwen-improve/qwen3-4B-oversample-st3-3/best --k 5 --temperature 0.7 --val-fraction 0.3 --min-support 20 --out $SCRATCH/8-18-qwen-improve/qwen3-4B-oversample-st3-3/best

# 4. Once #3 has written thresholds.json, this reruns self-consistency using those tuned
#    per-label thresholds instead of a flat 0.5 majority vote for the escalated subset --
#    compare its escalated-subset score against 2a's to see whether calibration beat plain
#    majority vote.
bash slurm_wrapper.sh 1 src/lora/lora_predict_generative_selfconsistent.py public_data_dev/dev.jsonl --model Qwen/Qwen3-4B --lean-prompt --df-path emnllp-dialog-flow-dialog-flow.json --batch-size 16 --adapter-dir $SCRATCH/8-18-qwen-improve/qwen3-4B-oversample-st3-3/best --thresholds-dir $SCRATCH/8-18-qwen-improve/qwen3-4B-oversample-st3-3/best --k 5 --temperature 0.7 --out runs/submission_selfconsistent_calibrated_dev.jsonl
