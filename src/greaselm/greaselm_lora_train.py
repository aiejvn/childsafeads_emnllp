"""Trains GreaseLMLoRAClassifier (greaselm_lora_model.py) on the ChildSafeAds task:
LoRA-adapted encoder + a genuinely-exercised GreaseLM-style GNN reasoning component
(GATConvE + MInt over a small legal/flow/combined KG), one forward pass per training
instance (not per st1/st2/st3 candidate -- see greaselm_lora_model.py's module
docstring for why that redesign matters for tractability).

Standalone: does not use common/classification_data.py's Dataset/Collator (this model
tokenizes raw text internally, same convention greaselm_train.py already established)
or lora_train.py/greaselm_train.py's model-building code, but DOES reuse the generic
dev-eval helpers (common/predict_utils.py's threshold tuning / decode / post-processing)
since those only assume a model exposing st1/st2/st3 logits.

Usage (from repo root):
    .venv/bin/python3 src/greaselm/greaselm_lora_train.py public_data_dev/train.jsonl public_data_dev/dev.jsonl \\
        --kg-mode combined --epochs 10 --batch-size 8 --output-dir runs/greaselm_lora_combined
    .venv/bin/python3 src/greaselm/greaselm_lora_train.py public_data_dev/train.jsonl public_data_dev/dev.jsonl \\
        --kg-mode combined --sample-size 8 --epochs 1 --batch-size 2 --output-dir runs/greaselm_lora_smoke  # smoke test
"""
import argparse
import json
import os
import random
import sys
import time
from datetime import datetime

import torch
from peft import LoraConfig, TaskType, get_peft_model
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm
from transformers import get_linear_schedule_with_warmup

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # so `import greaselm`/`import common` resolve
from common.classification_data import multi_hot  # noqa: E402
from common.predict_utils import decode, multi_hot_matrix, save_thresholds, tune_per_label_thresholds  # noqa: E402
from common.train_utils import compute_pos_weight  # noqa: E402
from greaselm import (  # noqa: E402
    ST1_LABELS, ST2_LABELS, ST3_LABELS,
    evaluate, full_context, load_split, setup_logging,
)
from greaselm.greaselm_lora_model import (  # noqa: E402
    GreaseLMLoRAClassifier, count_trainable_parameters, unfreeze_non_lora,
)

ST1_INDEX = {label: i for i, label in enumerate(ST1_LABELS)}
ST2_INDEX = {label: i for i, label in enumerate(ST2_LABELS)}
ST3_INDEX = {label: i for i, label in enumerate(ST3_LABELS)}


class GreaseLMLoRADataset(Dataset):
    """Same shape as greaselm_train.py's GreaseLMDataset (raw texts + label tensors) --
    redefined here rather than imported, keeping this a self-contained new line (see
    module docstring); the two files are not allowed to diverge in ways that matter
    since this is trivial data prep, not model logic."""

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


@torch.no_grad()
def run_inference(model, loader) -> tuple:
    ids, st1_idx, st2_probs, st3_probs = [], [], [], []
    for batch in tqdm(loader, desc="predicting", leave=False):
        out = model(input_ids=batch["texts"])
        ids.extend(batch["instanceID"])
        st1_idx.append(out["st1_logits"].argmax(dim=-1).cpu())
        st2_probs.append(torch.sigmoid(out["st2_logits"]).cpu())
        st3_probs.append(torch.sigmoid(out["st3_logits"]).cpu())
    return ids, torch.cat(st1_idx), torch.cat(st2_probs), torch.cat(st3_probs)


def tune_and_decode(model, loader, instances: list, default_threshold: float = 0.5) -> tuple:
    _, st1_idx, st2_probs, st3_probs = run_inference(model, loader)
    st2_threshold = tune_per_label_thresholds(st2_probs, multi_hot_matrix(instances, "st2", ST2_LABELS), default=default_threshold)
    st3_threshold = tune_per_label_thresholds(st3_probs, multi_hot_matrix(instances, "st3", ST3_LABELS), default=default_threshold)
    predictions = decode(st1_idx, st2_probs, st3_probs, st2_threshold, st3_threshold)
    return predictions, st2_threshold, st3_threshold


