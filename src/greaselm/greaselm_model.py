"""Top-level orchestrator, playing the role the paper's outer `GreaseLM` class played
(batches multiple-choice candidates, offsets edge_index like `GreaseLM.batch_graph`),
generalized to our three independent subtasks: st1 is softmax+CE over 5
mutually-exclusive candidates, st2/st3 are independent sigmoid+BCE per candidate (12
and 8 respectively). Standalone: does not import common/multitask_encoder.py,
last_layer_model.py, or lora_model.py (harness integration is out of scope for this
pass, see the plan).

Missing-candidate-node handling: only the combined KG mints st1_label:*/st2_label:*
nodes and links Disclosure/Product Risk to st3_flag:*; the legal KG only has
st3_flag:*; the flow KG has no label nodes at all. Rather than special-case kg_mode,
__init__ mints any of ST1_LABELS/ST2_LABELS/ST3_LABELS missing from the loaded graph as
an isolated node (own concept-embedding row, GATConvE's automatic self-loop, no other
edges) on a private deep copy -- see scratchpad.md for the reasoning. This keeps all
three kg_modes the same code path and turns "legal-only"/"flow-only" into a real
ablation arm instead of a crash.
"""
import copy
import os

import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoTokenizer

from . import ST1_LABELS, ST2_LABELS, ST3_LABELS
from .graph_schema import KnowledgeGraph
from .kg_embeddings import train_transe
from .modeling.modeling_greaselm import LMGNN

KG_DIR = os.path.join(os.path.dirname(__file__), "kg")
KG_PATHS = {
    "legal": os.path.join(KG_DIR, "legal_taxonomy_graph.json"),
    "flow": os.path.join(KG_DIR, "flow_graph.json"),
    "combined": os.path.join(KG_DIR, "combined_graph.json"),
}

SUBTASK_LABELS = {"st1": ST1_LABELS, "st2": ST2_LABELS, "st3": ST3_LABELS}
SUBTASK_NODE_TYPE = {"st1": "st1_label", "st2": "st2_label", "st3": "st3_flag"}


def _mint_missing_candidate_nodes(graph: KnowledgeGraph) -> KnowledgeGraph:
    graph = copy.deepcopy(graph)
    for subtask, labels in SUBTASK_LABELS.items():
        node_type = SUBTASK_NODE_TYPE[subtask]
        existing = {n.label for n in graph.nodes if n.type == node_type}
        for label in labels:
            if label not in existing:
                graph.add_node(f"{node_type}:{label}", node_type, label)
    return graph


