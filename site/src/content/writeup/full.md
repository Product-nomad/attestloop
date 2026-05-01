---
title: "Building a multi-agent regulatory attestation pipeline"
subtitle: "Five iterations, $1.31 per run, and what an honest agentic system looks like."
status: draft
updated: 2026-04-30
---


## The problem

A compliance officer at a UK fintech with 800 employees reads roughly 40 regulator publications a week. The list comes from EUR-Lex's AI Act feed, the FCA Handbook updates, EBA guidelines, ICO opinions, ESMA technical standards, and a half-dozen sector-specific bulletins that arrive on subscription. Of those forty publications, maybe three to five contain substantive obligations affecting the firm. The rest are press releases, speeches, scoping consultations, or commentary about regulations that already exist.

The substantive ones are the work. For each, the officer reads the document — sometimes a hundred pages of dense legal text — extracts the binding obligations, maps each obligation to the firm's existing controls library (typically two to four hundred entries in a SharePoint document or an OneTrust deployment), identifies the gaps where existing controls don't fully cover the new requirement, drafts proposed remediation, and routes the work to the affected teams in product, engineering, legal, and risk. Each substantive publication eats four to eight hours of senior compliance time.

This is before the AI Act. The AI Act adds a new layer of obligations across product engineering and operational risk that don't map cleanly to existing financial-services control libraries. NIST AI RMF, ISO 42001, the Commission's own guidelines on prohibited practices — these introduce categories that the existing GRC tooling wasn't designed to ingest, let alone map. The result is a quietly growing backlog: obligations identified but not assessed, gaps flagged but not closed, audit findings that compliance is technically meeting deadlines while substantively falling behind.

When the audit committee or the board asks the four questions that always get asked — Are we covered? What do we need to do? Prove it. What's coming next? — the honest answer is usually "we don't know yet, give us two weeks." Two weeks of senior time, every time something new lands.

Most existing tooling treats this as a content-management problem. Fetch the publication, tag it, store it, surface it in a dashboard. The dashboard is where the work hasn't been done yet. The mapping, the gap analysis, the remediation drafting — those still happen in someone's head, with a Word document and a copy of the controls library open in another tab.

This is a workflow problem, not an information problem. It has natural decomposition: classify, extract obligations, map to controls, identify gaps, draft responses, queue for review. Each step has different inputs, different reasoning patterns, different accuracy requirements. Each is testable, observable, improvable in isolation.

That decomposition is where multi-agent systems earn their keep.


## Why multi-agent

The honest thing about agentic systems in 2026 is that most projects called "agentic" don't need to be. A single well-prompted Claude or GPT call, with retrieval grounding it in domain context, handles a remarkable amount of what gets pitched as multi-agent work. The agentic framing is fashionable enough that picking it for fashion's sake is the default failure mode.

So the first design decision wasn't which agents but whether agents at all. Four alternatives were on the table.

A monolithic prompt. Hand Claude a regulator publication and a controls library, ask for the analysis, take the output. This is what most LLM-powered compliance demos actually do. It works for a while. It breaks at scale: a 135-page guideline document plus a 70-control framework plus reasoning headroom doesn't fit comfortably in a single context window, and the parts that fit aren't separately observable. If the model's classification is wrong, you discover it from the bad mappings two layers downstream. If the prompt drifts as you tune it, you can't tell which part of the output drifted with it. Single point of failure, single point of debugging.

RAG with retrieval over the controls library. Embed the controls, retrieve the relevant subset for each obligation, generate the mapping. This works fine for the mapping step in isolation. It doesn't address the obligation extraction problem, which is the part where most of the work lives. Bolting an extraction step in front of a RAG pipeline reinvents the multi-agent decomposition without admitting it.

A single agent with tools. One agent, given access to a fetch tool, an extraction tool, a retrieval tool, a drafting tool. The agent decides which tool to call when. Theoretically clean; in practice, the failure modes compound. If the agent decides to skip the extraction step and go straight to drafting, you don't catch it until the report is wrong. Per-step evals become per-trace evals, which are an order of magnitude harder to construct. The flexibility of agentic tool-calling is exactly what makes it brittle in production: every run is a different graph through tool-space.

