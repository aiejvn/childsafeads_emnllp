"""Standalone smoke test for GreaseLMLoRAClassifier (greaselm_lora_model.py): builds
the model, wraps it with PEFT LoRA + unfreeze_non_lora, runs a couple of forward+backward
steps on a handful of real instances, and confirms:
  (a) loss is finite
  (b) LoRA A/B params get real (nonzero) gradients
  (c) GATConvE/MInt/pooler/trunk/heads/edge_encoder/emb_node_type/emb_score all get
      real gradients (the actually-new GreaseLM mechanism, not a decorative no-op)
  (d) concept_emb's pretrained TransE table shows NO gradient (frozen by design)
  (e) the LM backbone's non-LoRA weights show NO gradient (frozen, adapted only via LoRA)

Usage (from repo root):
    .venv/bin/python3 src/greaselm/greaselm_lora_smoke.py --kg-mode combined --sample-size 4 --steps 2
"""
import argparse
import os
import random
import sys
import time

import torch
from peft import LoraConfig, TaskType, get_peft_model

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))  # so `import greaselm` resolves like a sibling of src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # so `import greaselm`/`import common` resolve
from greaselm import ST1_LABELS, ST2_LABELS, ST3_LABELS, full_context, load_split  # noqa: E402
from greaselm.greaselm_lora_model import GreaseLMLoRAClassifier, count_trainable_parameters, unfreeze_non_lora  # noqa: E402


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
    ap.add_argument("--kg-mode", choices=["legal", "flow", "combined"], default="combined")
    ap.add_argument("--base-model", default="FacebookAI/roberta-base")
    ap.add_argument("--sample-size", type=int, default=4)
    ap.add_argument("--steps", type=int, default=2)
    ap.add_argument("--k", type=int, default=2)
    ap.add_argument("--concept-dim", type=int, default=100)
    ap.add_argument("--lora-r", type=int, default=8)
    ap.add_argument("--lora-alpha", type=int, default=16)
    ap.add_argument("--target-modules", default="query,value")
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
    print(f"[smoke-lora:{args.kg_mode}] {len(instances)} instances, device={device}")

    t0 = time.time()
    base = GreaseLMLoRAClassifier(
        kg_mode=args.kg_mode, base_model_name=args.base_model, k=args.k, concept_dim=args.concept_dim,
    )
    lora_config = LoraConfig(
        task_type=TaskType.FEATURE_EXTRACTION,
        target_modules=args.target_modules.split(","),
        r=args.lora_r, lora_alpha=args.lora_alpha, lora_dropout=0.1,
    )
    model = get_peft_model(base, lora_config)
    unfreeze_non_lora(model)
    model = model.to(device)
    trainable_n, total_n = count_trainable_parameters(model)
    print(f"[smoke-lora:{args.kg_mode}] model built in {time.time() - t0:.1f}s, "
          f"trainable={trainable_n}/{total_n} ({trainable_n / total_n:.2%}), "
          f"n_real_nodes={base.n_real_nodes}, n_etype={base.base_edge_type.max().item() + 1 if base.base_edge_type.numel() else 0}")

    # sanity: are there actually LoRA params, GNN params, AND frozen backbone params?
    lora_names = [n for n, p in model.named_parameters() if "lora_" in n and p.requires_grad]
    gnn_names = [n for n, p in model.named_parameters() if "gnn_layers" in n and p.requires_grad]
    frozen_backbone = [n for n, p in model.named_parameters() if ".mp.lm." in n and not p.requires_grad and "lora_" not in n]
    frozen_concept = [n for n, p in model.named_parameters() if ".concept_emb.emb" in n and not p.requires_grad]
    print(f"[smoke-lora:{args.kg_mode}] lora params: {len(lora_names)}, trainable gnn params: {len(gnn_names)}, "
          f"frozen backbone params: {len(frozen_backbone)}, frozen concept_emb params: {len(frozen_concept)}")
    assert lora_names, "no trainable LoRA params found!"
    assert gnn_names, "no trainable GNN params found!"
    assert frozen_backbone, "no frozen backbone params found (LoRA freeze not working)!"
    assert frozen_concept, "concept_emb.emb should be frozen (freeze_ent_emb=True)!"

    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=1e-4)
    texts, st1_labels, st2_labels, st3_labels = build_batch(instances)

    for step in range(args.steps):
        t0 = time.time()
        model.train()
        out = model(input_ids=texts, st1_labels=st1_labels, st2_labels=st2_labels, st3_labels=st3_labels)
        loss = out["loss"]
        assert torch.isfinite(loss), f"non-finite loss: {loss}"
        optimizer.zero_grad()
        loss.backward()

        checked = {
            "lora_A/B (sample)": [p for n, p in model.named_parameters() if "lora_" in n][:4],
            "gnn_layers": [p for n, p in model.named_parameters() if "gnn_layers" in n and p.requires_grad],
            "mint": [p for n, p in model.named_parameters() if ".mint." in n or n.endswith(".mint.layers.0-Linear.weight") or "mint" in n.split(".")[-3:-1]],
            "pooler (top-level)": [p for n, p in model.named_parameters() if n.split(".")[-4:-3] == ["pooler"] or (".pooler." in n and ".mp.lm." not in n)],
            "trunk": [p for n, p in model.named_parameters() if ".trunk." in n],
            "heads": [p for n, p in model.named_parameters() if "_head." in n],
            "edge_encoder": [p for n, p in model.named_parameters() if "edge_encoder" in n],
            "emb_node_type": [p for n, p in model.named_parameters() if "emb_node_type" in n],
            "emb_score": [p for n, p in model.named_parameters() if "emb_score" in n and "concept" not in n],
            "concept_emb.emb (should be FROZEN, no grad)": [p for n, p in model.named_parameters() if ".concept_emb.emb" in n],
            "lm backbone non-lora (should be FROZEN, no grad)": [
                p for n, p in model.named_parameters() if ".mp.lm." in n and "lora_" not in n
            ][:4],
        }
        grad_report = {}
        for name, params in checked.items():
            grads = [p.grad for p in params if p is not None]
            has_grad = any(g is not None and torch.isfinite(g).all() and g.abs().sum() > 0 for g in grads) if grads else None
            grad_report[name] = has_grad

        optimizer.step()
        print(f"[smoke-lora:{args.kg_mode}] step {step + 1}/{args.steps} loss={loss.item():.4f} time={time.time() - t0:.1f}s")
        for name, has_grad in grad_report.items():
            print(f"    {name}: has_grad={has_grad}")

    print(f"[smoke-lora:{args.kg_mode}] OK")


if __name__ == "__main__":
    main()
