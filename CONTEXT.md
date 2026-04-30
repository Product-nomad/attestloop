# Attestloop — domain language

Single source of truth for the project's vocabulary. README, code comments,
commit messages, prompt strings, and every per-agent log must use these
terms exactly. Aliases drift; this file picks one and enforces it.

If two project docs disagree, this file wins. Fix the other place.

## Core nouns

| Term | Meaning | Don't say |
|---|---|---|
| **Publication** | A single regulator-published document fetched from a URL. Stored as a `Publication` Pydantic model with `url`, `title`, `raw_html`, `cleaned_text`, `fetched_at`. | "page", "doc", "source" (too generic). |
| **Regulation** | A named legal regime (e.g. EU AI Act). Has a config package at `src/attestloop/regulations/<id>/regulation.py` exporting a `REGULATION` constant. | "law" (some are not laws), "act" (a regulation is a kind of act, not vice versa). |
| **Framework** | A named control framework (e.g. NIST AI RMF). Has a config package at `src/attestloop/frameworks/<id>/framework.py` exporting a `FRAMEWORK` constant. | "standard" (frameworks are not always standards), "controls library". |
| **Obligation** | A discrete, citeable, **binding** requirement extracted from a Publication. Has a stable per-regulation ID prefix (e.g. `EUAIA-OBL-001`). Recitals, definitions, and aspirational language are not obligations. | "requirement" (broader), "rule" (could mean a code-level rule), "clause" (raw text, not the extracted concept). |
| **Control** | A single subcategory entry from a Framework (e.g. `GOVERN-1.1`). Has `id`, `function`, `category`, `subcategory_text`. | "subcategory" (NIST's word; we use Control as the cross-framework term), "requirement" (regulation-side). |
| **Mapping** (or **ControlMapping**) | The link from one Obligation to one Control, with `confidence` ∈ [0, 1] and a one- to three-sentence `reasoning`. Each Obligation gets between one and three Mappings. | "match" (suggests strict equality), "tag" (lossy), "control assignment" (verbose). |
| **Run** | One end-to-end invocation of the pipeline. Identified by `run_id` of the form `YYYYMMDD-HHMMSS`. Writes everything to `runs/<run_id>/`. | "execution", "job" (suggests background queue, which we don't have). |

## The agents

The three pipeline stages. **Lower-case nouns** when used in prose; the
class identifier `Classifier` / `Extractor` / `Mapper` is for code only.

| Agent | One-line role |
|---|---|
| **classifier** | In-scope / out-of-scope decision plus a category for the Publication. |
| **extractor** | Pulls Obligations from Publication text. |
| **mapper** | Maps each Obligation to up to three Controls. |

## Verdicts and states

| Term | Meaning |
|---|---|
| **In scope** | `ClassifierOutput.in_scope == True`. The pipeline proceeds to extractor and mapper. |
| **Out of scope** | `ClassifierOutput.in_scope == False`. Extractor and mapper are skipped; a short report is still written. |
| **Category** | One of `regulation`, `guideline`, `amendment`, `press_release`, `other`. Set by the classifier on every Run, in-scope or not. |
| **Confidence** | A float in `[0, 1]` set by the classifier (on its verdict) and by the mapper (on each Mapping). Not a probability — it's the model's own assessment. |

## Provenance and reproducibility

| Term | Meaning |
|---|---|
| **Prompt version** | SHA-256 of the prompt markdown file's full content, recorded on every `LLMCallLog`. Two Runs with the same `prompt_version` for an agent used the same prompt text. |
| **Fetch path** | Which detection signal in `fetch.py` decided how to parse the response: `PDF (magic bytes)`, `PDF (content-type)`, `PDF (URL)`, or `HTML`. Recorded in `fetch.log` for each Run. |
| **Source kind** | Synonym for fetch path (the value written after `# Source:` in `fetch.log`). |

## External identifiers

| Term | Meaning |
|---|---|
| **CELEX** | EU's stable identifier scheme for legal documents (e.g. `32024R1689` = Regulation (EU) 2024/1689). The fetcher recognises CELEX in EUR-Lex URLs and expands to the official HTML and PDF endpoints. |
| **Regulator publication URL** | The user-supplied URL pointing at one document. May land on an HTML page, a PDF, or a redirect to either. |

## Things to never call them

- **"Compliance"** as a verb or product noun. Attestloop does not certify
  compliance; it produces evidence a human reviews. Use **"attestation"**
  for the artefact and **"compliance"** only when quoting external sources.
- **"AI agent"** for the pipeline as a whole. Each stage is a single LLM
  call, not a looping autonomous agent. Use **"agent"** strictly for the
  three named stages (classifier / extractor / mapper).
- **"Recommendation"** for a Mapping. The mapper proposes a Control link
  with stated confidence; calling it a recommendation overstates authority.
