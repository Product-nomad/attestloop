# ADR-0007 — Extractor truncates source text at 50 000 characters

- **Status:** Accepted
- **Date:** 2026-04-30

## Context

Regulator publications range from short notices to ~500 KB of cleaned
text (e.g. the EU AI Act consolidated text). The extractor needs a
predictable cost shape and a working-context size that suits Sonnet.
Chunked extraction with cross-chunk obligation deduplication is real
work and would push v1 out of scope.

## Decision

`agents/extractor.py` truncates `cleaned_text[:50_000]` before sending
to the LLM, with a yellow `rich` warning when truncation fires.

## Consequences

Keeps the extractor's prompt under Sonnet's working-context comfort
zone, keeps cost predictable, ships v1. **Trade:** documents larger
than 50 000 chars only get their front matter seen. The first real run
truncated the Commission Guidelines (429 K chars → 50 K), so its 18
obligations come from roughly the first 12 % of the document. Chunked
extraction is in the backlog and will likely supersede this ADR.
