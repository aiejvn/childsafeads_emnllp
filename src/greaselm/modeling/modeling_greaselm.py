"""LM+GNN core, ported from GreaseLM/modeling/modeling_greaselm.py (snap-stanford/
GreaseLM, MIT-licensed): TextKGMessagePassing -> GreaseLMTextKGEncoder, RoBERTaGAT ->
GreaseLMGNNLayers, LMGNN -> LMGNN. Full rationale in
/home/k6/.claude/plans/parallel-juggling-rabin.md; short version:

  - Wraps `AutoModel.from_pretrained(base_model_name)` instead of subclassing
    modeling_bert/modeling_roberta (removed in our transformers version) or BertEncoder
    (as the original RoBERTaGAT does). One consequence: GreaseLMGNNLayers holds a
    second reference to the same `nn.ModuleList` of LM blocks that `self.lm` already
    registers -- verified this is harmless (PyTorch's default `remove_duplicate=True`
    means `.parameters()`/the optimizer see each tensor once, no double updates).
  - Confirmed empirically: `layer_module(hidden_states, attention_mask)` returns a bare
    Tensor here, not the old `(hidden_states, ...)` tuple -- no `[0]` unpacking.
  - Reframed as QA, faithfully: each ST1/ST2/ST3 candidate label is a "choice" (the
    dialog-flow export already stores these reasoning nodes as question+choices).
    `n_ntype=4` is kept as the paper has it (0=question-entity, 1=answer-entity,
    2=other, 3=context) -- node type 1 marks whichever candidate label this forward
    call is scoring, so LMGNN scores exactly one (text, candidate) pair per call, same
    as the original, and `greaselm_model.py` plays the outer `GreaseLM` wrapper's role
    (batches many candidates, offsets their edge_index like `GreaseLM.batch_graph`),
    generalized to run per-subtask (softmax+CE for st1's 5 mutually-exclusive choices,
    independent sigmoid+BCE per candidate for st2/st3).
  - No adj_lengths/padding: every instance uses the whole fixed-size KG, nothing to pad.
  - The unimodal/cross-modal split (paper's N-K unimodal + K cross-modal GreaseLM
    layers, GreaseLM paper Sec. 3.1) falls out of one `if i >= num_hidden_layers - k`
    gate in GreaseLMGNNLayers.forward, same as the original RoBERTaGAT.forward: the
    first N-K blocks run as plain LM layers, only the last K also run GATConvE + MInt.
"""
import os
import sys

import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoModel

_GREASELM_SUBMODULE = os.path.join(os.path.dirname(__file__), "..", "..", "..", "GreaseLM")
if not os.path.isdir(os.path.join(_GREASELM_SUBMODULE, "utils")):
    raise RuntimeError(
        "the GreaseLM submodule isn't checked out at ./GreaseLM -- this package imports "
        "utils/layers.py straight from it (dependency-clean, no need to duplicate). Run "
        "`git submodule update --init GreaseLM` from the repo root."
    )
sys.path.insert(0, _GREASELM_SUBMODULE)
from utils.layers import GELU, CustomizedEmbedding, MultiheadAttPoolLayer, MLP  # noqa: E402

from .modeling_gnn import GATConvE  # noqa: E402


