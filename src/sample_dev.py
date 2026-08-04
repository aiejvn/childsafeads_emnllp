"""Draw a fresh, unseeded random sample of instances from a release JSONL split
and write them verbatim to a standalone JSONL file.

Used by the prompt-tuning loop to get a different ~N-example batch every
iteration (as opposed to baseline_gpt.py's --sample-size, which is seeded
with random.Random(42) for reproducible smoke tests and is left untouched).

Usage:
    python src/sample_dev.py public_data_dev/dev.jsonl --n 10 --out runs/prompt_tuning/<run>/batch_iter1.jsonl
"""
import argparse
import json
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "starting_kit"))
from load_data import load_split


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="split file to sample from, e.g. public_data_dev/dev.jsonl")
    ap.add_argument("--n", type=int, default=10, help="number of instances to sample")
    ap.add_argument("--out", required=True, help="output JSONL path")
    args = ap.parse_args()

    instances = list(load_split(args.target))
    n = min(args.n, len(instances))
    sample = random.sample(instances, n)  # unseeded on purpose -- fresh draw every call

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        for inst in sample:
            f.write(json.dumps(inst) + "\n")

    print(f"wrote {n} instances to {args.out}")


if __name__ == "__main__":
    main()
