"""Shared pieces for the disclosure-family (undisclosed_advertising / inadequate_disclosure)
pipeline: src/disclosure_tagger_train.py trains a span tagger on this module's data, and
src/disclosure_pipeline.py runs it at inference time.

Evidence for these two flags -- gold `st3_evidence` quotes -- lives in either
`transcript.text` or `video_context.description` (roughly evenly split; never on the
product page for this flag pair), so `source_text()` is the concatenation of exactly
those two fields, and every char offset in this file is relative to that string.

Transcripts here are ASR output and often carry no punctuation at all (see e.g. train
instance 3: "...today's sponsor Dragon City they've added..." -- no period in sight), so
this module never assumes sentence boundaries exist; spans are word-window trims, not
sentence-snapped ones.
"""
import json
import os
import re
import sys

import torch
from torch.utils.data import Dataset

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "starting_kit"))
from load_data import load_split  # noqa: E402,F401 (re-exported for the train/pipeline scripts)

DISCLOSURE_FLAGS = {"undisclosed_advertising", "inadequate_disclosure"}

# Stage 1: cheap keyword/regex filter for sponsor-adjacent language. Not a classifier --
# a fast, dependency-free way to flag candidate instances and to log a sanity check
# against what the trained tagger (stage 2) finds.
SPONSOR_TERMS = [
    r"\bsponsors?(?:hip|ed|ing)?\b",
    r"\bpartner(?:ed|ship)?\b",
    r"\bbrought to you by\b",
    r"\baffiliate\b",
    r"\bcommission\b",
    r"\bpromo\s?code\b",
    r"\bdiscount code\b",
    r"#ad\b",
    r"\bpaid partnership\b",
    r"\bin collaboration with\b",
    r"\bteaming up with\b",
    r"\bthanks to\b",
]
SPONSOR_TERM_RE = re.compile("|".join(SPONSOR_TERMS), re.IGNORECASE)

LABEL_LIST = ["O", "B-DISC", "I-DISC"]
LABEL2ID = {label: i for i, label in enumerate(LABEL_LIST)}


def keyword_hits(text: str) -> list:
    """Character spans (start, end, matched text) of sponsor-adjacent terms -- stage 1."""
    return [(m.start(), m.end(), m.group(0)) for m in SPONSOR_TERM_RE.finditer(text)]


def source_text(instance: dict) -> str:
    """Where disclosure language can appear: transcript then video description, joined
    so every char offset below is relative to this exact string."""
    t = instance["transcript"]["text"]
    d = instance["video_context"]["description"]
    return f"{t}\n\n{d}"


def evidence_spans(instance: dict, text: str) -> list:
    """Char spans in `text` (must be `source_text(instance)`) covered by this instance's
    gold st3_evidence quotes for the disclosure flags, found by exact substring search.
    Returns [] both for clean instances (no disclosure flag -- correctly "O" everywhere)
    and for the ~20% of flagged instances whose quote doesn't appear verbatim; callers
    that build training data must tell these two apart with `has_disclosure_flag`,
    since only the first is valid negative supervision."""
    spans = []
    for ev in instance.get("labels", {}).get("st3_evidence", []):
        if ev.get("flag") not in DISCLOSURE_FLAGS:
            continue
        quote = ev.get("quote", "")
        if not quote:
            continue
        start = text.find(quote)
        if start != -1:
            spans.append((start, start + len(quote)))
    return spans


def has_disclosure_flag(instance: dict) -> bool:
    return bool(set(instance.get("labels", {}).get("st3", [])) & DISCLOSURE_FLAGS)


def taggable_instances(instances: list) -> list:
    """Filters to instances that are valid tagger supervision: clean instances (no
    disclosure flag -- legitimately "O" everywhere) and flagged instances whose evidence
    quote was actually found (a real positive span). Drops flagged instances with no
    locatable span (~20%, see module docstring) -- keeping them would teach the tagger
    "no span here" on segments that do contain a violation, which is worse than dropping
    the example."""
    keep = []
    for inst in instances:
        if not inst.get("labels"):
            continue
        if has_disclosure_flag(inst):
            spans = evidence_spans(inst, source_text(inst))
            if spans:
                keep.append(inst)
        else:
            keep.append(inst)
    return keep


