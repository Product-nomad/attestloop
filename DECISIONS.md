# Architectural decisions

One paragraph per decision, dated, in chronological order. Records the
*why* so the same call doesn't get re-litigated. Per
`~/WAYS_OF_WORKING.md` §9: when this file crosses ~10 decisions or starts
having superseded entries, migrate to `docs/adr/ADR-NNNN-title.md`. We're
already at ~14 — migration is on deck.

## 2026-04-30 — Pydantic v2 with `extra="forbid"` everywhere

Every domain model declares `model_config = ConfigDict(extra="forbid")`.
The cost is a small amount of boilerplate; the benefit is that schema
mismatches between the LLM's tool output and our model fail at parse
time with a clear `ValidationError` rather than silently dropping fields
into oblivion. Confidence floats are also bounded `Field(ge=0.0, le=1.0)`
so a model returning `1.5` is caught at the boundary.

## 2026-04-30 — Registry by dynamic import, not entry-points

`get_regulation(id)` and `get_framework(id)` use `importlib.import_module`
to load `attestloop.regulations.<id>.regulation` and
`attestloop.frameworks.<id>.framework`. **Why:** zero install-time
ceremony — drop a directory under `regulations/` and it just works. No
plugin discovery, no setup-tools entry-points, no `pkg_resources`.
**Trade:** unknown ids surface as `ModuleNotFoundError` rather than a
named-registry-miss, which is acceptable for a single-author PoC.

## 2026-04-30 — Regulation and framework configs as Python packages

Configs live as `regulations/<id>/regulation.py` and
`frameworks/<id>/framework.py` exporting `REGULATION` / `FRAMEWORK`
constants — not YAML, not JSON. **Why:** `pathlib.Path(__file__).parent /
"classifier.md"` resolves prompt paths cleanly; type checkers see the
shape; cross-references (e.g. `framework.controls = CONTROLS`) work
without serialisation gymnastics. **Trade:** non-Python contributors
can't author a regulation config. Acceptable for v1.

## 2026-04-30 — Prompts as standalone Markdown files, SHA-256 as `prompt_version`

Every agent loads its prompt from a versioned `.md` file at call time and
records the SHA-256 of the content as `prompt_version` on the
`LLMCallLog`. **Why:** prompts are the most-edited text in the project
and benefit from Markdown rendering, syntax highlighting, and review-
friendly diffs. Hashing the content (rather than a manual `v1`/`v2`
string) means the version updates automatically when the prompt changes
and two runs are exactly comparable iff their hashes match.

## 2026-04-30 — Anthropic tool-use to enforce structured output

Every LLM call defines exactly one tool whose `input_schema` is the
output Pydantic model's `model_json_schema()`, with
`tool_choice={"type": "tool", "name": ...}` forcing the call. **Why:**
tool-use is the most reliable structured-output path in the Anthropic
API as of model 4.6 — more reliable than JSON-mode prompting, and the
schema validation happens server-side. **Trade:** we lose the ability to
get a chain-of-thought prelude before the structured output; for the
three current agents we don't need one.

## 2026-04-30 — Mapper makes one LLM call per obligation (no batching, no caching)

The mapper iterates obligations and ships the full 72-control list with
each call. **Why this for v1:** simplest possible code path; per-call
logs are easy to audit; one obligation's mapping failure doesn't take
down the rest. **Cost reality:** on the first real run this was 86% of
spend ($0.54 of $0.62). **Follow-up planned:** batch N obligations per
call with prompt caching on the controls list — likely 5–10× cost
reduction, deferred so that v1 ships.

## 2026-04-30 — Extractor truncates source text at 50 000 characters

`agents/extractor.py` truncates `cleaned_text[:50_000]` with a `rich`
warning. **Why:** keeps the extractor's prompt under Sonnet's
working-context comfort zone, keeps cost predictable, ships v1.
**Trade:** documents larger than ~12 % of 50 K chars (i.e. most full
regulations) only get their first chunk seen. The first real run
truncated the Commission Guidelines (429 K chars → 50 K), so its 18
obligations come from the front matter. Chunked extraction is in the
backlog.

## 2026-04-30 — 200-character fetch threshold for empty-body detection

