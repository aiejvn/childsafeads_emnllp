"""Greedy weight-souping for the generative Qwen LoRA adapters (see lora_train_generative.py,
e.g. the 8-18 --oversample-rare-st3/--grad-accum-steps/--lr sweep in
slurm_dispatch_qwen_generative.sh): merge several trained adapters into one by averaging their
effective weight deltas, so a single forward pass at inference gets (some of) the benefit of
an ensemble without paying for multiple generation passes.

Why greedy, not "average all of them": uniform averaging of every candidate regularly
underperforms the single best candidate -- a weak adapter folded into the average drags the
good one down, exactly the failure mode a naive soup risks. This script instead ranks
candidates by their own solo score on `target`, starts the pool with the single best one, and
only adds each remaining candidate if the resulting trial soup's score on `target` doesn't
drop (within --tolerance) -- so nothing enters the pool without being measured to help. If
nothing ever improves on the single best candidate, the pool stays size 1 and the "soup" is
just a faithful copy of that checkpoint; the script says so plainly rather than souping
something pointless.

Why `target` should not be the dev.jsonl a training run already used for per-epoch checkpoint
selection without caveat: it wasn't used for *this* decision before (which of several distinct
training runs to combine), so it's the best available shared, never-trained-on split across
every one of this repo's generative checkpoints (train.jsonl is out -- each checkpoint's own
train/test-holdout split is a different random draw unless --split-seed was pinned, so a
freshly-drawn slice of train.jsonl is contaminated for most checkpoints). But reusing dev.jsonl
for a second decision on top of the first is a mild statistical reuse worth being honest about,
not a clean held-out test in the textbook sense -- treat the final soup's dev score as a
promising signal, not a guarantee, and sanity-check the shipped submission the same way any
other checkpoint here gets sanity-checked (a dev-set solo pass before trusting it on the
unlabeled competition target).

How the merge itself works: for a LoRA adapter, PEFT's `add_weighted_adapter(...,
combination_type="cat")` concatenates each pool member's A/B matrices along the rank dimension
(after scaling B by its share of the average) rather than averaging A and B independently --
the latter is NOT equivalent to averaging the adapters' effective updates (mean(A)@mean(B)
introduces cross terms between different adapters' input/output projections that correspond to
nothing meaningful), so "cat" is the only combination_type that reconstructs the exact average
of the pool's effective weight deltas, at the cost of a larger resulting rank (sum of the pool
members' ranks, e.g. up to 6*8=48 here -- still tiny next to a 4B backbone). Confirm your
installed peft version supports combination_type="cat" (`pip show peft`) before trusting this
end to end; --combination-type is exposed so you can fall back to "linear" (an approximation,
not exact) if "cat" isn't available.

Usage (from repo root):
    python src/lora/lora_soup_generative.py public_data_dev/dev.jsonl \\
        --model Qwen/Qwen3-4B --lean-prompt --df-path emnllp-dialog-flow-dialog-flow.json \\
        --candidate $SCRATCH/8-18-qwen-improve/qwen3-4B-evalevery2/best \\
        --candidate $SCRATCH/8-18-qwen-improve/qwen3-4B-oversample-st3-3/best \\
        --candidate $SCRATCH/8-18-qwen-improve/qwen3-4B-gradaccum8/best \\
        --candidate $SCRATCH/8-18-qwen-improve/qwen3-4B-lr1e-4-dropout0.2/best \\
        --candidate $SCRATCH/8-18-qwen-improve/qwen3-4B-st3weight2-oversample3/best \\
        --candidate $SCRATCH/8-18-qwen-improve/qwen3-4B-combined/best \\
        --out $SCRATCH/8-18-qwen-improve/soup-greedy
"""
import argparse
import os
import shutil
import sys
from datetime import datetime

import torch
from torch.utils.data import DataLoader
from transformers import AutoTokenizer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # so `import lora` resolves src/lora as a package
from common.dialog_flow import df_pre_context  # noqa: E402
from common.predict_utils import log_evaluation  # noqa: E402
from lora import CONTEXT_CHOICES, SFT_TAXONOMY, SYSTEM_PROMPT, evaluate, load_split, setup_logging  # noqa: E402
from lora.lora_data import GenerativeCollator, GenerativeDataset  # noqa: E402
from lora.lora_generative import generate_predictions  # noqa: E402
from lora.lora_model import PARALLELISM_CHOICES, load_peft_model_causal  # noqa: E402


