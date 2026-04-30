"""Tests for the v6 task 4 parallel Mapper.

These don't make Anthropic calls — they patch _call_mapper_async or
the AsyncAnthropic client to return synthetic results. The real
end-to-end behaviour is covered by the smoke run captured in
docs/example_runs/v6_parallel_mapper/."""
import asyncio
import inspect
from pathlib import Path
from unittest.mock import patch

import pytest

from attestloop.agents import mapper as mapper_module
from attestloop.agents.mapper import (
    MAPPER_CONCURRENCY,
    _map_to_controls_async,
    map_to_controls,
)
from attestloop.registry import Framework, get_framework
from attestloop.schemas import (
    ControlMapping,
    MapperInput,
    MapperOutput,
    Obligation,
)


def _obl(suffix: str) -> Obligation:
    return Obligation(
        id=f"EUAIA-OBL-{suffix}",
        source_paragraph="Article 5",
        requirement_text=f"Requirement {suffix}",
        scope="Providers",
        deadline=None,
        evidence_required=None,
    )


def _fixed_mapping(obligation_id: str, control_id: str = "GOVERN-1.1") -> ControlMapping:
    return ControlMapping(
        obligation_id=obligation_id,
        control_id=control_id,
        confidence=0.85,
        reasoning="(synthetic)",
    )


def test_async_mapper_preserves_input_order(tmp_path):
    """Five obligations, mocked LLM returns in shuffled completion
    order via random sleeps — final mappings list must follow input
    order, not completion order."""
    framework = get_framework("nist_ai_rmf")
    obligations = [_obl(f"{i:03d}") for i in (1, 2, 3, 4, 5)]
    # Inverse delays so OBL-005 returns first, OBL-001 last
    delays = {f"EUAIA-OBL-{i:03d}": 0.05 - i * 0.005 for i in (1, 2, 3, 4, 5)}

    async def fake_call(obligation, *args, **kwargs):
        await asyncio.sleep(max(0.001, delays[obligation.id]))
        return [_fixed_mapping(obligation.id)]

    with patch.object(mapper_module, "_call_mapper_async", fake_call):
        mappings, failures = asyncio.run(
            _map_to_controls_async(
                obligations, framework, "nist_ai_rmf", tmp_path
            )
        )

    assert failures == []
    ordered_ids = [m.obligation_id for m in mappings]
    expected = [o.id for o in obligations]
    assert ordered_ids == expected, (
        f"mappings out of input order: {ordered_ids} vs {expected}"
    )


def test_async_mapper_handles_partial_failures(tmp_path):
    """Mock raises on every 3rd obligation. Successful obligations'
    mappings must still arrive; failures must be captured in the
    returned MapperFailure list."""
    framework = get_framework("nist_ai_rmf")
    obligations = [_obl(f"{i:03d}") for i in range(1, 10)]

    async def fake_call(obligation, *args, **kwargs):
        idx = int(obligation.id.split("-")[-1])
        if idx % 3 == 0:
            raise RuntimeError(f"synthetic failure for {obligation.id}")
        return [_fixed_mapping(obligation.id)]

    with patch.object(mapper_module, "_call_mapper_async", fake_call):
        mappings, failures = asyncio.run(
            _map_to_controls_async(
                obligations, framework, "nist_ai_rmf", tmp_path
            )
        )

    successful = [o.id for o in obligations if int(o.id.split("-")[-1]) % 3 != 0]
    failed = [o.id for o in obligations if int(o.id.split("-")[-1]) % 3 == 0]

    assert [m.obligation_id for m in mappings] == successful
    assert sorted(f.obligation_id for f in failures) == sorted(failed)
    for f in failures:
        assert "synthetic failure" in f.error


def test_async_mapper_concurrency_respects_cap(tmp_path):
    """Run 30 obligations through the async mapper with a tracker that
    counts in-flight tasks. Maximum concurrent count must never exceed
    MAPPER_CONCURRENCY."""
    framework = get_framework("nist_ai_rmf")
    obligations = [_obl(f"{i:03d}") for i in range(1, 31)]

    state = {"in_flight": 0, "max_in_flight": 0}
    state_lock = asyncio.Lock()

    async def fake_call(obligation, *args, **kwargs):
        async with state_lock:
            state["in_flight"] += 1
            state["max_in_flight"] = max(state["max_in_flight"], state["in_flight"])
        await asyncio.sleep(0.05)
        async with state_lock:
            state["in_flight"] -= 1
        return [_fixed_mapping(obligation.id)]

    with patch.object(mapper_module, "_call_mapper_async", fake_call):
        asyncio.run(
            _map_to_controls_async(
                obligations, framework, "nist_ai_rmf", tmp_path
            )
        )

    assert state["max_in_flight"] <= MAPPER_CONCURRENCY, (
        f"semaphore violated: max in-flight = {state['max_in_flight']}, "
        f"cap = {MAPPER_CONCURRENCY}"
    )
    # And it should reach the cap given 30 obligations × 50 ms each
    assert state["max_in_flight"] >= MAPPER_CONCURRENCY - 1, (
        f"concurrency never approached cap: max in-flight = {state['max_in_flight']}"
    )


def test_sync_wrapper_preserves_signature():
    """The public sync entrypoint's first three positional parameters
    must remain compatible with the orchestration's map_node call site.
    Additional optional parameters (e.g. v6 task 5's mapper_concurrency)
    are allowed only if keyword-only and defaulted."""
    sig = inspect.signature(map_to_controls)
    params = list(sig.parameters.values())
    positional = [
        p for p in params
        if p.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )
    ]
    assert [p.name for p in positional] == ["input", "framework", "run_dir"]
    assert sig.return_annotation is MapperOutput
    assert positional[0].annotation is MapperInput
    assert positional[1].annotation is Framework
    assert positional[2].annotation is Path

    extra = [p for p in params if p.kind == inspect.Parameter.KEYWORD_ONLY]
    for p in extra:
        assert p.default is not inspect.Parameter.empty, (
            f"keyword-only param {p.name} must have a default to preserve "
            f"the v5 call site"
        )
