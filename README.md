# Attestloop

**Current version: v2.0.0.** Orchestration release: typed LangGraph state
machine, five LLM-driven agents (Classifier, Extractor, Mapper, Critic,
Clarifier), 8-way concurrent Mapper. The canonical v6 run is preserved at
[`docs/example_runs/v6_clean/`](docs/example_runs/v6_clean/); a like-for-like
v5-equivalent baseline at
[`docs/example_runs/v6_v5_equivalent_clean/`](docs/example_runs/v6_v5_equivalent_clean/).

Attestloop is a regulation-agnostic, agent-orchestrated regulatory attestation
pipeline. It ingests a regulator's publication, classifies it, extracts
discrete obligations from the text, and maps each obligation to controls in a
named control framework. Each run writes a self-contained log to disk — no
database, no web framework. Orchestration is a typed LangGraph StateGraph
in `src/attestloop/orchestration.py`; agent code lives under
`src/attestloop/agents/`.

v2 ships configurations for one regulation (EU AI Act) and one control
framework (NIST AI RMF, full 72-subcategory Core). Adding new regulations
or frameworks is a config drop, not a code change — drop a new package
under `src/attestloop/regulations/<id>/` or
`src/attestloop/frameworks/<id>/`; nothing in the core pipeline needs to
change.

## Pipeline

```
fetch → classify → [in_scope]    → extract → map → critic → report → END
                 → [low_conf_oos] → clarify → [in_scope]      → extract → ...
                                            → [low_conf_oos]  → review_queue → END
                                            → [confident_oos] → out_of_scope → END
                 → [confident_oos] → out_of_scope → END
```

