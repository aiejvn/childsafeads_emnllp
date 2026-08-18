#!/bin/bash

# Longformer (allenai/longformer-base-4096) experiments for the st1/st2/st3 encoder+MLP
# classifiers. One `bash slurm_wrapper.sh 1 ...` command per line -- copy-paste individual
# lines into your CLI. Drop --local from any line if the model isn't synced to
# ./models/allenai/longformer-base-4096 on the cluster (it'll resolve from the HF hub instead).
# batch-size=8 is a safe estimate for a single H100 (80GB) -- local testing on a 23GB GPU
# OOM'd at batch=4, worked at batch=2 (~14GB); Longformer's HF eager sliding-window attention
# is much more memory-hungry than its "linear attention" reputation suggests.

# --- st1 (single-label 5-way, --class-weight) ---

# 1. Replicate the in-progress local baseline on a fresh split -- confirms reproducibility.
bash slurm_wrapper.sh 1 src/lora/lora_train_st1_classifier.py public_data_dev/train.jsonl public_data_dev/dev.jsonl --model allenai/longformer-base-4096 --local --context full --max-length 4096 --truncation-side left --epochs 10 --batch-size 8 --lr 2e-4 --lora-r 8 --lora-alpha 16 --target-modules query,value --class-weight --oversample-rare-st1 3 --test-holdout 500 --output-dir $SCRATCH/long-runs/st1-classifier-longformer-rep2 --no-wandb

# 2. Global-attention LoRA adaptation -- the baseline only adapts local query/value;
#    Longformer's CLS-token classification signal flows through the global attention
#    pathway (query_global/value_global), which stays frozen otherwise.
bash slurm_wrapper.sh 1 src/lora/lora_train_st1_classifier.py public_data_dev/train.jsonl public_data_dev/dev.jsonl --model allenai/longformer-base-4096 --local --context full --max-length 4096 --truncation-side left --epochs 10 --batch-size 8 --lr 2e-4 --lora-r 8 --lora-alpha 16 --target-modules query,value,query_global,value_global --class-weight --oversample-rare-st1 3 --test-holdout 500 --output-dir $SCRATCH/long-runs/st1-classifier-longformer-global --no-wandb

# 3. Max-length=2048 -- cheaper context cap (79% instance coverage vs 4096's 99.5%).
bash slurm_wrapper.sh 1 src/lora/lora_train_st1_classifier.py public_data_dev/train.jsonl public_data_dev/dev.jsonl --model allenai/longformer-base-4096 --local --context full --max-length 2048 --truncation-side left --epochs 10 --batch-size 8 --lr 2e-4 --lora-r 8 --lora-alpha 16 --target-modules query,value --class-weight --oversample-rare-st1 3 --test-holdout 500 --output-dir $SCRATCH/long-runs/st1-classifier-longformer-maxlen2048 --no-wandb

# 4. Capacity bump (r16/a32) -- roberta showed an inverted-U under truncated context; worth
#    re-checking now that the model can see everything.
bash slurm_wrapper.sh 1 src/lora/lora_train_st1_classifier.py public_data_dev/train.jsonl public_data_dev/dev.jsonl --model allenai/longformer-base-4096 --local --context full --max-length 4096 --truncation-side left --epochs 10 --batch-size 8 --lr 2e-4 --lora-r 16 --lora-alpha 32 --target-modules query,value --class-weight --oversample-rare-st1 3 --test-holdout 500 --output-dir $SCRATCH/long-runs/st1-classifier-longformer-r16a32 --no-wandb

# 5. Oversample factor=2 -- roberta's oversample sweep was noisy under truncated context;
#    re-testing under genuinely full context removes that confound.
bash slurm_wrapper.sh 1 src/lora/lora_train_st1_classifier.py public_data_dev/train.jsonl public_data_dev/dev.jsonl --model allenai/longformer-base-4096 --local --context full --max-length 4096 --truncation-side left --epochs 10 --batch-size 8 --lr 2e-4 --lora-r 8 --lora-alpha 16 --target-modules query,value --class-weight --oversample-rare-st1 2 --test-holdout 500 --output-dir $SCRATCH/long-runs/st1-classifier-longformer-oversample2 --no-wandb

# --- st2 (multi-label, 12 product-category labels, --pos-weight) ---

# 1. Baseline -- first Longformer attempt for st2, standing recipe ported from st1 (r8/a16,
#    oversample-rare-st2=3, full context at 4096).
bash slurm_wrapper.sh 1 src/lora/lora_train_st2_classifier.py public_data_dev/train.jsonl public_data_dev/dev.jsonl --model allenai/longformer-base-4096 --local --context full --max-length 4096 --truncation-side left --epochs 10 --batch-size 8 --lr 2e-4 --lora-r 8 --lora-alpha 16 --target-modules query,value --pos-weight --oversample-rare-st2 3 --test-holdout 500 --output-dir $SCRATCH/long-runs/st2-classifier-longformer --no-wandb

