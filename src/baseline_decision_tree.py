"""Decision-tree-family baseline for ST3 (compliance-risk flags) only.

Built directly from the structural/lexical patterns found in `st3_findings.md`
(repo root) -- each engineered feature below traces back to a specific finding
there, rather than being generic bag-of-words. A TF-IDF block is added on top
so the tree still has a fighting chance at the more diffuse/semantic labels
(misleading_claim, direct_exhortation) that the structural findings alone
don't fully explain.

Two axes of "decision tree" are tried and grid-selected on dev:
  --estimator tree   a single DecisionTreeClassifier per label (interpretable,
                      but predict_proba is just leaf class-fraction -> coarse)
  --estimator forest  a RandomForestClassifier per label (an ensemble of the
                      same decision trees; smoother probabilities, tests
                      whether single-tree capacity is the bottleneck)
Per-label decision thresholds are tuned on dev via predict_proba (plain
.predict() on an imbalanced label is just an implicit 0.5 cut, which is rarely
optimal for macro-F1 on rare classes) and then applied blind to test-holdout.

Uses the same train/test-holdout methodology as the LoRA autoresearch track
(src/lora/lora_train_generative.py): 500 instances held out from train.jsonl at
a fresh random split_seed every run, remaining n-500 used for fitting; dev.jsonl
is the fixed validation set used for hyperparameter/threshold selection,
test-holdout is scored once at the end with the selected model. Reuses
ST3/ST3_FAMILY/macro_f1/sanitize_st3 from baseline_gpt.py so numbers are
directly comparable to the LoRA generative runs logged in
runs/lora-qwen/results.csv.

Usage (from repo root):
    python src/baseline_decision_tree.py
    python src/baseline_decision_tree.py --estimator forest
    python src/baseline_decision_tree.py --split-seed 12345  # pin for a repro check
"""
import argparse
import json
import os
import random
import re
import subprocess
import sys
from datetime import datetime

import numpy as np
from scipy import sparse
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multioutput import MultiOutputClassifier
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.tree import DecisionTreeClassifier

sys.path.insert(0, os.path.dirname(__file__))
from baseline_gpt import ST3, ST3_FAMILY, FAMILY_LABELS, macro_f1, sanitize_st3, setup_logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "starting_kit"))
from load_data import load_split

ST3_LABELS = sorted(ST3)

# --- keyword lexicons, drawn straight from st3_findings.md's manually-reviewed taxonomies ---

DISCLOSURE_RE = re.compile(
    r"\b(sponsor(ed|ing|s)?|paid partner(ship)?|thanks? to .*for sponsoring|"
    r"today'?s sponsor|affiliate link|#ad\b|paid promotion)\b", re.I,
)
# Broader than DISCLOSURE_RE: any commercial/promo signal at all, not just an explicit
# sponsorship acknowledgment. Finding: instances near-empty transcripts that are STILL
# labeled with a real st3 flag (not insufficient_context) almost always have this kind of
# promo language in video_context.description even though the sampled transcript window has
# nothing -- annotators judge off the description when the transcript segment doesn't carry
# the pitch. Deliberately excludes generic words like "subscribe"/"check out"/"link in"/
# "www." that appear in nearly every YouTube description regardless of commercial content.
COMMERCIAL_RE = re.compile(
    r"(\bsponsor|\bpaid partner|\baffiliate link|#ad\b|\buse code\b|\bpromo\s?code\b|"
    r"\bcoupon\b|\d+%\s*off|\bfree trial\b|\bdiscount\b)", re.I,
)
GUARANTEE_RE = re.compile(r"\b(guarantee(d)?|promise[ds]?|money.back)\b", re.I)
NUMERIC_CLAIM_RE = re.compile(
    r"\b\d+(\.\d+)?\s*(%|percent|times|x)\b|\breduc(e[sd]?|ing)\b.*\b\d+", re.I,
)
SUPERLATIVE_RE = re.compile(r"\b(best|#1|number one|most \w+|ultimate|top.rated)\b", re.I)
IMPERATIVE_RE = re.compile(
    r"\b(click|buy|grab|get yours|use code|use my code|visit|download|subscribe|order now|"
    r"shop now|claim|join|sign up|check out|link in (the )?(description|bio)|discount code|"
    r"don'?t miss|act now|limited time)\b", re.I,
)

