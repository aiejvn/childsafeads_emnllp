"""The one tool exposed to the analysis loop.

SOURCE: apps/backend/src/file/rag-search/rag-search-config.ts
        apps/backend/src/file/rag-search/rag-search.service.ts
        apps/backend/src/file/semantic-file-search.tool.ts

RAG is a TOOL, not a pre-step. The model decides how many times to search and
when it has enough to write the analysis. Do not collapse this into a fixed
pre-fetch — the loop is the point.

Not ported: the LLM reranker (`RerankerService.filter`) and the same-case
collapse (`dedupeSameCaseHits`, which needs enriched neutral-citation
metadata). Both are simplifications; if analysis quality suffers, the reranker
is the first thing to add back.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from ..backend_client import BackendClient, ChunkHit
from ..llm import ToolSpec
from ..prompts.context_file_format import format_context_file_entry
from ..types import RagHit, VectorSearchConfig

SemanticScope = Literal["user", "public", "all"]

# SOURCE: semantic-file-search.tool.ts :: DEFAULT_RESULT_LIMIT
DEFAULT_RESULT_LIMIT = 5

TOOL_NAME = "rag_search"

# SOURCE: semantic-file-search.tool.ts :: SemanticFileSearchTool description.
# The trailing read-file sentence is dropped: node-lab exposes no read_file
# tool, so telling the model to call it would invite a hallucinated call.
TOOL_DESCRIPTION = f"""Search the legal knowledge base by meaning. The indexed corpus covers:
- Case law: court decisions, judgments, comparator cases, precedent, authorities
- Legislation: statutes, regulations, codified rules
- The user's own uploaded documents: prior contracts, filings, past work product, inspiration material

Call this tool whenever the task asks for cited authorities, supporting court decisions, comparator cases, statutory provisions, regulations, precedent, or any document the user may have uploaded. Matter facts already inlined in your context do NOT substitute for retrieved authorities — if the instructions reference "relevant court cases", "comparator decisions", "applicable statute", "precedent", or similar, you must call this tool.

Input:
- query: a natural-language description of what to find. Examples: "wrongful dismissal reasonable notice senior executive 20+ years service", "Bardal factors comparator cases older employee long service", "Employment Standards Act termination notice provisions", "past NDA agreements with mutual non-disclosure clauses".

Returns: a <RAG_Context> block listing up to {DEFAULT_RESULT_LIMIT} documents, each as `fileId=<id> name="<name>" score=<n>` with the best-matching snippet. Cite results by fileId. The snippet is one chunk only.

Search as many times as you need with different queries; documents already returned by an earlier search are omitted from later results and reported as a count, so a search that returns nothing new means you have exhausted that line of inquiry. Stop searching and write the analysis once you have enough.

