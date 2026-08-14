"""Three-stage pipeline for the disclosure family (undisclosed_advertising /
inadequate_disclosure) only -- the other six ST3 flags are still baseline_gpt.py's job.

    Stage 1 (cheap, local):   regex/keyword filter for sponsor-adjacent language --
                              logged as a diagnostic against stage 2, not gating.
    Stage 2 (trained model):  a token-classification tagger (src/disclosure_tagger_train.py)
                              marks which words in TRANSCRIPT + DESCRIPTION are part of a
                              disclosure-relevant span, trained on gold st3_evidence quotes.
                              Predicted spans are trimmed to a word window and handed to
                              stage 3 -- this is what "eliminates non-ad stuff" from what
                              the LLM reads.
    Stage 3 (LLM):            a clarity classifier judges the trimmed span (or, if the
                              tagger found nothing -- untrained/no --tagger-dir, or a
                              genuine no-disclosure-anywhere case -- the full text instead)
                              against the child-comprehension standard: no disclosure
                              found anywhere, an inadequate one, or no issue.

Without --tagger-dir, stage 2 is skipped and every instance falls through to stage 3 on
its full TRANSCRIPT + DESCRIPTION text -- the "pure LLM" fallback for when the trained
tagger isn't trusted yet.

Usage (run from the repo root):
    python src/disclosure_pipeline.py public_data_dev/dev.jsonl --tagger-dir runs/disclosure_tagger/best
    python src/disclosure_pipeline.py public_data_dev/dev.jsonl  # no tagger -- pure LLM on full text
    python src/disclosure_pipeline.py public_data_dev/dev.jsonl --tagger-dir ... --sample-size 20  # smoke test

Prints macro-F1 over {undisclosed_advertising, inadequate_disclosure, no_disclosure_issue}
whenever the target split carries gold "labels", plus how often stage 2 fell back to the
full text and how the two verdict sources' accuracy compares.
"""
import argparse
import json
import os
import random
import sys
from datetime import datetime
from typing import Literal

import torch
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from torch.utils.data import DataLoader
from transformers import AutoModelForTokenClassification, AutoTokenizer

sys.path.insert(0, os.path.dirname(__file__))
from baseline_gpt import LABELS_TAXONOMY, macro_f1, setup_logging  # noqa: E402
from disclosure_data import (  # noqa: E402
    Collator, DISCLOSURE_FLAGS, DisclosureSpanDataset, decode_predicted_spans, keyword_hits,
    load_split, source_text, spans_to_words,
)

from dotenv import load_dotenv
load_dotenv()

NO_ISSUE = "no_disclosure_issue"
VERDICT_LABELS = ["undisclosed_advertising", "inadequate_disclosure", NO_ISSUE]

CLARITY_SYSTEM_PROMPT = """You are a compliance analyst judging ONE thing: whether a sponsored \
segment's commercial nature is disclosed clearly enough for a child to understand the content is \
paid for. You are given a trimmed excerpt -- either the specific span another system flagged as \
disclosure-relevant, or, if none was found, the segment's full transcript and video description \
-- plus OFFICIAL_DISCLOSURE, the platform's own paid-promotion label for this video.

Judge using this two-step procedure. Step 1: does the excerpt contain ANY acknowledgment that this \
is a commercial relationship -- sponsorship ("sponsor of this video", "sponsored by", "thanks to X \
for sponsoring"), a paid partnership/ad label, or an affiliate-link disclaimer ("contains affiliate \
links", "using affiliate links supports us", "I'll receive a commission")? If truly none, the verdict \
is undisclosed_advertising -- this holds even if the excerpt is otherwise clearly a product pitch; an \
enthusiastic pitch is not itself a disclosure. Step 2: if you found such an acknowledgment, judge \
whether it is clear and prominent enough for a child to understand this content is paid for (verdict: \
no_disclosure_issue) or buried, brief, generic legal/affiliate boilerplate, or otherwise unclear to a \
child (verdict: inadequate_disclosure) -- weigh several signals together rather than any one \
decisively: OFFICIAL_DISCLOSURE being true is a meaningful positive signal (not proof by itself) and \
false leans toward inadequate; an explicit plain-language sponsor/ad statement made early, before or \
alongside the pitch, leans toward adequate; a disclosure mentioned only once, only briefly, only after \
the persuasive pitch is already over, or that is a bare promo code/link with no explicit "sponsor"/"ad" \
language, or an affiliate-link legal disclaimer with no plain-language sponsor statement, leans toward \
inadequate.

If you were given the excerpt because a span-finder flagged it, trust that it captured the \
disclosure-relevant text if one exists -- but if the excerpt reads as pure product pitch with nothing \
resembling an acknowledgment, that is itself evidence for undisclosed_advertising, not a sign to guess. \
If you were given the full segment (no span was found), search all of it before concluding \
undisclosed_advertising.

Respond with the structured verdict only.

""" + LABELS_TAXONOMY


