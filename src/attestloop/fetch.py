import io
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import httpx
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from rich.console import Console
from selectolax.parser import HTMLParser

from attestloop.schemas import Publication

_USER_AGENT = "attestloop/0.1.0 (+regulatory-attestation-pipeline)"
_FETCH_TIMEOUT_SECONDS = 30.0
_STRIP_TAGS = ("script", "style", "noscript", "nav", "header", "footer", "aside", "form")
_MIN_USABLE_CHARS = 200

# CELEX identifiers are sector(1) + year(4) + type(1-2 letters) + number(4+ digits).
# Matches both ":" and URL-encoded "%3A" between the literal "CELEX" and the id.
_CELEX_RE = re.compile(r"CELEX(?::|%3A)([0-9]{5,6}[A-Z]+[0-9]+)", re.IGNORECASE)

_console = Console()


class EmptyPublicationError(RuntimeError):
    """Raised when no candidate URL produced enough usable text to classify."""


def _clean_text(html: str) -> tuple[str | None, str]:
    tree = HTMLParser(html)

    title_node = tree.css_first("title")
    title = title_node.text(strip=True) if title_node else None

    for selector in _STRIP_TAGS:
        for node in tree.css(selector):
            node.decompose()

    # Assumption: <main> or <article> is the publication body when present;
    # otherwise fall back to <body>, then to the whole tree. This keeps boilerplate
    # out of cleaned_text on standard regulator publications without over-fitting.
    main_node = tree.css_first("main") or tree.css_first("article") or tree.body or tree.root
    text = main_node.text(separator="\n", strip=True) if main_node else ""

    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return title, text


def _is_pdf_url(url: str) -> bool:
    parsed = urlparse(url)
    return "/PDF/" in url or parsed.path.lower().endswith(".pdf")


def _looks_like_pdf_bytes(content: bytes) -> bool:
    """Magic-byte sniff: a real PDF starts with the literal '%PDF-' header."""
    return content[:5] == b"%PDF-"


def _looks_like_filename(value: str) -> bool:
    """Heuristic for "this title looks like the URL filename": numeric-only
    strings (e.g. '112367') are the canonical case from the Commission
    newsroom redirect endpoint."""
    return value.isdigit()


def _title_from_body(text: str) -> str | None:
    """Scan the first 1000 characters of the cleaned body for the first
    non-trivial line plausibly being the document title: 30-200 chars long,
    not all-uppercase (rules out section banners like 'EUROPEAN COMMISSION'),
    and contains at least one space (rules out filename-like single tokens)."""
    head = text[:1000]
    for raw_line in head.splitlines():
        line = raw_line.strip()
        if 30 <= len(line) <= 200 and not line.isupper() and " " in line:
            return line
    return None


def _extract_pdf_text(content: bytes, source_url: str) -> tuple[str | None, str]:
    reader = PdfReader(io.BytesIO(content))

    pages: list[str] = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:  # pypdf raises a variety of types per-page; isolate per-page failures
            pages.append("")
    text = "\n\n".join(p for p in pages if p)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    # Title resolution precedence: PDF /Title metadata (if non-empty and not
    # a numeric filename) → first plausible body line → URL filename fallback.
    title: str | None = None
    if reader.metadata is not None:
        meta_title = reader.metadata.title
        if meta_title:
            title_str = str(meta_title).strip()
            if title_str and not _looks_like_filename(title_str):
                title = title_str

    if not title:
        title = _title_from_body(text)

    if not title:
        parsed = urlparse(source_url)
        filename = parsed.path.rstrip("/").rpartition("/")[2]
        title = filename or None

    return title, text


def resolve_eur_lex_url(url: str) -> list[str]:
    """If the URL contains a CELEX identifier, return ordered candidate content
    URLs (original, then HTML-only view, then PDF view). Otherwise return the
    URL unchanged. Duplicates are removed while preserving order."""

    match = _CELEX_RE.search(url)
    if not match:
        return [url]

    celex_id = match.group(1).upper()
    candidates = [
        url,
        f"https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:{celex_id}",
        f"https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:{celex_id}",
    ]
    return list(dict.fromkeys(candidates))


def _write_fetch_log(
    run_dir: Path | None, source: str, candidate_url: str, final_url: str
) -> None:
    if run_dir is None:
        return
    body = f"# Source: {source}\n# URL: {candidate_url}\n"
    if final_url != candidate_url:
        body += f"# Final URL (after redirects): {final_url}\n"
    (run_dir / "fetch.log").write_text(body)


def fetch_publication(url: str, run_dir: Path | None = None) -> Publication:
    headers = {"User-Agent": _USER_AGENT}
    candidates = resolve_eur_lex_url(url)
    attempts: list[str] = []

    with httpx.Client(
        headers=headers, timeout=_FETCH_TIMEOUT_SECONDS, follow_redirects=True
    ) as client:
        for candidate in candidates:
            try:
                response = client.get(candidate)
                response.raise_for_status()
            except httpx.HTTPError as e:
                _console.print(
                    f"[yellow]fetch: {candidate} failed: {e!r}[/yellow]"
                )
                attempts.append(f"{candidate} (failed: {e!r})")
                continue

            content_type = response.headers.get("content-type", "").lower()
            final_url = str(response.url)

            # Detection precedence: magic bytes (ground truth) > Content-Type
            # (server hint) > URL pattern (heuristic). Use the post-redirect URL
            # for the URL check so newsroom-style redirects to a .pdf target
            # are caught.
            if _looks_like_pdf_bytes(response.content):
                source_kind = "PDF (magic bytes)"
                parse_as_pdf = True
            elif content_type.startswith("application/pdf"):
                source_kind = "PDF (content-type)"
                parse_as_pdf = True
            elif _is_pdf_url(final_url):
                source_kind = "PDF (URL)"
                parse_as_pdf = True
            else:
                source_kind = "HTML"
                parse_as_pdf = False

            if parse_as_pdf:
                try:
                    title, cleaned_text = _extract_pdf_text(response.content, final_url)
                except (PdfReadError, ValueError, OSError) as e:
                    _console.print(
                        f"[yellow]fetch: {candidate} PDF parse failed: {e!r}[/yellow]"
                    )
                    attempts.append(f"{candidate} (failed: PDF parse {e!r})")
                    continue
                raw_html = ""
            else:
                raw_html = response.text
                title, cleaned_text = _clean_text(raw_html)

            usable_chars = len(cleaned_text.strip())
            if usable_chars >= _MIN_USABLE_CHARS:
                _write_fetch_log(run_dir, source_kind, candidate, final_url)
                return Publication(
                    url=candidate,
                    title=title,
                    raw_html=raw_html,
                    cleaned_text=cleaned_text,
                    fetched_at=datetime.now(timezone.utc),
                )

            _console.print(
                f"[yellow]fetch: {candidate} [{source_kind}] produced only "
                f"{usable_chars} usable chars (< {_MIN_USABLE_CHARS}); trying "
                "next candidate.[/yellow]"
            )
            attempts.append(
                f"{candidate} [{source_kind}, insufficient: {usable_chars} chars]"
            )

    raise EmptyPublicationError(
        f"No candidate URL produced >= {_MIN_USABLE_CHARS} chars of usable "
        "content. URLs tried:\n  - " + "\n  - ".join(attempts)
    )
