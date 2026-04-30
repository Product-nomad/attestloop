# ADR-0006 — Mapper makes one LLM call per obligation

- **Status:** Accepted
- **Date:** 2026-04-30

## Context

The mapper takes N obligations and returns control mappings for each.
Two main shapes were available: one call per obligation (sequential or
fan-out), or a single batched call with all obligations in the prompt
plus prompt caching on the controls list.

## Decision

For v1 the mapper iterates obligations and ships the full 72-control
list with each call. No batching, no prompt caching.

## Consequences

Simplest possible code path; per-call logs are easy to audit; one
obligation's mapping failure doesn't take down the rest. **Cost
reality:** on the first real run this was 86% of total spend ($0.54 of
$0.62, 18 obligations). **Follow-up planned:** batch N obligations per
call with prompt caching on the controls list — likely 5–10× cost
reduction. Deferred so that v1 ships and the cost shape is measurable
in real numbers, not predicted ones.
