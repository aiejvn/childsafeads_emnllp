"""Selective self-consistency wrapper around lora_predict_generative.py: run one cheap greedy
pass over the whole target split (identical to lora_predict_generative.py), then only for
instances whose greedy prediction touches a "fragile" label (--fragile-label, default the
three st3 labels the 8-17 run's log showed collapsing under continued training --
hfss_food_marketing/insufficient_context/direct_exhortation) resample --k times at
--temperature and take a per-label majority vote instead of trusting the single greedy
decode. Everything else keeps the cheap greedy answer.

Why selective rather than blanket K-sampling every instance: K-sampling the whole split
multiplies inference cost by K for no benefit on the ~90% of instances the model already
gets right confidently, and on a single GPU that cost is real wall-clock time, not a
rounding error. Restricting the extra passes to instances that already touch a known-weak
label keeps the added cost proportional to how much of the split is actually uncertain.

Why this can still hurt, and why the script measures rather than assumes: majority vote
pulls a borderline-positive rare label toward negative, since "not this rare label" is the
prior outcome most of the time -- a genuinely correct greedy "yes" from one specific
decoding path can lose 3-of-5 to sampled "no"s. So this script always reports the
escalated subset's own before/after macro-F1 (greedy-only vs. self-consistency-applied,
both scored only on the instances that were actually escalated) right next to the overall
submission score, so a regression on exactly the labels this is meant to fix is visible
immediately rather than hiding inside one blended number. Don't trust the merged
submission over the plain greedy one until that subset comparison shows an improvement on
a scored split (e.g. public_data_dev/dev.jsonl) -- on the real target (no gold labels) this
script can only report the escalation count, not whether it helped.

Usage (from repo root):
    python src/lora/lora_predict_generative_selfconsistent.py public_data_dev/dev.jsonl \\
        --model Qwen/Qwen3-4B --lean-prompt --df-path emnllp-dialog-flow-dialog-flow.json \\
        --adapter-dir $SCRATCH/8-18-qwen-improve/qwen3-4B-oversample-st3-3/best \\
        --k 5 --temperature 0.7 --out runs/submission_selfconsistent_dev.jsonl
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
from common.predict_utils import decode, load_thresholds, log_evaluation, write_submission  # noqa: E402
from lora import CONTEXT_CHOICES, SFT_TAXONOMY, ST2_LABELS, ST3_LABELS, SYSTEM_PROMPT, evaluate, load_split, setup_logging  # noqa: E402
from lora.lora_data import GenerativeCollator, GenerativeDataset  # noqa: E402
from lora.lora_few_shot import FEW_SHOT_BUILDERS  # noqa: E402
from lora.lora_generative import generate_predictions, self_consistency_probs  # noqa: E402
from lora.lora_model import PARALLELISM_CHOICES, load_peft_model_causal  # noqa: E402

DEFAULT_FRAGILE_LABELS = ["st3:hfss_food_marketing", "st3:insufficient_context", "st3:direct_exhortation"]


def parse_fragile_labels(raw: list) -> dict:
    """--fragile-label entries look like "st2:gambling" or "st3:hfss_food_marketing".
    Returns {tier: set(labels)}."""
    fragile = {"st1": set(), "st2": set(), "st3": set()}
    for entry in raw:
        tier, _, label = entry.partition(":")
        if tier not in fragile or not label:
            raise ValueError(f"--fragile-label {entry!r} must look like 'st2:gambling' or 'st3:hfss_food_marketing'")
        fragile[tier].add(label)
    return fragile


def touches_fragile_label(pred: dict, fragile: dict) -> bool:
    if pred["st1"] in fragile["st1"]:
        return True
    if fragile["st2"] & set(pred["st2"]):
        return True
    if fragile["st3"] & set(pred["st3"]):
        return True
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", help="split to predict on, e.g. public_data_dev/dev.jsonl")
    ap.add_argument("--model", default="Qwen/Qwen3-4B", help="must match the base model used in training")
    ap.add_argument("--adapter-dir", required=True, help="e.g. $SCRATCH/8-18-qwen-improve/qwen3-4B-oversample-st3-3/best")
    ap.add_argument("--context", choices=CONTEXT_CHOICES, default="full")
    ap.add_argument("--lean-prompt", action="store_true", help="must match the flag used in training")
    ap.add_argument("--df-path", default=None, help="must match the path used in training")
    ap.add_argument("--st3-only", action="store_true", help="must match the flag used in training")
    ap.add_argument("--st12-only", action="store_true", help="must match the flag used in training")
    ap.add_argument("--st1-only", action="store_true", help="must match the flag used in training")
    ap.add_argument("--few-shot", action="store_true", help="must match the flag used in training")
    ap.add_argument("--max-length", type=int, default=4096)
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--max-new-tokens", type=int, default=128)
    ap.add_argument("--load-in-4bit", action="store_true")
    ap.add_argument("--parallelism", choices=PARALLELISM_CHOICES, default="none")
    ap.add_argument("--fragile-label", action="append", default=None,
                     help="tier:label to escalate to self-consistency sampling when the greedy pass "
                          f"predicts it, repeatable. Default: {DEFAULT_FRAGILE_LABELS} (the labels the "
                          "8-17 run's dev diagnostics showed collapsing under continued training)")
    ap.add_argument("--k", type=int, default=5, help="samples per escalated instance -- odd, so per-label "
                     "majority vote can't tie")
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--thresholds-dir", default=None, help="directory holding a thresholds.json from "
                     "lora_calibrate_thresholds_generative.py -- if given, the escalated subset is decoded "
                     "with those per-label thresholds instead of a flat 0.5 majority vote")
    ap.add_argument("--sample-size", type=int, default=None, help="predict on a random sample only (smoke test)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--device", default=None)
    ap.add_argument("--out", help="defaults to runs/submission_lora_generative_selfconsistent_<timestamp>.jsonl")
    args = ap.parse_args()
    if sum([args.st3_only, args.st12_only, args.st1_only]) > 1:
        ap.error("--st3-only, --st12-only, and --st1-only are mutually exclusive")
    if args.k % 2 == 0:
        ap.error(f"--k {args.k} is even -- a per-label majority vote can tie. Use an odd K.")
    tier_mode = "st1_only" if args.st1_only else (
        "st12_only" if args.st12_only else ("st3_only" if args.st3_only else "joint"))
    if args.few_shot and tier_mode not in FEW_SHOT_BUILDERS:
        ap.error(f"--few-shot has no curated examples for {tier_mode} mode yet")
    fragile = parse_fragile_labels(args.fragile_label or DEFAULT_FRAGILE_LABELS)

    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    is_main = int(os.environ.get("RANK", "0")) == 0
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if is_main:
        log = setup_logging("runs", "lora_predict_generative_selfconsistent", args.model.replace("/", "_"), timestamp)
    else:
        log = logging.getLogger("lora_predict_generative_selfconsistent_worker")
        log.addHandler(logging.NullHandler())
        log.propagate = False
    log.info(f"fragile labels (escalate to {args.k}-sample self-consistency when predicted): "
             + ", ".join(f"{t}:{l}" for t, labels in fragile.items() for l in sorted(labels)))

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
    if args.sample_size:
        instances = random.Random(args.seed).sample(instances, min(args.sample_size, len(instances)))
    system_prompt = SFT_TAXONOMY if args.lean_prompt else SYSTEM_PROMPT
    df_text = df_pre_context(args.df_path, lean=args.lean_prompt) if args.df_path else None
    if args.few_shot:
        few_shot_text = FEW_SHOT_BUILDERS[tier_mode]()
        system_prompt = f"{system_prompt}\n\n{few_shot_text}"
    log.info(f"system prompt: {'lean' if args.lean_prompt else 'full'} ({len(system_prompt)} chars)"
             + (f" + dialog flow from {args.df_path} ({len(df_text)} chars)" if df_text else ""))

    def build_loader(insts):
        return DataLoader(
            GenerativeDataset(insts, tokenizer, args.context, args.max_length, system_prompt, df_text,
                              st3_only=args.st3_only, st12_only=args.st12_only, st1_only=args.st1_only,
                              include_completion=False),
            batch_size=args.batch_size, shuffle=False, collate_fn=GenerativeCollator(tokenizer),
        )

    # --- pass 1: one cheap greedy decode over the whole split, identical to lora_predict_generative.py ---
    ids, greedy_preds = generate_predictions(model, build_loader(instances), tokenizer, args.max_new_tokens,
                                              st3_only=args.st3_only, st12_only=args.st12_only,
                                              st1_only=args.st1_only, log=log)
    id_to_instance = {inst["instanceID"]: inst for inst in instances}
    escalate_ids = [iid for iid, pred in zip(ids, greedy_preds) if touches_fragile_label(pred, fragile)]
    log.info(f"escalating {len(escalate_ids)}/{len(ids)} instances to {args.k}-sample self-consistency "
             f"(touched a fragile label in the greedy pass)")

    final_preds = dict(zip(ids, greedy_preds))
    if escalate_ids:
        escalated_instances = [id_to_instance[iid] for iid in escalate_ids]
        # --- pass 2: k sampled decodes over just the escalated subset, majority-voted per label ---
        sc_ids, st1_votes, st2_freq, st3_freq = self_consistency_probs(
            model, build_loader(escalated_instances), tokenizer, args.max_new_tokens, args.k, args.temperature,
            st3_only=args.st3_only, st12_only=args.st12_only, st1_only=args.st1_only, log=log,
        )
        from lora import ST1_LABELS
        st1_idx = torch.tensor([ST1_LABELS.index(votes.most_common(1)[0][0]) for votes in st1_votes])
        if args.thresholds_dir:
            st2_threshold, st3_threshold = load_thresholds(args.thresholds_dir)
            if st2_threshold is None:
                ap.error(f"--thresholds-dir {args.thresholds_dir} has no thresholds.json -- run "
                         "lora_calibrate_thresholds_generative.py first")
            log.info(f"decoding the escalated subset with per-label thresholds from {args.thresholds_dir}")
        else:
            # flat 0.5 threshold = plain majority vote (per-label threshold *tuning* is a separate,
            # dev-set-fitted step -- see lora_calibrate_thresholds_generative.py / --thresholds-dir)
            st2_threshold = torch.full((len(ST2_LABELS),), 0.5)
            st3_threshold = torch.full((len(ST3_LABELS),), 0.5)
        sc_preds = decode(st1_idx, st2_freq, st3_freq, st2_threshold, st3_threshold)
        final_preds.update(dict(zip(sc_ids, sc_preds)))

        # --- did it actually help? score the escalated subset both ways, not just the blended whole ---
        gold_subset = [id_to_instance[iid]["labels"] for iid in escalate_ids if id_to_instance[iid].get("labels")]
        if gold_subset:
            greedy_subset = [dict(zip(ids, greedy_preds))[iid] for iid in escalate_ids]
            log.info(f"=== escalated subset ({len(gold_subset)} instances) -- greedy-only ===")
            log_evaluation(log, evaluate(gold_subset, greedy_subset))
            log.info(f"=== escalated subset ({len(gold_subset)} instances) -- self-consistency applied ===")
            log_evaluation(log, evaluate(gold_subset, sc_preds))
        else:
            log.info("escalated subset has no gold labels (unlabeled target) -- can't tell whether "
                     "self-consistency helped here; validate on a scored split (e.g. public_data_dev/dev.jsonl) "
                     "before trusting this submission over the plain greedy one")
    else:
        log.info("nothing touched a fragile label -- submission is identical to plain greedy decoding")

    if not is_main:
        return

    predictions = [final_preds[iid] for iid in ids]
    out = args.out or os.path.join("runs", f"submission_lora_generative_selfconsistent_{timestamp}.jsonl")
    error_out = os.path.join("runs", f"submission_lora_generative_selfconsistent_error_{timestamp}.jsonl")
    gold, n_errors = write_submission(out, error_out, ids, instances, predictions)
    log.info(f"wrote {len(predictions)} predictions to {out}")

    canonical = "submission_lora_generative.jsonl"
    shutil.copyfile(out, canonical)
    log.info(f"copied predictions to {canonical} (canonical submission file)")

    if gold:
        log.info(f"wrote {n_errors} misclassified instance(s) to {error_out}")
        log.info("=== full submission (greedy + selectively self-consistency-revised) ===")
        log_evaluation(log, evaluate(gold, predictions))
    else:
        log.info("target has no gold labels -- skipping evaluation")


if __name__ == "__main__":
    main()
