"""Aggregate an error jsonl written by baseline_gpt.py into a markdown report
that summarizes failure patterns: per-tier error counts, missing/extra label
frequency tables, and inferred missing->extra substitution pairs. Optionally
attaches the full instance text (transcript/video/product page) for up to
--max-detailed of the most illustrative error rows, looked up from a release
JSONL split by instanceID.

This is purely mechanical aggregation -- no LLM calls, no judgment about what
to change in the prompt. The report is meant to be read by a human/agent who
then decides how to edit SYSTEM_PROMPT.

Usage:
    python src/aggregate_errors.py runs/submission_gpt_error_<ts>.jsonl \
        [--dev public_data_dev/dev.jsonl] [--max-detailed 15] \
        --out runs/prompt_tuning/<run>/error_summary_iter{N}.md
"""
import argparse
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "starting_kit"))
from load_data import full_context, load_split


def load_error_rows(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def build_report(rows, dev_index, max_detailed):
    n = len(rows)
    tier_error_counts = Counter()
    st1_pairs = Counter()          # (gold, pred) for st1
    missing_counts = {"st2": Counter(), "st3": Counter()}
    extra_counts = {"st2": Counter(), "st3": Counter()}
    substitution_pairs = {"st2": Counter(), "st3": Counter()}

    for row in rows:
        errors = row.get("errors", {})
        for tier in ("st1", "st2", "st3"):
            if tier in errors:
                tier_error_counts[tier] += 1
        if "st1" in errors:
            st1_pairs[(errors["st1"]["gold"], errors["st1"]["pred"])] += 1
        for tier in ("st2", "st3"):
            if tier in errors:
                missing = errors[tier].get("missing", [])
                extra = errors[tier].get("extra", [])
                for m in missing:
                    missing_counts[tier][m] += 1
                for e in extra:
                    extra_counts[tier][e] += 1
                # Candidate substitutions: every missing label paired with every
                # extra label in the *same* instance -- an approximation of
                # "the model said X instead of Y" (co-occurrence, not causal).
                for m in missing:
                    for e in extra:
                        substitution_pairs[tier][(m, e)] += 1

    lines = []
    lines.append(f"# Error summary ({n} instance(s) with at least one error)\n")

    lines.append("## Per-tier error counts\n")
    for tier in ("st1", "st2", "st3"):
        lines.append(f"- {tier}: {tier_error_counts.get(tier, 0)}/{n}")
    lines.append("")

    if st1_pairs:
        lines.append("## st1 gold -> pred confusions\n")
        for (gold, pred), c in st1_pairs.most_common():
            lines.append(f"- {gold} -> {pred}: {c}x")
        lines.append("")

    for tier in ("st2", "st3"):
        if missing_counts[tier] or extra_counts[tier]:
            lines.append(f"## {tier} missing labels (gold had it, prediction missed it)\n")
            for label, c in missing_counts[tier].most_common():
                lines.append(f"- {label}: missing {c}x")
            lines.append("")
            lines.append(f"## {tier} extra labels (prediction hallucinated, not in gold)\n")
            for label, c in extra_counts[tier].most_common():
                lines.append(f"- {label}: extra {c}x")
            lines.append("")
            if substitution_pairs[tier]:
                lines.append(f"## {tier} inferred missing -> extra substitutions (same-instance co-occurrence)\n")
                for (m, e), c in substitution_pairs[tier].most_common(20):
                    lines.append(f"- {m} -> {e}: {c}x")
                lines.append("")

    # Detailed instances: prioritize the ones with the most errors (most
    # illustrative), then include full text if available in the dev index.
    detailed = sorted(
        rows,
        key=lambda r: len(r.get("errors", {}).get("st2", {}).get("missing", []))
        + len(r.get("errors", {}).get("st2", {}).get("extra", []))
        + len(r.get("errors", {}).get("st3", {}).get("missing", []))
        + len(r.get("errors", {}).get("st3", {}).get("extra", []))
        + (1 if "st1" in r.get("errors", {}) else 0),
        reverse=True,
    )[:max_detailed]

    if detailed:
        lines.append("## Detailed error instances\n")
        for row in detailed:
            iid = row["instanceID"]
            lines.append(f"### {iid}\n")
            lines.append(f"- gold: {json.dumps(row['gold'])}")
            lines.append(f"- pred: {json.dumps(row['pred'])}")
            lines.append(f"- errors: {json.dumps(row['errors'])}")
            if dev_index is not None and iid in dev_index:
                text = full_context(dev_index[iid])
                lines.append("\n<details><summary>full instance text</summary>\n")
                lines.append("```")
                lines.append(text)
                lines.append("```")
                lines.append("</details>\n")
            lines.append("")

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("error_jsonl", help="path to runs/submission_gpt_error_<ts>.jsonl")
    ap.add_argument("--dev", default=None,
                     help="release JSONL split to look up full instance text by instanceID")
    ap.add_argument("--max-detailed", type=int, default=15,
                     help="max number of error instances to include with full text")
    ap.add_argument("--out", required=True, help="output markdown path")
    args = ap.parse_args()

    rows = load_error_rows(args.error_jsonl)

    dev_index = None
    if args.dev:
        dev_index = {inst["instanceID"]: inst for inst in load_split(args.dev)}

    report = build_report(rows, dev_index, args.max_detailed)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"wrote error summary to {args.out}")


if __name__ == "__main__":
    main()
