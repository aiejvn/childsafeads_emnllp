"""Run a trained generative LoRA causal-LM adapter (see lora_train_generative.py) over a
split and write a submission.jsonl.

Usage (run from the repo root):
    python src/lora/lora_predict_generative.py public_data_dev/dev.jsonl \\
        --model Qwen/Qwen3.5-4B --adapter-dir runs/lora_qwen/best \\
        --out runs/submission_lora_qwen.jsonl

Prints the same macro-F1 metrics as lora_predict.py whenever the target split carries gold
"labels". Decoding is freeform generation, parsed against baseline_gpt.py's `Prediction`
schema (see lora_generative.py); a completion that fails to parse is regenerated up to 3
times before falling back to a default prediction, so -- unlike the encoder path's
independent-sigmoid decode() -- there's no separate disclosure-conflict/empty-st2 resolution
step here beyond that fallback.
"""
import argparse
import logging
import os
import random
import shutil
import sys
from datetime import datetime

import torch
from torch.utils.data import DataLoader
from transformers import AutoTokenizer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # so `import lora` resolves src/lora as a package
from common.dialog_flow import df_pre_context  # noqa: E402
from common.predict_utils import log_evaluation, write_submission  # noqa: E402
from lora import CONTEXT_CHOICES, SFT_TAXONOMY, SYSTEM_PROMPT, evaluate, load_split, setup_logging  # noqa: E402
from lora.lora_data import GenerativeCollator, GenerativeDataset  # noqa: E402
from lora.lora_few_shot import FEW_SHOT_BUILDERS  # noqa: E402
from lora.lora_generative import generate_predictions  # noqa: E402
from lora.lora_model import PARALLELISM_CHOICES, load_peft_model_causal  # noqa: E402

