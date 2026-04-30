---
section: 1
title: The problem
status: draft
updated: 2026-04-30
---

A compliance officer at a UK fintech with 800 employees reads roughly 40 regulator publications a week. The list comes from EUR-Lex's AI Act feed, the FCA Handbook updates, EBA guidelines, ICO opinions, ESMA technical standards, and a half-dozen sector-specific bulletins that arrive on subscription. Of those forty publications, maybe three to five contain substantive obligations affecting the firm. The rest are press releases, speeches, scoping consultations, or commentary about regulations that already exist.

The substantive ones are the work. For each, the officer reads the document — sometimes a hundred pages of dense legal text — extracts the binding obligations, maps each obligation to the firm's existing controls library (typically two to four hundred entries in a SharePoint document or an OneTrust deployment), identifies the gaps where existing controls don't fully cover the new requirement, drafts proposed remediation, and routes the work to the affected teams in product, engineering, legal, and risk. Each substantive publication eats four to eight hours of senior compliance time.

This is before the AI Act. The AI Act adds a new layer of obligations across product engineering and operational risk that don't map cleanly to existing financial-services control libraries. NIST AI RMF, ISO 42001, the Commission's own guidelines on prohibited practices — these introduce categories that the existing GRC tooling wasn't designed to ingest, let alone map. The result is a quietly growing backlog: obligations identified but not assessed, gaps flagged but not closed, audit findings that compliance is technically meeting deadlines while substantively falling behind.

When the audit committee or the board asks the four questions that always get asked — Are we covered? What do we need to do? Prove it. What's coming next? — the honest answer is usually "we don't know yet, give us two weeks." Two weeks of senior time, every time something new lands.

Most existing tooling treats this as a content-management problem. Fetch the publication, tag it, store it, surface it in a dashboard. The dashboard is where the work hasn't been done yet. The mapping, the gap analysis, the remediation drafting — those still happen in someone's head, with a Word document and a copy of the controls library open in another tab.

This is a workflow problem, not an information problem. It has natural decomposition: classify, extract obligations, map to controls, identify gaps, draft responses, queue for review. Each step has different inputs, different reasoning patterns, different accuracy requirements. Each is testable, observable, improvable in isolation.

That decomposition is where multi-agent systems earn their keep.
