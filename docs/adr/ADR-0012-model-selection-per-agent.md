# ADR-0012 — Sonnet 4.6 for extractor + mapper, Haiku 4.5 for classifier

- **Status:** Accepted
- **Date:** 2026-04-30

## Context

Three agents with different shapes. The classifier sees a snippet and
returns a five-way enum + boolean. The extractor and mapper produce
structured lists with reasoning fields and need to hit a tight schema
over potentially long input.

## Decision

- Classifier: `claude-haiku-4-5-20251001`.
- Extractor: `claude-sonnet-4-6`.
- Mapper: `claude-sonnet-4-6` (one call per obligation per ADR-0006).

## Consequences

Cost shape on the first real run: classifier $0.005, extractor $0.082,
mapper $0.537. Total $0.62 — Haiku-on-classifier saved roughly $0.04
without any quality loss observed. **Re-evaluate when:** Haiku 5 lands
(likely strong enough for the extractor); Sonnet caching matures
(would shift the mapper economics).
