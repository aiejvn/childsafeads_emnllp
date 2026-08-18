"""Per-label decision-threshold calibration for the generative Qwen pipeline -- the thing
src/common/predict_utils.py's tune_per_label_thresholds() already does every epoch for the
encoder+MLP LoRA classifiers (lora_train_st2_classifier.py/lora_train_st3_classifier.py),
but that machinery needs a probability per label, and the generative pipeline never
produces one: it decodes a free-text JSON completion, not a sigmoid. This script manufactures
that missing probability the same way lora_predict_generative_selfconsistent.py does --
k-sample self-consistency, per-label vote frequency in [0, 1] standing in for a probability --
then feeds it into the *same*, unmodified tune_per_label_thresholds()/decode() functions the
encoder path uses, and saves the result to thresholds.json in the same format
predict_utils.save_thresholds()/load_thresholds() already read and write. The output is
directly consumable by lora_predict_generative_selfconsistent.py's --thresholds-dir.

This is the expensive one of the three post-training scripts: unlike
lora_predict_generative_selfconsistent.py's selective escalation (only fragile-label
instances get resampled), building per-label thresholds needs a probability for *every*
st2/st3 label, so it runs k samples over the *entire* target split. Budget accordingly --
this is meant to be run once per checkpoint to produce a reusable thresholds.json, not on
every prediction run.

Overfitting risk and how this guards against it: several st3 labels have single-digit-to-low-
double-digit gold positives in public_data_dev/dev.jsonl (e.g. hfss_food_marketing,
insufficient_context). Grid-searching a threshold per label against that few positives and
then reporting the score on the *same* instances is close to guaranteed to fit dev noise
rather than signal -- exactly the failure mode the encoder pipeline avoids by tuning
thresholds on dev but only ever reloading (never re-tuning) them for its held-out test-holdout
pass. This script does the same split internally: `target` (e.g. public_data_dev/dev.jsonl,
the only split every one of this repo's generative checkpoints has never trained on) is
divided into a tune/check partition via --val-fraction, thresholds are fit on the tune
partition only, and both the (optimistic, same-data) tune-partition score and the honest
check-partition score are reported side by side -- never trust the tune-partition number
alone. --min-support skips tuning (falls back to the flat --default-threshold) for any label
with fewer than that many gold positives in the tune partition, since a threshold fit to a
handful of examples is closer to memorizing which few rows are positive than learning a real
decision boundary.

Usage (from repo root):
    python src/lora/lora_calibrate_thresholds_generative.py public_data_dev/dev.jsonl \\
        --model Qwen/Qwen3-4B --lean-prompt --df-path emnllp-dialog-flow-dialog-flow.json \\
        --adapter-dir $SCRATCH/8-18-qwen-improve/qwen3-4B-oversample-st3-3/best \\
        --k 5 --temperature 0.7 --out $SCRATCH/8-18-qwen-improve/qwen3-4B-oversample-st3-3/best
"""
import argparse
import os
import random
import sys
from datetime import datetime

import torch
from torch.utils.data import DataLoader
from transformers import AutoTokenizer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # so `import lora` resolves src/lora as a package
from common.dialog_flow import df_pre_context  # noqa: E402
from common.predict_utils import (  # noqa: E402
    decode, log_evaluation, multi_hot_matrix, save_thresholds, tune_per_label_thresholds,
)
from lora import (  # noqa: E402
    CONTEXT_CHOICES, SFT_TAXONOMY, ST1_LABELS, ST2_LABELS, ST3_LABELS, SYSTEM_PROMPT, evaluate, load_split,
    setup_logging,
)
from lora.lora_data import GenerativeCollator, GenerativeDataset  # noqa: E402
from lora.lora_generative import self_consistency_probs  # noqa: E402
from lora.lora_model import PARALLELISM_CHOICES, load_peft_model_causal  # noqa: E402


