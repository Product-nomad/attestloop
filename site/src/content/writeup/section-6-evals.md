---
title: Evals
status: draft
updated: 2026-04-30
---

The honest claim about v1's evals is that they're qualitative, not quantitative. Every iteration was driven by reading the actual output of the previous run. The v3 confidence floor came from noticing hedging language in the v2 mappings. The v5 deduplication came from noticing paraphrased duplicates in v4's obligation list. The cost optimisations came from reading per-agent JSON logs and identifying redundant input. This is real eval discipline; it just isn't measurement.

What was measured: per-agent cost, latency, output token counts, cache hit rates, the GOVERN-1.1 share trajectory across iterations, mapping confidence distribution, and the categorical pattern of unmapped obligations. Each of these was instrumented from v1 onwards via the per-call JSON logs. The data is in the repo.

What wasn't measured: precision and recall of obligation extraction against a hand-labelled gold set. Inter-rater reliability on which sentences in the source are binding obligations. Mapper accuracy against a panel of GRC consultants. Adversarial robustness on prompts that try to manipulate the Extractor or the Classifier.

Building a 50-obligation gold set is the first task before any production attempt would be defensible. It's the missing artefact that converts "the system produces good output by inspection" into "the system produces output that scores X on a defined benchmark." The current honest claim is that the mapping reasoning survives reading by someone with GRC background, that no run produced hedging language after v3, and that the unmapped obligations cluster in categories NIST AI RMF genuinely doesn't cover (Member State duties, public-authority procedural obligations, Commission-level reporting). Those are useful claims. They're not the same as measured precision and recall.

Quantitative evaluation is the v1 gap that hurts the most. Every other v1 limitation has a clean v2 path. The eval gap requires labelled data that doesn't exist yet, and labelling 50 obligations against NIST AI RMF requires somewhere between three and six hours of focused work by someone with the right background.
