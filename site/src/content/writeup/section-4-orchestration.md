---
title: Orchestration
status: draft
updated: 2026-04-30
---

The pipeline is a Python module — src/attestloop/pipeline.py — that ties the three agents and four passive components together. v1 ships sequential execution: each step runs to completion, writes its output to disk, and the next step picks it up. There is no orchestrator agent, no parallel work, no conditional routing. The shape is closer to a Unix pipeline than to LangGraph.

The top-level function reads:

```python
def run(url: str, regulation_id: str, framework_id: str) -> Path:
    run_dir = create_run_dir()
    publication = fetch_publication(url, run_dir)
    regulation = registry.get_regulation(regulation_id)
    framework = registry.get_framework(framework_id)

    classification = classify(publication, regulation, run_dir)
    if not classification.in_scope:
        return write_out_of_scope_report(run_dir, classification)

    obligations = extract_chunked(publication, regulation, run_dir)
    mappings = map_to_controls(obligations, framework, run_dir)

    return build_report(run_dir, publication, classification,
                        obligations, mappings, regulation, framework)
```

Eight lines of orchestration logic, each agent invocation taking structured input and returning structured output. Each output is also serialised to runs/<run_id>/<agent>.json before the next step runs, so the run is recoverable, inspectable, and debuggable from disk alone.

State passing is explicit. There's no shared mutable context, no implicit globals, no agent reading another agent's output through a side channel. The Mapper takes the Extractor's obligations list as a typed argument; if the Extractor returns nothing, the Mapper trivially produces nothing; if either fails, the disk artefacts from prior steps remain for diagnosis. The state machine is the call stack.

Failure handling lives at three levels. Per-call: each LLM invocation has a 60-second timeout and a single retry on transient errors (APITimeoutError, APIConnectionError, RateLimitError, InternalServerError). Per-agent: structured error types — EmptyPublicationError from the fetcher, RateLimitBackoff from the LLM wrapper — propagate cleanly to the pipeline, where they decide whether to retry, fail loudly, or short-circuit. Per-run: any uncaught error leaves the run directory intact with whatever artefacts had been written, so post-mortem is possible.

Human-in-the-loop boundaries exist conceptually but aren't wired in v1. The natural points are: between the Classifier and the Extractor (review borderline scope decisions), between the Mapper and the Report builder (review low-confidence mappings before they land in the report), and between the Report builder and any downstream system (sign-off before publication). v1 surfaces all the data needed for HITL — confidence scores per mapping, unmapped obligations as their own report section, hashed prompt versions in the provenance footer — but doesn't yet hold the pipeline open for human input. The architecture supports adding HITL hooks at those points without restructuring; v6's state-machine refactor made the wiring explicit.

v6: orchestration

v6 replaces the eight-line sequential function with a typed StateGraph from LangGraph. Each agent becomes a graph node. State flows through edges. Conditional routing makes ambiguous Classifier outputs trigger the Clarifier; confident ones bypass it. Parallel Mapper execution happens within the Mapper node — 8-way concurrent calls bounded by an asyncio.Semaphore.

The compiled graph:

```
fetch → classify → [in_scope] → extract → map → critic → report → END
                 → [low_conf_oos] → clarify → [in_scope] → extract → ...
                                           → [low_conf_oos] → review_queue → END
                                           → [confident_oos] → out_of_scope → END
                 → [confident_oos] → out_of_scope → END
```

The Mermaid source for this diagram is generated directly from the compiled LangGraph — `scripts/render_graph.py` calls `graph.get_graph().draw_mermaid()` on the compiled state machine and writes the result to `docs/orchestration/v6_pipeline.mmd`. The diagram is not hand-drawn; it's a literal rendering of the state machine the code constructs. If the orchestration changes, the diagram regenerates automatically.

A PipelineConfig dataclass with feature flags (mapper_concurrency, enable_critic, enable_clarifier_routing) lets the same codebase produce v5-equivalent runs (config = V5_EQUIVALENT) and v6 canonical runs (config = V6_CANONICAL) without forking. This is what makes the v5/v6 comparison rigorous: same code, same prompts, only the orchestration toggles change.

What v1 didn't have, and what v6 added: a typed PipelineState object passed through a LangGraph StateGraph, conditional edges that route based on agent outputs (Classifier returning in_scope=False, confidence<0.7 routes to the Clarifier rather than directly to the out-of-scope report), parallel Mapper execution with concurrency control, and a Critic agent that reviews mappings below 0.80 confidence before they reach the report.

Those are real orchestration patterns, and they were tracked in issue #4. v1 prioritised end-to-end correctness with explicit per-stage observability; v6 layered orchestration on top of that foundation. The order matters: orchestrating a pipeline that produces wrong outputs is wasted optimisation. Sequential execution with disk-logged state was the cheapest way to validate that each stage produced the right thing before the stages started talking to each other.

The v6 canonical run produces 70 obligations and 130–160 mappings on the same Commission Guidelines URL in 13 minutes 26 seconds — a 4-minute reduction from v5 baseline. Most of that gain comes from the parallel Mapper (8.13× speedup on Mapper wall-clock specifically). The Critic adds about 3 minutes of sequential review work, which is what makes the end-to-end pipeline less fast than the parallel Mapper would suggest. v6 moved the bottleneck from Mapper to Critic; the next optimisation lever (tracked as v7 work) is parallelising the Critic in the same way.
