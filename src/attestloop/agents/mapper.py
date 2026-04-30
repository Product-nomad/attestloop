import hashlib
import json
from pathlib import Path

from rich.console import Console

from attestloop.llm import call_with_logging
from attestloop.registry import Framework
from attestloop.schemas import (
    ControlMapping,
    MapperInput,
    MapperOutput,
    Obligation,
)

_MODEL = "claude-sonnet-4-6"

_console = Console()


def _format_controls(controls) -> str:
    rows = []
    for c in controls:
        rows.append(
            {
                "id": c.id,
                "function": c.function,
                "category": c.category,
                "subcategory_text": c.subcategory_text,
            }
        )
    return json.dumps(rows, indent=2)


def _build_user_message(obligation: Obligation, controls, framework_id: str) -> str:
    return (
        f"Framework: {framework_id}\n\n"
        "--- OBLIGATION ---\n"
        f"{obligation.model_dump_json(indent=2)}\n"
        "--- ALLOWED CONTROL IDS (return only IDs from this list) ---\n"
        f"{_format_controls(controls)}\n"
        "--- END ---"
    )


def map_to_controls(
    input: MapperInput, framework: Framework, run_dir: Path
) -> MapperOutput:
    system_prompt = framework.mapper_prompt_path.read_text()
    prompt_version = hashlib.sha256(system_prompt.encode("utf-8")).hexdigest()

    valid_ids = {c.id for c in framework.controls}
    aggregated: list[ControlMapping] = []

    for obligation in input.obligations:
        single = MapperInput(
            obligations=[obligation],
            controls=input.controls,
            framework_id=input.framework_id,
        )
        user_message = _build_user_message(
            obligation, single.controls, single.framework_id
        )

        result = call_with_logging(
            agent="mapper",
            model=_MODEL,
            system_prompt=system_prompt,
            user_message=user_message,
            output_schema=MapperOutput,
            run_dir=run_dir,
            prompt_version=prompt_version,
        )

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
            aggregated.append(mapping)

    return MapperOutput(mappings=aggregated)