AGE_RESTRICTED_LEXICON = {
    "betting_gambling": re.compile(
        r"\b(draftkings|mybookie|prizepicks|underdog|sky ?bet|pick6|sportsbook|fantasy sports|"
        r"bet(ting)?|wager|odds boost)\b", re.I,
    ),
    "alcohol": re.compile(
        r"\b(beer|wine|vodka|whisk(e)?y|gin|spirits|alcohol|brewery|winery|beer52|"
        r"bright cellars|botanist|cocktail)\b", re.I,
    ),
    "adult_sex_toys": re.compile(
        r"\b(lelo|bellesa|bessa|adam ?&? ?eve|lovehoney|vibrator|dildo|sex toy|clitoral|"
        r"masturbat\w*)\b", re.I,
    ),
    "skin_gambling": re.compile(
        r"\b(skinsmonkey|csgofast|skinclub|bandit camp|csgo skins|skin trading|case opening)\b",
        re.I,
    ),
    "energy_caffeine": re.compile(
        r"\b(g ?fuel|gamer ?supps|glitch energy|energy drink|high caffeine|\d+\s?mg caffeine)\b",
        re.I,
    ),
    "thc_cbd": re.compile(r"\b(thc|cbd|delta.?9|cushy dreams|5cbd)\b", re.I),
    "vaping_nicotine": re.compile(r"\b(vape|vaping|e.?cigarette|nicotine|fume|bong)\b", re.I),
    "other_restricted": re.compile(
        r"\b(bluechew|crypto(currency)?|bitcoin|firearm|knife\b|prescription)\b", re.I,
    ),
}

HFSS_LEXICON = {
    "energy_drink_brand": re.compile(
        r"\b(g ?fuel|gamer ?supps|glitch energy|turbo energy)\b", re.I,
    ),
    "candy_subscription_brand": re.compile(
        r"\b(tokyo treat|sakuraco|bokksu|wow box)\b", re.I,
    ),
    "misc_candy_soda": re.compile(
        r"\b(candy|soda|mountain dew|peanut butter cup|sour candy|gumm(y|ies)|chocolate bar)\b",
        re.I,
    ),
}


def real_word_count(text: str) -> int:
    """Unicode-aware content-word count: strips bracketed/starred sound cues ([Music],
    *outro*) and short filler tokens, but (unlike an ASCII-only [^a-zA-Z] strip) does not
    zero out non-Latin-script transcripts (Hindi, etc.) -- an earlier version of this used
    [^a-zA-Z] and misclassified every non-English transcript as empty."""
    stripped = re.sub(r"\[[^\]]*\]", " ", text)
    stripped = re.sub(r"\*[^*]*\*", " ", stripped)
    stripped = re.sub(r"\b(um|uh|okay|ok|so|foreign|hey|oh)\b", " ", stripped, flags=re.I)
    tokens = re.findall(r"\w+", stripped, flags=re.UNICODE)
    return len([t for t in tokens if len(t) > 1 and not t.isdigit()])


def first_match_relative_position(pattern: re.Pattern, text: str) -> float:
    """Finding (inadequate_disclosure): disclosure mentioned late in the segment, after the
    pitch, leans toward inadequate. Returns the match's start offset as a fraction of text
    length, or 1.0 (as late as possible) if there's no match at all."""
    if not text:
        return 1.0
    m = pattern.search(text)
    return (m.start() / len(text)) if m else 1.0


