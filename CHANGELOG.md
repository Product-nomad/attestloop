# Changelog

All notable changes to Attestloop are documented here. Format follows
[Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/).
Versioning is SemVer with descriptive suffixes for milestone tags
(e.g. `v0.1.0-first-real-run`). Pre-1.0, breaking changes can land in any
minor version — they are called out under **Changed** and **Removed**.

## [Unreleased]

### Added
- `LICENSE` (MIT).
- `CONTEXT.md` — single source of truth for domain language.
- `THREAT_MODEL.md` — what Attestloop defends against, what it doesn't,
  and where the soft spots are.
- `DECISIONS.md` — chronological record of v1 architectural choices and
  the rationale for each.
- `CHANGELOG.md` — this file.

### Changed
- `README.md` Status table: Threat model row flipped to ✅.

## [0.1.0-first-real-run] — 2026-04-30

First end-to-end run on a real EU regulator publication. Tagged at
[`72aada7`](https://github.com/Product-nomad/attestloop/commit/72aada7):
the Commission Guidelines on prohibited AI practices (C(2025) 5052
final) yielded 18 obligations and 54 NIST AI RMF mappings in 5 min 17 s
for $0.62. Snapshot preserved at
[`docs/example_run/`](docs/example_run/).

### Added
- Pydantic v2 schemas for `Publication`, `Obligation`, `Control`,
  `ControlMapping`, the three agent input/output pairs, `RunMetadata`,
  and `LLMCallLog`.
- Registry with dynamic-import lookup of regulations and frameworks.
- EU AI Act regulation config (`classifier.md`, `extractor.md`).
- NIST AI RMF 1.0 framework config — full 72-subcategory Core across
  GOVERN, MAP, MEASURE, and MANAGE.
- LLM wrapper using Anthropic tool-use to enforce structured output,
  with per-call cost log to `runs/<run_id>/<agent>.json`.
- Fetcher: HTML via `selectolax`, PDF via `pypdf`. Detection precedence
  is magic bytes → `Content-Type` → URL pattern. Records the chosen
  signal in `runs/<run_id>/fetch.log`.
- EUR-Lex `CELEX:<id>` URL helper that expands to the official HTML and
  PDF endpoints and tries each in order.
- Three agents: classifier (Haiku 4.5), extractor (Sonnet 4.6), mapper
  (Sonnet 4.6, one call per obligation).
- Pipeline CLI: `python -m attestloop.pipeline <url>` with
  `--regulation` / `--framework` defaults to `eu_ai_act` / `nist_ai_rmf`.
- Auto-loading `.env` via `python-dotenv` at pipeline startup.
- Markdown report generation per run, plus a structured
  `run_metadata.json` with cost and token totals.
- Snapshot of the first real end-to-end run preserved at
  `docs/example_run/`.

### Known limitations
- **Extractor truncates source text at 50 000 characters** (~12 % of a
  typical full regulation). Documents larger than that have their
  middle/back unseen by the extractor. Chunked extraction is in the
  backlog.
- **Mapper makes one Anthropic call per obligation** with the full
  controls list each time — no batching, no prompt caching. ≈86 % of
  per-run cost. Batching is in the backlog.
- **No JS rendering.** Single-page apps and lazy-loaded regulator pages
  return `EmptyPublicationError`; user must supply a canonical PDF or
  HTML-only URL.
- **No frozen golden set; no drift monitoring.** A single regulator run
  is preserved as a reference but it is not a regression baseline.
- **No prompt-injection defence** beyond the model's own. Only point
  the pipeline at sources you trust.

[Unreleased]: https://github.com/Product-nomad/attestloop/compare/v0.1.0-first-real-run...HEAD
[0.1.0-first-real-run]: https://github.com/Product-nomad/attestloop/releases/tag/v0.1.0-first-real-run