A multi-agent pipeline with explicit contracts between stages. Three LLM-driven agents — Classifier, Extractor, Mapper — each with a typed input, a typed output, a separate prompt, separate evals, separate cost optimisation. Support code for fetching, chunking, deduplication, report generation. Each agent boundary is a place where a hand-labelled gold set could plug in. Each agent's prompt can be iterated independently without disturbing the others. Each agent's cost can be tuned independently — Haiku for classification, Sonnet for extraction and mapping, with different prompt-caching strategies on each.

Multi-agent won, but not because agents are fashionable. It won because the workflow has natural boundaries between extraction (a parsing problem), mapping (a retrieval-and-reasoning problem), and synthesis (a structured-output problem). Treating those boundaries as agent contracts makes the system testable, observable, and improvable in ways the alternatives are not.

A note on what v1 isn't. The pipeline ships sequential execution: Classifier returns, Extractor runs, Mapper runs through the obligation list one at a time, the report builder assembles the output. There is no orchestrator agent making routing decisions. There is no parallel execution. There is no critic agent reviewing low-confidence mappings before the report is finalised. These are real and useful patterns; they're tracked as v6 work in the project's GitHub issues. v1 prioritised end-to-end correctness over orchestration sophistication, which is the right ordering for a portfolio piece — orchestration on top of a broken pipeline is wasted optimisation.


## Agent decomposition

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

The Extractor doesn't get the whole document at once. EU AI Act guidelines are routinely 100+ pages, and the cleaned text from the Commission's prohibited-practices guideline runs to ~430,000 characters. v1 chunks the document at ~40,000 characters with 2,000-character overlap, runs the Extractor once per chunk, and deduplicates the results. The chunk overlap catches obligations that straddle boundaries; the dedup pass handles the resulting paraphrased duplicates with fuzzy matching at threshold 80. Both are documented in *The iteration story*.

The system prompt is around 370 words. It defines what counts as a binding obligation (verbs like "shall," "must," "is prohibited"), what doesn't (verbs like "may," "should consider," "is encouraged to"), and how to populate the structured fields. It also includes explicit instruction to output an empty list when a chunk contains no binding obligations — without that instruction, the model fills the slot with weak extractions.

The Mapper

The Mapper takes one obligation at a time and returns 0–3 NIST AI RMF subcategory mappings, each with confidence ≥ 0.75 and reasoning anchored in the specific control text. The "0" matters: some obligations don't have a high-confidence mapping, and surfacing those as framework gaps is itself the audit-trail behaviour buyers need.

Input: one Obligation plus the full controls library (~70 NIST AI RMF subcategories). Output: a list of ControlMapping records.

Model: Claude Sonnet 4.6. This is the agent that benefits most from prompt caching: the controls library is identical across all 71 mapper calls in a run, so caching the prefix delivers 30× ROI on the cache write cost. *The iteration story* covers the iteration that established this.

The system prompt is around 520 words and is the most heavily iterated of the three. v1 of the prompt produced exactly 3 mappings per obligation regardless of fit. v3 added an explicit confidence floor and banned hedging language ("thematically aligned," "broadly related to," "in the spirit of"). v5 added a nudge for substantive provider obligations that the v3 floor was wrongly dropping. The current shape returns 0–3 mappings honestly, with reasoning that survives reading by someone with GRC background.

The four passive components

Watcher, Gap analyser, Drafter, Reviewer queue. v1 implements these as code, not as LLM-driven agents.

The Watcher is architected — the regulation registry has a polling interface and per-source adapter shape — but not implemented. v1 runs on demand against URLs supplied by the user. The Watcher becomes real in v2, with per-regulator scraping, dedup against history, and alerting.

The Gap analyser folds into the Mapper's confidence floor. An obligation with zero mappings is the gap analysis output: NIST AI RMF doesn't cover Member State designation duties, judicial pre-authorisation procedures, or Commission reporting obligations. Surfacing these as a separate "Obligations with no high-confidence framework mapping" section in the report does the work without a separate LLM call.

The Drafter is the report builder code in pipeline.py. It assembles the executive summary, the obligations table, the mappings table, the unmapped section, and the provenance footer from the structured outputs of the upstream agents. There's nothing the LLM adds here that deterministic templating doesn't.

The Reviewer queue is on-disk artefacts. Every run produces runs/<run_id>/ with the publication, per-agent JSON logs, the obligations and mappings JSON, the report markdown, and a run_metadata.json. Reviewing means opening the directory. v2 turns this into a proper queue with web UI; v1 leaves it as files.

