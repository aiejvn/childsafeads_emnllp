# ChildSafeAds Starting Kit

Files:
- `load_data.py` — loader for the graduated-rung release format (+ helpers for
  transcript-only and full-context views)
- `baseline_majority.py` — majority-class baseline producing a valid submission:
  `python baseline_majority.py train.jsonl dev.jsonl > submission.jsonl`
- `check_submission.py` — validate before uploading:
  `python check_submission.py submission.jsonl dev.jsonl`
- `sample_submission.jsonl` — a valid dev-phase submission (the majority baseline)

Submission object per instance:
`{"instanceID": "...", "st1": "<label>", "st2": [...], "st3": [...]}`
Labels: see `labels_taxonomy.md` in the dataset package. `no_flag` and
`insufficient_context` must stand alone in st3.

Reference scores of this baseline on dev: mean macro-F1 0.093
(st1 0.151 / st2 0.042 / st3 0.085). Beat it.
