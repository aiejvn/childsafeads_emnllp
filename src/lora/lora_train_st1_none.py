"""Train a LoRA-adapted BERT-family encoder (roBERTa/legal-bert) as a binary
classifier for a single question: does this instance's gold st1 equal "none"
(no identifiable commercial offer) or not?

A narrower probe than lora_train.py's joint st1/st2/st3 head: "none" is one of
st1's two rarest values (well under 2%% of train, see lora_train_generative.py's
--oversample-rare-st1), so it is easy for a joint model to ignore in favor of
the majority classes. This script isolates it as its own balanced binary task.

Usage (run from the repo root):
    python src/lora/lora_train_st1_none.py public_data_dev/train.jsonl public_data_dev/dev.jsonl \\
        --model FacebookAI/roberta-base --epochs 5 --batch-size 16 --class-weight \\
        --output-dir runs/lora_st1_none_roberta
    python src/lora/lora_train_st1_none.py public_data_dev/train.jsonl public_data_dev/dev.jsonl \\
        --sample-size 16 --epochs 1 --batch-size 4 --output-dir runs/lora_smoke  # smoke test

Saves the best-dev-macro-F1 adapter+head to <output-dir>/best and the final epoch's
to <output-dir>/last, plus that epoch's dev predictions.jsonl and the tuned
none-class decision threshold (thresholds.json).
"""
import argparse
import json
import os
import random
import sys
from datetime import datetime

import torch
import torch.nn.functional as F
import wandb
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm
from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # so `import lora` resolves src/lora as a package
from peft import LoraConfig, TaskType, get_peft_model  # noqa: E402
from lora import CONTEXT_CHOICES, load_split, render_context, setup_logging  # noqa: E402

NONE_LABEL = "none"
CLASS_NAMES = ("not_none", "none")  # index 0 / 1, matches st1_binary_label below


def st1_binary_label(inst: dict) -> int:
    return 1 if inst["labels"]["st1"] == NONE_LABEL else 0


class BinaryDataset(Dataset):
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
            item["label"] = st1_binary_label(inst)
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
    """Inverse-train-frequency weight per class (total / count[c], clamped like
    common.train_utils.compute_class_weight) -- "none" is rare enough that
    unweighted CE mostly learns to always predict "not_none"."""
    counts = torch.zeros(2)
    for inst in instances:
        counts[st1_binary_label(inst)] += 1
    total = len(instances)
    return (total / counts.clamp(min=1)).clamp(max=50.0)


def oversample_none(instances: list, factor: int) -> list:
    if factor <= 1:
        return instances
    out = []
    for inst in instances:
        out.append(inst)
        if inst["labels"]["st1"] == NONE_LABEL:
            out += [inst] * (factor - 1)
    return out


def build_model(model_path: str, lora_r: int, lora_alpha: int, lora_dropout: float, target_modules: list):
    model = AutoModelForSequenceClassification.from_pretrained(model_path, num_labels=2)
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
    """Returns (instanceIDs, none_probs) over the whole split -- none_probs is
    softmax(logits)[:, 1], the model's probability that st1 == "none"."""
    ids, probs = [], []
    for batch in tqdm(loader, desc="predicting", leave=False):
        batch = to_device(batch, device)
        logits = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"]).logits
        ids.extend(batch["instanceID"])
        probs.append(F.softmax(logits, dim=-1)[:, 1].cpu())
    return ids, torch.cat(probs)


def tune_threshold(none_probs: torch.Tensor, gold: torch.Tensor, default: float = 0.5, grid=None) -> float:
    """Sweep a threshold grid on the none-probability, picking the one maximizing
    F1 for the "none" class -- same idea as common.predict_utils.tune_per_label_thresholds,
    specialized to this script's single binary label. Keeps `default` only if the
    split has no gold "none" instances at all (degenerate on small --sample-size runs)."""
    grid = grid or [i / 20 for i in range(1, 20)]
    best_f1, best_t = -1.0, default
    for t in grid:
        pred = (none_probs >= t).float()
        tp = (pred * gold).sum().item()
        fp = (pred * (1 - gold)).sum().item()
        fn = ((1 - pred) * gold).sum().item()
        if tp == 0 and fp == 0 and fn == 0:
            continue
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall + 1e-9)
        if f1 > best_f1:
            best_f1, best_t = f1, t
    return best_t


