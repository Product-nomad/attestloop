import hashlib
import json
from pathlib import Path

from rich.console import Console

from attestloop.llm import call_with_logging
from attestloop.registry import Framework
from attestloop.schemas import (
    Control,
    ControlMapping,
    MapperInput,
    MapperOutput,
    Obligation,
)

_MODEL = "claude-sonnet-4-6"
_CONTROLS_HEADER = (
    "## Allowed control catalogue (the only IDs you may return)\n"
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


def _build_user_message(obligation: Obligation, framework_id: str) -> str:
    return (
        f"Framework: {framework_id}\n\n"
        "--- OBLIGATION ---\n"
        f"{obligation.model_dump_json(indent=2)}\n"
        "--- END ---"
    )


def map_to_controls(
    input: MapperInput, framework: Framework, run_dir: Path
) -> MapperOutput:
    system_prompt_text = framework.mapper_prompt_path.read_text()
    prompt_version = hashlib.sha256(system_prompt_text.encode("utf-8")).hexdigest()

    # Static across all per-obligation calls in the run: the prompt instructions
    # and the full controls catalogue. Concatenated into a single text block
    # marked with cache_control so Anthropic's prompt cache catches every call
    # after the first.
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
    aggregated: list[ControlMapping] = []

    for obligation in input.obligations:
        result = call_with_logging(
            agent="mapper",
            model=_MODEL,
            system_prompt=system_blocks,
            user_message=_build_user_message(obligation, input.framework_id),
            output_schema=MapperOutput,
            run_dir=run_dir,
            prompt_version=prompt_version,
            metadata_factory=(
                lambda r, oid=obligation.id: {
                    "obligation_id": oid,
                    "returned_mapping_count": len(r.mappings),
                }
            ),
        )

        kept_for_obligation: list[ControlMapping] = []
        for mapping in result.mappings:
            if mapping.control_id not in valid_ids:
                _console.print(
                    f"[yellow]mapper: discarding unknown control_id "
                    f"'{mapping.control_id}' for obligation "
                    f"'{obligation.id}'.[/yellow]"
                )
                continue
            if mapping.obligation_id != obligation.id:
                # Assumption: the mapper sometimes echoes back a different
                # obligation_id; rebind to the obligation we actually asked
                # about so downstream tables are coherent.
                mapping = mapping.model_copy(update={"obligation_id": obligation.id})
            kept_for_obligation.append(mapping)

        if not kept_for_obligation:
            _console.print(
                f"[yellow]mapper: no high-confidence mapping for obligation "
                f"'{obligation.id}'; recorded as unmapped in the report.[/yellow]"
            )
        aggregated.extend(kept_for_obligation)

    return MapperOutput(mappings=aggregated)
