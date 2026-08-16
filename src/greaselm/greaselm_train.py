"""Trains GreaseLMForClassification on the ChildSafeAds task. Standalone: does not use
common/classification_data.py's Dataset/Collator (GreaseLM's forward takes raw text
lists, not pre-tokenized ids -- tokenization happens per-candidate inside the model,
see greaselm_model.py) or lora_train.py/last_layer_train.py's model-building code, but
does reuse the same dev-eval helpers (common/predict_utils.py's threshold tuning /
decode / post-processing) since those are generic over any model exposing st1/st2/st3
logits.

Freezes all but the last --num-unfrozen-layers transformer blocks of the wrapped LM by
default, same rationale as last_layer_model.py's build_frozen_model -- but here it's
not optional-by-default: with n_ntype=4 QA-shaped scoring, ONE LMGNN forward = ONE
(text, candidate) pair, so one training instance costs 25 forward passes (5 st1 + 12
st2 + 8 st3 candidates). Full-finetuning all 12 roberta-base blocks through that many
forward passes per instance is not tractable in this session's compute budget; freezing
down to the last few blocks (still leaving every GATConvE/MInt/pooler/fc parameter
fully trainable, which is the actually-new part of this architecture) is a deliberate
tractability decision, not a claim that it's the right long-run training recipe -- see
scratchpad.md.

Usage (from repo root):
    python src/greaselm/greaselm_train.py public_data_dev/train.jsonl public_data_dev/dev.jsonl \\
        --kg-mode combined --epochs 200 --batch-size 4 --num-unfrozen-layers 2 --output-dir runs/greaselm_combined
    python src/greaselm/greaselm_train.py public_data_dev/train.jsonl public_data_dev/dev.jsonl \\
        --kg-mode legal --sample-size 8 --epochs 1 --batch-size 2 --output-dir runs/greaselm_smoke  # smoke test
"""
import argparse
import json
import os
import random
import sys
import time
from datetime import datetime

import torch
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # so `import greaselm`/`import common` resolve
from common.classification_data import multi_hot  # noqa: E402
from common.predict_utils import (  # noqa: E402
    decode, log_prediction_diagnostics, multi_hot_matrix, save_thresholds, tune_per_label_thresholds,
)
from common.train_utils import compute_pos_weight  # noqa: E402
from greaselm import (  # noqa: E402
    GreaseLMForClassification, ST1_LABELS, ST2_LABELS, ST3_LABELS,
    evaluate, full_context, load_split, setup_logging,
)

ST1_INDEX = {label: i for i, label in enumerate(ST1_LABELS)}
ST2_INDEX = {label: i for i, label in enumerate(ST2_LABELS)}
ST3_INDEX = {label: i for i, label in enumerate(ST3_LABELS)}


class GreaseLMDataset(Dataset):
    def __init__(self, instances: list):
        self.instances = instances

    def __len__(self) -> int:
        return len(self.instances)

    def __getitem__(self, idx: int) -> dict:
        inst = self.instances[idx]
        item = {"instanceID": inst["instanceID"], "text": full_context(inst)}
        labels = inst.get("labels")
        if labels:
            item["st1_label"] = ST1_INDEX[labels["st1"]]
            item["st2_label"] = multi_hot(labels["st2"], ST2_INDEX)
            item["st3_label"] = multi_hot(labels["st3"], ST3_INDEX)
        return item


def collate(batch: list) -> dict:
    out = {"instanceID": [b["instanceID"] for b in batch], "texts": [b["text"] for b in batch]}
    if "st1_label" in batch[0]:
        out["st1_labels"] = torch.tensor([b["st1_label"] for b in batch], dtype=torch.long)
        out["st2_labels"] = torch.tensor([b["st2_label"] for b in batch], dtype=torch.float)
        out["st3_labels"] = torch.tensor([b["st3_label"] for b in batch], dtype=torch.float)
    return out


def freeze_lm(model: GreaseLMForClassification, num_unfrozen_layers: int) -> None:
    """Freezes the wrapped LM's embeddings + all-but-last-N transformer blocks. Every
    other parameter (GATConvE layers, MInt/mint, emb_node_type, emb_score, pooler, fc,
    edge_encoder) stays trainable -- unaffected by this function, already
    `requires_grad=True` on a fresh model. concept_emb.emb is frozen separately, inside
    CustomizedEmbedding itself (freeze_ent_emb=True by default)."""
    lm = model.lmgnn.mp.lm
    for p in lm.parameters():
        p.requires_grad = False
    layers = lm.encoder.layer
    trailing = layers[-num_unfrozen_layers:] if num_unfrozen_layers > 0 else []
    for layer in trailing:
        for p in layer.parameters():
            p.requires_grad = True


