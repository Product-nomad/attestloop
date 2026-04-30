# ADR-0002 — Registry by dynamic import, not entry-points

- **Status:** Accepted
- **Date:** 2026-04-30

## Context

Attestloop needs a way to look up a regulation or framework by id at
CLI invocation time. Options ranged from setuptools entry-points to
`pkg_resources` plugin discovery to a hard-coded dispatch table.

## Decision

`get_regulation(id)` and `get_framework(id)` use `importlib.import_module`
to load `attestloop.regulations.<id>.regulation` and
`attestloop.frameworks.<id>.framework` and read the named module-level
constant.

## Consequences

Zero install-time ceremony — drop a directory under `regulations/` and
it just works. No plugin discovery, no setuptools entry-points, no
`pkg_resources`. **Trade:** unknown ids surface as `ModuleNotFoundError`
rather than a named-registry-miss error, which is acceptable for a
single-author PoC. If we ever publish Attestloop as a library that
third parties extend, we'll revisit.
