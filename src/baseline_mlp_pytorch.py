"""Feedforward-MLP "pure ML" baseline for ST3 -- trained from scratch (no pretrained
embeddings/transformers) on the exact same findings-derived features + TF-IDF block as
src/baseline_decision_tree.py, whose feature engineering this script imports directly.

Purpose: after grid-searching decision trees / random forests / gradient-boosted trees /
logistic regression, this checks whether a small neural net over the *same* feature space
can clear a materially higher st3 macro-F1 -- i.e. whether the ceiling seen so far is a
model-capacity limit (an MLP should close it) or a feature/data-quality limit (an MLP would
plateau at roughly the same place too).

Same train/test-holdout methodology as the rest of the autoresearch tracks: 500 instances
held out from train.jsonl at a fresh random split_seed every run, dev.jsonl used for
per-epoch model selection AND per-label threshold tuning (predict_proba sweep, same as
baseline_decision_tree.py), test-holdout scored once at the end with the selected
epoch+thresholds. Results appended to runs/baseline_decision_tree/results.csv (same schema)
so all "pure ML" families are directly comparable in one table.

Usage (from repo root):
    python src/baseline_mlp_pytorch.py
    python src/baseline_mlp_pytorch.py --split-seed 42 --epochs 300
"""
import argparse
import json
import os
import random
import sys
from datetime import datetime

import numpy as np
import torch
import torch.nn as nn

sys.path.insert(0, os.path.dirname(__file__))
from baseline_decision_tree import (
    ST3_LABELS, build_matrix, engineer_features, evaluate_st3, git_commit,
)
from baseline_gpt import sanitize_st3, setup_logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MultiLabelBinarizer, StandardScaler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "starting_kit"))
from load_data import load_split


class MLP(nn.Module):
    def __init__(self, in_dim: int, hidden: list, n_labels: int, dropout: float):
        super().__init__()
        layers = []
        prev = in_dim
        for h in hidden:
            layers += [nn.Linear(prev, h), nn.ReLU(), nn.Dropout(dropout)]
            prev = h
        layers.append(nn.Linear(prev, n_labels))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)


def tune_thresholds(proba: np.ndarray, y_true_bin: np.ndarray) -> np.ndarray:
    n_labels = proba.shape[1]
    thresholds = np.full(n_labels, 0.5)
    for i in range(n_labels):
        y_true = y_true_bin[:, i]
        best_t, best_f1 = 0.5, -1.0
        for t in np.arange(0.05, 1.0, 0.05):
            y_pred = (proba[:, i] >= t).astype(int)
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
        thresholds[i] = best_t
    return thresholds


