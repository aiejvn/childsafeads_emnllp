# The generative dev/test leak: independent verification

## Summary

The leak was real, and it was exactly what commit `9e8946a` claims: `GenerativeDataset.__getitem__`
(in `src/lora/lora_data.py`) decided whether to append the gold completion to `input_ids` based
solely on `if labels:` — i.e. "does this instance carry a `labels` dict at all" — rather than "is
this input about to be trained on or generated from." Dev and test-holdout instances carry gold
`labels` too (they have to, for scoring), so before the fix they got the *exact same*
prompt-plus-gold-JSON sequence as training instances, and that full sequence — correct answer
already written into it — was handed straight to `model.generate()`. The model was not predicting;
it was continuing a string that already contained the right answer, and that continuation was
scored as if it were a zero-shot prediction. The fix adds an explicit `include_completion` flag
(default `True`) so callers can opt out, and the dev/test-holdout/predict call sites now do.
Separately, and importantly: `load_split` (in `starting_kit/load_data.py`, the function the user
was calling "load_data") does **not** leak anything. It is a bare JSONL line-reader — it returns
whatever JSON dict is on each line, including that dict's `"labels"` key, and does not construct
any prompt or any `model.generate()` input. Returning gold labels as data is not a leak; splicing
those labels into a string fed to `generate()` is. The bug was entirely downstream of
`load_split`, inside `GenerativeDataset.__getitem__`.z

**Verified against commit `9e8946a4047020b5b0f67739bd71ca068de72669`** (the fix commit itself, dated
2026-08-14 15:34:33 +0000).
**Current HEAD at time of this investigation: `3764dad167344f6da2dbcbf77dbc305f67db350d`** (dated
2026-08-14 23:28:52 +0000, 8 commits' worth of runtime after the fix — no code changes to the fix
itself since).

## The actual bug (pre-fix code, from `git show 9e8946a`'s diff)

`src/lora/lora_data.py`, `GenerativeDataset.__getitem__` (pre-fix, diff context lines):

```python
        item = {"instanceID": inst["instanceID"]}
        labels = inst.get("labels")
        if labels:
            ...
            chunks = format_completion_chunks(labels, st2_weights, st3_weights)
            completion_ids, weight_per_tok = [], []
            for text, weight in chunks:
                ids = self.tokenizer(text, add_special_tokens=False)["input_ids"]
                completion_ids += ids
                weight_per_tok += [weight] * len(ids)
            completion_ids.append(self.tokenizer.eos_token_id)
            weight_per_tok.append(1.0)
            item["input_ids"] = prompt_ids + completion_ids
```

`GenerativeDataset.__init__` took no parameter at all to suppress this — there was no way to tell
the class "this instance has gold labels, but don't put them in `input_ids`."

`src/lora/lora_train_generative.py` (pre-fix), where `dev_ds` and the test-holdout dataset were
built with the identical constructor call used for `train_ds`:

```python
    train_ds = GenerativeDataset(train_instances, tokenizer, args.context, args.max_length,
                                 system_prompt, df_text, st3_loss_weight=args.st3_loss_weight,
                                 st2_pos_weight=st2_pos_weight, st3_pos_weight=st3_pos_weight)
    dev_ds = GenerativeDataset(dev_instances, tokenizer, args.context, args.max_length,
                               system_prompt, df_text)
    ...
        ids, preds = generate_predictions(model, dev_loader, tokenizer, args.max_new_tokens)
```

and further down, for the test-holdout pass:

```python
            test_loader = DataLoader(
                GenerativeDataset(test_holdout_instances, tokenizer, args.context, args.max_length,
                                  system_prompt, df_text),
                batch_size=eval_batch_size, shuffle=False, collate_fn=collate,
            )
            test_ids, test_preds = generate_predictions(test_model, test_loader, tokenizer, args.max_new_tokens)
```

Since `dev_instances`/`test_holdout_instances` carry `inst["labels"]` (needed later for `evaluate()`),
`dev_ds`/the test dataset built completion-appended `input_ids`, and those full sequences (prompt +
gold JSON + eos) were passed as `batch["input_ids"]` straight into `model.generate()` inside
`generate_predictions` (`src/lora/lora_generative.py`, pre-fix) — which just calls
`model.generate(input_ids=batch["input_ids"][rows], ...)` and then decodes
`out[:, prompt_len:]` as "the prediction," where `prompt_len = batch["input_ids"].shape[1]` — i.e.
`prompt_len` was actually the length of prompt+gold-answer, not just the prompt. So the "prediction"
being scored was whatever token continuation followed the model's own already-correct answer.

## Exactly how the fix works (current code, as of HEAD)

