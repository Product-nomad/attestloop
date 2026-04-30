# ADR-0014 — 60 s LLM timeout with one retry on transient errors

- **Status:** Accepted
- **Date:** 2026-04-30

## Context

The Anthropic SDK can hang on network glitches and occasionally
returns transient errors (rate-limit, 5xx, connection drop). We need
a posture: how long to wait, and whether to retry.

## Decision

`call_with_logging` sets `timeout=60.0` on the Anthropic client and
retries exactly once on `APITimeoutError`, `APIConnectionError`,
`RateLimitError`, or `InternalServerError`. All other exceptions
propagate.

## Consequences

Covers the common flake without masking real failures. **Why one retry,
not exponential backoff:** for v1 the agents are sequential and a real
outage should fail loudly so the user notices; the cost of one extra
duplicate API call is small compared to the cost of silently looping
on a broken endpoint. Reconsider when we add background or scheduled
runs.
