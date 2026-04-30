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

### Side note: the run that didn't happen

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
