"""Inline recursion + the annotation context block.

The Worker Classification export has NO node with `childNodeIds` and none with
`annotations` (see test_answer_and_flow.test_fixture_coverage_gap...), so this
module runs against a hand-built fixture instead. `fixtures/
inline-children-flow.json` has a parent with five children — one more than
CHILD_BATCH_SIZE — so the batch boundary is actually exercised.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from node_lab.backend_client import BackendClient, ExcerptRecord
from node_lab.documents import DocumentResolver, ResolvedFile
from node_lab.flow import load_flow
from node_lab.reasoning.children import CHILD_BATCH_SIZE
from node_lab.reasoning.runner import RunDeps, RunOptions, run_node

from fakes import FakeLLM

FLOW_PATH = Path(__file__).resolve().parent / "fixtures/inline-children-flow.json"


class StubResolver(DocumentResolver):
    async def resolve_file(self, file_id: str) -> ResolvedFile:
        return ResolvedFile(
            file_id=file_id,
            name=f"{file_id}.pdf",
            text="document body text",
            origin="cache",
        )

    async def resolve_excerpt(self, excerpt_id, importance):
        from node_lab.types import AnnotationExcerpt

        return AnnotationExcerpt(
            id=excerpt_id,
            title="Pinned rule",
            text="verbatim excerpt text",
            source_type=importance,
            pinpoint="para. 17",
        )


def _deps(tmp_path: Path, llm: FakeLLM, **overrides):
    flow = load_flow(FLOW_PATH)
    backend = BackendClient(base_url="http://unused", api_key="nap_unused")
    deps = RunDeps(
        flow=flow,
        llm=llm,
        backend=backend,
        resolver=StubResolver(backend=backend, cache_dir=tmp_path),
        options=RunOptions(
            model="claude-sonnet-4-6", cache_dir=tmp_path, **overrides
        ),
    )
    return flow, deps


def test_every_inline_child_runs_and_sees_the_parent_answer(tmp_path):
    llm = FakeLLM()
    flow, deps = _deps(tmp_path, llm, rag=False, reflect=False, children="inline")
    transcript = asyncio.run(run_node(flow.by_id("parent"), {}, deps))

    ids = [c["node"]["id"] for c in transcript["childResults"]]
    assert ids == [f"child-{i}" for i in range(5)]
    assert len(ids) > CHILD_BATCH_SIZE  # the batch boundary is crossed

    for child in transcript["childResults"]:
        prompt = child["prompts"]["analysis"]
        assert "Fact: Parent" in prompt
        assert "Assessment for Parent: 2 - No" in prompt


def test_second_batch_sees_first_batch_answers(tmp_path):
    llm = FakeLLM()
    flow, deps = _deps(tmp_path, llm, rag=False, reflect=False, children="inline")
    transcript = asyncio.run(run_node(flow.by_id("parent"), {}, deps))

    first_batch = transcript["childResults"][:CHILD_BATCH_SIZE]
    last = transcript["childResults"][CHILD_BATCH_SIZE]

    # Same-batch siblings see the pre-batch snapshot only...
    for child in first_batch:
        assert "Fact: Child 0" not in child["prompts"]["analysis"]
    # ...and the next batch sees every answer the previous batch produced.
    for i in range(CHILD_BATCH_SIZE):
        assert f"Fact: Child {i}" in last["prompts"]["analysis"]


def test_child_token_usage_rolls_up_into_the_parent(tmp_path):
    llm = FakeLLM()
    flow, deps = _deps(tmp_path, llm, rag=False, reflect=False, children="inline")
    transcript = asyncio.run(run_node(flow.by_id("parent"), {}, deps))

    child_total = sum(
        c["tokenUsage"]["output_tokens"] for c in transcript["childResults"]
    )
    assert transcript["tokenUsage"]["output_tokens"] > child_total


def test_annotation_context_block_reaches_the_analysis_prompt(tmp_path):
    llm = FakeLLM()
    flow, deps = _deps(tmp_path, llm, rag=False, reflect=False, children="none")
    transcript = asyncio.run(run_node(flow.by_id("annotated"), {}, deps))

    prompt = transcript["prompts"]["analysis"]
    assert "<Annotated_Context>" in prompt
    assert '- fileId=file-1 name="file-1.pdf" importance=authoritative' in prompt
    assert "summary: document body text" in prompt
    assert 'excerptId=excerpt-1 title="Pinned rule"' in prompt
    assert "pinpoint: para. 17" in prompt
    assert transcript["annotationFiles"] == ["file-1"]
    # The block sits between <Conversation_Facts> and <SubAgent_Answers>.
    assert prompt.index("</Conversation_Facts>") < prompt.index("<Annotated_Context>")
    assert prompt.index("</Annotated_Context>") < prompt.index("<SubAgent_Answers>")


def test_nodes_without_annotations_get_no_block(tmp_path):
    llm = FakeLLM()
    flow, deps = _deps(tmp_path, llm, rag=False, reflect=False, children="none")
    transcript = asyncio.run(run_node(flow.by_id("child-0"), {}, deps))
    assert "<Annotated_Context>" not in transcript["prompts"]["analysis"]
