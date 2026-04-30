import re
from datetime import datetime, timezone

import httpx
from selectolax.parser import HTMLParser

from attestloop.schemas import Publication

_USER_AGENT = "attestloop/0.1.0 (+regulatory-attestation-pipeline)"
_FETCH_TIMEOUT_SECONDS = 30.0
_STRIP_TAGS = ("script", "style", "noscript", "nav", "header", "footer", "aside", "form")


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


def fetch_publication(url: str) -> Publication:
    headers = {"User-Agent": _USER_AGENT}
    with httpx.Client(
        headers=headers, timeout=_FETCH_TIMEOUT_SECONDS, follow_redirects=True
    ) as client:
        response = client.get(url)
        response.raise_for_status()
        raw_html = response.text

    title, cleaned_text = _clean_text(raw_html)
    return Publication(
        url=url,
        title=title,
        raw_html=raw_html,
        cleaned_text=cleaned_text,
        fetched_at=datetime.now(timezone.utc),
    )
