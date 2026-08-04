"""Exploratory data analysis over train.jsonl / dev.jsonl."""
import json
import statistics
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "public_data_dev"

ST3_FAMILIES = {
    "disclosure": {"undisclosed_advertising", "inadequate_disclosure"},
    "content": {"direct_exhortation", "misleading_claim"},
    "product": {"age_restricted_or_prohibited_product", "hfss_food_marketing"},
    "housekeeping": {"no_flag", "insufficient_context"},
}


def load(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def st3_family(flag):
    for fam, flags in ST3_FAMILIES.items():
        if flag in flags:
            return fam
    return "unknown"


def analyze_split(name, rows):
    print(f"\n{'=' * 60}\n{name} (n={len(rows)})\n{'=' * 60}")

    # --- schema / missingness ---
    missing_transcript = sum(1 for r in rows if not r.get("transcript", {}).get("text"))
    missing_product = sum(1 for r in rows if not r.get("product_page", {}).get("text"))
    ids = [r["instanceID"] for r in rows]
    dup_ids = len(ids) - len(set(ids))
    print(f"Missing/empty transcript text: {missing_transcript}")
    print(f"Missing/empty product_page text: {missing_product}")
    print(f"Duplicate instanceIDs: {dup_ids}")

    # --- ST1 ---
    st1_counts = Counter(r["labels"]["st1"] for r in rows)
    print("\nST1 (single-label) distribution:")
    for label, count in st1_counts.most_common():
        print(f"  {label:30s} {count:5d} ({count/len(rows):.1%})")

    # --- ST2 ---
    st2_counts = Counter()
    st2_per_instance = []
    for r in rows:
        tags = r["labels"]["st2"]
        st2_per_instance.append(len(tags))
        st2_counts.update(tags)
    print(f"\nST2 (multi-label) avg tags/instance: {statistics.mean(st2_per_instance):.2f}")
    print("ST2 tag frequency:")
    for label, count in st2_counts.most_common():
        print(f"  {label:30s} {count:5d} ({count/len(rows):.1%})")

    # --- ST3 ---
    st3_counts = Counter()
    st3_family_counts = Counter()
    st3_per_instance = []
    exclusivity_violations = 0
    disclosure_mutex_violations = 0
    evidence_present = 0
    evidence_absent_for_flagged = 0
    for r in rows:
        flags = r["labels"]["st3"]
        st3_per_instance.append(len(flags))
        st3_counts.update(flags)
        st3_family_counts.update({st3_family(f) for f in flags})
        flagset = set(flags)
        if ("no_flag" in flagset or "insufficient_context" in flagset) and len(flagset) > 1:
            exclusivity_violations += 1
        if {"undisclosed_advertising", "inadequate_disclosure"} <= flagset:
            disclosure_mutex_violations += 1
        ev = r["labels"].get("st3_evidence", [])
        real_flags = flagset - {"no_flag", "insufficient_context"}
        if real_flags:
            if ev:
                evidence_present += 1
            else:
                evidence_absent_for_flagged += 1

    print(f"\nST3 (multi-label) avg flags/instance: {statistics.mean(st3_per_instance):.2f}")
    print("ST3 flag frequency:")
    for label, count in st3_counts.most_common():
        print(f"  {label:38s} {count:5d} ({count/len(rows):.1%})")
    print("ST3 family rollup (instance touches family >=1 flag):")
    for fam, count in st3_family_counts.most_common():
        print(f"  {fam:15s} {count:5d} ({count/len(rows):.1%})")
    print(f"\nExclusivity violations (no_flag/insufficient_context + others): {exclusivity_violations}")
    print(f"undisclosed_advertising & inadequate_disclosure both present: {disclosure_mutex_violations}")
    print(f"Flagged instances WITH evidence: {evidence_present}, WITHOUT evidence: {evidence_absent_for_flagged}")

    # --- official_disclosure vs disclosure-family flags ---
    official_true = sum(1 for r in rows if r["video_context"].get("official_disclosure") == "true")
    official_false = sum(1 for r in rows if r["video_context"].get("official_disclosure") == "false")
    disclosure_flag_present = sum(
        1 for r in rows if set(r["labels"]["st3"]) & ST3_FAMILIES["disclosure"]
    )
    official_true_but_flagged = sum(
        1 for r in rows
        if r["video_context"].get("official_disclosure") == "true"
        and set(r["labels"]["st3"]) & ST3_FAMILIES["disclosure"]
    )
    print(f"\nofficial_disclosure=true: {official_true}, =false: {official_false}, other/missing: {len(rows)-official_true-official_false}")
    print(f"Instances with a disclosure-family st3 flag: {disclosure_flag_present}")
    print(f"official_disclosure=true but STILL has disclosure flag: {official_true_but_flagged}")

    # --- text/metadata characteristics ---
    transcript_word_counts = [len(r["transcript"]["text"].split()) for r in rows]
    product_word_counts = [len(r["product_page"]["text"].split()) for r in rows if r.get("product_page", {}).get("text")]
    durations = [
        float(r["transcript"]["segment_end"]) - float(r["transcript"]["segment_start"])
        for r in rows
    ]
    print(f"\nTranscript word count: mean={statistics.mean(transcript_word_counts):.0f}, "
          f"median={statistics.median(transcript_word_counts):.0f}, "
          f"min={min(transcript_word_counts)}, max={max(transcript_word_counts)}")
    if product_word_counts:
        print(f"Product page word count: mean={statistics.mean(product_word_counts):.0f}, "
              f"median={statistics.median(product_word_counts):.0f}, "
              f"min={min(product_word_counts)}, max={max(product_word_counts)}")
    print(f"Segment duration (s): mean={statistics.mean(durations):.1f}, "
          f"median={statistics.median(durations):.1f}, "
          f"min={min(durations):.1f}, max={max(durations):.1f}")

    # --- channels ---
    channels = Counter(r["channel_context"]["channelID"] for r in rows)
    print(f"\nUnique channels: {len(channels)}")
    print("Top 10 channels by instance count:")
    for ch, count in channels.most_common(10):
        name = next(r["channel_context"]["channel_name"] for r in rows if r["channel_context"]["channelID"] == ch)
        print(f"  {name:30s} {count:5d}")

    return {
        "rows": rows,
        "st1_counts": st1_counts,
        "st2_counts": st2_counts,
        "st3_counts": st3_counts,
        "st3_family_counts": st3_family_counts,
        "channels": channels,
    }


def cross_split_checks(train_stats, dev_stats):
    print(f"\n{'=' * 60}\nCROSS-SPLIT CHECKS\n{'=' * 60}")

    train_channels = set(train_stats["channels"])
    dev_channels = set(dev_stats["channels"])
    overlap = train_channels & dev_channels
    print(f"Channels in train: {len(train_channels)}, in dev: {len(dev_channels)}")
    print(f"Overlapping channels: {len(overlap)} "
          f"({len(overlap)/len(dev_channels):.1%} of dev channels also in train)")

    n_train = len(train_stats["rows"])
    n_dev = len(dev_stats["rows"])
    print("\nST1 distribution shift (train% vs dev%):")
    all_labels = set(train_stats["st1_counts"]) | set(dev_stats["st1_counts"])
    for label in sorted(all_labels):
        t = train_stats["st1_counts"].get(label, 0) / n_train
        d = dev_stats["st1_counts"].get(label, 0) / n_dev
        print(f"  {label:30s} train={t:.1%}  dev={d:.1%}  delta={d-t:+.1%}")

    print("\nST3 distribution shift (train% vs dev%):")
    all_flags = set(train_stats["st3_counts"]) | set(dev_stats["st3_counts"])
    for flag in sorted(all_flags):
        t = train_stats["st3_counts"].get(flag, 0) / n_train
        d = dev_stats["st3_counts"].get(flag, 0) / n_dev
        print(f"  {flag:38s} train={t:.1%}  dev={d:.1%}  delta={d-t:+.1%}")


if __name__ == "__main__":
    train_rows = load(DATA_DIR / "train.jsonl")
    dev_rows = load(DATA_DIR / "dev.jsonl")

    train_stats = analyze_split("TRAIN", train_rows)
    dev_stats = analyze_split("DEV", dev_rows)
    cross_split_checks(train_stats, dev_stats)