def apply_min_support(threshold: torch.Tensor, gold_multihot: torch.Tensor, min_support: int,
                      default: float) -> torch.Tensor:
    support = gold_multihot.sum(dim=0)
    out = threshold.clone()
    out[support < min_support] = default
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", help="scored split to calibrate against, e.g. public_data_dev/dev.jsonl "
                     "(must carry gold labels -- split internally into tune/check partitions)")
    ap.add_argument("--model", default="Qwen/Qwen3-4B", help="must match the base model used in training")
    ap.add_argument("--adapter-dir", required=True)
    ap.add_argument("--context", choices=CONTEXT_CHOICES, default="full")
    ap.add_argument("--lean-prompt", action="store_true", help="must match the flag used in training")
    ap.add_argument("--df-path", default=None, help="must match the path used in training")
    ap.add_argument("--max-length", type=int, default=4096)
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--max-new-tokens", type=int, default=128)
    ap.add_argument("--load-in-4bit", action="store_true")
    ap.add_argument("--parallelism", choices=PARALLELISM_CHOICES, default="none")
    ap.add_argument("--k", type=int, default=5, help="samples per instance used to build the vote-frequency "
                     "pseudo-probability")
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--val-fraction", type=float, default=0.3, help="fraction of `target` held back as the "
                     "check partition (thresholds are tuned on the rest and never touch this fraction "
                     "until the final honest-score report). Pass 0 to tune on the whole split with no "
                     "held-out check (the tune-partition score is then the only number reported, and it "
                     "is optimistic -- only do this if you already have another way to validate)")
    ap.add_argument("--min-support", type=int, default=20, help="labels with fewer than this many gold "
                     "positives in the tune partition keep --default-threshold instead of being tuned -- "
                     "grid-searching a threshold against a handful of positives mostly fits noise")
    ap.add_argument("--default-threshold", type=float, default=0.5)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--device", default=None)
    ap.add_argument("--out", required=True, help="directory to write thresholds.json to -- typically the "
                     "same --adapter-dir, so lora_predict_generative_selfconsistent.py's --thresholds-dir "
                     "can point straight at the checkpoint")
    args = ap.parse_args()

    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log = setup_logging("runs", "lora_calibrate_thresholds_generative", args.model.replace("/", "_"), timestamp)

    model_path = os.path.join("models", args.model)
    if not os.path.isdir(model_path):
        raise FileNotFoundError(f"expected local model at {model_path!r} (from --model {args.model!r})")
    log.info(f"loading model/tokenizer from local path {model_path} (no remote download)")

    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"

    model = load_peft_model_causal(
        model_path, args.adapter_dir, load_in_4bit=args.load_in_4bit, device=device, parallelism=args.parallelism,
        local_files_only=True,
    )
    if args.parallelism == "none" and not args.load_in_4bit:
        model = model.to(device)
    model.eval()

    instances = list(load_split(args.target))
    if not all(inst.get("labels") for inst in instances):
        raise SystemExit(f"{args.target} has instances with no gold labels -- threshold calibration needs a "
                          "fully-labeled split (e.g. public_data_dev/dev.jsonl), not the withheld test split")

    system_prompt = SFT_TAXONOMY if args.lean_prompt else SYSTEM_PROMPT
    df_text = df_pre_context(args.df_path, lean=args.lean_prompt) if args.df_path else None
    log.info(f"system prompt: {'lean' if args.lean_prompt else 'full'} ({len(system_prompt)} chars)"
             + (f" + dialog flow from {args.df_path} ({len(df_text)} chars)" if df_text else ""))

    loader = DataLoader(
        GenerativeDataset(instances, tokenizer, args.context, args.max_length, system_prompt, df_text,
                          include_completion=False),
        batch_size=args.batch_size, shuffle=False, collate_fn=GenerativeCollator(tokenizer),
    )
    ids, st1_votes, st2_freq, st3_freq = self_consistency_probs(
        model, loader, tokenizer, args.max_new_tokens, args.k, args.temperature, log=log,
    )
    id_to_instance = {inst["instanceID"]: inst for inst in instances}
    ordered_instances = [id_to_instance[iid] for iid in ids]
    st1_idx = torch.tensor([ST1_LABELS.index(votes.most_common(1)[0][0]) for votes in st1_votes])

    rng = random.Random(args.seed)
    order = list(range(len(ids)))
    rng.shuffle(order)
    n_check = round(len(order) * args.val_fraction)
    check_idx = sorted(order[:n_check])
    tune_idx = sorted(order[n_check:])
    log.info(f"tune partition: {len(tune_idx)} instances, check (held-out) partition: {len(check_idx)} instances")

    tune_st2_gold = multi_hot_matrix([ordered_instances[i] for i in tune_idx], "st2", ST2_LABELS)
    tune_st3_gold = multi_hot_matrix([ordered_instances[i] for i in tune_idx], "st3", ST3_LABELS)
    st2_threshold = tune_per_label_thresholds(st2_freq[tune_idx], tune_st2_gold, default=args.default_threshold)
    st3_threshold = tune_per_label_thresholds(st3_freq[tune_idx], tune_st3_gold, default=args.default_threshold)
    st2_threshold = apply_min_support(st2_threshold, tune_st2_gold, args.min_support, args.default_threshold)
    st3_threshold = apply_min_support(st3_threshold, tune_st3_gold, args.min_support, args.default_threshold)
    log.info("tuned st2 thresholds: " + ", ".join(f"{l}={t:.2f}" for l, t in zip(ST2_LABELS, st2_threshold.tolist())))
    log.info("tuned st3 thresholds: " + ", ".join(f"{l}={t:.2f}" for l, t in zip(ST3_LABELS, st3_threshold.tolist())))

    def decode_and_score(idx: list, label: str) -> None:
        preds = decode(st1_idx[idx], st2_freq[idx], st3_freq[idx], st2_threshold, st3_threshold)
        gold = [ordered_instances[i]["labels"] for i in idx]
        log.info(f"=== {label} ({len(idx)} instances) ===")
        log_evaluation(log, evaluate(gold, preds))

    decode_and_score(tune_idx, "tune partition -- OPTIMISTIC, thresholds were fit on this data")
    if check_idx:
        decode_and_score(check_idx, "check (held-out) partition -- the honest number")
    else:
        log.info("--val-fraction 0: no held-out check partition -- the tune-partition score above is the "
                 "only number available and is optimistic; validate some other way before trusting these "
                 "thresholds over a flat 0.5")

    save_thresholds(args.out, st2_threshold, st3_threshold)
    log.info(f"wrote thresholds.json to {args.out} -- point lora_predict_generative_selfconsistent.py's "
             "--thresholds-dir here")


if __name__ == "__main__":
    main()