def score(model, loader, tokenizer, max_new_tokens, gold, label, log) -> float:
    _, preds = generate_predictions(model, loader, tokenizer, max_new_tokens)
    metrics = evaluate(gold, preds)
    log.info(f"{label}: mean_macro_f1={metrics['mean_macro_f1']:.3f} "
             f"(st1={metrics['st1_macro_f1']:.3f} st2={metrics['st2_macro_f1']:.3f} st3={metrics['st3_macro_f1']:.3f})")
    return metrics["mean_macro_f1"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", help="scored split to validate every solo/trial/final score against, e.g. "
                     "public_data_dev/dev.jsonl (must carry gold labels)")
    ap.add_argument("--model", default="Qwen/Qwen3-4B", help="must match every candidate's training run")
    ap.add_argument("--candidate", action="append", required=True,
                     help="adapter dir to consider, repeatable (>=2 required)")
    ap.add_argument("--context", choices=CONTEXT_CHOICES, default="full")
    ap.add_argument("--lean-prompt", action="store_true", help="must match every candidate's training run")
    ap.add_argument("--df-path", default=None, help="must match every candidate's training run")
    ap.add_argument("--max-length", type=int, default=4096)
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--max-new-tokens", type=int, default=128)
    ap.add_argument("--parallelism", choices=PARALLELISM_CHOICES, default="none")
    ap.add_argument("--tolerance", type=float, default=0.0, help="accept a candidate into the pool if the "
                     "trial soup's score is at least (running pool score - tolerance); 0.0 requires the "
                     "trial to not drop the score at all")
    ap.add_argument("--combination-type", default="cat", choices=("cat", "linear", "svd"),
                     help="see module docstring -- 'cat' is the exact combination, the others approximate")
    ap.add_argument("--sample-size", type=int, default=None, help="score on a random sample only (smoke test)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--device", default=None)
    ap.add_argument("--out", required=True, help="directory to write the merged adapter to -- usable "
                     "directly as --adapter-dir for lora_predict_generative.py")
    args = ap.parse_args()
    if len(args.candidate) < 2:
        ap.error(f"--candidate given {len(args.candidate)} time(s) -- need at least 2 to soup")

    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log = setup_logging("runs", "lora_soup_generative", args.model.replace("/", "_"), timestamp)
    log.info(f"candidates: {args.candidate}")

    model_path = os.path.join("models", args.model)
    if not os.path.isdir(model_path):
        raise FileNotFoundError(f"expected local model at {model_path!r} (from --model {args.model!r})")
    log.info(f"loading model/tokenizer from local path {model_path} (no remote download)")

    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"

    import random
    instances = list(load_split(args.target))
    if args.sample_size:
        instances = random.Random(args.seed).sample(instances, min(args.sample_size, len(instances)))
    if not all(inst.get("labels") for inst in instances):
        raise SystemExit(f"{args.target} has instances with no gold labels -- souping needs a scored split "
                          "to validate against, e.g. public_data_dev/dev.jsonl")
    gold = [inst["labels"] for inst in instances]

    system_prompt = SFT_TAXONOMY if args.lean_prompt else SYSTEM_PROMPT
    df_text = df_pre_context(args.df_path, lean=args.lean_prompt) if args.df_path else None
    log.info(f"system prompt: {'lean' if args.lean_prompt else 'full'} ({len(system_prompt)} chars)"
             + (f" + dialog flow from {args.df_path} ({len(df_text)} chars)" if df_text else ""))
    loader = DataLoader(
        GenerativeDataset(instances, tokenizer, args.context, args.max_length, system_prompt, df_text,
                          include_completion=False),
        batch_size=args.batch_size, shuffle=False, collate_fn=GenerativeCollator(tokenizer),
    )

    # --- load candidate 0 as the PeftModel's "default" adapter, then load the rest onto the
    #     same base via .load_adapter() -- one base in memory, switch active adapter with
    #     .set_adapter() instead of reloading the ~8GB base per candidate ---
    name_to_path = {"default": args.candidate[0]}
    model = load_peft_model_causal(model_path, args.candidate[0], device=device, parallelism=args.parallelism,
                                   local_files_only=True)
    if args.parallelism == "none":
        model = model.to(device)
    model.eval()
    for i, path in enumerate(args.candidate[1:], start=1):
        name = f"cand{i}"
        model.load_adapter(path, adapter_name=name)
        name_to_path[name] = path

    # --- rank every candidate by its own solo score on `target` ---
    solo_score = {}
    for name in name_to_path:
        model.set_adapter(name)
        solo_score[name] = score(model, loader, tokenizer, args.max_new_tokens, gold,
                                 f"solo [{name}] {name_to_path[name]}", log)
    ranked = sorted(name_to_path, key=lambda n: -solo_score[n])
    log.info("solo ranking: " + ", ".join(f"{n}={solo_score[n]:.3f}" for n in ranked))
    best_solo_name, best_solo_score = ranked[0], solo_score[ranked[0]]

    # --- greedy pool build: start from the best solo candidate, only add another candidate
    #     if the trial soup (equal-weight average of pool + candidate) doesn't drop the score ---
    pool = [best_solo_name]
    pool_score = best_solo_score
    for name in ranked[1:]:
        trial_pool = pool + [name]
        weights = [1.0 / len(trial_pool)] * len(trial_pool)
        model.base_model.add_weighted_adapter(trial_pool, weights, adapter_name="trial",
                                              combination_type=args.combination_type)
        model.set_adapter("trial")
        trial_score = score(model, loader, tokenizer, args.max_new_tokens, gold,
                            f"trial pool {trial_pool}", log)
        model.delete_adapter("trial")
        if trial_score >= pool_score - args.tolerance:
            log.info(f"accepted {name}: trial pool scored {trial_score:.3f} >= "
                     f"running pool's {pool_score:.3f} - tolerance {args.tolerance}")
            pool, pool_score = trial_pool, trial_score
        else:
            log.info(f"rejected {name}: trial pool scored {trial_score:.3f} < "
                     f"running pool's {pool_score:.3f} - tolerance {args.tolerance}")

    if len(pool) == 1:
        log.info(f"no candidate ever improved on the single best solo checkpoint ({best_solo_name}) -- "
                 "the 'soup' below is a faithful copy of it, not an actual merge")
    else:
        log.info(f"final pool: {pool} (equal-weight average), validated score={pool_score:.3f} vs. "
                 f"best solo score={best_solo_score:.3f} ({best_solo_name})")

    # --- build the final soup adapter, drop every other adapter so save_pretrained only
    #     persists this one, and normalize peft's output layout to <out>/adapter_config.json
    #     at the root regardless of whether this peft version nests it under the adapter name ---
    weights = [1.0 / len(pool)] * len(pool)
    model.base_model.add_weighted_adapter(pool, weights, adapter_name="soup", combination_type=args.combination_type)
    model.set_adapter("soup")
    for name in list(model.peft_config.keys()):
        if name != "soup":
            model.delete_adapter(name)
    os.makedirs(args.out, exist_ok=True)
    model.save_pretrained(args.out)
    nested = os.path.join(args.out, "soup")
    if not os.path.exists(os.path.join(args.out, "adapter_config.json")) and os.path.isdir(nested):
        for fname in os.listdir(nested):
            shutil.move(os.path.join(nested, fname), os.path.join(args.out, fname))
        os.rmdir(nested)
        log.info(f"normalized {args.out}/soup/* up to {args.out}/* (this peft version nests saved "
                 "adapters under their name)")
    log.info(f"wrote soup adapter ({pool}) to {args.out}")

    # --- reload the saved artifact fresh and re-score, to confirm what's on disk actually
    #     reproduces the in-memory soup's validated score before anyone trusts it ---
    del model
    torch.cuda.empty_cache()
    reloaded = load_peft_model_causal(model_path, args.out, device=device, parallelism=args.parallelism,
                                      local_files_only=True)
    if args.parallelism == "none":
        reloaded = reloaded.to(device)
    reloaded.eval()
    reload_score = score(reloaded, loader, tokenizer, args.max_new_tokens, gold,
                         f"reloaded-from-disk soup at {args.out}", log)
    if abs(reload_score - pool_score) > 1e-6:
        log.warning(f"reloaded soup scored {reload_score:.3f}, in-memory soup scored {pool_score:.3f} -- "
                    "these should match; don't trust this checkpoint until you understand why they differ")
    log.info(f"summary: best solo={best_solo_score:.3f} ({best_solo_name}) vs. soup={reload_score:.3f} "
             f"({pool}) -- {'soup wins' if reload_score > best_solo_score else 'best solo checkpoint wins, ship that instead'}")


if __name__ == "__main__":
    main()
