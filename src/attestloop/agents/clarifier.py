"""Clarifier agent.

When the Classifier returns out_of_scope at low confidence (< 0.7), the
pipeline doesn't write the document off — it asks the Clarifier to
fetch extra signal from the publication (table of contents, first
pages, or section headings) and re-invoke the Classifier on an
augmented input. The Clarifier itself does not make a classification
decision; it augments the prompt and delegates to the existing
Classifier (Haiku 4.5). v6 task 3 introduces the agent and the
single-pass loop bound — there's no second clarification if the first
one still produces ambiguity."""
import re
from pathlib import Path

from rich.console import Console

from attestloop.agents.classifier import classify
from attestloop.registry import Regulation
from attestloop.schemas import (
    ClarifierOutput,
    ClassifierInput,
    ClassifierOutput,
    Publication,
)

_console = Console()

_TOC_HEADER_RE = re.compile(
    r"(?im)^\s*(table of contents|contents)\s*$",
)

# Recognise common section-heading shapes in regulator documents:
# "1.", "1.1", "1.2.3", "Article 5", "Section 4", "Chapter II", "Annex IV".
_HEADING_RE = re.compile(
    r"^(?:"
    r"\d+(?:\.\d+)*\.?"
    r"|Article\s+\d+(?:[a-z])?(?:\([0-9a-z]+\))*"
    r"|Section\s+\d+(?:\.\d+)*"
    r"|Chapter\s+(?:\d+|[IVXLCDM]+)"
    r"|Annex\s+(?:[IVXLCDM]+|\d+)"
    r")\b",
    re.IGNORECASE,
)

# Caps for each augmentation source so the augmented body stays inside
# the Classifier's 12 000-char input window with the original snippet.
_TOC_CHARS = 3000
_FIRST_PAGES_CHARS = 15_000
_HEADINGS_MAX = 50

# How much of the original cleaned text to retain in the re-classification
# input, alongside the appended additional context. 8000 + 3500 ≈ 12000
# (the Classifier's truncation cap), so the second classification sees
# both signals.
_ORIGINAL_RETAIN_CHARS = 8000
_ADDITIONAL_RETAIN_CHARS = 3500


def _extract_table_of_contents(text: str) -> str | None:
    match = _TOC_HEADER_RE.search(text)
    if not match:
        return None
    after = text[match.end() : match.end() + _TOC_CHARS].strip()
    return after or None


def _extract_section_headings(text: str) -> list[str]:
    headings: list[str] = []
    for line in text[:50_000].splitlines():
        stripped = line.strip()
        if 5 <= len(stripped) <= 120 and _HEADING_RE.match(stripped):
            headings.append(stripped)
            if len(headings) >= _HEADINGS_MAX:
                break
    return headings


def _extract_additional_context(cleaned_text: str) -> tuple[str, str]:
    """Return (extracted_text, context_source_label). Tries table of
    contents → section headings → first 5 pages, in order of
    informativeness."""
    toc = _extract_table_of_contents(cleaned_text)
    if toc and len(toc) >= 100:
        return toc, "table_of_contents"

    headings = _extract_section_headings(cleaned_text)
    if len(headings) >= 5:
        return "\n".join(headings), "section_headings"

    return cleaned_text[:_FIRST_PAGES_CHARS], "first_5_pages"


def _build_augmented_text(original_cleaned: str, extra: str, source: str) -> str:
    return (
        f"{original_cleaned[:_ORIGINAL_RETAIN_CHARS]}\n\n"
        f"--- ADDITIONAL CONTEXT FROM CLARIFIER (source: {source}) ---\n\n"
        f"{extra[:_ADDITIONAL_RETAIN_CHARS]}"
    )


def clarify_and_reclassify(
    publication: Publication,
    classification: ClassifierOutput,
    regulation: Regulation,
    run_dir: Path,
) -> ClarifierOutput:
    """Augment the publication's cleaned_text with additional context
    extracted from the document, then re-invoke the Classifier. The
    initial classification is preserved on the returned ClarifierOutput
    so the audit trail in clarifier.json is self-describing."""

    extra_text, source = _extract_additional_context(publication.cleaned_text)

    _console.print(
        f"[yellow]clarifier: re-classifying with additional context "
        f"(source={source}, {len(extra_text)} chars). Initial verdict was "
        f"{('in_scope' if classification.in_scope else 'out_of_scope')} "
        f"at {classification.confidence:.2f}.[/yellow]"
    )

    augmented_text = _build_augmented_text(
        publication.cleaned_text, extra_text, source
    )
    augmented_pub = publication.model_copy(update={"cleaned_text": augmented_text})

    reclassification = classify(
        ClassifierInput(publication=augmented_pub, regulation_id=regulation.id),
        regulation,
        run_dir,
    )

    _console.print(
        f"[yellow]clarifier: re-classification verdict "
        f"{('in_scope' if reclassification.in_scope else 'out_of_scope')} "
        f"at {reclassification.confidence:.2f}.[/yellow]"
    )

    return ClarifierOutput(
        initial_classification=classification,
        additional_context=extra_text,
        context_source=source,
        reclassification=reclassification,
    )
