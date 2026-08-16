# node-lab

Run **one OpenJustice reasoning node** (plus its children) against raw LLM APIs,
driven by a dialog-flow export JSON. No NestJS, no Postgres, no Qdrant, no blob
storage, no execution loop.

This is a **deliberate distillation** of `reasoning-node.runner.ts`, not a port
of it. The whole node is four steps:

```text
build analysis prompt from the node's config
  → analysis (LLM tool loop; the model calls RAG as many times as it wants,
              then writes the analysis when it judges it has enough)
  → self-reflection (optional)
  → final answer(s)
  → pass those answers to the children
```

See `../../NODE_LAB_PLAN.md` for what was deliberately left out and why. Do not
reintroduce context curation, requirement extraction, sub-agent fan-out,
citation repair, the audit trail, or the context pool without asking.

## Quick start

```bash
cd scripts/node-lab
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

.venv/bin/python -m node_lab list --flow ../Worker_Classification_Annotation_Flow__Imported_-dialog-flow.json

# Phase 1: no documents, no backend, no network beyond the LLM APIs.
.venv/bin/python -m node_lab run \
  --flow ../Worker_Classification_Annotation_Flow__Imported_-dialog-flow.json \
  --node "Tri-lateral Relationship" \
  --no-rag --no-reflect --children none
```

The transcript lands in `out/<timestamp>-<nodeId>.json`.

## Environment

| Variable | Needed for |
|---|---|
| `ANTHROPIC_API_KEY` | any `claude-*` model |
| `OPENAI_API_KEY` | any `gpt-*` model — including the default answer model |
| `NODE_LAB_BACKEND_URL` | RAG + document resolution |
| `NODE_LAB_API_KEY` | same; a `nap_` bearer key (`HybridAuthGuard` accepts it) |

A `.env` in this directory is loaded automatically when `python-dotenv` is
installed. **The default `--answer-model` is `gpt-5.4-nano`** (mirroring
`UTILITY_MODEL`), so a Claude-only run still needs `OPENAI_API_KEY` — or pass
`--answer-model claude-haiku-4-5`.

## CLI

```text
python -m node_lab run \
  --flow <export.json> \
  --node "<label or id>" \
  --message "..." \                  # repeatable matter facts
  --model claude-sonnet-4-6 \
  --answer-model gpt-5.4-nano \
  --children inline|graph|both|none \
  --answers fixtures/answers.json \  # optional prior answers
  --no-rag --no-reflect \
  --rag-fixture fixtures/rag.json \  # replay recorded hits
  --text-dir documents/ \            # local <fileId>.txt overrides
  --out out/

python -m node_lab list --flow <export.json>
python -m node_lab check-prompts
```

`--answers` takes either `{id: {label, prediction, rationale?}}` or the
shorthand `{id: "prediction"}`.

`--rag-fixture` takes `{"<query>": [{fileId, chunkText, chunkIndex, score}]}`;
a `"*"` key answers any query the fixture does not name.

## Children

Two distinct concepts, as in production:

* **Inline** (`config.childNodeIds`) — recursive, in DFS batches of 4. Each
  batch sees the answers of every previous batch; same-batch siblings see only
  the pre-batch snapshot.
* **Graph** (`edges[]`) — **every** node reached by an outgoing edge, in edge
  order, each target at most once, **one hop only**. Non-reasoning targets are
  reported with a "runner not ported" notice rather than guessed at.

The answers dict (`{node_id: {label, prediction, rationale}}`) is the only
thing passed down. It replaces the ContextPool / FactDictionary entirely and
renders into the child's `<Conversation_Facts>`.

## Parity

Prompt **constants** — one command:

```bash
.venv/bin/python -m node_lab check-prompts
```

Prompt **builders** (the assembled string, which is what actually reaches the
model) — two commands, because the TS side needs Node:

```bash
cd ../../apps/backend
node_modules/.bin/ts-node -T \
  --compiler-options '{"module":"commonjs","moduleResolution":"node","experimentalDecorators":true,"emitDecoratorMetadata":true,"target":"es2023","esModuleInterop":true}' \
  -r tsconfig-paths/register \
  ../../scripts/node-lab/parity/dump_ts_prompts.ts \
  --flow ../../scripts/Worker_Classification_Annotation_Flow__Imported_-dialog-flow.json \
  --node "Tri-lateral Relationship" --out /tmp/ts-prompts

cd ../../scripts/node-lab
.venv/bin/python -m node_lab.parity.check_builder_parity \
  --flow ../Worker_Classification_Annotation_Flow__Imported_-dialog-flow.json \
  --node "Tri-lateral Relationship" --ts-dir /tmp/ts-prompts
```

Both currently report zero drift.

## Tests

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest tests -q
```

They run the whole pipeline against a scripted LLM — no network. Inline
children and annotations have no fixture in the Worker Classification flow
(0 nodes with `childNodeIds`, 0 with `annotations`), so
`tests/fixtures/inline-children-flow.json` is hand-built for those.

## Known infidelities

Read these before treating a lab result as a production result.

1. **The pipeline is distilled, not reproduced.** Analysis text is comparable;
   anything depending on curation, sub-agent fan-out, citations, or the fact
   dictionary is not.
2. **`read_file` is not ported.** `rag_search` is the only tool. Annotation
   files therefore carry the **full parsed document text** in the
   `<Annotated_Context>` `summary:` slot, where production puts the short
   ingest-time metadata summary and lets the model fetch text on demand. The
   block's "call read_file with the fileId" sentence is stale here; it is kept
   verbatim so the prompt stays diffable against the TS.
3. **The annotation block is injected into the analysis prompt.** Production
   reaches `<Annotated_Context>` through the sub-agent prompt, which is gone.
   Without this the annotation sources would never reach the model. This is the
   one place `build_analysis_message` diverges from `buildAnalysisMessage`, and
   only for nodes that actually have annotations — the no-annotation case is
   byte-identical (verified).
4. **`<SubAgent_Answers>` always renders its own empty-input fallback.** The
   builder is byte-faithful; the fan-out that would fill it is gone.
5. **The RAG reranker and same-case collapse are not ported.** The reranker is
   the first thing to add back if analysis quality suffers.
6. **Per-requirement annotation scoping is not ported**
   (`scopeAnnotationsToParagraphs`) — it exists to give each sub-agent its own
   slice. The single analysis call gets every annotation source.
7. **PDF text differs.** `pypdf` is not byte-identical to the Node `pdf-parse`
   path. `--text-dir` is the escape hatch.
8. **`--message` has no production analogue.** The conversation layer is not
   ported, so messages are injected as prior answers labelled "User message".
9. **`scripts/` is gitignored repo-wide** (root `.gitignore:106`). This
   directory is untracked as-is; commit it with `git add -f scripts/node-lab`,
   or add `!scripts/node-lab/` to the root `.gitignore`.

## Layout

```text
node_lab/
  cli.py             argparse entry point
  flow.py            DF export loader → node index + outgoing edges
  types.py           pydantic mirrors of node config + results
  llm.py             generate_object / generate_text over Anthropic + OpenAI
  schemas.py         the three structured-output JSON Schemas
  backend_client.py  httpx client (RAG + documents)
  documents.py       fileId → parsed text (override → cache → backend)
  prompts/           verbatim prompt copies, one module per .prompts.ts
  tools/rag_search.py   the one tool exposed to the analysis loop
  reasoning/         analysis → reflect → answer → children, plus runner.py
  parity/            drift checks against the TS sources
parity/dump_ts_prompts.ts   the TS half of the builder parity check
```
