"""Validate a submission file before uploading.

Usage: python check_submission.py submission.jsonl [target_split.jsonl]
"""
import json
import sys

ST1 = {"physical_goods", "digital_content_or_services", "physical_services", "none", "other"}
ST2 = {"toys", "food", "apps", "hardware_electronics", "fashion", "health", "education",
       "financial", "gambling", "gambling_adjacent", "creator_community", "other"}
ST3 = {"undisclosed_advertising", "inadequate_disclosure", "direct_exhortation",
       "misleading_claim", "age_restricted_or_prohibited_product", "hfss_food_marketing",
       "no_flag", "insufficient_context"}

if __name__ == "__main__":
    errs, n = 0, 0
    ids = set()
    for ln, line in enumerate(open(sys.argv[1], encoding="utf-8"), 1):
        if not line.strip():
            continue
        n += 1
        try:
            o = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"line {ln}: bad JSON ({e})"); errs += 1; continue
        if "instanceID" not in o:
            print(f"line {ln}: missing instanceID"); errs += 1; continue
        if o["instanceID"] in ids:
            print(f"line {ln}: duplicate instanceID"); errs += 1
        ids.add(o["instanceID"])
        if "st1" in o and o["st1"] not in ST1:
            print(f"line {ln}: bad st1 '{o['st1']}'"); errs += 1
        if "st2" in o and not set(o["st2"]) <= ST2:
            print(f"line {ln}: bad st2 {set(o['st2']) - ST2}"); errs += 1
        if "st3" in o:
            if not set(o["st3"]) <= ST3:
                print(f"line {ln}: bad st3 {set(o['st3']) - ST3}"); errs += 1
            if ({"no_flag", "insufficient_context"} & set(o["st3"])) and len(o["st3"]) > 1:
                print(f"line {ln}: no_flag/insufficient_context must stand alone"); errs += 1
    if len(sys.argv) > 2:
        want = {json.loads(l)["instanceID"] for l in open(sys.argv[2], encoding="utf-8") if l.strip()}
        miss = want - ids
        if miss:
            print(f"WARNING: {len(miss)} target instances have no prediction (they score 0)")
    print(f"{n} predictions, {errs} errors" + (" — OK to submit" if errs == 0 else " — FIX BEFORE SUBMITTING"))
    sys.exit(1 if errs else 0)
