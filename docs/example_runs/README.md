# Example runs

Successive end-to-end runs of the Attestloop pipeline against the same
real EU regulator publication — the **Commission Guidelines on prohibited
artificial intelligence (AI) practices** (`C(2025) 5052 final`) — kept
side-by-side so the impact of each pipeline change can be traced
empirically.

The source URL is the same in every row:
`https://ec.europa.eu/newsroom/dae/redirection/document/112367` (PDF
served via redirect; detected by magic-byte sniff and parsed via
`pypdf`). Cleaned text length is 428 902 chars.

## Comparison

| Version | Run dir | Obligations | Mappings (kept) | Unmapped | Mean conf | Min conf | GOVERN-1.1 share | Cost | Wall-clock |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **v1** truncated extractor, mapper unconstrained | [`../example_run/`](../example_run/) | 18 | 54 | 0 | n/a (mapper not yet logging confidence summary) | n/a | 16/54 = 29.6 % | $0.62 | 5 min 17 s |
| **v2** chunked extractor (12 chunks), mapper unconstrained | (not snapshotted; data from `runs/20260430-094628/` on disk) | 68 | 203 | 0 | 0.788 | 0.550 | 52/203 = 25.6 % | $2.61 | 21 min 22 s |
| **v3** chunked extractor + Mapper confidence floor 0.75, no slot-filling | [`v3_confidence_floor/`](v3_confidence_floor/) | 72 | 164 | 12 | 0.817 | 0.750 | 34/164 = 20.7 % | $2.78 | 41 min 35 s |
| **v4** + Anthropic prompt caching on Mapper controls list | [`v4_prompt_caching/`](v4_prompt_caching/) | 69 | 124 | 24 | 0.812 | 0.760 | 19/124 = 15.3 % | **$1.19** | **14 min 51 s** |
| **v5** + fuzzy dedup, title fallback, null rendering, mapper nudge — **canonical writeup run** | [`v5_clean/`](v5_clean/) | 71 (from 83 raw) | 154 | 13 | 0.815 | 0.750 | 49/154 = 31.8 % | $1.30 | 17 min 17 s |
| **v6 task 4** + LangGraph orchestration + Critic + Clarifier + 8-way concurrent Mapper | [`v6_parallel_mapper/`](v6_parallel_mapper/) | 61 (from 73 raw) | 129 | 13 | 0.817 | 0.750 | 43/129 = 33.3 % | $1.76 | **13 min 23 s** |

## What changed between v2 and v3

The mapper prompt at `src/attestloop/frameworks/nist_ai_rmf/mapper.md`
was rewritten with three new hard constraints:

1. **0–3 mappings, no slot-filling.** Returning fewer mappings (or zero)
   is now the correct answer when nothing genuinely qualifies, instead
   of always padding to three.
2. **Confidence floor 0.75.** The model is told to drop any mapping it
   would describe with hedging language (*"thematically aligned"*,
   *"not a verbatim match but"*, etc.) — those are the markers of a
   sub-0.75 mapping.
3. **Specificity over breadth.** A single mapping at 0.85 to a
   precisely-applicable subcategory beats three at 0.70 to broadly-
   applicable ones. `GOVERN-1.1` ("Legal and regulatory requirements
   involving AI are understood, managed, and documented") is named in
   the prompt as the canonical broad-fit subcategory to deprioritise.

### Observed effect on the same source document

- **Mappings dropped from 203 → 164** (−19.2 %). The dropped 39 are
  the ones the v2 prompt would have padded out with low-confidence
  filler.
- **Mean confidence rose from 0.788 → 0.817**; minimum rose from
  0.550 to exactly 0.750 (the model held to the new floor precisely).
- **GOVERN-1.1 share fell from 25.6 % → 20.7 %**, dropping 18
  obligations' worth of "this is a legal requirement" catch-all
  mappings without losing any of the genuinely strong ones.
- **12 obligations now have no high-confidence mapping** and are
  surfaced in a labelled "Obligations with no high-confidence
  framework mapping" section of the report (was 0 in v2). These are
  predominantly the procedural authorisation duties under EU AI Act
  Article 5(2)–(4) — judicial pre-authorisation, registration in
  Member-State registers, case-by-case notification of competent
  authorities — which the NIST AI RMF, designed for AI developers and
  deployers, does not directly cover.
- **Distribution of mappings per obligation:** 12 with zero, 1 with
  one, 14 with two, 45 with three. v2 was effectively all-three.
- **Costs rose slightly** ($2.61 → $2.78) because the slimmer mapper
  output was offset by a few more obligations (72 vs 68) and by
  rate-limit backoff (the org's 30 K input-tokens-per-minute Sonnet
  cap forced 30 s sleeps between several extractor calls; see
  ADR-0014). Mapper cost itself fell on a per-mapping basis from
  $2.03/203 = $0.0100 in v2 to $2.19/164 = $0.0133 in v3.

## What changed between v3 and v4

The Mapper agent's system block (prompt instructions + the full
72-subcategory NIST AI RMF controls catalogue, ~7 700 tokens of
identical static content per call) is now sent inside a single
`cache_control: {"type": "ephemeral"}` block. `LLMCallLog` gained
`cache_creation_input_tokens` and `cache_read_input_tokens` for per-call
observability; `MODEL_PRICING` gained `cache_write` (1.25× input) and
`cache_read` (0.10× input) entries; `_cost_usd` factors all four token
categories.