def count_trainable_parameters(model) -> tuple:
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    return trainable, total


@torch.no_grad()
def run_inference(model, loader, device) -> tuple:
    ids, st1_idx, st2_probs, st3_probs = [], [], [], []
    for batch in tqdm(loader, desc="predicting", leave=False):
        out = model(batch["texts"])
        ids.extend(batch["instanceID"])
        st1_idx.append(out["st1_logits"].argmax(dim=-1).cpu())
        st2_probs.append(torch.sigmoid(out["st2_logits"]).cpu())
        st3_probs.append(torch.sigmoid(out["st3_logits"]).cpu())
    return ids, torch.cat(st1_idx), torch.cat(st2_probs), torch.cat(st3_probs)


def tune_and_decode(model, loader, device, instances: list, default_threshold: float = 0.5) -> tuple:
    _, st1_idx, st2_probs, st3_probs = run_inference(model, loader, device)
    st2_threshold = tune_per_label_thresholds(st2_probs, multi_hot_matrix(instances, "st2", ST2_LABELS), default=default_threshold)
    st3_threshold = tune_per_label_thresholds(st3_probs, multi_hot_matrix(instances, "st3", ST3_LABELS), default=default_threshold)
    predictions = decode(st1_idx, st2_probs, st3_probs, st2_threshold, st3_threshold)
    return predictions, st2_threshold, st3_threshold


