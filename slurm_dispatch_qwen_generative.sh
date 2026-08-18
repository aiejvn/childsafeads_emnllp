#!/bin/bash

# Qwen3-4B generative LoRA (joint st1/st2/st3) follow-ups to the 8-17 run
# (slurm_logs/8-17-runs/slurm_lora_train_generative_20260817_210119.log). One
# `bash slurm_wrapper.sh 1 ...` command per line -- copy-paste individual lines
# into your CLI.
#
# What that run showed: train loss went 1.17 -> 0.0000 over 20 epochs while dev
# mean_macro_f1 only moved 0.697 (epoch 10) -> 0.706 (epoch 20) -- ~1h50m of extra
# compute for +0.009. Worse, the extra training actively erased a rare label:
# hfss_food_marketing dev F1 went 0.143 (epoch 10) -> 0.000 (epoch 20) despite a
# pos_weight of 50.0 on it. --eval-every was 10, so there are only two data points
# and no visibility into where the real peak was or when the collapse started.
# st3 stays the weak stage throughout (macro_f1 0.55-0.61) with heavy confusion
# among hfss_food_marketing / inadequate_disclosure / misleading_claim /
# direct_exhortation / no_flag.
#
# Every run below keeps --epochs 12 --eval-every 2 (finer-grained checkpoints,
# stop before the interpolate-to-near-zero regime) so we can actually see the
# peak and catch any per-label collapse instead of guessing between two
# snapshots. --split-seed is intentionally left unset per the script's own
# guidance (a fixed holdout just becomes a second dev set experiments overfit
# to) -- dev.jsonl is the fixed ground truth across all of these.

# 1. Eval-cadence control -- otherwise identical to the 8-17 run's config
#    (same lr/lora-r/target-modules/pos-weight/batch/grad-accum). Isolates how
#    much of the epoch-10-vs-20 story was just eval granularity vs real signal.
bash slurm_wrapper.sh 1 src/lora/lora_train_generative.py public_data_dev/train.jsonl public_data_dev/dev.jsonl --model Qwen/Qwen3-4B --df-path emnllp-dialog-flow-dialog-flow.json --lean-prompt --epochs 12 --eval-every 2 --batch-size 1 --grad-accum-steps 4 --lr 2e-4 --lora-r 8 --lora-alpha 16 --lora-dropout 0.1 --target-modules q_proj,k_proj,v_proj,o_proj --pos-weight --test-holdout 500 --eval-batch-size 16 --output-dir runs/8-18-qwen-improve/qwen3-4B-evalevery2 --checkpoint-save-path $SCRATCH/8-18-qwen-improve/qwen3-4B-evalevery2

# 2. Oversample rare st3 labels (factor 3) -- the 8-17 run left
#    --oversample-rare-st3 at its default of 1 (a no-op) and relied on
#    pos_weight alone, which did not stop hfss_food_marketing from collapsing
#    to F1=0.000. Actually duplicating those rare-label instances in the train
#    stream should give the model more exposure than loss reweighting alone.
bash slurm_wrapper.sh 1 src/lora/lora_train_generative.py public_data_dev/train.jsonl public_data_dev/dev.jsonl --model Qwen/Qwen3-4B --df-path emnllp-dialog-flow-dialog-flow.json --lean-prompt --epochs 12 --eval-every 2 --batch-size 1 --grad-accum-steps 4 --lr 2e-4 --lora-r 8 --lora-alpha 16 --lora-dropout 0.1 --target-modules q_proj,k_proj,v_proj,o_proj --pos-weight --oversample-rare-st3 3 --test-holdout 500 --eval-batch-size 16 --output-dir runs/8-18-qwen-improve/qwen3-4B-oversample-st3-3 --checkpoint-save-path $SCRATCH/8-18-qwen-improve/qwen3-4B-oversample-st3-3

