"""Training-loop helpers shared by src/lora/lora_train.py and
src/last_layer/last_layer_train.py: moving a batch to device, and inverse-frequency
BCE pos_weight. Per-epoch dev decoding uses common/predict_utils.py's
`tune_and_decode` (per-label-tuned thresholds), not a flat threshold here.
"""
import torch


def to_device(batch: dict, device: str) -> dict:
    return {k: (v.to(device) if torch.is_tensor(v) else v) for k, v in batch.items()}


def compute_pos_weight(instances: list, labels_key: str, label_list: list) -> torch.Tensor:
    """
        Inverse-frequency BCE pos_weight per label, from training-set label counts.
        Classes that appear less frequently receive more weight during loss calculation.
    """
    pos = torch.zeros(len(label_list))
    for inst in instances:
        for flag in inst["labels"][labels_key]:
            if flag in label_list:
                pos[label_list.index(flag)] += 1
    total = len(instances)
    neg = total - pos
    return (neg / pos.clamp(min=1)).clamp(max=50.0)


def compute_class_weight(instances: list, labels_key: str, label_list: list) -> torch.Tensor:
    """Inverse-frequency class weight per label for a single-label (multi-class,
    mutually exclusive) field -- the categorical-CE analogue of compute_pos_weight,
    which assumes each label is an independent binary flag (right for st2/st3's
    multi-label sets, wrong for a field like st1 where every instance has exactly
    one value). weight[c] = total / count[c], clamped the same way as
    compute_pos_weight so a near-empty class doesn't get an extreme weight."""
    counts = torch.zeros(len(label_list))
    for inst in instances:
        value = inst["labels"][labels_key]
        if value in label_list:
            counts[label_list.index(value)] += 1
    total = len(instances)
    return (total / counts.clamp(min=1)).clamp(max=50.0)