Skip only when the task is purely about already-provided text (e.g. "summarize this paragraph") and requires no external authorities or comparator material."""


def derive_scope(
    document_scopes: list[str] | None,
) -> SemanticScope | None:
    """SOURCE: rag-search-config.ts :: deriveScope

    FAILS CLOSED: returns None when the list is undefined OR empty. Both mean
    "no scope was resolved" — the caller must treat None as "retrieval
    disabled" and skip searching. An undefined list must NEVER default to
    client+public; that would silently widen access to private documents the
    node was never configured to see.
    """
    if document_scopes is None:
        return None
    client = "client" in document_scopes
    library = "public" in document_scopes
    if not client and not library:
        return None
    if client and library:
        return "all"
    return "user" if client else "public"


def build_rag_options(
    vector_config: VectorSearchConfig | None,
    *,
    limit: int = DEFAULT_RESULT_LIMIT,
) -> dict[str, Any] | None:
    """SOURCE: rag-search-config.ts :: buildRagOptions

    Returns None on every path where a scope cannot be resolved, so the caller
    skips retrieval rather than running an unscoped (user-wide) search:

      * no per-node vector config          -> None
      * `documentScopes` undefined or `[]` -> None (see derive_scope)
    """
    if vector_config is None:
        return None
    scope = derive_scope(vector_config.document_scopes)
    if scope is None:
        return None
    return {
        "scope": scope,
        "limit": limit,
        "file_filter": _parse_filters(vector_config.filters),
    }


def _parse_filters(filters: Any) -> dict[str, Any] | None:
    """Pass through the node's Qdrant filter, dropping empties.

    `parseVectorSearchFilters` normalises a richer editor shape; node-lab
    forwards whatever the export carries and lets the backend validate it.
    """
    if not filters or not isinstance(filters, dict):
        return None
    cleaned = {k: v for k, v in filters.items() if v not in (None, [], {}, "")}
    return cleaned or None


@dataclass
class RagCallRecord:
    """One tool invocation, as it lands in the run transcript."""

    query: str
    hits: list[RagHit] = field(default_factory=list)
    #: fileIds this call found but withheld because an earlier call in the same
    #: analysis loop already returned them.
    suppressed_file_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "hits": [h.model_dump() for h in self.hits],
            "suppressedFileIds": self.suppressed_file_ids,
        }


class RagSearchTool:
    """Stateful for the lifetime of ONE analysis loop.

    Two distinct dedups, both required:

    * *Within* one call — best chunk per `fileId`, then score sort. The
      backend returns chunk-level hits and one file can produce many.
    * *Across* calls — `_seen_ids` holds every `fileId` already returned.
      Because the model drives the loop it will issue overlapping queries;
      without this the same document is re-fed on every call, burning context
      and skewing the analysis toward whatever the early queries matched.

    Suppressed hits are REPORTED in the tool result rather than silently
    dropped, so the model can tell a genuinely empty search from a fully
    deduped one and stop searching instead of rephrasing forever.
    """

    def __init__(
        self,
        *,
        backend: BackendClient,
        vector_config: VectorSearchConfig | None,
        limit: int = DEFAULT_RESULT_LIMIT,
        fixture: Path | None = None,
        on_progress: Callable[[str], None] | None = None,
    ) -> None:
        self._backend = backend
        self._options = build_rag_options(vector_config, limit=limit)
        self._limit = limit
        self._on_progress = on_progress or (lambda _msg: None)
        self._seen_ids: set[str] = set()
        self._names: dict[str, str] = {}
        self.calls: list[RagCallRecord] = []
        self._fixture = _load_fixture(fixture) if fixture else None

    @property
    def enabled(self) -> bool:
        """Whether the tool should be exposed at all.

        Mirrors `SemanticFileSearchTool.load` returning null: when
        `buildRagOptions` yields nothing, the agent must not see the tool.
        """
        return self._options is not None or self._fixture is not None

    def spec(self) -> ToolSpec:
        return ToolSpec(
            name=TOOL_NAME,
            description=TOOL_DESCRIPTION,
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural-language description of what to find.",
                    }
                },
                "required": ["query"],
                "additionalProperties": False,
            },
            execute=self._execute,
        )

    async def _execute(self, args: dict[str, Any]) -> str:
        query = (args.get("query") or "").strip()
        if not query:
            return "No query supplied."

        self._on_progress(f"Searching uploaded documents for: {query}")
        chunks = await self._fetch(query)
        deduped = self._best_chunk_per_file(chunks)

        fresh: list[RagHit] = []
        suppressed: list[str] = []
        for hit in deduped:
            if hit.file_id in self._seen_ids:
                suppressed.append(hit.file_id)
                continue
            self._seen_ids.add(hit.file_id)
            fresh.append(hit)

        await self._attach_names(fresh)
        self.calls.append(
            RagCallRecord(query=query, hits=fresh, suppressed_file_ids=suppressed)
        )

        if not fresh:
            if suppressed:
                self._on_progress(
                    f"{len(suppressed)} result(s), all previously retrieved."
                )
                return (
                    f"{len(suppressed)} result(s), all {len(suppressed)} already "
                    "retrieved by an earlier search — nothing new for this query. "
                    "Try a materially different angle, or stop searching and write "
                    "the analysis."
                )
            self._on_progress("No matching documents found.")
            return "No matching documents found in the user's library."

        entries = "\n".join(
            format_context_file_entry(
                file_id=hit.file_id,
                name=self._names.get(hit.file_id, hit.file_id),
                body=hit.snippet or "(no snippet available)",
                body_label="snippet",
                meta=f"score={hit.score:.3f}",
            )
            for hit in fresh
        )
        total = len(fresh) + len(suppressed)
        note = (
            f"\n({total} result(s), {len(suppressed)} already retrieved and omitted.)"
            if suppressed
            else ""
        )
        self._on_progress(
            f"Found {len(fresh)} document{'' if len(fresh) == 1 else 's'}."
        )
        return f"<RAG_Context>\n{entries}\n</RAG_Context>{note}"

    # -- internals --------------------------------------------------------

    async def _fetch(self, query: str) -> list[ChunkHit]:
        if self._fixture is not None:
            return self._fixture.get(query, self._fixture.get("*", []))
        assert self._options is not None  # guarded by `enabled`
        return await self._backend.search_files(query, **self._options)

    @staticmethod
    def _best_chunk_per_file(chunks: list[ChunkHit]) -> list[RagHit]:
        """Collapse chunk-level hits to one per file, keeping the best score."""
        best: dict[str, ChunkHit] = {}
        for chunk in chunks:
            current = best.get(chunk.file_id)
            if current is None or chunk.score > current.score:
                best[chunk.file_id] = chunk
        ordered = sorted(best.values(), key=lambda c: c.score, reverse=True)
        return [
            RagHit(file_id=c.file_id, name=c.file_id, score=c.score, snippet=c.chunk_text)
            for c in ordered
        ]

    async def _attach_names(self, hits: list[RagHit]) -> None:
        """`/files/search` returns no file name; fetch it once per fileId.

        A metadata miss is not fatal — the fileId is a usable label and the
        citation marker only ever carries the UUID.
        """
        for hit in hits:
            if hit.file_id in self._names:
                hit.name = self._names[hit.file_id]
                continue
            if self._fixture is not None:
                self._names[hit.file_id] = hit.name
                continue
            try:
                meta = await self._backend.get_file_metadata(hit.file_id)
                self._names[hit.file_id] = meta.name
            except Exception:  # noqa: BLE001 — cosmetic lookup only
                self._names[hit.file_id] = hit.file_id
            hit.name = self._names[hit.file_id]


def _load_fixture(path: Path) -> dict[str, list[ChunkHit]]:
    """Replay recorded hits for deterministic reruns.

    Format: `{"<query>": [{"fileId","chunkText","chunkIndex","score"}, ...]}`.
    A `"*"` key answers any query the fixture does not name.
    """
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return {
        query: [
            ChunkHit(
                file_id=item["fileId"],
                chunk_text=item.get("chunkText") or "",
                chunk_index=item.get("chunkIndex", 0),
                score=float(item.get("score", 0.0)),
            )
            for item in items
        ]
        for query, items in raw.items()
    }


__all__ = [
    "DEFAULT_RESULT_LIMIT",
    "TOOL_DESCRIPTION",
    "TOOL_NAME",
    "RagCallRecord",
    "RagSearchTool",
    "build_rag_options",
    "derive_scope",
]
