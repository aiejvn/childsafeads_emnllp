"""Train a LoRA-adapted causal LM (e.g. Qwen3.5-4B/2B/0.8B) generatively on the
ChildSafeAds task: given the same zero-shot prompt used for the GPT baseline
(SYSTEM_PROMPT + "SEGMENT DATA:\\n\\n{text}", src/baseline_gpt.py), the model is fine-tuned
via next-token cross-entropy to generate the gold st1/st2/st3 label as JSON matching
baseline_gpt.py's `Prediction` schema -- loss is masked to the completion tokens only.

This is the generative counterpart to lora_train.py, which LoRA-adapts encoder (BERT-family)
models via classification heads instead; use that script for roberta-base/legal-bert.

Usage (run from the repo root):
    python src/lora/lora_train_generative.py public_data_dev/train.jsonl public_data_dev/dev.jsonl \\
        --model Qwen/Qwen3.5-4B --epochs 3 --batch-size 4 --output-dir runs/lora_qwen
    python src/lora/lora_train_generative.py public_data_dev/train.jsonl public_data_dev/dev.jsonl \\
        --model Qwen/Qwen3.5-0.8B --sample-size 8 --epochs 1 --batch-size 2 \\
        --output-dir runs/lora_smoke_qwen  # smoke test

Per-epoch dev eval decodes via constrained/structured generation (lm-format-enforcer,
see lora_generative.py) against the same schema, so predictions are always valid JSON.

Saves the best-dev-macro-F1 adapter to <output-dir>/best and the final epoch's to
<output-dir>/last (both loadable with lora_predict_generative.py).
"""
import argparse
import os
import random
import sys
from datetime import datetime

import torch
from torch.utils.data import DataLoader
from tqdm import tqdm
from transformers import AutoTokenizer, get_linear_schedule_with_warmup

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # so `import lora` resolves src/lora as a package
from lora import evaluate, load_split, setup_logging  # noqa: E402
from lora.lora_data import GenerativeCollator, GenerativeDataset  # noqa: E402
from lora.lora_generative import generate_predictions  # noqa: E402
from lora.lora_model import build_peft_model_causal  # noqa: E402


def to_device(batch: dict, device: str) -> dict:
    return {k: (v.to(device) if torch.is_tensor(v) else v) for k, v in batch.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("train", help="training split, e.g. public_data_dev/train.jsonl")
    ap.add_argument("dev", help="dev split for per-epoch evaluation, e.g. public_data_dev/dev.jsonl")
    ap.add_argument("--model", default="Qwen/Qwen3.5-4B")
    ap.add_argument("--context", choices=["transcript", "full"], default="full")
    ap.add_argument("--max-length", type=int, default=4096, help="prompt now includes the full "
                     "SYSTEM_PROMPT + labels taxonomy, not just the segment text, so this is much "
                     "larger than lora_train.py's default")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--grad-accum-steps", type=int, default=4)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--warmup-ratio", type=float, default=0.06)
    ap.add_argument("--lora-r", type=int, default=8)
    ap.add_argument("--lora-alpha", type=int, default=16)
    ap.add_argument("--lora-dropout", type=float, default=0.1)
    ap.add_argument("--target-modules", default="q_proj,v_proj", help="comma-separated module names to LoRA-adapt")
    ap.add_argument("--load-in-4bit", action="store_true", help="QLoRA via bitsandbytes (must be installed separately)")
    ap.add_argument("--max-new-tokens", type=int, default=128, help="generation budget for the JSON completion during dev eval")
    ap.add_argument("--sample-size", type=int, default=None, help="sample N train and N dev instances (seeded smoke test)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--device", default=None, help="defaults to cuda if available, else cpu")
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log = setup_logging("runs", "lora_train_generative", args.model.replace("/", "_"), timestamp)
    log.info(f"config: {vars(args)} device={device}")

    train_instances = list(load_split(args.train))
    dev_instances = list(load_split(args.dev))
    if args.sample_size:
        rng = random.Random(args.seed)
        train_instances = rng.sample(train_instances, min(args.sample_size, len(train_instances)))
        dev_instances = rng.sample(dev_instances, min(args.sample_size, len(dev_instances)))
    log.info(f"train={len(train_instances)} dev={len(dev_instances)}")

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = build_peft_model_causal(
        args.model, lora_r=args.lora_r, lora_alpha=args.lora_alpha, lora_dropout=args.lora_dropout,
        target_modules=args.target_modules.split(","), load_in_4bit=args.load_in_4bit, device=device,
    )
    if not args.load_in_4bit:
        model = model.to(device)
    model.print_trainable_parameters()

    collate = GenerativeCollator(tokenizer)
    train_ds = GenerativeDataset(train_instances, tokenizer, args.context, args.max_length)
    dev_ds = GenerativeDataset(dev_instances, tokenizer, args.context, args.max_length)
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, collate_fn=collate)
    dev_loader = DataLoader(dev_ds, batch_size=args.batch_size, shuffle=False, collate_fn=collate)

    trainable = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(trainable, lr=args.lr)
    steps_per_epoch = -(-len(train_loader) // args.grad_accum_steps)  # ceil div
    total_steps = steps_per_epoch * args.epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=int(args.warmup_ratio * total_steps), num_training_steps=total_steps
    )

    best_f1 = -1.0
    os.makedirs(args.output_dir, exist_ok=True)
    for epoch in range(args.epochs):
        model.train()
        tokenizer.padding_side = "right"  # loss-masked labels must line up token-for-token
        running_loss = 0.0
        for step, batch in enumerate(tqdm(train_loader, desc=f"epoch {epoch + 1}/{args.epochs}")):
            batch = to_device(batch, device)
            out = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"], labels=batch["labels"])
            loss = out.loss / args.grad_accum_steps
            loss.backward()
            running_loss += out.loss.item()
            if (step + 1) % args.grad_accum_steps == 0 or step + 1 == len(train_loader):
                torch.nn.utils.clip_grad_norm_(trainable, 1.0)
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()
        log.info(f"epoch {epoch + 1}: mean train loss = {running_loss / len(train_loader):.4f}")

        tokenizer.padding_side = "left"  # batched model.generate() needs left-padding
        _, preds = generate_predictions(model, dev_loader, tokenizer, device, args.max_new_tokens)
        gold = [inst["labels"] for inst in dev_instances]
        metrics = evaluate(gold, preds)
        log.info(f"epoch {epoch + 1} dev metrics: " + ", ".join(f"{k}={v:.3f}" for k, v in metrics.items()))

        if metrics["mean_macro_f1"] > best_f1:
            best_f1 = metrics["mean_macro_f1"]
            model.save_pretrained(os.path.join(args.output_dir, "best"))
            log.info(f"epoch {epoch + 1}: new best mean_macro_f1={best_f1:.3f}, saved to {args.output_dir}/best")

    model.save_pretrained(os.path.join(args.output_dir, "last"))
    log.info(f"saved final epoch adapter to {args.output_dir}/last (best dev mean_macro_f1={best_f1:.3f})")


if __name__ == "__main__":
    main()