class GreaseLMGNNLayers(nn.Module):
    """Ported from RoBERTaGAT: runs the LM's blocks one at a time (the first N-K are
    unimodal, LM-only); for the top K, also runs one GATConvE layer, then MInt-fuses
    [CLS] (LM) with the context node (GNN) and splits the result back into both
    streams."""

    def __init__(self, lm_layers, k, n_ntype, n_etype, hidden_size, dropout, ie_dim, sent_dim,
                 info_exchange=True, ie_layer_num=1, sep_ie_layers=False):
        super().__init__()
        self.lm_layers = lm_layers  # nn.ModuleList; second reference into the wrapped AutoModel, see module docstring
        self.num_hidden_layers = len(lm_layers)
        self.k = k
        self.edge_encoder = nn.Sequential(
            nn.Linear(n_etype + 1 + n_ntype * 2, hidden_size), nn.BatchNorm1d(hidden_size),
            nn.ReLU(), nn.Linear(hidden_size, hidden_size),
        )
        self.gnn_layers = nn.ModuleList([GATConvE(hidden_size, n_ntype, n_etype, self.edge_encoder) for _ in range(k)])
        self.activation = GELU()
        self.dropout_rate = dropout
        self.info_exchange = info_exchange

        # --- MInt: the bidirectional LM<->GNN interaction-node fusion module. One MLP
        # per fused layer (or one shared across all k, if sep_ie_layers=False); input =
        # [CLS] (LM) concat context-node (GNN), output is split back into both streams.
        self.sep_ie_layers = sep_ie_layers
        if sep_ie_layers:
            self.mint_layers = nn.ModuleList(
                [MLP(sent_dim + hidden_size, ie_dim, sent_dim + hidden_size, ie_layer_num, dropout) for _ in range(k)]
            )
        else:
            self.mint = MLP(sent_dim + hidden_size, ie_dim, sent_dim + hidden_size, ie_layer_num, dropout)

    def forward(self, hidden_states, attention_mask, _X, edge_index, edge_type, _node_type, _node_feature_extra):
        bs = hidden_states.size(0)
        for i, layer_module in enumerate(self.lm_layers):
            # --- plain (unimodal, if i < num_hidden_layers - k) LM block ---
            hidden_states = layer_module(hidden_states, attention_mask)  # bare Tensor in this transformers version

            if i >= self.num_hidden_layers - self.k:
                gnn_layer_index = i - self.num_hidden_layers + self.k

                # --- cross-modal layer, part 1: one GNN block (GATConvE) ---
                _X = self.gnn_layers[gnn_layer_index](_X, edge_index, edge_type, _node_type, _node_feature_extra)
                _X = self.activation(_X)
                _X = F.dropout(_X, self.dropout_rate, training=self.training)

                # --- cross-modal layer, part 2: MInt block. Fuse LM's [CLS]
                # (position 0) with GNN's context node (node 0), write the fused
                # halves back into both streams ---
                if self.info_exchange:
                    X = _X.view(bs, -1, _X.size(1))  # [bs, n_node, concept_dim]
                    cls_feats = hidden_states[:, 0, :]
                    context_node_feats = X[:, 0, :]
                    mint_input = torch.cat([cls_feats, context_node_feats], dim=1)
                    mint = self.mint_layers[gnn_layer_index] if self.sep_ie_layers else self.mint
                    mint_output = mint(mint_input)
                    fused_cls_feats, fused_context_node_feats = torch.split(
                        mint_output, [cls_feats.size(1), context_node_feats.size(1)], dim=1,
                    )
                    hidden_states = hidden_states.clone()
                    hidden_states[:, 0, :] = fused_cls_feats
                    X = X.clone()
                    X[:, 0, :] = fused_context_node_feats
                    _X = X.view_as(_X)
                # --- end MInt block ---
        return hidden_states, _X


