"""Per-label specialized model search + soft-voting ensemble for ST3.

Motivation: baseline_decision_tree.py found that 5 model families (tree, forest,
histgb, logreg, from-scratch MLP), all sharing ONE feature space and ONE model
choice across all 8 st3 labels, converge to st3_macro_f1 ~0.45-0.53 -- suggesting
a feature/data ceiling rather than a model-capacity one. This script tests two
remaining "try harder" angles per the user's request:

1. **Per-label model+feature-view selection**, not one global choice. Some labels
   are near-deterministic from a tiny feature subset (insufficient_context from
   transcript emptiness alone; undisclosed_advertising/inadequate_disclosure/
   no_flag from disclosure-related columns alone, see st3_findings.md) --
   drowning those in an 828-dim feature space (mostly TF-IDF irrelevant to them)
   may cost them accuracy relative to a small model fit on just the relevant
   columns. For every label, independently grid over {feature view} x {model
   family} and keep whichever wins on dev for THAT label.
2. **XGBoost** (not tried in baseline_decision_tree.py) and a **soft-voting
   ensemble** (mean predict_proba across the 5 "full"-view models) as two more
   candidates per label.

Same train/test-holdout methodology as the rest of the autoresearch tracks
(500 instances held out from train.jsonl at a fresh split_seed every run,
dev.jsonl for model/threshold selection). Results appended to
runs/baseline_decision_tree/results.csv (same schema as the other classical-ML
baselines) so everything stays comparable in one table.

Usage (from repo root):
    python src/baseline_per_label_ensemble.py
    python src/baseline_per_label_ensemble.py --split-seed 42
"""
import argparse
import json
import os
import random
import subprocess
import sys
from datetime import datetime

import numpy as np
from scipy import sparse
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.tree import DecisionTreeClassifier
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

sys.path.insert(0, os.path.dirname(__file__))
from baseline_decision_tree import (
    ST3_LABELS, build_matrix, engineer_features, evaluate_st3,
)
from baseline_decision_tree import TfidfVectorizer  # re-exported import, keeps one definition
from baseline_gpt import ST3_FAMILY, FAMILY_LABELS, macro_f1, sanitize_st3, setup_logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "starting_kit"))
from load_data import load_split

EMPTINESS_COLS = ["transcript_near_empty", "transcript_word_len", "transcript_char_len"]
DISCLOSURE_COLS = [
    "official_disclosure_true", "official_disclosure_false", "official_disclosure_missing",
    "transcript_has_disclosure_lang", "description_has_disclosure_lang",
    "disclosure_only_in_description", "disclosure_relative_position",
]
LABEL_SPECIAL_VIEW = {
    "insufficient_context": ("emptiness", EMPTINESS_COLS),
    "undisclosed_advertising": ("disclosure", DISCLOSURE_COLS),
    "inadequate_disclosure": ("disclosure", DISCLOSURE_COLS),
    "no_flag": ("disclosure", DISCLOSURE_COLS),
}


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=os.path.dirname(__file__),
        ).decode().strip()
    except Exception:
        return "unknown"


def make_models() -> dict:
    return {
        "tree": DecisionTreeClassifier(max_depth=6, min_samples_leaf=2, random_state=0),
        "forest": RandomForestClassifier(
            n_estimators=300, max_depth=None, min_samples_leaf=2, random_state=0, n_jobs=-1,
        ),
        "histgb": HistGradientBoostingClassifier(
            max_depth=6, min_samples_leaf=10, learning_rate=0.1, max_iter=200, random_state=0,
        ),
        "logreg": LogisticRegression(C=0.1, max_iter=2000, solver="liblinear", random_state=0),
        "xgboost": XGBClassifier(
            n_estimators=200, max_depth=4, learning_rate=0.1, eval_metric="logloss",
            random_state=0, n_jobs=-1, verbosity=0,
        ),
    }


def best_threshold_f1(proba: np.ndarray, y_true: np.ndarray) -> tuple:
    best_t, best_f1 = 0.5, -1.0
    for t in np.arange(0.05, 1.0, 0.05):
        y_pred = (proba >= t).astype(int)
        tp = int(np.sum((y_true == 1) & (y_pred == 1)))
        fp = int(np.sum((y_true == 0) & (y_pred == 1)))
        fn = int(np.sum((y_true == 1) & (y_pred == 0)))
        if tp == 0 and fp == 0 and fn == 0:
            continue
        p = tp / (tp + fp) if (tp + fp) else 0.0
        r = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * p * r / (p + r + 1e-6)
        if f1 > best_f1:
            best_f1, best_t = f1, t
    return best_t, best_f1