#  bash slurm_wrapper.sh 4 src/lora/lora_predict_generative.py public_data_test/test.jsonl  --model Qwen/Qwen3-4B --adapter-dir $SCRATCH/Qwen-4B/best --out runs/submission_lora_qwen3-4B-8-13.jsonl --parallelism pipeline --lean-prompt --df-path emnllp-dialog-flow-dialog-flow.json  --batch-size 1
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="split to predict on, e.g. public_data_dev/dev.jsonl")
    ap.add_argument("--model", default="Qwen/Qwen3.5-4B", help="must match the base model used in training")
    ap.add_argument("--adapter-dir", required=True, help="e.g. runs/lora_qwen/best")
    ap.add_argument("--context", choices=CONTEXT_CHOICES, default="full",
                    help="which rungs of the instance the model sees. no_product_page drops the linked page "
                         "entirely (a median 38%% of full_context's tokens); st2_page keeps only its "
                         "ST2-bearing lines, see common/page_filter.py")
    ap.add_argument("--lean-prompt", action="store_true",
                    help="must match the flag used in training -- the adapter was fit against "
                         "whichever system prompt was in front of it")
    ap.add_argument("--df-path", default=None, help="must match the path used in training")
    ap.add_argument("--st3-only", action="store_true", help="must match the flag used in "
                     "training -- selects the {\"st3\":[...]} completion schema for parsing")
    ap.add_argument("--st12-only", action="store_true", help="must match the flag used in "
                     "training -- selects the {\"st1\":...,\"st2\":[...]} completion schema "
                     "for parsing")
    ap.add_argument("--st1-only", action="store_true", help="must match the flag used in "
                     "training -- selects the {\"st1\":...} completion schema for parsing. "
                     "Mutually exclusive with --st3-only/--st12-only")
    ap.add_argument("--few-shot", action="store_true", help="must match the flag used in "
                     "training -- appends the same hand-picked FEW-SHOT EXAMPLES section to "
                     "the system prompt (see lora_few_shot.py). Only --st1-only has a curated "
                     "example set so far")
    ap.add_argument("--max-length", type=int, default=4096)
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--max-new-tokens", type=int, default=128)
    ap.add_argument("--load-in-4bit", action="store_true", help="must match the flag used in training")
    ap.add_argument("--parallelism", choices=PARALLELISM_CHOICES, default="none", help="split the model "
                     "across GPUs (requires >=2, must match training if inference-quality matters): "
                     "\"pipeline\" shards layers via device_map=\"auto\"; \"tensor\" shards weight matrices "
                     "via tp_plan=\"auto\" (must launch with torchrun); \"none\" keeps everything on --device")
    ap.add_argument("--sample-size", type=int, default=None, help="predict on a random sample only (smoke test)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--device", default=None)
    ap.add_argument("--out", help="defaults to runs/submission_lora_generative_<timestamp>.jsonl")
    args = ap.parse_args()
    if sum([args.st3_only, args.st12_only, args.st1_only]) > 1:
        ap.error("--st3-only, --st12-only, and --st1-only are mutually exclusive")
    tier_mode = "st1_only" if args.st1_only else (
        "st12_only" if args.st12_only else ("st3_only" if args.st3_only else "joint"))
    if args.few_shot and tier_mode not in FEW_SHOT_BUILDERS:
        ap.error(f"--few-shot has no curated examples for {tier_mode} mode yet (only "
                 f"{sorted(FEW_SHOT_BUILDERS)} are curated -- see lora_few_shot.py)")

    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    is_main = int(os.environ.get("RANK", "0")) == 0  # only rank 0 logs/writes output under --parallelism tensor
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if is_main:
        log = setup_logging("runs", "lora_predict_generative", args.model.replace("/", "_"), timestamp)
    else:
        log = logging.getLogger("lora_predict_generative_worker")
        log.addHandler(logging.NullHandler())
        log.propagate = False

    model_path = os.path.join("models", args.model)
    if not os.path.isdir(model_path):
        raise FileNotFoundError(
            f"expected local model at {model_path!r} (from --model {args.model!r}); "
            f"download it first with `hf download {args.model} --local-dir {model_path}`"
        )
    log.info(f"loading model/tokenizer from local path {model_path} (no remote download)")

    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"  # batched model.generate() needs left-padding

    model = load_peft_model_causal(
        model_path, args.adapter_dir, load_in_4bit=args.load_in_4bit, device=device, local_files_only=True,
        parallelism=args.parallelism,
    )
    if args.parallelism == "none" and not args.load_in_4bit:
        model = model.to(device)
    model.eval()

    instances = list(load_split(args.target))
    if args.sample_size:
        instances = random.Random(args.seed).sample(instances, min(args.sample_size, len(instances)))
    system_prompt = SFT_TAXONOMY if args.lean_prompt else SYSTEM_PROMPT
    df_text = df_pre_context(args.df_path, lean=args.lean_prompt) if args.df_path else None
    if args.few_shot:
        few_shot_text = FEW_SHOT_BUILDERS[tier_mode]()
        log.info(f"--few-shot: appending {tier_mode} FEW-SHOT EXAMPLES section "
                 f"({len(few_shot_text)} chars) to the system prompt")
        system_prompt = f"{system_prompt}\n\n{few_shot_text}"
    log.info(f"system prompt: {'lean' if args.lean_prompt else 'full'} ({len(system_prompt)} chars)"
             + (f" + dialog flow from {args.df_path} ({len(df_text)} chars)" if df_text else ""))
    loader = DataLoader(
        GenerativeDataset(instances, tokenizer, args.context, args.max_length, system_prompt, df_text,
                          st3_only=args.st3_only, st12_only=args.st12_only, st1_only=args.st1_only,
                          include_completion=False),
        batch_size=args.batch_size, shuffle=False, collate_fn=GenerativeCollator(tokenizer),
    )
    ids, predictions = generate_predictions(model, loader, tokenizer, args.max_new_tokens,
                                            st3_only=args.st3_only, st12_only=args.st12_only,
                                            st1_only=args.st1_only, log=log)

    if not is_main:  # avoid every rank racing to write the same output files under --parallelism tensor
        return

    out = args.out or os.path.join("runs", f"submission_lora_generative_{timestamp}.jsonl")
    error_out = os.path.join("runs", f"submission_lora_generative_error_{timestamp}.jsonl")
    gold, n_errors = write_submission(out, error_out, ids, instances, predictions)
    log.info(f"wrote {len(predictions)} predictions to {out}")

    canonical = "submission_lora_generative.jsonl"
    shutil.copyfile(out, canonical)
    log.info(f"copied predictions to {canonical} (canonical submission file)")

    if gold:
        log.info(f"wrote {n_errors} misclassified instance(s) to {error_out}")
        metrics = evaluate(gold, predictions)
        log_evaluation(log, metrics)
    else:
        log.info("target has no gold labels -- skipping evaluation")


if __name__ == "__main__":
    main()
