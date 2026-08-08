#!/bin/bash
# Usage: bash slurm_wrapper.sh <GPUs> <train_script> [train_args...]
#
# Example:
#   bash slurm_wrapper.sh 4 src/lora/lora_train_generative.py public_data_dev/train.jsonl public_data_dev/dev.jsonl --epochs 200 --output-dir runs/lora_legalbert --no-wandb

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

TORCHRUN_CMD="uv run --with-requirements requirements.txt $TRAIN_SCRIPT ${EXTRA_ARGS[*]}"

echo
echo "Job: $JOB_NAME on $GPUs GPUs"
echo "Command: $TORCHRUN_CMD"
echo "Log: $LOG"
echo

cat > "$SLURM_SCRIPT" <<EOF
#!/bin/bash
#SBATCH --account=rrg-zhu2048
#SBATCH --partition=gpubase_l40s_b2
#SBATCH --nodes=1
#SBATCH --gres=gpu:2
#SBATCH --job-name=lora_generative_qwen
#SBATCH --output=$LOG
#SBATCH --ntasks=1
#SBATCH --time=4:00:00
#SBATCH --mem=40gb
#SBATCH --cpus-per-task=10

echo "Running on \$(hostname)"
echo "Started: \$(date)"
echo "Account: \$SLURM_JOB_ACCOUNT"
echo "Partition: \$SLURM_JOB_PARTITION"
echo "---"


cd "$SLURM_SUBMIT_DIR"
bash setup_uv.sh

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