def engineer_features(instances: list) -> dict:
    """Returns {"numeric": np.ndarray, "text": list[str]} -- numeric holds the hand-built
    findings-derived features, text holds the concatenated transcript+product-page text for
    the supplementary TF-IDF block."""
    rows = []
    texts = []
    for inst in instances:
        transcript = inst["transcript"]["text"]
        video = inst["video_context"]
        page = inst.get("product_page") or {}
        description = video.get("description", "")
        page_text = page.get("text", "") or ""

        official_disclosure = video.get("official_disclosure", "")
        transcript_has_disclosure = bool(DISCLOSURE_RE.search(transcript))
        description_has_disclosure = bool(DISCLOSURE_RE.search(description))
        transcript_wc = real_word_count(transcript)
        transcript_near_empty = transcript_wc < 6
        description_commercial = bool(COMMERCIAL_RE.search(description))

        word_len = max(transcript_wc, 1)
        imperative_count = len(IMPERATIVE_RE.findall(transcript))
        row = {
            "transcript_char_len": len(transcript),
            "transcript_word_len": transcript_wc,
            "transcript_near_empty": int(transcript_near_empty),
            "description_word_len": real_word_count(description),
            "description_commercial_hit": int(description_commercial),
            # Finding: transcript-empty instances still get a real st3 flag (not
            # insufficient_context) when the description alone carries commercial content --
            # insufficient_context requires BOTH to be thin. See real_word_count's docstring.
            "context_insufficient": int(transcript_near_empty and not description_commercial),
            "official_disclosure_true": int(official_disclosure == "true"),
            "official_disclosure_false": int(official_disclosure == "false"),
            "official_disclosure_missing": int(official_disclosure not in ("true", "false")),
            "transcript_has_disclosure_lang": int(transcript_has_disclosure),
            "description_has_disclosure_lang": int(description_has_disclosure),
            "disclosure_only_in_description": int(
                description_has_disclosure and not transcript_has_disclosure
            ),
            "disclosure_relative_position": first_match_relative_position(DISCLOSURE_RE, transcript),
            "guarantee_promise_hit": int(bool(GUARANTEE_RE.search(transcript))),
            "numeric_comparative_claim_hit": int(bool(NUMERIC_CLAIM_RE.search(transcript))),
            "superlative_hit": len(SUPERLATIVE_RE.findall(transcript)),
            "imperative_verb_count": imperative_count,
            "imperative_verb_density": imperative_count / word_len,
            "imperative_zero": int(imperative_count == 0),
            "has_product_page": int(bool(page.get("resolved_url"))),
        }
        combined = f"{transcript} {description} {page_text}"
        for name, pattern in AGE_RESTRICTED_LEXICON.items():
            row[f"age_restricted__{name}"] = int(bool(pattern.search(combined)))
        for name, pattern in HFSS_LEXICON.items():
            row[f"hfss__{name}"] = int(bool(pattern.search(combined)))

        rows.append(row)
        # description is included now (previously only transcript+page_text) -- it carries
        # real signal for insufficient_context and inadequate_disclosure, see findings above.
        texts.append(f"{transcript}\n{description}\n{page_text}")

    keys = sorted(rows[0].keys())
    numeric = np.array([[r[k] for k in keys] for r in rows], dtype=float)
    return {"numeric": numeric, "text": texts, "feature_names": keys}


def build_matrix(feats: dict, vectorizer: TfidfVectorizer, fit: bool):
    tfidf = vectorizer.fit_transform(feats["text"]) if fit else vectorizer.transform(feats["text"])
    return sparse.hstack([sparse.csr_matrix(feats["numeric"]), tfidf]).tocsr()


def make_base_estimator(estimator: str, params: dict):
    if estimator == "tree":
        return DecisionTreeClassifier(
            max_depth=params["max_depth"], min_samples_leaf=params["min_samples_leaf"],
            class_weight="balanced", random_state=0,
        )
    if estimator == "forest":
        return RandomForestClassifier(
            n_estimators=params["n_estimators"], max_depth=params["max_depth"],
            min_samples_leaf=params["min_samples_leaf"],
            class_weight="balanced", random_state=0, n_jobs=-1,
        )
    if estimator == "histgb":
        return HistGradientBoostingClassifier(
            max_depth=params["max_depth"], min_samples_leaf=params["min_samples_leaf"],
            learning_rate=params["learning_rate"], max_iter=params["n_estimators"], random_state=0,
        )
    if estimator == "logreg":
        return LogisticRegression(
            C=params["C"], class_weight="balanced", max_iter=2000, solver="liblinear", random_state=0,
        )
    raise ValueError(estimator)


