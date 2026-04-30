import hashlib
from pathlib import Path

from rich.console import Console

from attestloop.llm import call_with_logging
from attestloop.registry import Regulation
from attestloop.schemas import ExtractorInput, ExtractorOutput, Obligation

_MODEL = "claude-sonnet-4-6"
_CHUNK_CHARS = 40_000
_CHUNK_OVERLAP = 2_000
_DEFAULT_OBLIGATION_PREFIX = "OBL"

_console = Console()


def _chunk_text(text: str, size: int, overlap: int) -> list[str]:
    if not text:
        return [""]
    if len(text) <= size:
        return [text]
    stride = size - overlap
    chunks: list[str] = []
    pos = 0
    while pos < len(text):
        chunks.append(text[pos:pos + size])
        if pos + size >= len(text):
            break
        pos += stride
    return chunks


def _build_user_message(
    input: ExtractorInput, chunk_text: str, chunk_index: int, total_chunks: int
) -> str:
    title = input.publication.title or "(no title)"
    chunk_marker = (
        f"This is chunk {chunk_index + 1} of {total_chunks} from a longer publication. "
        "Extract obligations only from the text in this chunk; downstream code "
        "deduplicates obligations whose requirement_text overlaps across chunks."
        if total_chunks > 1
        else ""
    )
    return (
        f"Regulation under consideration: {input.regulation_id}\n"
        f"Publication URL: {input.publication.url}\n"
        f"Publication title: {title}\n"
        f"{chunk_marker}\n\n"
        f"--- BEGIN PUBLICATION TEXT (chunk {chunk_index + 1}/{total_chunks}) ---\n"
        f"{chunk_text}\n"
        f"--- END PUBLICATION TEXT (chunk {chunk_index + 1}/{total_chunks}) ---"
    )


def _dedupe_obligations(obligations: list[Obligation]) -> tuple[list[Obligation], int]:
    """Case-insensitive substring dedup. Keeps the most-complete (longest) version.

    Iterating in order, for each candidate:
      - if any kept obligation's text contains the candidate's text → drop the candidate
        (the kept one is at least as complete)
      - else if any kept obligation's text is contained in the candidate's text →
        replace the kept entry with the candidate (candidate is more complete)
      - else → append as a new unique obligation

    Returns (kept_obligations, n_duplicates_removed).
    """
    kept: list[Obligation] = []
    removed = 0
    for candidate in obligations:
        cand_text = candidate.requirement_text.lower().strip()
        if not cand_text:
            removed += 1
            continue

        skip = False
        replaced = False
        for i, existing in enumerate(kept):
            existing_text = existing.requirement_text.lower().strip()
            if cand_text == existing_text or cand_text in existing_text:
                removed += 1
                skip = True
                break
            if existing_text in cand_text:
                kept[i] = candidate
                removed += 1
                replaced = True
                break
        if not (skip or replaced):
            kept.append(candidate)
    return kept, removed


def _infer_prefix(obligations: list[Obligation]) -> str:
    """Use the prefix the model already used (e.g. 'EUAIA-OBL' from 'EUAIA-OBL-001').
    Falls back to a generic 'OBL' if no recognisable pattern is found."""
    for obl in obligations:
        if "-" in obl.id:
            prefix, _, suffix = obl.id.rpartition("-")
            if prefix and suffix.isdigit():
                return prefix
    return _DEFAULT_OBLIGATION_PREFIX


def _renumber(obligations: list[Obligation], prefix: str) -> list[Obligation]:
    return [
        obl.model_copy(update={"id": f"{prefix}-{i + 1:03d}"})
        for i, obl in enumerate(obligations)
    ]


def extract(
    input: ExtractorInput, regulation: Regulation, run_dir: Path
) -> ExtractorOutput:
    system_prompt = regulation.extractor_prompt_path.read_text()
    prompt_version = hashlib.sha256(system_prompt.encode("utf-8")).hexdigest()

    cleaned = input.publication.cleaned_text
    chunks = _chunk_text(cleaned, _CHUNK_CHARS, _CHUNK_OVERLAP)
    n_chunks = len(chunks)

    if n_chunks > 1:
        _console.print(
            f"[yellow]extractor: extracting from {n_chunks} chunks "
            f"({len(cleaned):,} total chars, ~{_CHUNK_CHARS:,} per chunk, "
            f"{_CHUNK_OVERLAP:,} overlap).[/yellow]"
        )

    all_obligations: list[Obligation] = []
    for i, chunk in enumerate(chunks):
        result = call_with_logging(
            agent="extractor",
            model=_MODEL,
            system_prompt=system_prompt,
            user_message=_build_user_message(input, chunk, i, n_chunks),
            output_schema=ExtractorOutput,
            run_dir=run_dir,
            prompt_version=prompt_version,
            metadata_factory=(
                lambda r, ci=i, n=n_chunks, cl=len(chunk): {
                    "chunk_index": ci,
                    "total_chunks": n,
                    "chunk_chars": cl,
                    "chunk_obligation_count": len(r.obligations),
                }
            ),
        )
        all_obligations.extend(result.obligations)

    if n_chunks <= 1:
        return ExtractorOutput(obligations=all_obligations)

    deduped, removed = _dedupe_obligations(all_obligations)
    if removed > 0:
        _console.print(
            f"[yellow]extractor: deduplicated {removed} obligations "
            f"(case-insensitive substring match); {len(deduped)} remain "
            f"from {len(all_obligations)} raw extractions.[/yellow]"
        )
    prefix = _infer_prefix(deduped)
    renumbered = _renumber(deduped, prefix=prefix)
    return ExtractorOutput(obligations=renumbered)
