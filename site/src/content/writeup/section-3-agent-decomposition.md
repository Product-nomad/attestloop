---
section: 3
title: Agent decomposition
status: draft
word_count: 860
updated: 2026-04-30
---

The pipeline has seven components. Three are LLM-driven agents with their own prompts, evals, and per-call cost profiles. Four are deterministic code that does work the LLM doesn't need to do. Treating those distinctions seriously is what separates "agentic system" as a label from "agentic system" as a design choice.

The Classifier

The Classifier exists because Sonnet on every published document would waste 90% of the per-document budget. EUR-Lex publishes regulations, regulatory technical standards, binding guidelines, draft amendments, press releases, speeches, and Commission communications about consultations. Of those, only the first four contain binding obligations a compliance team needs to act on. The rest are context.

Input: a fetched Publication with the cleaned text and metadata. Output: a structured ClassifierOutput with in_scope: bool, category: Literal["regulation", "guideline", "amendment", "press_release", "other"], confidence: float, and reasoning: str. Schema enforced via Anthropic tool-use, so the model literally cannot return malformed output.

Model: Claude Haiku 4.5. Cost per call ~$0.005, latency ~3 seconds. The decision is well within Haiku's range — distinguishing a binding regulation from a press release is pattern recognition, not deep reasoning. Using Sonnet here would cost 6× more for no measurable accuracy gain on the gold set.

The system prompt is around 280 words. It tells the model what kinds of documents are in scope under the EU AI Act specifically, gives explicit examples of borderline cases (a Commission Communication that announces but doesn't constitute a binding instrument is out of scope; a published guideline interpreting Article 5 prohibitions is in scope), and instructs it to bias toward false in ambiguous cases. The bias matters: a missed obligation extracted from an out-of-scope document is recoverable; an obligation falsely extracted from a press release contaminates the report.

Why a separate agent and not a function call inside the Extractor? Because extraction is structurally a different problem, and merging them obscures the failure mode. If the Extractor is also doing scoping, a wrong extraction looks like a wrong obligation rather than a wrong document. Separating them gives each layer its own accuracy metric.

The Extractor

The Extractor is the most expensive agent per call and the one most sensitive to prompt drift. Its job is to read regulatory text and emit structured Obligation records — id, source_paragraph, requirement_text, scope, deadline, evidence_required. The hard part is distinguishing binding requirements from explanatory text, examples, and recitals.

Input: the publication's cleaned text, plus the regulation context. Output: a list of obligations, each with stable IDs (EUAIA-OBL-001, EUAIA-OBL-002, ...) and explicit source citations.

Model: Claude Sonnet 4.6. Sonnet's reasoning depth matters here in a way it doesn't for classification. The Extractor has to handle ambiguous regulatory language — sentences that contain a binding requirement and an explanatory aside and an exception clause, all in one paragraph. Haiku produces noticeably worse output on this; the gold-set check, when it gets built, will quantify how much worse.

The Extractor doesn't get the whole document at once. EU AI Act guidelines are routinely 100+ pages, and the cleaned text from the Commission's prohibited-practices guideline runs to ~430,000 characters. v1 chunks the document at ~40,000 characters with 2,000-character overlap, runs the Extractor once per chunk, and deduplicates the results. The chunk overlap catches obligations that straddle boundaries; the dedup pass handles the resulting paraphrased duplicates with fuzzy matching at threshold 80. Both are documented in Section 5.

The system prompt is around 370 words. It defines what counts as a binding obligation (verbs like "shall," "must," "is prohibited"), what doesn't (verbs like "may," "should consider," "is encouraged to"), and how to populate the structured fields. It also includes explicit instruction to output an empty list when a chunk contains no binding obligations — without that instruction, the model fills the slot with weak extractions.

The Mapper

The Mapper takes one obligation at a time and returns 0–3 NIST AI RMF subcategory mappings, each with confidence ≥ 0.75 and reasoning anchored in the specific control text. The "0" matters: some obligations don't have a high-confidence mapping, and surfacing those as framework gaps is itself the audit-trail behaviour buyers need.

Input: one Obligation plus the full controls library (~70 NIST AI RMF subcategories). Output: a list of ControlMapping records.

Model: Claude Sonnet 4.6. This is the agent that benefits most from prompt caching: the controls library is identical across all 71 mapper calls in a run, so caching the prefix delivers 30× ROI on the cache write cost. Section 5 covers the iteration that established this.

The system prompt is around 520 words and is the most heavily iterated of the three. v1 of the prompt produced exactly 3 mappings per obligation regardless of fit. v3 added an explicit confidence floor and banned hedging language ("thematically aligned," "broadly related to," "in the spirit of"). v5 added a nudge for substantive provider obligations that the v3 floor was wrongly dropping. The current shape returns 0–3 mappings honestly, with reasoning that survives reading by someone with GRC background.

The four passive components

Watcher, Gap analyser, Drafter, Reviewer queue. v1 implements these as code, not as LLM-driven agents.

The Watcher is architected — the regulation registry has a polling interface and per-source adapter shape — but not implemented. v1 runs on demand against URLs supplied by the user. The Watcher becomes real in v2, with per-regulator scraping, dedup against history, and alerting.

The Gap analyser folds into the Mapper's confidence floor. An obligation with zero mappings is the gap analysis output: NIST AI RMF doesn't cover Member State designation duties, judicial pre-authorisation procedures, or Commission reporting obligations. Surfacing these as a separate "Obligations with no high-confidence framework mapping" section in the report does the work without a separate LLM call.

The Drafter is the report builder code in pipeline.py. It assembles the executive summary, the obligations table, the mappings table, the unmapped section, and the provenance footer from the structured outputs of the upstream agents. There's nothing the LLM adds here that deterministic templating doesn't.

The Reviewer queue is on-disk artefacts. Every run produces runs/<run_id>/ with the publication, per-agent JSON logs, the obligations and mappings JSON, the report markdown, and a run_metadata.json. Reviewing means opening the directory. v2 turns this into a proper queue with web UI; v1 leaves it as files.

The honest framing: four of the seven components in the pipeline diagram are deterministic code, not LLM agents. v1 ships three real agents, and that's the right scope for the v1 problem. Adding LLM agents where deterministic code suffices is a common failure mode in agentic projects — every stage doesn't need to be a model call.
