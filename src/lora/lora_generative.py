"""Freeform-generation decode helpers shared by lora_train_generative.py (per-epoch dev eval)
and lora_predict_generative.py (final inference), so the two scripts don't duplicate the
generate()/parse loop.

The model is fine-tuned to emit a JSON completion matching baseline_gpt.py's `Prediction`
schema directly (see GenerativeDataset.format_completion in lora_data.py), so at decode time we
just ask it to generate and parse the result -- no constrained/structured-generation library.
If a generation doesn't parse into a valid `Prediction`, we regenerate (sampling, so a retry can
actually differ from the failed attempt) up to MAX_ATTEMPTS times per item before giving up and
falling back to a safe default, the same way baseline_gpt.py does on API errors.
"""
import os
import re
from collections import Counter
from typing import List, Literal

import torch
from pydantic import BaseModel, ValidationError
from tqdm import tqdm

from . import ST1_LABELS, ST2_LABELS, ST3_LABELS, Prediction, sanitize_st3  # noqa: F401

MAX_ATTEMPTS = 3
_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


class St3OnlyPrediction(BaseModel):
    """Schema for --st3-only mode's completion, which drops st1/st2 from the JSON
    entirely (see GenerativeDataset/format_completion_chunks's st3_only branch in
    lora_data.py) so every completion token trains st3 -- none are spent on subtasks
    --st3-only isn't scoring."""
    st3: List[Literal[tuple(ST3_LABELS)]]


class St12OnlyPrediction(BaseModel):
    """Schema for --st12-only mode's completion, the mirror image of St3OnlyPrediction:
    drops st3 from the JSON entirely (see format_completion_chunks's st12_only branch in
    lora_data.py) so every completion token trains st1/st2."""
    st1: Literal[tuple(ST1_LABELS)]
    st2: List[Literal[tuple(ST2_LABELS)]]


class St1OnlyPrediction(BaseModel):
    """Schema for --st1-only mode's completion: drops st2/st3 both, leaving just
    `{"st1":...}` (see format_completion_chunks's st1_only branch in lora_data.py) so
    every completion token trains st1 alone."""
    st1: Literal[tuple(ST1_LABELS)]


def parse_completion(text: str, st3_only: bool = False, st12_only: bool = False,
                     st1_only: bool = False) -> dict | None:
    """Extract+validate a JSON object from a freeform completion against the Prediction
    schema (or St3OnlyPrediction/St12OnlyPrediction/St1OnlyPrediction, in --st3-only/
    --st12-only/--st1-only mode). Returns None (rather than a fallback dict) so the caller
    can tell a parse failure apart from a genuine prediction and decide whether to retry.
    In --st3-only mode st1/st2 are filled with a fixed placeholder ("other"/[]); in
    --st12-only mode st3 is filled with a fixed placeholder (sanitize_st3([]), i.e.
    ["insufficient_context"]); in --st1-only mode both st2/st3 get their placeholders --
    common.evaluate() always scores all three subtasks, and write_submission needs a
    complete prediction dict, but the placeholder tier(s) are never trained/meaningful in
    that mode; only the tier(s) that mode actually trains should be read from the result."""
    match = _JSON_RE.search(text)
    if not match:
        return None
    try:
        if st1_only:
            pred = St1OnlyPrediction.model_validate_json(match.group(0))
            return {"st1": pred.st1, "st2": [], "st3": sanitize_st3([])}
        if st3_only:
            pred = St3OnlyPrediction.model_validate_json(match.group(0))
            return {"st1": "other", "st2": [], "st3": sanitize_st3(list(pred.st3))}
        if st12_only:
            pred = St12OnlyPrediction.model_validate_json(match.group(0))
            return {"st1": pred.st1, "st2": list(pred.st2), "st3": sanitize_st3([])}
        pred = Prediction.model_validate_json(match.group(0))
    except ValidationError:
        return None
    return {"st1": pred.st1, "st2": list(pred.st2), "st3": sanitize_st3(list(pred.st3))}


def _fallback() -> dict:
    return {"st1": "other", "st2": [], "st3": sanitize_st3([])}


def _to_device(batch: dict, device: str) -> dict:
    return {k: (v.to(device) if torch.is_tensor(v) else v) for k, v in batch.items()}