class ClarityVerdict(BaseModel):
    verdict: Literal[tuple(VERDICT_LABELS)] = Field(
        description="undisclosed_advertising, inadequate_disclosure, or no_disclosure_issue"
    )


def to_device(batch: dict, device: str) -> dict:
    return {k: (v.to(device) if torch.is_tensor(v) else v) for k, v in batch.items()}


def derive_gold(instance: dict) -> str:
    st3 = set(instance["labels"]["st3"])
    hit = st3 & DISCLOSURE_FLAGS
    return next(iter(hit)) if hit else NO_ISSUE


@torch.no_grad()
def run_tagger(instances: list, tokenizer, model, device: str, batch_size: int, max_length: int,
                context_words: int) -> dict:
    """Returns {instanceID: [trimmed context string, ...]} for instances where the tagger
    found at least one span; instances with none are simply absent from the result, so
    the caller's fallback (full text) applies by omission."""
    model.eval()
    loader = DataLoader(
        DisclosureSpanDataset(instances, tokenizer, max_length), batch_size=batch_size,
        shuffle=False, collate_fn=Collator(tokenizer),
    )
    by_id = {inst["instanceID"]: inst for inst in instances}
    trimmed = {}
    for batch in loader:
        gpu_batch = to_device({k: v for k, v in batch.items() if k != "instanceID"}, device)
        logits = model(**gpu_batch).logits
        pred_ids = logits.argmax(dim=-1).cpu()
        # offset_mapping isn't in the collated batch (Collator drops it) -- recompute
        # per-instance from the tokenizer directly, same call the dataset made.
        for i, iid in enumerate(batch["instanceID"]):
            inst = by_id[iid]
            text = source_text(inst)
            enc = tokenizer(text, truncation=True, max_length=max_length, return_offsets_mapping=True)
            n = len(enc["input_ids"])
            char_spans = decode_predicted_spans(text, enc["offset_mapping"], pred_ids[i][:n].tolist())
            if char_spans:
                trimmed[iid] = spans_to_words(text, char_spans, context_words)
    return trimmed