# 2. Global-attention LoRA adaptation.
bash slurm_wrapper.sh 1 src/lora/lora_train_st2_classifier.py public_data_dev/train.jsonl public_data_dev/dev.jsonl --model allenai/longformer-base-4096 --local --context full --max-length 4096 --truncation-side left --epochs 10 --batch-size 8 --lr 2e-4 --lora-r 8 --lora-alpha 16 --target-modules query,value,query_global,value_global --pos-weight --oversample-rare-st2 3 --test-holdout 500 --output-dir $SCRATCH/long-runs/st2-classifier-longformer-global --no-wandb

# 3. Max-length=2048.
bash slurm_wrapper.sh 1 src/lora/lora_train_st2_classifier.py public_data_dev/train.jsonl public_data_dev/dev.jsonl --model allenai/longformer-base-4096 --local --context full --max-length 2048 --truncation-side left --epochs 10 --batch-size 8 --lr 2e-4 --lora-r 8 --lora-alpha 16 --target-modules query,value --pos-weight --oversample-rare-st2 3 --test-holdout 500 --output-dir $SCRATCH/long-runs/st2-classifier-longformer-maxlen2048 --no-wandb

# 4. Capacity bump (r16/a32).
bash slurm_wrapper.sh 1 src/lora/lora_train_st2_classifier.py public_data_dev/train.jsonl public_data_dev/dev.jsonl --model allenai/longformer-base-4096 --local --context full --max-length 4096 --truncation-side left --epochs 10 --batch-size 8 --lr 2e-4 --lora-r 16 --lora-alpha 32 --target-modules query,value --pos-weight --oversample-rare-st2 3 --test-holdout 500 --output-dir $SCRATCH/long-runs/st2-classifier-longformer-r16a32 --no-wandb

# 5. Oversample factor=2.
bash slurm_wrapper.sh 1 src/lora/lora_train_st2_classifier.py public_data_dev/train.jsonl public_data_dev/dev.jsonl --model allenai/longformer-base-4096 --local --context full --max-length 4096 --truncation-side left --epochs 10 --batch-size 8 --lr 2e-4 --lora-r 8 --lora-alpha 16 --target-modules query,value --pos-weight --oversample-rare-st2 2 --test-holdout 500 --output-dir $SCRATCH/long-runs/st2-classifier-longformer-oversample2 --no-wandb

# --- st3 (multi-label, adversarial/quality-flag labels, --pos-weight) ---

# 1. Baseline -- first Longformer attempt for st3, standing recipe ported from st1.
bash slurm_wrapper.sh 1 src/lora/lora_train_st3_classifier.py public_data_dev/train.jsonl public_data_dev/dev.jsonl --model allenai/longformer-base-4096 --local --context full --max-length 4096 --truncation-side left --epochs 10 --batch-size 8 --lr 2e-4 --lora-r 8 --lora-alpha 16 --target-modules query,value --pos-weight --oversample-rare-st3 3 --test-holdout 500 --output-dir $SCRATCH/long-runs/st3-classifier-longformer --no-wandb

# 2. Global-attention LoRA adaptation.
bash slurm_wrapper.sh 1 src/lora/lora_train_st3_classifier.py public_data_dev/train.jsonl public_data_dev/dev.jsonl --model allenai/longformer-base-4096 --local --context full --max-length 4096 --truncation-side left --epochs 10 --batch-size 8 --lr 2e-4 --lora-r 8 --lora-alpha 16 --target-modules query,value,query_global,value_global --pos-weight --oversample-rare-st3 3 --test-holdout 500 --output-dir $SCRATCH/long-runs/st3-classifier-longformer-global --no-wandb

# 3. Max-length=2048.
bash slurm_wrapper.sh 1 src/lora/lora_train_st3_classifier.py public_data_dev/train.jsonl public_data_dev/dev.jsonl --model allenai/longformer-base-4096 --local --context full --max-length 2048 --truncation-side left --epochs 10 --batch-size 8 --lr 2e-4 --lora-r 8 --lora-alpha 16 --target-modules query,value --pos-weight --oversample-rare-st3 3 --test-holdout 500 --output-dir $SCRATCH/long-runs/st3-classifier-longformer-maxlen2048 --no-wandb

# 4. Capacity bump (r16/a32).
bash slurm_wrapper.sh 1 src/lora/lora_train_st3_classifier.py public_data_dev/train.jsonl public_data_dev/dev.jsonl --model allenai/longformer-base-4096 --local --context full --max-length 4096 --truncation-side left --epochs 10 --batch-size 8 --lr 2e-4 --lora-r 16 --lora-alpha 32 --target-modules query,value --pos-weight --oversample-rare-st3 3 --test-holdout 500 --output-dir $SCRATCH/long-runs/st3-classifier-longformer-r16a32 --no-wandb

# 5. Oversample factor=2.
bash slurm_wrapper.sh 1 src/lora/lora_train_st3_classifier.py public_data_dev/train.jsonl public_data_dev/dev.jsonl --model allenai/longformer-base-4096 --local --context full --max-length 4096 --truncation-side left --epochs 10 --batch-size 8 --lr 2e-4 --lora-r 8 --lora-alpha 16 --target-modules query,value --pos-weight --oversample-rare-st3 2 --test-holdout 500 --output-dir $SCRATCH/long-runs/st3-classifier-longformer-oversample2 --no-wandb
