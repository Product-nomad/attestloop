---
title: Costs and latency
status: draft
updated: 2026-04-30
---

| Agent | Model | Calls | Cost (v6) | Mean latency | Notes |
|---|---|---:|---:|---:|---|
| Classifier | Claude Haiku 4.5 | 1 | $0.005 | 3.7 s | |
| Extractor | Claude Sonnet 4.6 | 12 | $0.61 | 20.2 s | Chunked; sequential |
| Mapper | Claude Sonnet 4.6 | ~70 | $0.69 | 11.1 s sequential / 1.4 s effective parallel | 8-way concurrent |
| Critic | Claude Sonnet 4.6 | ~42 | $0.50 | ~10 s | Reviews obligations with mappings <0.80 |
| Clarifier | Claude Haiku 4.5 (delegated) | 0 (typically) | $0.00 | n/a | Only fires on ambiguous classifications |

Total: $2.09 per run, 13 minutes 26 seconds wall-clock, against a 135-page regulator publication producing 71 obligations and 160 mapped controls.

The cost shape is worth comparing. Manual review of the same publication by a senior compliance officer would cost on the order of £500-1000 in analyst time at GRC consultant rates, before any control-mapping work happens. The major incumbent regulatory monitoring tools — OneTrust, Diligent, Wolters Kluwer Enablon — sell their AI-Act monitoring modules at £40,000-150,000 per year flat fee, regardless of how many publications get processed or how few obligations get mapped. A naïve single-call GPT-4 approach against the same document would cost roughly £3-5 per run with no provenance, no confidence handles, no separately-tunable agents, and no audit trail.

Or compare against a v5-equivalent run on the same code: $1.31, 12 minutes 38 seconds. The 60% cost increase from v5 to v6 is entirely the Critic. v6 buys audit-grade second-pass review at that price. The PipelineConfig flags allow switching to v5-equivalent execution at one-third the cost when audit assurance isn't needed.

$2.09 per run is the cost shape of deliberate engineering: Haiku for the classification step that doesn't need Sonnet, prompt caching on the Mapper's redundant controls input, chunked extraction to handle long documents without context-limit failures, parallel Mapper dispatch to keep wall-clock inside the cache window, and a Critic agent that reviews only the obligations where review adds value. Each optimisation came from instrumented measurement, not from guesswork. The 30× return on the prompt cache write specifically is documented in *The iteration story*; it's the largest single cost reduction in the iteration sequence.

The Mapper itself is now 8.13× faster on wall-clock thanks to 8-way concurrent execution. The pipeline as a whole gained only seconds because the Critic — which runs sequentially after the Mapper — adds ~3 minutes of its own work. The bottleneck moved, in other words. The natural next step is parallelising the Critic the same way the Mapper was, which would bring total pipeline wall-clock to roughly 5–7 minutes. That work is tracked as v7 in the GitHub backlog.
