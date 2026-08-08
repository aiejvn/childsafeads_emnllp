"""Multi-task encoder body: one shared transformer encoder, three heads (st1/st2/st3).

`AutoModelForSequenceClassification` only supports a single head, so this wraps a
plain `AutoModel` body with three linear heads (st1: softmax, st2/st3: sigmoid).
Consumers decide how to train it -- `src/lora` LoRA-adapts the encoder's attention
layers via PEFT, `src/last_layer` freezes everything but the last N transformer
blocks -- this module has no dependency on either training strategy.
"""
from typing import Optional

import torch
import torch.nn as nn
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
