"""Critic agent. Second-pass review of Mapper output for any obligation
whose mappings include at least one entry below 0.80 confidence. The
Critic does not auto-replace mappings — its only authority is to confirm
or flag for human review. The Mapper's output stands in the report
regardless of the Critic's decision."""
import hashlib
import json
from pathlib import Path

from rich.console import Console

from attestloop.llm import call_with_logging
from attestloop.registry import Framework
from attestloop.schemas import (
    Control,
    ControlMapping,
    CriticDecision,
    CriticOutput,
    Obligation,
)

CRITIC_MODEL = "claude-sonnet-4-6"
LOW_CONFIDENCE_THRESHOLD = 0.80

_CONTROLS_HEADER = (
    "## Allowed control catalogue (the same list the Mapper saw)\n"
    "Each entry is one NIST AI RMF 1.0 subcategory. JSON below.\n"
)

_console = Console()


def _format_controls(controls: list[Control]) -> str:
    rows = [
        {
            "id": c.id,
            "function": c.function,
            "category": c.category,
            "subcategory_text": c.subcategory_text,
        }
        for c in controls
    ]
    return json.dumps(rows, indent=2)


def _format_proposed_mappings(mappings: list[ControlMapping]) -> str:
    rows = [
        {
            "control_id": m.control_id,
            "confidence": m.confidence,
            "reasoning": m.reasoning,
        }
        for m in mappings
    ]
    return json.dumps(rows, indent=2)


def _build_user_message(
    obligation: Obligation, proposed_mappings: list[ControlMapping]
) -> str:
    return (
        "--- OBLIGATION ---\n"
        f"{obligation.model_dump_json(indent=2)}\n\n"
        f"--- MAPPER'S PROPOSED MAPPINGS ({len(proposed_mappings)}) ---\n"
        f"{_format_proposed_mappings(proposed_mappings)}\n"
        "--- END ---"
    )


def _needs_review(
    mappings: list[ControlMapping], threshold: float = LOW_CONFIDENCE_THRESHOLD
) -> bool:
    """True iff any mapping for this obligation is below `threshold`.
    Empty list returns False — no mappings means a framework gap, which
    the Mapper has already surfaced as `unmapped` and the Critic does
    not need to look at."""
    return any(m.confidence < threshold for m in mappings)


def review_mappings(
    obligations: list[Obligation],
    mappings: list[ControlMapping],
    framework: Framework,
    run_dir: Path,
    *,
    confidence_threshold: float = LOW_CONFIDENCE_THRESHOLD,
) -> CriticOutput:
    """Review the subset of obligations whose Mapper output contains at
    least one mapping below `confidence_threshold` (default 0.80).
    Returns one CriticDecision per reviewed obligation; obligations
    whose mappings are all high-confidence (or empty) are skipped
    without LLM call."""
    system_prompt_text = framework.critic_prompt_path.read_text()
    prompt_version = hashlib.sha256(system_prompt_text.encode("utf-8")).hexdigest()

    # Same cached prefix shape as the Mapper — prompt + controls catalogue
    # in one ephemeral-cached system block. With a single new write on
    # the first Critic call and reads on every subsequent one.
    cached_system_text = (
        f"{system_prompt_text}\n\n"
        f"{_CONTROLS_HEADER}\n"
        f"{_format_controls(framework.controls)}\n"
    )
    system_blocks: list[dict] = [
        {
            "type": "text",
            "text": cached_system_text,
            "cache_control": {"type": "ephemeral"},
        }
    ]

    valid_ids = {c.id for c in framework.controls}
    by_obligation: dict[str, list[ControlMapping]] = {}
    for m in mappings:
        by_obligation.setdefault(m.obligation_id, []).append(m)

    aggregated: list[CriticDecision] = []

    for obligation in obligations:
        obl_mappings = by_obligation.get(obligation.id, [])
        if not obl_mappings:
            continue  # framework gap; not the Critic's concern
        if not _needs_review(obl_mappings, confidence_threshold):
            continue  # all mappings >= threshold; nothing to review

        result = call_with_logging(
            agent="critic",
            model=CRITIC_MODEL,
            system_prompt=system_blocks,
            user_message=_build_user_message(obligation, obl_mappings),
            output_schema=CriticOutput,
            run_dir=run_dir,
            prompt_version=prompt_version,
            metadata_factory=(
                lambda r, oid=obligation.id, n=len(obl_mappings): {
                    "obligation_id": oid,
                    "n_proposed_mappings": n,
                    "decision": (
                        r.decisions[0].decision if r.decisions else "(empty)"
                    ),
                }
            ),
        )

        if not result.decisions:
            _console.print(
                f"[yellow]critic: model returned no decision for "
                f"'{obligation.id}'; treating as unreviewed.[/yellow]"
            )
            continue

        # Take the first decision; the prompt asks for exactly one per call.
        decision = result.decisions[0]

        # Defensive rebinding: ensure obligation_id matches what we asked
        # about (the model occasionally echoes back a different id) and
        # that reviewed_mappings only contains real control IDs.
        if decision.obligation_id != obligation.id:
            decision = decision.model_copy(update={"obligation_id": obligation.id})
        cleaned_reviewed = [
            cid for cid in decision.reviewed_mappings if cid in valid_ids
        ]
        if cleaned_reviewed != decision.reviewed_mappings:
            decision = decision.model_copy(
                update={"reviewed_mappings": cleaned_reviewed}
            )

        if decision.decision == "flag_for_review":
            _console.print(
                f"[yellow]critic: flagged {obligation.id} for human review "
                f"(confidence {decision.confidence:.2f}).[/yellow]"
            )

        aggregated.append(decision)

    return CriticOutput(decisions=aggregated)
