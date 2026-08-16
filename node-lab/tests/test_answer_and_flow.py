"""Prediction parsing / ranges, and flow loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from node_lab.flow import AmbiguousNodeError, NodeNotFoundError, load_flow
from node_lab.reasoning.answer import build_prediction_range, parse_prediction_value
from node_lab.types import FactDataType, PredictionCandidate

FLOW_PATH = (
    Path(__file__).resolve().parents[2]
    / "Worker_Classification_Annotation_Flow__Imported_-dialog-flow.json"
)


@pytest.mark.parametrize("sentinel", ["", "null", "NULL"])
def test_null_sentinels(sentinel):
    assert parse_prediction_value(sentinel, FactDataType.TEXT) is None


def test_numeric_coercion_and_fallback():
    assert parse_prediction_value("24", FactDataType.NUMBER) == 24
    assert parse_prediction_value("0.75", FactDataType.PERCENTAGE) == 0.75
    assert parse_prediction_value("not a number", FactDataType.NUMBER) == "not a number"


def test_boolean_coercion():
    assert parse_prediction_value("TRUE", FactDataType.BOOLEAN) is True
    assert parse_prediction_value(" false ", FactDataType.BOOLEAN) is False
    assert parse_prediction_value("maybe", FactDataType.BOOLEAN) == "maybe"


def test_custom_enum_values_pass_through_except_the_null_sentinel():
    # "null" is a legitimate enum member in the Worker Classification flow, but
    # the sentinel check runs first — exactly as in the TS. The raw string
    # stays available on the candidate.
    assert parse_prediction_value("2 - No", FactDataType.CUSTOM) == "2 - No"
    assert parse_prediction_value("null", FactDataType.CUSTOM) is None


def test_prediction_range_is_number_only_and_needs_two_distinct_values():
    two = [
        PredictionCandidate(prediction="12", probability=0.6),
        PredictionCandidate(prediction="18", probability=0.4),
    ]
    assert build_prediction_range(two, FactDataType.NUMBER) == {"min": 12, "max": 18}
    assert build_prediction_range(two, FactDataType.TEXT) is None
    assert build_prediction_range(two[:1], FactDataType.NUMBER) is None
    same = [
        PredictionCandidate(prediction="12", probability=0.6),
        PredictionCandidate(prediction="12", probability=0.4),
    ]
    assert build_prediction_range(same, FactDataType.NUMBER) is None


def test_flow_counts_match_the_export():
    flow = load_flow(FLOW_PATH)
    assert len(flow.nodes) == 33
    assert len(flow.edges) == 32
    by_type: dict[str, int] = {}
    for node in flow.nodes:
        by_type[node.type] = by_type.get(node.type, 0) + 1
    assert by_type == {"reasoning": 30, "start": 1, "fact": 1, "outcome": 1}


def test_resolution_by_id_and_label():
    flow = load_flow(FLOW_PATH)
    by_label = flow.resolve("Tri-lateral Relationship")
    assert flow.resolve(by_label.id) is by_label
    with pytest.raises(NodeNotFoundError):
        flow.resolve("no such node")


def test_ambiguous_labels_are_an_error_not_a_first_match():
    flow = load_flow(FLOW_PATH)
    target = flow.resolve("Tri-lateral Relationship")
    clone = target.model_copy(update={"id": "clone"})
    flow.export.nodes.append(clone)
    reloaded = type(flow)(flow.export)
    with pytest.raises(AmbiguousNodeError):
        reloaded.resolve("Tri-lateral Relationship")


def test_fixture_coverage_gap_is_still_the_documented_one():
    """Guards the plan's fixture note: 0 child-bearing, 0 annotated, 30 RAG-on."""
    flow = load_flow(FLOW_PATH)
    reasoning = [n for n in flow.nodes if n.type == "reasoning"]
    configs = [n.reasoning_config() for n in reasoning]
    assert sum(1 for c in configs if c.child_node_ids) == 0
    assert sum(1 for c in configs if c.annotations) == 0
    assert sum(1 for c in configs if c.vector_search_config and c.vector_search_config.enabled) == 30
