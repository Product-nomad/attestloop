---
section: 5
title: Iteration
status: draft
updated: 2026-04-30
---

Five runs are preserved in the repo at docs/example_runs/v1 through v5. Each is a full snapshot of a real pipeline execution against the Commission Guidelines on prohibited AI practices, the 135-page Communication published 4 February 2025. Each iteration changed exactly one variable. Reading them in sequence is the most honest way to understand how the v1 pipeline got to where it is.

| Run | Approach | Obligations | Mappings | Unmapped | Cost | Wall-clock |
|---|---|---:|---:|---:|---:|---:|
| v1 | Truncated baseline | 18 | 54 | — | $0.62 | 5m 17s |
| v2 | Full document, chunked | 68 | 203 | — | $2.61 | 21m 22s |
| v3 | Confidence floor on Mapper | 72 | 164 | 12 | $2.78 | 41m 35s |
| v4 | Prompt caching on Mapper | 69 | 124 | 24 | $1.19 | 14m 51s |
| v5 | Fuzzy deduplication | 71 | 154 | 13 | $1.31 | 17m 17s |

The numbers move in interesting ways. Cost climbs and then drops. Mappings climb, then fall sharply, then partially recover. Wall-clock improves only after caching lands. The iteration story is the explanation.

v1 was the first end-to-end run. The Extractor's input was hard-truncated to 50,000 characters — about 12% of the document's 430,000 characters of cleaned text. 18 obligations came out, all from Article 5(1)(a)–(h), the prohibitions section that opens the guidelines. The mappings were dense — 3 controls per obligation, none rejected — but the obligation count was a known undercount of roughly an order of magnitude. The right next move was obvious: process the whole document.

v2 replaced truncation with chunked extraction. 12 chunks of ~40,000 characters each, with 2,000-character overlap to catch obligations that straddled boundaries. The Extractor ran twelve times instead of once. The obligation count jumped to 68. The mapping count jumped to 203 — still 3 per obligation, still nothing rejected. Cost rose 4.2× to $2.61 because the Mapper was now making 68 sequential Sonnet calls instead of 18. Wall-clock rose to 21 minutes. Coverage was now full; quality was now the question.

v3 tightened the Mapper's prompt with a confidence floor. The v2 Mapper was producing exactly 3 mappings per obligation, regardless of fit. Reading the output, the third mapping was almost always reaching — using phrases like "thematically aligned" and "broadly related to" that signal hedging. The v3 prompt added an explicit floor of 0.75 confidence, a ban on hedging language with examples, and explicit permission to return zero mappings when nothing fit. Mapping count dropped from 203 to 164. Twelve obligations came back unmapped — and on inspection, those twelve were almost all procedural duties on Member States, market surveillance authorities, or the Commission, which NIST AI RMF doesn't cover. The system was now honestly admitting framework gaps.

The most valuable signal from v3 was that the model self-regulated. The pre-filter and post-filter mapping counts were identical: the LLM returned 164 mappings, and the post-hoc validation rejected zero. The prompt was being internalised, not enforced retrospectively by code.

v4 added prompt caching on the Mapper's controls library. The Mapper had been sending the full 70-control NIST AI RMF list as input on every one of 68 calls. With Anthropic's ephemeral cache, the controls list became a single cached prefix written once on the first call and read 67 times on subsequent calls at 10% of the input cost. Cost dropped from $2.78 to $1.19 — a 57% reduction. Wall-clock dropped from 41 minutes to 15. Cache hit rate was 97%; the 3% misses were caused by rate-limit retries blowing through the 5-minute TTL.

The cache write cost $0.034 in increased per-token pricing. The cache reads saved $1.42 in input cost. 30× ROI on the cache write is the kind of optimisation result that comes from instrumented measurement, not guesswork.

v5 fixed a correctness issue introduced by chunking. Reading v4's output carefully, several obligations were near-duplicates. The Article 5(1)(c) social-scoring prohibition appeared in chunks 1 and 11 with slightly different wording. The substring-match deduplication v2 had introduced couldn't catch paraphrases. v5 replaced substring matching with rapidfuzz.token_set_ratio at threshold 80. Twelve duplicates merged. The final obligation count stabilised at 71.

v5 also fixed three smaller issues surfaced during the iteration: the report was rendering "null" as a literal string for empty deadlines (cosmetic, but ugly), the title was falling back to the URL filename "112367" because the PDF metadata title was empty (also cosmetic), and the Mapper was occasionally dropping substantive provider obligations whose only confident mapping was to GOVERN-1.1 — the catch-all "legal and regulatory requirements involving AI are understood, managed, and documented" subcategory. A targeted prompt nudge restored those mappings without reintroducing slot-fill.

Five runs, five changes, each visible in the comparison table and inspectable in the repo. The trajectory is what makes the writeup substantive: not "here is the system" but "here is how the system got to be defensible."

A specific design pattern worth surfacing: every iteration was driven by reading the actual output, not by metric chasing. v3's confidence floor came from noticing hedging language in the v2 mappings. v5's dedup came from noticing duplicate obligations in v4's output. The v4 cost optimisation came from noticing that 90% of Mapper input was redundant across calls. Reading the output is the eval that always works, even before the formal eval set exists.