def tag_tokens(offsets: list, spans: list) -> list:
    """Offset-mapping entries -> BIO label ids, tagging every token that overlaps a span."""
    labels = [LABEL2ID["O"]] * len(offsets)
    for start, end in spans:
        first = True
        for i, (tok_start, tok_end) in enumerate(offsets):
            if tok_start == tok_end:  # special token (offset (0, 0)); never tagged
                continue
            if tok_start < end and tok_end > start:  # token overlaps [start, end)
                labels[i] = LABEL2ID["B-DISC"] if first else LABEL2ID["I-DISC"]
                first = False
    return labels


class DisclosureSpanDataset(Dataset):
    """One example per instance: `source_text(instance)` tokenized, with BIO labels
    where gold evidence spans fall (None for predict-only instances with no `labels`)."""

    def __init__(self, instances: list, tokenizer, max_length: int = 512):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.instances = instances

    def __len__(self):
        return len(self.instances)

    def __getitem__(self, idx):
        inst = self.instances[idx]
        text = source_text(inst)
        enc = self.tokenizer(text, truncation=True, max_length=self.max_length, return_offsets_mapping=True)
        item = {
            "input_ids": enc["input_ids"],
            "attention_mask": enc["attention_mask"],
            "instanceID": inst["instanceID"],
        }
        if inst.get("labels"):
            spans = evidence_spans(inst, text)  # [] for clean instances -- correct all-"O"
            item["labels"] = tag_tokens(enc["offset_mapping"], spans)
        return item


class Collator:
    """Right-pads input_ids/attention_mask/labels to the batch's longest example.
    `labels` is omitted from the batch dict for predict-only data (no instance in the
    batch carries gold labels), same convention as lora/lora_data.py's Collator."""

    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def __call__(self, batch: list) -> dict:
        max_len = max(len(b["input_ids"]) for b in batch)
        pad_id = self.tokenizer.pad_token_id
        input_ids, attention_mask = [], []
        for b in batch:
            pad = max_len - len(b["input_ids"])
            input_ids.append(b["input_ids"] + [pad_id] * pad)
            attention_mask.append(b["attention_mask"] + [0] * pad)
        out = {
            "input_ids": torch.tensor(input_ids),
            "attention_mask": torch.tensor(attention_mask),
            "instanceID": [b["instanceID"] for b in batch],
        }
        if "labels" in batch[0]:
            labels = []
            for b in batch:
                pad = max_len - len(b["labels"])
                labels.append(b["labels"] + [-100] * pad)
            out["labels"] = torch.tensor(labels)
        return out


def spans_to_words(text: str, token_spans: list, context_words: int = 12) -> list:
    """Merges predicted char spans that are close together (within `context_words` words
    of each other) and pads each with `context_words` words of surrounding context on
    both sides -- the "trimmed sentence" stage 3 reads, snapped to word boundaries since
    ASR transcripts here can't be trusted to have sentence punctuation (see module
    docstring). Returns the trimmed strings, longest-context first is not guaranteed;
    order follows `token_spans`."""
    if not token_spans:
        return []
    # Word boundaries: every whitespace-delimited token's (start, end) in `text`.
    words = [(m.start(), m.end()) for m in re.finditer(r"\S+", text)]

    def word_index_at(char_idx: int, default: int) -> int:
        for i, (ws, we) in enumerate(words):
            if ws <= char_idx < we:
                return i
        return default

    merged = []
    for start, end in sorted(token_spans):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    trimmed = []
    for start, end in merged:
        start_word = word_index_at(start, 0)
        end_word = word_index_at(max(end - 1, start), len(words) - 1)
        lo = max(0, start_word - context_words)
        hi = min(len(words) - 1, end_word + context_words)
        if not words:
            continue
        trimmed.append(text[words[lo][0]:words[hi][1]])
    return trimmed


def decode_predicted_spans(text: str, offsets: list, label_ids: list) -> list:
    """Token offset_mapping + predicted BIO label ids -> merged char spans (start, end)
    in `text`. A B-DISC starts a new span; a following I-DISC extends it; anything else
    (including an I-DISC with no preceding B/I, which shouldn't happen but a model can
    still emit) starts a new span defensively rather than raising."""
    spans = []
    current = None
    for (tok_start, tok_end), label_id in zip(offsets, label_ids):
        if tok_start == tok_end:
            continue
        label = LABEL_LIST[label_id]
        if label == "B-DISC":
            if current:
                spans.append(current)
            current = [tok_start, tok_end]
        elif label == "I-DISC" and current is not None:
            current[1] = tok_end
        else:
            if current:
                spans.append(current)
            current = None
    if current:
        spans.append(current)
    return [(s, e) for s, e in spans]