def save_checkpoint(model, output_dir, config: dict) -> None:
    os.makedirs(output_dir, exist_ok=True)
    trainable_state = {name: p.detach().cpu() for name, p in model.named_parameters() if p.requires_grad}
    torch.save(trainable_state, os.path.join(output_dir, "model.pt"))
    with open(os.path.join(output_dir, "config.json"), "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("train", help="training split, e.g. public_data_dev/train.jsonl")
    ap.add_argument("dev", help="dev split for per-epoch evaluation, e.g. public_data_dev/dev.jsonl")
    ap.add_argument("--kg-mode", choices=["legal", "flow", "combined"], required=True)
    ap.add_argument("--base-model", default="FacebookAI/roberta-base")
    ap.add_argument("--max-length", type=int, default=256)
    ap.add_argument("--k", type=int, default=3, help="number of top cross-modal (GATConvE+MInt) layers")
    ap.add_argument("--concept-dim", type=int, default=100)
    ap.add_argument("--transe-epochs", type=int, default=200)
    ap.add_argument("--epochs", type=int, default=200)
    ap.add_argument("--batch-size", type=int, default=4, help="instances per batch; actual forward-pass batch is this x num_candidates per subtask")
    ap.add_argument("--grad-accum-steps", type=int, default=1)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--warmup-ratio", type=float, default=0.06)
    ap.add_argument("--num-unfrozen-layers", type=int, default=2, help="trailing LM blocks left trainable; see module docstring")
    ap.add_argument("--st2-loss-weight", type=float, default=1.0)
    ap.add_argument("--st3-loss-weight", type=float, default=1.0)
    ap.add_argument("--pos-weight", action="store_true")
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--sample-size", type=int, default=None)
    ap.add_argument("--eval-every", type=int, default=1, help="run dev eval every N epochs (dev eval is also 25x per instance -- expensive)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--device", default=None)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--no-wandb", action="store_true")
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log = setup_logging("runs", "greaselm_train", args.kg_mode, timestamp)
    log.info(f"config: {vars(args)} device={device}")

    try:
        import wandb
        wandb.init(
            project="childsafeads-emnllp", name=f"greaselm_{args.kg_mode}_{timestamp}",
            config=vars(args), mode="disabled" if args.no_wandb else "online",
        )
    except Exception as e:
        log.warning(f"wandb unavailable ({e}); continuing without it")
        wandb = None

    train_instances = list(load_split(args.train))
    dev_instances = list(load_split(args.dev))
    if args.sample_size:
        rng = random.Random(args.seed)
        train_instances = rng.sample(train_instances, min(args.sample_size, len(train_instances)))
        dev_instances = rng.sample(dev_instances, min(args.sample_size, len(dev_instances)))
    log.info(f"train={len(train_instances)} dev={len(dev_instances)}")

    train_loader = DataLoader(GreaseLMDataset(train_instances), batch_size=args.batch_size, shuffle=True, collate_fn=collate)
    dev_loader = DataLoader(GreaseLMDataset(dev_instances), batch_size=args.batch_size, shuffle=False, collate_fn=collate)

    t0 = time.time()
    model = GreaseLMForClassification(
        kg_mode=args.kg_mode, base_model_name=args.base_model, k=args.k, concept_dim=args.concept_dim,
        transe_epochs=args.transe_epochs, max_length=args.max_length,
    ).to(device)
    freeze_lm(model, args.num_unfrozen_layers)
    trainable_n, total_n = count_trainable_parameters(model)
    log.info(f"model built in {time.time() - t0:.1f}s; trainable params: {trainable_n}/{total_n} ({trainable_n / total_n:.2%})")

    st2_pos_weight = compute_pos_weight(train_instances, "st2", ST2_LABELS).to(device) if args.pos_weight else None
    st3_pos_weight = compute_pos_weight(train_instances, "st3", ST3_LABELS).to(device) if args.pos_weight else None

    trainable = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(trainable, lr=args.lr)
    steps_per_epoch = -(-len(train_loader) // args.grad_accum_steps)
    total_steps = steps_per_epoch * args.epochs
    from transformers import get_linear_schedule_with_warmup
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=int(args.warmup_ratio * total_steps), num_training_steps=total_steps
    )

    best_f1 = -1.0
    os.makedirs(args.output_dir, exist_ok=True)
    config = {
        "kg_mode": args.kg_mode, "base_model_name": args.base_model, "k": args.k,
        "concept_dim": args.concept_dim, "max_length": args.max_length, "num_unfrozen_layers": args.num_unfrozen_layers,
    }
    metrics = None

    for epoch in range(args.epochs):
        model.train()
        running_loss = 0.0
        for step, batch in enumerate(tqdm(train_loader, desc=f"epoch {epoch + 1}/{args.epochs}")):
            out = model(
                batch["texts"], st1_labels=batch["st1_labels"], st2_labels=batch["st2_labels"], st3_labels=batch["st3_labels"],
                st2_loss_weight=args.st2_loss_weight, st3_loss_weight=args.st3_loss_weight,
                st2_pos_weight=st2_pos_weight, st3_pos_weight=st3_pos_weight,
            )
            loss = out["loss"] / args.grad_accum_steps
            loss.backward()
            running_loss += out["loss"].item()
            if (step + 1) % args.grad_accum_steps == 0 or step + 1 == len(train_loader):
                torch.nn.utils.clip_grad_norm_(trainable, 1.0)
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()
        train_loss = running_loss / len(train_loader)
        log.info(f"epoch {epoch + 1}: mean train loss = {train_loss:.4f}")
        log_payload = {"epoch": epoch + 1, "train_loss": train_loss}

        if (epoch + 1) % args.eval_every == 0 or epoch + 1 == args.epochs:
            model.eval()
            preds, st2_threshold, st3_threshold = tune_and_decode(
                model, dev_loader, device, dev_instances, default_threshold=args.threshold,
            )
            gold = [inst["labels"] for inst in dev_instances]
            metrics = evaluate(gold, preds)
            scalar_metrics = {k: v for k, v in metrics.items() if k != "per_label_f1"}
            log.info(f"epoch {epoch + 1} dev metrics (tuned thresholds): " + ", ".join(f"{k}={v:.3f}" for k, v in scalar_metrics.items()))
            log_prediction_diagnostics(log, gold, preds)
            log_payload.update({f"dev_{k}": v for k, v in scalar_metrics.items()})

            if metrics["mean_macro_f1"] > best_f1:
                best_f1 = metrics["mean_macro_f1"]
                best_dir = os.path.join(args.output_dir, "best")
                save_checkpoint(model, best_dir, config)
                save_thresholds(best_dir, st2_threshold, st3_threshold)
                log.info(f"epoch {epoch + 1}: new best mean_macro_f1={best_f1:.3f}, saved to {args.output_dir}/best")

            # save "last" at every eval point (not just at the very end) so an
            # unattended multi-hour run always has a recoverable checkpoint if
            # interrupted mid-training, not only if it completes all --epochs.
            last_dir = os.path.join(args.output_dir, "last")
            save_checkpoint(model, last_dir, config)
            save_thresholds(last_dir, st2_threshold, st3_threshold)
            log.info(f"epoch {epoch + 1}: saved running checkpoint to {args.output_dir}/last")

        if wandb is not None:
            wandb.log(log_payload)

    log.info(f"training complete (best dev mean_macro_f1={best_f1:.3f})")
    if wandb is not None:
        if metrics is not None:
            wandb.summary.update({f"final_dev_{k}": v for k, v in metrics.items()})
        wandb.summary["best_mean_macro_f1"] = best_f1
        wandb.finish()


if __name__ == "__main__":
    main()
