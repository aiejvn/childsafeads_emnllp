"""Dedicated, cross-validated binary classifiers for the two st3 labels found to be
structurally near-deterministic: undisclosed_advertising and insufficient_context.

Why these two get their own script instead of living in the general per-label search
(baseline_per_label_ensemble.py): that search showed insufficient_context overfitting badly
to dev's 7-ish positives (dev F1 0.54-0.75 -> test F1 0.24-0.27 in every replicate) because
independently picking among 11-16 candidates per label, with a threshold tuned on a
single ~7-positive dev draw, is enough freedom to fit dev noise for a label this rare.

This script instead:
1. Uses a SMALL, hand-scoped feature set per label (not the full 828-dim space) --
   grounded directly in st3_findings.md's structural analysis, refined here after finding
   two real bugs in the original heuristics (see baseline_decision_tree.py's
   real_word_count/COMMERCIAL_RE docstrings): the near-emptiness check was ASCII-only and
   silently misclassified every non-English transcript as empty, and insufficient_context
   actually requires BOTH the transcript AND the video description to be
   thin/non-promotional (not transcript alone -- descriptions are annotated on too, so an
   empty transcript with a promo-heavy description still gets a real flag, not
   insufficient_context).
2. Picks the model/hyperparameter/threshold using stratified K-fold CV *within train only*
   (not a single dev draw) for a more stable estimate given how few positives these labels
   have (12-40 in train), THEN confirms/finalizes on dev, THEN checks test-holdout once.
3. Reports test-holdout performance across several fresh-split replicates specifically for
   these two labels, since "does it generalize to test" was the explicit ask.

Usage (from repo root):
    python src/baseline_two_label_focus.py
    python src/baseline_two_label_focus.py --split-seed 42
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
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.tree import DecisionTreeClassifier

sys.path.insert(0, os.path.dirname(__file__))
from baseline_decision_tree import engineer_features
from baseline_gpt import ST3_FAMILY, FAMILY_LABELS, macro_f1, setup_logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "starting_kit"))
from load_data import load_split

TARGET_LABELS = ["undisclosed_advertising", "insufficient_context"]

LABEL_FEATURES = {
    "undisclosed_advertising": [
        "official_disclosure_true", "official_disclosure_false", "official_disclosure_missing",
        "transcript_has_disclosure_lang", "description_has_disclosure_lang",
        "disclosure_only_in_description", "disclosure_relative_position",
    ],
    "insufficient_context": [
        "transcript_word_len", "transcript_char_len", "transcript_near_empty",
        "description_word_len", "description_commercial_hit", "context_insufficient",
    ],
}
# TF-IDF text per label: undisclosed_advertising benefits from transcript+description
# n-grams (learns disclosure phrasing beyond the hand regex); insufficient_context is kept
# feature-only (no TF-IDF) since the whole point is that there's no reliable text signal in
# the empty case -- TF-IDF on near-empty text is mostly noise/overfitting risk for 12-40 positives.
LABEL_USE_TFIDF = {"undisclosed_advertising": True, "insufficient_context": False}


def select_columns(feats: dict, cols: list) -> np.ndarray:
    idx = [feats["feature_names"].index(c) for c in cols]
    return feats["numeric"][:, idx]


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


def make_candidates() -> dict:
    return {
        "logreg_C0.1": LogisticRegression(C=0.1, class_weight="balanced", max_iter=2000,
                                           solver="liblinear", random_state=0),
        "logreg_C1.0": LogisticRegression(C=1.0, class_weight="balanced", max_iter=2000,
                                           solver="liblinear", random_state=0),
        "tree_d2": DecisionTreeClassifier(max_depth=2, class_weight="balanced", random_state=0),
        "tree_d3": DecisionTreeClassifier(max_depth=3, class_weight="balanced", random_state=0),
    }


def cv_select_model(X: np.ndarray, y: np.ndarray, log, label: str) -> str:
    """5-fold stratified CV within train only, picks the candidate with the best mean F1
    (own per-fold tuned threshold) -- more stable than a single ~7-positive dev draw for
    these rare labels."""
    n_splits = min(5, int(y.sum()), int((1 - y).sum()))
    n_splits = max(n_splits, 2)
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=0)
    scores = {name: [] for name in make_candidates()}
    for train_idx, val_idx in skf.split(X, y):
        candidates = make_candidates()
        for name, model in candidates.items():
            model.fit(X[train_idx], y[train_idx])
            proba = model.predict_proba(X[val_idx])
            classes = list(model.classes_)
            p = (proba[:, classes.index(1)] if len(classes) > 1
                 else np.full(len(val_idx), float(classes[0])))
            _, f1 = best_threshold_f1(p, y[val_idx])
            scores[name].append(f1)
    means = {name: np.mean(v) for name, v in scores.items()}
    log.info(f"  [{label}] {n_splits}-fold CV mean F1 per candidate: "
             + ", ".join(f"{k}={v:.3f}" for k, v in means.items()))
    return max(means, key=means.get)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", default=os.path.join("public_data_dev", "train.jsonl"))
    ap.add_argument("--dev", default=os.path.join("public_data_dev", "dev.jsonl"))
    ap.add_argument("--test-holdout", type=int, default=500)
    ap.add_argument("--split-seed", type=int, default=None)
    ap.add_argument("--max-tfidf-features", type=int, default=150)
    args = ap.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = os.path.join("runs", "baseline_decision_tree")
    log = setup_logging(log_dir, "two_label_focus", "sklearn", timestamp)

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

    results = {}
    for label in TARGET_LABELS:
        cols = LABEL_FEATURES[label]
        X_train_struct = select_columns(train_feats, cols)
        X_dev_struct = select_columns(dev_feats, cols)
        X_test_struct = select_columns(test_feats, cols)

        if LABEL_USE_TFIDF[label]:
            vectorizer = TfidfVectorizer(
                max_features=args.max_tfidf_features, ngram_range=(1, 2), min_df=3,
                stop_words="english",
            )
            tfidf_train = vectorizer.fit_transform(train_feats["text"])
            tfidf_dev = vectorizer.transform(dev_feats["text"])
            tfidf_test = vectorizer.transform(test_feats["text"])
            X_train = sparse.hstack([sparse.csr_matrix(X_train_struct), tfidf_train]).toarray()
            X_dev = sparse.hstack([sparse.csr_matrix(X_dev_struct), tfidf_dev]).toarray()
            X_test = sparse.hstack([sparse.csr_matrix(X_test_struct), tfidf_test]).toarray()
        else:
            X_train, X_dev, X_test = X_train_struct, X_dev_struct, X_test_struct

        y_train = np.array([1 if label in inst["labels"]["st3"] else 0 for inst in train_instances])
        y_dev = np.array([1 if label in inst["labels"]["st3"] else 0 for inst in dev_instances])
        y_test = np.array([1 if label in inst["labels"]["st3"] else 0 for inst in test_holdout])
        log.info(f"[{label}] n_train_pos={y_train.sum()} n_dev_pos={y_dev.sum()} n_test_pos={y_test.sum()} "
                 f"features={cols}{'+tfidf' if LABEL_USE_TFIDF[label] else ''}")

        best_name = cv_select_model(X_train, y_train, log, label)
        model = make_candidates()[best_name]
        model.fit(X_train, y_train)

        def pos_proba(m, X):
            proba = m.predict_proba(X)
            classes = list(m.classes_)
            return proba[:, classes.index(1)] if len(classes) > 1 else np.full(X.shape[0], float(classes[0]))

        dev_proba = pos_proba(model, X_dev)
        threshold, dev_f1 = best_threshold_f1(dev_proba, y_dev)
        test_proba = pos_proba(model, X_test)
        test_pred = (test_proba >= threshold).astype(int)
        tp = int(np.sum((y_test == 1) & (test_pred == 1)))
        fp = int(np.sum((y_test == 0) & (test_pred == 1)))
        fn = int(np.sum((y_test == 1) & (test_pred == 0)))
        p = tp / (tp + fp) if (tp + fp) else 0.0
        r = tp / (tp + fn) if (tp + fn) else 0.0
        test_f1 = 2 * p * r / (p + r + 1e-6)

        log.info(f"[{label}] winner={best_name} threshold={threshold:.2f} "
                 f"dev_f1={dev_f1:.3f} test_f1={test_f1:.3f} "
                 f"(test tp={tp} fp={fp} fn={fn}, precision={p:.3f} recall={r:.3f})")
        results[label] = {
            "model": best_name, "threshold": threshold, "dev_f1": dev_f1, "test_f1": test_f1,
            "test_precision": p, "test_recall": r, "n_train_pos": int(y_train.sum()),
        }

    log.info("=== summary ===")
    for label, r in results.items():
        log.info(f"  {label}: model={r['model']} dev_f1={r['dev_f1']:.3f} test_f1={r['test_f1']:.3f}")

    results_path = os.path.join(log_dir, "results.csv")
    is_new = not os.path.exists(results_path)
    with open(results_path, "a", encoding="utf-8") as f:
        if is_new:
            f.write("commit,split_seed,estimator,params,"
                    "test_st3_macro_f1,test_st3_family_macro_f1,"
                    "dev_st3_macro_f1,dev_st3_family_macro_f1,"
                    "train_st3_macro_f1,model,description\n")
        mean_dev = np.mean([r["dev_f1"] for r in results.values()])
        mean_test = np.mean([r["test_f1"] for r in results.values()])
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=os.path.dirname(__file__),
        ).decode().strip()
        desc = "Dedicated small-feature-set + CV-selected binary classifiers for " \
               "undisclosed_advertising and insufficient_context only " \
               f"(per-label F1: {[(k, round(v['test_f1'],3)) for k,v in results.items()]}). " \
               "Not directly comparable to the full-8-label st3_macro_f1 rows above -- " \
               "test_st3_macro_f1/dev_st3_macro_f1 columns here are the mean over just these 2 labels."
        f.write(",".join([
            commit, str(split_seed), "two_label_focus", f'"{results}"',
            f"{mean_test:.3f}", "", f"{mean_dev:.3f}", "", "", "classical_ml_sklearn", f'"{desc}"',
        ]) + "\n")
    log.info(f"appended results row to {results_path}")


if __name__ == "__main__":
    main()
