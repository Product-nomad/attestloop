# ADR-0001 — Pydantic v2 with `extra="forbid"` everywhere

- **Status:** Accepted
- **Date:** 2026-04-30

## Context

Every cross-boundary data shape in Attestloop — tool outputs from
Claude, configs loaded from disk, log entries written for audit — needs
a strict, machine-checkable contract. Pydantic v2 is the obvious choice
for typed Python; the question was whether to allow forward-compatible
extra fields or reject them.

## Decision

Every domain model declares `model_config = ConfigDict(extra="forbid")`.
Confidence floats are bounded with `Field(ge=0.0, le=1.0)` so a model
returning `1.5` is caught at the boundary.

## Consequences

A small amount of boilerplate. The benefit is that schema mismatches
between the LLM's tool output and our model fail at parse time with a
clear `ValidationError` rather than silently dropping fields into
oblivion. If a regulator config later wants to add fields, we have to
update the schema explicitly — which is exactly the audit trail we
want.
