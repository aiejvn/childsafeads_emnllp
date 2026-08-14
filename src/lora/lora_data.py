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
import warnings

import torch
from torch.utils.data import Dataset

from . import SYSTEM_PROMPT, load_split, render_context  # noqa: F401 (load_split re-exported)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common.classification_data import (  # noqa: E402,F401 (re-exported for lora_train.py/lora_predict.py)
    ClassificationDataset, Collator, ST1_INDEX, ST2_INDEX, ST3_INDEX, multi_hot,
)

COMPLETION_TOKEN_BUDGET = 96  # slack reserved out of max_length for the JSON completion + eos
_SEGMENT_PLACEHOLDER = "\x00SEGMENT_TEXT\x00"  # never occurs in real transcripts; marks the splice point


def format_completion(labels: dict) -> str:
    """Gold st1/st2/st3 rendered as JSON matching baseline_gpt.py's `Prediction` schema --
    this is the text the causal LM is trained to generate."""
    return "".join(text for text, _ in format_completion_chunks(labels))


def _quoted_label_chunks(labels_sorted: list, weights: dict) -> list:
    """[(text, weight), ...] for a JSON array of quoted label strings (no brackets --
    the caller supplies those), e.g. ["a","b"] -> [('"a"', w_a), (',', 1.0), ('"b"', w_b)]."""
    chunks = []
    for i, label in enumerate(labels_sorted):
        if i > 0:
            chunks.append((",", 1.0))
        chunks.append((json.dumps(label), weights.get(label, 1.0)))
    return chunks


def format_completion_chunks(
    labels: dict, st2_weights: dict = None, st3_weights: dict = None, st3_only: bool = False,
) -> list:
    """Same rendering as format_completion, split into (text, weight) chunks whose
    concatenated text reproduces format_completion(labels) exactly. Each st2/st3 label's
    own quoted-string token span carries that label's weight (`weights.get(label, 1.0)`);
    st1 and all JSON punctuation stay at weight 1.0. `st2_weights`/`st3_weights` are
    {label: weight} dicts -- e.g. inverse-train-frequency from --pos-weight, or a flat
    per-field multiplier like --st3-loss-weight. Used by GenerativeDataset to build a
    per-token loss_weight array for a custom weighted cross-entropy (see
    lora_train_generative.py's weighted_lm_loss).

    `st3_only` drops st1/st2 from the completion entirely -- `{"st3":[...]}` instead of
    the full three-key object -- so every completion token trains st3 specifically (see
    --st3-only in lora_train_generative.py). Pairs with lora_generative.py's
    St3OnlyPrediction, which parses this shorter schema back out at decode time."""
    st2_weights, st3_weights = st2_weights or {}, st3_weights or {}
    if st3_only:
        chunks = [('{"st3":[', 1.0)]
        chunks += _quoted_label_chunks(sorted(labels["st3"]), st3_weights)
        chunks.append(("]}", 1.0))
        return chunks
    chunks = [(json.dumps({"st1": labels["st1"]}, separators=(",", ":"))[:-1] + ',"st2":[', 1.0)]
    chunks += _quoted_label_chunks(sorted(labels["st2"]), st2_weights)
    chunks.append(('],"st3":[', 1.0))
    chunks += _quoted_label_chunks(sorted(labels["st3"]), st3_weights)
    chunks.append(("]}", 1.0))
    return chunks