class GreaseLMTextKGEncoder(nn.Module):
    """Ported from TextKGMessagePassing. node_type -> emb_node_type (Linear->GELU);
    node_score -> sinusoidal basis sin(1.1^j * score) -> emb_score (Linear->GELU).
    Drives GreaseLMGNNLayers with the LM's raw embedding output."""

    def __init__(self, base_model_name, k, n_ntype, n_etype, concept_dim, dropout=0.2,
                 ie_dim=200, info_exchange=True, ie_layer_num=1, sep_ie_layers=False):
        super().__init__()
        self.lm = AutoModel.from_pretrained(base_model_name)
        self.n_ntype = n_ntype
        self.n_etype = n_etype
        self.hidden_size = concept_dim
        self.emb_node_type = nn.Linear(n_ntype, concept_dim // 2)
        self.emb_score = nn.Linear(concept_dim // 2, concept_dim // 2)
        self.activation = GELU()
        self.Vh = nn.Linear(concept_dim, concept_dim)
        self.Vx = nn.Linear(concept_dim, concept_dim)
        self.dropout = nn.Dropout(dropout)
        self.sent_dim = self.lm.config.hidden_size
        self.gnn_layers_module = GreaseLMGNNLayers(
            self.lm.encoder.layer, k=k, n_ntype=n_ntype, n_etype=n_etype, hidden_size=concept_dim,
            dropout=dropout, ie_dim=ie_dim, sent_dim=self.sent_dim,
            info_exchange=info_exchange, ie_layer_num=ie_layer_num, sep_ie_layers=sep_ie_layers,
        )

    def pool_lm(self, sequence_output: torch.Tensor) -> torch.Tensor:
        if getattr(self.lm, "pooler", None) is not None:
            return self.lm.pooler(sequence_output)
        return sequence_output[:, 0]

    def forward(self, input_ids, attention_mask, H, edge_index, edge_type, node_type, node_score):
        """
        H: [bs, n_node, concept_dim] node features (context row already zeroed by LMGNN)
        edge_index/edge_type: already batched/offset across the bs graphs
        node_type: [bs, n_node] long in {0,1,2,3}; node_score: [bs, n_node, 1] float
        """
        embedding_output = self.lm.embeddings(input_ids=input_ids)
        extended_attention_mask = self.lm.get_extended_attention_mask(attention_mask, input_ids.shape)

        bs, n_node = node_type.size()
        T = F.one_hot(node_type.reshape(-1), self.n_ntype).float().view(bs, n_node, self.n_ntype)
        node_type_emb = self.activation(self.emb_node_type(T))

        js = torch.pow(torch.full((), 1.1, device=node_type.device), torch.arange(self.hidden_size // 2, device=node_type.device).float())
        B = torch.sin(js.view(1, 1, -1) * node_score)
        node_score_emb = self.activation(self.emb_score(B))

        _X = H.view(-1, H.size(2))  # [bs*n_node, concept_dim]
        _node_type = node_type.reshape(-1)  # [bs*n_node]
        _node_feature_extra = torch.cat([node_type_emb, node_score_emb], dim=2).reshape(_node_type.size(0), -1)

        lm_hidden, _X = self.gnn_layers_module(
            embedding_output, extended_attention_mask, _X, edge_index, edge_type, _node_type, _node_feature_extra,
        )

        X = _X.view(bs, n_node, -1)
        output = self.activation(self.Vh(H) + self.Vx(X))
        output = self.dropout(output)
        return lm_hidden, output


class LMGNN(nn.Module):
    """Ported from LMGNN, including its final `fc` head: each forward call scores
    exactly one (text, candidate-label) pair and returns a single logit, same as the
    original -- greaselm_model.py batches many candidates through this per instance."""

    def __init__(self, base_model_name, k, n_ntype, n_etype, num_concepts, concept_dim,
                 pretrained_concept_emb=None, freeze_ent_emb=True, n_attention_head=2,
                 fc_dim=200, n_fc_layer=0, p_emb=0.2, p_gnn=0.2, p_fc=0.2,
                 ie_dim=200, info_exchange=True, ie_layer_num=1, sep_ie_layers=False):
        super().__init__()
        concept_in_dim = pretrained_concept_emb.size(1) if pretrained_concept_emb is not None else concept_dim
        self.concept_emb = CustomizedEmbedding(
            concept_num=num_concepts, concept_in_dim=concept_in_dim, concept_out_dim=concept_dim,
            pretrained_concept_emb=pretrained_concept_emb, freeze_ent_emb=freeze_ent_emb,
        )
        self.dropout_e = nn.Dropout(p_emb)
        self.mp = GreaseLMTextKGEncoder(
            base_model_name, k, n_ntype, n_etype, concept_dim, dropout=p_gnn, ie_dim=ie_dim,
            info_exchange=info_exchange, ie_layer_num=ie_layer_num, sep_ie_layers=sep_ie_layers,
        )
        self.pooler = MultiheadAttPoolLayer(n_attention_head, self.mp.sent_dim, concept_dim)
        concat_dim = concept_dim * 2 + self.mp.sent_dim
        self.fc = MLP(concat_dim, fc_dim, 1, n_fc_layer, p_fc, layer_norm=True)
        self.dropout_fc = nn.Dropout(p_fc)

    def forward(self, input_ids, attention_mask, concept_ids, node_type_ids, node_scores, edge_index, edge_type):
        """
        concept_ids: [bs, n_node] long -- index 0 is always the context node (value
            ignored, embedding zeroed below); indices 1.. index into the KG's node list
        node_type_ids: [bs, n_node] long in {0,1,2,3}: 1 marks this row's candidate
            label node, 0 marks other nodes mentioned in the segment text, 3 is always
            index 0 (context), 2 is everything else
        node_scores: [bs, n_node, 1] float, zeros
        edge_index/edge_type: already batched/offset (greaselm_model.py's batch_graph)

        Returns (logits, pool_attn); logits: [bs, 1], one score per (text, candidate).
        """
        gnn_input = self.concept_emb(concept_ids)
        gnn_input = gnn_input.clone()
        gnn_input[:, 0] = 0
        gnn_input = self.dropout_e(gnn_input)

        lm_hidden, gnn_output = self.mp(input_ids, attention_mask, gnn_input, edge_index, edge_type, node_type_ids, node_scores)

        sent_vecs = self.mp.pool_lm(lm_hidden)  # [bs, sent_dim]
        Z_vecs = gnn_output[:, 0]  # [bs, concept_dim] -- context node's final GNN embedding

        graph_vecs, pool_attn = self.pooler(sent_vecs, gnn_output[:, 1:])  # attention-pool over real KG nodes only

        concat = torch.cat([graph_vecs, sent_vecs, Z_vecs], dim=1)
        logits = self.fc(self.dropout_fc(concat))
        return logits, pool_attn
