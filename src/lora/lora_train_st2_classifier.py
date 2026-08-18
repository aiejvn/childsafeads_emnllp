"""Train a LoRA-adapted BERT-family encoder (roBERTa/legal-bert) as a dedicated
multi-label classifier over st2 ("what product category(ies) does this transcript's
commercial offer belong to?", one or more of the 12 ST2_LABELS).

Sibling of lora_train_st1_classifier.py, generalized from that script's single-label
5-way softmax/argmax setup to st2's multi-label taxonomy: BCE-with-logits in place of
CE (--pos-weight, common.train_utils.compute_pos_weight, in place of --class-weight),
per-label threshold tuning in place of argmax (common.predict_utils.
tune_per_label_thresholds, the same mechanism lora_train.py's joint st1/st2/st3 model
uses each dev epoch), and multi-label F1/oversampling that key off "does this
instance carry any rare label" rather than "is this instance's one label rare".
Carries over every other lora_train_st1_classifier.py feature: --context/--max-length/
--truncation-side/--page-token-budget, --test-holdout with a fresh-by-default random
split, best/last checkpoint saving, and wandb logging.

Usage (run from the repo root):
    python src/lora/lora_train_st2_classifier.py public_data_dev/train.jsonl public_data_dev/dev.jsonl \\
        --model FacebookAI/roberta-base --epochs 5 --batch-size 16 --pos-weight \\
        --oversample-rare-st2 3 --output-dir runs/lora_st2_classifier_roberta
    python src/lora/lora_train_st2_classifier.py public_data_dev/train.jsonl public_data_dev/dev.jsonl \\
        --sample-size 16 --epochs 1 --batch-size 4 --output-dir runs/lora_smoke  # smoke test

Saves the best-dev-macro-F1 adapter+head to <output-dir>/best (plus that epoch's dev
predictions.jsonl and tuned thresholds.json) and the final epoch's to <output-dir>/last.

Pass --test-holdout N (default 500, matching lora_train_st1_classifier.py) to carve a random
generalization-check split out of `train` -- evaluated once at the end with the best-dev
checkpoint, decoded with the best-dev thresholds (not re-tuned on the holdout, which
would leak its gold labels into threshold selection).
"""
import argparse
import json
import os
import random
import sys
from collections import Counter
from datetime import datetime

import torch
import torch.nn.functional as F
import wandb
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm
from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # so `import lora`/`common` resolve src/lora, src/common as packages
from peft import LoraConfig, PeftModel, TaskType, get_peft_model  # noqa: E402
from common.classification_data import ST2_INDEX, multi_hot  # noqa: E402
from common.predict_utils import multi_hot_matrix, tune_per_label_thresholds  # noqa: E402
from common.train_utils import compute_pos_weight  # noqa: E402
from lora import CONTEXT_CHOICES, ST2_LABELS, load_split, render_context, setup_logging  # noqa: E402


class ST2Dataset(Dataset):
    def __init__(self, instances: list, tokenizer, context: str = "full", max_length: int = 512,
                 page_token_budget: int = None):
        self.instances = instances
        self.tokenizer = tokenizer
        self.context = context
        self.max_length = max_length
        # Only meaningful for --context full: reserves this many tokens (kept from the PAGE
        # block's START, e.g. product title/category) instead of letting whole-string
        # truncation decide how much of PAGE survives -- see --page-token-budget's help text
        # for why plain --truncation-side left still loses the start of long PAGE blocks.
        self.page_token_budget = page_token_budget

    def __len__(self) -> int:
        return len(self.instances)

    def _encode_budgeted(self, text: str) -> tuple:
        prefix, marker, page = text.partition("\n\nPAGE (")
        page = marker[2:] + page  # restore "PAGE (" (marker's leading "\n\n" is the prefix/page separator, dropped)
        page_ids = self.tokenizer(page, add_special_tokens=False, truncation=False)["input_ids"]
        page_budget = min(self.page_token_budget, self.max_length - 2)
        page_ids = page_ids[:page_budget]  # keep PAGE's start
        prefix_budget = max(0, self.max_length - 2 - len(page_ids))
        prefix_ids = self.tokenizer(prefix, add_special_tokens=False, truncation=False)["input_ids"]
        prefix_ids = prefix_ids[-prefix_budget:] if prefix_budget else []  # keep prefix's end, closest to PAGE
        input_ids = [self.tokenizer.cls_token_id] + prefix_ids + page_ids + [self.tokenizer.sep_token_id]
        return input_ids, [1] * len(input_ids)

    def __getitem__(self, idx: int) -> dict:
        inst = self.instances[idx]
        text = render_context(inst, self.context)
        if self.page_token_budget and self.context == "full" and "\n\nPAGE (" in text:
            input_ids, attention_mask = self._encode_budgeted(text)
        else:
            enc = self.tokenizer(text, truncation=True, max_length=self.max_length)
            input_ids, attention_mask = enc["input_ids"], enc["attention_mask"]
        item = {"instanceID": inst["instanceID"], "input_ids": input_ids, "attention_mask": attention_mask}
        if inst.get("labels"):
            item["label"] = multi_hot(inst["labels"]["st2"], ST2_INDEX)
        return item


