"""Predict-time helpers shared by src/lora and src/last_layer's train/predict scripts:
batched inference, per-label threshold tuning, final decode (per-label thresholds +
`resolve_disclosure_conflict`/`st2_fallback` post-processing), and threshold
persistence -- both training scripts tune st2/st3 thresholds on the dev split each
epoch (per-label thresholds matter a lot for this task's macro F1) and save them
alongside the checkpoint; the predict scripts load them back by default instead of
falling back to a single flat --threshold.
"""
import json
import os

import torch
from tqdm import tqdm

from . import ST1_LABELS, ST2_LABELS, ST3_LABELS, sanitize_st3
from .train_utils import to_device

UNDISCLOSED, INADEQUATE = "undisclosed_advertising", "inadequate_disclosure"
UNDISCLOSED_IDX, INADEQUATE_IDX = ST3_LABELS.index(UNDISCLOSED), ST3_LABELS.index(INADEQUATE)


@torch.no_grad()
def run_inference(model, loader, device):
    """Returns (instanceIDs, st1_idx, st2_probs, st3_probs) stacked across the whole split."""
    ids, st1_idx, st2_probs, st3_probs = [], [], [], []
    for batch in tqdm(loader, desc="predicting"):
        batch = to_device(batch, device)
        out = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"])
        ids.extend(batch["instanceID"])
        st1_idx.append(out["st1_logits"].argmax(dim=-1).cpu())
        st2_probs.append(torch.sigmoid(out["st2_logits"]).cpu())
        st3_probs.append(torch.sigmoid(out["st3_logits"]).cpu())
    return ids, torch.cat(st1_idx), torch.cat(st2_probs), torch.cat(st3_probs)


def tune_per_label_thresholds(
    probs: torch.Tensor, gold_multihot: torch.Tensor, grid=None, default: float = 0.5,
) -> torch.Tensor:
    """Sweep a threshold grid per label, picking the one maximizing that label's F1.
    A label keeps `default` only if every grid point yields tp=fp=fn=0 -- i.e. the
    label has zero gold positives in this split AND the model's predicted probability
    never crosses even the lowest grid threshold (0.05) for anyone. With real
    train/dev splits every ST2/ST3 label has some gold positives, so this only bites
    in practice on small --sample-size smoke-test subsets where a rare label can be
    absent entirely."""
    grid = grid or [i / 20 for i in range(1, 20)]
    thresholds = torch.full((probs.shape[1],), default)
    for j in range(probs.shape[1]):
        best_f1, best_t = -1.0, default
        col_probs, col_gold = probs[:, j], gold_multihot[:, j]
        for t in grid:
            pred = (col_probs >= t).float()
            tp = (pred * col_gold).sum().item()
            fp = (pred * (1 - col_gold)).sum().item()
            fn = ((1 - pred) * col_gold).sum().item()
            if tp == 0 and fp == 0 and fn == 0:
                continue
            precision = tp / (tp + fp) if (tp + fp) else 0.0
            recall = tp / (tp + fn) if (tp + fn) else 0.0
            f1 = 2 * precision * recall / (precision + recall + 1e-6)
            if f1 > best_f1:
                best_f1, best_t = f1, t
        thresholds[j] = best_t
    return thresholds


def multi_hot_matrix(instances: list, labels_key: str, label_list: list) -> torch.Tensor:
    mat = torch.zeros(len(instances), len(label_list))
    for i, inst in enumerate(instances):
        for flag in inst["labels"][labels_key]:
            if flag in label_list:
                mat[i, label_list.index(flag)] = 1.0
    return mat


def resolve_disclosure_conflict(st3_flags: list, st3_prob_row: torch.Tensor) -> list:
    if UNDISCLOSED in st3_flags and INADEQUATE in st3_flags:
        drop = INADEQUATE if st3_prob_row[UNDISCLOSED_IDX] >= st3_prob_row[INADEQUATE_IDX] else UNDISCLOSED
        return [f for f in st3_flags if f != drop]
    return st3_flags


def st2_fallback(st2_flags: list, st2_prob_row: torch.Tensor) -> list:
    return st2_flags if st2_flags else [ST2_LABELS[int(st2_prob_row.argmax())]]


def decode(st1_idx, st2_probs, st3_probs, st2_threshold, st3_threshold) -> list:
    preds = []
    for i in range(len(st1_idx)):
        st2 = [ST2_LABELS[j] for j in range(len(ST2_LABELS)) if st2_probs[i, j] >= st2_threshold[j]]
        st3 = [ST3_LABELS[j] for j in range(len(ST3_LABELS)) if st3_probs[i, j] >= st3_threshold[j]]
        st3 = sanitize_st3(resolve_disclosure_conflict(st3, st3_probs[i]))
        st2 = st2_fallback(st2, st2_probs[i])
        preds.append({"st1": ST1_LABELS[st1_idx[i]], "st2": st2, "st3": st3})
    return preds


def tune_and_decode(model, loader, device, instances: list, default_threshold: float = 0.5) -> tuple:
    """Runs inference once, tunes per-label st2/st3 thresholds against `instances`' own
    gold labels, and decodes with the tuned thresholds. Used both by predict.py's
    --tune-thresholds-on and by the training scripts' per-epoch dev eval, since a single
    flat threshold is known to under/over-flag st2/st3 on this task. Returns
    (predictions, st2_threshold, st3_threshold)."""
    _, st1_idx, st2_probs, st3_probs = run_inference(model, loader, device)
    st2_threshold = tune_per_label_thresholds(
        st2_probs, multi_hot_matrix(instances, "st2", ST2_LABELS), default=default_threshold,
    )
    st3_threshold = tune_per_label_thresholds(
        st3_probs, multi_hot_matrix(instances, "st3", ST3_LABELS), default=default_threshold,
    )
    predictions = decode(st1_idx, st2_probs, st3_probs, st2_threshold, st3_threshold)
    return predictions, st2_threshold, st3_threshold


def save_thresholds(output_dir: str, st2_threshold: torch.Tensor, st3_threshold: torch.Tensor) -> None:
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, "thresholds.json"), "w", encoding="utf-8") as f:
        json.dump({"st2_threshold": st2_threshold.tolist(), "st3_threshold": st3_threshold.tolist()}, f, indent=2)


def load_thresholds(checkpoint_dir: str):
    """Returns (st2_threshold, st3_threshold) tensors if <checkpoint_dir>/thresholds.json
    exists (written by lora_train.py/last_layer_train.py), else (None, None)."""
    path = os.path.join(checkpoint_dir, "thresholds.json")
    if not os.path.exists(path):
        return None, None
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return torch.tensor(data["st2_threshold"]), torch.tensor(data["st3_threshold"])
