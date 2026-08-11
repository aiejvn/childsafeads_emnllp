"""Dataset/collation for encoder classification pipelines (shared by src/lora and
src/last_layer). Reuses `transcript_only`/`full_context` from starting_kit/load_data.py
(same input framing as the LLM baselines) and the ST1/ST2/ST3 label orderings from
baseline_gpt.py, so label indices line up across baselines and predictions round-trip
through the same submission schema / check_submission.py validator.
"""
import torch
from torch.utils.data import Dataset

from . import ST1_LABELS, ST2_LABELS, ST3_LABELS, render_context

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
    def __init__(self, instances: list, tokenizer, context: str = "full", max_length: int = 512, df_text: str = None):
        self.instances = instances
        self.tokenizer = tokenizer
        self.context = context
        self.max_length = max_length
        self.df_text = df_text  # autoDF flow graph rendered as Mermaid (see greaselm.kg.build_kg.build_flow_kg /
        # KnowledgeGraph.to_mermaid), prepended before each instance's text so it's tokenized first

    def __len__(self) -> int:
        return len(self.instances)

    def __getitem__(self, idx: int) -> dict:
        inst = self.instances[idx]
        text = render_context(inst, self.context)
        if self.df_text:
            text = self.df_text + "\n\n" + text
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
    """Dynamic padding via `tokenizer.pad()`, which pads on `tokenizer.padding_side`
    (right, for the encoder tokenizers this pipeline uses -- RoBERTa/BERT-family --
    since unlike decoder-only generation, encoder attention has no causal-position
    sensitivity that would require left-padding). Keeps instanceIDs alongside the
    padded batch and stacks labels (only present when the batch's instances carry
    gold labels, i.e. train/dev)."""

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
