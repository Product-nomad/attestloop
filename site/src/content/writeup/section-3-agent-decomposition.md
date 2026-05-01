---
title: Agent decomposition
status: draft
updated: 2026-04-30
---

The pipeline has nine components. Five are LLM-driven agents with their own prompts, evals, and per-call cost profiles — three since v1 (Classifier, Extractor, Mapper) and two added in v6 (Clarifier, Critic). Four are deterministic code that does work the LLM doesn't need to do. Treating those distinctions seriously is what separates "agentic system" as a label from "agentic system" as a design choice.

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

The Extractor doesn't get the whole document at once. EU AI Act guidelines are routinely 100+ pages, and the cleaned text from the Commission's prohibited-practices guideline runs to ~430,000 characters. v1 chunks the document at ~40,000 characters with 2,000-character overlap, runs the Extractor once per chunk, and deduplicates the results. The chunk overlap catches obligations that straddle boundaries; the dedup pass handles the resulting paraphrased duplicates with fuzzy matching at threshold 80. Both are documented in *The iteration story*.

The system prompt is around 370 words. It defines what counts as a binding obligation (verbs like "shall," "must," "is prohibited"), what doesn't (verbs like "may," "should consider," "is encouraged to"), and how to populate the structured fields. It also includes explicit instruction to output an empty list when a chunk contains no binding obligations — without that instruction, the model fills the slot with weak extractions.

The Mapper

The Mapper takes one obligation at a time and returns 0–3 NIST AI RMF subcategory mappings, each with confidence ≥ 0.75 and reasoning anchored in the specific control text. The "0" matters: some obligations don't have a high-confidence mapping, and surfacing those as framework gaps is itself the audit-trail behaviour buyers need.

Input: one Obligation plus the full controls library (~70 NIST AI RMF subcategories). Output: a list of ControlMapping records.

Model: Claude Sonnet 4.6. This is the agent that benefits most from prompt caching: the controls library is identical across all 71 mapper calls in a run, so caching the prefix delivers 30× ROI on the cache write cost. *The iteration story* covers the iteration that established this.

The system prompt is around 520 words and is the most heavily iterated of the three. v1 of the prompt produced exactly 3 mappings per obligation regardless of fit. v3 added an explicit confidence floor and banned hedging language ("thematically aligned," "broadly related to," "in the spirit of"). v5 added a nudge for substantive provider obligations that the v3 floor was wrongly dropping. The current shape returns 0–3 mappings honestly, with reasoning that survives reading by someone with GRC background.

The Clarifier

The Clarifier is the v6 addition for ambiguous Classifier outputs. When the Classifier returns in_scope=False with confidence below 0.7, the pipeline routes to the Clarifier rather than directly to the out-of-scope report. The Clarifier extracts additional document context — table of contents, first 5 pages, or section headings, whichever is most informative — and re-runs the Classifier with the augmented input. If the second classification is confident in either direction, the pipeline routes accordingly. If it's still ambiguous, the pipeline writes a "review queue" report distinguished from out-of-scope.

The Clarifier itself is mostly text-extraction code. The actual LLM call is a re-invocation of the Classifier on augmented input — so the Clarifier's added cost is one extra Haiku call per ambiguous classification, ~$0.005.

In practice, the Clarifier rarely fires. Real-world regulatory documents tend to classify confidently in either direction. The Clarifier is a safety net for the long tail — draft amendments, stakeholder consultations, Commission communications that announce rather than constitute binding instruments. On the canonical Commission Guidelines URL the Clarifier never triggers. The synthetic smoke test in `scripts/smoke_clarifier.py` exercises the code path with a contrived ambiguous input.

The Critic

The Critic is the v6 addition for second-pass review of low-confidence Mapper output. It reviews any obligation whose mappings include at least one entry below 0.80 confidence. It returns one of two decisions per reviewed obligation: confirm (mappings stand, no change) or flag_for_review (mappings stand, but the report annotates them as flagged for human attention). It does not auto-replace mappings.

The decision shape matters. Auto-replacement would create a failure mode where a confidently-wrong Critic overwrites a defensible Mapper output, and the audit trail loses signal. Flagging preserves the Mapper's reasoning while adding a second-pass review record that downstream humans can act on. The Critic is advisory, not authoritative.

Input: one Obligation plus the Mapper's proposed mappings plus the full controls library. Output: a CriticDecision with the decision, the Critic's own confidence (on the same 0–1 scale as the Mapper), the reasoning, and the list of control IDs reviewed.

Model: Claude Sonnet 4.6, same as the Mapper, with the same prompt-caching strategy on the controls library. Each Critic call costs roughly the same as a Mapper call.

The Critic only reviews obligations where review adds value. Obligations whose mappings are all above 0.80 confidence are skipped. Obligations with zero mappings are skipped — they're framework gaps, not weak mappings.

The first canonical v6 run flagged 14 obligations out of 42 reviewed (33%). Reading those 14 flag reasons, every single one named a specific control that was being stretched semantically and at least one alternative the Mapper missed. Five recurring patterns surfaced — MANAGE-1.1 misused as per-event authorisation, MAP-3.3 reaching for legal-perimeter semantics, MEASURE-2.9 stretched from interpretability into manipulation-detection, GOVERN-6.1 mis-applied to provider's own legal duties, MANAGE-4.1 stretched to cover pre-event authorisation. These are real failure modes the Critic surfaces. Addressing them through negative examples in the Mapper prompt is tracked in the GitHub backlog.

The four passive components

Watcher, Gap analyser, Drafter, Reviewer queue. v1 implements these as code, not as LLM-driven agents.

The Watcher is architected — the regulation registry has a polling interface and per-source adapter shape — but not implemented. v1 runs on demand against URLs supplied by the user. The Watcher becomes real in v2, with per-regulator scraping, dedup against history, and alerting.

The Gap analyser folds into the Mapper's confidence floor. An obligation with zero mappings is the gap analysis output: NIST AI RMF doesn't cover Member State designation duties, judicial pre-authorisation procedures, or Commission reporting obligations. Surfacing these as a separate "Obligations with no high-confidence framework mapping" section in the report does the work without a separate LLM call.

The Drafter is the report builder code in pipeline.py. It assembles the executive summary, the obligations table, the mappings table, the unmapped section, and the provenance footer from the structured outputs of the upstream agents. There's nothing the LLM adds here that deterministic templating doesn't.

The Reviewer queue is on-disk artefacts. Every run produces runs/<run_id>/ with the publication, per-agent JSON logs, the obligations and mappings JSON, the report markdown, and a run_metadata.json. Reviewing means opening the directory. v2 turns this into a proper queue with web UI; v1 leaves it as files.

v1 ships three real LLM agents and four deterministic components. v6 added two more LLM agents — the Clarifier and the Critic — bringing the LLM agent count to five. The four passive components stay code, not models. Adding LLM agents where deterministic code suffices is a common failure mode in agentic projects; v6's additions both serve genuinely model-shaped purposes (handling ambiguity for the Clarifier, second-pass review for the Critic) rather than substituting for code that already worked.
