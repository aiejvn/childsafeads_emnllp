"""node-lab — a standalone harness for one OpenJustice reasoning node.

A deliberate distillation of `reasoning-node.runner.ts`, not a port of it:

    build analysis prompt from the node's config
      -> analysis (LLM tool loop; the model calls RAG until it has enough)
      -> self-reflection (optional)
      -> final answer(s)
      -> pass those answers to the children

See ../NODE_LAB_PLAN.md for what was deliberately left out and why.
"""

__version__ = "0.1.0"