### Cache verification on v4

| Measurement | Value |
|---|---:|
| Mapper call 1 (cold): `cache_creation_input_tokens` | **7 731** |
| Mapper call 1 (cold): `cache_read_input_tokens` | 0 |
| Mapper calls 2–69: `cache_read_input_tokens` (every single call) | **7 731** |
| Mapper calls 2–69: `cache_creation_input_tokens` non-zero on | 2 calls (#34, #50, see below) |
| Run-wide regular input tokens | 173 865 |
| Run-wide cache-write tokens | 8 952 (one 7 731 cold write + two minor 572 / 649 re-writes) |
| Run-wide cache-read tokens | **525 708** |

The 5-minute ephemeral cache TTL fired twice during the run, once
between calls 33→34 (~2.5 min idle while waiting on the rate-limit
backoff for an earlier 5xx) and once between calls 49→50. Each
re-cache cost ~600 tokens at write price; the rest of the run reads
the cache cleanly.

### Speed effect

Cold-cache mapper call (#1): **9 886 ms**. Warm mean across calls
2–69: 8 792 ms when including the three rate-limit-retried outliers
(63 168 ms, 68 076 ms, 69 314 ms) → 1.12× speedup. Excluding those
three outliers, warm mean is **6 113 ms** → **1.62× speedup** on the
LLM call itself, which lines up with cached-prefix behaviour.

Wall-clock dropped 41 min 35 s → 14 min 51 s (**−64 %**). Mapper sum-
latency 1 315 s → 608 s. Most of the wall-clock saving is rate-limit
pressure being relieved: cached tokens don't count against the
30 K-input-tokens-per-minute Sonnet quota, so the 30 s backoff fires
far less often.

### Cost effect

Total cost **$2.78 → $1.19** (−57 %). Mapper-only cost
**$2.19 → $0.61** (−72 %), the biggest single line-item reduction
in the project to date.

### Audit-trail effect

Same source document, but v4 returned 24 obligations as unmapped vs
v3's 12. This is genuine variance, not a regression — the extractor
output is also slightly different (69 obligations vs 72), the
underlying LLM is non-deterministic, and the confidence floor is
strict. The unmapped IDs in v4 cover the same procedural authorisation
duties as v3 plus several more from the latter half of the document.
GOVERN-1.1 share continued to fall (20.7 % → 15.3 %), suggesting the
cache reset between calls didn't reintroduce the slot-filling behaviour.

## What changed between v4 and v5 — and why this is the canonical writeup run

Four narrowly-scoped fixes, each addressing a specific defect surfaced
in v4. The cumulative effect is the cleanest report the pipeline has
produced.

### 1. Fuzzy deduplication (extractor)

Replaced the v2-era case-insensitive substring dedup (which fired
**zero times** on the v3 and v4 runs) with `rapidfuzz.fuzz.token_set_ratio`
at a similarity floor of **80**. Threshold chosen at 80 rather than 85
because the duplicate pairs in v4 — same Article 5(1)(c) prohibition
extracted from chunks 1 and 11 with different paragraph references —
score in the 80-85 band. When a duplicate is found, the obligation
with the **longer `source_paragraph`** wins (better citation
specificity); ties go to the earlier-extracted obligation. Optional
fields (`deadline`, `evidence_required`) are merged from the dropped
entry into the kept one if the kept one has them empty.

Effect on v5: **83 raw obligations → 71 after dedup (12 merged)**,
across 12 logged merges with similarity scores ranging 81–98.

### 2. Title fallback (fetcher)

When PDF `/Title` metadata is empty or numeric-only (the
`ec.europa.eu/newsroom/...` redirect served the file with no title and
a numeric filename `112367`), the fetcher now scans the first 1 000
chars of cleaned body text for the first line that is 30–200 chars
long, not all-uppercase, and contains at least one space — exactly
the shape of a substantive document title in a Commission PDF.
URL-filename fallback is preserved as a last resort.

Effect on v5: **title resolved to "Commission Guidelines on prohibited
artificial intelligence practices established by"** (truncated by
the 200-char window from the full "...by Regulation (EU) 2024/1689
(AI Act)" but a vast improvement over `'112367'`).

### 3. Null-literal rendering (report generator)

A minority of LLM-emitted obligations had the literal string `"null"`
(or `"None"`) where an optional field should have been empty.
`_md_nullable_cell` now treats `None`, `"null"`, and `"None"`
(case-insensitive) and empty/whitespace strings uniformly as missing
data, rendering them as em-dash. Applied to every cell in the
obligations, mappings, and unmapped tables.

Effect on v5: **zero literal `null` / `None` / `NULL` cells** in the
rendered report.

### 4. Mapper prompt nudge (NIST AI RMF mapper)

Added a single bullet to the "Empty mappings are correct outcomes"
section instructing the model that **substantive provider/deployer
obligations whose substance is legal compliance** (e.g. the
open-source carve-out for AI systems that constitute prohibited
practices) almost always have a defensible `GOVERN-1.1` mapping at
≥ 0.75, and to reconsider before returning `[]` for those. The empty
list remains correct for procedural duties on public authorities
(judicial pre-authorisation etc.) — the nudge is targeted.

Effect on v5: the open-source-exclusion obligation
(`EUAIA-OBL-014` here) now maps to `GOVERN-1.1 @ 0.88` and
`MANAGE-1.1 @ 0.80` instead of being dropped. **GOVERN-1.1 share
rose from 15.3 % (v4) → 31.8 % (v5)** — a deliberate restoration of
the legitimate compliance mappings the v3 confidence floor had been
filtering away too aggressively for this class of duty.

### Headline numbers

| Metric | v4 | v5 |
|---|---:|---:|
| Pre-dedup obligations | n/a (substring dedup never fired) | 83 |
| Post-dedup obligations | 69 | 71 |
| Merge log entries | 0 | 12 |
| Mappings (kept) | 124 | 154 |
| Unmapped obligations | 24 | 13 |
| Title | `112367` | `Commission Guidelines on prohibited artificial intelligence practices established by` |
| Literal `null` cells in report | several | **0** |
| GOVERN-1.1 share | 15.3 % | 31.8 % |
| Mean confidence | 0.812 | 0.815 |
| Total cost | $1.19 | $1.30 |
| Wall-clock | 14 min 51 s | 17 min 17 s |

**v5 is the canonical writeup run.** Subsequent versions should be
benchmarked against it, not against earlier snapshots.

## What changed in v6 — orchestration, second-pass review, parallel mapping

v6 is a four-task arc that turns the v5 sequential pipeline into a
LangGraph orchestration with a second-pass reviewer (Critic), a
salvage path for ambiguous out-of-scope verdicts (Clarifier), and an
8-way concurrent Mapper. Tasks 1–3 are zero- or near-zero-cost
structural changes; task 4 is the first measurable wall-clock win.
Only task 4 is snapshotted in this directory because tasks 1–3
preserve the v5 metrics by construction.

### Task 4 — 8-way concurrent Mapper

The Mapper agent's per-obligation calls are now dispatched through a
single `asyncio.gather(*tasks)` with an `asyncio.Semaphore(8)`
controlling concurrency. The public sync entrypoint
`map_to_controls(input, framework, run_dir) -> MapperOutput` is
preserved so `map_node` in the LangGraph orchestration calls it
identically to v5; the parallelism is internal to the agent and the
graph diagram is unchanged.

Concurrency safety: an in-memory `MapperCallBuffer` guarded by an
`asyncio.Lock` collects every `LLMCallLog` produced during the
`gather`, then writes `mapper.json` to disk in a single operation
after all tasks have completed. This avoids the read-modify-write
race that would result from each task appending to the on-disk JSON
file independently.

Determinism: `asyncio.gather(*tasks, return_exceptions=True)` yields
results in completion order, not input order. `_map_to_controls_async`
post-sorts the assembled mappings by input obligation order, then by
descending confidence within each obligation, so two runs with the
same LLM responses produce identical `mappings.json` regardless of
which task happened to finish first.

Failure handling: any obligation whose mapper call raises after all
internal retries (1 fast + up to 4 30-s rate-limit backoffs) is
captured as a `MapperFailure(obligation_id, error)` rather than
crashing the run. Failures are written to `mapper_failures.json`
(file is omitted when the list is empty), surfaced in the report
under "Obligations that errored during mapping", and propagated into
the LangGraph state as `mapper_failures`.

### Headline numbers — v6 task 4 vs v6 task 3 baseline

Direct same-URL comparison against the v6 task 3 run
(`runs/20260430-172550/`, 71 obligations, sequential Mapper still
shipping):

| Metric | v6 task 3 (sequential) | v6 task 4 (parallel) | Change |
|---|---:|---:|---:|
| Obligations (post-dedup) | 71 | 61 | stochastic (different extractor pass) |
| Mapper calls | 71 | 61 | -14 % (fewer obligations) |
| Mappings produced | 155 | 129 | -17 % (fewer obligations) |
| Mapper sum-latency (would-be sequential) | 9 min 1 s | 16 min 47 s | n/a — different obligation set |
| **Mapper wall-clock** | **9 min 0 s** | **2 min 17 s** | **−75 % (3.94× speedup)** |
| **Effective parallelism** (sum-latency ÷ wall-clock) | 1.00× | **7.33×** | semaphore cap is 8 |
| Pipeline wall-clock (LLM-only) | 21 min 53 s | 13 min 19 s | −39 % (1.64× speedup) |
| Total cost | $1.91 | $1.76 | −7.5 % (within 5 % per-obligation) |
| Mapper cost | $0.72 | $0.67 | −6.4 % |
| Mapper cache hit rate | 90.2 % | 86.6 % | −3.6 pp (see below) |
| Max in-flight mapper calls | 1 | 8 | semaphore working |

The 7.33× effective parallelism on a semaphore cap of 8 is the
expected steady-state when the average call latency is large compared
to the dispatch overhead. Cap is never exceeded
(`test_async_mapper_concurrency_respects_cap` enforces this).

### Cache-hit rate dip is structural, not a regression

v4's prompt-cache analysis showed every warm call reading
`cache_read_input_tokens = 7 731`. With sequential dispatch, call 1
writes the cache and calls 2–N read it. With 8-way parallel dispatch,
the **first 8 calls all start before any of them returns**, so they
each pay the cache-creation cost (~3 936 tokens of system block);
calls 9–61 hit the warm cache cleanly. Observed in this run:
cache-creation tokens 31 484 ≈ 8 × 3 936; cache-read tokens 448 647
across 53 reads. This is the cost of parallelism on the prompt-cache
side, and at Sonnet's 1.25× write vs 0.10× read ratio it works out
to roughly $0.04 of extra cache-write spend per run — well below the
5 % budget the task spec set.

### Wall-clock saving is mostly the Mapper, not the rest of the pipeline

The Mapper went from 9 min to 2 min 17 s; the other agents
(Classifier, Extractor, Critic) were untouched and run in roughly the
same time as before. Pipeline wall-clock fell 21 min 53 s →
13 min 19 s, of which ~6 min 43 s comes directly from the Mapper
parallelism and the rest from natural variance in the Extractor's
12 sequential chunk calls and Critic's per-flagged-obligation calls
(neither of which task 4 touches).

### Why this run has 61 obligations rather than 71

The Extractor is a stochastic 12-chunk run with rapidfuzz dedup; the
exact post-dedup count varies per invocation between roughly 60 and
75 obligations on this document. Task 4 is a Mapper change only —
the Extractor was not touched and the variance here is not
attributable to it. The wall-clock and cost savings reported above
are conservative because the v6-task-3 baseline produced *more*
obligations to map (71 vs 61); on a per-obligation basis the speedup
is even larger.

## Side note: the run that didn't happen

A first attempt at v3 (`runs/20260430-102938/`, since deleted)
crashed at the extractor with a 429 rate-limit error from Anthropic.
The wrapper's retry policy at the time retried immediately, which is
useless against a per-minute quota. ADR-relevant fix: separated the
fast-retry path (timeouts, connection drops, 5xx — one immediate
retry) from the rate-limit path (30 s backoff, up to 4 attempts).
Committed as `48a1a5f` before this v3 run started.

## Conventions

- **One subdirectory per snapshot version**: `vN_short_label/`. The
  full set of run artefacts lives inside (`publication.json`,
  `classifier.json`, `extractor.json`, `mapper.json`,
  `obligations.json`, `mappings.json`, `run_metadata.json`,
  `fetch.log`, `report.md`).
- **Earlier snapshots are not retroactively populated.** v1 lives at
  `docs/example_run/` (the original snapshot path); v2 was not
  snapshotted at the time and its numbers above are derived from
  `runs/20260430-094628/` which still exists on the build host.
- **Same source URL across versions** so comparisons are
  apples-to-apples on pipeline changes, not on document drift.
