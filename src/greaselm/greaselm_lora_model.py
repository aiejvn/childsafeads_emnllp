"""GreaseLM + LoRA classifier: a NEW, standalone integration line (see
greaselm_lora_train.py for the training loop). Does not import/modify
greaselm_model.py or lora_model.py -- this is a separate experimental recipe that
happens to reuse the same lower-level building blocks both of those already reuse
(`GreaseLMTextKGEncoder` from modeling/modeling_greaselm.py, GreaseLM/utils/layers.py's
CustomizedEmbedding/MLP/MultiheadAttPoolLayer, kg_embeddings.py's train_transe,
graph_schema.py's KnowledgeGraph).

Why this is NOT `greaselm_model.py` reused as-is: that class treats every ST1/ST2/ST3
candidate label as a separate multiple-choice "answer" node and does one full LMGNN
forward PER CANDIDATE (25 forwards per training instance -- 5 st1 + 12 st2 + 8 st3).
That is what makes their own baseline run (300-sample subset, 200 epochs, ~5h) top out
at mean_macro_f1=0.489: most of the compute budget goes to redundant forwards, not
learning signal. See scratchpad.md for the full history.

The redesign here: ONE forward per instance, classification-style (mirroring
common/multitask_encoder.py's MultiTaskEncoder: one shared trunk, three independent
linear heads), while still genuinely exercising the GNN. Every st1/st2/st3 label node
in the KG is marked node_type=1 ("answer/label" node) on EVERY forward -- not
conditionally per a single candidate being scored -- so the GATConvE + MInt layers
attend over the KG once per instance, not once per candidate. Node types:
    3 = context node (position 0, no edges beyond GATConvE's automatic self-loop)
    1 = an st1_label/st2_label/st3_flag node (always, regardless of instance content)
    0 = any other node whose label substring-matches the instance text (same
        lightweight entity-linking stand-in greaselm_model.py already uses)
    2 = everything else
This makes one training step cost about the same as one MultiTaskEncoder forward plus
a small (tens-of-nodes) GNN pass -- no 25x blowup -- so the full 2353/504 train/dev
split fits a 10-epoch budget comfortably (confirmed by timing, see
greaselm_lora_train.py's module docstring / the run log).

LoRA wiring: build the full GreaseLMLoRAClassifier first, THEN
`get_peft_model(model, LoraConfig(target_modules=[...], task_type=FEATURE_EXTRACTION))`
with no `modules_to_save` (fragile with this much nesting -- see plan). That freezes
everything except LoRA A/B by default; `unfreeze_non_lora(...)` below does a manual
second pass to re-enable gradients on the genuinely-new parts (GATConvE, MInt, the
top-level attention pooler, trunk, heads, edge_encoder, emb_node_type, emb_score) while
leaving the frozen LM backbone (adapted only via LoRA) and the pretrained/frozen TransE
concept-embedding table untouched.

Reference for why the second `nn.ModuleList` reference (GreaseLMGNNLayers.lm_layers,
which is the *same* object as `self.mp.lm.encoder.layer`) stays valid after PEFT swaps
query/value Linear submodules in-place: modeling_greaselm.py's module docstring +
verified empirically in greaselm_lora_smoke.py.
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
from .modeling.modeling_greaselm import GreaseLMTextKGEncoder

_GREASELM_SUBMODULE = os.path.join(os.path.dirname(__file__), "..", "..", "GreaseLM")
import sys  # noqa: E402
sys.path.insert(0, _GREASELM_SUBMODULE)
from utils.layers import CustomizedEmbedding, MLP, MultiheadAttPoolLayer  # noqa: E402

KG_DIR = os.path.join(os.path.dirname(__file__), "kg")
KG_PATHS = {
    "legal": os.path.join(KG_DIR, "legal_taxonomy_graph.json"),
    "flow": os.path.join(KG_DIR, "flow_graph.json"),
    "combined": os.path.join(KG_DIR, "combined_graph.json"),
}

SUBTASK_LABELS = {"st1": ST1_LABELS, "st2": ST2_LABELS, "st3": ST3_LABELS}
SUBTASK_NODE_TYPE = {"st1": "st1_label", "st2": "st2_label", "st3": "st3_flag"}


def _mint_missing_candidate_nodes(graph: KnowledgeGraph) -> KnowledgeGraph:
    """Copied/adapted from greaselm_model.py (not imported -- see module docstring):
    mints an isolated node for any ST1/ST2/ST3 label missing from the loaded graph, so
    every label has a real concept-embedding row and can be marked node_type=1."""
    graph = copy.deepcopy(graph)
    for subtask, labels in SUBTASK_LABELS.items():
        node_type = SUBTASK_NODE_TYPE[subtask]
        existing = {n.label for n in graph.nodes if n.type == node_type}
        for label in labels:
            if label not in existing:
                graph.add_node(f"{node_type}:{label}", node_type, label)
    return graph


class GreaseLMLoRAClassifier(nn.Module):
    def __init__(
        self, kg_mode: str = "combined", base_model_name: str = "FacebookAI/roberta-base",
        k: int = 2, concept_dim: int = 100, transe_epochs: int = 200,
        n_attention_head: int = 2, fc_dim: int = 200, n_fc_layer: int = 1,
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
        # Flat list of every st1/st2/st3 label node's position (+1 context offset),
        # across all three subtasks -- these are ALWAYS node_type=1, every forward.
        all_candidate_pos = []
        for subtask, labels in SUBTASK_LABELS.items():
            node_type = SUBTASK_NODE_TYPE[subtask]
            for label in labels:
                all_candidate_pos.append(node_index[f"{node_type}:{label}"] + 1)
        self.register_buffer("candidate_pos", torch.tensor(sorted(set(all_candidate_pos)), dtype=torch.long))

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

        # --- The three reused building blocks, wired the same way LMGNN wires them
        # (modeling_greaselm.py), but as direct attributes here instead of nested
        # inside an LMGNN that forces a single-logit-per-forward QA framing. ---
        concept_in_dim = pretrained_concept_emb.size(1)
        self.concept_emb = CustomizedEmbedding(
            concept_num=self.n_real_nodes + 1, concept_in_dim=concept_in_dim, concept_out_dim=concept_dim,
            pretrained_concept_emb=pretrained_concept_emb, freeze_ent_emb=True,
        )
        self.dropout_e = nn.Dropout(p_emb)
        self.mp = GreaseLMTextKGEncoder(
            base_model_name, k, n_ntype=4, n_etype=n_etype, concept_dim=concept_dim, dropout=p_gnn,
            ie_dim=ie_dim, info_exchange=info_exchange,
        )
        self.pooler = MultiheadAttPoolLayer(n_attention_head, self.mp.sent_dim, concept_dim)

        concat_dim = concept_dim * 2 + self.mp.sent_dim
        self.trunk = MLP(concat_dim, fc_dim, fc_dim, n_fc_layer, p_fc, layer_norm=True)
        self.dropout_fc = nn.Dropout(p_fc)
        self.st1_head = nn.Linear(fc_dim, len(ST1_LABELS))
        self.st2_head = nn.Linear(fc_dim, len(ST2_LABELS))
        self.st3_head = nn.Linear(fc_dim, len(ST3_LABELS))

    def _node_type_ids(self, texts: list, device) -> torch.Tensor:
        """[bs, n_node_total] long: 3 at position 0 (context); 1 at every st1/st2/st3
        label node (always -- the key redesign vs. greaselm_model.py's per-candidate
        conditional type-1 marking); 0 at any other node whose label is a substring hit
        in the instance text; 2 everywhere else."""
        bs = len(texts)
        node_type = torch.full((bs, self.n_node_total), 2, dtype=torch.long)
        node_type[:, 0] = 3
        for b, text in enumerate(texts):
            text_lower = text.lower()
            for i, label_lower in enumerate(self.node_labels_lower):
                if label_lower and label_lower in text_lower:
                    node_type[b, i + 1] = 0
        node_type[:, self.candidate_pos] = 1
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

    def forward(
        self, input_ids=None, texts: list = None, attention_mask=None, inputs_embeds=None,
        st1_labels=None, st2_labels=None, st3_labels=None,
        st2_loss_weight: float = 1.0, st3_loss_weight: float = 1.0,
        st2_pos_weight=None, st3_pos_weight=None, **kwargs,
    ) -> dict:
        """`input_ids` is (despite the name) a list[str] of raw instance texts, not a
        tokenized tensor -- tokenization happens internally (same convention
        greaselm_model.py uses). Named `input_ids` rather than `texts` so this lines up
        with `PeftModelForFeatureExtraction.forward`'s fixed positional signature
        (input_ids, attention_mask, inputs_embeds, ...) -- PEFT's FEATURE_EXTRACTION
        wrapper always calls the wrapped module with those exact keyword names, so a
        differently-named first argument would silently land in **kwargs instead. Callers
        may also pass `texts=` directly (bypassing PEFT) for convenience/tests;
        `attention_mask`/`inputs_embeds` are accepted-and-ignored, same as
        MultiTaskEncoder's **kwargs catch-all for the same wrapper quirk."""
        texts = texts if texts is not None else input_ids
        device = next(self.parameters()).device
        bs = len(texts)

        node_type_ids = self._node_type_ids(texts, device)  # [bs, n_node_total]
        concept_ids = torch.arange(self.n_node_total, device=device).unsqueeze(0).expand(bs, -1)
        node_scores = torch.zeros(bs, self.n_node_total, 1, device=device)
        edge_index, edge_type = self._batched_edges(bs, device)

        enc = self.tokenizer(
            texts, truncation=True, max_length=self.max_length, padding=True, return_tensors="pt",
        )
        input_ids = enc["input_ids"].to(device)
        attention_mask = enc["attention_mask"].to(device)

        gnn_input = self.concept_emb(concept_ids)
        gnn_input = gnn_input.clone()
        gnn_input[:, 0] = 0
        gnn_input = self.dropout_e(gnn_input)

        lm_hidden, gnn_output = self.mp(input_ids, attention_mask, gnn_input, edge_index, edge_type, node_type_ids, node_scores)

        sent_vecs = self.mp.pool_lm(lm_hidden)          # [bs, sent_dim] -- LM [CLS]/pooler
        Z_vecs = gnn_output[:, 0]                        # [bs, concept_dim] -- GNN context-node output
        graph_vecs, _ = self.pooler(sent_vecs, gnn_output[:, 1:])  # attention-pool over real KG nodes

        concat = torch.cat([graph_vecs, sent_vecs, Z_vecs], dim=1)
        trunk_out = self.trunk(self.dropout_fc(concat))
        st1_logits = self.st1_head(trunk_out)
        st2_logits = self.st2_head(trunk_out)
        st3_logits = self.st3_head(trunk_out)

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


def unfreeze_non_lora(peft_model) -> None:
    """After get_peft_model() (which by default trains only LoRA A/B), re-enable
    gradients on everything that is genuinely new/untrained in this recipe: GATConvE,
    MInt, the top-level attention pooler, trunk, heads, edge_encoder, emb_node_type,
    emb_score. Leaves frozen: the pretrained/frozen TransE concept-embedding table
    (`concept_emb.emb`, matching freeze_ent_emb=True's convention elsewhere in this
    repo) and the wrapped LM backbone's non-LoRA weights (`mp.lm.*`, adapted only via
    LoRA A/B)."""
    for name, p in peft_model.named_parameters():
        if "lora_" in name:
            continue  # already trainable (get_peft_model's default)
        if ".concept_emb.emb" in name:
            continue  # keep frozen: pretrained TransE table
        if ".mp.lm." in name:
            continue  # frozen transformer backbone, adapted only via LoRA A/B
        p.requires_grad = True


def count_trainable_parameters(model) -> tuple:
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    return trainable, total
