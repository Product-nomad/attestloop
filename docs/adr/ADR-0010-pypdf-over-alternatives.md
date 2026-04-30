# ADR-0010 — `pypdf` over `pdfminer.six` and `pdfplumber`

- **Status:** Accepted
- **Date:** 2026-04-30

## Context

We need to extract text from regulator-published PDFs. The mainstream
options for pure-Python PDF text extraction are `pypdf`,
`pdfminer.six`, and `pdfplumber`.

## Decision

Adopted `pypdf>=4.0` (pinned to `6.10.2` in `uv.lock`).

## Consequences

Single dependency, actively maintained, works as a drop-in for our
use case. **Why not `pdfminer.six`:** known slower; harder API. **Why
not `pdfplumber`:** pulls `pdfminer.six` transitively plus `pillow`;
we don't need its table extraction. **Trade:** `pypdf`'s extracted
text from EU Commission PDFs has stray `EN` prefixes and inconsistent
paragraph breaks (visible in the first run's `cleaned_text[:300]`).
Downstream agents have so far been robust to it; if we need higher
fidelity we'll evaluate `pdfminer.six` per-document, not as a wholesale
swap.
