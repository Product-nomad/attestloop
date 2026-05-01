---
title: Costs and latency
status: draft
updated: 2026-04-30
---

| Agent | Model | Calls | Cost (v5) | Mean latency |
|---|---|---:|---:|---:|
| Classifier | Claude Haiku 4.5 | 1 | $0.005 | 3.7 s |
| Extractor | Claude Sonnet 4.6 | 12 | $0.61 | 20.2 s |
| Mapper | Claude Sonnet 4.6 | 71 | $0.69 | 11.1 s |

Total: $1.31 per run, 17 minutes wall-clock, against a 135-page regulator publication producing 71 obligations and 154 mapped controls.

The cost shape is worth comparing. Manual review of the same publication by a senior compliance officer would cost on the order of £500-1000 in analyst time at GRC consultant rates, before any control-mapping work happens. The major incumbent regulatory monitoring tools — OneTrust, Diligent, Wolters Kluwer Enablon — sell their AI-Act monitoring modules at £40,000-150,000 per year flat fee, regardless of how many publications get processed or how few obligations get mapped. A naïve single-call GPT-4 approach against the same document would cost roughly £3-5 per run with no provenance, no confidence handles, no separately-tunable agents, and no audit trail.

$1.31 per run is the cost shape of deliberate engineering: Haiku for the classification step that doesn't need Sonnet, prompt caching on the Mapper's redundant controls input, chunked extraction to handle long documents without context-limit failures. Each optimisation came from instrumented measurement, not from guesswork. The 30× return on the prompt cache write specifically is documented in *The iteration story*; it's the largest single cost reduction in the iteration sequence.

Latency is the v1 limitation that v6's parallel Mapper execution will close. 71 sequential Sonnet calls at ~11 seconds each accounts for most of the 17-minute wall-clock. Eight-way concurrent execution would reduce that to roughly 2 minutes of Mapper work, leaving Extraction as the new dominant cost.
