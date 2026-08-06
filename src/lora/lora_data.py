"""Dataset/collation for the LoRA encoder pipeline.

Reuses `transcript_only`/`full_context` from starting_kit/load_data.py (same input
framing as the LLM baselines) and the ST1/ST2/ST3 label orderings from baseline_gpt.py,
so label indices line up across baselines and predictions round-trip through the same
submission schema / check_submission.py validator.
"""
import json

import torch
from torch.utils.data import Dataset

from . import ( 
    ST1_LABELS, ST2_LABELS, ST3_LABELS, SYSTEM_PROMPT, full_context, load_split, transcript_only,
)

ST1_INDEX = {label: i for i, label in enumerate(ST1_LABELS)}
ST2_INDEX = {label: i for i, label in enumerate(ST2_LABELS)}
ST3_INDEX = {label: i for i, label in enumerate(ST3_LABELS)}


def multi_hot(flags, index: dict) -> list:
    vec = [0.0] * len(index)
    for f in flags:
        if f in index:
            vec[index[f]] = 1.0
    return vec


class ClassificationDataset(Dataset):
    def __init__(self, instances: list, tokenizer, context: str = "full", max_length: int = 512):
        self.instances = instances
        self.tokenizer = tokenizer
        self.context = context
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.instances)

    def __getitem__(self, idx: int) -> dict:
        inst = self.instances[idx]
        text = full_context(inst) if self.context == "full" else transcript_only(inst)
        enc = self.tokenizer(text, truncation=True, max_length=self.max_length)
        item = {
            "instanceID": inst["instanceID"],
            "input_ids": enc["input_ids"],
            "attention_mask": enc["attention_mask"],
        }
        labels = inst.get("labels")
        if labels:
            item["st1_label"] = ST1_INDEX[labels["st1"]]
            item["st2_label"] = multi_hot(labels["st2"], ST2_INDEX)
            item["st3_label"] = multi_hot(labels["st3"], ST3_INDEX)
        return item


class Collator:
    """Dynamic padding via the tokenizer, keeping instanceIDs and stacking labels
    (only present when the batch's instances carry gold labels, i.e. train/dev)."""

    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def __call__(self, batch: list) -> dict:
        encodings = [{"input_ids": b["input_ids"], "attention_mask": b["attention_mask"]} for b in batch]
        padded = self.tokenizer.pad(encodings, return_tensors="pt")
        out = {"instanceID": [b["instanceID"] for b in batch], **padded}
        if "st1_label" in batch[0]:
            out["st1_labels"] = torch.tensor([b["st1_label"] for b in batch], dtype=torch.long)
            out["st2_labels"] = torch.tensor([b["st2_label"] for b in batch], dtype=torch.float)
            out["st3_labels"] = torch.tensor([b["st3_label"] for b in batch], dtype=torch.float)
        return out


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
