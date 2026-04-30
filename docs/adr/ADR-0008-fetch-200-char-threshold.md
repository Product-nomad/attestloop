# ADR-0008 — 200-character fetch threshold for empty-body detection

- **Status:** Accepted
- **Date:** 2026-04-30

## Context

The first iteration of the fetcher returned a `Publication` with empty
`cleaned_text` whenever a page was JS-rendered or behind a redirect,
silently feeding nothing to the classifier. We needed a clean signal
that distinguishes "page loaded but is genuinely tiny" from "page is
empty / fetch failed".

## Decision

`fetch.py` raises `EmptyPublicationError` if no candidate URL produces
≥ 200 chars of stripped, usable text. The pipeline catches this and
exits with code `3` and a clear stderr message.

## Consequences

Distinguishes a brief regulator notice (reliably > 200 chars) from a
SPA shell or 404 (reliably < 200 chars). Callers can branch on exit
code `3` to retry or escalate. **Trade:** a real notice shorter than
200 chars would be wrongly rejected; we have not seen one in practice
and the failure mode (false negative on tiny notice) is preferable to
the alternative (silently classifying nothing).
