"""TransE pretraining on a KnowledgeGraph's own (source, relation, target) triples --
stands in for the original GreaseLM paper's externally-supplied, ConceptNet-pretrained
`cp_emb.pt` (adaptation #5 in the plan), since no equivalent exists for our custom
domain KGs. No disk caching (see scratchpad.md): callers may mutate the graph (mint
extra isolated candidate nodes) between loading and training, so a path/mtime-keyed
cache would go stale silently; training is sub-second on graphs this small anyway.

TransE itself: entities and relations each get a d-dim vector; training pushes
e_source + e_relation ~= e_target for true triples, via a margin ranking loss against
corrupted (random wrong source or target) negatives, with entity vectors renormalized
to unit norm each epoch (prevents the trivial "scale everything up" collapse).
"""
import torch
import torch.nn as nn
import torch.nn.functional as F

from .graph_schema import KnowledgeGraph


def train_transe(
    graph: KnowledgeGraph, dim: int = 100, epochs: int = 200, margin: float = 1.0,
    lr: float = 0.01, seed: int = 42,
) -> torch.Tensor:
    """Returns a [len(graph.nodes) + 1, dim] tensor: row 0 is a zero row reserved for
    the context/dummy node slot (LMGNN zeroes it at runtime regardless), rows 1..N are
    the trained entity embeddings for graph.nodes[0..N-1], in that order -- i.e. this
    is exactly the `pretrained_concept_emb` LMGNN's CustomizedEmbedding expects, no
    further offsetting needed by the caller."""
    n = len(graph.nodes)
    node_index = graph.node_index()
    relation_types = graph.relation_types()
    rel_index = {r: i for i, r in enumerate(relation_types)}
    n_rel = len(relation_types)

    triples = torch.tensor(
        [[node_index[e.source], rel_index[e.relation], node_index[e.target]] for e in graph.edges],
        dtype=torch.long,
    )
    if triples.numel() == 0:
        # no edges at all (degenerate/empty graph) -- nothing to train, random init is all we can offer
        out = torch.zeros(n + 1, dim)
        out[1:].normal_(mean=0.0, std=0.02)
        return out

    gen = torch.Generator().manual_seed(seed)
    bound = 6 / (dim ** 0.5)
    entity_emb = nn.Embedding(n, dim)
    relation_emb = nn.Embedding(n_rel, dim)
    nn.init.uniform_(entity_emb.weight, -bound, bound, generator=gen)
    nn.init.uniform_(relation_emb.weight, -bound, bound, generator=gen)

    optimizer = torch.optim.Adam(list(entity_emb.parameters()) + list(relation_emb.parameters()), lr=lr)
    src, rel, tgt = triples[:, 0], triples[:, 1], triples[:, 2]
    n_triples = triples.size(0)

    for _ in range(epochs):
        with torch.no_grad():
            entity_emb.weight.div_(entity_emb.weight.norm(dim=1, keepdim=True).clamp_min(1e-12))

        corrupt_source = torch.rand(n_triples, generator=gen) < 0.5
        rand_nodes = torch.randint(0, n, (n_triples,), generator=gen)
        neg_src = torch.where(corrupt_source, rand_nodes, src)
        neg_tgt = torch.where(corrupt_source, tgt, rand_nodes)

        pos_dist = (entity_emb(src) + relation_emb(rel) - entity_emb(tgt)).norm(dim=1)
        neg_dist = (entity_emb(neg_src) + relation_emb(rel) - entity_emb(neg_tgt)).norm(dim=1)
        loss = F.relu(margin + pos_dist - neg_dist).mean()

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    out = torch.zeros(n + 1, dim)
    out[1:] = entity_emb.weight.detach()
    return out
