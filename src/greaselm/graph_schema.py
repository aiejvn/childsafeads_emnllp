"""Typed graph schema shared by every KG builder in src/greaselm/kg/ and consumed by
greaselm_model.py. Mirrors the shape of emnllp-dialog-flow-dialog-flow.json (a "nodes"
list with id/type/data.label, an "edges" list with id/source/target) so a KG built here
can be inspected with the same mental model as that flow export, and so a future flow
export can be parsed with the same loader. The one addition on top of the flow-JSON
shape is `relation` on each edge, since a knowledge graph's edges carry semantic types
(has_severity, in_family, ...) that a UI flow's edges don't need.

Three KG variants are built from this schema (build_legal_kg.py, build_flow_kg.py,
build_combined_kg.py); greaselm_model.py is graph-source-agnostic (reads whichever JSON
it's pointed at, no node/edge count hardcoded), so switching between them is a
constructor argument, not a code change.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field


@dataclass
class KGNode:
    id: str
    type: str
    label: str
    meta: dict = field(default_factory=dict)

    def to_json(self) -> dict:
        return {"id": self.id, "type": self.type, "data": {"label": self.label, "meta": self.meta}}

    @staticmethod
    def from_json(d: dict) -> "KGNode":
        return KGNode(id=d["id"], type=d["type"], label=d["data"]["label"], meta=d["data"].get("meta", {}))


@dataclass
class KGEdge:
    source: str
    target: str
    relation: str
    meta: dict = field(default_factory=dict)

    @property
    def id(self) -> str:
        return f"edge_{self.source}_{self.relation}_{self.target}"

    def to_json(self) -> dict:
        return {
            "id": self.id, "source": self.source, "target": self.target,
            "relation": self.relation, "data": {"meta": self.meta},
        }

    @staticmethod
    def from_json(d: dict) -> "KGEdge":
        return KGEdge(source=d["source"], target=d["target"], relation=d["relation"], meta=d.get("data", {}).get("meta", {}))


class KnowledgeGraph:
    def __init__(self, name: str, nodes: list = None, edges: list = None):
        self.name = name
        self.nodes: list = nodes or []
        self.edges: list = edges or []

    def add_node(self, id: str, type: str, label: str, **meta) -> None:
        if id in self.node_index():
            raise ValueError(f"duplicate node id {id!r} in graph {self.name!r}")
        self.nodes.append(KGNode(id=id, type=type, label=label, meta=meta))

    def add_edge(self, source: str, target: str, relation: str, **meta) -> None:
        idx = self.node_index()
        if source not in idx:
            raise ValueError(f"edge source {source!r} is not a node in graph {self.name!r}")
        if target not in idx:
            raise ValueError(f"edge target {target!r} is not a node in graph {self.name!r}")
        self.edges.append(KGEdge(source=source, target=target, relation=relation, meta=meta))

    def node_index(self) -> dict:
        """id -> position in self.nodes, i.e. the row a node occupies in the encoder's
        node-embedding table. Recomputed on demand (graphs here are small, built once
        then static) rather than cached, so it's always consistent with self.nodes."""
        return {n.id: i for i, n in enumerate(self.nodes)}

    def node_types(self) -> list:
        return sorted({n.type for n in self.nodes})

    def relation_types(self) -> list:
        return sorted({e.relation for e in self.edges})

    def merge(self, other: "KnowledgeGraph", name: str = None) -> "KnowledgeGraph":
        """Union of two graphs' nodes/edges. Node ids must already be disjoint (the
        builders namespace ids per-source, e.g. "st3_flag:x" vs a flow node's UUID, so
        this never has to rewrite ids)."""
        overlap = set(self.node_index()) & set(other.node_index())
        if overlap:
            raise ValueError(f"cannot merge graphs with overlapping node ids: {sorted(overlap)[:5]}...")
        return KnowledgeGraph(
            name or f"{self.name}+{other.name}",
            list(self.nodes) + list(other.nodes),
            list(self.edges) + list(other.edges),
        )

    def to_json(self) -> dict:
        return {
            "version": "1.0",
            "knowledgeGraph": {"name": self.name},
            "nodes": [n.to_json() for n in self.nodes],
            "edges": [e.to_json() for e in self.edges],
        }

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_json(), f, indent=2)

    def to_mermaid(self, direction: str = "LR") -> str:
        """Renders the same nodes/edges as a Mermaid flowchart instead of JSON, for
        visual inspection (e.g. in an Artifact, which renders ```mermaid fences
        natively) rather than training consumption -- greaselm_model.py still reads
        to_json()/save(), this is a parallel view onto the same graph.
        Node ids are remapped to n0, n1, ... since ids like "st3_flag:no_flag" contain
        characters Mermaid's node-id grammar doesn't accept; the original id/label is
        kept as the node's display text.
        """
        safe_id = {n.id: f"n{i}" for i, n in enumerate(self.nodes)}
        lines = [f"flowchart {direction}"]
        for n in self.nodes:
            label = n.label.replace('"', "'")
            lines.append(f'    {safe_id[n.id]}["{label}"]:::{n.type}')
        for e in self.edges:
            relation = e.relation.replace('"', "'")
            lines.append(f"    {safe_id[e.source]} -->|{relation}| {safe_id[e.target]}")
        for t in self.node_types():
            lines.append(f"    classDef {t} stroke-width:1px")
        return "\n".join(lines)

    def save_mermaid(self, path: str, direction: str = "LR") -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_mermaid(direction))

    @staticmethod
    def load(path: str) -> "KnowledgeGraph":
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        name = d.get("knowledgeGraph", {}).get("name", path)
        return KnowledgeGraph(
            name=name,
            nodes=[KGNode.from_json(n) for n in d["nodes"]],
            edges=[KGEdge.from_json(e) for e in d["edges"]],
        )