def labels_from_proba(proba: np.ndarray, thresholds: np.ndarray, classes: list) -> list:
    preds = []
    for row in proba:
        labels = [classes[i] for i, v in enumerate(row) if v >= thresholds[i]]
        preds.append(sanitize_st3(labels))
    return preds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", default=os.path.join("public_data_dev", "train.jsonl"))
    ap.add_argument("--dev", default=os.path.join("public_data_dev", "dev.jsonl"))
    ap.add_argument("--test-holdout", type=int, default=500)
    ap.add_argument("--split-seed", type=int, default=None,
                     help="fresh random seed every run unless pinned -- see feedback-rotating-test-holdout")
    ap.add_argument("--max-tfidf-features", type=int, default=800)
    ap.add_argument("--hidden", default="256,128", help="comma-separated hidden layer sizes")
    ap.add_argument("--dropout", type=float, default=0.3)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--weight-decay", type=float, default=1e-4)
    ap.add_argument("--epochs", type=int, default=300)
    ap.add_argument("--eval-every", type=int, default=5)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--device", default=None)
    args = ap.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = os.path.join("runs", "baseline_decision_tree")
    log = setup_logging(log_dir, "mlp_pytorch", "scratch", timestamp)

    torch.manual_seed(args.seed)
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    log.info(f"device={device}")

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
    X_train = build_matrix(train_feats, vectorizer, fit=True).toarray()
    X_dev = build_matrix(dev_feats, vectorizer, fit=False).toarray()
    X_test = build_matrix(test_feats, vectorizer, fit=False).toarray()

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_dev = scaler.transform(X_dev)
    X_test = scaler.transform(X_test)

    mlb = MultiLabelBinarizer(classes=ST3_LABELS)
    y_train = mlb.fit_transform([inst["labels"]["st3"] for inst in train_instances]).astype(np.float32)
    y_dev = mlb.transform([inst["labels"]["st3"] for inst in dev_instances])

    train_gold = [inst["labels"]["st3"] for inst in train_instances]
    dev_gold = [inst["labels"]["st3"] for inst in dev_instances]
    test_gold = [inst["labels"]["st3"] for inst in test_holdout]

    pos_counts = y_train.sum(axis=0)
    neg_counts = len(y_train) - pos_counts
    pos_weight = torch.tensor(np.clip(neg_counts / np.clip(pos_counts, 1, None), 1.0, 50.0),
                               dtype=torch.float32, device=device)
    log.info(f"pos_weight per label: {dict(zip(ST3_LABELS, pos_weight.cpu().numpy().round(2).tolist()))}")

    X_train_t = torch.tensor(X_train, dtype=torch.float32, device=device)
    y_train_t = torch.tensor(y_train, dtype=torch.float32, device=device)
    X_dev_t = torch.tensor(X_dev, dtype=torch.float32, device=device)
    X_test_t = torch.tensor(X_test, dtype=torch.float32, device=device)

    hidden = [int(h) for h in args.hidden.split(",")]
    model = MLP(X_train.shape[1], hidden, len(ST3_LABELS), args.dropout).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    best = None
    for epoch in range(1, args.epochs + 1):
        model.train()
        optimizer.zero_grad()
        logits = model(X_train_t)
        loss = criterion(logits, y_train_t)
        loss.backward()
        optimizer.step()

        if epoch % args.eval_every == 0 or epoch == args.epochs:
            model.eval()
            with torch.no_grad():
                dev_proba = torch.sigmoid(model(X_dev_t)).cpu().numpy()
            thresholds = tune_thresholds(dev_proba, y_dev)
            dev_pred = labels_from_proba(dev_proba, thresholds, mlb.classes_.tolist())
            dev_metrics = evaluate_st3(dev_gold, dev_pred)
            log.info(f"epoch {epoch}: train_loss={loss.item():.4f} "
                     f"dev_st3_macro_f1={dev_metrics['st3_macro_f1']:.3f}")
            if best is None or dev_metrics["st3_macro_f1"] > best["dev_metrics"]["st3_macro_f1"]:
                best = {
                    "epoch": epoch, "thresholds": thresholds, "dev_metrics": dev_metrics,
                    "state_dict": {k: v.clone() for k, v in model.state_dict().items()},
                }

    log.info(f"selected epoch={best['epoch']} by dev_st3_macro_f1={best['dev_metrics']['st3_macro_f1']:.3f}")
    log.info(f"tuned per-label thresholds: "
             f"{dict(zip(mlb.classes_.tolist(), best['thresholds'].round(2).tolist()))}")

    model.load_state_dict(best["state_dict"])
    model.eval()
    with torch.no_grad():
        test_proba = torch.sigmoid(model(X_test_t)).cpu().numpy()
        train_proba = torch.sigmoid(model(X_train_t)).cpu().numpy()
    test_pred = labels_from_proba(test_proba, best["thresholds"], mlb.classes_.tolist())
    test_metrics = evaluate_st3(test_gold, test_pred)
    train_pred = labels_from_proba(train_proba, best["thresholds"], mlb.classes_.tolist())
    train_metrics = evaluate_st3(train_gold, train_pred)

    log.info("=== train (fit) ===")
    log.info(f"st3_macro_f1={train_metrics['st3_macro_f1']:.3f} "
             f"st3_family_macro_f1={train_metrics['st3_family_macro_f1']:.3f}")
    log.info("=== dev (model + threshold selection) ===")
    log.info(f"st3_macro_f1={best['dev_metrics']['st3_macro_f1']:.3f} "
             f"st3_family_macro_f1={best['dev_metrics']['st3_family_macro_f1']:.3f}")
    for label in ST3_LABELS:
        log.info(f"  {label}: {best['dev_metrics']['per_label_f1'].get(label, float('nan')):.3f}")
    log.info("=== test-holdout (final check) ===")
    log.info(f"st3_macro_f1={test_metrics['st3_macro_f1']:.3f} "
             f"st3_family_macro_f1={test_metrics['st3_family_macro_f1']:.3f}")
    for label in ST3_LABELS:
        log.info(f"  {label}: {test_metrics['per_label_f1'].get(label, float('nan')):.3f}")

    out_path = os.path.join("runs", f"submission_mlp_{timestamp}.jsonl")
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
        params = {"hidden": hidden, "dropout": args.dropout, "lr": args.lr,
                   "weight_decay": args.weight_decay, "epoch": best["epoch"]}
        desc = "From-scratch MLP (BCEWithLogitsLoss+pos_weight) over the same findings-derived " \
               f"features + top-{args.max_tfidf_features} TF-IDF as baseline_decision_tree.py, " \
               "per-label thresholds tuned on dev each eval; tests whether a nonlinear model " \
               "closes the gap over tree/forest/histgb/logreg on the identical feature space."
        f.write(",".join([
            git_commit(), str(split_seed), "mlp_pytorch", f'"{params}"',
            f"{test_metrics['st3_macro_f1']:.3f}", f"{test_metrics['st3_family_macro_f1']:.3f}",
            f"{best['dev_metrics']['st3_macro_f1']:.3f}", f"{best['dev_metrics']['st3_family_macro_f1']:.3f}",
            f"{train_metrics['st3_macro_f1']:.3f}", "classical_ml_sklearn", f'"{desc}"',
        ]) + "\n")
    log.info(f"appended results row to {results_path}")


if __name__ == "__main__":
    main()