The honest framing: four of the seven components in the pipeline diagram are deterministic code, not LLM agents. v1 ships three real agents, and that's the right scope for the v1 problem. Adding LLM agents where deterministic code suffices is a common failure mode in agentic projects — every stage doesn't need to be a model call.


## Orchestration

The pipeline is a Python module — src/attestloop/pipeline.py — that ties the three agents and four passive components together. v1 ships sequential execution: each step runs to completion, writes its output to disk, and the next step picks it up. There is no orchestrator agent, no parallel work, no conditional routing. The shape is closer to a Unix pipeline than to LangGraph.

The top-level function reads:

```python
def run(url: str, regulation_id: str, framework_id: str) -> Path:
    run_dir = create_run_dir()
    publication = fetch_publication(url, run_dir)
    regulation = registry.get_regulation(regulation_id)
    framework = registry.get_framework(framework_id)

    classification = classify(publication, regulation, run_dir)
    if not classification.in_scope:
        return write_out_of_scope_report(run_dir, classification)

    obligations = extract_chunked(publication, regulation, run_dir)
    mappings = map_to_controls(obligations, framework, run_dir)

    return build_report(run_dir, publication, classification,
                        obligations, mappings, regulation, framework)
```

Eight lines of orchestration logic, each agent invocation taking structured input and returning structured output. Each output is also serialised to runs/<run_id>/<agent>.json before the next step runs, so the run is recoverable, inspectable, and debuggable from disk alone.

State passing is explicit. There's no shared mutable context, no implicit globals, no agent reading another agent's output through a side channel. The Mapper takes the Extractor's obligations list as a typed argument; if the Extractor returns nothing, the Mapper trivially produces nothing; if either fails, the disk artefacts from prior steps remain for diagnosis. The state machine is the call stack.

Failure handling lives at three levels. Per-call: each LLM invocation has a 60-second timeout and a single retry on transient errors (APITimeoutError, APIConnectionError, RateLimitError, InternalServerError). Per-agent: structured error types — EmptyPublicationError from the fetcher, RateLimitBackoff from the LLM wrapper — propagate cleanly to the pipeline, where they decide whether to retry, fail loudly, or short-circuit. Per-run: any uncaught error leaves the run directory intact with whatever artefacts had been written, so post-mortem is possible.

Human-in-the-loop boundaries exist conceptually but aren't wired in v1. The natural points are: between the Classifier and the Extractor (review borderline scope decisions), between the Mapper and the Report builder (review low-confidence mappings before they land in the report), and between the Report builder and any downstream system (sign-off before publication). v1 surfaces all the data needed for HITL — confidence scores per mapping, unmapped obligations as their own report section, hashed prompt versions in the provenance footer — but doesn't yet hold the pipeline open for human input. The architecture supports adding HITL hooks at those points without restructuring; v6's state-machine refactor will make the wiring explicit.

What v1 doesn't have, and what v6 will: a typed PipelineState object passed through a LangGraph StateGraph, conditional edges that route based on agent outputs (Classifier returning in_scope=False, confidence<0.7 should route to a Clarifier agent, not directly to the out-of-scope report), parallel Mapper execution with concurrency control, and a Critic agent that reviews mappings below 0.80 confidence before they reach the report.

Those are real orchestration patterns, and they're tracked in issue #4. v1 prioritised end-to-end correctness with explicit per-stage observability; v6 layers orchestration on top of that foundation. The order matters: orchestrating a pipeline that produces wrong outputs is wasted optimisation. Sequential execution with disk-logged state was the cheapest way to validate that each stage produced the right thing before the stages started talking to each other.

A pragmatic note: for a v1 portfolio piece running on demand against single documents, sequential execution is also operationally adequate. 17 minutes wall-clock for a 71-obligation, 154-mapping run on a 135-page guideline is acceptable for human-paced compliance work. v6 closes the latency gap — and unlocks scheduled multi-document runs — but v1's latency isn't a v1 problem.


## Iteration

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


## Evals

