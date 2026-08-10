#!/bin/bash
# Usage: bash slurm_wrapper_torchrun.sh <GPUs> <train_script> [train_args...]
#
# Same as slurm_wrapper.sh, but actually launches via `torchrun` (multi-process, one per GPU)
# instead of plain `python` (single process). Use this for train_args that need a real
# torch.distributed process group -- e.g. lora_train_generative.py/lora_predict_generative.py's
# --parallelism tensor (see src/lora/lora_model.py), which requires RANK/LOCAL_RANK/WORLD_SIZE
# to be set per-process; plain `python ... --parallelism tensor` fails fast with a clear error
# telling you to use torchrun instead. --parallelism pipeline/none still work fine here too,
# since torchrun with --nproc-per-node=1 just runs a single process like plain python would.
#
# Example:
#   bash slurm_wrapper_torchrun.sh 4 src/lora/lora_train_generative.py public_data_dev/train.jsonl public_data_dev/dev.jsonl --epochs 200 --output-dir runs/lora_qwen --parallelism tensor

GPUs=$1
TRAIN_SCRIPT=$2
PARTITION=gpubase_l40s_b2

if [ -z "$GPUs" ] || [ -z "$TRAIN_SCRIPT" ]; then
    echo "Usage: bash $0 <GPUs> <train_script> [train_args...]"
    echo
    echo "  GPUs          number of GPUs (sets torchrun --nproc-per-node)"
    echo "  train_script  path to the Python training script"
    echo "  train_args    any remaining args are passed through to train_script"
    echo "                (pass --parallelism tensor yourself if that's what you want)"
    exit 1
fi

shift 2
EXTRA_ARGS=("$@")

JOB_NAME=$(basename "$TRAIN_SCRIPT" .py)
DATETIME=$(date +%Y%m%d_%H%M%S)
LOG="slurm_${JOB_NAME}_torchrun_${DATETIME}.log"
SLURM_SCRIPT="slurm_${JOB_NAME}_torchrun.slrm"
SLURM_SUBMIT_DIR=$(pwd)

TORCHRUN_CMD="torchrun --standalone --nproc-per-node=$GPUs $TRAIN_SCRIPT ${EXTRA_ARGS[*]}"

echo
echo "Job: $JOB_NAME on $GPUs GPUs (torchrun)"
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
#SBATCH --time=4:00:00
#SBATCH --mem=40gb
#SBATCH --cpus-per-task=10

echo "Running on \$(hostname)"
echo "Started: \$(date)"
echo "Account: \$SLURM_JOB_ACCOUNT"
echo "Partition: \$SLURM_JOB_PARTITION"
echo "---"


cd "$SLURM_SUBMIT_DIR"

# --- Setup workspace  ---source .venv/bin/activate

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
