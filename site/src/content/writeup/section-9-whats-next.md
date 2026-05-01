---
title: What's next
status: draft
updated: 2026-04-30
---

v6 has shipped. The orchestration work tracked in issue #4 is complete: LangGraph state machine, parallel Mapper, Critic agent, and Clarifier agent with conditional routing. The remaining items below are the v7+ backlog.

- **Mapper batching for cost optimisation (#1).** 4–8 obligations per Sonnet call instead of one, reducing API overhead by ~10×. Trade-off: per-batch failure handling becomes the new failure mode to manage.
- **Longer-TTL cache for sustained throughput (#2).** The 5-minute ephemeral cache is insufficient for runs that hit rate limits. Anthropic's longer-TTL cache tier or restructured call cadence both close the gap.
- **Multi-source watcher agent (#3).** v1 runs on demand against URLs the user supplies. The Watcher polls regulator sources on a schedule, deduplicates against historical runs, and queues new in-scope publications. The architecture supports it; v2 implements the per-regulator scrape adapters.
- **Quantitative evals.** Hand-labelled gold sets for obligation extraction and mapping accuracy. The first task before any production attempt would be defensible.
- **Multi-framework support.** ISO 42001, SOC 2 AI Trust Criteria, customer-supplied control libraries. The Framework registry already supports the abstraction; v2 implements the additional frameworks.
- **Parallelise the Critic.** v6 moved the bottleneck from Mapper to Critic. The Critic's pattern is identical to the Mapper's (per-obligation, cacheable controls block, embarrassingly parallel) — applying the same `asyncio.gather` + `Semaphore` pattern brings total pipeline wall-clock to ~5–7 minutes.
- **Negative examples in the Mapper prompt.** The five recurring failure patterns the Critic surfaced (MANAGE-1.1 mis-used as per-event gate, MAP-3.3 reaching for legal-perimeter semantics, etc.) could be addressed directly in the Mapper prompt with negative examples. Worth measuring whether this drops the Critic flag rate without hurting overall mapping coverage.

v1 is a portfolio piece designed to demonstrate orchestration thinking and end-to-end engineering against a real problem. Production readiness is a different artefact, and the gap between v1 and a real product is named explicitly so the reader knows what's missing. Naming the gap is itself a v1 feature.