class Collator:
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def __call__(self, batch: list) -> dict:
        encodings = [{"input_ids": b["input_ids"], "attention_mask": b["attention_mask"]} for b in batch]
        padded = self.tokenizer.pad(encodings, return_tensors="pt")
        out = {"instanceID": [b["instanceID"] for b in batch], **padded}
        if "label" in batch[0]:
            out["labels"] = torch.tensor([b["label"] for b in batch], dtype=torch.float)
        return out


def label_frequency(instances: list, threshold_labels: list = ST2_LABELS) -> dict:
    n = len(instances)
    counts = Counter(flag for inst in instances for flag in inst["labels"]["st2"])
    return {label: counts.get(label, 0) / n for label in threshold_labels}


def compute_minority_labels(instances: list, threshold: float) -> set:
    """Labels whose train-set frequency is below `threshold` -- same rare-label definition
    oversample_rare/undersample_majority use, but computed once from the pristine
    pre-oversampling train split and held fixed for the run, so --oversample-rare-st2's
    duplication can't inflate a label's apparent frequency out of "minority" status
    partway through training. Mirrors lora_train_generative.py's --minority-select
    compute_minority_labels."""
    freq = label_frequency(instances)
    return {label for label in ST2_LABELS if freq[label] < threshold}


def minority_majority_f1(per_label_f1: dict, minority_labels: set) -> tuple:
    """Mean F1 over minority-labeled vs majority-labeled entries of `per_label_f1` -- surfaces
    whether a checkpoint that looks good on macro F1 is actually still failing the rare
    labels optimizing for overall accuracy tends to under-serve."""
    minority_scores = [f1 for label, f1 in per_label_f1.items() if label in minority_labels]
    majority_scores = [f1 for label, f1 in per_label_f1.items() if label not in minority_labels]
    minority_f1 = sum(minority_scores) / len(minority_scores) if minority_scores else float("nan")
    majority_f1 = sum(majority_scores) / len(majority_scores) if majority_scores else float("nan")
    return minority_f1, majority_f1


def oversample_rare(instances: list, factor: int, threshold: float = 0.05) -> tuple:
    """Duplicate every train instance that carries at least one gold st2 label under
    `threshold` train-frequency `factor` times over. Unlike st1's single-label version,
    an instance can carry several st2 labels at once, so "rare" is decided per-label and
    an instance qualifies for duplication if any one of its labels is rare. Returns
    (oversampled_instances, rare_labels) for logging."""
    if factor <= 1:
        return instances, set()
    freq = label_frequency(instances)
    rare = {label for label in ST2_LABELS if freq[label] < threshold}
    out = []
    for inst in instances:
        out.append(inst)
        if rare & set(inst["labels"]["st2"]):
            out += [inst] * (factor - 1)
    return out, rare


