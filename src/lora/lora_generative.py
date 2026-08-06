"""Structured-generation decode helpers shared by lora_train_generative.py (per-epoch dev
eval) and lora_predict_generative.py (final inference), so the two scripts don't duplicate
the generate()/parse loop.

Decoding is constrained to baseline_gpt.py's `Prediction` JSON schema via lm-format-enforcer
(https://github.com/noamgat/lm-format-enforcer), so the model can't emit invalid st1/st2/st3
labels or malformed JSON -- unlike the freeform-generate-then-regex-parse approach, output is
schema-valid by construction.
"""
import json

import torch
from lmformatenforcer import JsonSchemaParser
from lmformatenforcer.integrations.transformers import build_transformers_prefix_allowed_tokens_fn
from tqdm import tqdm

from . import Prediction, sanitize_st3  # noqa: F401


def build_prefix_allowed_tokens_fn(tokenizer):
    parser = JsonSchemaParser(Prediction.model_json_schema())
    return build_transformers_prefix_allowed_tokens_fn(tokenizer, parser)


def parse_completion(text: str) -> dict:
    """Schema-constrained generation should always yield valid JSON, but fall back the same
    way baseline_gpt.py does (st1="other") if something still goes wrong."""
    try:
        pred = json.loads(text)
        return {
            "st1": pred["st1"],
            "st2": list(pred.get("st2", [])),
            "st3": sanitize_st3(list(pred.get("st3", []))),
        }
    except (json.JSONDecodeError, KeyError, TypeError):
        return {"st1": "other", "st2": [], "st3": sanitize_st3([])}


def _to_device(batch: dict, device: str) -> dict:
    return {k: (v.to(device) if torch.is_tensor(v) else v) for k, v in batch.items()}


@torch.no_grad()
def generate_predictions(model, loader, tokenizer, device: str, max_new_tokens: int) -> tuple:
    """Batched structured generation over `loader`. Requires `loader`'s collator to have
    left-padded input_ids/attention_mask (set tokenizer.padding_side = "left" before building
    it) so every sequence's prompt ends at the same position and `out[:, prompt_len:]` is
    exactly the new tokens for the whole batch. Returns (instanceIDs, predictions), both in
    loader-iteration order.
    """
    prefix_fn = build_prefix_allowed_tokens_fn(tokenizer)
    ids, preds = [], []
    model.eval()
    for batch in tqdm(loader, desc="generating"):
        batch = _to_device(batch, device)
        prompt_len = batch["input_ids"].shape[1]
        out = model.generate(
            input_ids=batch["input_ids"],
            attention_mask=batch["attention_mask"],
            prefix_allowed_tokens_fn=prefix_fn,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
        )
        ids.extend(batch["instanceID"])
        for row in out[:, prompt_len:]:
            preds.append(parse_completion(tokenizer.decode(row, skip_special_tokens=True)))
    return ids, preds