`fetch.py` raises `EmptyPublicationError` if no candidate URL produces
≥ 200 chars of stripped, usable text. **Why 200:** distinguishes
"page rendered but is genuinely tiny" (e.g. a brief notice) from
"page is JS-only / fetch returned empty body" (zero or near-zero chars).
A regulator's own brief notices reliably exceed 200 chars; SPA shells
without rendered content reliably don't. CLI exits with code `3` so
callers can branch on it.

## 2026-04-30 — PDF detection precedence: magic bytes > Content-Type > URL

`fetch.py` decides whether to route a response to `pypdf` in this strict
order: (1) `content[:5] == b"%PDF-"` → `PDF (magic bytes)`, (2)
`Content-Type: application/pdf` → `PDF (content-type)`, (3) URL ends in
`.pdf` or contains `/PDF/` → `PDF (URL)`, (4) else `HTML`. **Why this
order:** magic bytes are ground truth — a Commission redirect URL with
no extension and no `application/pdf` header (the
`ec.europa.eu/newsroom/dae/redirection/document/112367` case) was
mis-detected as HTML in the previous version, with selectolax dumping
911 KB of binary into the classifier prompt. Magic-byte sniffing
catches that cleanly. The decision signal is recorded in `fetch.log` so
future failures are debuggable.

## 2026-04-30 — `pypdf` over `pdfminer.six` and `pdfplumber`

Single dependency, actively maintained (one major release since
the `>=4.0` constraint we set), works as a drop-in for our use case.
**Why not `pdfminer.six`:** known slower; harder API. **Why not
`pdfplumber`:** pulls `pdfminer.six` transitively plus `pillow`; we
don't need table extraction. **Trade:** `pypdf`'s extracted text from
EU Commission PDFs has stray `EN` prefixes and inconsistent paragraph
breaks; downstream agents have so far been robust to it.

## 2026-04-30 — `python-dotenv` for `.env` loading

`load_dotenv()` runs as the first action of `pipeline.main()`, before
argparse and before any Anthropic client construction. No-op when `.env`
is absent. **Why a library, not a hand-rolled parser:** `.env` is a
de-facto standard with edge cases (quoting, escaping, comments) and the
library is one transitive dep with no security surface beyond what we
already have. Alternative considered: relying purely on shell `export`,
rejected because it makes the auto-resume-after-reboot story brittle.

## 2026-04-30 — Sonnet 4.6 for extractor + mapper, Haiku 4.5 for classifier

Classifier needs cheap, fast, decent reasoning over a snippet → Haiku
4.5. Extractor and mapper need stronger reasoning over longer text and
must hit a tight schema → Sonnet 4.6. **Cost shape on the first real
run:** classifier $0.005, extractor $0.082, mapper $0.537. Re-evaluate
when Haiku 5 lands (likely strong enough for the extractor) and when
Sonnet caching matures (would shift the mapper economics).

## 2026-04-30 — NIST AI RMF 1.0 controls embedded in Python

`frameworks/nist_ai_rmf/controls.py` declares all 72 subcategories as
`Control(...)` literals in a single list. **Why not a YAML/JSON file
loaded at import:** the Python literal is type-checked, easy to grep,
diffs cleanly under code review, and there is no chance of a missing
file at runtime. **Trade:** ~770 lines of dense data in source.
Acceptable for one framework; if we add five more we'll factor out a
loader.

## 2026-04-30 — 60 s LLM timeout with one retry on transient errors

`call_with_logging` sets `timeout=60.0` on the Anthropic client and
retries exactly once on `APITimeoutError`, `APIConnectionError`,
`RateLimitError`, or `InternalServerError`. **Why one:** covers the
common flake without masking real failures. **Why not exponential
backoff:** for v1 the agents are sequential and a real outage should
fail loudly so the user notices; the cost of an extra retry is one
duplicate API call.

## 2026-04-30 — Run logs as a flat directory of named JSON files

Per-run output goes to `runs/<run_id>/{publication.json,
classifier.json, extractor.json, mapper.json, mappings.json,
obligations.json, run_metadata.json, fetch.log, report.md}`. **Why
flat:** every artefact is grep-able and diffable; no nested directory
gymnastics; `tar -czf run.tar.gz runs/<run_id>/` ships the whole thing.
**Trade:** a future `chunked-extractor` design that wants per-chunk logs
will need a sub-directory; cross that bridge then.