The diagram above is rendered from the compiled LangGraph state machine —
[`scripts/render_graph.py`](scripts/render_graph.py) writes the Mermaid
source to
[`docs/orchestration/v6_pipeline.mmd`](docs/orchestration/v6_pipeline.mmd),
which the site at [attestloop.ai](https://attestloop.ai/) renders
client-side. If the orchestration changes, the diagram regenerates
automatically.

Each agent stage is one or more Anthropic calls with a versioned,
regulation-specific prompt. Inputs and outputs are typed Pydantic models.
The fetcher detects PDFs by magic bytes (then `Content-Type`, then URL) and
extracts text via `pypdf` when the response is binary; otherwise it cleans
HTML via `selectolax`. EUR-Lex CELEX URLs are expanded to the official HTML
and PDF endpoints automatically.

## Agents

- **classifier** — decides whether a fetched publication is in scope for the
  named regulation, and what category of document it is. Haiku 4.5.
- **clarifier** — when the Classifier returns `in_scope=False` at confidence
  &lt; 0.7, augments the input with extra document context (TOC, first 5 pages,
  or section headings) and re-invokes the Classifier. Single-pass loop bound.
- **extractor** — pulls discrete, citeable obligations out of the publication
  body. Sonnet 4.6, chunked at 12 × ~40 K chars with 2 K overlap and
  rapidfuzz-based dedup.
- **mapper** — maps each obligation to zero or more controls in the chosen
  framework, with a confidence score and reasoning. Sonnet 4.6 with prompt
  caching on the controls list, dispatched 8-way parallel.
- **critic** — second-pass review of any obligation whose Mapper output
  includes a mapping below 0.80 confidence. Returns `confirm` or
  `flag_for_review` (advisory; never auto-replaces a mapping). Sonnet 4.6.

## How to run

```bash
uv sync --extra dev
uv run pytest          # tests covering schemas, mapper, orchestration, config, report
cp .env.example .env   # then paste your ANTHROPIC_API_KEY
uv run python -m attestloop \
    --url <regulator-publication-url> \
    --regulation eu_ai_act \
    --framework nist_ai_rmf \
    --config v6
```

`--config v5` switches to the V5_EQUIVALENT preset (serial Mapper, no Critic,
no Clarifier routing) which produces a v5-shape attestation at v5 cost.
`--config v6` (the default) is the canonical orchestration described above.

The pipeline auto-loads `.env` from the current working directory (or any
parent) at startup via `python-dotenv`. If `.env` is missing the loader is a
no-op; if `ANTHROPIC_API_KEY` is still unset after loading, the CLI exits
with code 2 and a clear error pointing at `.env.example`. You can also
export the key directly in your shell.

Exit codes: `0` clean run, `2` missing API key, `3` fetch produced no usable
content (page is JS-rendered, behind a redirect, or returns < 200 chars).

Run logs land in `runs/<run_id>/`. The `runs/` directory itself is
gitignored, but representative end-to-end runs are preserved in
[`docs/example_runs/`](docs/example_runs/) — six versions of the same source
document, including the canonical v6 run and a v5-equivalent baseline.

## Canonical v6 run

Tagged at
[`v2.0.0`](https://github.com/Product-nomad/attestloop/releases/tag/v2.0.0).

| Metric                     | Value                                                                 |
|----------------------------|-----------------------------------------------------------------------|
| Source document            | Commission Guidelines on prohibited AI practices (C(2025) 5052 final) |
| Fetch path                 | PDF (detected by magic bytes), `pypdf` extraction                     |
| Cleaned text               | 428 902 chars (chunked at 12 × ~40 000 with 2 000-char overlap)       |
| Classifier verdict         | in scope, `guideline`, high confidence                                |
| Obligations extracted      | 71 (after rapidfuzz dedup)                                            |
| Control mappings produced  | 160                                                                   |
| Unmapped obligations       | 10                                                                    |
| Critic decisions           | 44 reviewed, 15 flagged for human review                              |
| Total cost                 | $2.09                                                                 |
| Wall-clock                 | 13 min 26 s                                                           |
| Mapper wall-clock          | 1 min 01 s (8-way parallel; 8.13× v5_equivalent baseline)             |
| Models                     | Haiku 4.5 (classifier, clarifier), Sonnet 4.6 (extractor, mapper, critic) |

A like-for-like v5-equivalent baseline (`--config v5`: serial Mapper, no
Critic, no Clarifier routing) on the same code produces 72 obligations,
157 mappings, $1.31 total cost, 12 min 38 s wall-clock — see
[`docs/example_runs/v6_v5_equivalent_clean/`](docs/example_runs/v6_v5_equivalent_clean/).
The 60 % cost increase from v5_eq to v6 is entirely the Critic.

## Project documentation

| File                                                    | What's in it                                                                       |
|---------------------------------------------------------|------------------------------------------------------------------------------------|
| [`README.md`](README.md)                                | This file — overview, how to run, current status.                                  |
| [`CONTEXT.md`](CONTEXT.md)                              | Single source of truth for domain language (Publication, Obligation, etc.).        |
| [`THREAT_MODEL.md`](THREAT_MODEL.md)                    | What Attestloop defends against, what it doesn't, where the soft spots are.        |
| [`docs/adr/`](docs/adr/)                                | Numbered Architectural Decision Records — one file per decision.                   |
| [`DECISIONS.md`](DECISIONS.md)                          | Redirect to `docs/adr/` (kept so `grep DECISIONS` still works).                    |
| [`CHANGELOG.md`](CHANGELOG.md)                          | Keep-a-Changelog history with `[Unreleased]` and tagged releases.                  |
| [`docs/example_runs/`](docs/example_runs/)              | Six per-version snapshots of the same source document with a comparison index.     |
| [`docs/example_runs/v6_clean/`](docs/example_runs/v6_clean/) | Canonical v2.0.0 run.                                                          |
| [`docs/orchestration/v6_pipeline.mmd`](docs/orchestration/v6_pipeline.mmd) | Mermaid source generated from the compiled LangGraph state machine. |
| [`LICENSE`](LICENSE)                                    | Apache 2.0.                                                                        |

## Status

| Component                                                    | Status                                          |
|--------------------------------------------------------------|-------------------------------------------------|
| Pydantic schemas (`schemas.py`)                              | ✅ done                                         |
| Registry (`registry.py`)                                     | ✅ done                                         |
| EU AI Act config + classifier/extractor                      | ✅ done                                         |
| NIST AI RMF config (72 subcategories)                        | ✅ done                                         |
| `fetch.py` (HTML + PDF, EUR-Lex helpers)                     | ✅ done                                         |
| `llm.py` (tool-use, retry, cost log)                         | ✅ done                                         |
| Five agents + pipeline CLI                                   | ✅ done (Classifier, Clarifier, Extractor, Mapper, Critic) |
| Chunked extractor + rapidfuzz dedup                          | ✅ done (v2 → v5)                               |
| Mapper prompt caching                                        | ✅ done (v4)                                    |
| LangGraph orchestration + conditional routing                | ✅ done (v6)                                    |
| Critic agent (advisory second-pass review)                   | ✅ done (v6)                                    |
| Clarifier agent (low-confidence Classifier retry)            | ✅ done (v6)                                    |
| 8-way concurrent Mapper                                      | ✅ done (v6)                                    |
| `PipelineConfig` flag dataclass (V5_EQUIVALENT / V6_CANONICAL) | ✅ done (v6)                                  |
| Canonical v6 run + v5-equivalent baseline                    | ✅ done (see [`docs/example_runs/`](docs/example_runs/)) |
| Threat model (`THREAT_MODEL.md`)                             | ✅ done                                         |
| Architectural decisions (`docs/adr/`)                        | ✅ done (15 ADRs)                               |
| Parallelise the Critic                                       | 🚧 v7 backlog                                   |
| Negative examples in Mapper prompt for Critic-flagged patterns | 🚧 v7 backlog                                 |
| Frozen golden set + quantitative evals                       | 🚧 v7                                           |
| Multi-source watcher                                         | 🚧 v7                                           |
| Multi-framework support (ISO 42001, SOC 2 AI Trust Criteria) | 🚧 v7 backlog                                   |
| Mapper batching                                              | 🚧 v7 backlog                                   |

## Honest scope

Portfolio / research artefact. Not a production compliance product, does not
constitute legal advice, and the obligation extraction is best treated as a
starting point for human review. The Critic's flag rate is uncalibrated
against a labelled gold set — the 33 % observed flag rate is consistent with
reading the flagged obligations and confirming each is a substantive concern,
but that is not the same as measured precision and recall. The Clarifier
rarely fires on real regulator URLs that classify confidently; the synthetic
smoke test in
[`scripts/smoke_clarifier.py`](scripts/smoke_clarifier.py) is the only
production exercise of that code path.
