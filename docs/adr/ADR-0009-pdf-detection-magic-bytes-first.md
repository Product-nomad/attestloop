# ADR-0009 — PDF detection precedence: magic bytes > Content-Type > URL

- **Status:** Accepted
- **Date:** 2026-04-30

## Context

The original PDF detection used Content-Type *or* URL pattern. The
Commission's `ec.europa.eu/newsroom/dae/redirection/document/112367`
URL has no `.pdf` extension, no `/PDF/` segment, and (apparently) no
`application/pdf` Content-Type — but the response body is a PDF. The
fetcher mis-routed it to selectolax, which dumped 911 KB of binary
into the classifier prompt and burned $0.0114 on Haiku for unparseable
input.

## Decision

`fetch.py` decides whether to route a response to `pypdf` in this strict
order: (1) `content[:5] == b"%PDF-"` → `PDF (magic bytes)`, (2)
`Content-Type: application/pdf` → `PDF (content-type)`, (3) URL ends in
`.pdf` or contains `/PDF/` → `PDF (URL)`, (4) else `HTML`. The chosen
signal is recorded in `fetch.log`.

## Consequences

Magic bytes are ground truth — they catch the newsroom-redirect case
and any future regulator that serves PDFs without honest headers.
Content-Type is a server hint, kept as a fast-path. URL pattern is the
weakest signal but useful when we haven't fetched yet (e.g. for the
`/PDF/` skip-warning that no longer fires). **Trade:** we always read
the response body before deciding, even for HTML — but we need the
body anyway, so this is free.
