import re
from datetime import datetime, timezone

import httpx
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


def fetch_publication(url: str) -> Publication:
    headers = {"User-Agent": _USER_AGENT}
    candidates = resolve_eur_lex_url(url)
    attempts: list[str] = []

    with httpx.Client(
        headers=headers, timeout=_FETCH_TIMEOUT_SECONDS, follow_redirects=True
    ) as client:
        for candidate in candidates:
            if "/PDF/" in candidate:
                _console.print(
                    f"[yellow]fetch: skipping PDF candidate {candidate} "
                    "(binary fetch not supported in v1).[/yellow]"
                )
                attempts.append(f"{candidate} (skipped: PDF)")
                continue

            try:
                response = client.get(candidate)
                response.raise_for_status()
            except httpx.HTTPError as e:
                _console.print(
                    f"[yellow]fetch: {candidate} failed: {e!r}[/yellow]"
                )
                attempts.append(f"{candidate} (failed: {e!r})")
                continue

            raw_html = response.text
            title, cleaned_text = _clean_text(raw_html)
            usable_chars = len(cleaned_text.strip())

            if usable_chars >= _MIN_USABLE_CHARS:
                return Publication(
                    url=candidate,
                    title=title,
                    raw_html=raw_html,
                    cleaned_text=cleaned_text,
                    fetched_at=datetime.now(timezone.utc),
                )

            _console.print(
                f"[yellow]fetch: {candidate} produced only {usable_chars} "
                f"usable chars (< {_MIN_USABLE_CHARS}); trying next candidate.[/yellow]"
            )
            attempts.append(f"{candidate} (insufficient: {usable_chars} chars)")

    raise EmptyPublicationError(
        f"No candidate URL produced >= {_MIN_USABLE_CHARS} chars of usable "
        "content. URLs tried:\n  - " + "\n  - ".join(attempts)
    )
