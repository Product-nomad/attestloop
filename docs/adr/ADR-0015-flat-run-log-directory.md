# ADR-0015 — Run logs as a flat directory of named JSON files

- **Status:** Accepted
- **Date:** 2026-04-30

## Context

Each pipeline run produces several artefacts: the fetched publication,
per-agent LLM call logs, the extractor's obligation list, the mapper's
mappings, the rendered report, run-level metadata, and a fetch trace.
These could nest into per-agent subdirectories or sit flat alongside
each other.

## Decision

Per-run output goes to a flat `runs/<run_id>/` directory containing
`publication.json`, `classifier.json`, `extractor.json`, `mapper.json`,
`mappings.json`, `obligations.json`, `run_metadata.json`, `fetch.log`,
and `report.md`.

## Consequences

Every artefact is grep-able and diffable; `tar -czf run.tar.gz
runs/<run_id>/` ships the whole thing as one file. Cross-run
comparisons (`diff runs/RUN-A/classifier.json runs/RUN-B/classifier.json`)
are trivial. **Trade:** a future chunked-extractor design that wants
per-chunk logs will need a sub-directory; we will cross that bridge
when the chunked extractor lands and supersede this ADR.