def undersample_majority(instances: list, factor: int, seed: int, threshold: float = 0.05) -> tuple:
    """Randomly drops instances whose gold st2 labels are ALL at/above `threshold`
    train-frequency (i.e. carry no rare label) down to 1/factor of that group's original
    count -- the complementary lever to oversample_rare. Instances carrying any rare
    label are always kept, since dropping them would double-penalize the rare classes
    this function isn't meant to touch. Same rare/majority split point (computed
    pre-undersampling) as oversample_rare uses. Returns (instances, majority_labels)."""
    if factor <= 1:
        return instances, set()
    freq = label_frequency(instances)
    majority = {label for label in ST2_LABELS if freq[label] >= threshold}
    majority_only = [inst for inst in instances if set(inst["labels"]["st2"]) <= majority]
    rare_bearing = [inst for inst in instances if not (set(inst["labels"]["st2"]) <= majority)]
    rng = random.Random(seed)
    keep_n = max(1, len(majority_only) // factor)
    majority_only = rng.sample(majority_only, keep_n)
    return rare_bearing + majority_only, majority


def build_model(model_path: str, lora_r: int, lora_alpha: int, lora_dropout: float, target_modules: list):
    model = AutoModelForSequenceClassification.from_pretrained(model_path, num_labels=len(ST2_LABELS))
    lora_config = LoraConfig(
        task_type=TaskType.SEQ_CLS,  # peft auto-adds the classifier head to modules_to_save for this task type
        target_modules=target_modules,
        r=lora_r,
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout,
    )
    return get_peft_model(model, lora_config)


def to_device(batch: dict, device: str) -> dict:
    return {k: (v.to(device) if torch.is_tensor(v) else v) for k, v in batch.items()}


@torch.no_grad()
def run_inference(model, loader, device) -> tuple:
    """Returns (instanceIDs, probs) over the whole split -- probs is sigmoid(logits),
    one probability per st2 label per instance (multi-label decoding, unlike st1's
    single argmax: which labels are "on" depends on per-label thresholds, tuned
    separately -- see tune_per_label_thresholds)."""
    ids, all_probs = [], []
    for batch in tqdm(loader, desc="predicting", leave=False):
        batch = to_device(batch, device)
        logits = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"]).logits
        ids.extend(batch["instanceID"])
        all_probs.append(torch.sigmoid(logits).cpu())
    return ids, torch.cat(all_probs)


def multilabel_metrics(probs: torch.Tensor, gold: torch.Tensor, thresholds: torch.Tensor) -> dict:
    """Per-label F1 (independent binary decision per label, thresholded) + their macro
    average, plus exact_match (subset accuracy: every label correct for the instance) --
    the multi-label analogue of lora_train_st1_classifier.py's multiclass_metrics."""
    pred = (probs >= thresholds).float()
    per_label_f1 = {}
    for j, label in enumerate(ST2_LABELS):
        tp = (pred[:, j] * gold[:, j]).sum().item()
        fp = (pred[:, j] * (1 - gold[:, j])).sum().item()
        fn = ((1 - pred[:, j]) * gold[:, j]).sum().item()
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        per_label_f1[label] = 2 * precision * recall / (precision + recall + 1e-9) if (tp + fp + fn) else 0.0
    exact_match = (pred == gold).all(dim=1).float().mean().item() if len(gold) else 0.0
    return {
        "exact_match": exact_match,
        "macro_f1": sum(per_label_f1.values()) / len(per_label_f1),
        "per_label_f1": per_label_f1,
    }


def evaluate_split(model, loader, instances: list, device: str, thresholds: torch.Tensor = None) -> tuple:
    """If `thresholds` is None, tunes per-label thresholds against this split's own gold
    labels (dev, per epoch). If given (the best-dev checkpoint's saved thresholds), reuses
    them as-is instead of re-tuning -- required for the test-holdout pass, since tuning on
    the holdout's own gold would leak it into threshold selection."""
    ids, probs = run_inference(model, loader, device)
    gold = multi_hot_matrix(instances, "st2", ST2_LABELS)
    if thresholds is None:
        thresholds = tune_per_label_thresholds(probs, gold)
    metrics = multilabel_metrics(probs, gold, thresholds)
    metrics["loss"] = F.binary_cross_entropy(probs.clamp(1e-6, 1 - 1e-6), gold).item()
    return metrics, ids, gold, (probs >= thresholds).float(), thresholds


def write_predictions(path: str, ids: list, gold: torch.Tensor, pred: torch.Tensor) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for iid, g, p in zip(ids, gold, pred):
            gold_labels = [ST2_LABELS[j] for j in range(len(ST2_LABELS)) if g[j] == 1]
            pred_labels = [ST2_LABELS[j] for j in range(len(ST2_LABELS)) if p[j] == 1]
            f.write(json.dumps({"instanceID": iid, "gold_st2": gold_labels, "pred_st2": pred_labels}) + "\n")


def save_thresholds(output_dir: str, thresholds: torch.Tensor) -> None:
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, "thresholds.json"), "w", encoding="utf-8") as f:
        json.dump({label: t for label, t in zip(ST2_LABELS, thresholds.tolist())}, f, indent=2)


