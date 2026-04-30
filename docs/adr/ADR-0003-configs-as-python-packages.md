# ADR-0003 — Regulation and framework configs as Python packages

- **Status:** Accepted
- **Date:** 2026-04-30

## Context

Each regulation and framework has structured metadata (id, name,
prompt-file paths) plus, for frameworks, a typed list of `Control`
objects. Storage options were YAML, JSON, TOML, or Python.

## Decision

Configs live as `regulations/<id>/regulation.py` and
`frameworks/<id>/framework.py` exporting `REGULATION` / `FRAMEWORK`
constants — Python source, not a data file.

## Consequences

`pathlib.Path(__file__).parent / "classifier.md"` resolves prompt paths
cleanly. Type checkers see the shape. Cross-references (e.g.
`framework.controls = CONTROLS`) work without serialisation gymnastics.
**Trade:** non-Python contributors can't author a regulation config.
Acceptable for v1; if we ever onboard non-developer subject-matter
experts as config authors we'll add a YAML loader.
