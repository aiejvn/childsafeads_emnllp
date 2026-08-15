"""Scope derivation and the two dedups."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from node_lab.backend_client import BackendClient, ChunkHit
from node_lab.tools.rag_search import RagSearchTool, build_rag_options, derive_scope
from node_lab.types import VectorSearchConfig


@pytest.mark.parametrize(
    ("scopes", "expected"),
    [
        (None, None),  # undefined -> DISABLED, never a widened default
        ([], None),  # empty      -> DISABLED
        (["client"], "user"),
        (["public"], "public"),
        (["client", "public"], "all"),
        (["nonsense"], None),
    ],
)
def test_derive_scope_fails_closed(scopes, expected):
    assert derive_scope(scopes) == expected


def test_build_rag_options_requires_a_vector_config():
    assert build_rag_options(None) is None
    assert build_rag_options(VectorSearchConfig(enabled=True)) is None
    assert (
        build_rag_options(
            VectorSearchConfig(enabled=True, documentScopes=["client"])
        )["scope"]
        == "user"
    )


def _tool(tmp_path: Path, hits: list[dict]) -> RagSearchTool:
    fixture = tmp_path / "rag.json"
    fixture.write_text(json.dumps({"*": hits}), encoding="utf-8")
    return RagSearchTool(
        backend=BackendClient(base_url="http://unused", api_key="nap_unused"),
        vector_config=VectorSearchConfig(enabled=True, documentScopes=["client"]),
        fixture=fixture,
    )


def test_within_call_dedup_keeps_best_chunk_per_file(tmp_path):
    tool = _tool(
        tmp_path,
        [
            {"fileId": "f1", "chunkText": "low", "chunkIndex": 0, "score": 0.4},
            {"fileId": "f1", "chunkText": "high", "chunkIndex": 1, "score": 0.9},
            {"fileId": "f2", "chunkText": "mid", "chunkIndex": 0, "score": 0.6},
        ],
    )
    asyncio.run(tool.spec().execute({"query": "q"}))

    (call,) = tool.calls
    assert [h.file_id for h in call.hits] == ["f1", "f2"]  # score-sorted
    assert call.hits[0].snippet == "high"


def test_cross_call_dedup_suppresses_and_reports(tmp_path):
    tool = _tool(
        tmp_path,
        [
            {"fileId": "f1", "chunkText": "a", "chunkIndex": 0, "score": 0.9},
            {"fileId": "f2", "chunkText": "b", "chunkIndex": 0, "score": 0.6},
        ],
    )
    spec = tool.spec()
    first = asyncio.run(spec.execute({"query": "one"}))
    second = asyncio.run(spec.execute({"query": "two"}))

    assert "fileId=f1" in first and "fileId=f2" in first

    # No fileId appears in two ragCalls entries.
    returned = [h.file_id for call in tool.calls for h in call.hits]
    assert sorted(returned) == ["f1", "f2"]

    # A fully deduped call reports suppression rather than an empty result.
    assert tool.calls[1].hits == []
    assert sorted(tool.calls[1].suppressed_file_ids) == ["f1", "f2"]
    assert "already retrieved" in second
    assert "No matching documents" not in second


def test_partial_suppression_is_annotated(tmp_path):
    fixture = tmp_path / "rag.json"
    fixture.write_text(
        json.dumps(
            {
                "one": [{"fileId": "f1", "chunkText": "a", "chunkIndex": 0, "score": 0.9}],
                "two": [
                    {"fileId": "f1", "chunkText": "a", "chunkIndex": 0, "score": 0.9},
                    {"fileId": "f3", "chunkText": "c", "chunkIndex": 0, "score": 0.5},
                ],
            }
        ),
        encoding="utf-8",
    )
    tool = RagSearchTool(
        backend=BackendClient(base_url="http://unused", api_key="nap_unused"),
        vector_config=VectorSearchConfig(enabled=True, documentScopes=["client"]),
        fixture=fixture,
    )
    spec = tool.spec()
    asyncio.run(spec.execute({"query": "one"}))
    second = asyncio.run(spec.execute({"query": "two"}))

    assert "fileId=f3" in second
    assert "fileId=f1" not in second
    assert "1 already retrieved and omitted" in second


def test_tool_is_disabled_when_scope_unresolved(tmp_path):
    tool = RagSearchTool(
        backend=BackendClient(base_url="http://unused", api_key="nap_unused"),
        vector_config=VectorSearchConfig(enabled=True, documentScopes=[]),
    )
    assert tool.enabled is False


def test_empty_search_reads_differently_from_a_deduped_one(tmp_path):
    tool = _tool(tmp_path, [])
    out = asyncio.run(tool.spec().execute({"query": "q"}))
    assert "No matching documents" in out
    assert tool.calls[0].suppressed_file_ids == []


def test_best_chunk_helper_is_score_ordered():
    hits = RagSearchTool._best_chunk_per_file(
        [
            ChunkHit(file_id="a", chunk_text="", chunk_index=0, score=0.1),
            ChunkHit(file_id="b", chunk_text="", chunk_index=0, score=0.8),
        ]
    )
    assert [h.file_id for h in hits] == ["b", "a"]