class GreaseLMForClassification(nn.Module):
    def __init__(
        self, kg_mode: str, base_model_name: str = "FacebookAI/roberta-base",
        k: int = 3, concept_dim: int = 100, transe_epochs: int = 200,
        n_attention_head: int = 2, fc_dim: int = 200, n_fc_layer: int = 0,
        p_emb: float = 0.2, p_gnn: float = 0.2, p_fc: float = 0.2,
        ie_dim: int = 200, info_exchange: bool = True, max_length: int = 256,
    ):
        super().__init__()
        if kg_mode not in KG_PATHS:
            raise ValueError(f"kg_mode must be one of {list(KG_PATHS)}, got {kg_mode!r}")
        self.kg_mode = kg_mode
        self.max_length = max_length

        raw_graph = KnowledgeGraph.load(KG_PATHS[kg_mode])
        self.graph = _mint_missing_candidate_nodes(raw_graph)
        node_index = self.graph.node_index()
        self.n_real_nodes = len(self.graph.nodes)
        self.n_node_total = self.n_real_nodes + 1  # +1: context node lives at position 0

        self.node_labels_lower = [n.label.lower() for n in self.graph.nodes]
        self.candidate_pos = {
            subtask: [node_index[f"{SUBTASK_NODE_TYPE[subtask]}:{label}"] + 1 for label in labels]
            for subtask, labels in SUBTASK_LABELS.items()
        }  # +1: same context-node offset as every other real-node position

        relation_types = self.graph.relation_types()
        rel_index = {r: i for i, r in enumerate(relation_types)}
        n_etype = len(relation_types)
        if self.graph.edges:
            edge_index = torch.tensor(
                [[node_index[e.source] + 1, node_index[e.target] + 1] for e in self.graph.edges], dtype=torch.long,
            ).t()
            edge_type = torch.tensor([rel_index[e.relation] for e in self.graph.edges], dtype=torch.long)
        else:
            edge_index = torch.zeros(2, 0, dtype=torch.long)
            edge_type = torch.zeros(0, dtype=torch.long)
        self.register_buffer("base_edge_index", edge_index)
        self.register_buffer("base_edge_type", edge_type)

        pretrained_concept_emb = train_transe(self.graph, dim=concept_dim, epochs=transe_epochs)

        self.tokenizer = AutoTokenizer.from_pretrained(base_model_name)
        self.lmgnn = LMGNN(
            base_model_name, k=k, n_ntype=4, n_etype=n_etype,
            num_concepts=self.n_real_nodes + 1, concept_dim=concept_dim,
            pretrained_concept_emb=pretrained_concept_emb, freeze_ent_emb=True,
            n_attention_head=n_attention_head, fc_dim=fc_dim, n_fc_layer=n_fc_layer,
            p_emb=p_emb, p_gnn=p_gnn, p_fc=p_fc, ie_dim=ie_dim, info_exchange=info_exchange,
        )

    def _mentioned_node_type(self, texts: list, device) -> torch.Tensor:
        """[bs, n_node_total] long: 3 at position 0 (context), else 0 (this node's label
        found as a substring of the instance text -- lightweight entity-linking stand-in,
        see scratchpad.md) or 2 (not found). Candidate-node overrides (type 1) are
        applied per (instance, candidate) row afterward, in forward_subtask."""
        bs = len(texts)
        node_type = torch.full((bs, self.n_node_total), 2, dtype=torch.long)
        node_type[:, 0] = 3
        for b, text in enumerate(texts):
            text_lower = text.lower()
            for i, label_lower in enumerate(self.node_labels_lower):
                if label_lower and label_lower in text_lower:
                    node_type[b, i + 1] = 0
        return node_type.to(device)

    def _batched_edges(self, num_rows: int, device):
        n = self.n_node_total
        e = self.base_edge_index.size(1)
        if e == 0:
            return (
                torch.zeros(2, 0, dtype=torch.long, device=device),
                torch.zeros(0, dtype=torch.long, device=device),
            )
        offsets = (torch.arange(num_rows, device=device) * n).view(-1, 1, 1)
        edge_index = self.base_edge_index.to(device).unsqueeze(0) + offsets  # [num_rows, 2, E]
        edge_index = edge_index.permute(1, 0, 2).reshape(2, -1)
        edge_type = self.base_edge_type.to(device).repeat(num_rows)
        return edge_index, edge_type

    def forward_subtask(self, texts: list, subtask: str, device=None) -> torch.Tensor:
        """texts: list of `bs` raw instance strings. Returns [bs, num_candidates]
        logits -- one LMGNN forward per (instance, candidate) row, batched together, one
        candidate label per row tokenized as a sentence pair (instance text, candidate
        label text)."""
        device = device or next(self.parameters()).device
        labels = SUBTASK_LABELS[subtask]
        nc = len(labels)
        bs = len(texts)

        base_node_type = self._mentioned_node_type(texts, device)  # [bs, n_node_total]
        candidate_pos = self.candidate_pos[subtask]

        pair_texts, pair_candidates, node_type_rows = [], [], []
        for b in range(bs):
            for c in range(nc):
                pair_texts.append(texts[b])
                pair_candidates.append(labels[c].replace("_", " "))
                row = base_node_type[b].clone()
                row[candidate_pos[c]] = 1
                node_type_rows.append(row)
        node_type_ids = torch.stack(node_type_rows, dim=0)  # [bs*nc, n_node_total]

        enc = self.tokenizer(
            pair_texts, pair_candidates, truncation="only_first", max_length=self.max_length,
            padding=True, return_tensors="pt",
        )
        input_ids = enc["input_ids"].to(device)
        attention_mask = enc["attention_mask"].to(device)

        num_rows = bs * nc
        concept_ids = torch.arange(self.n_node_total, device=device).unsqueeze(0).expand(num_rows, -1)
        node_scores = torch.zeros(num_rows, self.n_node_total, 1, device=device)
        edge_index, edge_type = self._batched_edges(num_rows, device)

        logits, _ = self.lmgnn(input_ids, attention_mask, concept_ids, node_type_ids, node_scores, edge_index, edge_type)
        return logits.view(bs, nc)

    def forward(
        self, texts: list, st1_labels=None, st2_labels=None, st3_labels=None,
        st2_loss_weight: float = 1.0, st3_loss_weight: float = 1.0,
        st2_pos_weight=None, st3_pos_weight=None,
    ) -> dict:
        device = next(self.parameters()).device
        st1_logits = self.forward_subtask(texts, "st1", device)
        st2_logits = self.forward_subtask(texts, "st2", device)
        st3_logits = self.forward_subtask(texts, "st3", device)

        loss = None
        if st1_labels is not None:
            loss = (
                F.cross_entropy(st1_logits, st1_labels.to(device))
                + st2_loss_weight * F.binary_cross_entropy_with_logits(
                    st2_logits, st2_labels.to(device), pos_weight=st2_pos_weight,
                )
                + st3_loss_weight * F.binary_cross_entropy_with_logits(
                    st3_logits, st3_labels.to(device), pos_weight=st3_pos_weight,
                )
            )
        return {"loss": loss, "st1_logits": st1_logits, "st2_logits": st2_logits, "st3_logits": st3_logits}
