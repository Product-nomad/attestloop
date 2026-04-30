import hashlib
from pathlib import Path

from attestloop.llm import call_with_logging
from attestloop.registry import Regulation
from attestloop.schemas import ClassifierInput, ClassifierOutput

_MODEL = "claude-haiku-4-5-20251001"
_MAX_BODY_CHARS = 12_000


def _build_user_message(input: ClassifierInput) -> str:
    title = input.publication.title or "(no title)"
    body = input.publication.cleaned_text[:_MAX_BODY_CHARS]
    return (
        f"Regulation under consideration: {input.regulation_id}\n"
        f"Publication URL: {input.publication.url}\n"
        f"Publication title: {title}\n\n"
        f"--- BEGIN PUBLICATION TEXT ---\n{body}\n--- END PUBLICATION TEXT ---"
    )


def classify(
    input: ClassifierInput, regulation: Regulation, run_dir: Path
) -> ClassifierOutput:
    system_prompt = regulation.classifier_prompt_path.read_text()
    prompt_version = hashlib.sha256(system_prompt.encode("utf-8")).hexdigest()

    return call_with_logging(
        agent="classifier",
        model=_MODEL,
        system_prompt=system_prompt,
        user_message=_build_user_message(input),
        output_schema=ClassifierOutput,
        run_dir=run_dir,
        prompt_version=prompt_version,
    )
