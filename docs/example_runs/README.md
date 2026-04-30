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
