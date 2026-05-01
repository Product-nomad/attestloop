# Changelog

All notable changes to Attestloop are documented here. Format follows
[Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/).
Versioning is SemVer with descriptive suffixes for milestone tags
(e.g. `v0.1.0-first-real-run`). Pre-1.0, breaking changes can land in any
minor version — they are called out under **Changed** and **Removed**.

## [Unreleased]

No unreleased changes.

## [2.0.0] — 2026-05-01

Orchestration. The sequential v1 pipeline is replumbed as a typed
LangGraph state machine. Two new LLM-driven agents (Critic, Clarifier)
plus 8-way concurrent Mapper execution. Mapper wall-clock collapses
8.13× against a v5-equivalent baseline; the pipeline-level wall-clock
moves only slightly because the Critic adds ~3 minutes of sequential
review work — the bottleneck moved from Mapper to Critic.

### Added
- LangGraph state machine in `src/attestloop/orchestration.py`. Typed
  `PipelineState`, conditional routing on Classifier confidence,
  single-pass Clarifier loop, fan-in to a unified report node.
- `Critic` agent in `src/attestloop/agents/critic.py`. Reviews any
  obligation whose Mapper output includes at least one mapping below
  0.80 confidence. Decisions are `confirm` or `flag_for_review` —
  advisory only, never auto-replaces a mapping. System prompt at
  `src/attestloop/frameworks/nist_ai_rmf/critic.md`.
- `Clarifier` agent in `src/attestloop/agents/clarifier.py`. When the
  Classifier returns `in_scope=False` at confidence < 0.7, the
  Clarifier extracts additional document context (table of contents,
  first 5 pages, or section headings — whichever is most informative)
  and re-invokes the Classifier on the augmented input. Single-pass
  loop bound: a still-ambiguous re-classification routes to a
  review-queue report rather than retrying.
- Async Mapper execution. 8-way concurrent calls bounded by an
  `asyncio.Semaphore`. In-memory `MapperCallBuffer` (lock-protected)
  collects per-call logs and writes `mapper.calls.json` once after
  `asyncio.gather` completes. Determinism preserved via post-gather
  sort by input obligation order, then descending confidence within
  each obligation. Per-obligation failures captured as `MapperFailure`
  records rather than crashing the run.
- `PipelineConfig` dataclass with feature flags
  (`mapper_concurrency`, `enable_critic`, `enable_clarifier_routing`,
  `critic_confidence_threshold`, `classifier_low_confidence_threshold`).
  `V5_EQUIVALENT` and `V6_CANONICAL` presets. CLI flag `--config v5|v6`
  selects between the two; same code, same prompts, only the
  orchestration toggles change.
- LangGraph-rendered Mermaid pipeline diagram. `scripts/render_graph.py`
  calls `graph.get_graph().draw_mermaid()` on the compiled state
  machine and writes the result to `docs/orchestration/v6_pipeline.mmd`.
  The site renders it client-side via lazy-loaded `mermaid`.
- Snapshots: `docs/example_runs/v6_v5_equivalent_clean/` (v5-equivalent
  baseline under v6 code) and `docs/example_runs/v6_clean/` (canonical
  v6 run). Comparison index in `docs/example_runs/README.md` updated
  with v5_eq and v6 rows plus a "What changed between v5 and v6"
  section that isolates the orchestration impact.
