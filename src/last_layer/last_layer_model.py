"""Last-layer-only wiring around the shared `MultiTaskEncoder`
(common/multitask_encoder.py): freezes the entire encoder except its last
`num_unfrozen_layers` transformer blocks, and fully trains the st1/st2/st3 heads --
no PEFT/LoRA involved. Checkpoints save only the trainable parameters (last-N-layers +
heads), not the full model, since the frozen majority of weights are always just the
pretrained base and don't need to round-trip through disk.
"""
import json
import logging
import os
import sys

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common.multitask_encoder import MultiTaskEncoder  # noqa: E402

log = logging.getLogger(__name__)


def build_frozen_model(
    base_model_name: str, num_st1: int, num_st2: int, num_st3: int, num_unfrozen_layers: int = 1,
) -> MultiTaskEncoder:
    """Fresh MultiTaskEncoder with the whole encoder body frozen, then its LAST
    `num_unfrozen_layers` transformer blocks unfrozen again, plus fully-trainable
    st1/st2/st3 heads. E.g. for a 12-block encoder with num_unfrozen_layers=1, blocks
    0-10 stay frozen and only block 11 (the final one, closest to the heads) trains."""
    model = MultiTaskEncoder(base_model_name, num_st1, num_st2, num_st3)

    # Step 1: freeze the whole encoder body (all blocks + embeddings + pooler, if any).
    for p in model.encoder.parameters():
        p.requires_grad = False

    # Step 2: re-unfreeze only the trailing `num_unfrozen_layers` transformer blocks.
    layers = model.encoder.encoder.layer  # nn.ModuleList; same attribute path for RobertaModel and BertModel
    if num_unfrozen_layers > len(layers):
        log.warning(
            f"num_unfrozen_layers={num_unfrozen_layers} exceeds model depth ({len(layers)} layers); "
            f"unfreezing all {len(layers)} instead"
        )
    trailing_layers = layers[-num_unfrozen_layers:] if num_unfrozen_layers > 0 else []
    for layer in trailing_layers:
        for p in layer.parameters():
            p.requires_grad = True

    # Step 3: heads are always fully trainable (already True on a fresh nn.Linear; explicit for clarity).
    for head in (model.st1_head, model.st2_head, model.st3_head):
        for p in head.parameters():
            p.requires_grad = True

    return model


def count_trainable_parameters(model: MultiTaskEncoder) -> tuple:
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    return trainable, total


def save_frozen_model(
    model: MultiTaskEncoder, output_dir: str,
    base_model_name: str, num_st1: int, num_st2: int, num_st3: int, num_unfrozen_layers: int,
) -> None:
    """Saves only the trainable subset of the state dict (last-N-layers + heads) plus a
    config.json recording how to rebuild the architecture -- mirrors what a PEFT adapter
    directory does for the LoRA suite, but as plain torch tensors."""
    os.makedirs(output_dir, exist_ok=True)
    trainable_state = {name: p.detach().cpu() for name, p in model.named_parameters() if p.requires_grad}
    torch.save(trainable_state, os.path.join(output_dir, "model.pt"))
    config = {
        "base_model_name": base_model_name,
        "num_st1": num_st1,
        "num_st2": num_st2,
        "num_st3": num_st3,
        "num_unfrozen_layers": num_unfrozen_layers,
    }
    with open(os.path.join(output_dir, "config.json"), "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def load_frozen_model(checkpoint_dir: str) -> tuple:
    """Rebuilds MultiTaskEncoder's architecture from config.json (loading fresh pretrained
    weights for the frozen majority of the encoder) then overlays the trained last-N-layers
    + heads from model.pt. Returns (model, config) so callers can sanity-check
    config['base_model_name'] against a --model flag."""
    with open(os.path.join(checkpoint_dir, "config.json"), encoding="utf-8") as f:
        config = json.load(f)
    model = build_frozen_model(
        config["base_model_name"], config["num_st1"], config["num_st2"], config["num_st3"],
        config.get("num_unfrozen_layers", 1),
    )
    trainable_state = torch.load(os.path.join(checkpoint_dir, "model.pt"), map_location="cpu")
    model.load_state_dict(trainable_state, strict=False)
    return model, config
