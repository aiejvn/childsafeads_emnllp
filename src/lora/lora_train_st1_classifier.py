"""Train a LoRA-adapted BERT-family encoder (roBERTa/legal-bert) as a full 5-way
classifier over st1 ("what kind of commercial offer, if any, does this transcript
present?"): digital_content_or_services / none / other / physical_goods /
physical_services.

Sibling of lora_train_st1_none.py, generalized from that script's binary none-vs-not
probe to the full st1 taxonomy. Motivation: the childsafeads_emnllp autoresearch
track (see lora_train_generative.py --st1-only) found a smaller, simpler
encoder+MLP classifier is worth trying against the generative-LLM approach for st1,
particularly because st1's minority classes (none/other, each well under 3%% of
train) are prone to being ignored by a model optimizing overall accuracy -- the
same "collapse to majority" failure mode lora_train_st1_none.py's docstring names
for its binary probe, generalized here to the full 5-way task via --class-weight
(inverse-train-frequency per-class CE weighting) and --oversample-rare-st1
(duplicate rare-class train instances), both optional but recommended together.

Usage (run from the repo root):
    python src/lora/lora_train_st1_classifier.py public_data_dev/train.jsonl public_data_dev/dev.jsonl \\
        --model FacebookAI/roberta-base --epochs 5 --batch-size 16 --class-weight \\
        --oversample-rare-st1 3 --output-dir runs/lora_st1_classifier_roberta
    python src/lora/lora_train_st1_classifier.py public_data_dev/train.jsonl public_data_dev/dev.jsonl \\
        --sample-size 16 --epochs 1 --batch-size 4 --output-dir runs/lora_smoke  # smoke test

Saves the best-dev-macro-F1 adapter+head to <output-dir>/best and the final epoch's
to <output-dir>/last, plus that epoch's dev predictions.jsonl.

Pass --test-holdout N (default 500, matching lora_train_generative.py) to carve a random
generalization-check split out of `train` -- evaluated once at the end with the best-dev
checkpoint.
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

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # so `import lora` resolves src/lora as a package
from peft import LoraConfig, PeftModel, TaskType, get_peft_model  # noqa: E402
from lora import CONTEXT_CHOICES, ST1_LABELS, load_split, render_context, setup_logging  # noqa: E402


class ST1Dataset(Dataset):
    def __init__(self, instances: list, tokenizer, context: str = "full", max_length: int = 512):
        self.instances = instances
        self.tokenizer = tokenizer
        self.context = context
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.instances)

    def __getitem__(self, idx: int) -> dict:
        inst = self.instances[idx]
        text = render_context(inst, self.context)
        enc = self.tokenizer(text, truncation=True, max_length=self.max_length)
        item = {"instanceID": inst["instanceID"], "input_ids": enc["input_ids"], "attention_mask": enc["attention_mask"]}
        if inst.get("labels"):
            item["label"] = ST1_LABELS.index(inst["labels"]["st1"])
        return item


class Collator:
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def __call__(self, batch: list) -> dict:
        encodings = [{"input_ids": b["input_ids"], "attention_mask": b["attention_mask"]} for b in batch]
        padded = self.tokenizer.pad(encodings, return_tensors="pt")
        out = {"instanceID": [b["instanceID"] for b in batch], **padded}
        if "label" in batch[0]:
            out["labels"] = torch.tensor([b["label"] for b in batch], dtype=torch.long)
        return out


def compute_class_weight(instances: list) -> torch.Tensor:
    """Inverse-train-frequency weight per st1 label (total / count[c], clamped to 50 like
    common.train_utils.compute_class_weight) -- without it, unweighted CE mostly ignores
    none/other (each well under 3%% of train) in favor of the two majority classes."""
    counts = torch.zeros(len(ST1_LABELS))
    for inst in instances:
        counts[ST1_LABELS.index(inst["labels"]["st1"])] += 1
    total = len(instances)
    return (total / counts.clamp(min=1)).clamp(max=50.0)


def oversample_rare(instances: list, factor: int, threshold: float = 0.05) -> tuple:
    """Duplicate every train instance whose gold st1 falls under `threshold` train-frequency
    `factor` times over -- same rare-label definition lora_train_generative.py's
    --oversample-rare-st1 uses, computed pre-oversampling so the rare set can't shift under
    its own duplication. Returns (oversampled_instances, rare_labels) for logging."""
    if factor <= 1:
        return instances, set()
    freq = Counter(inst["labels"]["st1"] for inst in instances)
    n = len(instances)
    rare = {label for label in ST1_LABELS if freq.get(label, 0) / n < threshold}
    out = []
    for inst in instances:
        out.append(inst)
        if inst["labels"]["st1"] in rare:
            out += [inst] * (factor - 1)
    return out, rare


def undersample_majority(instances: list, factor: int, seed: int, threshold: float = 0.05) -> tuple:
    """Randomly drop train instances whose gold st1 is at/above `threshold` train-frequency down
    to 1/factor of their original count -- the complementary lever to oversample_rare (shrinking
    the majority classes instead of duplicating the rare ones). Same rare/majority split point
    (computed pre-undersampling) as oversample_rare uses. Returns (instances, majority_labels)."""
    if factor <= 1:
        return instances, set()
    freq = Counter(inst["labels"]["st1"] for inst in instances)
    n = len(instances)
    majority = {label for label in ST1_LABELS if freq.get(label, 0) / n >= threshold}
    rng = random.Random(seed)
    out = []
    for label in ST1_LABELS:
        label_instances = [inst for inst in instances if inst["labels"]["st1"] == label]
        if label in majority:
            keep_n = max(1, len(label_instances) // factor)
            label_instances = rng.sample(label_instances, keep_n)
        out.extend(label_instances)
    return out, majority


def build_model(model_path: str, lora_r: int, lora_alpha: int, lora_dropout: float, target_modules: list):
    model = AutoModelForSequenceClassification.from_pretrained(model_path, num_labels=len(ST1_LABELS))
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
    """Returns (instanceIDs, pred_indices, logits) over the whole split -- pred_indices is
    argmax(logits, dim=-1), the model's single most-likely st1 label per instance (standard
    multi-class decoding, no per-class threshold needed unlike the binary none-probe's
    tuned-threshold approach)."""
    ids, preds, all_logits = [], [], []
    for batch in tqdm(loader, desc="predicting", leave=False):
        batch = to_device(batch, device)
        logits = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"]).logits
        ids.extend(batch["instanceID"])
        preds.append(logits.argmax(dim=-1).cpu())
        all_logits.append(logits.cpu())
    return ids, torch.cat(preds), torch.cat(all_logits)


def multiclass_metrics(gold: list, pred: list) -> dict:
    """Per-label F1 (one-vs-rest TP/FP/FN over ST1_LABELS) + their macro average --
    the same computation lora_train_generative.py's per-label st1 F1 logging does, kept
    self-contained here rather than importing sklearn."""
    per_label_f1 = {}
    for idx, label in enumerate(ST1_LABELS):
        tp = sum(1 for g, p in zip(gold, pred) if g == idx and p == idx)
        fp = sum(1 for g, p in zip(gold, pred) if g != idx and p == idx)
        fn = sum(1 for g, p in zip(gold, pred) if g == idx and p != idx)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        per_label_f1[label] = 2 * precision * recall / (precision + recall + 1e-9) if (tp + fp + fn) else 0.0
    accuracy = sum(1 for g, p in zip(gold, pred) if g == p) / len(gold) if gold else 0.0
    return {
        "accuracy": accuracy,
        "macro_f1": sum(per_label_f1.values()) / len(per_label_f1),
        "per_label_f1": per_label_f1,
    }


def evaluate_split(model, loader, instances: list, device: str) -> tuple:
    ids, pred, logits = run_inference(model, loader, device)
    gold = [ST1_LABELS.index(inst["labels"]["st1"]) for inst in instances]
    pred_list = pred.tolist()
    metrics = multiclass_metrics(gold, pred_list)
    metrics["loss"] = F.cross_entropy(logits, torch.tensor(gold, dtype=torch.long)).item()
    return metrics, ids, gold, pred_list


def write_predictions(path: str, ids: list, gold: list, pred: list) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for iid, g, p in zip(ids, gold, pred):
            f.write(json.dumps({"instanceID": iid, "gold_st1": ST1_LABELS[g], "pred_st1": ST1_LABELS[p]}) + "\n")


def log_metrics(log, prefix: str, metrics: dict) -> None:
    scalar = {k: v for k, v in metrics.items() if k not in ("per_label_f1",)}
    log.info(f"{prefix}: " + ", ".join(f"{k}={v:.3f}" if isinstance(v, float) else f"{k}={v}" for k, v in scalar.items()))
    log.info(f"{prefix} per-label F1: " + ", ".join(f"{k}={v:.3f}" for k, v in metrics["per_label_f1"].items()))


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
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--grad-accum-steps", type=int, default=1)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument(
        "--head-lr", type=float, default=None,
        help="separate LR for the randomly-initialized classifier head (modules_to_save); "
        "defaults to --lr (one param group) when omitted, same idea as lora_train_st1_none.py's --head-lr",
    )
    ap.add_argument("--warmup-ratio", type=float, default=0.06)
    ap.add_argument("--lora-r", type=int, default=8)
    ap.add_argument("--lora-alpha", type=int, default=16)
    ap.add_argument("--lora-dropout", type=float, default=0.1)
    ap.add_argument("--target-modules", default="query,value", help="comma-separated module names to LoRA-adapt")
    ap.add_argument("--class-weight", action="store_true", help="reweight CE by inverse train-set "
                     "frequency per st1 label -- recommended, since none/other are each under 3%% "
                     "of train and unweighted CE tends to collapse to only the majority classes")
    ap.add_argument("--oversample-rare-st1", type=int, default=1, help="duplicate each train instance "
                     "whose gold st1 is under 5%% train frequency this many times over. 1 (default) "
                     "disables oversampling; composes with --class-weight (different mechanisms -- "
                     "this changes how often the model sees rare examples per epoch, class-weight "
                     "scales their loss)")
    ap.add_argument("--undersample-majority-st1", type=int, default=1, help="randomly drop train "
                     "instances whose gold st1 is at/above 5%% train frequency down to 1/factor of "
                     "their original count -- complementary lever to --oversample-rare-st1 (shrinks "
                     "the majority classes instead of duplicating the rare ones). 1 (default) "
                     "disables it; can be combined with --oversample-rare-st1")
    ap.add_argument("--oversample-first", action="store_true", help="when combining both levers, "
                     "apply --oversample-rare-st1 before --undersample-majority-st1 instead of the "
                     "default order (undersample majority first, then oversample rare) -- changes "
                     "both the exact instance counts (oversample_rare's factor multiplies whatever "
                     "count the rare labels have at that point) and which labels cross the 5%% "
                     "rare/majority threshold, since that split is recomputed on whatever "
                     "distribution exists when each function runs")
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
    log = setup_logging("runs", "lora_train_st1_classifier", args.model.replace("/", "_"), timestamp)
    log.info(f"config: {vars(args)} device={device}")

    wandb.init(
        project="childsafeads-emnllp",
        name=f"lora_st1_classifier_{args.model.replace('/', '_')}_{timestamp}",
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

    train_dist = Counter(inst["labels"]["st1"] for inst in train_instances)
    dev_dist = Counter(inst["labels"]["st1"] for inst in dev_instances)
    log.info(f"train={len(train_instances)} dist=" + ", ".join(
        f"{label}={train_dist.get(label, 0)} ({train_dist.get(label, 0) / len(train_instances):.1%})" for label in ST1_LABELS))
    log.info(f"dev={len(dev_instances)} dist=" + ", ".join(f"{label}={dev_dist.get(label, 0)}" for label in ST1_LABELS))

    def apply_undersample():
        nonlocal train_instances
        train_instances, majority_labels = undersample_majority(train_instances, args.undersample_majority_st1, args.seed)
        if args.undersample_majority_st1 > 1:
            log.info(f"undersampled majority st1 labels {sorted(majority_labels)} to 1/{args.undersample_majority_st1}: "
                     f"train now {len(train_instances)} instances")

    def apply_oversample():
        nonlocal train_instances
        train_instances, rare_labels = oversample_rare(train_instances, args.oversample_rare_st1)
        if args.oversample_rare_st1 > 1:
            log.info(f"oversampled rare st1 labels {sorted(rare_labels)} {args.oversample_rare_st1}x: "
                     f"train now {len(train_instances)} instances")

    if args.oversample_first:
        apply_oversample()
        apply_undersample()
    else:
        apply_undersample()
        apply_oversample()

    class_weight = compute_class_weight(train_instances).to(device) if args.class_weight else None
    if class_weight is not None:
        log.info("class_weight: " + ", ".join(f"{label}={w:.3f}" for label, w in zip(ST1_LABELS, class_weight.tolist())))

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    tokenizer.truncation_side = args.truncation_side
    train_ds = ST1Dataset(train_instances, tokenizer, args.context, args.max_length)
    dev_ds = ST1Dataset(dev_instances, tokenizer, args.context, args.max_length)
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
    os.makedirs(args.output_dir, exist_ok=True)
    for epoch in range(args.epochs):
        model.train()
        running_loss = 0.0
        for step, batch in enumerate(tqdm(train_loader, desc=f"epoch {epoch + 1}/{args.epochs}")):
            batch = to_device(batch, device)
            logits = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"]).logits
            loss = F.cross_entropy(logits, batch["labels"], weight=class_weight)
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
        metrics, ids, gold, pred = evaluate_split(model, dev_loader, dev_instances, device)
        log_metrics(log, f"epoch {epoch + 1} dev metrics", metrics)
        wandb.log({"epoch": epoch + 1, "train_loss": train_loss,
                   **{f"dev_{k}": v for k, v in metrics.items() if k != "per_label_f1"}})

        if metrics["macro_f1"] > best_f1:
            best_f1 = metrics["macro_f1"]
            best_dir = os.path.join(args.output_dir, "best")
            model.save_pretrained(best_dir)
            write_predictions(os.path.join(best_dir, "predictions.jsonl"), ids, gold, pred)
            log.info(f"epoch {epoch + 1}: new best macro_f1={best_f1:.3f}, saved to {args.output_dir}/best")

    last_dir = os.path.join(args.output_dir, "last")
    model.save_pretrained(last_dir)
    write_predictions(os.path.join(last_dir, "predictions.jsonl"), ids, gold, pred)
    log.info(f"saved final epoch adapter to {args.output_dir}/last (best dev macro_f1={best_f1:.3f})")
    wandb.summary.update({f"final_dev_{k}": v for k, v in metrics.items() if k != "per_label_f1"})
    wandb.summary["best_macro_f1"] = best_f1

    if test_holdout_instances:
        best_dir = os.path.join(args.output_dir, "best")
        log.info(f"reloading best-dev checkpoint from {best_dir} for the test-holdout pass "
                 f"(generalization check, not used for model selection)")
        del model  # free the training model before loading a second full copy for holdout eval
        torch.cuda.empty_cache()
        test_base = AutoModelForSequenceClassification.from_pretrained(model_path, num_labels=len(ST1_LABELS))
        test_model = PeftModel.from_pretrained(test_base, best_dir).to(device)
        test_model.eval()
        test_loader = DataLoader(
            ST1Dataset(test_holdout_instances, tokenizer, args.context, args.max_length),
            batch_size=args.batch_size, shuffle=False, collate_fn=collate,
        )
        test_metrics, test_ids, test_gold, test_pred = evaluate_split(test_model, test_loader, test_holdout_instances, device)
        del test_model
        torch.cuda.empty_cache()
        log_metrics(log, "test holdout metrics", test_metrics)
        write_predictions(os.path.join(best_dir, "test_predictions.jsonl"), test_ids, test_gold, test_pred)
        wandb.summary.update({f"test_holdout_{k}": v for k, v in test_metrics.items() if k != "per_label_f1"})

    wandb.finish()


if __name__ == "__main__":
    main()