def binary_metrics(gold: list, pred: list) -> dict:
    tp = sum(1 for g, p in zip(gold, pred) if g == 1 and p == 1)
    fp = sum(1 for g, p in zip(gold, pred) if g == 0 and p == 1)
    fn = sum(1 for g, p in zip(gold, pred) if g == 1 and p == 0)
    tn = sum(1 for g, p in zip(gold, pred) if g == 0 and p == 0)
    none_precision = tp / (tp + fp) if (tp + fp) else 0.0
    none_recall = tp / (tp + fn) if (tp + fn) else 0.0
    none_f1 = 2 * none_precision * none_recall / (none_precision + none_recall + 1e-9)
    not_none_precision = tn / (tn + fn) if (tn + fn) else 0.0
    not_none_recall = tn / (tn + fp) if (tn + fp) else 0.0
    not_none_f1 = 2 * not_none_precision * not_none_recall / (not_none_precision + not_none_recall + 1e-9)
    accuracy = (tp + tn) / len(gold) if gold else 0.0
    return {
        "accuracy": accuracy,
        "none_precision": none_precision, "none_recall": none_recall, "none_f1": none_f1,
        "not_none_f1": not_none_f1,
        "macro_f1": (none_f1 + not_none_f1) / 2,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
    }


def write_predictions(path: str, ids: list, gold: list, pred: list, none_probs: torch.Tensor) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for iid, g, p, prob in zip(ids, gold, pred, none_probs.tolist()):
            f.write(json.dumps({
                "instanceID": iid,
                "gold_st1": CLASS_NAMES[g], "pred_st1": CLASS_NAMES[p], "none_prob": round(prob, 4),
            }) + "\n")


