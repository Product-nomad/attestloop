# Architectural decision records

One file per decision, numbered in chronological order. Numbering makes
supersession visible — when a later ADR overrides an earlier one, the
older entry's status changes from `Accepted` to `Superseded by ADR-NNNN`
and stays in the directory for context.

Migrated from a flat `DECISIONS.md` on 2026-04-30 once the project crossed
~10 entries, per `~/WAYS_OF_WORKING.md` §9.

## Index

| # | Title | Status |
|---|---|---|
| [0001](ADR-0001-pydantic-strict-models.md) | Pydantic v2 with `extra="forbid"` everywhere | Accepted |
| [0002](ADR-0002-dynamic-import-registry.md) | Registry by dynamic import, not entry-points | Accepted |
| [0003](ADR-0003-configs-as-python-packages.md) | Regulation and framework configs as Python packages | Accepted |
| [0004](ADR-0004-prompts-as-markdown-files.md) | Prompts as standalone Markdown files; SHA-256 of content as `prompt_version` | Accepted |
| [0005](ADR-0005-anthropic-tool-use-for-structured-output.md) | Anthropic tool-use to enforce structured output | Accepted |
| [0006](ADR-0006-mapper-one-call-per-obligation.md) | Mapper makes one LLM call per obligation | Accepted |
| [0007](ADR-0007-extractor-50k-char-truncation.md) | Extractor truncates source text at 50 000 characters | Accepted |
| [0008](ADR-0008-fetch-200-char-threshold.md) | 200-character fetch threshold for empty-body detection | Accepted |
| [0009](ADR-0009-pdf-detection-magic-bytes-first.md) | PDF detection precedence: magic bytes > Content-Type > URL | Accepted |
| [0010](ADR-0010-pypdf-over-alternatives.md) | `pypdf` over `pdfminer.six` and `pdfplumber` | Accepted |
| [0011](ADR-0011-python-dotenv-for-env-loading.md) | `python-dotenv` for `.env` loading | Accepted |
| [0012](ADR-0012-model-selection-per-agent.md) | Sonnet 4.6 for extractor + mapper, Haiku 4.5 for classifier | Accepted |
| [0013](ADR-0013-controls-embedded-in-python.md) | NIST AI RMF 1.0 controls embedded in Python | Accepted |
| [0014](ADR-0014-llm-timeout-and-single-retry.md) | 60 s LLM timeout with one retry on transient errors | Accepted |
| [0015](ADR-0015-flat-run-log-directory.md) | Run logs as a flat directory of named JSON files | Accepted |

## Conventions

- **Filename:** `ADR-NNNN-kebab-case-title.md`. Numbers are zero-padded
  to 4 digits; never reused, even after a supersession.
- **Header fields:** `Status`, `Date`, optional `Supersedes` and
  `Superseded by`. Status is `Proposed`, `Accepted`, `Superseded by
  ADR-NNNN`, or `Withdrawn`.
- **Body:** `Context`, `Decision`, `Consequences`. One paragraph each
  is plenty for v1-scale calls; expand only when the decision warrants it.