`src/lora/lora_data.py`, `GenerativeDataset.__init__` (current, lines ~105–121) adds the flag:

```python
    def __init__(self, instances: list, tokenizer, context: str = "full", max_length: int = 4096,
                 system_prompt: str = SYSTEM_PROMPT, df_text: str = None, st3_loss_weight: float = 1.0,
                 st2_pos_weight: dict = None, st3_pos_weight: dict = None, st3_only: bool = False,
                 st12_only: bool = False, include_completion: bool = True):
        ...
        self.include_completion = include_completion
```

and `__getitem__` (current, lines ~178–203) gates on both conditions:

```python
        item = {"instanceID": inst["instanceID"]}
        labels = inst.get("labels")
        if labels and self.include_completion:
            ...
            item["input_ids"] = prompt_ids + completion_ids
            item["attention_mask"] = [1] * len(item["input_ids"])
            item["labels"] = [-100] * len(prompt_ids) + completion_ids
            item["loss_weight"] = [1.0] * len(prompt_ids) + weight_per_tok
        else:
            item["input_ids"] = prompt_ids
            item["attention_mask"] = [1] * len(prompt_ids)
        return item
```

Call sites in current `src/lora/lora_train_generative.py`:

- `train_ds` (line 303–306): constructed with no `include_completion` arg, so it defaults to `True`
  — correct, training needs the completion as the supervision target.
- `dev_ds` (lines 307–309):
  ```python
      dev_ds = GenerativeDataset(dev_instances, tokenizer, args.context, args.max_length,
                                 system_prompt, df_text, st3_only=args.st3_only,
                                 st12_only=args.st12_only, include_completion=False)
  ```
- test-holdout dataset (lines 413–416):
  ```python
              GenerativeDataset(test_holdout_instances, tokenizer, args.context, args.max_length,
                                system_prompt, df_text, st3_only=args.st3_only,
                                st12_only=args.st12_only, include_completion=False),
  ```

Current `src/lora/lora_predict_generative.py` (lines 102–104), the standalone inference script:

```python
    loader = DataLoader(
        GenerativeDataset(instances, tokenizer, args.context, args.max_length, system_prompt, df_text,
                          include_completion=False),
        batch_size=args.batch_size, shuffle=False, collate_fn=GenerativeCollator(tokenizer),
    )
```

All three generation-bound call sites explicitly pass `include_completion=False`; only the one
training call site relies on the (correct) default of `True`. I traced every constructor call to
`GenerativeDataset` in the current tree (`grep -n "GenerativeDataset(" src/lora/*.py`) and confirmed
there are exactly these four call sites — no others exist that could still be leaking.

## The `load_data`/`load_split` claim: confirmed correct, and not in tension with the leak

There is no function literally named `load_data` anywhere in the repo (`grep -rn "def load_data\b"`
returns nothing); the user's "load_data" refers to `starting_kit/load_data.py`, whose actual
public functions are `load_split`, `transcript_only`, and `full_context`. Its entire content:

```python
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
```

`load_split` is a pure generator over a JSONL file: `json.loads(line)` for each non-blank line,
yielded as-is. It has no concept of a prompt, a chat template, or `model.generate()`. It does not
even know the field is called `"labels"` — it just returns whatever the release JSONL happens to
contain per instance, which includes `"labels"` (dev/test releases in this dataset carry gold
labels by design, since the harness needs them for scoring). **`load_split` never leaks.** The
user's claim is correct.

Import chain, traced directly (not assumed): `starting_kit/load_data.py:load_split` is imported by
`src/common/__init__.py` (`from load_data import full_context, load_split, transcript_only`, after
adding `starting_kit/` to `sys.path`), which is in turn re-exported by `src/lora/__init__.py`
(`from common import (..., load_split, ...)`), and finally used in
`src/lora/lora_train_generative.py` as `train_instances = list(load_split(args.train))` /
`dev_instances = list(load_split(args.dev))`, and in `src/lora/lora_data.py`'s
`GenerativeDataset` via `from . import ... load_split ...` (re-exported, not directly used inside
the dataset class itself — the dataset takes already-loaded instance lists as its constructor
argument).

Why this is compatible with the leak having been real: **returning gold labels as data is not the
same operation as leaking gold labels into a model input.** `load_split` performs the former —
it's just a JSONL reader, and dev/test instances legitimately need to carry gold labels so that
downstream code (`evaluate()` in `baseline_gpt.py`/`common/__init__.py`) has something to score
predictions against. That's normal, necessary, and not a bug. The bug was a *second, separate*
transformation, several layers downstream of `load_split`: `GenerativeDataset.__getitem__` in
`src/lora/lora_data.py` took those already-loaded instance dicts (which correctly contain
`"labels"`) and — because its own logic couldn't distinguish "building a training example" from
"building a generation prompt" — spliced the gold-label JSON directly into the token sequence
handed to `model.generate()`. `load_split` supplies the raw material; `GenerativeDataset` is where
that raw material either correctly becomes a training target or, pre-fix, incorrectly leaked into
an eval-time model input. The user's intuition that `load_data` "never leaks" is correct, and it
correctly locates the fault outside of it, in `GenerativeDataset`.