def get_proba_matrix(clf: MultiOutputClassifier, X) -> np.ndarray:
    """Positive-class probability per label. Handles the (rare, small-n) case where a
    per-label estimator only ever saw one class during fit."""
    cols = []
    for estimator in clf.estimators_:
        classes = list(estimator.classes_)
        proba = estimator.predict_proba(X)
        if len(classes) == 1:
            cols.append(np.full(X.shape[0], float(classes[0])))
        else:
            cols.append(proba[:, classes.index(1)])
    return np.column_stack(cols)


def tune_thresholds(proba: np.ndarray, y_true_bin: np.ndarray) -> np.ndarray:
    """Per-label threshold maximizing that label's binary F1 on the given (dev) set."""
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


def evaluate_st3(gold_labels: list, pred_labels: list) -> dict:
    st3_f1, st3_per_label = macro_f1(gold_labels, pred_labels, ST3_LABELS)
    fam = lambda flags: [ST3_FAMILY[f] for f in flags]
    fam_f1, fam_per_label = macro_f1(
        [fam(g) for g in gold_labels], [fam(p) for p in pred_labels], FAMILY_LABELS
    )
    return {
        "st3_macro_f1": st3_f1,
        "st3_family_macro_f1": fam_f1,
        "per_label_f1": st3_per_label,
        "per_family_f1": fam_per_label,
    }


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=os.path.dirname(__file__),
        ).decode().strip()
    except Exception:
        return "unknown"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", default=os.path.join("public_data_dev", "train.jsonl"))
    ap.add_argument("--dev", default=os.path.join("public_data_dev", "dev.jsonl"))
    ap.add_argument("--test-holdout", type=int, default=500,
                     help="instances held out from --train for a final generalization check "
                          "(same convention as lora_train_generative.py)")
    ap.add_argument("--split-seed", type=int, default=None,
                     help="seed for the train/test-holdout split; default is a fresh random "
                          "seed every run (do not pin across experiments -- see "
                          "feedback-rotating-test-holdout)")
    ap.add_argument("--max-tfidf-features", type=int, default=800)
    ap.add_argument("--estimators", nargs="+", default=["tree", "forest", "histgb", "logreg"],
                     choices=["tree", "forest", "histgb", "logreg"],
                     help="which estimator families to grid over")
    args = ap.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = os.path.join("runs", "baseline_decision_tree")
    log = setup_logging(log_dir, "decision_tree", "sklearn", timestamp)

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
    log.info(f"engineered {len(train_feats['feature_names'])} structural features: "
             f"{train_feats['feature_names']}")

    vectorizer = TfidfVectorizer(
        max_features=args.max_tfidf_features, ngram_range=(1, 2), min_df=3, stop_words="english",
    )
    X_train = build_matrix(train_feats, vectorizer, fit=True)
    X_dev = build_matrix(dev_feats, vectorizer, fit=False)
    X_test = build_matrix(test_feats, vectorizer, fit=False)
    # HistGradientBoostingClassifier in this sklearn version rejects sparse X outright.
    X_train_dense, X_dev_dense, X_test_dense = X_train.toarray(), X_dev.toarray(), X_test.toarray()

    mlb = MultiLabelBinarizer(classes=ST3_LABELS)
    y_train = mlb.fit_transform([inst["labels"]["st3"] for inst in train_instances])
    y_dev = mlb.transform([inst["labels"]["st3"] for inst in dev_instances])

    train_gold = [inst["labels"]["st3"] for inst in train_instances]
    dev_gold = [inst["labels"]["st3"] for inst in dev_instances]
    test_gold = [inst["labels"]["st3"] for inst in test_holdout]

    def grid_for(name: str) -> list:
        if name == "tree":
            return [{"max_depth": d, "min_samples_leaf": m, "n_estimators": None}
                     for d in (4, 6, 8, 10, 15, None) for m in (1, 2, 5)]
        if name == "forest":
            return [{"max_depth": d, "min_samples_leaf": m, "n_estimators": n}
                     for d in (None, 10, 20) for m in (1, 2, 5) for n in (200, 500)]
        if name == "histgb":
            return [{"max_depth": d, "min_samples_leaf": m, "n_estimators": n, "learning_rate": lr}
                     for d in (3, 6) for m in (10, 20) for n in (100, 300)
                     for lr in (0.05, 0.1)]
        if name == "logreg":
            return [{"C": c} for c in (0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0)]
        raise ValueError(name)

    best = None
    for estimator_name in args.estimators:
        fit_X, dev_X = (X_train_dense, X_dev_dense) if estimator_name == "histgb" else (X_train, X_dev)
        for params in grid_for(estimator_name):
            clf = MultiOutputClassifier(make_base_estimator(estimator_name, params), n_jobs=1)
            clf.fit(fit_X, y_train)

            dev_proba = get_proba_matrix(clf, dev_X)
            thresholds = tune_thresholds(dev_proba, y_dev)
            dev_pred = labels_from_proba(dev_proba, thresholds, mlb.classes_.tolist())
            dev_metrics = evaluate_st3(dev_gold, dev_pred)

            log.info(f"  grid estimator={estimator_name} params={params} "
                     f"-> dev_st3_macro_f1={dev_metrics['st3_macro_f1']:.3f}")
            if best is None or dev_metrics["st3_macro_f1"] > best["dev_metrics"]["st3_macro_f1"]:
                best = {
                    "estimator": estimator_name, "params": params,
                    "clf": clf, "thresholds": thresholds,
                    "dev_metrics": dev_metrics, "dev_pred": dev_pred,
                }

    log.info(f"selected estimator={best['estimator']} params={best['params']} "
             f"by dev_st3_macro_f1={best['dev_metrics']['st3_macro_f1']:.3f}")
    log.info(f"tuned per-label thresholds: "
             f"{dict(zip(mlb.classes_.tolist(), best['thresholds'].round(2).tolist()))}")

    final_test_X = X_test_dense if best["estimator"] == "histgb" else X_test
    final_train_X = X_train_dense if best["estimator"] == "histgb" else X_train
    test_proba = get_proba_matrix(best["clf"], final_test_X)
    test_pred = labels_from_proba(test_proba, best["thresholds"], mlb.classes_.tolist())
    test_metrics = evaluate_st3(test_gold, test_pred)

    train_proba = get_proba_matrix(best["clf"], final_train_X)
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

    feat_names = vectorizer.get_feature_names_out().tolist()
    all_names = train_feats["feature_names"] + [f"tfidf__{t}" for t in feat_names]
    if best["estimator"] in ("tree", "forest"):
        importances = np.mean([e.feature_importances_ for e in best["clf"].estimators_], axis=0)
        top = sorted(zip(all_names, importances), key=lambda x: -x[1])[:20]
        log.info("=== top 20 features by mean importance across per-label trees ===")
        for name, imp in top:
            log.info(f"  {name}: {imp:.4f}")
    elif best["estimator"] == "histgb":
        log.info("(histgb: sklearn doesn't expose feature_importances_ for HistGradientBoosting "
                 "without a separate permutation-importance pass; skipping)")
    elif best["estimator"] == "logreg":
        coefs = np.mean([np.abs(e.coef_[0]) for e in best["clf"].estimators_], axis=0)
        top = sorted(zip(all_names, coefs), key=lambda x: -x[1])[:20]
        log.info("=== top 20 features by mean |coef| across per-label logistic regressions ===")
        for name, imp in top:
            log.info(f"  {name}: {imp:.4f}")

    out_path = os.path.join("runs", f"submission_dt_{timestamp}.jsonl")
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
        desc = "Classical-ML grid (tree/forest/histgb/logreg) over findings-derived features + " \
               f"top-{args.max_tfidf_features} TF-IDF, per-label thresholds tuned on dev via predict_proba."
        f.write(",".join([
            git_commit(), str(split_seed), best["estimator"], f'"{best["params"]}"',
            f"{test_metrics['st3_macro_f1']:.3f}", f"{test_metrics['st3_family_macro_f1']:.3f}",
            f"{best['dev_metrics']['st3_macro_f1']:.3f}", f"{best['dev_metrics']['st3_family_macro_f1']:.3f}",
            f"{train_metrics['st3_macro_f1']:.3f}", "classical_ml_sklearn", f'"{desc}"',
        ]) + "\n")
    log.info(f"appended results row to {results_path}")


if __name__ == "__main__":
    main()
