# v6 task 3 — Clarifier agent synthetic smoke

This directory captures evidence that the Clarifier code path executed
end-to-end against the live Anthropic API. **It is a synthetic test,
not a canonical run.** The fixture is a deliberately-thin paragraph
that mentions the AI Act in passing and embeds a short Table of
Contents — the kind of input where you'd want a real-world Clarifier
to step in.

## Why synthetic

Three real URLs were tried first as the natural smoke target. All
three returned confident `out_of_scope` verdicts on the initial
Classifier pass — too confident to trigger the Clarifier branch in the
production pipeline:

| URL | Verdict | Confidence |
|---|---|---:|
| Wikipedia · Information Commissioner's Office | out_of_scope | 0.99 |
| Commission digital-strategy AI-Act landing page | out_of_scope | 0.92 |
| Wikipedia · Artificial Intelligence Act | out_of_scope | 0.95 |

That's the Classifier prompt's "bias toward false in ambiguous cases"
instruction working as designed. The Clarifier exists as a safety net
for genuinely ambiguous documents, which are rare in practice on the
EU AI Act prompt configuration.

To exercise the Clarifier code path on the live API anyway, the script
`scripts/smoke_clarifier.py` constructs a thin `Publication` object
with text that contains both a borderline AI-Act mention and a
Table-of-Contents marker, then invokes `clarify_and_reclassify`
directly. The artefacts in this directory are the result.

## What's in this directory

- `classifier.json` — two `LLMCallLog` entries, one per Classifier
  invocation. The second is the Clarifier-triggered re-call.
- `clarifier.json` — the `ClarifierOutput` audit record:
  `initial_classification`, `additional_context` (227 chars),
  `context_source: "table_of_contents"`, `reclassification`.

## What this proves

- The Clarifier's three-step pattern executes against a real model:
  context-extraction → augmented-input → re-classify.
- The TOC heuristic (`_extract_table_of_contents`) correctly fires on
  the synthetic fixture and beats the section-heading and first-pages
  fallbacks.
- The audit trail is self-describing: `clarifier.json` alone tells you
  what the Clarifier saw, what it added, and what changed.
- The `LOW_CONFIDENCE_THRESHOLD = 0.7` is correctly biased toward
  conservatism — the Clarifier won't fire on a confident verdict, even
  if downstream effects (extra Haiku call) are cheap.

## What this does not prove

- The Clarifier's effect on a *real* low-confidence classification
  hasn't been observed in production. The unit tests cover routing
  semantics; this smoke covers the agent's code paths; live
  observation waits for a regulator URL that genuinely lands the
  Classifier in the < 0.7 confidence band. That hasn't yet appeared on
  the EU AI Act prompt — we'll see it eventually.
