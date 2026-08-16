"""Step 4 — pass the answers to the children.

"Children" covers two distinct concepts the production runner treats
differently (lib/reasoning-node/child-execution.ts):

* **Inline children** (`config.childNodeIds`) — sub-reasoning steps executed
  recursively, in DFS batches.
* **Graph children** (`node.children`, derived from `edges[]`) — the next
  nodes reached by this node's outgoing edges.

The answers dict is the ONLY thing passed down. It replaces the ContextPool /
FactDictionary entirely; there is no shared mutable pool and no child cache
(recomputation is cheap and keeps the lab honest).
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from ..flow import Flow
from ..types import FlowNode, NodeType, PriorAnswer

# SOURCE: child-execution.ts :: CHILD_BATCH_SIZE
CHILD_BATCH_SIZE = 4

RunFn = Callable[[FlowNode, Mapping[str, PriorAnswer]], Awaitable[dict[str, Any]]]


def _answers_from(result: dict[str, Any]) -> dict[str, PriorAnswer]:
    """Extract the `{node_id: PriorAnswer}` a completed run contributes."""
    return {
        node_id: PriorAnswer.model_validate(entry)
        for node_id, entry in (result.get("answersOut") or {}).items()
    }


async def execute_inline_children(
    *,
    parent: FlowNode,
    flow: Flow,
    answers: Mapping[str, PriorAnswer],
    run_fn: RunFn,
) -> list[dict[str, Any]]:
    """Recursive `run()` over `config.childNodeIds`, in DFS batches of 4.

    Ordering semantics, ported deliberately: same-batch siblings all see the
    snapshot taken *before* their batch started, and each batch's answers are
    merged in before the next batch runs. That is the deterministic reading of
    production's shared `runPool` — there, same-batch siblings may or may not
    see each other's facts depending on scheduling; cross-batch ordering is
    guaranteed by the sequential batch loop either way.
    """
    config = parent.reasoning_config()
    children = flow.inline_children(config.child_node_ids)
    if not children:
        return []

    accumulated: dict[str, PriorAnswer] = dict(answers)
    results: list[dict[str, Any]] = []

    for start in range(0, len(children), CHILD_BATCH_SIZE):
        batch = children[start : start + CHILD_BATCH_SIZE]
        snapshot = dict(accumulated)
        batch_results = await asyncio.gather(
            *(run_fn(child, snapshot) for child in batch)
        )
        for result in batch_results:
            results.append(result)
            accumulated.update(_answers_from(result))

    return results


async def execute_graph_children(
    *,
    parent: FlowNode,
    flow: Flow,
    answers: Mapping[str, PriorAnswer],
    run_fn: RunFn,
) -> list[dict[str, Any]]:
    """Run EVERY node reached by an outgoing edge — not just the first.

    One hop only: graph children do not themselves expand. Fan-out follows
    `edges[]` order and each target runs at most once even when several edges
    converge on it (`Flow.graph_children` dedups).

    Non-reasoning targets are reported, not guessed at: start / fact / switch /
    outcome runners are deliberately not ported, and inventing their semantics
    would make a lab result look like a flow result.
    """
    results: list[dict[str, Any]] = []
    for target in flow.graph_children(parent.id):
        if target.type != NodeType.REASONING.value:
            results.append(
                {
                    "node": {
                        "id": target.id,
                        "label": target.label,
                        "type": target.type,
                        "config": target.data.config,
                    },
                    "skipped": "runner not ported",
                    "note": (
                        f"`{target.type}` nodes are out of node-lab's scope; only "
                        "reasoning runners are ported. Config is dumped above for "
                        "inspection."
                    ),
                }
            )
            continue
        results.append(await run_fn(target, answers))
    return results


__all__ = [
    "CHILD_BATCH_SIZE",
    "RunFn",
    "execute_graph_children",
    "execute_inline_children",
]
