# ADR-0004 — Prompts as standalone Markdown files; SHA-256 of content as `prompt_version`

- **Status:** Accepted
- **Date:** 2026-04-30

## Context

Prompts are the single most-edited text in the project. They need to
live somewhere that diffs cleanly, renders nicely under code review,
and produces a reproducible identifier so two runs can be compared
exactly.

## Decision

Every agent loads its prompt from a versioned `.md` file (e.g.
`regulations/eu_ai_act/classifier.md`) at call time and records the
SHA-256 of the full file content as `prompt_version` on the
`LLMCallLog`.

## Consequences

Markdown gets syntax highlighting and review-friendly diffs. Hashing
the content (rather than a manual `v1` / `v2` string) means the version
updates automatically when the prompt changes — and two runs are
exactly comparable iff their hashes match. **Trade:** adding a comment
or whitespace-only edit to a prompt file changes `prompt_version`,
which slightly inflates the false-positive rate when comparing
"meaningful" prompt changes. Tolerable for a project at this scale.
