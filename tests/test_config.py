"""Tests for the v6 task 5 PipelineConfig dataclass and its effect on
graph compilation. Compilation-time tests only — no Anthropic calls."""
import asyncio
from unittest.mock import patch

from attestloop.agents import mapper as mapper_module
from attestloop.agents.mapper import _map_to_controls_async
from attestloop.config import (
    DEFAULT,
    V5_EQUIVALENT,
    V6_CANONICAL,
    PipelineConfig,
)
from attestloop.orchestration import build_pipeline_graph
from attestloop.registry import get_framework
from attestloop.schemas import ControlMapping, Obligation


def test_default_is_v6_canonical():
    assert DEFAULT is V6_CANONICAL


def test_v5_equivalent_disables_orchestration():
    assert V5_EQUIVALENT.mapper_concurrency == 1
    assert V5_EQUIVALENT.enable_critic is False
    assert V5_EQUIVALENT.enable_clarifier_routing is False


def test_v6_canonical_enables_orchestration():
    assert V6_CANONICAL.mapper_concurrency == 8
    assert V6_CANONICAL.enable_critic is True
    assert V6_CANONICAL.enable_clarifier_routing is True


def test_v5_equivalent_config_skips_critic():
    """Building the graph with V5_EQUIVALENT must omit the Critic
    node entirely — the v5 baseline did not have a second-pass
    reviewer."""
    graph = build_pipeline_graph(V5_EQUIVALENT).get_graph()
    nodes = set(graph.nodes)
    assert "critic" not in nodes
    assert "clarify" not in nodes
    assert "review_queue" not in nodes
    assert {"fetch", "classify", "extract", "map", "report", "out_of_scope"}.issubset(
        nodes
    )


def test_v6_canonical_config_includes_critic():
    """Building the graph with V6_CANONICAL must include all v6
    orchestration nodes — Critic, Clarifier, review_queue."""
    graph = build_pipeline_graph(V6_CANONICAL).get_graph()
    nodes = set(graph.nodes)
    assert "critic" in nodes
    assert "clarify" in nodes
    assert "review_queue" in nodes


def _obl(suffix: str) -> Obligation:
    return Obligation(
        id=f"EUAIA-OBL-{suffix}",
        source_paragraph="Article 5",
        requirement_text=f"Requirement {suffix}",
        scope="Providers",
        deadline=None,
        evidence_required=None,
    )


def test_v5_equivalent_uses_serial_mapper(tmp_path):
    """With mapper_concurrency=1 the semaphore is never contended:
    max_in_flight stays at 1 even with multiple obligations and
    overlapping fake-call delays. Confirms the config flag is wired
    through the async fan-out."""
    framework = get_framework("nist_ai_rmf")
    obligations = [_obl(f"{i:03d}") for i in range(1, 11)]

    state = {"in_flight": 0, "max_in_flight": 0}
    state_lock = asyncio.Lock()

    async def fake_call(obligation, *args, **kwargs):
        async with state_lock:
            state["in_flight"] += 1
            state["max_in_flight"] = max(state["max_in_flight"], state["in_flight"])
        await asyncio.sleep(0.01)
        async with state_lock:
            state["in_flight"] -= 1
        return [
            ControlMapping(
                obligation_id=obligation.id,
                control_id="GOVERN-1.1",
                confidence=0.85,
                reasoning="(synthetic)",
            )
        ]

    with patch.object(mapper_module, "_call_mapper_async", fake_call):
        asyncio.run(
            _map_to_controls_async(
                obligations,
                framework,
                "nist_ai_rmf",
                tmp_path,
                mapper_concurrency=V5_EQUIVALENT.mapper_concurrency,
            )
        )

    assert state["max_in_flight"] == 1, (
        f"v5-equivalent mapper_concurrency=1 must serialise calls; "
        f"observed max_in_flight={state['max_in_flight']}"
    )


def test_pipeline_config_is_frozen():
    """Frozen dataclass — accidental mutation must raise rather than
    silently change a config that's been passed into a graph."""
    cfg = PipelineConfig()
    try:
        cfg.mapper_concurrency = 16  # type: ignore[misc]
    except (AttributeError, Exception):
        return
    raise AssertionError("PipelineConfig should be frozen")
