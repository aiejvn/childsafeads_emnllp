"""LoRA-specific wiring around the shared `MultiTaskEncoder` (now in
common/multitask_encoder.py): LoRA-adapts the encoder's attention layers while
training the st1/st2/st3 heads fully via PEFT's `modules_to_save`.
"""
import os
import sys
from typing import Optional

import torch
from peft import LoraConfig, PeftModel, TaskType, get_peft_model
from transformers import AutoModelForCausalLM

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common.multitask_encoder import MultiTaskEncoder  # noqa: E402


def build_peft_model(
    base_model_name: str,
    num_st1: int,
    num_st2: int,
    num_st3: int,
    lora_r: int = 8,
    lora_alpha: int = 16,
    lora_dropout: float = 0.1,
    target_modules: Optional[list] = None,
) -> PeftModel:
    """Build a fresh MultiTaskEncoder and wrap it with LoRA adapters (encoder attention
    Q/V projections) plus fully-trainable st1/st2/st3 heads."""
    model = MultiTaskEncoder(base_model_name, num_st1, num_st2, num_st3)
    lora_config = LoraConfig(
        task_type=TaskType.FEATURE_EXTRACTION,
        target_modules=target_modules or ["query", "value"],
        modules_to_save=["st1_head", "st2_head", "st3_head"],
        r=lora_r,
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout,
    )
    return get_peft_model(model, lora_config)


def load_peft_model(base_model_name: str, num_st1: int, num_st2: int, num_st3: int, adapter_dir: str) -> PeftModel:
    """Rebuild the base MultiTaskEncoder and attach trained LoRA weights + heads from adapter_dir."""
    model = MultiTaskEncoder(base_model_name, num_st1, num_st2, num_st3)
    return PeftModel.from_pretrained(model, adapter_dir)


PARALLELISM_CHOICES = ("none", "pipeline", "tensor")


def _require_multi_gpu(parallelism: str) -> None:
    """--parallelism pipeline/tensor only make sense across >=2 GPUs -- fail fast with a clear
    message rather than let device_map="auto" silently no-op (pipeline) or let tensor mode
    crash deep inside torch.distributed's env-var lookup on a single-GPU box."""
    if parallelism == "none":
        return
    n = torch.cuda.device_count()
    if n < 2:
        raise RuntimeError(
            f"--parallelism {parallelism} requires at least 2 GPUs (torch.cuda.device_count()={n}). "
            "Pass --parallelism none to run on a single GPU."
        )
    if parallelism == "tensor" and int(os.environ.get("WORLD_SIZE", "1")) < 2:
        raise RuntimeError(
            "--parallelism tensor requires launching under torchrun, e.g.:\n"
            f"  torchrun --nproc-per-node={n} <script>.py ... --parallelism tensor\n"
            "plain `python ...` only starts one process, so there's no process group to shard across."
        )


def _load_causal_base(
    base_model_name: str, load_in_4bit: bool, device: str, local_files_only: bool = False,
    parallelism: str = "none",
):
    """Shared AutoModelForCausalLM loading for build/load_peft_model_causal. 4-bit (QLoRA)
    is opt-in and requires `bitsandbytes`, which is not installed by default -- raises with
    a clear message rather than importing it eagerly.

    `parallelism` (see PARALLELISM_CHOICES): "none" keeps the old single-`device` behavior
    (quantized weights via device_map at load time, since bnb layers can't be moved with a
    later plain `.to(device)`); "pipeline" (device_map="auto") splits the model's layers
    across GPUs; "tensor" (tp_plan="auto", needs torchrun -- see _require_multi_gpu) splits
    individual weight matrices across GPUs. For Qwen3.5 specifically, its registered
    `_tp_plan` only covers `lm_head`, so "tensor" here really means "shard just the huge
    vocab-sized logits tensor, replicate the 32 backbone layers per rank" -- not a full split.
    Either "pipeline" or "tensor" places the model already; callers should not additionally
    call `.to(device)` in those cases."""
    _require_multi_gpu(parallelism)
    quantization_config = None
    if load_in_4bit:
        try:
            from transformers import BitsAndBytesConfig
        except ImportError as e:
            raise ImportError(
                "--load-in-4bit requires the `bitsandbytes` package, which is not installed. "
                "Install it (`pip install bitsandbytes`) or drop --load-in-4bit."
            ) from e
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.bfloat16,
        )
    load_kwargs = dict(
        torch_dtype=torch.bfloat16, quantization_config=quantization_config, local_files_only=local_files_only,
    )
    if parallelism == "tensor":
        load_kwargs["tp_plan"] = "auto"
    elif parallelism == "pipeline":
        load_kwargs["device_map"] = "balanced_low_0" # auto, balanced, balanced_low_0, or sequential
    elif load_in_4bit:
        load_kwargs["device_map"] = {"": device}
    return AutoModelForCausalLM.from_pretrained(base_model_name, **load_kwargs)


def build_peft_model_causal(
    base_model_name: str,
    lora_r: int = 8,
    lora_alpha: int = 16,
    lora_dropout: float = 0.1,
    target_modules: Optional[list] = None,
    load_in_4bit: bool = False,
    device: str = "cuda",
    local_files_only: bool = False,
    parallelism: str = "none",
) -> PeftModel:
    """Build a fresh causal LM (e.g. Qwen) and LoRA-adapt its attention projections, for the
    generative training path (see lora_train_generative.py): the model is fine-tuned via
    plain next-token cross-entropy to generate the gold st1/st2/st3 label as JSON, so unlike
    build_peft_model there are no extra classification heads / modules_to_save. `device` is
    only used to place quantized weights when load_in_4bit=True and parallelism="none" (see
    _load_causal_base) -- otherwise the caller is expected to `.to(device)` the returned model
    themselves, or not to (see `parallelism`, PARALLELISM_CHOICES).

    Gradient checkpointing is always on: with LoRA, the frozen base layers still need their
    forward activations cached to backprop into the adapters, so peak memory scales with
    num_layers * batch_size * seq_len same as full fine-tuning unless checkpointing recomputes
    them instead of retaining them. `use_cache=False` goes with it -- Qwen3.5 has no
    auto-disable guard for this like some other model classes, and also slows down
    lora_generative.py's model.generate() calls; deferred for now."""
    model = _load_causal_base(
        base_model_name, load_in_4bit, device, local_files_only=local_files_only, parallelism=parallelism,
    )
    model.config.use_cache = False
    if load_in_4bit:
        from peft import prepare_model_for_kbit_training
        # checkpointing enabled below, uniformly for both branches -- this only does the
        # quantization-specific prep (freezing base params, upcasting norms to fp32)
        model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=False)
    model.gradient_checkpointing_enable()
    model.enable_input_require_grads()
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        target_modules=target_modules or ["q_proj", "v_proj"],
        r=lora_r,
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout,
    )
    return get_peft_model(model, lora_config)


def load_peft_model_causal(
    base_model_name: str, adapter_dir: str, load_in_4bit: bool = False, device: str = "cuda",
    local_files_only: bool = False, parallelism: str = "none",
) -> PeftModel:
    """Rebuild the base causal LM and attach trained LoRA weights from adapter_dir."""
    model = _load_causal_base(
        base_model_name, load_in_4bit, device, local_files_only=local_files_only, parallelism=parallelism,
    )
    return PeftModel.from_pretrained(model, adapter_dir)
