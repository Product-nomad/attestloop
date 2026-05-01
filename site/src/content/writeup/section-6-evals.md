---
title: Evals
status: draft
updated: 2026-04-30
---

The honest claim about v1's evals is that they're qualitative, not quantitative. Every iteration was driven by reading the actual output of the previous run. The v3 confidence floor came from noticing hedging language in the v2 mappings. The v5 deduplication came from noticing paraphrased duplicates in v4's obligation list. The cost optimisations came from reading per-agent JSON logs and identifying redundant input. This is real eval discipline; it just isn't measurement.

What was measured: per-agent cost, latency, output token counts, cache hit rates, the GOVERN-1.1 share trajectory across iterations, mapping confidence distribution, and the categorical pattern of unmapped obligations. Each of these was instrumented from v1 onwards via the per-call JSON logs. The data is in the repo.

What wasn't measured: precision and recall of obligation extraction against a hand-labelled gold set. Inter-rater reliability on which sentences in the source are binding obligations. Mapper accuracy against a panel of GRC consultants. Adversarial robustness on prompts that try to manipulate the Extractor or the Classifier.

v6 introduces a different kind of eval signal: the Critic's flag rate and the patterns within it. The first canonical v6 run flagged 14 obligations out of 42 reviewed. Reading the flag reasons surfaced five recurring failure modes in the Mapper — specific patterns of semantic stretch where the Mapper used a control that didn't quite fit. This is not a precision/recall measurement, but it's a structured signal about where the Mapper's reasoning is weakest, and it's actionable: each failure mode could be addressed by adding a negative example to the Mapper prompt. The Critic effectively functions as a continuous live eval against every run, surfacing material for the next prompt iteration.

Building a 50-obligation gold set is still the first task before any production attempt would be defensible. Until that exists, the Critic's flag patterns are the next-best signal: structured, actionable, and produced for free on every run. The honest current claim is that the mapping reasoning survives reading by someone with GRC background, that no run produced hedging language after v3, and that the Critic flags genuine semantic stretches at a rate consistent with what a human reviewer would catch. Those are useful claims. They're not the same as measured precision and recall.

Quantitative evaluation is the v1 gap that hurts the most. Every other v1 limitation has a clean v2 path. The eval gap requires labelled data that doesn't exist yet, and labelling 50 obligations against NIST AI RMF requires somewhere between three and six hours of focused work by someone with the right background.