# 3. Larger effective batch (grad-accum 8 -> effective batch 8, up from 4) --
#    batch-size is pinned at 1 by max-length=4096 memory limits, so grad-accum
#    is the only lever. Smoother gradients may slow the collapse into the
#    near-zero-loss interpolation regime seen by epoch ~8 in the 8-17 run.
bash slurm_wrapper.sh 1 src/lora/lora_train_generative.py public_data_dev/train.jsonl public_data_dev/dev.jsonl --model Qwen/Qwen3-4B --df-path emnllp-dialog-flow-dialog-flow.json --lean-prompt --epochs 12 --eval-every 2 --batch-size 1 --grad-accum-steps 8 --lr 2e-4 --lora-r 8 --lora-alpha 16 --lora-dropout 0.1 --target-modules q_proj,k_proj,v_proj,o_proj --pos-weight --test-holdout 500 --eval-batch-size 16 --output-dir runs/8-18-qwen-improve/qwen3-4B-gradaccum8 --checkpoint-save-path $SCRATCH/8-18-qwen-improve/qwen3-4B-gradaccum8

# 4. Lower LR + more LoRA dropout -- direct regularization against the
#    interpolate-to-zero trajectory (loss hit 0.0000 by epoch 19 in the 8-17
#    run), rather than just catching it earlier via eval cadence.
bash slurm_wrapper.sh 1 src/lora/lora_train_generative.py public_data_dev/train.jsonl public_data_dev/dev.jsonl --model Qwen/Qwen3-4B --df-path emnllp-dialog-flow-dialog-flow.json --lean-prompt --epochs 12 --eval-every 2 --batch-size 1 --grad-accum-steps 4 --lr 1e-4 --lora-r 8 --lora-alpha 16 --lora-dropout 0.2 --target-modules q_proj,k_proj,v_proj,o_proj --pos-weight --test-holdout 500 --eval-batch-size 16 --output-dir runs/8-18-qwen-improve/qwen3-4B-lr1e-4-dropout0.2 --checkpoint-save-path $SCRATCH/8-18-qwen-improve/qwen3-4B-lr1e-4-dropout0.2

# 5. st3-loss-weight bump (2x) + oversample-rare-st3 3 together -- st3 is the
#    persistently weak stage (macro_f1 0.55-0.61 across every checkpoint in the
#    8-17 run); push more gradient signal at it from both the loss and the
#    data-stream side simultaneously rather than one lever alone.
bash slurm_wrapper.sh 1 src/lora/lora_train_generative.py public_data_dev/train.jsonl public_data_dev/dev.jsonl --model Qwen/Qwen3-4B --df-path emnllp-dialog-flow-dialog-flow.json --lean-prompt --epochs 12 --eval-every 2 --batch-size 1 --grad-accum-steps 4 --lr 2e-4 --lora-r 8 --lora-alpha 16 --lora-dropout 0.1 --target-modules q_proj,k_proj,v_proj,o_proj --pos-weight --st3-loss-weight 2.0 --oversample-rare-st3 3 --test-holdout 500 --eval-batch-size 16 --output-dir runs/8-18-qwen-improve/qwen3-4B-st3weight2-oversample3 --checkpoint-save-path $SCRATCH/8-18-qwen-improve/qwen3-4B-st3weight2-oversample3

# 6. Combined best-guess -- merges the two changes above that don't fight each
#    other (oversample-rare-st3 + larger effective batch) into one candidate
#    for the next full run, once 1-5 show which levers actually moved dev
#    macro_f1 without re-triggering the rare-label collapse.
bash slurm_wrapper.sh 1 src/lora/lora_train_generative.py public_data_dev/train.jsonl public_data_dev/dev.jsonl --model Qwen/Qwen3-4B --df-path emnllp-dialog-flow-dialog-flow.json --lean-prompt --epochs 12 --eval-every 2 --batch-size 1 --grad-accum-steps 8 --lr 2e-4 --lora-r 8 --lora-alpha 16 --lora-dropout 0.1 --target-modules q_proj,k_proj,v_proj,o_proj --pos-weight --oversample-rare-st3 3 --test-holdout 500 --eval-batch-size 16 --output-dir runs/8-18-qwen-improve/qwen3-4B-combined --checkpoint-save-path $SCRATCH/8-18-qwen-improve/qwen3-4B-combined
