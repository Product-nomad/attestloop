# ADR-0013 — NIST AI RMF 1.0 controls embedded in Python

- **Status:** Accepted
- **Date:** 2026-04-30

## Context

The NIST AI RMF 1.0 Core has 72 subcategories. They could live as a
YAML/JSON data file loaded at import, or as Python literals in source.

## Decision

`frameworks/nist_ai_rmf/controls.py` declares all 72 subcategories as
`Control(...)` literals in a single list (`CONTROLS`). The framework
config imports `CONTROLS` and exposes it on `FRAMEWORK.controls`.

## Consequences

Type-checked, easy to grep, diffs cleanly under code review, no chance
of a missing data file at runtime. **Trade:** ~770 lines of dense data
in source. Acceptable for one framework; if we add five more we will
factor out a YAML or CSV loader and supersede this ADR.
