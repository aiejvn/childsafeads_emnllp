"""Minimal loader for the ChildSafeAds release format (graduated data rungs)."""
import json
from pathlib import Path


def load_split(path):
    """Yield instances from a release JSONL (train/dev/test)."""
    for line in Path(path).open(encoding="utf-8"):
        if line.strip():
            yield json.loads(line)


def transcript_only(instance):
    """Rung 1: what a transcript-only monitoring system sees."""
    return instance["transcript"]["text"]


def full_context(instance):
    """All distributed rungs concatenated for convenience."""
    t = instance["transcript"]["text"]
    v = instance["video_context"]
    p = instance["product_page"]
    return (f"TRANSCRIPT:\n{t}\n\nVIDEO: {v['title']}\nDESCRIPTION:\n{v['description']}\n"
            f"OFFICIAL_DISCLOSURE: {v['official_disclosure']}\n\n"
            f"PAGE ({p['page_title']}):\n{p['text']}")
