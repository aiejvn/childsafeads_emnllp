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
