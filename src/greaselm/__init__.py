"""Barrel: re-exports the shared labels/data-loading pieces from `common/` (same
convention as `src/lora`/`src/last_layer`) plus this package's own core building
blocks -- `KnowledgeGraph` (graph_schema.py) and `GATConvE` (modeling/modeling_gnn.py,
ported from GreaseLM/modeling/modeling_gnn.py) -- so `greaselm_smoke.py` and any future
consumer import one thing instead of reaching into submodules directly.

Scripts under `src/greaselm/` are run from the repo root, e.g.
`python src/greaselm/greaselm_smoke.py --kg-source legal --sample-size 8`.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common import (  # noqa: E402
    ST1_LABELS, ST2_LABELS, ST3_LABELS,
    evaluate, full_context, load_split, setup_logging,
)

from .graph_schema import KGEdge, KGNode, KnowledgeGraph  # noqa: E402
from .modeling.modeling_gnn import GATConvE  # noqa: E402
from .greaselm_model import GreaseLMForClassification  # noqa: E402

__all__ = [
    "ST1_LABELS", "ST2_LABELS", "ST3_LABELS",
    "evaluate", "full_context", "load_split", "setup_logging",
    "KGEdge", "KGNode", "KnowledgeGraph",
    "GATConvE",
    "GreaseLMForClassification",
]
