"""Majority-class baseline: predicts the most frequent training labels everywhere.

Usage: python baseline_majority.py train.jsonl dev.jsonl > submission.jsonl
"""
import json
import sys
from collections import Counter

train, target = sys.argv[1], sys.argv[2]
c1, c2, c3 = Counter(), Counter(), Counter()
for line in open(train, encoding="utf-8"):
    lab = json.loads(line).get("labels")
    if lab:
        c1[lab["st1"]] += 1
        c2.update(lab["st2"])
        c3.update(lab["st3"])
st1 = c1.most_common(1)[0][0]
st2 = [c2.most_common(1)[0][0]]
st3 = [c3.most_common(1)[0][0]]
for line in open(target, encoding="utf-8"):
    iid = json.loads(line)["instanceID"]
    print(json.dumps({"instanceID": iid, "st1": st1, "st2": st2, "st3": st3}))
