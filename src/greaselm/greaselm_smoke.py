"""Standalone smoke test: loads a handful of real instances, builds one
GreaseLMForClassification per --kg-source, runs a few forward+backward steps on
--device, and confirms gradients reach both the LM's blocks and every
GATConvE/MInt/CustomizedEmbedding parameter. Bypasses
common/classification_data.py's Dataset/Collator on purpose (harness integration is
deferred, see the plan) -- reuses only load_split/full_context (plain data I/O).

Usage (from repo root):
    python src/greaselm/greaselm_smoke.py --kg-source combined --sample-size 4 --steps 2
"""
import argparse
import os
import random
import sys
import time

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))  # so `import greaselm` resolves like a sibling of src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # so `import greaselm`/`import common` resolve
from greaselm import GreaseLMForClassification, ST1_LABELS, ST2_LABELS, ST3_LABELS, full_context, load_split  # noqa: E402


def build_batch(instances):
    texts = [full_context(inst) for inst in instances]
    st1_labels = torch.tensor([ST1_LABELS.index(inst["labels"]["st1"]) for inst in instances], dtype=torch.long)
    st2_labels = torch.zeros(len(instances), len(ST2_LABELS))
    st3_labels = torch.zeros(len(instances), len(ST3_LABELS))
    for i, inst in enumerate(instances):
        for flag in inst["labels"]["st2"]:
            if flag in ST2_LABELS:
                st2_labels[i, ST2_LABELS.index(flag)] = 1.0
        for flag in inst["labels"]["st3"]:
            if flag in ST3_LABELS:
                st3_labels[i, ST3_LABELS.index(flag)] = 1.0
    return texts, st1_labels, st2_labels, st3_labels


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", default="public_data_dev/train.jsonl")
    ap.add_argument("--kg-source", choices=["legal", "flow", "combined"], default="combined")
    ap.add_argument("--base-model", default="FacebookAI/roberta-base")
    ap.add_argument("--sample-size", type=int, default=4)
    ap.add_argument("--steps", type=int, default=2)
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--concept-dim", type=int, default=100)
    ap.add_argument("--device", default=None)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")

    repo_root = os.path.join(os.path.dirname(__file__), "..", "..")
    train_path = os.path.join(repo_root, args.train)
    instances = list(load_split(train_path))
    rng = random.Random(args.seed)
    instances = rng.sample(instances, min(args.sample_size, len(instances)))
    print(f"[smoke:{args.kg_source}] {len(instances)} instances, device={device}")

    t0 = time.time()
    model = GreaseLMForClassification(
        kg_mode=args.kg_source, base_model_name=args.base_model, k=args.k, concept_dim=args.concept_dim,
    ).to(device)
    print(f"[smoke:{args.kg_source}] model built in {time.time() - t0:.1f}s, "
          f"n_real_nodes={model.n_real_nodes}, n_etype={model.base_edge_type.max().item() + 1 if model.base_edge_type.numel() else 0}")

    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-5)
    texts, st1_labels, st2_labels, st3_labels = build_batch(instances)

    for step in range(args.steps):
        t0 = time.time()
        model.train()
        out = model(texts, st1_labels=st1_labels, st2_labels=st2_labels, st3_labels=st3_labels)
        loss = out["loss"]
        optimizer.zero_grad()
        loss.backward()

        checked = {
            "gnn_layers": model.lmgnn.mp.gnn_layers_module.gnn_layers,
            "mint": model.lmgnn.mp.gnn_layers_module.mint,
            "concept_emb.emb": model.lmgnn.concept_emb.emb,
            "pooler": model.lmgnn.pooler,
            "fc": model.lmgnn.fc,
            "emb_node_type": model.lmgnn.mp.emb_node_type,
            "emb_score": model.lmgnn.mp.emb_score,
        }
        grad_report = {}
        for name, module in checked.items():
            grads = [p.grad for p in module.parameters() if p.requires_grad]
            has_grad = any(g is not None and torch.isfinite(g).all() and g.abs().sum() > 0 for g in grads) if grads else None
            grad_report[name] = has_grad

        optimizer.step()
        print(f"[smoke:{args.kg_source}] step {step + 1}/{args.steps} loss={loss.item():.4f} "
              f"time={time.time() - t0:.1f}s grads={grad_report}")

    print(f"[smoke:{args.kg_source}] OK")


if __name__ == "__main__":
    main()