def save_threshold(output_dir: str, threshold: float) -> None:
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, "thresholds.json"), "w", encoding="utf-8") as f:
        json.dump({"none_threshold": threshold}, f, indent=2)


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
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--grad-accum-steps", type=int, default=1)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument(
        "--head-lr", type=float, default=None,
        help="separate LR for the randomly-initialized classifier head (modules_to_save); "
        "defaults to --lr (one param group) when omitted, same idea as lora_train.py's --head-lr",
    )
    ap.add_argument("--warmup-ratio", type=float, default=0.06)
    ap.add_argument("--lora-r", type=int, default=256)
    ap.add_argument("--lora-alpha", type=int, default=16)
    ap.add_argument("--lora-dropout", type=float, default=0.1)
    ap.add_argument("--target-modules", default="query,value", help="comma-separated module names to LoRA-adapt")
    ap.add_argument("--class-weight", action="store_true", help="reweight CE by inverse train-set "
                     "frequency of none/not_none -- recommended, since none is under 2%% of train "
                     "and unweighted CE tends to collapse to always predicting not_none")
    ap.add_argument("--oversample-none", type=int, default=1, help="duplicate each train instance "
                     "with gold st1==none this many times over. 1 (default) disables oversampling; "
                     "composes with --class-weight (different mechanisms -- this changes how often "
                     "the model sees none examples per epoch, class-weight scales their loss)")
    ap.add_argument("--threshold", type=float, default=0.5, help="fallback none-class probability "
                     "threshold for epochs where tune_threshold can't tune one (no gold none in dev)")
    ap.add_argument("--sample-size", type=int, default=None, help="sample N train and N dev instances (seeded smoke test)")
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
    log = setup_logging("runs", "lora_train_st1_none", args.model.replace("/", "_"), timestamp)
    log.info(f"config: {vars(args)} device={device}")

    wandb.init(
        project="childsafeads-emnllp",
        name=f"lora_st1_none_{args.model.replace('/', '_')}_{timestamp}",
        config=vars(args),
        mode="disabled" if args.no_wandb else "online",
    )

    train_instances = list(load_split(args.train))
    dev_instances = list(load_split(args.dev))
    if args.sample_size:
        rng = random.Random(args.seed)
        train_instances = rng.sample(train_instances, min(args.sample_size, len(train_instances)))
        dev_instances = rng.sample(dev_instances, min(args.sample_size, len(dev_instances)))

    train_none = sum(1 for inst in train_instances if inst["labels"]["st1"] == NONE_LABEL)
    dev_none = sum(1 for inst in dev_instances if inst["labels"]["st1"] == NONE_LABEL)
    log.info(f"train={len(train_instances)} (none={train_none}, {train_none / len(train_instances):.1%}) "
             f"dev={len(dev_instances)} (none={dev_none}, {dev_none / len(dev_instances):.1%})")

    train_instances = oversample_none(train_instances, args.oversample_none)
    if args.oversample_none > 1:
        log.info(f"oversampled none {args.oversample_none}x: train now {len(train_instances)} instances")

    class_weight = compute_class_weight(train_instances).to(device) if args.class_weight else None
    if class_weight is not None:
        log.info(f"class_weight: not_none={class_weight[0]:.3f} none={class_weight[1]:.3f}")

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    train_ds = BinaryDataset(train_instances, tokenizer, args.context, args.max_length)
    dev_ds = BinaryDataset(dev_instances, tokenizer, args.context, args.max_length)
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
        # peft's SEQ_CLS modules_to_save wraps the classifier head in a
        # ModulesToSaveWrapper, whose params are named *.classifier.modules_to_save.*
        # (verified against a built model) -- "modules_to_save" never appears in the
        # LoRA-adapted encoder param names (those are *.lora_A/lora_B.default.weight).
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
        ids, none_probs = run_inference(model, dev_loader, device)
        gold = [st1_binary_label(inst) for inst in dev_instances]
        gold_t = torch.tensor(gold, dtype=torch.float)
        threshold = tune_threshold(none_probs, gold_t, default=args.threshold)
        pred = (none_probs >= threshold).long().tolist()
        metrics = binary_metrics(gold, pred)
        log.info(f"epoch {epoch + 1} dev metrics (threshold={threshold:.2f}): "
                 + ", ".join(f"{k}={v:.3f}" if isinstance(v, float) else f"{k}={v}" for k, v in metrics.items()))
        wandb.log({"epoch": epoch + 1, "train_loss": train_loss, "none_threshold": threshold,
                   **{f"dev_{k}": v for k, v in metrics.items()}})

        if metrics["macro_f1"] > best_f1:
            best_f1 = metrics["macro_f1"]
            best_dir = os.path.join(args.output_dir, "best")
            model.save_pretrained(best_dir)
            save_threshold(best_dir, threshold)
            write_predictions(os.path.join(best_dir, "predictions.jsonl"), ids, gold, pred, none_probs)
            log.info(f"epoch {epoch + 1}: new best macro_f1={best_f1:.3f}, saved to {args.output_dir}/best")

    last_dir = os.path.join(args.output_dir, "last")
    model.save_pretrained(last_dir)
    save_threshold(last_dir, threshold)
    write_predictions(os.path.join(last_dir, "predictions.jsonl"), ids, gold, pred, none_probs)
    log.info(f"saved final epoch adapter to {args.output_dir}/last (best dev macro_f1={best_f1:.3f})")
    wandb.summary.update({f"final_dev_{k}": v for k, v in metrics.items()})
    wandb.summary["best_macro_f1"] = best_f1
    wandb.finish()


if __name__ == "__main__":
    main()
