"""LangGraph orchestration layer for the Attestloop pipeline.

Wires the existing agent functions into a typed StateGraph so future v6
work (Critic, Clarifier, parallel Mapper) can attach as additional nodes
and conditional edges without restructuring the call site. v6 task 1
introduces the wiring; behaviour is unchanged from v5 — the graph is
sequential, single-threaded, and each node calls the same agent function
with the same arguments as the prior pipeline.py main()."""
from datetime import datetime
from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, StateGraph

from attestloop.agents.classifier import classify
from attestloop.agents.extractor import extract
from attestloop.agents.mapper import map_to_controls
from attestloop.fetch import fetch_publication
from attestloop.registry import Framework, Regulation
from attestloop.report import (
    aggregate_usage,
    build_in_scope_report,
    build_out_of_scope_report,
)
from attestloop.schemas import (
    ClassifierInput,
    ClassifierOutput,
    ControlMapping,
    ExtractorInput,
    ExtractorOutput,
    MapperInput,
    MapperOutput,
    Obligation,
    Publication,
    RunMetadata,
)


class PipelineState(TypedDict, total=False):
    """Typed state passed through the graph. `total=False` because
    fields are populated incrementally as each node runs; LangGraph
    merges per-node return dicts into the running state."""

    # Inputs (set by run() before invoking the graph)
    url: str
    regulation_id: str
    framework_id: str
    run_dir: Path
    run_id: str
    started_at: datetime
    regulation: Regulation
    framework: Framework

    # Per-agent outputs
    publication: Publication
    classification: ClassifierOutput
    obligations: list[Obligation]
    mappings: list[ControlMapping]

    # Final
    report_path: Path


# ─────────────────────────── nodes ───────────────────────────

def fetch_node(state: PipelineState) -> dict:
    publication = fetch_publication(state["url"], run_dir=state["run_dir"])
    (state["run_dir"] / "publication.json").write_text(
        publication.model_dump_json(indent=2)
    )
    return {"publication": publication}


def classify_node(state: PipelineState) -> dict:
    classification = classify(
        ClassifierInput(
            publication=state["publication"],
            regulation_id=state["regulation"].id,
        ),
        state["regulation"],
        state["run_dir"],
    )
    return {"classification": classification}


def extract_node(state: PipelineState) -> dict:
    extractor_output = extract(
        ExtractorInput(
            publication=state["publication"],
            regulation_id=state["regulation"].id,
        ),
        state["regulation"],
        state["run_dir"],
    )
    (state["run_dir"] / "obligations.json").write_text(
        extractor_output.model_dump_json(indent=2)
    )
    return {"obligations": extractor_output.obligations}


def map_node(state: PipelineState) -> dict:
    mapper_output = map_to_controls(
        MapperInput(
            obligations=state["obligations"],
            controls=state["framework"].controls,
            framework_id=state["framework"].id,
        ),
        state["framework"],
        state["run_dir"],
    )
    (state["run_dir"] / "mappings.json").write_text(
        mapper_output.model_dump_json(indent=2)
    )
    return {"mappings": mapper_output.mappings}


def report_node(state: PipelineState) -> dict:
    cost, in_tok, out_tok = aggregate_usage(state["run_dir"])
    report = build_in_scope_report(
        publication=state["publication"],
        classifier_output=state["classification"],
        extractor_output=ExtractorOutput(obligations=state["obligations"]),
        mapper_output=MapperOutput(mappings=state["mappings"]),
        regulation=state["regulation"],
        framework=state["framework"],
        run_id=state["run_id"],
        started_at=state["started_at"],
        cost_usd=cost,
        input_tokens=in_tok,
        output_tokens=out_tok,
    )
    report_path = state["run_dir"] / "report.md"
    report_path.write_text(report)

    metadata = RunMetadata(
        run_id=state["run_id"],
        started_at=state["started_at"],
        regulation_id=state["regulation"].id,
        framework_id=state["framework"].id,
        total_cost_usd=cost,
        total_input_tokens=in_tok,
        total_output_tokens=out_tok,
    )
    (state["run_dir"] / "run_metadata.json").write_text(
        metadata.model_dump_json(indent=2)
    )
    return {"report_path": report_path}


def out_of_scope_node(state: PipelineState) -> dict:
    cost, in_tok, out_tok = aggregate_usage(state["run_dir"])
    report = build_out_of_scope_report(
        publication=state["publication"],
        classifier_output=state["classification"],
        regulation=state["regulation"],
        framework=state["framework"],
        run_id=state["run_id"],
        started_at=state["started_at"],
        cost_usd=cost,
        input_tokens=in_tok,
        output_tokens=out_tok,
    )
    report_path = state["run_dir"] / "report.md"
    report_path.write_text(report)

    metadata = RunMetadata(
        run_id=state["run_id"],
        started_at=state["started_at"],
        regulation_id=state["regulation"].id,
        framework_id=state["framework"].id,
        total_cost_usd=cost,
        total_input_tokens=in_tok,
        total_output_tokens=out_tok,
    )
    (state["run_dir"] / "run_metadata.json").write_text(
        metadata.model_dump_json(indent=2)
    )
    return {"report_path": report_path}


# ─────────────────────────── edges ───────────────────────────

def route_after_classify(state: PipelineState) -> str:
    """Conditional edge after the Classifier. v1 only branches on
    in_scope; v6 task 3 will add a low-confidence Clarifier branch."""
    return "extract" if state["classification"].in_scope else "out_of_scope"


# ───────────────────────── graph builder ─────────────────────────

def build_pipeline_graph():
    """Compile the v6 pipeline as a LangGraph StateGraph. Returns a
    CompiledStateGraph ready for `.invoke(initial_state)`."""
    graph = StateGraph(PipelineState)

    graph.add_node("fetch", fetch_node)
    graph.add_node("classify", classify_node)
    graph.add_node("extract", extract_node)
    graph.add_node("map", map_node)
    graph.add_node("report", report_node)
    graph.add_node("out_of_scope", out_of_scope_node)

    graph.set_entry_point("fetch")
    graph.add_edge("fetch", "classify")
    graph.add_conditional_edges(
        "classify",
        route_after_classify,
        {"extract": "extract", "out_of_scope": "out_of_scope"},
    )
    graph.add_edge("extract", "map")
    graph.add_edge("map", "report")
    graph.add_edge("report", END)
    graph.add_edge("out_of_scope", END)

    return graph.compile()
