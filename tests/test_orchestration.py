"""Structural tests for the v6 LangGraph orchestration layer.

These don't make Anthropic calls — they exercise graph compilation and
the conditional-edge router. End-to-end behaviour is verified by the
v5-equivalence smoke run captured in docs/example_runs/."""
from typing import get_type_hints
from unittest.mock import patch

import pytest

from attestloop.agents.critic import review_mappings
from attestloop.orchestration import (
    PipelineState,
    build_pipeline_graph,
    route_after_classify,
)
from attestloop.registry import get_framework
from attestloop.schemas import (
    ClassifierOutput,
    ControlMapping,
    CriticDecision,
    CriticOutput,
    Obligation,
)


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
        "critic_decisions",
        "report_path",
    }
    missing = required_fields - hints.keys()
    assert not missing, f"PipelineState missing fields: {missing}"


def test_pipeline_state_includes_critic_decisions():
    hints = get_type_hints(PipelineState)
    assert "critic_decisions" in hints


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


# ─────────────────────────── Critic tests ───────────────────────────

def _obl(oid: str = "EUAIA-OBL-001") -> Obligation:
    return Obligation(
        id=oid,
        source_paragraph="Article 5(1)(a)",
        requirement_text="Providers shall not place on the market.",
        scope="Providers",
        deadline=None,
        evidence_required=None,
    )


def _mapping(oid: str, control_id: str, conf: float) -> ControlMapping:
    return ControlMapping(
        obligation_id=oid,
        control_id=control_id,
        confidence=conf,
        reasoning="(test)",
    )


def test_critic_node_skips_high_confidence_obligations(tmp_path):
    """Every mapping >= 0.80 → no Critic review needed → zero LLM calls."""
    framework = get_framework("nist_ai_rmf")
    obligations = [_obl("EUAIA-OBL-001"), _obl("EUAIA-OBL-002")]
    mappings = [
        _mapping("EUAIA-OBL-001", "GOVERN-1.1", 0.85),
        _mapping("EUAIA-OBL-002", "MAP-1.1", 0.92),
    ]
    with patch("attestloop.agents.critic.call_with_logging") as mock_call:
        result = review_mappings(obligations, mappings, framework, tmp_path)
        assert mock_call.call_count == 0
        assert result.decisions == []


def test_critic_node_reviews_low_confidence_obligations(tmp_path):
    """Mappings below 0.80 trigger a Critic call per obligation; high-
    confidence ones are skipped. Empty mappings (framework gaps) are
    also skipped — those belong in the unmapped section, not the
    Critic's queue."""
    framework = get_framework("nist_ai_rmf")
    obligations = [
        _obl("EUAIA-OBL-001"),  # one low mapping → reviewed
        _obl("EUAIA-OBL-002"),  # all high → skipped
        _obl("EUAIA-OBL-003"),  # no mappings (framework gap) → skipped
    ]
    mappings = [
        _mapping("EUAIA-OBL-001", "GOVERN-1.1", 0.78),
        _mapping("EUAIA-OBL-002", "MAP-1.1", 0.92),
    ]

    fake_response = CriticOutput(
        decisions=[
            CriticDecision(
                obligation_id="EUAIA-OBL-001",
                decision="confirm",
                reasoning="defensible catch-all on a procedural duty",
                confidence=0.85,
                reviewed_mappings=["GOVERN-1.1"],
            )
        ]
    )
    with patch(
        "attestloop.agents.critic.call_with_logging",
        return_value=fake_response,
    ) as mock_call:
        result = review_mappings(obligations, mappings, framework, tmp_path)
        assert mock_call.call_count == 1
        assert len(result.decisions) == 1
        assert result.decisions[0].obligation_id == "EUAIA-OBL-001"
        assert result.decisions[0].decision == "confirm"


def test_critic_decision_schema():
    """CriticDecision validates the two allowed Literal values and
    rejects anything else."""
    confirm = CriticDecision(
        obligation_id="EUAIA-OBL-001",
        decision="confirm",
        reasoning="ok",
        confidence=0.9,
        reviewed_mappings=["GOVERN-1.1"],
    )
    assert confirm.decision == "confirm"

    flag = CriticDecision(
        obligation_id="EUAIA-OBL-001",
        decision="flag_for_review",
        reasoning="ok",
        confidence=0.85,
        reviewed_mappings=["GOVERN-1.1", "MANAGE-1.1"],
    )
    assert flag.decision == "flag_for_review"

    with pytest.raises(Exception):
        CriticDecision(
            obligation_id="EUAIA-OBL-001",
            decision="auto_replace",
            reasoning="not allowed",
            confidence=0.9,
            reviewed_mappings=[],
        )