@torch.no_grad()
def generate_predictions(model, loader, tokenizer, max_new_tokens: int, st3_only: bool = False,
                         st12_only: bool = False, st1_only: bool = False, log=None,
                         force_sample: bool = False, temperature: float = 0.7) -> tuple:
    """Batched freeform generation over `loader`. Requires `loader`'s collator to have
    left-padded input_ids/attention_mask (set tokenizer.padding_side = "left" before building
    it) so every sequence's prompt ends at the same position and `out[:, prompt_len:]` is
    exactly the new tokens for the whole batch. `st3_only`/`st12_only`/`st1_only` must match
    how the model was trained (see GenerativeDataset's st3_only/st12_only/st1_only) -- they
    only change which schema completions are parsed against, not generation itself.

    Items that fail to parse are regenerated (sampled, sub-batched to just the failing rows)
    up to MAX_ATTEMPTS times; anything still unparseable after that falls back to a default
    prediction rather than retrying forever. Returns (instanceIDs, predictions), both in
    loader-iteration order.

    `force_sample` (default False, the original behavior: greedy on the first attempt, only
    sampled on parse-failure retries) makes every attempt -- including the first -- sample at
    `temperature` instead of decoding greedily. Set it when the caller wants K independently
    varied completions per instance (self-consistency voting -- see
    lora_predict_generative_selfconsistent.py/lora_calibrate_thresholds_generative.py): calling
    this function K times with force_sample=False would return the identical greedy completion
    all K times, since only the (rare) parse-failure retry path ever samples.

    Batches are moved to `model.device` rather than a caller-supplied device string, since
    that's correct whether the model sits on one GPU or is dispatched across several via
    `--parallelism pipeline`/`tensor` (see lora_model.py's build/load_peft_model_causal).

    If `log` is given, logs a min/mean/max summary of each instance's real (unpadded) input
    length in tokens once generation finishes -- useful for comparing --context levels, whose
    prompts can differ by thousands of tokens."""
    ids, preds = [], []
    seq_lens = []
    model.eval()
    device = model.device
    is_main = int(os.environ.get("RANK", "0")) == 0  # avoid duplicate progress bars under --parallelism tensor
    for batch in tqdm(loader, desc="generating", disable=not is_main):
        batch = _to_device(batch, device)
        prompt_len = batch["input_ids"].shape[1]
        seq_lens.extend(batch["attention_mask"].sum(dim=1).tolist())
        pending = list(range(batch["input_ids"].shape[0]))
        batch_preds = [None] * len(pending)

        for attempt in range(MAX_ATTEMPTS):
            rows = torch.tensor(pending, device=device)
            out = model.generate(
                input_ids=batch["input_ids"][rows],
                attention_mask=batch["attention_mask"][rows],
                max_new_tokens=max_new_tokens,
                do_sample=force_sample or attempt > 0,  # first try greedy; retries sample so they can differ
                temperature=temperature if (force_sample or attempt > 0) else None,
                pad_token_id=tokenizer.pad_token_id,
            )
            still_pending = []
            for row_idx, gen_row in zip(pending, out[:, prompt_len:]):
                pred = parse_completion(tokenizer.decode(gen_row, skip_special_tokens=True),
                                        st3_only=st3_only, st12_only=st12_only, st1_only=st1_only)
                if pred is None:
                    still_pending.append(row_idx)
                else:
                    batch_preds[row_idx] = pred
            pending = still_pending
            if not pending:
                break

        for row_idx in pending:
            batch_preds[row_idx] = _fallback()

        ids.extend(batch["instanceID"])
        preds.extend(batch_preds)
    if log is not None and seq_lens:
        log.info(f"generate_predictions: input length (tokens, unpadded) -- "
                 f"min={min(seq_lens)} mean={sum(seq_lens) / len(seq_lens):.0f} max={max(seq_lens)} n={len(seq_lens)}")
    return ids, preds


@torch.no_grad()
def self_consistency_probs(model, loader, tokenizer, max_new_tokens: int, k: int, temperature: float = 0.7,
                           st3_only: bool = False, st12_only: bool = False, st1_only: bool = False,
                           log=None) -> tuple:
    """Runs `generate_predictions(..., force_sample=True)` k times over `loader` and
    aggregates per-instance/per-label vote frequencies -- the self-consistency signal both
    lora_predict_generative_selfconsistent.py (majority-vote decode) and
    lora_calibrate_thresholds_generative.py (frequency as a pseudo-probability, fed into
    common/predict_utils.tune_per_label_thresholds) build on, so the k-sample loop only
    lives in one place. Returns (ids, st1_votes, st2_freq, st3_freq):
      - ids: instanceIDs, loader-iteration order (matches st1_votes/st2_freq/st3_freq's order)
      - st1_votes: list[Counter], one per instance, tallying its k sampled st1 labels
      - st2_freq / st3_freq: torch.Tensor [n_instances, n_labels], each entry the fraction of
        the k samples (in [0, 1]) that included that label -- same shape/range as the encoder
        pipeline's sigmoid outputs (predict_utils.run_inference), so it's a drop-in input to
        tune_per_label_thresholds/decode without either of those needing to know it came from
        vote-counting rather than a classification head.

    Runs k full passes over the whole of `loader` -- callers that only want to spend this cost
    on a subset of instances (e.g. ones a cheap prior greedy pass flagged as touching a fragile
    label) should build `loader` over just that subset rather than filtering after the fact.
    `loader` must not shuffle -- instance order must be identical across the k passes for the
    per-index aggregation below to line up."""
    ids_ref = None
    st1_lists, st2_lists, st3_lists = None, None, None
    for sample_idx in range(k):
        ids, preds = generate_predictions(
            model, loader, tokenizer, max_new_tokens, st3_only=st3_only, st12_only=st12_only,
            st1_only=st1_only, log=(log if sample_idx == 0 else None), force_sample=True, temperature=temperature,
        )
        if ids_ref is None:
            ids_ref = ids
            st1_lists = [[] for _ in ids]
            st2_lists = [[] for _ in ids]
            st3_lists = [[] for _ in ids]
        elif ids != ids_ref:
            raise RuntimeError("loader yielded a different instance order across self-consistency "
                                "samples -- build it with shuffle=False")
        for i, pred in enumerate(preds):
            st1_lists[i].append(pred["st1"])
            st2_lists[i].append(pred["st2"])
            st3_lists[i].append(pred["st3"])

    st1_votes = [Counter(labels) for labels in st1_lists]
    st2_freq = torch.zeros(len(ids_ref), len(ST2_LABELS))
    st3_freq = torch.zeros(len(ids_ref), len(ST3_LABELS))
    for i in range(len(ids_ref)):
        # st2_lists[i]/st3_lists[i] are lists of k per-sample label *lists* (multi-label),
        # not k single labels -- flatten one level before counting per-label frequency.
        for sample_labels in st2_lists[i]:
            for label in sample_labels:
                st2_freq[i, ST2_LABELS.index(label)] += 1
        for sample_labels in st3_lists[i]:
            for label in sample_labels:
                st3_freq[i, ST3_LABELS.index(label)] += 1
    st2_freq /= k
    st3_freq /= k
    return ids_ref, st1_votes, st2_freq, st3_freq