The honest claim about v1's evals is that they're qualitative, not quantitative. Every iteration was driven by reading the actual output of the previous run. The v3 confidence floor came from noticing hedging language in the v2 mappings. The v5 deduplication came from noticing paraphrased duplicates in v4's obligation list. The cost optimisations came from reading per-agent JSON logs and identifying redundant input. This is real eval discipline; it just isn't measurement.

What was measured: per-agent cost, latency, output token counts, cache hit rates, the GOVERN-1.1 share trajectory across iterations, mapping confidence distribution, and the categorical pattern of unmapped obligations. Each of these was instrumented from v1 onwards via the per-call JSON logs. The data is in the repo.

What wasn't measured: precision and recall of obligation extraction against a hand-labelled gold set. Inter-rater reliability on which sentences in the source are binding obligations. Mapper accuracy against a panel of GRC consultants. Adversarial robustness on prompts that try to manipulate the Extractor or the Classifier.

Building a 50-obligation gold set is the first task before any production attempt would be defensible. It's the missing artefact that converts "the system produces good output by inspection" into "the system produces output that scores X on a defined benchmark." The current honest claim is that the mapping reasoning survives reading by someone with GRC background, that no run produced hedging language after v3, and that the unmapped obligations cluster in categories NIST AI RMF genuinely doesn't cover (Member State duties, public-authority procedural obligations, Commission-level reporting). Those are useful claims. They're not the same as measured precision and recall.

Quantitative evaluation is the v1 gap that hurts the most. Every other v1 limitation has a clean v2 path. The eval gap requires labelled data that doesn't exist yet, and labelling 50 obligations against NIST AI RMF requires somewhere between three and six hours of focused work by someone with the right background.


## Costs and latency

| Agent | Model | Calls | Cost (v5) | Mean latency |
|---|---|---:|---:|---:|
| Classifier | Claude Haiku 4.5 | 1 | $0.005 | 3.7 s |
| Extractor | Claude Sonnet 4.6 | 12 | $0.61 | 20.2 s |
| Mapper | Claude Sonnet 4.6 | 71 | $0.69 | 11.1 s |

Total: $1.31 per run, 17 minutes wall-clock, against a 135-page regulator publication producing 71 obligations and 154 mapped controls.

The cost shape is worth comparing. Manual review of the same publication by a senior compliance officer would cost on the order of £500-1000 in analyst time at GRC consultant rates, before any control-mapping work happens. The major incumbent regulatory monitoring tools — OneTrust, Diligent, Wolters Kluwer Enablon — sell their AI-Act monitoring modules at £40,000-150,000 per year flat fee, regardless of how many publications get processed or how few obligations get mapped. A naïve single-call GPT-4 approach against the same document would cost roughly £3-5 per run with no provenance, no confidence handles, no separately-tunable agents, and no audit trail.

$1.31 per run is the cost shape of deliberate engineering: Haiku for the classification step that doesn't need Sonnet, prompt caching on the Mapper's redundant controls input, chunked extraction to handle long documents without context-limit failures. Each optimisation came from instrumented measurement, not from guesswork. The 30× return on the prompt cache write specifically is documented in *The iteration story*; it's the largest single cost reduction in the iteration sequence.

Latency is the v1 limitation that v6's parallel Mapper execution will close. 71 sequential Sonnet calls at ~11 seconds each accounts for most of the 17-minute wall-clock. Eight-way concurrent execution would reduce that to roughly 2 minutes of Mapper work, leaving Extraction as the new dominant cost.


## Failure modes

Six things that broke or surprised during development. Each is preserved in the git history; the stories are what makes the writeup credible to a reader who has built systems like this.

EUR-Lex's PDF-on-demand quirk. The first attempt to fetch the AI Act guidelines from EUR-Lex returned an HTTP 202 response with an empty body. EUR-Lex generates PDFs on demand; the first request kicks off generation, and the client is expected to retry. The fetcher needed magic-byte detection — checking the first five bytes of the response for %PDF- — because both Content-Type and URL-pattern checks failed on the redirect chain. Real regulator scraping is materially harder than the demos suggest.

The model that recognised a 404 page. During development, one fetch returned a Commission "Page not found" template — about 489 characters of navigation HTML with no actual document content. The Classifier marked it out_of_scope with confidence 0.98 and reasoning that explicitly noted the URL suggested a guidelines page but the content was a 404 template. The first reaction was to debug the system; the actual outcome was the system refusing to extract obligations from a non-document. Belief calibration the right way around.

