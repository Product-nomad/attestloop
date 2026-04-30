import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console

from attestloop.agents.classifier import classify
from attestloop.agents.extractor import extract
from attestloop.agents.mapper import map_to_controls
from attestloop.fetch import fetch_publication
from attestloop.registry import Framework, Regulation, get_framework, get_regulation
from attestloop.schemas import (
    ClassifierInput,
    ClassifierOutput,
    ExtractorInput,
    ExtractorOutput,
    MapperInput,
    MapperOutput,
    Obligation,
    Publication,
    RunMetadata,
)

# Assumption: runs/ lives at the repo root next to src/ and tests/. The package
# itself is under src/attestloop/, so resolving up three parents lands at the
# repo root.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_RUNS_ROOT = _REPO_ROOT / "runs"

_CLASSIFIER_MODEL = "claude-haiku-4-5-20251001"
_EXTRACTOR_MODEL = "claude-sonnet-4-6"
_MAPPER_MODEL = "claude-sonnet-4-6"

_console = Console()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_text().encode("utf-8")).hexdigest()


def _aggregate_usage(run_dir: Path) -> tuple[float, int, int]:
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


def _md_escape_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


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
                id=_md_escape_cell(o.id),
                src=_md_escape_cell(o.source_paragraph),
                req=_md_escape_cell(o.requirement_text),
                scope=_md_escape_cell(o.scope),
                dl=_md_escape_cell(o.deadline or "—"),
                ev=_md_escape_cell(o.evidence_required or "—"),
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
                oid=_md_escape_cell(m.obligation_id),
                cid=_md_escape_cell(m.control_id),
                fn=_md_escape_cell(function),
                conf=m.confidence,
                why=_md_escape_cell(m.reasoning),
            )
        )
    return header + "\n".join(rows) + "\n"


def _build_in_scope_report(
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
        "\n## Provenance\n",
        f"- Regulation: {regulation.name} (`{regulation.id}`, {regulation.jurisdiction})\n",
        f"- Framework: {framework.name} (`{framework.id}`, {len(framework.controls)} controls)\n",
        f"- Classifier model: `{_CLASSIFIER_MODEL}`\n",
        f"- Extractor model: `{_EXTRACTOR_MODEL}`\n",
        f"- Mapper model: `{_MAPPER_MODEL}`\n",
        f"- Classifier prompt SHA-256: `{_sha256(regulation.classifier_prompt_path)}`\n",
        f"- Extractor prompt SHA-256: `{_sha256(regulation.extractor_prompt_path)}`\n",
        f"- Mapper prompt SHA-256: `{_sha256(framework.mapper_prompt_path)}`\n",
        f"- Started at: {started_at.isoformat()}\n",
        f"- Total cost: ${cost_usd:.4f}\n",
        f"- Total tokens: {input_tokens:,} input / {output_tokens:,} output\n",
    ]
    return "".join(parts)


def _build_out_of_scope_report(
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
        f"- Classifier model: `{_CLASSIFIER_MODEL}`\n"
        f"- Classifier prompt SHA-256: `{_sha256(regulation.classifier_prompt_path)}`\n"
        f"- Started at: {started_at.isoformat()}\n"
        f"- Total cost: ${cost_usd:.4f}\n"
        f"- Total tokens: {input_tokens:,} input / {output_tokens:,} output\n"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="attestloop",
        description="Run the Attestloop attestation pipeline against a single URL.",
    )
    parser.add_argument("url", help="URL of the regulator publication to assess.")
    parser.add_argument(
        "--regulation",
        default="eu_ai_act",
        help="Regulation registry id (default: eu_ai_act).",
    )
    parser.add_argument(
        "--framework",
        default="nist_ai_rmf",
        help="Framework registry id (default: nist_ai_rmf).",
    )
    args = parser.parse_args(argv)

    started_at = datetime.now(timezone.utc)
    run_id = started_at.strftime("%Y%m%d-%H%M%S")
    run_dir = _RUNS_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    regulation = get_regulation(args.regulation)
    framework = get_framework(args.framework)

    _console.print(f"[bold]Run {run_id}[/bold] -> {run_dir}")

    with _console.status("Fetching..."):
        publication = fetch_publication(args.url)
    (run_dir / "publication.json").write_text(publication.model_dump_json(indent=2))

    with _console.status("Classifying..."):
        classifier_output = classify(
            ClassifierInput(publication=publication, regulation_id=regulation.id),
            regulation,
            run_dir,
        )

    if not classifier_output.in_scope:
        cost, in_tok, out_tok = _aggregate_usage(run_dir)
        report = _build_out_of_scope_report(
            publication=publication,
            classifier_output=classifier_output,
            regulation=regulation,
            framework=framework,
            run_id=run_id,
            started_at=started_at,
            cost_usd=cost,
            input_tokens=in_tok,
            output_tokens=out_tok,
        )
        report_path = run_dir / "report.md"
        report_path.write_text(report)

        metadata = RunMetadata(
            run_id=run_id,
            started_at=started_at,
            regulation_id=regulation.id,
            framework_id=framework.id,
            total_cost_usd=cost,
            total_input_tokens=in_tok,
            total_output_tokens=out_tok,
        )
        (run_dir / "run_metadata.json").write_text(metadata.model_dump_json(indent=2))

        _console.print(
            f"[yellow]Out of scope; report written to[/yellow] {report_path}"
        )
        print(report_path)
        return 0

    with _console.status("Extracting..."):
        extractor_output = extract(
            ExtractorInput(publication=publication, regulation_id=regulation.id),
            regulation,
            run_dir,
        )
    (run_dir / "obligations.json").write_text(extractor_output.model_dump_json(indent=2))

    n = len(extractor_output.obligations)
    with _console.status(f"Mapping ({n} obligations)..."):
        mapper_output = map_to_controls(
            MapperInput(
                obligations=extractor_output.obligations,
                controls=framework.controls,
                framework_id=framework.id,
            ),
            framework,
            run_dir,
        )
    (run_dir / "mappings.json").write_text(mapper_output.model_dump_json(indent=2))

    cost, in_tok, out_tok = _aggregate_usage(run_dir)
    report = _build_in_scope_report(
        publication=publication,
        classifier_output=classifier_output,
        extractor_output=extractor_output,
        mapper_output=mapper_output,
        regulation=regulation,
        framework=framework,
        run_id=run_id,
        started_at=started_at,
        cost_usd=cost,
        input_tokens=in_tok,
        output_tokens=out_tok,
    )
    report_path = run_dir / "report.md"
    report_path.write_text(report)

    metadata = RunMetadata(
        run_id=run_id,
        started_at=started_at,
        regulation_id=regulation.id,
        framework_id=framework.id,
        total_cost_usd=cost,
        total_input_tokens=in_tok,
        total_output_tokens=out_tok,
    )
    (run_dir / "run_metadata.json").write_text(metadata.model_dump_json(indent=2))

    print(report_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
