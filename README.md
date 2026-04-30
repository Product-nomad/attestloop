# Attestloop

**Phase: Build (v1, portfolio / proof-of-concept).**

Attestloop is a regulation-agnostic, agent-orchestrated regulatory attestation
pipeline. It ingests a regulator's publication, classifies it, extracts
discrete obligations from the text, and maps each obligation to controls in a
named control framework. Each run writes a self-contained log to disk — no
database, no orchestrator, no web framework.

v1 ships with two configs out of the box:

- **Regulation:** EU AI Act
- **Framework:** NIST AI RMF

Adding a new regulation or framework is a matter of dropping a new config
package under `src/attestloop/regulations/<id>/` or
`src/attestloop/frameworks/<id>/`; nothing in the core pipeline needs to
change.

## Pipeline

```
  ┌──────────┐    ┌────────────┐    ┌───────────┐    ┌─────────┐    ┌──────┐
  │  fetch   │ -> │ classifier │ -> │ extractor │ -> │ mapper  │ -> │ log  │
  │ (URL ->  │    │ (in scope? │    │ (text ->  │    │ (obli-  │    │ (run │
  │  HTML)   │    │  category) │    │ obliga-   │    │ gations │    │ JSON │
  │          │    │            │    │ tions)    │    │ -> ctl) │    │ )    │
  └──────────┘    └────────────┘    └───────────┘    └─────────┘    └──────┘
```

Each agent stage is one Anthropic call with a versioned, regulation-specific
prompt. Inputs and outputs are typed Pydantic models.

## Agents

- **classifier** — decides whether a fetched publication is in scope for the
  named regulation, and what category of document it is.
- **extractor** — pulls discrete, citeable obligations out of the publication
  body.
- **mapper** — maps each obligation to one or more controls in the chosen
  framework, with a confidence score and reasoning.

## How to run

This is part 1 of the build. The pipeline isn't wired up yet — only the
schemas, registry, and project skeleton are in place.

```bash
# from the repo root
uv sync --extra dev
uv run pytest
```

Once an `ANTHROPIC_API_KEY` is set, invocation looks like:

```bash
cp .env.example .env  # then paste your ANTHROPIC_API_KEY
uv run python -m attestloop.pipeline \
    --regulation eu_ai_act \
    --framework nist_ai_rmf \
    <regulator-publication-url>
```

The pipeline auto-loads `.env` from the current working directory (or any
parent) at startup via `python-dotenv`. If `.env` is missing the loader is a
no-op; if `ANTHROPIC_API_KEY` is still unset after loading, the CLI exits
with a clear error pointing at `.env.example`. You can also export the key
directly in your shell instead of using `.env`.

Run logs land in `runs/<run_id>/`. The `runs/` directory itself is
gitignored, but a representative end-to-end run is preserved in
[`docs/example_run/`](docs/example_run/) as the canonical example output —
classifier / extractor / mapper logs, fetch trace, full obligation list,
control mappings, and the rendered `report.md` from a real EU AI Act
guidelines run.

## Status

| Component                                | Status     |
|------------------------------------------|------------|
| Pydantic schemas (`schemas.py`)          | ✅ done    |
| Registry (`registry.py`)                 | ✅ done    |
| EU AI Act regulation config              | 🚧 part 2  |
| NIST AI RMF framework config             | 🚧 part 2  |
| `fetch.py`, `llm.py`, `pipeline.py`      | 🚧 part 2  |
| Agents (classifier / extractor / mapper) | 🚧 part 2  |
| Real-publication validation runs         | 🚧 part 3  |

## Honest scope

This is a portfolio / proof-of-concept build. It is not a production
compliance product, does not constitute legal advice, and the obligation
extraction is best treated as a starting point for human review.