Slot-fill in the Mapper. The v2 prompt asked for "1–3 mappings per obligation"; the model interpreted this as "always 3" and produced reasoning hedges to fill the slots. Phrases like "thematically aligned" and "not a verbatim match but" appeared on roughly a third of the v2 mappings. The fix wasn't tighter post-filtering — it was an explicit confidence floor in the prompt with examples of what not to return. After v3, the pre-filter and post-filter counts matched, proving the model was self-regulating rather than the code post-hoc.

Chunked extraction producing paraphrased duplicates. v2's chunked extractor was catching obligations at chunk boundaries — exactly what 2,000-character overlap was meant to do — but the Article 5(1)(c) prohibition appeared in three different chunks with slightly different wording each time. Substring-match deduplication couldn't catch the paraphrases. The fix was rapidfuzz.token_set_ratio at threshold 80, which merged 12 paraphrased duplicates in v5. The lesson: chunk overlap is a correctness mechanism, but the dedup pass it requires is non-trivial to get right.

Anthropic's 5-minute cache TTL exceeded by rate-limit retries. v4's prompt caching delivered a 97% hit rate, not 100%. The 3% misses were caused by rate-limit retries inserting 30-second backoff pauses; with multiple consecutive backoffs on a long run, the cache TTL would expire and the next call would write a fresh cache entry. The cost of the rewrites was small — two extra cache writes on a 71-call run — but the diagnostic process surfaced a useful observation: latency variance from rate limits is itself an orchestration problem, and the right v6 fix is parallel execution to keep the call cadence inside the cache window.

The model's tendency to map every prohibition to GOVERN-1.1. GOVERN-1.1 — "legal and regulatory requirements involving AI are understood, managed, and documented" — is a defensible mapping for almost any Article 5 prohibition. The v2 Mapper used it on 26% of all mappings. v3's confidence floor brought that to 21% by dropping the weakest catch-all uses. v5's targeted prompt nudge for substantive provider obligations restored some legitimate uses, settling at 32%. The v5 share is correct: GOVERN-1.1 is the right control for most prohibition-shaped obligations, and the trajectory wasn't "use it less" but "use it precisely."


## What's next

v2 work is tracked in the repo's GitHub issues. The most important items:

- **Mapper batching for cost optimisation (#1).** 4–8 obligations per Sonnet call instead of one, reducing API overhead by ~10×. Trade-off: per-batch failure handling becomes the new failure mode to manage.
- **Longer-TTL cache for sustained throughput (#2).** The 5-minute ephemeral cache is insufficient for runs that hit rate limits. Anthropic's longer-TTL cache tier or restructured call cadence both close the gap.
- **Multi-source watcher agent (#3).** v1 runs on demand against URLs the user supplies. The Watcher polls regulator sources on a schedule, deduplicates against historical runs, and queues new in-scope publications. The architecture supports it; v2 implements the per-regulator scrape adapters.
- **Real orchestration: state machine, parallel execution, critic agent (#4).** The largest piece of v6 work and the one that converts v1 from a sequential pipeline into a genuinely orchestrated system.
- **Quantitative evals.** Hand-labelled gold sets for obligation extraction and mapping accuracy. The first task before any production attempt would be defensible.
- **Multi-framework support.** ISO 42001, SOC 2 AI Trust Criteria, customer-supplied control libraries. The Framework registry already supports the abstraction; v2 implements the additional frameworks.

v1 is a portfolio piece designed to demonstrate orchestration thinking and end-to-end engineering against a real problem. Production readiness is a different artefact, and the gap between v1 and a real product is named explicitly so the reader knows what's missing. Naming the gap is itself a v1 feature.


## Closing

What the project demonstrates: the ability to scope a multi-agent system against a real problem, ship it iteratively with measured cost and quality at each step, and reason honestly about the production gap. The pipeline produces $1.31 attestation reports against a real EU regulator publication, with full provenance, configurable confidence floors, and a clear v6 path to genuine orchestration.

The live demo at [attestloop.ai](https://attestloop.ai/). The source at [github.com/Product-nomad/attestloop](https://github.com/Product-nomad/attestloop). Available for AI Delivery Manager roles in regulated industries — particularly UK gov, financial services, and healthtech.

— Simon Newton, April 2026
