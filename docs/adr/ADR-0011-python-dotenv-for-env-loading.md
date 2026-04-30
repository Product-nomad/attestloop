# ADR-0011 — `python-dotenv` for `.env` loading

- **Status:** Accepted
- **Date:** 2026-04-30

## Context

The CLI needs an `ANTHROPIC_API_KEY` from somewhere. Pure-environment
loading (i.e. requiring the user to `export` it) makes the
auto-resume-after-reboot story brittle for a systemd-driven box. A
`.env` file is the de-facto standard but parsing one is full of edge
cases (quoting, escaping, comments).

## Decision

Added `python-dotenv>=1.0.1` and call `load_dotenv()` as the first
action of `pipeline.main()`, before argparse and before any Anthropic
client construction. No-op when `.env` is absent. Fail-fast with exit
code `2` if `ANTHROPIC_API_KEY` is still unset after loading.

## Consequences

`.env` file living next to the project root works without ceremony;
`export ANTHROPIC_API_KEY=…` in the shell still works as before; the
pipeline never starts an Anthropic call without a key. **Trade:** one
extra dependency. The library is small, has no security surface
beyond what we already accept, and is widely used.