def build_clarity_messages(instance: dict, excerpt: str) -> list:
    disclosure = instance["video_context"]["official_disclosure"]
    human = f"OFFICIAL_DISCLOSURE: {disclosure}\n\nEXCERPT:\n\n{excerpt}"
    return [SystemMessage(CLARITY_SYSTEM_PROMPT), HumanMessage(human)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="split file to predict on, e.g. dev.jsonl")
    ap.add_argument("--tagger-dir", default=None,
                     help="stage-2 tagger checkpoint (see disclosure_tagger_train.py); omit to skip "
                          "stage 2 and run every instance through stage 3 on its full text")
    ap.add_argument("--model", default="gpt-5.4", help="stage-3 clarity classifier")
    ap.add_argument("--context-words", type=int, default=12,
                     help="words of context padded around each tagger-predicted span")
    ap.add_argument("--max-length", type=int, default=512, help="tagger max token length")
    ap.add_argument("--tagger-batch-size", type=int, default=16)
    ap.add_argument("--sample-size", type=int, default=None)
    ap.add_argument("--max-concurrency", type=int, default=8)
    ap.add_argument("--device", default=None)
    args = ap.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log = setup_logging("runs", "disclosure_pipeline", args.model, timestamp)
    out = os.path.join("runs", f"disclosure_pipeline_{timestamp}.jsonl")
    log.info(f"config: target={args.target} tagger_dir={args.tagger_dir} model={args.model} "
             f"context_words={args.context_words} sample_size={args.sample_size} out={out}")

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("Set OPENAI_API_KEY in the environment (or a .env file) first.")

    instances = list(load_split(args.target))
    if args.sample_size:
        instances = random.Random(42).sample(instances, min(args.sample_size, len(instances)))

    # Stage 1: diagnostic only -- logged, not gating stage 2/3.
    n_keyword_hit = sum(1 for inst in instances if keyword_hits(source_text(inst)))
    log.info(f"stage 1 (keyword filter): {n_keyword_hit}/{len(instances)} instances have a sponsor-adjacent term")

    # Stage 2.
    tagger_spans = {}
    if args.tagger_dir:
        device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
        log.info(f"stage 2: loading tagger from {args.tagger_dir} on {device}")
        tokenizer = AutoTokenizer.from_pretrained(args.tagger_dir)
        model = AutoModelForTokenClassification.from_pretrained(args.tagger_dir).to(device)
        tagger_spans = run_tagger(
            instances, tokenizer, model, device, args.tagger_batch_size, args.max_length, args.context_words,
        )
        log.info(f"stage 2: found >=1 span for {len(tagger_spans)}/{len(instances)} instances "
                 f"({len(instances) - len(tagger_spans)} fall back to full text)")
    else:
        log.info("stage 2: skipped (no --tagger-dir) -- every instance falls back to full text")

    # Stage 3.
    excerpts, used_fallback = [], []
    for inst in instances:
        spans = tagger_spans.get(inst["instanceID"])
        if spans:
            excerpts.append("\n[...]\n".join(spans))
            used_fallback.append(False)
        else:
            excerpts.append(source_text(inst))
            used_fallback.append(True)

    llm = ChatOpenAI(model=args.model, temperature=0).with_structured_output(
        ClarityVerdict, method="json_schema", strict=True
    )
    batch_inputs = [build_clarity_messages(inst, excerpt) for inst, excerpt in zip(instances, excerpts)]
    results = llm.batch(batch_inputs, config={"max_concurrency": args.max_concurrency}, return_exceptions=True)

    predictions, gold = [], []
    with open(out, "w", encoding="utf-8") as f:
        for inst, result, excerpt, fell_back in zip(instances, results, excerpts, used_fallback):
            if isinstance(result, Exception):
                log.warning(f"{inst['instanceID']} failed ({result})")
                verdict = NO_ISSUE
            else:
                verdict = result.verdict
            predictions.append(verdict)
            f.write(json.dumps({
                "instanceID": inst["instanceID"], "verdict": verdict,
                "used_fallback": fell_back, "excerpt_chars": len(excerpt),
            }) + "\n")
            if inst.get("labels"):
                gold.append(derive_gold(inst))
    log.info(f"wrote {len(predictions)} predictions to {out}")

    # Only evaluate when every instance carries gold labels -- gold is collected
    # conditionally above, so a partial mix would misalign it against `predictions`.
    if gold and len(gold) == len(predictions):
        f1, per_label = macro_f1([[g] for g in gold], [[p] for p in predictions], VERDICT_LABELS)
        log.info(f"disclosure macro-F1: {f1:.3f}")
        log.info("per-verdict F1: " + ", ".join(f"{l}={v:.3f}" for l, v in sorted(per_label.items())))

        for used_fb in (False, True):
            idx = [i for i, fb in enumerate(used_fallback) if fb == used_fb]
            if not idx:
                continue
            correct = sum(1 for i in idx if gold[i] == predictions[i])
            log.info(f"  {'fallback (full text)' if used_fb else 'stage-2 span'} instances: "
                     f"{correct}/{len(idx)} correct ({correct / len(idx):.3f})")
    else:
        log.info("target has no gold labels (or a partial mismatch) -- skipping evaluation")


if __name__ == "__main__":
    main()
