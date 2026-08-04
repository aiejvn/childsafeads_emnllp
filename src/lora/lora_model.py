"""Multi-task LoRA classifier: one shared encoder, three heads (st1/st2/st3).

`AutoModelForSequenceClassification` only supports a single head, so this wraps a
plain `AutoModel` body with three linear heads (st1: softmax, st2/st3: sigmoid) and
LoRA-adapts the encoder's attention layers while training the heads fully via PEFT's
`modules_to_save`.
"""
from typing import Optional

import torch
import torch.nn as nn
from peft import LoraConfig, PeftModel, TaskType, get_peft_model
from torch.nn import BCEWithLogitsLoss, CrossEntropyLoss
from transformers import AutoModel


class MultiTaskEncoder(nn.Module):
    def __init__(self, base_model_name: str, num_st1: int, num_st2: int, num_st3: int):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(base_model_name)
        hidden = self.encoder.config.hidden_size
        self.st1_head = nn.Linear(hidden, num_st1)
        self.st2_head = nn.Linear(hidden, num_st2)
        self.st3_head = nn.Linear(hidden, num_st3)

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        st1_labels: Optional[torch.Tensor] = None,
        st2_labels: Optional[torch.Tensor] = None,
        st3_labels: Optional[torch.Tensor] = None,
        st2_loss_weight: float = 1.0,
        st3_loss_weight: float = 1.0,
        st2_pos_weight: Optional[torch.Tensor] = None,
        st3_pos_weight: Optional[torch.Tensor] = None,
        **kwargs,  # PeftModelForFeatureExtraction.forward always passes inputs_embeds/output_attentions/etc.
    ) -> dict:
        pooled = self.encoder(input_ids=input_ids, attention_mask=attention_mask).last_hidden_state[:, 0]
        st1_logits = self.st1_head(pooled)
        st2_logits = self.st2_head(pooled)
        st3_logits = self.st3_head(pooled)

        loss = None
        if st1_labels is not None:
            loss = (
                CrossEntropyLoss()(st1_logits, st1_labels)
                + st2_loss_weight * BCEWithLogitsLoss(pos_weight=st2_pos_weight)(st2_logits, st2_labels)
                + st3_loss_weight * BCEWithLogitsLoss(pos_weight=st3_pos_weight)(st3_logits, st3_labels)
            )

        return {"loss": loss, "st1_logits": st1_logits, "st2_logits": st2_logits, "st3_logits": st3_logits}


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