## Empirical evidence (from `runs/lora-qwen/results.csv`, quoted verbatim)

The CSV has a `commit` column recording which commit produced each row, which makes a genuine
before/after comparison possible. Header:

```
commit,test_mean_macro_f1,test_st1_macro_f1,test_st2_macro_f1,test_st3_macro_f1,test_st3_family_macro_f1,dev_mean_macro_f1,dev_st1_macro_f1,dev_st2_macro_f1,dev_st3_macro_f1,dev_st3_family_macro_f1,model,status,description
```

**Row at file line 16** (commit `2595582`, *pre-fix*, `--context transcript`, full st1/st2/st3
completion, epochs=2, `--pos-weight`, `split_seed=1260877750`):

```
test_mean_macro_f1=0.586, test_st3_macro_f1=0.549
dev_mean_macro_f1=0.605,  dev_st3_macro_f1=0.608
```

**Row at file line 17** (commit `9e8946a`, *post-fix*, same `--context transcript`, but
`--st3-only` mode, matched epochs=2, `--pos-weight`, `split_seed=487509613`):

```
test_st3_macro_f1=0.200
dev_st3_macro_f1=0.201
```

The row's own description states: "Compare to the PRE-FIX transcript-context row (commit
`2595582`, this same context level, full st1/st2/st3 completion, not st3-only): that row reported
dev st3=0.608/test=0.549 — roughly 3x higher than this genuine number." I independently confirm
those two numbers are exactly what's in the CSV (0.608/0.549 vs 0.201/0.200). Caveat I'm flagging
myself: this pair is matched on context level and epoch count but **not** on completion mode (full
three-key JSON vs `--st3-only`'s single-key JSON), so it is not a perfectly clean ablation of the
leak in isolation — some of the gap could in principle reflect the completion-mode difference
rather than purely the leak. Row at file line 24 addresses that gap.

**Row at file line 24** (commit `3764dad`, *post-fix*, `--context transcript`, **full**
st1/st2/st3 completion — i.e. same completion mode as the line-16 row — epochs raised 2→5,
`--final-eval-only`, smaller n=100 dev/test-holdout subsamples):

```
test_mean_macro_f1=0.483, test_st3_macro_f1=0.357
dev_mean_macro_f1=0.439,  dev_st3_macro_f1=0.374
```

This row's own description is explicit that it is *not* a replication of the line-16 number:
"row 16 (commit 2595582) predates the eval-leakage fix (9e8946a, ...) — its dev=0.605/test=0.586
mean_macro_f1 and st3=0.608/0.549 are inflated (dev/test prompts had the gold answer embedded, model
just echoed it), NOT a valid target to compare against. This row is the trustworthy post-fix
measurement of the same recipe, not a replication of row 16's number." Even accounting for the
epoch count and holdout-size differences between these two rows, post-fix `test_mean_macro_f1`
(0.483) and `test_st3_macro_f1` (0.357) are both substantially below the pre-fix numbers at the same
context level (0.586 / 0.549) — consistent in direction and rough magnitude with the st3-only
comparison above.

Both post-fix comparisons point the same way: matched-context pre-fix numbers were inflated by a
factor of roughly 1.5–3x on st3 specifically, corroborating the mechanism described in the fix
commit (the model was "predicting" a continuation of its own already-correct answer).

## What this means going forward

Any `lora_train_generative.py`/`lora_predict_generative.py` dev or test-holdout result recorded at
a commit **before** `9e8946a4047020b5b0f67739bd71ca068de72669` used the leaking code path and
should be treated as invalid — not usable for model comparison, hyperparameter selection, or
publication. Concretely, in `runs/lora-qwen/results.csv` that is every row whose `commit` column is
one of: `1294f42`, `2806f83`, `fb7f866`, `2595582` (or any earlier commit) — i.e. file lines
2 through 16 inclusive in the current CSV. Rows whose `commit` is `9e8946a` or later
(`9e8946a`, `3764dad`, and anything after) used the fixed `include_completion=False` path for
dev/test and are the only numbers in that file that should be trusted for eval purposes. Training
loss/metrics themselves were never affected (`train_ds` always intentionally included the
completion), only dev/test-holdout/predict evaluation numbers were inflated.
