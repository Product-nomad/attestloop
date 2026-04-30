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

from attestloop.agents.clarifier import clarify_and_reclassify
from attestloop.agents.classifier import classify
from attestloop.agents.critic import review_mappings
from attestloop.agents.extractor import extract
from attestloop.agents.mapper import map_to_controls
from attestloop.fetch import fetch_publication
from attestloop.registry import Framework, Regulation
from attestloop.report import (
    aggregate_usage,
    build_in_scope_report,
    build_out_of_scope_report,
    build_review_queue_report,
)
from attestloop.schemas import (
    ClarifierOutput,
    ClassifierInput,
    ClassifierOutput,
    ControlMapping,
    CriticDecision,
    ExtractorInput,
    ExtractorOutput,
    MapperFailure,
    MapperInput,
    MapperOutput,
    Obligation,
    Publication,
    RunMetadata,
)
import json as _json

# Below this confidence on an out_of_scope verdict, the pipeline routes
# to the Clarifier rather than committing to the out-of-scope report.
LOW_CONFIDENCE_THRESHOLD = 0.7


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
    clarifier_output: ClarifierOutput
    obligations: list[Obligation]
    mappings: list[ControlMapping]
    mapper_failures: list[MapperFailure]
    critic_decisions: list[CriticDecision]

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

    # Parallel Mapper writes mapper_failures.json only when at least one
    # obligation errored permanently — read it back so report_node can
    # surface the failures section. Empty list when the file is absent.
    failures: list[MapperFailure] = []
    failures_path = state["run_dir"] / "mapper_failures.json"
    if failures_path.exists():
        failures = [
            MapperFailure(**entry) for entry in _json.loads(failures_path.read_text())
        ]

    return {
        "mappings": mapper_output.mappings,
        "mapper_failures": failures,
    }


def critic_node(state: PipelineState) -> dict:
    """Run the second-pass Critic on any obligation whose mappings
    include at least one entry below 0.80 confidence. Always invoked
    in the in-scope path; produces an empty decisions list when there
    is nothing to review.

    The structured CriticOutput is persisted to critic_decisions.json
    rather than critic.json — the latter is reserved for the per-call
    LLMCallLog list written by call_with_logging, matching the
    obligations.json / mappings.json convention for the upstream agents.
    """
    output = review_mappings(
        state["obligations"],
        state["mappings"],
        state["framework"],
        state["run_dir"],
    )
    (state["run_dir"] / "critic_decisions.json").write_text(
        output.model_dump_json(indent=2)
    )
    return {"critic_decisions": output.decisions}


def report_node(state: PipelineState) -> dict:
    cost, in_tok, out_tok = aggregate_usage(state["run_dir"])
    report = build_in_scope_report(
        publication=state["publication"],
        classifier_output=state["classification"],
        clarifier_output=state.get("clarifier_output"),
        extractor_output=ExtractorOutput(obligations=state["obligations"]),
        mapper_output=MapperOutput(mappings=state["mappings"]),
        mapper_failures=state.get("mapper_failures", []),
        critic_decisions=state.get("critic_decisions", []),
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
        clarifier_output=state.get("clarifier_output"),
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


def clarify_node(state: PipelineState) -> dict:
    """Re-attempt classification with additional context fetched from
    the publication. Supersedes state['classification'] with the
    re-classification while preserving the original on the
    ClarifierOutput.initial_classification field for the audit trail."""
    output = clarify_and_reclassify(
        state["publication"],
        state["classification"],
        state["regulation"],
        state["run_dir"],
    )
    (state["run_dir"] / "clarifier.json").write_text(
        output.model_dump_json(indent=2)
    )
    return {
        "clarifier_output": output,
        "classification": output.reclassification,
    }


def review_queue_node(state: PipelineState) -> dict:
    """Both classification passes returned ambiguous out_of_scope. The
    pipeline cannot reach a confident verdict from this URL alone;
    write a review-queue report and let a human take it from here."""
    cost, in_tok, out_tok = aggregate_usage(state["run_dir"])
    report = build_review_queue_report(
        publication=state["publication"],
        classifier_output=state["classification"],
        clarifier_output=state["clarifier_output"],
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
    """Conditional edge after the Classifier. Three outcomes:
      - in_scope (any confidence) → extract
      - out_of_scope at confidence ≥ 0.7 → commit, write out_of_scope report
      - out_of_scope at confidence < 0.7 → clarify (re-attempt with extra context)
    """
    classification = state["classification"]
    if classification.in_scope:
        return "extract"
    if classification.confidence < LOW_CONFIDENCE_THRESHOLD:
        return "clarify"
    return "out_of_scope"


def route_after_clarify(state: PipelineState) -> str:
    """Conditional edge after the Clarifier's re-classification.
    Single-pass loop bound: there is no second Clarifier attempt. If
    the re-classification is still ambiguous, the pipeline writes a
    review-queue report and exits — this is the upper bound on cost
    and on the depth of automated reasoning the system commits to."""
    classification = state["classification"]  # superseded by clarify_node
    if classification.in_scope:
        return "extract"
    if classification.confidence < LOW_CONFIDENCE_THRESHOLD:
        return "review_queue"
    return "out_of_scope"


# ───────────────────────── graph builder ─────────────────────────

def build_pipeline_graph():
    """Compile the v6 pipeline as a LangGraph StateGraph. Returns a
    CompiledStateGraph ready for `.invoke(initial_state)`."""
    graph = StateGraph(PipelineState)

    graph.add_node("fetch", fetch_node)
    graph.add_node("classify", classify_node)
    graph.add_node("clarify", clarify_node)
    graph.add_node("extract", extract_node)
    graph.add_node("map", map_node)
    graph.add_node("critic", critic_node)
    graph.add_node("report", report_node)
    graph.add_node("out_of_scope", out_of_scope_node)
    graph.add_node("review_queue", review_queue_node)

    graph.set_entry_point("fetch")
    graph.add_edge("fetch", "classify")
    graph.add_conditional_edges(
        "classify",
        route_after_classify,
        {
            "extract": "extract",
            "clarify": "clarify",
            "out_of_scope": "out_of_scope",
        },
    )
    graph.add_conditional_edges(
        "clarify",
        route_after_clarify,
        {
            "extract": "extract",
            "review_queue": "review_queue",
            "out_of_scope": "out_of_scope",
        },
    )
    graph.add_edge("extract", "map")
    graph.add_edge("map", "critic")
    graph.add_edge("critic", "report")
    graph.add_edge("report", END)
    graph.add_edge("out_of_scope", END)
    graph.add_edge("review_queue", END)

    return graph.compile()
