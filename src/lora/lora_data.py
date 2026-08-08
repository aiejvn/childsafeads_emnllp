"""Dataset/collation for the LoRA encoder pipeline.

`ClassificationDataset`/`Collator`/`multi_hot` (used by the classification/encoder path)
now live in `common/classification_data.py`, shared with `src/last_layer`; re-exported
here for backwards compatibility since `lora_train.py`/`lora_predict.py` import them
from this module. Only the generative/causal-LM path (`GenerativeDataset` and friends,
below) is LoRA-specific and stays defined here.
"""
import json
import os
import sys

import torch
from torch.utils.data import Dataset

from . import SYSTEM_PROMPT, full_context, load_split, transcript_only  # noqa: F401 (load_split re-exported)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common.classification_data import (  # noqa: E402,F401 (re-exported for lora_train.py/lora_predict.py)
    ClassificationDataset, Collator, ST1_INDEX, ST2_INDEX, ST3_INDEX, multi_hot,
)

COMPLETION_TOKEN_BUDGET = 96  # slack reserved out of max_length for the JSON completion + eos
_SEGMENT_PLACEHOLDER = "\x00SEGMENT_TEXT\x00"  # never occurs in real transcripts; marks the splice point


def format_completion(labels: dict) -> str:
    """Gold st1/st2/st3 rendered as JSON matching baseline_gpt.py's `Prediction` schema --
    this is the text the causal LM is trained to generate."""
    pred = {"st1": labels["st1"], "st2": sorted(labels["st2"]), "st3": sorted(labels["st3"])}
    return json.dumps(pred, separators=(",", ":"))


class GenerativeDataset(Dataset):
    """Formats each instance as the same zero-shot chat prompt used for the GPT baseline
    (SYSTEM_PROMPT + "SEGMENT DATA:\\n\\n{text}"), with the gold label rendered as a JSON
    completion. `labels` is -100 over the prompt tokens so cross-entropy only applies to the
    completion, i.e. standard causal-LM SFT. Instances without gold labels (predict-only
    splits) yield prompt-only input_ids/attention_mask for `model.generate()`.

    The segment text is the only part of the prompt long enough to need truncating, and its
    length varies per-instance while the surrounding chat-template scaffolding (system
    prompt/taxonomy, role markers, generation-prompt marker) doesn't -- so the prefix/suffix
    around it are tokenized once in __init__ (split on a placeholder) and only the text's own
    tokens are truncated per-item, then spliced back in. This avoids re-tokenizing the whole
    (long, mostly-fixed) prompt on every __getitem__ call.
    """

    def __init__(self, instances: list, tokenizer, context: str = "full", max_length: int = 4096):
        self.instances = instances
        self.tokenizer = tokenizer
        self.context = context
        self.max_length = max_length

        rendered = self._render_prompt(_SEGMENT_PLACEHOLDER)
        prefix_str, suffix_str = rendered.split(_SEGMENT_PLACEHOLDER)
        self.prefix_ids = tokenizer(prefix_str, add_special_tokens=False)["input_ids"]
        self.suffix_ids = tokenizer(suffix_str, add_special_tokens=False)["input_ids"]

    def __len__(self) -> int:
        return len(self.instances)

    def _render_prompt(self, text: str) -> str:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"SEGMENT DATA:\n\n{text}"},
        ]
        return self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    def __getitem__(self, idx: int) -> dict:
        inst = self.instances[idx]
        text = full_context(inst) if self.context == "full" else transcript_only(inst)

        text_budget = max(1, self.max_length - len(self.prefix_ids) - len(self.suffix_ids) - COMPLETION_TOKEN_BUDGET)
        text_ids = self.tokenizer(text, truncation=True, max_length=text_budget, add_special_tokens=False)["input_ids"]
        prompt_ids = self.prefix_ids + text_ids + self.suffix_ids

        item = {"instanceID": inst["instanceID"]}
        labels = inst.get("labels")
        if labels:
            completion_ids = self.tokenizer(
                format_completion(labels) + self.tokenizer.eos_token, add_special_tokens=False,
            )["input_ids"]
            item["input_ids"] = prompt_ids + completion_ids
            item["attention_mask"] = [1] * len(item["input_ids"])
            item["labels"] = [-100] * len(prompt_ids) + completion_ids
        else:
            item["input_ids"] = prompt_ids
            item["attention_mask"] = [1] * len(prompt_ids)
        return item


class GenerativeCollator:
    """Pads input_ids/attention_mask on `tokenizer.padding_side` (right during training so
    the loss-masked `labels` line up token-for-token; set to left before any batched
    `model.generate()` call, since decoder-only generation needs left-padding), padding
    `labels` (when present) with -100 to match."""

    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def __call__(self, batch: list) -> dict:
        has_labels = "labels" in batch[0]
        max_len = max(len(b["input_ids"]) for b in batch)
        pad_id = self.tokenizer.pad_token_id
        left = self.tokenizer.padding_side == "left"

        input_ids, attention_mask, labels = [], [], []
        for b in batch:
            pad_n = max_len - len(b["input_ids"])
            pad_ids = [pad_id] * pad_n
            pad_mask = [0] * pad_n
            if left:
                input_ids.append(pad_ids + b["input_ids"])
                attention_mask.append(pad_mask + b["attention_mask"])
                if has_labels:
                    labels.append([-100] * pad_n + b["labels"])
            else:
                input_ids.append(b["input_ids"] + pad_ids)
                attention_mask.append(b["attention_mask"] + pad_mask)
                if has_labels:
                    labels.append(b["labels"] + [-100] * pad_n)

        out = {
            "instanceID": [b["instanceID"] for b in batch],
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
        }
        if has_labels:
            out["labels"] = torch.tensor(labels, dtype=torch.long)
        return out
