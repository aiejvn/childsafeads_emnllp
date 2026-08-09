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


def _load_causal_base(base_model_name: str, load_in_4bit: bool, device: str, local_files_only: bool = False):
    """Shared AutoModelForCausalLM loading for build/load_peft_model_causal. 4-bit (QLoRA)
    is opt-in and requires `bitsandbytes`, which is not installed by default -- raises with
    a clear message rather than importing it eagerly. Quantized weights are placed directly
    via device_map at load time (bnb layers can't be moved with a later plain `.to(device)`);
    callers should only call `.to(device)` themselves when load_in_4bit is False."""
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
    return AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.bfloat16,
        quantization_config=quantization_config,
        device_map={"": device} if load_in_4bit else None,
        local_files_only=local_files_only,
    )


def build_peft_model_causal(
    base_model_name: str,
    lora_r: int = 8,
    lora_alpha: int = 16,
    lora_dropout: float = 0.1,
    target_modules: Optional[list] = None,
    load_in_4bit: bool = False,
    device: str = "cuda",
    local_files_only: bool = False,
) -> PeftModel:
    """Build a fresh causal LM (e.g. Qwen) and LoRA-adapt its attention projections, for the
    generative training path (see lora_train_generative.py): the model is fine-tuned via
    plain next-token cross-entropy to generate the gold st1/st2/st3 label as JSON, so unlike
    build_peft_model there are no extra classification heads / modules_to_save. `device` is
    only used to place quantized weights when load_in_4bit=True (see _load_causal_base) --
    otherwise the caller is expected to `.to(device)` the returned model themselves."""
    model = _load_causal_base(base_model_name, load_in_4bit, device, local_files_only=local_files_only)
    if load_in_4bit:
        from peft import prepare_model_for_kbit_training
        model = prepare_model_for_kbit_training(model)
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
    local_files_only: bool = False,
) -> PeftModel:
    """Rebuild the base causal LM and attach trained LoRA weights from adapter_dir."""
    model = _load_causal_base(base_model_name, load_in_4bit, device, local_files_only=local_files_only)
    return PeftModel.from_pretrained(model, adapter_dir)
