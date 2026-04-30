"""Structural tests for the v6 LangGraph orchestration layer.

These don't make Anthropic calls — they exercise graph compilation and
the conditional-edge router. End-to-end behaviour is verified by the
v5-equivalence smoke run captured in docs/example_runs/."""
from typing import get_type_hints

from attestloop.orchestration import (
    PipelineState,
    build_pipeline_graph,
    route_after_classify,
)
from attestloop.schemas import ClassifierOutput


def test_graph_builds_without_error():
    graph = build_pipeline_graph()
    assert graph is not None
    # CompiledStateGraph exposes the underlying graph for visualisation.
    drawable = graph.get_graph()
    nodes = set(drawable.nodes)
    expected = {
        "__start__",
        "__end__",
        "fetch",
        "classify",
        "extract",
        "map",
        "report",
        "out_of_scope",
    }
    assert expected.issubset(nodes), f"missing nodes: {expected - nodes}"


def test_graph_state_typed_correctly():
    """PipelineState should declare every field the nodes read from
    state. Catches the case where a future node author forgets to add
    a field to the TypedDict."""
    hints = get_type_hints(PipelineState)
    required_fields = {
        "url",
        "regulation_id",
        "framework_id",
        "run_dir",
        "run_id",
        "started_at",
        "regulation",
        "framework",
        "publication",
        "classification",
        "obligations",
        "mappings",
        "report_path",
    }
    missing = required_fields - hints.keys()
    assert not missing, f"PipelineState missing fields: {missing}"


def _stub_classifier_output(in_scope: bool) -> ClassifierOutput:
    return ClassifierOutput(
        in_scope=in_scope,
        category="regulation" if in_scope else "press_release",
        confidence=0.9,
        reasoning="(test stub)",
    )


def test_route_after_classify_in_scope():
    state: PipelineState = {"classification": _stub_classifier_output(True)}
    assert route_after_classify(state) == "extract"


def test_route_after_classify_out_of_scope():
    state: PipelineState = {"classification": _stub_classifier_output(False)}
    assert route_after_classify(state) == "out_of_scope"
