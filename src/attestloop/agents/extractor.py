import hashlib
from pathlib import Path

from rich.console import Console

from attestloop.llm import call_with_logging
from attestloop.registry import Regulation
from attestloop.schemas import ExtractorInput, ExtractorOutput

_MODEL = "claude-sonnet-4-6"
_MAX_BODY_CHARS = 50_000

_console = Console()


def _build_user_message(input: ExtractorInput) -> str:
    title = input.publication.title or "(no title)"
    body = input.publication.cleaned_text
    if len(body) > _MAX_BODY_CHARS:
        _console.print(
            f"[yellow]extractor: publication body is {len(body):,} chars; "
            f"truncating to {_MAX_BODY_CHARS:,} for the LLM call.[/yellow]"
        )
        body = body[:_MAX_BODY_CHARS]
    return (
        f"Regulation under consideration: {input.regulation_id}\n"
        f"Publication URL: {input.publication.url}\n"
        f"Publication title: {title}\n\n"
        f"--- BEGIN PUBLICATION TEXT ---\n{body}\n--- END PUBLICATION TEXT ---"
    )


def extract(
    input: ExtractorInput, regulation: Regulation, run_dir: Path
) -> ExtractorOutput:
    system_prompt = regulation.extractor_prompt_path.read_text()
    prompt_version = hashlib.sha256(system_prompt.encode("utf-8")).hexdigest()

    return call_with_logging(
        agent="extractor",
        model=_MODEL,
        system_prompt=system_prompt,
        user_message=_build_user_message(input),
        output_schema=ExtractorOutput,
        run_dir=run_dir,
        prompt_version=prompt_version,
    )
