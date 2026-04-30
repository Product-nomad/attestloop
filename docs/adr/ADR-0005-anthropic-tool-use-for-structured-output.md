# ADR-0005 — Anthropic tool-use to enforce structured output

- **Status:** Accepted
- **Date:** 2026-04-30

## Context

Each agent must return data that round-trips through a Pydantic model.
Free-form Claude output plus regex/JSON parsing is brittle; JSON-mode
prompting drifts. We needed the strictest available output contract.

## Decision

Every LLM call defines exactly one tool whose `input_schema` is the
output Pydantic model's `model_json_schema()`, with
`tool_choice={"type": "tool", "name": ...}` forcing the call.

## Consequences

Tool-use is the most reliable structured-output path in the Anthropic
API as of model 4.6 — more reliable than JSON-mode prompting, and the
schema validation happens server-side before we ever see the result.
**Trade:** we lose the ability to get a chain-of-thought prelude before
the structured output. For the three current agents (which embed any
needed reasoning inside the schema's `reasoning` field) we don't need
one. If a future agent needs visible scratchwork we'll add a second
non-tool message, not abandon tool-use.
