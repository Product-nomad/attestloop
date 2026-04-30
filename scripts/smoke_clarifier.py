"""Synthetic smoke for the Clarifier agent.

Real-world URLs all classify as confident out_of_scope (≥0.92) on the
current Classifier prompt — the prompt's "bias toward false in
ambiguous cases" instruction is too decisive to easily produce a
sub-0.7 confidence verdict. This script constructs a deliberately-thin
Publication (a borderline blurb that mentions the AI Act but doesn't
quote any binding language) and invokes clarify_and_reclassify
directly. That exercises the Clarifier's three code paths
(context-extraction → augmented-input → re-classify) against the live
Anthropic API and writes the resulting ClarifierOutput to disk for the
v6 task 3 snapshot.

Run with: uv run python scripts/smoke_clarifier.py
"""
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console

load_dotenv()

from attestloop.agents.classifier import classify
from attestloop.agents.clarifier import clarify_and_reclassify
from attestloop.registry import get_regulation
from attestloop.runs import create_run_dir
from attestloop.schemas import ClassifierInput, Publication

console = Console()

# Deliberately thin: mentions the AI Act and binding language ("must",
# "obligations") but is structured like a news blurb rather than a
# binding instrument. The first 200-300 chars give the Classifier
# minimal signal to commit to either side, which is the failure mode
# the Clarifier exists to recover from.
THIN_BODY = """
AI Act update - April 2026

The European Commission has continued work on implementing
Regulation (EU) 2024/1689 (the "AI Act"). Providers and deployers must
review their obligations under Article 5 and ensure compliance with
the prohibited practices regime by the deadlines stated in the Act.

Further detail on prohibited practices, high-risk AI system requirements,
governance arrangements, and penalties is available in the official
Commission guidelines and the consolidated text of Regulation 2024/1689.

This brief is for information only.

---

Table of Contents
1. Background
2. Article 5 prohibitions
3. High-risk system requirements (Annex III)
4. Provider obligations
5. Deployer obligations
6. Governance and penalties
7. Implementation timeline

(Detailed sections in the linked PDF.)
"""

publication = Publication(
    url="local://smoke_clarifier_test",
    title="AI Act update — April 2026 (synthetic test fixture)",
    raw_html="",
    cleaned_text=THIN_BODY,
    fetched_at=datetime.now(timezone.utc),
)

run_id, started_at, run_dir = create_run_dir()
console.print(f"[bold]synthetic clarifier smoke[/bold] -> {run_dir}")

regulation = get_regulation("eu_ai_act")

# First pass: classify the thin document. We don't pre-stub a
# low-confidence ClassifierOutput — we run the real Classifier and let
# it decide. If the Classifier comes back ≥ 0.7 confidence we'll
# observe that and adjust the fixture; if it comes back < 0.7 we feed
# its output into clarify_and_reclassify to exercise the real path.
classification = classify(
    ClassifierInput(publication=publication, regulation_id=regulation.id),
    regulation,
    run_dir,
)
console.print(
    f"[cyan]initial classify:[/cyan] in_scope={classification.in_scope}, "
    f"category={classification.category}, "
    f"confidence={classification.confidence:.2f}"
)

clarifier_output = clarify_and_reclassify(
    publication, classification, regulation, run_dir,
)

(run_dir / "clarifier.json").write_text(clarifier_output.model_dump_json(indent=2))
console.print(
    f"[cyan]reclassified:[/cyan] in_scope={clarifier_output.reclassification.in_scope}, "
    f"confidence={clarifier_output.reclassification.confidence:.2f}, "
    f"context_source={clarifier_output.context_source}"
)
console.print(f"\n[green]wrote {run_dir / 'clarifier.json'}[/green]")
