# Attestloop

**Phase: Validate (proof-of-concept).** One end-to-end run against a real EU
regulator publication is preserved in [`docs/example_run/`](docs/example_run/).
A frozen golden set and drift monitoring are not yet in place.

Attestloop is a regulation-agnostic, agent-orchestrated regulatory attestation
pipeline. It ingests a regulator's publication, classifies it, extracts
discrete obligations from the text, and maps each obligation to controls in a
named control framework. Each run writes a self-contained log to disk — no
database, no orchestrator, no web framework.

v1 ships with two configs out of the box:

- **Regulation:** EU AI Act
- **Framework:** NIST AI RMF (full 72-subcategory Core)

Adding a new regulation or framework is a matter of dropping a new config
package under `src/attestloop/regulations/<id>/` or
`src/attestloop/frameworks/<id>/`; nothing in the core pipeline needs to
change.

## Pipeline

```
  ┌──────────┐    ┌────────────┐    ┌───────────┐    ┌─────────┐    ┌──────┐
  │  fetch   │ -> │ classifier │ -> │ extractor │ -> │ mapper  │ -> │ log  │
  │ (URL ->  │    │ (in scope? │    │ (text ->  │    │ (obli-  │    │ (run │
  │ HTML/PDF)│    │  category) │    │ obliga-   │    │ gations │    │ JSON │
  │          │    │            │    │ tions)    │    │ -> ctl) │    │ )    │
  └──────────┘    └────────────┘    └───────────┘    └─────────┘    └──────┘
```

Each agent stage is one Anthropic call with a versioned, regulation-specific
prompt. Inputs and outputs are typed Pydantic models. The fetcher detects
PDFs by magic bytes (then `Content-Type`, then URL) and extracts text via
`pypdf` when the response is binary; otherwise it cleans HTML via
`selectolax`. EUR-Lex CELEX URLs are expanded to the official HTML and PDF
endpoints automatically.

## Agents

- **classifier** — decides whether a fetched publication is in scope for the
  named regulation, and what category of document it is.
- **extractor** — pulls discrete, citeable obligations out of the publication
  body.
- **mapper** — maps each obligation to one or more controls in the chosen
  framework, with a confidence score and reasoning.

## How to run

```bash
uv sync --extra dev
uv run pytest          # 15 schema round-trip tests
cp .env.example .env   # then paste your ANTHROPIC_API_KEY
uv run python -m attestloop.pipeline \
    --regulation eu_ai_act \
    --framework nist_ai_rmf \
    <regulator-publication-url>
```

The pipeline auto-loads `.env` from the current working directory (or any
parent) at startup via `python-dotenv`. If `.env` is missing the loader is a
no-op; if `ANTHROPIC_API_KEY` is still unset after loading, the CLI exits
with code 2 and a clear error pointing at `.env.example`. You can also
export the key directly in your shell.

Exit codes: `0` clean run, `2` missing API key, `3` fetch produced no usable
content (page is JS-rendered, behind a redirect, or returns < 200 chars).

Run logs land in `runs/<run_id>/`. The `runs/` directory itself is
gitignored, but a representative end-to-end run is preserved in
[`docs/example_run/`](docs/example_run/) — classifier / extractor / mapper
logs, fetch trace, full obligation list, control mappings, and the rendered
`report.md` from a real EU AI Act guidelines run.

## First real run

Tagged at
[`v0.1.0-first-real-run`](https://github.com/Product-nomad/attestloop/releases/tag/v0.1.0-first-real-run).

| Metric                     | Value                                                                 |
|----------------------------|-----------------------------------------------------------------------|
| Source document            | Commission Guidelines on prohibited AI practices (C(2025) 5052 final) |
| Fetch path                 | PDF (detected by magic bytes), `pypdf` extraction                     |
| Cleaned text               | 428 902 chars (truncated to 50 000 for the extractor)                 |
| Classifier verdict         | in scope, `guideline`, confidence 0.95                                |
| Obligations extracted      | 18                                                                    |
| Control mappings produced  | 54 (each obligation mapped to up to 3 controls)                       |
| Total cost                 | $0.62                                                                 |
| Wall-clock                 | 5 min 17 s                                                            |
| Models                     | Haiku 4.5 (classifier), Sonnet 4.6 (extractor + mapper)               |

Cost is dominated by mapper calls (≈86 %) — the mapper makes one LLM call
per obligation and ships the full 72-control list with each. Batching with
prompt caching is a known follow-up.

## Status

| Component                                  | Status                              |
|--------------------------------------------|-------------------------------------|
| Pydantic schemas (`schemas.py`)            | ✅ done                             |
| Registry (`registry.py`)                   | ✅ done                             |
| EU AI Act config + classifier/extractor    | ✅ done                             |
| NIST AI RMF config (72 subcategories)      | ✅ done                             |
| `fetch.py` (HTML + PDF, EUR-Lex helpers)   | ✅ done                             |
| `llm.py` (tool-use, retry, cost log)       | ✅ done                             |
| Three agents + pipeline CLI                | ✅ done                             |
| First real-publication end-to-end run      | ✅ done (see `docs/example_run/`)   |
| Frozen golden set                          | 🚧 next                             |
| Drift monitoring (weekly run vs golden)    | 🚧 next                             |
| Chunked extractor (lift 50 K truncation)   | 🚧 backlog                          |
| Mapper batching + prompt caching           | 🚧 backlog                          |
| Threat model (`THREAT_MODEL.md`)           | ✅ done                             |

## Honest scope

Portfolio / proof-of-concept. Not a production compliance product, does not
constitute legal advice, and the obligation extraction is best treated as a
starting point for human review. The first real run truncated its source at
50 000 characters — the 18 obligations therefore come from roughly the first
12 % of the document; the remainder was not seen by the extractor.
