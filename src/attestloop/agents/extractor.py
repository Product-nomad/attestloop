import hashlib
from pathlib import Path

from rapidfuzz import fuzz
from rich.console import Console

from attestloop.llm import call_with_logging
from attestloop.registry import Regulation
from attestloop.schemas import ExtractorInput, ExtractorOutput, Obligation

_MODEL = "claude-sonnet-4-6"
_CHUNK_CHARS = 40_000
_CHUNK_OVERLAP = 2_000
_DEFAULT_OBLIGATION_PREFIX = "OBL"
_DEDUP_SIMILARITY_FLOOR = 80

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


def _merge_optional_fields(winner: Obligation, loser: Obligation) -> Obligation:
    """If the winner's deadline / evidence_required are empty or None, copy
    the loser's non-empty value into the winner. Returns the (possibly
    updated) winner."""
    updates: dict[str, str] = {}
    if not winner.deadline and loser.deadline:
        updates["deadline"] = loser.deadline
    if not winner.evidence_required and loser.evidence_required:
        updates["evidence_required"] = loser.evidence_required
    if updates:
        return winner.model_copy(update=updates)
    return winner


def _dedupe_obligations(
    obligations: list[Obligation], chunk_indices: list[int]
) -> tuple[list[Obligation], int]:
    """Fuzzy dedup using rapidfuzz token_set_ratio. Two obligations are
    duplicates if their requirement_text similarity score >= 80. When
    duplicates are found, keep the one with the more specific (longer)
    source_paragraph; on ties, keep the earlier-extracted obligation.
    Optional fields (deadline, evidence_required) from the loser are merged
    into the winner if the winner's are empty.

    Each merge is logged via rich. Returns (kept_obligations, n_merged).
    """
    kept: list[Obligation] = []
    kept_chunks: list[int] = []
    n_merged = 0

    for candidate, cand_chunk in zip(obligations, chunk_indices):
        cand_text = candidate.requirement_text.strip()
        if not cand_text:
            n_merged += 1
            continue

        best_idx = -1
        best_score = 0
        for i, existing in enumerate(kept):
            score = int(fuzz.token_set_ratio(cand_text, existing.requirement_text))
            if score >= _DEDUP_SIMILARITY_FLOOR and score > best_score:
                best_score = score
                best_idx = i

        if best_idx < 0:
            kept.append(candidate)
            kept_chunks.append(cand_chunk)
            continue

        existing = kept[best_idx]
        existing_chunk = kept_chunks[best_idx]
        cand_src_len = len(candidate.source_paragraph)
        existing_src_len = len(existing.source_paragraph)

        if cand_src_len > existing_src_len:
            winner, loser = candidate, existing
            winner_chunk, loser_chunk = cand_chunk, existing_chunk
        else:
            # Equal-length sources: keep the earlier-extracted (existing) one.
            winner, loser = existing, candidate
            winner_chunk, loser_chunk = existing_chunk, cand_chunk

        winner = _merge_optional_fields(winner, loser)
        kept[best_idx] = winner
        kept_chunks[best_idx] = winner_chunk

        _console.print(
            f"[yellow]extractor: merging {loser.id} (chunk "
            f"{loser_chunk + 1}, similarity {best_score}) into "
            f"{winner.id} (chunk {winner_chunk + 1})[/yellow]"
        )
        n_merged += 1

    return kept, n_merged


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
    chunk_indices: list[int] = []
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
        for obl in result.obligations:
            all_obligations.append(obl)
            chunk_indices.append(i)

    if n_chunks <= 1:
        _console.print(
            f"[yellow]extractor: deduplication merged 0 obligations; "
            f"final count {len(all_obligations)}[/yellow]"
        )
        return ExtractorOutput(obligations=all_obligations)

    deduped, n_merged = _dedupe_obligations(all_obligations, chunk_indices)
    _console.print(
        f"[yellow]extractor: deduplication merged {n_merged} obligations; "
        f"final count {len(deduped)}[/yellow]"
    )
    prefix = _infer_prefix(deduped)
    renumbered = _renumber(deduped, prefix=prefix)
    return ExtractorOutput(obligations=renumbered)
