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
from collections import Counter

import torch
from tqdm import tqdm

from . import ST1_LABELS, ST2_LABELS, ST3_LABELS, prediction_errors, sanitize_st3
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


def write_submission(out_path: str, error_path: str, ids: list, instances: list, predictions: list) -> tuple:
    """Writes one prediction per line to out_path, matching baseline_gpt.py's submission
    format (`{"instanceID": ..., "st1": ..., "st2": [...], "st3": [...]}`); `ids`,
    `instances`, and `predictions` must all be in the same order. For instances that carry
    gold `labels` (train/dev, not the withheld test set), also writes any misclassified
    ones to error_path via `prediction_errors`. Returns (gold, n_errors): the collected
    gold label dicts (empty if `instances` carries none) and how many of them were
    misclassified, for the caller to log and/or feed to `evaluate`/`log_evaluation`."""
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    gold = []
    n_errors = 0
    with open(out_path, "w", encoding="utf-8") as f, open(error_path, "w", encoding="utf-8") as f_err:
        for iid, inst, pred in zip(ids, instances, predictions):
            f.write(json.dumps({"instanceID": iid, **pred}) + "\n")
            if inst.get("labels"):
                gold.append(inst["labels"])
                errors = prediction_errors(inst["labels"], pred)
                if errors:
                    n_errors += 1
                    f_err.write(json.dumps({
                        "instanceID": iid, "gold": inst["labels"], "pred": pred, "errors": errors,
                    }) + "\n")
    return gold, n_errors


def log_evaluation(log, metrics: dict) -> None:
    """Logs an `evaluate()` result the way baseline_gpt.py does: the scalar st1/st2/st3/
    st3_family/mean macro-F1 values, then each tier's per-label F1 breakdown."""
    log.info("Evaluation:")
    for k, v in metrics.items():
        if k == "per_label_f1":
            continue
        log.info(f"  {k}: {v:.3f}")
    for tier, per_label in metrics["per_label_f1"].items():
        log.info(f"  {tier} per-label F1: " + ", ".join(f"{l}={f:.3f}" for l, f in sorted(per_label.items())))


def log_label_diagnostics(log, tier: str, gold_labels: list, pred_labels: list) -> None:
    """Logs `tier`'s label distribution (gold vs. predicted counts) and the gold-label x
    predicted-label cross-product counts: the co-occurrence of every (gold, pred) label
    pair within the same instance/token, tallied over `zip(gold_labels, pred_labels)`.
    Surfaces systematic confusions (e.g. an inadequate_disclosure gold flag consistently
    landing next to an undisclosed_advertising prediction) and under/over-flagging bias
    that per-label F1 alone doesn't show. `gold_labels`/`pred_labels` are parallel lists,
    one label collection (a list, even a singleton one for a single-label tier) per
    instance/token."""
    gold_counts = Counter(f for flags in gold_labels for f in flags)
    pred_counts = Counter(f for flags in pred_labels for f in flags)
    labels = sorted(set(gold_counts) | set(pred_counts))
    log.info(f"[{tier}] label distribution (gold / pred):")
    for label in labels:
        log.info(f"  {label}: gold={gold_counts[label]}, pred={pred_counts[label]}")

    cross = Counter()
    for g_flags, p_flags in zip(gold_labels, pred_labels):
        for g in g_flags:
            for p in p_flags:
                cross[(g, p)] += 1
    log.info(f"[{tier}] gold x pred cross-product counts (gold -> pred: count):")
    for (g, p), count in sorted(cross.items(), key=lambda kv: (-kv[1], kv[0])):
        log.info(f"  {g} -> {p}: {count}")


def log_prediction_diagnostics(log, gold: list, pred: list, tiers: tuple = ("st1", "st2", "st3")) -> None:
    """st1/st2/st3-shaped wrapper around `log_label_diagnostics`: `gold`/`pred` are the
    same {"st1": str, "st2": [...], "st3": [...]} dicts `evaluate()`/`write_submission()`
    use. Run once per dev eval alongside `log_evaluation`."""
    log.info("=== Prediction diagnostics ===")
    for tier in tiers:
        gold_labels = [[g["st1"]] for g in gold] if tier == "st1" else [g[tier] for g in gold]
        pred_labels = [[p["st1"]] for p in pred] if tier == "st1" else [p[tier] for p in pred]
        log_label_diagnostics(log, tier, gold_labels, pred_labels)


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
