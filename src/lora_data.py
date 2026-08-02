"""Dataset/collation for the LoRA encoder pipeline.

Reuses `transcript_only`/`full_context` from starting_kit/load_data.py (same input
framing as the LLM baselines) and the ST1/ST2/ST3 label orderings from baseline_gpt.py,
so label indices line up across baselines and predictions round-trip through the same
submission schema / check_submission.py validator.
"""
import os
import sys

import torch
from torch.utils.data import Dataset

sys.path.insert(0, os.path.dirname(__file__))
from baseline_gpt import ST1_LABELS, ST2_LABELS, ST3_LABELS  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "starting_kit"))
from load_data import full_context, load_split, transcript_only  # noqa: E402

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
