"""Shared reasoning-discipline prompt fragments.

SOURCE: apps/backend/src/node-execution/runners/shared/reasoning-discipline.prompt.ts

Copied VERBATIM. `parity/check_prompt_drift.py` diffs these against the TS on
demand — keep them byte-for-byte and never reflow.

`COMPARING_SOURCES_TABULAR` is the outcome-synthesis/layout variant and is NOT
imported by the reasoning-analysis prompt (which carries its own variant adding
file-vs-excerpt sourcing guidance). It is not ported.
"""

# SOURCE: reasoning-discipline.prompt.ts :: SYNTHESIS_FIDELITY
SYNTHESIS_FIDELITY = """### Synthesis fidelity
Any proposition more general than what a single cited source states — claims of the form "X only matters when Y", "the trend is Z", aggregations across multiple sources, or any higher-order rule extracted from a body of cited material — must be either (a) attributed to a source that asserts it expressly, or (b) framed openly as your inference with the chain of derivation shown ("Taken together, A holds … and B holds …, from which it follows that …"). Do not assert a synthesized rule and attach citations as if those sources stated the rule themselves. Every assertion has either a supporting citation or a visible derivation; never both absent."""

# SOURCE: reasoning-discipline.prompt.ts :: EVALUATIVE_ANCHORS
EVALUATIVE_ANCHORS = """### Evaluative anchors
Before applying any qualitative scale (mid-range, high, low, strong, weak, mild, severe, material, significant, substantial, modest, etc.), define the scale's endpoints with concrete reference points drawn from the cited material or the facts, and locate the present case relative to those endpoints. If the scale cannot be defined, do not use the shorthand — substitute a quantitative formulation, a comparative ("higher than X, lower than Y"), or a direct description of the underlying facts. Bare qualitative labels with no anchor are forbidden."""

__all__ = ["EVALUATIVE_ANCHORS", "SYNTHESIS_FIDELITY"]