def save_checkpoint(model, output_dir, config: dict) -> None:
    """Saves every `requires_grad=True` param by name (LoRA A/B + every manually
    unfrozen GreaseLM-side param: GATConvE, MInt, top-level attention pooler, trunk,
    heads, edge_encoder, emb_node_type, emb_score) as a flat state dict. NOT
    `PeftModel.save_pretrained` -- that only serializes LoRA adapter weights (plus
    `modules_to_save`, which this recipe deliberately doesn't use, see
    greaselm_lora_model.py), so it would silently drop the GNN/pooler/trunk/heads --
    most of what actually got trained here. Mirrors greaselm_train.py's
    save_checkpoint for the same reason (that model has the same PEFT-less-adapter
    mismatch, just without PEFT in the picture at all)."""
    os.makedirs(output_dir, exist_ok=True)
    trainable_state = {name: p.detach().cpu() for name, p in model.named_parameters() if p.requires_grad}
    torch.save(trainable_state, os.path.join(output_dir, "model.pt"))
    with open(os.path.join(output_dir, "config.json"), "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("train", help="training split, e.g. public_data_dev/train.jsonl")
    ap.add_argument("dev", help="dev split for per-epoch evaluation, e.g. public_data_dev/dev.jsonl")
    ap.add_argument("--kg-mode", choices=["legal", "flow", "combined"], default="combined")
    ap.add_argument("--base-model", default="FacebookAI/roberta-base")
    ap.add_argument("--max-length", type=int, default=256)
    ap.add_argument("--k", type=int, default=2, help="number of top cross-modal (GATConvE+MInt) layers")
    ap.add_argument("--concept-dim", type=int, default=100)
    ap.add_argument("--transe-epochs", type=int, default=200)
    ap.add_argument("--n-attention-head", type=int, default=2)
    ap.add_argument("--fc-dim", type=int, default=200)
    ap.add_argument("--n-fc-layer", type=int, default=1)
    ap.add_argument("--p-emb", type=float, default=0.2)
    ap.add_argument("--p-gnn", type=float, default=0.2)
    ap.add_argument("--p-fc", type=float, default=0.2)
    ap.add_argument("--ie-dim", type=int, default=200)
    ap.add_argument("--no-info-exchange", action="store_true", help="disable MInt fusion between LM and GNN (ablation)")
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--grad-accum-steps", type=int, default=1)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--warmup-ratio", type=float, default=0.06)
    ap.add_argument("--lora-r", type=int, default=64)
    ap.add_argument("--lora-alpha", type=int, default=128)
    ap.add_argument("--lora-dropout", type=float, default=0.1)
    ap.add_argument("--target-modules", default="query,value,key,dense", help="comma-separated module names to LoRA-adapt")
    ap.add_argument("--st2-loss-weight", type=float, default=1.0)
    ap.add_argument("--st3-loss-weight", type=float, default=2.0)
    ap.add_argument("--pos-weight", action="store_true", help="reweight st2/st3 BCE by inverse train-set frequency")
    ap.add_argument("--clip-norm", type=float, default=1.0, help="global grad-clip norm across ALL trainable params "
                     "(LoRA + GNN + trunk + heads together). Was hardcoded at 1.0; exposed as a flag after k=1 and "
                     "wider-GNN (concept_dim/n_attention_head/fc_dim) runs both collapsed to a near-constant output "
                     "with this hardcoded at 1.0 -- suspected the shared clip was starving effective gradient budget "
                     "once the mix of trainable-param gradient magnitudes shifted away from the k=2/default-width "
                     "combo that happened to train stably")
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--sample-size", type=int, default=None, help="sample N train and N dev instances (seeded smoke test)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--device", default=None)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--no-wandb", action="store_true")
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log = setup_logging("runs", "greaselm_lora_train", args.kg_mode, timestamp)
    log.info(f"config: {vars(args)} device={device}")

    try:
        import wandb
        wandb.init(
            project="childsafeads-emnllp", name=f"greaselm_lora_{args.kg_mode}_{timestamp}",
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

    train_loader = DataLoader(GreaseLMLoRADataset(train_instances), batch_size=args.batch_size, shuffle=True, collate_fn=collate)
    dev_loader = DataLoader(GreaseLMLoRADataset(dev_instances), batch_size=args.batch_size, shuffle=False, collate_fn=collate)

    t0 = time.time()
    base = GreaseLMLoRAClassifier(
        kg_mode=args.kg_mode, base_model_name=args.base_model, k=args.k, concept_dim=args.concept_dim,
        transe_epochs=args.transe_epochs, n_attention_head=args.n_attention_head, fc_dim=args.fc_dim,
        n_fc_layer=args.n_fc_layer, p_emb=args.p_emb, p_gnn=args.p_gnn, p_fc=args.p_fc, ie_dim=args.ie_dim,
        info_exchange=not args.no_info_exchange, max_length=args.max_length,
    )
    lora_config = LoraConfig(
        task_type=TaskType.FEATURE_EXTRACTION,
        target_modules=args.target_modules.split(","),
        r=args.lora_r, lora_alpha=args.lora_alpha, lora_dropout=args.lora_dropout,
    )
    model = get_peft_model(base, lora_config)
    unfreeze_non_lora(model)
    model = model.to(device)
    trainable_n, total_n = count_trainable_parameters(model)
    log.info(f"model built in {time.time() - t0:.1f}s; trainable params: {trainable_n}/{total_n} ({trainable_n / total_n:.2%})")

    st2_pos_weight = compute_pos_weight(train_instances, "st2", ST2_LABELS).to(device) if args.pos_weight else None
    st3_pos_weight = compute_pos_weight(train_instances, "st3", ST3_LABELS).to(device) if args.pos_weight else None

    trainable = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(trainable, lr=args.lr)
    steps_per_epoch = -(-len(train_loader) // args.grad_accum_steps)  # ceil div
    total_steps = steps_per_epoch * args.epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=int(args.warmup_ratio * total_steps), num_training_steps=total_steps
    )

    best_f1 = -1.0
    os.makedirs(args.output_dir, exist_ok=True)
    config = {
        "kg_mode": args.kg_mode, "base_model_name": args.base_model, "k": args.k, "concept_dim": args.concept_dim,
        "max_length": args.max_length, "n_attention_head": args.n_attention_head, "fc_dim": args.fc_dim,
        "n_fc_layer": args.n_fc_layer, "ie_dim": args.ie_dim, "info_exchange": not args.no_info_exchange,
        "lora_r": args.lora_r, "lora_alpha": args.lora_alpha, "target_modules": args.target_modules,
    }
    metrics = None
    st2_threshold = st3_threshold = None

    for epoch in range(args.epochs):
        model.train()
        running_loss = 0.0
        for step, batch in enumerate(tqdm(train_loader, desc=f"epoch {epoch + 1}/{args.epochs}")):
            out = model(
                input_ids=batch["texts"], st1_labels=batch["st1_labels"], st2_labels=batch["st2_labels"], st3_labels=batch["st3_labels"],
                st2_loss_weight=args.st2_loss_weight, st3_loss_weight=args.st3_loss_weight,
                st2_pos_weight=st2_pos_weight, st3_pos_weight=st3_pos_weight,
            )
            loss = out["loss"] / args.grad_accum_steps
            loss.backward()
            running_loss += out["loss"].item()
            if (step + 1) % args.grad_accum_steps == 0 or step + 1 == len(train_loader):
                torch.nn.utils.clip_grad_norm_(trainable, args.clip_norm)
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()
        train_loss = running_loss / len(train_loader)
        log.info(f"epoch {epoch + 1}: mean train loss = {train_loss:.4f}")
        log_payload = {"epoch": epoch + 1, "train_loss": train_loss}

        model.eval()
        preds, st2_threshold, st3_threshold = tune_and_decode(
            model, dev_loader, dev_instances, default_threshold=args.threshold,
        )
        gold = [inst["labels"] for inst in dev_instances]
        metrics = evaluate(gold, preds)
        log.info(f"epoch {epoch + 1} dev metrics: " + ", ".join(f"{k}={v:.3f}" for k, v in metrics.items()))
        log_payload.update({f"dev_{k}": v for k, v in metrics.items()})

        if metrics["mean_macro_f1"] > best_f1:
            best_f1 = metrics["mean_macro_f1"]
            best_dir = os.path.join(args.output_dir, "best")
            save_checkpoint(model, best_dir, config)
            save_thresholds(best_dir, st2_threshold, st3_threshold)
            log.info(f"epoch {epoch + 1}: new best mean_macro_f1={best_f1:.3f}, saved to {args.output_dir}/best")

        if wandb is not None:
            wandb.log(log_payload)

    last_dir = os.path.join(args.output_dir, "last")
    save_checkpoint(model, last_dir, config)
    if st2_threshold is not None:
        save_thresholds(last_dir, st2_threshold, st3_threshold)
    log.info(f"saved final epoch checkpoint to {args.output_dir}/last (best dev mean_macro_f1={best_f1:.3f})")
    if wandb is not None:
        if metrics is not None:
            wandb.summary.update({f"final_dev_{k}": v for k, v in metrics.items()})
        wandb.summary["best_mean_macro_f1"] = best_f1
        wandb.finish()


if __name__ == "__main__":
    main()
