"""Dialog-flow export loader: JSON file -> node index + outgoing-edge lookup.

node-lab never *traverses* the flow. It resolves one node by id or label, and
(when `--children graph` is on) follows that node's outgoing edges exactly one
hop. Edges are otherwise informational — `node_lab list` prints them for
orientation.
"""

from __future__ import annotations

import json
from pathlib import Path

from .types import FlowEdge, FlowExport, FlowNode


class NodeNotFoundError(LookupError):
    pass


class AmbiguousNodeError(LookupError):
    pass


class Flow:
    def __init__(self, export: FlowExport, path: Path | None = None) -> None:
        self.export = export
        self.path = path
        self._by_id: dict[str, FlowNode] = {n.id: n for n in export.nodes}
        self._by_label: dict[str, list[FlowNode]] = {}
        for node in export.nodes:
            self._by_label.setdefault(node.label, []).append(node)

    @property
    def name(self) -> str:
        return self.export.dialog_flow.name

    @property
    def nodes(self) -> list[FlowNode]:
        return self.export.nodes

    @property
    def edges(self) -> list[FlowEdge]:
        return self.export.edges

    def by_id(self, node_id: str) -> FlowNode | None:
        return self._by_id.get(node_id)

    def resolve(self, id_or_label: str) -> FlowNode:
        """Find a node by exact id, then by exact label.

        Labels are not unique by construction, so an ambiguous label is an
        error rather than a silent first-match — picking one arbitrarily would
        make a lab run irreproducible.
        """
        node = self._by_id.get(id_or_label)
        if node is not None:
            return node

        matches = self._by_label.get(id_or_label, [])
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            ids = ", ".join(m.id for m in matches)
            raise AmbiguousNodeError(
                f'Label "{id_or_label}" matches {len(matches)} nodes ({ids}). '
                "Pass a node id instead."
            )
        raise NodeNotFoundError(f'No node with id or label "{id_or_label}".')

    def outgoing(self, node_id: str) -> list[FlowEdge]:
        """Edges leaving `node_id`, in export order.

        Export order is the fan-out order for `--children graph`, so it must be
        stable — do not sort.
        """
        return [e for e in self.edges if e.source == node_id]

    def graph_children(self, node_id: str) -> list[FlowNode]:
        """Targets of every outgoing edge, deduped, in edge order.

        Several edges may converge on one target; each target runs at most
        once.
        """
        seen: set[str] = set()
        out: list[FlowNode] = []
        for edge in self.outgoing(node_id):
            if edge.target in seen:
                continue
            seen.add(edge.target)
            target = self._by_id.get(edge.target)
            if target is not None:
                out.append(target)
        return out

    def inline_children(self, child_node_ids: list[str]) -> list[FlowNode]:
        """Resolve `config.childNodeIds` against `nodes[]`.

        Inline child reasoning nodes ARE present in `nodes[]` — the canvas
        stores them as real nodes and derives the parent's `childNodeIds` at
        save time (dialog-flow-save.ts). Unknown ids are dropped, mirroring the
        `getById` miss in child-execution.ts.
        """
        out: list[FlowNode] = []
        for child_id in child_node_ids:
            node = self._by_id.get(child_id)
            if node is not None:
                out.append(node)
        return out


def load_flow(path: str | Path) -> Flow:
    p = Path(path)
    with p.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)
    return Flow(FlowExport.model_validate(raw), path=p)


__all__ = [
    "AmbiguousNodeError",
    "Flow",
    "NodeNotFoundError",
    "load_flow",
]
