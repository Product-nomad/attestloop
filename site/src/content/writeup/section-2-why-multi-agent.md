---
title: Why multi-agent
status: draft
updated: 2026-04-30
---

The honest thing about agentic systems in 2026 is that most projects called "agentic" don't need to be. A single well-prompted Claude or GPT call, with retrieval grounding it in domain context, handles a remarkable amount of what gets pitched as multi-agent work. The agentic framing is fashionable enough that picking it for fashion's sake is the default failure mode.

So the first design decision wasn't which agents but whether agents at all. Four alternatives were on the table.

A monolithic prompt. Hand Claude a regulator publication and a controls library, ask for the analysis, take the output. This is what most LLM-powered compliance demos actually do. It works for a while. It breaks at scale: a 135-page guideline document plus a 70-control framework plus reasoning headroom doesn't fit comfortably in a single context window, and the parts that fit aren't separately observable. If the model's classification is wrong, you discover it from the bad mappings two layers downstream. If the prompt drifts as you tune it, you can't tell which part of the output drifted with it. Single point of failure, single point of debugging.

RAG with retrieval over the controls library. Embed the controls, retrieve the relevant subset for each obligation, generate the mapping. This works fine for the mapping step in isolation. It doesn't address the obligation extraction problem, which is the part where most of the work lives. Bolting an extraction step in front of a RAG pipeline reinvents the multi-agent decomposition without admitting it.

A single agent with tools. One agent, given access to a fetch tool, an extraction tool, a retrieval tool, a drafting tool. The agent decides which tool to call when. Theoretically clean; in practice, the failure modes compound. If the agent decides to skip the extraction step and go straight to drafting, you don't catch it until the report is wrong. Per-step evals become per-trace evals, which are an order of magnitude harder to construct. The flexibility of agentic tool-calling is exactly what makes it brittle in production: every run is a different graph through tool-space.

A multi-agent pipeline with explicit contracts between stages. Three LLM-driven agents — Classifier, Extractor, Mapper — each with a typed input, a typed output, a separate prompt, separate evals, separate cost optimisation. Support code for fetching, chunking, deduplication, report generation. Each agent boundary is a place where a hand-labelled gold set could plug in. Each agent's prompt can be iterated independently without disturbing the others. Each agent's cost can be tuned independently — Haiku for classification, Sonnet for extraction and mapping, with different prompt-caching strategies on each.

Multi-agent won, but not because agents are fashionable. It won because the workflow has natural boundaries between extraction (a parsing problem), mapping (a retrieval-and-reasoning problem), and synthesis (a structured-output problem). Treating those boundaries as agent contracts makes the system testable, observable, and improvable in ways the alternatives are not.

A note on what v1 isn't. The pipeline ships sequential execution: Classifier returns, Extractor runs, Mapper runs through the obligation list one at a time, the report builder assembles the output. There is no orchestrator agent making routing decisions. There is no parallel execution. There is no critic agent reviewing low-confidence mappings before the report is finalised. These are real and useful patterns; they're tracked as v6 work in the project's GitHub issues. v1 prioritised end-to-end correctness over orchestration sophistication, which is the right ordering for a portfolio piece — orchestration on top of a broken pipeline is wasted optimisation.