- Site: `PipelineDiagram.astro` renders the Mermaid output (monochrome
  theme overriding Mermaid's defaults). Five LLM agents in expansion
  panels (Classifier, Clarifier, Extractor, Mapper, Critic); four
  passive components in a "Code, not agent" callout. Four-question
  answer cards refreshed from the `v6_clean` snapshot. Numbers table
  extended to seven runs (v1–v5 plus v5_eq and v6). Hero and footer
  bumped to v2.0.0.
- Writeup integrated v6 throughout. New subsections in *Agent
  decomposition* for Critic and Clarifier; new v6 subsection in
  *Pipeline structure* with the auto-generated Mermaid reference and
  the PipelineConfig story; v6 row in iteration story comparison
  table plus a v6 narrative paragraph; new paragraph in *Evals* on
  Critic-as-eval signal; v6 cost table replaces v5 in *Costs and
  latency*; two new v6 anecdotes in *Failure modes*; v7 backlog items
  in *What's next*; v2.0.0 release paragraph in the closing.
- `tests/test_config.py` — six tests covering preset shape,
  graph-build with V5_EQUIVALENT vs V6_CANONICAL, and the
  serial-mapper behaviour at `mapper_concurrency=1`.
- `tests/test_mapper.py` — four tests covering input-order
  preservation, partial-failure handling, semaphore concurrency cap,
  and the public sync wrapper signature.
- `tests/test_report.py` — five tests covering `aggregate_usage()`'s
  dual-naming-scheme support across v1–v5 and v6 snapshots.

### Changed
- `pipeline.py` reduced from 421 lines to 88. Orchestration moved to
  `orchestration.py`; report generation extracted to `report.py`; run
  directory creation extracted to `runs.py`. CLI gains `--url` (the
  positional URL form remains accepted) and `--config v5|v6`.
- Per-call LLM logs renamed from `<agent>.json` to `<agent>.calls.json`
  in `llm.py` and the parallel Mapper. Structured outputs use
  distinctive names (`obligations.json`, `mappings.json`,
  `critic_decisions.json`, `clarifier_output.json`,
  `classification.json` — the last newly written by `classify_node`).
- `aggregate_usage()` reads both naming schemes so historical v1–v5
  snapshots in `docs/example_runs/` keep summing correctly. When a
  directory has both `<agent>.json` and `<agent>.calls.json`, the
  `.calls.json` wins and the legacy file is ignored — never
  double-counted. Structured-output filenames are blocklisted so
  accidental new structured outputs don't get summed as token costs.
- Writeup style: numbered section headings (`## Section N — Title`)
  replaced with title-based (`## Title`). Cross-references between
  sections use italicised section titles rather than numbers. The
  assembled `full.md` rebuilt under v2.0.0 frontmatter.

### Performance
- Mapper wall-clock: 8 min 18 s (sequential) → 1 min 01 s (8-way
  parallel) — 8.13× speedup measured against a v5_equivalent run on
  the same code with `mapper_concurrency=1`. Effective parallelism
  7.61× of the semaphore cap; max in-flight calls observed = 8.
- Pipeline wall-clock: 12 min 38 s (v5_eq) → 13 min 26 s (v6). Net
  change small because the Critic adds ~3 minutes of sequential
  review work; the bottleneck moved from Mapper to Critic.
- Cost: $1.31 (v5_eq) → $2.09 (v6). The 60 % increase is entirely the
  Critic. Use `--config v5` to switch back to v5-equivalent execution
  at v5 cost when audit-grade second-pass review isn't needed.
- Cache hit rate: 91.5 % (v5_eq, sequential) → 86.6 % (v6, parallel).
  Structural cost of cold-start parallelism: the first 8 calls each
  pay the cache write because none can read from a warm cache yet.
  Net cost impact ≈ $0.04/run, well inside the 5 % budget the task
  spec set.

### Known limitations
- Critic flag rate is uncalibrated against a labelled gold set. The
  33 % flag rate on the v6 canonical run is consistent with reading
  the flagged obligations and confirming each is a substantive
  concern, but this is not the same as measured precision and recall.
- Clarifier rarely fires on real-world documents. The synthetic smoke
  test in `scripts/smoke_clarifier.py` is the only production
  exercise of the code path; on the canonical Commission Guidelines
  URL the Classifier returns high-confidence `in_scope` and the
  Clarifier never triggers.
- Critic execution remains sequential. Parallelising it the same way
  the Mapper was is the obvious next optimisation; tracked in v7
  backlog along with negative examples in the Mapper prompt for the
  five recurring failure patterns the Critic has surfaced.

## [1.0.0] — 2026-04-30

First production-ready release. Five-iteration journey from a
50 000-character truncated baseline to a full-document pipeline with
confidence-floored mappings, prompt caching, and fuzzy deduplication.
Canonical v5 run at `docs/example_runs/v5_clean/`: 71 obligations,
154 mappings, 13 unmapped, $1.31 total cost, 17 min 17 s wall-clock
on the Commission Guidelines on prohibited AI practices.

### Added
- `LICENSE` (Apache 2.0).
- `CONTEXT.md` — single source of truth for domain language.
- `THREAT_MODEL.md` — what Attestloop defends against, what it
  doesn't, and where the soft spots are.
- `CHANGELOG.md` — this file.
- `docs/adr/` — 15 numbered Architectural Decision Records, plus an
  index at `docs/adr/README.md`. Captures v1 architectural choices
  and the rationale for each.
- Anthropic prompt caching on the Mapper's controls list. ~7 700-token
  static prefix cached via `cache_control: {"type": "ephemeral"}`.
  v4 measurement: 30× ROI on the cache write cost, 97 % hit rate
  across 67 of 68 calls in a single run.
- Confidence floor 0.75 on Mapper output with explicit empty-list
  support. Eliminates slot-fill ("thematically aligned",
  "broadly related to") that v2 produced; obligations the framework
  doesn't cover surface as a separate "Obligations with no
  high-confidence framework mapping" report section.
- Chunked extraction. Documents are split into 12 ~40 000-character
  chunks with a 2 000-character overlap; the Extractor runs once per
  chunk, then a fuzzy deduplicator (`rapidfuzz.token_set_ratio` at
  threshold 80) merges paraphrased duplicates that span chunk
  boundaries.
- Title fallback. When PDF metadata `/Title` is empty or
  numeric-only, the fetcher scans the first 1 000 chars of cleaned
  body text for the first line that's 30–200 chars, not all-uppercase,
  and contains at least one space. URL-filename fallback preserved as
  last resort.
- Site at [attestloop.ai](https://attestloop.ai/): hero, four-question
  structure, hand-drawn pipeline diagram with click-to-expand panels,
  numbers table tracking v1–v5, writeup at `/writeup`. Astro 5 +
  Tailwind 4, deployed to Cloudflare Pages.
- Engineering writeup covering problem framing, multi-agent
  decomposition, agent-by-agent details, pipeline structure, the
  iteration story, evals, costs and latency, failure modes, and the
  v2 backlog.
- v1 through v5 snapshots in `docs/example_runs/`, with a comparison
  index at `docs/example_runs/README.md`.

### Changed
- Migrated `DECISIONS.md` (flat chronological log) to numbered ADRs
  at `docs/adr/ADR-NNNN-<title>.md` once the project crossed ~10
  entries, per `~/WAYS_OF_WORKING.md` §9. `DECISIONS.md` remains as
  a redirect pointer.
- `README.md` Status table: Threat model row flipped to ✅;
  `docs/adr/` row added at ✅; new "Project documentation" table
  added at the top of the docs section to surface every project-level
  document.
- Mapper prompt heavily iterated: v3 added the confidence floor and
  banned hedging language with examples; v5 added a nudge for
  substantive provider obligations whose only confident mapping was
  to GOVERN-1.1 (the catch-all "legal and regulatory requirements
  involving AI are understood, managed, and documented") so those
  legitimate uses weren't filtered away by the floor.
- Report generator: `_md_nullable_cell` treats `None`, `"null"`,
  `"None"` (case-insensitive), and empty/whitespace strings uniformly
  as missing data, rendering as em-dash. Replaces literal "null"
  cells in v4 reports.

### Removed
- `DECISIONS.md` flat log replaced by `docs/adr/` numbered records.

### Performance
- Final v5 cost: $1.31 per run, 17 min 17 s wall-clock against the
  Commission Guidelines on prohibited AI practices (135 pages,
  ~430 000 cleaned characters).
- v3 → v4 prompt caching reduced run cost from $2.78 to $1.19 (−57 %)
  and wall-clock from 41 min 35 s to 14 min 51 s.

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

[Unreleased]: https://github.com/Product-nomad/attestloop/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/Product-nomad/attestloop/releases/tag/v2.0.0
[1.0.0]: https://github.com/Product-nomad/attestloop/releases/tag/v1.0.0
[0.1.0-first-real-run]: https://github.com/Product-nomad/attestloop/releases/tag/v0.1.0-first-real-run
