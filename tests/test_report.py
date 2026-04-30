"""Tests for the report module's aggregate_usage helper.

The v6 task 5 filename rename (<agent>.json → <agent>.calls.json)
means aggregate_usage must support both naming schemes — old v1–v5
snapshots have <agent>.json, new v6+ runs use the .calls.json
suffix. The function must read either one without double-counting
when both are present and without summing structured-output files
that happen to be JSON lists."""
import json
from pathlib import Path

from attestloop.report import aggregate_usage


def _write_log(path: Path, *, cost: float, in_tok: int, out_tok: int) -> None:
    """Write a single-entry per-call log file in the LLMCallLog shape."""
    path.write_text(
        json.dumps(
            [
                {
                    "agent": path.stem.replace(".calls", ""),
                    "model": "claude-sonnet-4-6",
                    "prompt_version": "deadbeef",
                    "input_tokens": in_tok,
                    "output_tokens": out_tok,
                    "cost_usd": cost,
                    "latency_ms": 100,
                    "started_at": "2026-04-30T18:00:00+00:00",
                    "prompt": "(test)",
                    "response": "(test)",
                }
            ]
        )
    )


def test_aggregate_usage_reads_new_calls_naming(tmp_path):
    _write_log(tmp_path / "classifier.calls.json", cost=0.10, in_tok=100, out_tok=10)
    _write_log(tmp_path / "mapper.calls.json", cost=0.50, in_tok=500, out_tok=50)
    cost, in_tok, out_tok = aggregate_usage(tmp_path)
    assert cost == 0.60
    assert in_tok == 600
    assert out_tok == 60


def test_aggregate_usage_reads_legacy_naming(tmp_path):
    _write_log(tmp_path / "classifier.json", cost=0.10, in_tok=100, out_tok=10)
    _write_log(tmp_path / "mapper.json", cost=0.50, in_tok=500, out_tok=50)
    cost, in_tok, out_tok = aggregate_usage(tmp_path)
    assert cost == 0.60
    assert in_tok == 600
    assert out_tok == 60


def test_aggregate_usage_handles_both_naming_schemes(tmp_path):
    """A directory mixing old and new — calls.json takes precedence
    for any agent that has both, and unique-named legacy logs are
    still summed. Total must not double-count."""
    _write_log(tmp_path / "mapper.calls.json", cost=0.50, in_tok=500, out_tok=50)
    _write_log(tmp_path / "mapper.json", cost=99.99, in_tok=99999, out_tok=9999)
    _write_log(tmp_path / "extractor.json", cost=0.20, in_tok=200, out_tok=20)
    cost, in_tok, out_tok = aggregate_usage(tmp_path)
    assert cost == 0.70
    assert in_tok == 700
    assert out_tok == 70


def test_aggregate_usage_skips_structured_outputs(tmp_path):
    """Structured-output files (obligations.json, mappings.json,
    classification.json, etc.) must be ignored even though they live
    next to call logs in the same directory."""
    _write_log(tmp_path / "classifier.calls.json", cost=0.10, in_tok=100, out_tok=10)
    (tmp_path / "obligations.json").write_text(
        json.dumps({"obligations": []})
    )
    (tmp_path / "mappings.json").write_text(json.dumps({"mappings": []}))
    (tmp_path / "classification.json").write_text(
        json.dumps(
            {
                "in_scope": True,
                "category": "regulation",
                "confidence": 0.9,
                "reasoning": "(test)",
            }
        )
    )
    (tmp_path / "clarifier_output.json").write_text(json.dumps({"foo": "bar"}))
    (tmp_path / "critic_decisions.json").write_text(json.dumps({"decisions": []}))
    (tmp_path / "publication.json").write_text(json.dumps({}))
    (tmp_path / "run_metadata.json").write_text(json.dumps({}))

    cost, in_tok, out_tok = aggregate_usage(tmp_path)
    assert cost == 0.10
    assert in_tok == 100
    assert out_tok == 10


def test_aggregate_usage_empty_dir(tmp_path):
    cost, in_tok, out_tok = aggregate_usage(tmp_path)
    assert (cost, in_tok, out_tok) == (0.0, 0, 0)