def fit_proba(model_name, model, X_train, y_train, sample_weight, X_dev, X_test, X_train_self):
    """Fits once on train, returns (proba_train, proba_dev, proba_test)."""
    densify = model_name == "histgb"
    Xt = X_train.toarray() if (densify and sparse.issparse(X_train)) else X_train
    Xd = X_dev.toarray() if (densify and sparse.issparse(X_dev)) else X_dev
    Xs = X_test.toarray() if (densify and sparse.issparse(X_test)) else X_test
    Xtt = X_train_self.toarray() if (densify and sparse.issparse(X_train_self)) else X_train_self
    model.fit(Xt, y_train, sample_weight=sample_weight)

    def pos_proba(X):
        proba = model.predict_proba(X)
        classes = list(model.classes_)
        if len(classes) == 1:
            return np.full(X.shape[0], float(classes[0]))
        return proba[:, classes.index(1)]

    return pos_proba(Xtt), pos_proba(Xd), pos_proba(Xs)


def numeric_view(feats: dict, cols: list) -> np.ndarray:
    idx = [feats["feature_names"].index(c) for c in cols]
    return feats["numeric"][:, idx]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", default=os.path.join("public_data_dev", "train.jsonl"))
    ap.add_argument("--dev", default=os.path.join("public_data_dev", "dev.jsonl"))
    ap.add_argument("--test-holdout", type=int, default=500)
    ap.add_argument("--split-seed", type=int, default=None,
                     help="fresh random seed every run unless pinned -- see feedback-rotating-test-holdout")
    ap.add_argument("--max-tfidf-features", type=int, default=800)
    args = ap.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = os.path.join("runs", "baseline_decision_tree")
    log = setup_logging(log_dir, "per_label_ensemble", "sklearn_xgboost", timestamp)

    split_seed = args.split_seed if args.split_seed is not None else random.SystemRandom().randint(0, 2**31 - 1)
    all_train = list(load_split(args.train))
    shuffled = all_train[:]
    random.Random(split_seed).shuffle(shuffled)
    test_holdout = shuffled[:args.test_holdout]
    train_instances = shuffled[args.test_holdout:]
    dev_instances = list(load_split(args.dev))
    log.info(f"split_seed={split_seed} train={len(train_instances)} "
             f"test_holdout={len(test_holdout)} dev={len(dev_instances)}")

    train_feats = engineer_features(train_instances)
    dev_feats = engineer_features(dev_instances)
    test_feats = engineer_features(test_holdout)

    vectorizer = TfidfVectorizer(
        max_features=args.max_tfidf_features, ngram_range=(1, 2), min_df=3, stop_words="english",
    )
    X_train_full = build_matrix(train_feats, vectorizer, fit=True)
    X_dev_full = build_matrix(dev_feats, vectorizer, fit=False)
    X_test_full = build_matrix(test_feats, vectorizer, fit=False)

    X_train_struct = sparse.csr_matrix(train_feats["numeric"])
    X_dev_struct = sparse.csr_matrix(dev_feats["numeric"])
    X_test_struct = sparse.csr_matrix(test_feats["numeric"])

    mlb = MultiLabelBinarizer(classes=ST3_LABELS)
    y_train = mlb.fit_transform([inst["labels"]["st3"] for inst in train_instances])
    y_dev = mlb.transform([inst["labels"]["st3"] for inst in dev_instances])
    y_test = mlb.transform([inst["labels"]["st3"] for inst in test_holdout])

    train_gold = [inst["labels"]["st3"] for inst in train_instances]
    dev_gold = [inst["labels"]["st3"] for inst in dev_instances]
    test_gold = [inst["labels"]["st3"] for inst in test_holdout]

    final_train_proba = np.zeros((len(train_instances), len(ST3_LABELS)))
    final_dev_proba = np.zeros((len(dev_instances), len(ST3_LABELS)))
    final_test_proba = np.zeros((len(test_holdout), len(ST3_LABELS)))
    final_thresholds = np.zeros(len(ST3_LABELS))
    winners = {}

    for label_idx, label in enumerate(ST3_LABELS):
        y_train_label = y_train[:, label_idx]
        y_dev_label = y_dev[:, label_idx]
        sample_weight = compute_sample_weight("balanced", y_train_label)
        n_pos = int(y_train_label.sum())

        views = [("full", X_train_full, X_dev_full, X_test_full),
                 ("structural", X_train_struct, X_dev_struct, X_test_struct)]
        if label in LABEL_SPECIAL_VIEW:
            view_name, cols = LABEL_SPECIAL_VIEW[label]
            views.append((view_name, sparse.csr_matrix(numeric_view(train_feats, cols)),
                          sparse.csr_matrix(numeric_view(dev_feats, cols)),
                          sparse.csr_matrix(numeric_view(test_feats, cols))))

        candidates = []
        full_view_probas = {}  # model_name -> (train, dev, test) proba, for the voting ensemble
        for view_name, Xtr, Xdv, Xte in views:
            for model_name, model in make_models().items():
                try:
                    p_train, p_dev, p_test = fit_proba(
                        model_name, model, Xtr, y_train_label, sample_weight, Xdv, Xte, Xtr,
                    )
                except Exception as e:
                    log.info(f"  [{label}] {view_name}/{model_name} failed: {e}")
                    continue
                t, f1 = best_threshold_f1(p_dev, y_dev_label)
                candidates.append({
                    "view": view_name, "model": model_name, "threshold": t, "dev_f1": f1,
                    "proba_train": p_train, "proba_dev": p_dev, "proba_test": p_test,
                })
                if view_name == "full":
                    full_view_probas[model_name] = (p_train, p_dev, p_test)

        if len(full_view_probas) == len(make_models()):
            vote_train = np.mean([v[0] for v in full_view_probas.values()], axis=0)
            vote_dev = np.mean([v[1] for v in full_view_probas.values()], axis=0)
            vote_test = np.mean([v[2] for v in full_view_probas.values()], axis=0)
            t, f1 = best_threshold_f1(vote_dev, y_dev_label)
            candidates.append({
                "view": "full", "model": "voting_ensemble", "threshold": t, "dev_f1": f1,
                "proba_train": vote_train, "proba_dev": vote_dev, "proba_test": vote_test,
            })

        best = max(candidates, key=lambda c: c["dev_f1"])
        winners[label] = {"view": best["view"], "model": best["model"], "dev_f1": best["dev_f1"]}
        log.info(f"[{label}] n_train_pos={n_pos} -> winner view={best['view']} "
                 f"model={best['model']} threshold={best['threshold']:.2f} dev_f1={best['dev_f1']:.3f} "
                 f"(candidates tried: {len(candidates)})")

        final_train_proba[:, label_idx] = best["proba_train"]
        final_dev_proba[:, label_idx] = best["proba_dev"]
        final_test_proba[:, label_idx] = best["proba_test"]
        final_thresholds[label_idx] = best["threshold"]

    def to_labels(proba):
        preds = []
        for row in proba:
            labels = [ST3_LABELS[i] for i, v in enumerate(row) if v >= final_thresholds[i]]
            preds.append(sanitize_st3(labels))
        return preds

    train_pred = to_labels(final_train_proba)
    dev_pred = to_labels(final_dev_proba)
    test_pred = to_labels(final_test_proba)
    train_metrics = evaluate_st3(train_gold, train_pred)
    dev_metrics = evaluate_st3(dev_gold, dev_pred)
    test_metrics = evaluate_st3(test_gold, test_pred)

    log.info("=== per-label winners ===")
    for label, w in winners.items():
        log.info(f"  {label}: view={w['view']} model={w['model']} dev_f1={w['dev_f1']:.3f}")
    log.info("=== train (fit) ===")
    log.info(f"st3_macro_f1={train_metrics['st3_macro_f1']:.3f} "
             f"st3_family_macro_f1={train_metrics['st3_family_macro_f1']:.3f}")
    log.info("=== dev (model + threshold selection) ===")
    log.info(f"st3_macro_f1={dev_metrics['st3_macro_f1']:.3f} "
             f"st3_family_macro_f1={dev_metrics['st3_family_macro_f1']:.3f}")
    for label in ST3_LABELS:
        log.info(f"  {label}: {dev_metrics['per_label_f1'].get(label, float('nan')):.3f}")
    log.info("=== test-holdout (final check) ===")
    log.info(f"st3_macro_f1={test_metrics['st3_macro_f1']:.3f} "
             f"st3_family_macro_f1={test_metrics['st3_family_macro_f1']:.3f}")
    for label in ST3_LABELS:
        log.info(f"  {label}: {test_metrics['per_label_f1'].get(label, float('nan')):.3f}")

    out_path = os.path.join("runs", f"submission_perlabel_{timestamp}.jsonl")
    with open(out_path, "w", encoding="utf-8") as f:
        for inst, pred in zip(test_holdout, test_pred):
            f.write(json.dumps({"instanceID": inst["instanceID"], "st3": pred}) + "\n")
    log.info(f"wrote test-holdout predictions to {out_path}")

    results_path = os.path.join(log_dir, "results.csv")
    is_new = not os.path.exists(results_path)
    with open(results_path, "a", encoding="utf-8") as f:
        if is_new:
            f.write("commit,split_seed,estimator,params,"
                    "test_st3_macro_f1,test_st3_family_macro_f1,"
                    "dev_st3_macro_f1,dev_st3_family_macro_f1,"
                    "train_st3_macro_f1,model,description\n")
        params = {label: f"{w['view']}/{w['model']}" for label, w in winners.items()}
        desc = "Per-label independent model+feature-view search (full/structural/label-specific " \
               "narrow view x tree/forest/histgb/logreg/xgboost/voting-ensemble), each label keeps " \
               "whichever combo wins its own dev F1, thresholds tuned per label on dev."
        f.write(",".join([
            git_commit(), str(split_seed), "per_label_ensemble", f'"{params}"',
            f"{test_metrics['st3_macro_f1']:.3f}", f"{test_metrics['st3_family_macro_f1']:.3f}",
            f"{dev_metrics['st3_macro_f1']:.3f}", f"{dev_metrics['st3_family_macro_f1']:.3f}",
            f"{train_metrics['st3_macro_f1']:.3f}", "classical_ml_sklearn", f'"{desc}"',
        ]) + "\n")
    log.info(f"appended results row to {results_path}")


if __name__ == "__main__":
    main()