class GenerativeDataset(Dataset):
    """Formats each instance as a chat prompt (`system_prompt` + "SEGMENT DATA:\\n\\n{text}"),
    with the gold label rendered as a JSON completion. `labels` is -100 over the prompt tokens
    so cross-entropy only applies to the completion, i.e. standard causal-LM SFT. Instances
    without gold labels (predict-only splits) yield prompt-only input_ids/attention_mask for
    `model.generate()`.

    `system_prompt` defaults to the zero-shot prompt the GPT baseline uses, which keeps the
    input framing identical across baselines; pass `common.SFT_TAXONOMY` instead (the scripts'
    --lean-prompt) to drop the instruction prose and label definitions that 2,353 labelled
    examples supersede, and that otherwise leave only ~470 of 4,096 tokens for the segment.

    The segment text is the only part of the prompt long enough to need truncating, and its
    length varies per-instance while the surrounding chat-template scaffolding (system
    prompt/taxonomy, role markers, generation-prompt marker) doesn't -- so the prefix/suffix
    around it are tokenized once in __init__ (split on a placeholder) and only the text's own
    tokens are truncated per-item, then spliced back in. This avoids re-tokenizing the whole
    (long, mostly-fixed) prompt on every __getitem__ call.
    """

    def __init__(self, instances: list, tokenizer, context: str = "full", max_length: int = 4096,
                 system_prompt: str = SYSTEM_PROMPT, df_text: str = None, st3_loss_weight: float = 1.0,
                 st2_pos_weight: dict = None, st3_pos_weight: dict = None, st3_only: bool = False,
                 include_completion: bool = True):
        self.instances = instances
        self.tokenizer = tokenizer
        self.st3_only = st3_only
        # Whether to append the gold completion to input_ids. True for training (the
        # completion IS the supervision signal). Must be False for anything headed into
        # model.generate() -- dev/test instances carry gold "labels" too (needed for
        # scoring, fetched separately from the raw instance dicts, never from this
        # dataset's per-item "labels" tensor), so `if labels:` alone can't tell training
        # and generation-time use apart. Getting this wrong means generate() is handed a
        # prompt with the correct answer already written into it, and "predicts" a
        # continuation *after* its own gold answer -- inflated, invalid eval numbers.
        self.include_completion = include_completion
        self.context = context
        self.max_length = max_length
        self.st3_loss_weight = st3_loss_weight
        self.st2_pos_weight = st2_pos_weight or {}
        # st3_loss_weight (a flat --st3-loss-weight multiplier) and st3_pos_weight (per-label
        # inverse-frequency from --pos-weight) compose multiplicatively: pos_weight corrects
        # for imbalance *within* st3, st3_loss_weight expresses that the whole st3 subtask
        # matters more than st1/st2 -- independent, both apply if both are set.
        self.st3_pos_weight = {k: v * st3_loss_weight for k, v in (st3_pos_weight or {}).items()}
        self.default_st3_weight = st3_loss_weight
        # df_text joins the system message rather than going in front of the per-instance
        # text the way ClassificationDataset prepends it. It is identical for every
        # instance, so it belongs with the rest of the fixed scaffolding: tokenized once
        # here instead of on every __getitem__, and outside the per-item truncation --
        # which cuts from the front, and would otherwise spend the whole text budget on
        # the flow and leave nothing of the segment.
        self.system_prompt = f"{system_prompt}\n\n{df_text}" if df_text else system_prompt

        rendered = self._render_prompt(_SEGMENT_PLACEHOLDER)
        prefix_str, suffix_str = rendered.split(_SEGMENT_PLACEHOLDER)
        self.prefix_ids = tokenizer(prefix_str, add_special_tokens=False)["input_ids"]
        self.suffix_ids = tokenizer(suffix_str, add_special_tokens=False)["input_ids"]

        # Only the segment text is truncatable, so once the fixed scaffolding fills
        # max_length the text budget hits its max(1, ...) floor and sequences run *past*
        # max_length rather than being clipped to it -- silently, and straight into the
        # fp32 logits tensor that dominates training memory. Warn rather than raise: it's
        # a legitimate if wasteful config, and the predict path has to be free to mirror
        # whatever training used.
        fixed = len(self.prefix_ids) + len(self.suffix_ids) + COMPLETION_TOKEN_BUDGET
        if fixed >= max_length:
            warnings.warn(
                f"fixed prompt scaffolding is {fixed:,} tokens against max_length {max_length:,}: "
                f"the segment text is truncated to 1 token and sequences will still exceed "
                f"max_length. Use --lean-prompt, or raise --max-length.",
                stacklevel=2,
            )

    def __len__(self) -> int:
        return len(self.instances)

    def _render_prompt(self, text: str) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"SEGMENT DATA:\n\n{text}"},
        ]
        return self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    def __getitem__(self, idx: int) -> dict:
        inst = self.instances[idx]
        text = render_context(inst, self.context)

        text_budget = max(1, self.max_length - len(self.prefix_ids) - len(self.suffix_ids) - COMPLETION_TOKEN_BUDGET)
        text_ids = self.tokenizer(text, truncation=True, max_length=text_budget, add_special_tokens=False)["input_ids"]
        prompt_ids = self.prefix_ids + text_ids + self.suffix_ids

        item = {"instanceID": inst["instanceID"]}
        labels = inst.get("labels")
        if labels and self.include_completion:
            # Each st2/st3 label's own quoted-string token span is tokenized separately
            # (same splice-and-concatenate approach as prefix_ids/suffix_ids above) so it
            # can carry its own loss weight -- inverse-train-frequency per label
            # (--pos-weight) and/or a flat st3-wide multiplier (--st3-loss-weight).
            st2_weights = {l: self.st2_pos_weight.get(l, 1.0) for l in labels["st2"]}
            st3_weights = {l: self.st3_pos_weight.get(l, self.default_st3_weight) for l in labels["st3"]}
            chunks = format_completion_chunks(labels, st2_weights, st3_weights, st3_only=self.st3_only)
            completion_ids, weight_per_tok = [], []
            for text, weight in chunks:
                ids = self.tokenizer(text, add_special_tokens=False)["input_ids"]
                completion_ids += ids
                weight_per_tok += [weight] * len(ids)
            completion_ids.append(self.tokenizer.eos_token_id)
            weight_per_tok.append(1.0)
            item["input_ids"] = prompt_ids + completion_ids
            item["attention_mask"] = [1] * len(item["input_ids"])
            item["labels"] = [-100] * len(prompt_ids) + completion_ids
            item["loss_weight"] = [1.0] * len(prompt_ids) + weight_per_tok
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

        input_ids, attention_mask, labels, loss_weight = [], [], [], []
        for b in batch:
            pad_n = max_len - len(b["input_ids"])
            pad_ids = [pad_id] * pad_n
            pad_mask = [0] * pad_n
            if left:
                input_ids.append(pad_ids + b["input_ids"])
                attention_mask.append(pad_mask + b["attention_mask"])
                if has_labels:
                    labels.append([-100] * pad_n + b["labels"])
                    loss_weight.append([0.0] * pad_n + b["loss_weight"])
            else:
                input_ids.append(b["input_ids"] + pad_ids)
                attention_mask.append(b["attention_mask"] + pad_mask)
                if has_labels:
                    labels.append(b["labels"] + [-100] * pad_n)
                    loss_weight.append(b["loss_weight"] + [0.0] * pad_n)

        out = {
            "instanceID": [b["instanceID"] for b in batch],
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
        }
        if has_labels:
            out["labels"] = torch.tensor(labels, dtype=torch.long)
            out["loss_weight"] = torch.tensor(loss_weight, dtype=torch.float)
        return out
