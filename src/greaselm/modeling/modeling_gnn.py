"""GATConvE, ported from GreaseLM/modeling/modeling_gnn.py (snap-stanford/GreaseLM,
MIT-licensed) -- same relational-GAT math, rewritten against plain PyTorch tensor ops
instead of torch_geometric.nn.MessagePassing / torch_scatter.scatter /
torch_geometric.utils.softmax (neither package is installed here, and both pin ancient
CUDA-specific wheels incompatible with our torch==2.13 -- see the plan at
/home/k6/.claude/plans/parallel-juggling-rabin.md for the full compatibility rationale).

Per-edge computation is unchanged from the original:
  - edge feature = one_hot(edge_type) concat one_hot(head_node_type) concat
    one_hot(tail_node_type), projected through `edge_encoder` to an edge embedding.
  - self-loops get their own reserved edge-type slot (index n_etype) before any of this.
  - key   = linear_key(x_i (target) concat edge_embedding)
  - msg   = linear_msg(x_j (source) concat edge_embedding)
  - query = linear_query(x_j (source) alone)
  - score = scaled dot(query, key), softmax'd **grouped by each edge's source node**
    (not target -- a deliberate GreaseLM/QA-GNN choice, kept as-is), then rescaled by
    that source node's out-degree (self-loop counted).
  - messages are aggregated (sum) at each edge's *target* node, then passed through a
    final MLP.

The only actual rewrite is mechanical: torch_geometric's `MessagePassing.propagate` +
`torch_scatter.scatter` + `torch_geometric.utils.softmax` are replaced by
`Tensor.scatter_reduce_`/`scatter_add_`/`index_add_` (all native to torch>=1.12; we have
2.13), operating on the same flattened block-diagonal batched-graph representation the
original uses (see modeling_greaselm.py's batching, which mirrors
GreaseLM.batch_graph offsetting each example's edge_index before concatenation).
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


def scatter_softmax(scores: torch.Tensor, index: torch.Tensor, num_groups: int) -> torch.Tensor:
    """scores: [E, H]; index: [E] long, which of num_groups each row belongs to.
    Returns [E, H] with each group's rows softmax-normalized independently -- the plain
    PyTorch equivalent of torch_geometric.utils.softmax(scores, index)."""
    E, H = scores.shape
    idx = index.unsqueeze(-1).expand(E, H)
    group_max = scores.new_full((num_groups, H), float("-inf"))
    group_max.scatter_reduce_(0, idx, scores, reduce="amax", include_self=True)
    shifted = (scores - group_max.gather(0, idx)).exp()
    group_sum = scores.new_zeros((num_groups, H))
    group_sum.scatter_add_(0, idx, shifted)
    return shifted / group_sum.gather(0, idx).clamp_min(1e-16)


class GATConvE(nn.Module):
    """
    Args:
        emb_dim (int): dimensionality of GNN hidden states
        n_ntype (int): number of node types
        n_etype (int): number of edge relation types
    """
    def __init__(self, emb_dim, n_ntype, n_etype, edge_encoder, head_count=4, aggr="add"):
        super().__init__()
        assert emb_dim % 2 == 0
        assert aggr == "add", "only sum aggregation is implemented in this port"
        self.emb_dim = emb_dim
        self.n_ntype = n_ntype
        self.n_etype = n_etype
        self.edge_encoder = edge_encoder

        self.head_count = head_count
        assert emb_dim % head_count == 0
        self.dim_per_head = emb_dim // head_count
        self.linear_key = nn.Linear(3 * emb_dim, head_count * self.dim_per_head)
        self.linear_msg = nn.Linear(3 * emb_dim, head_count * self.dim_per_head)
        self.linear_query = nn.Linear(2 * emb_dim, head_count * self.dim_per_head)

        self._alpha = None

        self.mlp = nn.Sequential(
            nn.Linear(emb_dim, emb_dim), nn.BatchNorm1d(emb_dim), nn.ReLU(), nn.Linear(emb_dim, emb_dim),
        )

    def forward(self, x, edge_index, edge_type, node_type, node_feature_extra, return_attention_weights=False):
        """
        x: [N, emb_dim]
        edge_index: [2, E] (row 0 = source/head, row 1 = target/tail)
        edge_type: [E,]
        node_type: [N,]
        node_feature_extra: [N, emb_dim]
        """
        N = x.size(0)
        device = x.device

        edge_vec = F.one_hot(edge_type, self.n_etype + 1).float()  # [E, n_etype+1]
        self_edge_vec = torch.zeros(N, self.n_etype + 1, device=device)
        self_edge_vec[:, self.n_etype] = 1

        head_type = node_type[edge_index[0]]  # [E,] head=src
        tail_type = node_type[edge_index[1]]  # [E,] tail=tgt
        head_vec = F.one_hot(head_type, self.n_ntype).float()
        tail_vec = F.one_hot(tail_type, self.n_ntype).float()
        headtail_vec = torch.cat([head_vec, tail_vec], dim=1)  # [E, 2*n_ntype]
        self_head_vec = F.one_hot(node_type, self.n_ntype).float()
        self_headtail_vec = torch.cat([self_head_vec, self_head_vec], dim=1)  # [N, 2*n_ntype]

        edge_vec = torch.cat([edge_vec, self_edge_vec], dim=0)  # [E+N, n_etype+1]
        headtail_vec = torch.cat([headtail_vec, self_headtail_vec], dim=0)  # [E+N, 2*n_ntype]
        edge_embeddings = self.edge_encoder(torch.cat([edge_vec, headtail_vec], dim=1))  # [E+N, emb_dim]

        loop_index = torch.arange(N, dtype=torch.long, device=device).unsqueeze(0).repeat(2, 1)
        edge_index = torch.cat([edge_index, loop_index], dim=1)  # [2, E+N]

        x_cat = torch.cat([x, node_feature_extra], dim=1)  # [N, 2*emb_dim]
        src_index, tgt_index = edge_index[0], edge_index[1]
        x_i = x_cat[tgt_index]  # target features, per edge
        x_j = x_cat[src_index]  # source features, per edge

        key = self.linear_key(torch.cat([x_i, edge_embeddings], dim=1)).view(-1, self.head_count, self.dim_per_head)
        msg = self.linear_msg(torch.cat([x_j, edge_embeddings], dim=1)).view(-1, self.head_count, self.dim_per_head)
        query = self.linear_query(x_j).view(-1, self.head_count, self.dim_per_head)

        query = query / (self.dim_per_head ** 0.5)
        scores = (query * key).sum(dim=2)  # [E+N, heads]
        alpha = scatter_softmax(scores, src_index, N)  # grouped by SOURCE node, matching the original
        self._alpha = alpha

        src_out_degree = torch.bincount(src_index, minlength=N)[src_index].float()  # [E+N,]
        alpha = alpha * src_out_degree.unsqueeze(1)

        weighted_msg = (msg * alpha.unsqueeze(-1)).view(-1, self.head_count * self.dim_per_head)  # [E+N, emb_dim]

        aggr_out = x.new_zeros(N, self.emb_dim)
        aggr_out.index_add_(0, tgt_index, weighted_msg)  # sum messages at each edge's target node

        out = self.mlp(aggr_out)

        alpha_out, self._alpha = self._alpha, None
        if return_attention_weights:
            return out, (edge_index, alpha_out)
        return out