def load_thresholds(checkpoint_dir: str):
    path = os.path.join(checkpoint_dir, "thresholds.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return torch.tensor([data[label] for label in ST2_LABELS])


def log_metrics(log, prefix: str, metrics: dict) -> None:
    scalar = {k: v for k, v in metrics.items() if k not in ("per_label_f1",)}
    log.info(f"{prefix}: " + ", ".join(f"{k}={v:.3f}" if isinstance(v, float) else f"{k}={v}" for k, v in scalar.items()))
    log.info(f"{prefix} per-label F1: " + ", ".join(f"{k}={v:.3f}" for k, v in metrics["per_label_f1"].items()))


def log_minority_f1(log, prefix: str, per_label_f1: dict, minority_labels: set) -> tuple:
    """Logs and returns (minority_f1, majority_f1) -- see minority_majority_f1. Split out from
    log_metrics since minority_labels is fixed for the run (computed once pre-oversampling),
    not part of the per-epoch metrics dict."""
    minority_f1, majority_f1 = minority_majority_f1(per_label_f1, minority_labels)
    log.info(f"{prefix}: minority_f1={minority_f1:.3f} majority_f1={majority_f1:.3f} "
             f"(minority labels: {sorted(minority_labels)})")
    return minority_f1, majority_f1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("train", help="training split, e.g. public_data_dev/train.jsonl")
    ap.add_argument("dev", help="dev split for per-epoch evaluation, e.g. public_data_dev/dev.jsonl")
    ap.add_argument("--model", default="FacebookAI/roberta-base")
    ap.add_argument(
        "--local", action="store_true",
        help="load --model from ./models/{model} instead of the HF hub (must already be downloaded there)",
    )
    ap.add_argument("--context", choices=CONTEXT_CHOICES, default="full",
                    help="which rungs of the instance the model sees, see lora_train.py's --context")
    ap.add_argument("--max-length", type=int, default=512)
    ap.add_argument("--truncation-side", choices=["left", "right"], default="right",
                     help="which end to cut when the rendered context exceeds --max-length. "
                     "HF default is 'right' (keep the start, drop the end) -- for --context full, "
                     "render_context puts TRANSCRIPT first and the product PAGE block last, so at "
                     "roberta-base's 512-token ceiling, right-truncation silently drops the PAGE "
                     "block entirely for most instances (measured: ~78%% of a 300-instance train "
                     "sample). 'left' keeps the end instead, preserving PAGE content at the cost "
                     "of the tail of a long transcript.")
    ap.add_argument("--page-token-budget", type=int, default=None, help="only meaningful for "
                     "--context full: instead of truncating the whole rendered string (which, "
                     "even with --truncation-side left, still cuts off PAGE's own start for "
                     "~42%% of instances when PAGE alone exceeds the remaining budget), reserve "
                     "this many tokens for PAGE specifically (kept from PAGE's start) and give "
                     "the rest to the transcript+metadata prefix (kept from the prefix's end, "
                     "closest to PAGE). Overrides --truncation-side for --context full instances "
                     "that contain a PAGE block; other context modes are unaffected.")
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--grad-accum-steps", type=int, default=1)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument(
        "--head-lr", type=float, default=None,
        help="separate LR for the randomly-initialized classifier head (modules_to_save); "
        "defaults to --lr (one param group) when omitted, same idea as lora_train_st1_classifier.py's --head-lr",
    )
    ap.add_argument("--warmup-ratio", type=float, default=0.06)
    ap.add_argument("--lora-r", type=int, default=8)
    ap.add_argument("--lora-alpha", type=int, default=16)
    ap.add_argument("--lora-dropout", type=float, default=0.1)
    ap.add_argument("--target-modules", default="query,value", help="comma-separated module names to LoRA-adapt")
    ap.add_argument("--pos-weight", action="store_true", help="reweight BCE by inverse train-set "
                     "frequency per st2 label (common.train_utils.compute_pos_weight) -- the "
                     "multi-label analogue of lora_train_st1_classifier.py's --class-weight")
    ap.add_argument(
        "--threshold", type=float, default=0.5,
        help="fallback per-label threshold for labels tune_per_label_thresholds can't tune "
        "(only bites on tiny --sample-size smoke tests where a label has zero gold positives)",
    )
    ap.add_argument("--oversample-rare-st2", type=int, default=1, help="duplicate each train instance "
                     "carrying a gold st2 label under 5%% train frequency this many times over. 1 "
                     "(default) disables oversampling; composes with --pos-weight (different "
                     "mechanisms -- this changes how often the model sees rare labels per epoch, "
                     "pos-weight scales their loss)")
    ap.add_argument("--undersample-majority-st2", type=int, default=1, help="randomly drop train "
                     "instances whose gold st2 labels are all at/above 5%% train frequency down to "
                     "1/factor of their original count -- complementary lever to "
                     "--oversample-rare-st2 (shrinks the majority-only instances instead of "
                     "duplicating the rare-bearing ones). 1 (default) disables it; can be combined "
                     "with --oversample-rare-st2")
    ap.add_argument("--oversample-first", action="store_true", help="when combining both levers, "
                     "apply --oversample-rare-st2 before --undersample-majority-st2 instead of the "
                     "default order (undersample majority-only first, then oversample rare-bearing) "
                     "-- changes both the exact instance counts and which labels cross the 5%% "
                     "rare/majority threshold, since that split is recomputed on whatever "
                     "distribution exists when each function runs")
    ap.add_argument("--minority-freq-threshold", type=float, default=0.05, help="labels under this "
                     "train frequency (computed once from the pristine pre-oversampling train split) "
                     "count as 'minority' for the per-epoch minority/majority F1 log split -- same "
                     "definition --oversample-rare-st2/--undersample-majority-st2 use, but tracked "
                     "independently of them so it stays meaningful even with both levers disabled")
    ap.add_argument("--sample-size", type=int, default=None, help="sample N train and N dev instances (seeded smoke test)")
    ap.add_argument("--test-holdout", type=int, default=500, help="hold out this many instances from "
                     "`train` (disjoint from what's trained on) for a one-time generalization check "
                     "with the best-dev checkpoint, evaluated after training finishes. 0 disables it.")
    ap.add_argument("--split-seed", type=int, default=None, help="seed for the train/test-holdout split; "
                     "omit for a fresh random split every run (logged either way)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--device", default=None, help="defaults to cuda if available, else cpu")
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--no-wandb", action="store_true", help="disable W&B logging")
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")

    model_path = args.model
    if args.local:
        local_path = os.path.join("models", args.model)
        if not os.path.isdir(local_path):
            raise FileNotFoundError(f"--local set but {local_path} does not exist")
        model_path = local_path

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log = setup_logging("runs", "lora_train_st2_classifier", args.model.replace("/", "_"), timestamp)
    log.info(f"config: {vars(args)} device={device}")

    wandb.init(
        project="childsafeads-emnllp",
        name=f"lora_st2_classifier_{args.model.replace('/', '_')}_{timestamp}",
        config=vars(args),
        mode="disabled" if args.no_wandb else "online",
    )

    train_instances = list(load_split(args.train))
    dev_instances = list(load_split(args.dev))

    test_holdout_instances = []
    if args.test_holdout:
        split_seed = args.split_seed if args.split_seed is not None else random.SystemRandom().randint(0, 2**31 - 1)
        shuffled = train_instances[:]
        random.Random(split_seed).shuffle(shuffled)
        test_holdout_instances = shuffled[:args.test_holdout]
        train_instances = shuffled[args.test_holdout:]
        log.info(f"train/test-holdout split (fresh random split every run unless --split-seed is "
                 f"pinned): split_seed={split_seed} train={len(train_instances)} "
                 f"test_holdout={len(test_holdout_instances)}")

    if args.sample_size:
        rng = random.Random(args.seed)
        train_instances = rng.sample(train_instances, min(args.sample_size, len(train_instances)))
        dev_instances = rng.sample(dev_instances, min(args.sample_size, len(dev_instances)))

    train_freq = label_frequency(train_instances)
    dev_dist = Counter(flag for inst in dev_instances for flag in inst["labels"]["st2"])
    log.info(f"train={len(train_instances)} dist=" + ", ".join(
        f"{label}={train_freq[label] * len(train_instances):.0f} ({train_freq[label]:.1%})" for label in ST2_LABELS))
    log.info(f"dev={len(dev_instances)} dist=" + ", ".join(f"{label}={dev_dist.get(label, 0)}" for label in ST2_LABELS))

    minority_labels = compute_minority_labels(train_instances, args.minority_freq_threshold)
    log.info(f"minority st2 labels (train freq < {args.minority_freq_threshold}, fixed for the run): "
             f"{sorted(minority_labels)}")

    def apply_undersample():
        nonlocal train_instances
        train_instances, majority_labels = undersample_majority(train_instances, args.undersample_majority_st2, args.seed)
        if args.undersample_majority_st2 > 1:
            log.info(f"undersampled majority-only st2 instances (labels {sorted(majority_labels)}) to "
                     f"1/{args.undersample_majority_st2}: train now {len(train_instances)} instances")

    def apply_oversample():
        nonlocal train_instances
        train_instances, rare_labels = oversample_rare(train_instances, args.oversample_rare_st2)
        if args.oversample_rare_st2 > 1:
            log.info(f"oversampled rare-bearing st2 instances (labels {sorted(rare_labels)}) "
                     f"{args.oversample_rare_st2}x: train now {len(train_instances)} instances")

    if args.oversample_first:
        apply_oversample()
        apply_undersample()
    else:
        apply_undersample()
        apply_oversample()

    pos_weight = compute_pos_weight(train_instances, "st2", ST2_LABELS).to(device) if args.pos_weight else None
    if pos_weight is not None:
        log.info("pos_weight: " + ", ".join(f"{label}={w:.3f}" for label, w in zip(ST2_LABELS, pos_weight.tolist())))

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    tokenizer.truncation_side = args.truncation_side
    train_ds = ST2Dataset(train_instances, tokenizer, args.context, args.max_length, args.page_token_budget)
    dev_ds = ST2Dataset(dev_instances, tokenizer, args.context, args.max_length, args.page_token_budget)
    collate = Collator(tokenizer)
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, collate_fn=collate)
    dev_loader = DataLoader(dev_ds, batch_size=args.batch_size, shuffle=False, collate_fn=collate)

    model = build_model(
        model_path, args.lora_r, args.lora_alpha, args.lora_dropout, args.target_modules.split(","),
    ).to(device)
    model.print_trainable_parameters()

    trainable = [p for p in model.parameters() if p.requires_grad]
    head_lr = args.head_lr if args.head_lr is not None else args.lr
    if head_lr == args.lr:
        optimizer = torch.optim.AdamW(trainable, lr=args.lr)
    else:
        head_params = [p for n, p in model.named_parameters() if p.requires_grad and "modules_to_save" in n]
        lora_params = [p for n, p in model.named_parameters() if p.requires_grad and "modules_to_save" not in n]
        optimizer = torch.optim.AdamW([
            {"params": lora_params, "lr": args.lr},
            {"params": head_params, "lr": head_lr},
        ])
        log.info(f"using separate LRs: lora={args.lr} head={head_lr} ({len(lora_params)} lora tensors, {len(head_params)} head tensors)")
    steps_per_epoch = -(-len(train_loader) // args.grad_accum_steps)  # ceil div
    total_steps = steps_per_epoch * args.epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=int(args.warmup_ratio * total_steps), num_training_steps=total_steps
    )

    best_f1 = -1.0
    thresholds = None
    os.makedirs(args.output_dir, exist_ok=True)
    for epoch in range(args.epochs):
        model.train()
        running_loss = 0.0
        for step, batch in enumerate(tqdm(train_loader, desc=f"epoch {epoch + 1}/{args.epochs}")):
            batch = to_device(batch, device)
            logits = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"]).logits
            loss = F.binary_cross_entropy_with_logits(logits, batch["labels"], pos_weight=pos_weight)
            (loss / args.grad_accum_steps).backward()
            running_loss += loss.item()
            if (step + 1) % args.grad_accum_steps == 0 or step + 1 == len(train_loader):
                torch.nn.utils.clip_grad_norm_(trainable, 1.0)
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()
        train_loss = running_loss / len(train_loader)
        log.info(f"epoch {epoch + 1}: mean train loss = {train_loss:.4f}")

        model.eval()
        metrics, ids, gold, pred, thresholds = evaluate_split(model, dev_loader, dev_instances, device)
        log_metrics(log, f"epoch {epoch + 1} dev metrics", metrics)
        minority_f1, majority_f1 = log_minority_f1(
            log, f"epoch {epoch + 1} dev minority/majority F1", metrics["per_label_f1"], minority_labels,
        )
        wandb.log({"epoch": epoch + 1, "train_loss": train_loss,
                   "dev_minority_f1": minority_f1, "dev_majority_f1": majority_f1,
                   **{f"dev_{k}": v for k, v in metrics.items() if k != "per_label_f1"}})

        if metrics["macro_f1"] > best_f1:
            best_f1 = metrics["macro_f1"]
            best_dir = os.path.join(args.output_dir, "best")
            model.save_pretrained(best_dir)
            save_thresholds(best_dir, thresholds)
            write_predictions(os.path.join(best_dir, "predictions.jsonl"), ids, gold, pred)
            log.info(f"epoch {epoch + 1}: new best macro_f1={best_f1:.3f}, saved to {args.output_dir}/best")

    last_dir = os.path.join(args.output_dir, "last")
    model.save_pretrained(last_dir)
    save_thresholds(last_dir, thresholds)
    write_predictions(os.path.join(last_dir, "predictions.jsonl"), ids, gold, pred)
    log.info(f"saved final epoch adapter to {args.output_dir}/last (best dev macro_f1={best_f1:.3f})")
    wandb.summary.update({f"final_dev_{k}": v for k, v in metrics.items() if k != "per_label_f1"})
    wandb.summary["best_macro_f1"] = best_f1
    wandb.summary["final_dev_minority_f1"], wandb.summary["final_dev_majority_f1"] = minority_f1, majority_f1

    if test_holdout_instances:
        best_dir = os.path.join(args.output_dir, "best")
        best_thresholds = load_thresholds(best_dir)
        log.info(f"reloading best-dev checkpoint from {best_dir} for the test-holdout pass "
                 f"(generalization check, not used for model selection); reusing its dev-tuned "
                 f"thresholds rather than re-tuning on the holdout, which would leak its gold labels")
        del model  # free the training model before loading a second full copy for holdout eval
        torch.cuda.empty_cache()
        test_base = AutoModelForSequenceClassification.from_pretrained(model_path, num_labels=len(ST2_LABELS))
        test_model = PeftModel.from_pretrained(test_base, best_dir).to(device)
        test_model.eval()
        test_loader = DataLoader(
            ST2Dataset(test_holdout_instances, tokenizer, args.context, args.max_length, args.page_token_budget),
            batch_size=args.batch_size, shuffle=False, collate_fn=collate,
        )
        test_metrics, test_ids, test_gold, test_pred, _ = evaluate_split(
            test_model, test_loader, test_holdout_instances, device, thresholds=best_thresholds,
        )
        del test_model
        torch.cuda.empty_cache()
        log_metrics(log, "test holdout metrics", test_metrics)
        test_minority_f1, test_majority_f1 = log_minority_f1(
            log, "test holdout minority/majority F1", test_metrics["per_label_f1"], minority_labels,
        )
        write_predictions(os.path.join(best_dir, "test_predictions.jsonl"), test_ids, test_gold, test_pred)
        wandb.summary.update({f"test_holdout_{k}": v for k, v in test_metrics.items() if k != "per_label_f1"})
        wandb.summary["test_holdout_minority_f1"], wandb.summary["test_holdout_majority_f1"] = test_minority_f1, test_majority_f1

    wandb.finish()


if __name__ == "__main__":
    main()
