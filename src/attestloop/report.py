"""Report builder. Pulled out of pipeline.py so orchestration nodes can
build the final report.md without importing the CLI module."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

from attestloop.registry import Framework, Regulation
from attestloop.schemas import (
    ClassifierOutput,
    ExtractorOutput,
    MapperOutput,
    Obligation,
    Publication,
)

CLASSIFIER_MODEL = "claude-haiku-4-5-20251001"
EXTRACTOR_MODEL = "claude-sonnet-4-6"
MAPPER_MODEL = "claude-sonnet-4-6"


def sha256_of_path(path: Path) -> str:
    return hashlib.sha256(path.read_text().encode("utf-8")).hexdigest()


def aggregate_usage(run_dir: Path) -> tuple[float, int, int]:
    """Sum cost_usd / input_tokens / output_tokens across every per-agent
    JSON log in the run directory. Skips non-log artefacts."""
    cost = 0.0
    in_tok = 0
    out_tok = 0
    for log_path in run_dir.glob("*.json"):
        if log_path.name in {
            "publication.json",
            "obligations.json",
            "mappings.json",
            "run_metadata.json",
        }:
            continue
        try:
            entries = json.loads(log_path.read_text())
        except json.JSONDecodeError:
            continue
        if not isinstance(entries, list):
            continue
        for entry in entries:
            cost += float(entry.get("cost_usd", 0.0))
            in_tok += int(entry.get("input_tokens", 0))
            out_tok += int(entry.get("output_tokens", 0))
    return cost, in_tok, out_tok


_NULLISH_CELL_VALUES = {"", "null", "none"}


def _md_escape_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def _md_nullable_cell(value) -> str:
    """Render a possibly-empty / possibly-null-literal cell as an em-dash.
    Treats None, the strings 'null'/'None' (any case), and empty/whitespace
    strings as missing data — preventing the literal word "null" from
    leaking into the report when the LLM emits it for an optional field."""
    if value is None:
        return "—"
    s = str(value).strip()
    if s.lower() in _NULLISH_CELL_VALUES:
        return "—"
    return _md_escape_cell(s)


def _obligations_table(obligations: list[Obligation]) -> str:
    if not obligations:
        return "_No obligations were extracted._\n"
    header = (
        "| ID | Source | Requirement | Scope | Deadline | Evidence required |\n"
        "|---|---|---|---|---|---|\n"
    )
    rows = []
    for o in obligations:
        rows.append(
            "| {id} | {src} | {req} | {scope} | {dl} | {ev} |".format(
                id=_md_nullable_cell(o.id),
                src=_md_nullable_cell(o.source_paragraph),
                req=_md_nullable_cell(o.requirement_text),
                scope=_md_nullable_cell(o.scope),
                dl=_md_nullable_cell(o.deadline),
                ev=_md_nullable_cell(o.evidence_required),
            )
        )
    return header + "\n".join(rows) + "\n"


def _mappings_table(mappings, controls_by_id: dict) -> str:
    if not mappings:
        return "_No control mappings were produced._\n"
    header = (
        "| Obligation | Control ID | Function | Confidence | Reasoning |\n"
        "|---|---|---|---|---|\n"
    )
    rows = []
    for m in mappings:
        ctl = controls_by_id.get(m.control_id)
        function = ctl.function if ctl else "—"
        rows.append(
            "| {oid} | {cid} | {fn} | {conf:.2f} | {why} |".format(
                oid=_md_nullable_cell(m.obligation_id),
                cid=_md_nullable_cell(m.control_id),
                fn=_md_nullable_cell(function),
                conf=m.confidence,
                why=_md_nullable_cell(m.reasoning),
            )
        )
    return header + "\n".join(rows) + "\n"


def _unmapped_table(unmapped: list[Obligation]) -> str:
    if not unmapped:
        return "_All obligations received at least one high-confidence mapping._\n"
    header = (
        "| ID | Source | Requirement | Scope |\n"
        "|---|---|---|---|\n"
    )
    rows = []
    for o in unmapped:
        rows.append(
            "| {id} | {src} | {req} | {scope} |".format(
                id=_md_nullable_cell(o.id),
                src=_md_nullable_cell(o.source_paragraph),
                req=_md_nullable_cell(o.requirement_text),
                scope=_md_nullable_cell(o.scope),
            )
        )
    return header + "\n".join(rows) + "\n"


def build_in_scope_report(
    *,
    publication: Publication,
    classifier_output: ClassifierOutput,
    extractor_output: ExtractorOutput,
    mapper_output: MapperOutput,
    regulation: Regulation,
    framework: Framework,
    run_id: str,
    started_at: datetime,
    cost_usd: float,
    input_tokens: int,
    output_tokens: int,
) -> str:
    pub_title = publication.title or "(untitled)"
    obligations = extractor_output.obligations
    mapped_obligation_ids = {m.obligation_id for m in mapper_output.mappings}
    n_obl = len(obligations)
    n_mapped = sum(1 for o in obligations if o.id in mapped_obligation_ids)
    n_unmapped = n_obl - n_mapped

    summary_lines = [
        (
            f"Attestloop assessed \"{pub_title}\" against "
            f"{regulation.name} and identified {n_obl} binding obligation"
            f"{'' if n_obl == 1 else 's'}."
        ),
        (
            f"Of these, {n_mapped} were mapped to one or more subcategories "
            f"of {framework.name}; {n_unmapped} obligation"
            f"{'' if n_unmapped == 1 else 's'} had no high-confidence mapping."
        ),
        (
            "The full obligation list and proposed control mapping follow; "
            "this assessment is not legal advice."
        ),
    ]

    controls_by_id = {c.id: c for c in framework.controls}
    unmapped_obligations = [o for o in obligations if o.id not in mapped_obligation_ids]

    parts = [
        f"# Attestation report — {regulation.name}\n",
        f"**Source:** [{pub_title}]({publication.url})\n",
        f"**Run:** `{run_id}`\n",
        "\n## Executive summary\n",
        " ".join(summary_lines) + "\n",
        "\n## Obligations\n",
        _obligations_table(obligations),
        "\n## Control mappings\n",
        _mappings_table(mapper_output.mappings, controls_by_id),
        f"\n## Obligations with no high-confidence framework mapping ({n_unmapped})\n",
        (
            "These obligations were extracted from the source but no "
            f"{framework.name} subcategory cleared the mapper's 0.75 "
            "confidence floor. This is a deliberate audit-trail outcome — "
            "weak mappings are dropped rather than surfaced. Common causes "
            "are procedural duties on public authorities (registration, "
            "judicial pre-authorisation, notification) which the framework "
            "does not directly cover.\n\n"
        ),
        _unmapped_table(unmapped_obligations),
        "\n## Provenance\n",
        f"- Regulation: {regulation.name} (`{regulation.id}`, {regulation.jurisdiction})\n",
        f"- Framework: {framework.name} (`{framework.id}`, {len(framework.controls)} controls)\n",
        f"- Classifier model: `{CLASSIFIER_MODEL}`\n",
        f"- Extractor model: `{EXTRACTOR_MODEL}`\n",
        f"- Mapper model: `{MAPPER_MODEL}`\n",
        f"- Classifier prompt SHA-256: `{sha256_of_path(regulation.classifier_prompt_path)}`\n",
        f"- Extractor prompt SHA-256: `{sha256_of_path(regulation.extractor_prompt_path)}`\n",
        f"- Mapper prompt SHA-256: `{sha256_of_path(framework.mapper_prompt_path)}`\n",
        f"- Started at: {started_at.isoformat()}\n",
        f"- Total cost: ${cost_usd:.4f}\n",
        f"- Total tokens: {input_tokens:,} input / {output_tokens:,} output\n",
    ]
    return "".join(parts)


def build_out_of_scope_report(
    *,
    publication: Publication,
    classifier_output: ClassifierOutput,
    regulation: Regulation,
    framework: Framework,
    run_id: str,
    started_at: datetime,
    cost_usd: float,
    input_tokens: int,
    output_tokens: int,
) -> str:
    pub_title = publication.title or "(untitled)"
    return (
        f"# Attestation report — {regulation.name} (out of scope)\n\n"
        f"**Source:** [{pub_title}]({publication.url})\n\n"
        f"**Run:** `{run_id}`\n\n"
        "## Result\n\n"
        f"The classifier judged this publication **out of scope** for "
        f"{regulation.name}.\n\n"
        f"- Category: `{classifier_output.category}`\n"
        f"- Confidence: {classifier_output.confidence:.2f}\n\n"
        "**Reasoning:** "
        f"{classifier_output.reasoning}\n\n"
        "Extraction and mapping were skipped.\n\n"
        "## Provenance\n\n"
        f"- Regulation: {regulation.name} (`{regulation.id}`, {regulation.jurisdiction})\n"
        f"- Framework (not used): {framework.name} (`{framework.id}`)\n"
        f"- Classifier model: `{CLASSIFIER_MODEL}`\n"
        f"- Classifier prompt SHA-256: `{sha256_of_path(regulation.classifier_prompt_path)}`\n"
        f"- Started at: {started_at.isoformat()}\n"
        f"- Total cost: ${cost_usd:.4f}\n"
        f"- Total tokens: {input_tokens:,} input / {output_tokens:,} output\n"
    )
