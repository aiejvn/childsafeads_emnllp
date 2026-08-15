#!/bin/bash
# Usage: bash slurm_wrapper.sh <GPUs> <train_script> [train_args...]
#
# Example:
#   bash slurm_wrapper.sh 4 src/lora/lora_train_generative.py public_data_dev/train.jsonl public_data_dev/dev.jsonl --epochs 200 --output-dir runs/lora_legalbert --no-wandb
#   bash slurm_wrapper.sh 4 src/lora/lora_train_generative.py public_data_dev/train.jsonl public_data_dev/dev.jsonl --epochs 200 --output-dir runs/lora_legalbert --parallelism pipeline --model Qwen/Qwen3-4B --df-path emnllp-dialog-flow-dialog-flow.json --lean-prompt --batch-size 1 --output-dir runs/lora_qwen --checkpoint-save-path $SCRATCH/8-12/Qwen3-4B-batch-size-1

#  bash slurm_wrapper.sh 4 src/lora/lora_train_generative.py public_data_dev/train.jsonl public_data_dev/dev.jsonl --epochs 200 --parallelism pipeline --model Qwen/Qwen3-4B --df-path emnllp-dialog-flow-dialog-flow.json --lean-prompt --batch-size 1 --output-dir runs/lora_qwen3-4B --checkpoint-save-path $SCRATCH/8-14/Qwen3-4B --split-seed 42 
#  bash slurm_wrapper.sh 4 src/lora/lora_train_generative.py public_data_dev/train.jsonl public_data_dev/dev.jsonl --epochs 200 --parallelism pipeline --df-path emnllp-dialog-flow-dialog-flow.json --lean-prompt --batch-size 1 --output-dir runs/lora_gemma-4-E4B --checkpoint-save-path $SCRATCH/8-14/gemma-4-E4B --model google/gemma-4-E4B --split-seed 42

GPUs=$1
TRAIN_SCRIPT=$2
PARTITION=gpubase_l40s_b2

if [ -z "$GPUs" ] || [ -z "$TRAIN_SCRIPT" ]; then
    echo "Usage: bash $0 <GPUs> <train_script> [train_args...]"
    echo
    echo "  GPUs          number of GPUs (also sets torchrun --nproc_per_node)"
    echo "  train_script  path to the Python training script"
    echo "  train_args    any remaining args are passed through to train_script"
    exit 1
fi

shift 2
EXTRA_ARGS=("$@")

JOB_NAME=$(basename "$TRAIN_SCRIPT" .py)
DATETIME=$(date +%Y%m%d_%H%M%S)
LOG="slurm_${JOB_NAME}_${DATETIME}.log"
SLURM_SCRIPT="slurm_${JOB_NAME}.slrm"
SLURM_SUBMIT_DIR=$(pwd)

TORCHRUN_CMD="python $TRAIN_SCRIPT ${EXTRA_ARGS[*]}"

echo
echo "Job: $JOB_NAME on $GPUs GPUs"
echo "Command: $TORCHRUN_CMD"
echo "Log: $LOG"
echo

cat > "$SLURM_SCRIPT" <<EOF
#!/bin/bash
#SBATCH --account=rrg-zhu2048
#SBATCH --nodes=1
#SBATCH --gres=gpu:$GPUs
#SBATCH --job-name=$JOB_NAME
#SBATCH --output=$LOG
#SBATCH --ntasks=1
#SBATCH --time=10:00:00
#SBATCH --mem=40gb
#SBATCH --cpus-per-task=10

echo "Running on \$(hostname)"
echo "Started: \$(date)"
echo "Account: \$SLURM_JOB_ACCOUNT"
echo "Partition: \$SLURM_JOB_PARTITION"
echo "---"


cd "$SLURM_SUBMIT_DIR"

# --- Setup workspace  ---
source .venv/bin/activate

echo "Python: \$(which python)  Torch: \$(python -c 'import torch; print(torch.__version__)')"
echo "---"

echo "Command: $TORCHRUN_CMD"
$TORCHRUN_CMD

echo "---"
echo "Finished: \$(date)"
EOF

# --- Submit ---
SLURM_JOB_ID=$(sbatch --parsable "$SLURM_SCRIPT")
scontrol update JobId="$SLURM_JOB_ID" JobName="${JOB_NAME}_${SLURM_JOB_ID}"
RESOLVED_LOG="${LOG//%j/$SLURM_JOB_ID}"
echo "Submitted job $SLURM_JOB_ID — log: $RESOLVED_LOG"
