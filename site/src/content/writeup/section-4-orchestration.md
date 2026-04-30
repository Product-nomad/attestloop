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

Human-in-the-loop boundaries exist conceptually but aren't wired in v1. The natural points are: between the Classifier and the Extractor (review borderline scope decisions), between the Mapper and the Report builder (review low-confidence mappings before they land in the report), and between the Report builder and any downstream system (sign-off before publication). v1 surfaces all the data needed for HITL — confidence scores per mapping, unmapped obligations as their own report section, hashed prompt versions in the provenance footer — but doesn't yet hold the pipeline open for human input. The architecture supports adding HITL hooks at those points without restructuring; v6's state-machine refactor will make the wiring explicit.

What v1 doesn't have, and what v6 will: a typed PipelineState object passed through a LangGraph StateGraph, conditional edges that route based on agent outputs (Classifier returning in_scope=False, confidence<0.7 should route to a Clarifier agent, not directly to the out-of-scope report), parallel Mapper execution with concurrency control, and a Critic agent that reviews mappings below 0.80 confidence before they reach the report.

Those are real orchestration patterns, and they're tracked in issue #4. v1 prioritised end-to-end correctness with explicit per-stage observability; v6 layers orchestration on top of that foundation. The order matters: orchestrating a pipeline that produces wrong outputs is wasted optimisation. Sequential execution with disk-logged state was the cheapest way to validate that each stage produced the right thing before the stages started talking to each other.

A pragmatic note: for a v1 portfolio piece running on demand against single documents, sequential execution is also operationally adequate. 17 minutes wall-clock for a 71-obligation, 154-mapping run on a 135-page guideline is acceptable for human-paced compliance work. v6 closes the latency gap — and unlocks scheduled multi-document runs — but v1's latency isn't a v1 problem.
