"""Scoring (macro-F1, per-instance error diffs) and logging/diagnostics for st1/st2/st3
predictions.

Split out of baseline_gpt.py (which re-exports the names below for its existing external
consumers).
"""
import logging
import os
from collections import Counter
from typing import List

from st3_schemas import FAMILY_LABELS, ST1_LABELS, ST2_LABELS, ST3_FAMILY, ST3_LABELS

def setup_logging(log_dir: str, method: str, model: str, timestamp: str) -> logging.Logger:
    """Log everything (config, warnings, gold-label inventory, results) to console + a run file."""
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"run_{timestamp}_{method}_{model}.log")

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(threadName)s | %(message)s")
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(fmt)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"logging to {log_path}")
    return logger


def log_gold_label_inventory(logger: logging.Logger, gold: List[dict]) -> None:
    """Log the distinct gold labels observed in this run, one line per tier."""
    st1_seen = {g["st1"] for g in gold}
    st2_seen = {label for g in gold for label in g["st2"]}
    st3_seen = {label for g in gold for label in g["st3"]}
    logger.info("=== Distinct gold labels observed, by tier ===")
    logger.info(f"[ST1 - commercial type]     {sorted(st1_seen)}")
    logger.info(f"[ST2 - product category]    {sorted(st2_seen)}")
    logger.info(f"[ST3 - compliance flags]    {sorted(st3_seen)}")


# Dedicated copies of common/predict_utils.py's log_label_diagnostics/log_prediction_diagnostics
# (used by the LoRA/last_layer baselines) rather than importing them -- common/__init__.py does

# Dedicated copies of common/predict_utils.py's log_label_diagnostics/log_prediction_diagnostics
# (used by the LoRA/last_layer baselines) rather than importing them -- common/__init__.py does
# `from baseline_gpt import ...`, so importing back from common here would be circular.
def log_label_diagnostics(logger: logging.Logger, tier: str, gold_labels: list, pred_labels: list) -> None:
    """Logs `tier`'s label distribution -- how often each label appears in gold vs. how often
    the model predicts it, overall -- and the gold-label x predicted-label cross-product
    counts: the co-occurrence of every (gold, pred) label pair within the same instance,
    tallied over `zip(gold_labels, pred_labels)`. Surfaces systematic confusions (e.g. an
    inadequate_disclosure gold flag consistently landing next to an undisclosed_advertising
    prediction) and under/over-flagging bias that per-label F1 alone doesn't show.
    `gold_labels`/`pred_labels` are parallel lists, one label collection (a list, even a
    singleton one for a single-label tier) per instance."""
    gold_counts = Counter(f for flags in gold_labels for f in flags)
    pred_counts = Counter(f for flags in pred_labels for f in flags)
    labels = sorted(set(gold_counts) | set(pred_counts))
    logger.info(f"[{tier}] label distribution (gold / pred):")
    for label in labels:
        logger.info(f"  {label}: gold={gold_counts[label]}, pred={pred_counts[label]}")

    cross = Counter()
    for g_flags, p_flags in zip(gold_labels, pred_labels):
        for g in g_flags:
            for p in p_flags:
                cross[(g, p)] += 1
    logger.info(f"[{tier}] gold x pred cross-product counts (gold -> pred: count):")
    for (g, p), count in sorted(cross.items(), key=lambda kv: (-kv[1], kv[0])):
        logger.info(f"  {g} -> {p}: {count}")


def log_prediction_diagnostics(logger: logging.Logger, gold: list, pred: list,
                                tiers: tuple = ("st1", "st2", "st3")) -> None:
    """st1/st2/st3-shaped wrapper around `log_label_diagnostics`: `gold`/`pred` are the
    same {"st1": str, "st2": [...], "st3": [...]} dicts `evaluate()` uses. `tiers`
    restricts the diagnostics to the tiers `pred` actually carries (e.g. --st3-only)."""
    logger.info("=== Prediction diagnostics ===")
    for tier in tiers:
        gold_labels = [[g["st1"]] for g in gold] if tier == "st1" else [g[tier] for g in gold]
        pred_labels = [[p["st1"]] for p in pred] if tier == "st1" else [p[tier] for p in pred]
        log_label_diagnostics(logger, tier, gold_labels, pred_labels)


def macro_f1(y_true: List[list], y_pred: List[list], labels: List[str]) -> tuple:
    """Macro-F1 over multi-label sets, averaged across `labels`. Returns (macro_f1, per_label_f1)."""
    per_label = {}
    # Iterate over labels to avoid having to O(n^2) loop over every y_true and check if it is in y_pred (or vice-versa)
    for label in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if label in t and label in p)
        fp = sum(1 for t, p in zip(y_true, y_pred) if label not in t and label in p)
        fn = sum(1 for t, p in zip(y_true, y_pred) if label in t and label not in p)
        if tp == 0 and fp == 0 and fn == 0:
            continue  # label absent from both gold and predictions; skip like sklearn does
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall + 10e-6)
        per_label[label] = f1
    macro = sum(per_label.values()) / len(per_label) if per_label else 0.0
    return macro, per_label


def prediction_errors(gold: dict, pred: dict, tiers: tuple = ("st1", "st2", "st3")) -> dict:
    """Diff a prediction against gold, tier by tier. Returns {} if fully correct;
    otherwise one entry per wrong tier describing exactly what was wrong. `tiers`
    restricts the diff to the tiers `pred` actually carries (e.g. --st3-only)."""
    errors = {}
    if "st1" in tiers and pred["st1"] != gold["st1"]:
        errors["st1"] = {"gold": gold["st1"], "pred": pred["st1"]}
    for tier in ("st2", "st3"):
        if tier not in tiers:
            continue
        missing = sorted(set(gold[tier]) - set(pred[tier]))  # gold labels the prediction missed
        extra = sorted(set(pred[tier]) - set(gold[tier]))    # predicted labels not in gold
        if missing or extra:
            errors[tier] = {"missing": missing, "extra": extra}
    return errors


def evaluate(gold: List[dict], pred: List[dict], tiers: tuple = ("st1", "st2", "st3")) -> dict:
    """`tiers` restricts scoring to the tiers `pred` actually carries (e.g. --st3-only,
    where pred has no st1/st2 to score, and mean_macro_f1 -- a blend of all three -- is
    meaningless)."""
    metrics, per_label = {}, {}
    if "st1" in tiers:
        metrics["st1_macro_f1"], per_label["st1"] = macro_f1(
            [[g["st1"]] for g in gold], [[p["st1"]] for p in pred], ST1_LABELS
        )
    if "st2" in tiers:
        metrics["st2_macro_f1"], per_label["st2"] = macro_f1(
            [g["st2"] for g in gold], [p["st2"] for p in pred], ST2_LABELS
        )
    if "st3" in tiers:
        metrics["st3_macro_f1"], per_label["st3"] = macro_f1(
            [g["st3"] for g in gold], [p["st3"] for p in pred], ST3_LABELS
        )
        fam = lambda flags: [ST3_FAMILY[f] for f in flags]
        metrics["st3_family_macro_f1"], per_label["st3_family"] = macro_f1(
            [fam(g["st3"]) for g in gold], [fam(p["st3"]) for p in pred], FAMILY_LABELS
        )
    if set(("st1", "st2", "st3")) <= set(tiers):
        metrics["mean_macro_f1"] = (metrics["st1_macro_f1"] + metrics["st2_macro_f1"] + metrics["st3_macro_f1"]) / 3
    metrics["per_label_f1"] = per_label
    return metrics


# From repo root:
# python src/baseline_gpt.py public_data_dev/dev.jsonl --sample-size 10 
