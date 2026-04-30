from datetime import datetime, timezone

from attestloop.schemas import (
    ClassifierInput,
    ClassifierOutput,
    Control,
    ControlMapping,
    ExtractorInput,
    ExtractorOutput,
    LLMCallLog,
    MapperInput,
    MapperOutput,
    Obligation,
    Publication,
    RunMetadata,
)


def _roundtrip(model):
    cls = type(model)
    return cls.model_validate_json(model.model_dump_json())


def _publication() -> Publication:
    return Publication(
        url="https://example.eu/regulation",
        title="Example Regulation",
        raw_html="<html><body><p>Hello</p></body></html>",
        cleaned_text="Hello",
        fetched_at=datetime(2026, 4, 30, 12, 0, 0, tzinfo=timezone.utc),
    )


def _obligation(obligation_id: str = "obl-1") -> Obligation:
    return Obligation(
        id=obligation_id,
        source_paragraph="Article 9(2)",
        requirement_text="Providers shall establish a risk management system.",
        scope="high-risk AI systems",
        deadline="2027-08-02",
        evidence_required="Documented risk management system covering the lifecycle.",
    )


def _control(control_id: str = "GV.RM-01") -> Control:
    return Control(
        id=control_id,
        function="GOVERN",
        category="GV.RM",
        subcategory_text="Risk management strategies are established and managed.",
    )


def test_publication_roundtrip():
    pub = _publication()
    out = _roundtrip(pub)
    assert out == pub


def test_publication_roundtrip_title_none():
    pub = _publication().model_copy(update={"title": None})
    out = _roundtrip(pub)
    assert out.title is None


def test_classifier_input_roundtrip():
    inp = ClassifierInput(publication=_publication(), regulation_id="eu_ai_act")
    assert _roundtrip(inp) == inp


def test_classifier_output_roundtrip():
    out = ClassifierOutput(
        in_scope=True,
        category="regulation",
        confidence=0.92,
        reasoning="Title and structure match a primary regulation.",
    )
    assert _roundtrip(out) == out


def test_obligation_roundtrip():
    obl = _obligation()
    assert _roundtrip(obl) == obl


def test_obligation_roundtrip_optional_fields_none():
    obl = _obligation().model_copy(update={"deadline": None, "evidence_required": None})
    out = _roundtrip(obl)
    assert out.deadline is None
    assert out.evidence_required is None


def test_extractor_input_roundtrip():
    inp = ExtractorInput(publication=_publication(), regulation_id="eu_ai_act")
    assert _roundtrip(inp) == inp


def test_extractor_output_roundtrip():
    out = ExtractorOutput(obligations=[_obligation("o1"), _obligation("o2")])
    assert _roundtrip(out) == out


def test_extractor_output_empty():
    out = ExtractorOutput(obligations=[])
    assert _roundtrip(out) == out


def test_control_roundtrip():
    ctl = _control()
    assert _roundtrip(ctl) == ctl


def test_control_mapping_roundtrip():
    mapping = ControlMapping(
        obligation_id="obl-1",
        control_id="GV.RM-01",
        confidence=0.78,
        reasoning="Risk management obligation aligns with the GOVERN function.",
    )
    assert _roundtrip(mapping) == mapping


def test_mapper_input_roundtrip():
    inp = MapperInput(
        obligations=[_obligation("o1")],
        controls=[_control("GV.RM-01"), _control("MP.IA-01")],
        framework_id="nist_ai_rmf",
    )
    assert _roundtrip(inp) == inp


def test_mapper_output_roundtrip():
    out = MapperOutput(
        mappings=[
            ControlMapping(
                obligation_id="o1",
                control_id="GV.RM-01",
                confidence=0.8,
                reasoning="Direct alignment.",
            )
        ]
    )
    assert _roundtrip(out) == out


def test_run_metadata_roundtrip():
    meta = RunMetadata(
        run_id="run-2026-04-30-001",
        started_at=datetime(2026, 4, 30, 12, 0, 0, tzinfo=timezone.utc),
        regulation_id="eu_ai_act",
        framework_id="nist_ai_rmf",
        total_cost_usd=0.1234,
        total_input_tokens=12000,
        total_output_tokens=3400,
    )
    assert _roundtrip(meta) == meta


def test_llm_call_log_roundtrip():
    log = LLMCallLog(
        agent="classifier",
        model="claude-opus-4-7",
        prompt_version="v1",
        input_tokens=2500,
        output_tokens=180,
        cost_usd=0.0421,
        latency_ms=1843,
        started_at=datetime(2026, 4, 30, 12, 0, 1, tzinfo=timezone.utc),
        prompt="System: ...\nUser: ...",
        response='{"in_scope": true, "category": "regulation", "confidence": 0.9, "reasoning": "..."}',
    )
    assert _roundtrip(log) == log
