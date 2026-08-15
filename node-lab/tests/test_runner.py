"""End-to-end shape of the four-step node, with a scripted LLM."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from node_lab.backend_client import BackendClient
from node_lab.documents import DocumentResolver
from node_lab.flow import load_flow
from node_lab.reasoning.runner import RunDeps, RunOptions, run_node
from node_lab.types import FactDataType, PredictionCandidate

from fakes import FakeLLM

FLOW_PATH = (
    Path(__file__).resolve().parents[2]
    / "Worker_Classification_Annotation_Flow__Imported_-dialog-flow.json"
)
TARGET_NODE = "45183b44-86cc-4fd0-b425-4769f07dbc37"  # Tri-lateral Relationship


def _deps(tmp_path: Path, llm: FakeLLM, **option_overrides):
    flow = load_flow(FLOW_PATH)
    backend = BackendClient(base_url="http://unused", api_key="nap_unused")
    options = RunOptions(
        model="claude-sonnet-4-6",
        cache_dir=tmp_path / "cache",
        **option_overrides,
    )
    deps = RunDeps(
        flow=flow,
        llm=llm,
        backend=backend,
        resolver=DocumentResolver(backend=backend, cache_dir=tmp_path / "cache"),
        options=options,
    )
    return flow, deps


def _rag_fixture(tmp_path: Path) -> Path:
    path = tmp_path / "rag.json"
    path.write_text(
        json.dumps(
            {
                "*": [
                    {"fileId": "f1", "chunkText": "a", "chunkIndex": 0, "score": 0.9},
                    {"fileId": "f2", "chunkText": "b", "chunkIndex": 0, "score": 0.5},
                ]
            }
        ),
        encoding="utf-8",
    )
    return path


def test_no_rag_run_produces_an_enum_answer(tmp_path):
    llm = FakeLLM()
    flow, deps = _deps(tmp_path, llm, rag=False, reflect=False, children="none")
    node = flow.by_id(TARGET_NODE)
    transcript = asyncio.run(run_node(node, {}, deps))

    enum_values = node.reasoning_config().custom_enum_values
    assert transcript["answers"][0]["prediction"] in enum_values
    assert transcript["tokenUsage"]["input_tokens"] > 0
    assert transcript["tokenUsage"]["output_tokens"] > 0
    assert transcript["analysis"]["toolsOffered"] == []
    assert transcript["reflection"] is None
    assert transcript["ragCalls"] == []


def test_rag_tool_is_offered_and_loop_stays_under_the_cap(tmp_path):
    llm = FakeLLM(rag_queries=["first", "second"])
    flow, deps = _deps(
        tmp_path,
        llm,
        rag=True,
        reflect=False,
        children="none",
        rag_fixture=_rag_fixture(tmp_path),
    )
    transcript = asyncio.run(run_node(flow.by_id(TARGET_NODE), {}, deps))

    assert transcript["analysis"]["toolsOffered"] == ["rag_search"]
    assert len(transcript["ragCalls"]) == 2
    # Step budget is 10 when the analysis call carries a tool (client.ts:105).
    assert transcript["analysis"]["steps"] < 10
    assert transcript["analysis"]["hitStepCap"] is False

    # No fileId appears in two ragCalls entries.
    seen = [h["file_id"] for call in transcript["ragCalls"] for h in call["hits"]]
    assert len(seen) == len(set(seen))
    assert transcript["ragCalls"][1]["suppressedFileIds"] == ["f1", "f2"]


def test_reflection_revision_feeds_the_answer_step(tmp_path):
    llm = FakeLLM(
        reflection={
            "findings": ["fixed a range"],
            "revisedText": "## Facts\nrevised\n\n## Analysis\nrevised",
            "clean": False,
        }
    )
    flow, deps = _deps(tmp_path, llm, rag=False, reflect=True, children="none")
    transcript = asyncio.run(run_node(flow.by_id(TARGET_NODE), {}, deps))

    assert transcript["reflection"]["revised"] is True
    assert transcript["reflection"]["findings"] == ["fixed a range", "fixed a range"]
    # Both versions land in the transcript; the revised one reaches prediction.
    assert transcript["analysis"]["rationale"] != transcript["reflection"]["text"]
    answer_prompt = next(
        c["prompt"] for c in llm.calls if c["schema"] == "reasoning_predictions"
    )
    assert "revised" in answer_prompt


def test_graph_children_run_every_outgoing_target_with_the_parent_answer(tmp_path):
    llm = FakeLLM()
    flow, deps = _deps(tmp_path, llm, rag=False, reflect=False, children="graph")
    node = flow.by_id(TARGET_NODE)
    transcript = asyncio.run(run_node(node, {}, deps))

    targets = [t.id for t in flow.graph_children(TARGET_NODE)]
    assert [c["node"]["id"] for c in transcript["childResults"]] == targets

    child = transcript["childResults"][0]
    assert "2 - No" in child["prompts"]["analysis"]
    assert "Tri-lateral Relationship" in child["prompts"]["analysis"]
    # One hop only.
    assert child["childResults"] == []


def test_non_reasoning_graph_targets_stop_with_a_notice(tmp_path):
    llm = FakeLLM()
    flow, deps = _deps(tmp_path, llm, rag=False, reflect=False, children="graph")
    # The fact node "Upload Case Document" feeds the target node; run the start
    # node's successor chain from a reasoning node that points at the outcome.
    outcome = next(n for n in flow.nodes if n.type == "outcome")
    parent = next(
        n
        for n in flow.nodes
        if n.type == "reasoning"
        and any(e.target == outcome.id for e in flow.outgoing(n.id))
    )
    transcript = asyncio.run(run_node(parent, {}, deps))

    skipped = [c for c in transcript["childResults"] if c.get("skipped")]
    assert skipped and skipped[0]["skipped"] == "runner not ported"
    assert skipped[0]["node"]["type"] == "outcome"


def test_converging_edges_run_a_target_only_once(tmp_path):
    flow = load_flow(FLOW_PATH)
    node = flow.by_id(TARGET_NODE)
    duplicate = flow.edges[0].model_copy(update={"id": "dupe"})
    flow.export.edges.append(duplicate)
    assert len(flow.outgoing(TARGET_NODE)) == 2
    assert len(flow.graph_children(TARGET_NODE)) == 1
    assert node is not None


def test_children_none_skips_expansion(tmp_path):
    llm = FakeLLM()
    flow, deps = _deps(tmp_path, llm, rag=False, reflect=False, children="none")
    transcript = asyncio.run(run_node(flow.by_id(TARGET_NODE), {}, deps))
    assert transcript["childResults"] == []


def test_prior_answers_reach_the_analysis_prompt(tmp_path):
    from node_lab.types import PriorAnswer

    llm = FakeLLM()
    flow, deps = _deps(tmp_path, llm, rag=False, reflect=False, children="none")
    prior = {
        "n1": PriorAnswer(label="Earlier finding", prediction="1 - Yes", rationale="why")
    }
    transcript = asyncio.run(run_node(flow.by_id(TARGET_NODE), prior, deps))

    prompt = transcript["prompts"]["analysis"]
    assert "Fact: Earlier finding" in prompt
    assert "Assessment for Earlier finding: 1 - Yes" in prompt
    assert "Rationale: why" in prompt


def test_answer_model_defaults_to_the_utility_model(tmp_path):
    llm = FakeLLM()
    flow, deps = _deps(tmp_path, llm, rag=False, reflect=False, children="none")
    asyncio.run(run_node(flow.by_id(TARGET_NODE), {}, deps))

    analysis_call = next(c for c in llm.calls if c["schema"] == "reasoning_rationale")
    answer_call = next(c for c in llm.calls if c["schema"] == "reasoning_predictions")
    assert analysis_call["model"] == "claude-sonnet-4-6"
    assert answer_call["model"] == "gpt-5.4-nano"


def test_analysis_system_prompt_carries_the_cache_breakpoint(tmp_path):
    llm = FakeLLM()
    flow, deps = _deps(tmp_path, llm, rag=False, reflect=False, children="none")
    asyncio.run(run_node(flow.by_id(TARGET_NODE), {}, deps))

    analysis_call = next(c for c in llm.calls if c["schema"] == "reasoning_rationale")
    assert analysis_call["system"].cached is True
