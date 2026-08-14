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
from typing import List, Literal

import torch
from pydantic import BaseModel, ValidationError
from tqdm import tqdm

from . import ST3_LABELS, Prediction, sanitize_st3  # noqa: F401

MAX_ATTEMPTS = 3
_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


class St3OnlyPrediction(BaseModel):
    """Schema for --st3-only mode's completion, which drops st1/st2 from the JSON
    entirely (see GenerativeDataset/format_completion_chunks's st3_only branch in
    lora_data.py) so every completion token trains st3 -- none are spent on subtasks
    --st3-only isn't scoring."""
    st3: List[Literal[tuple(ST3_LABELS)]]


def parse_completion(text: str, st3_only: bool = False) -> dict | None:
    """Extract+validate a JSON object from a freeform completion against the Prediction
    schema (or St3OnlyPrediction, in --st3-only mode). Returns None (rather than a fallback
    dict) so the caller can tell a parse failure apart from a genuine prediction and decide
    whether to retry. In --st3-only mode st1/st2 are filled with a fixed placeholder
    ("other"/[]) -- common.evaluate() always scores all three subtasks, and write_submission
    needs a complete prediction dict, but those two values are never trained/meaningful here;
    only st3_macro_f1/st3_family_macro_f1 should be read from the result."""
    match = _JSON_RE.search(text)
    if not match:
        return None
    try:
        if st3_only:
            pred = St3OnlyPrediction.model_validate_json(match.group(0))
            return {"st1": "other", "st2": [], "st3": sanitize_st3(list(pred.st3))}
        pred = Prediction.model_validate_json(match.group(0))
    except ValidationError:
        return None
    return {"st1": pred.st1, "st2": list(pred.st2), "st3": sanitize_st3(list(pred.st3))}


def _fallback() -> dict:
    return {"st1": "other", "st2": [], "st3": sanitize_st3([])}


def _to_device(batch: dict, device: str) -> dict:
    return {k: (v.to(device) if torch.is_tensor(v) else v) for k, v in batch.items()}


@torch.no_grad()
def generate_predictions(model, loader, tokenizer, max_new_tokens: int, st3_only: bool = False, log=None) -> tuple:
    """Batched freeform generation over `loader`. Requires `loader`'s collator to have
    left-padded input_ids/attention_mask (set tokenizer.padding_side = "left" before building
    it) so every sequence's prompt ends at the same position and `out[:, prompt_len:]` is
    exactly the new tokens for the whole batch. `st3_only` must match how the model was
    trained (see GenerativeDataset's st3_only) -- it only changes which schema completions
    are parsed against, not generation itself.

    Items that fail to parse are regenerated (sampled, sub-batched to just the failing rows)
    up to MAX_ATTEMPTS times; anything still unparseable after that falls back to a default
    prediction rather than retrying forever. Returns (instanceIDs, predictions), both in
    loader-iteration order.

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
                do_sample=attempt > 0,  # first try greedy; retries sample so they can differ
                temperature=0.7 if attempt > 0 else None,
                pad_token_id=tokenizer.pad_token_id,
            )
            still_pending = []
            for row_idx, gen_row in zip(pending, out[:, prompt_len:]):
                pred = parse_completion(tokenizer.decode(gen_row, skip_special_tokens=True), st3_only=st3_only)
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
