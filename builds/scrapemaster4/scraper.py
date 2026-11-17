"""The real scraping pipeline the pasted drafts in the original upload never
actually got wired into any of the (empty) intended files.

fetch -> extract main content (readability-lxml) -> convert to text
(html2text) -> hand to an LLMClient for structured extraction -> optionally
follow pagination and repeat, up to max_pages.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import html2text
import requests
from bs4 import BeautifulSoup
from readability import Document

from api_management import LLMClient
from pagination_detector import detect_next_page_url

STRUCTURAL_NOISE_TAGS = ("nav", "footer", "header", "aside", "script", "style")

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
}


class FetchError(RuntimeError):
    """Raised after every retry has failed, carrying the last real cause."""


def fetch_html(url: str, *, max_retries: int = 3, retry_delay: float = 2.0, timeout: float = 10.0) -> str:
    last_exc: Optional[Exception] = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as exc:
            last_exc = exc
            logger.warning("fetch_html attempt %d/%d for %s failed: %s", attempt, max_retries, url, exc)
            if attempt < max_retries:
                time.sleep(retry_delay)
    raise FetchError(f"Failed to fetch {url} after {max_retries} attempts") from last_exc


def clean_html_to_text(html: str) -> str:
    """Strips nav/ads/boilerplate, then converts the remaining HTML to
    plain-ish text via html2text -- the two cleanup deps the scaffold's
    requirements.txt names (readability-lxml, html2text) but nothing in it
    ever actually called.

    readability-lxml's Document.summary() scores content by link density
    and text volume, which on a short page (verified against this build's
    own test fixture) doesn't reliably separate a <nav>/<footer> from the
    real article -- there's just not enough signal for the heuristic to
    work with. Semantic noise tags are stripped structurally first, which
    is unambiguous regardless of page length, then readability runs on
    what's left to catch density-based noise readability is actually good
    at (sidebars, related-post widgets, ad blocks)."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(STRUCTURAL_NOISE_TAGS):
        tag.decompose()
    main_html = Document(str(soup)).summary(html_partial=True)
    converter = html2text.HTML2Text()
    converter.ignore_links = True
    converter.ignore_images = True
    converter.body_width = 0
    return converter.handle(main_html).strip()


@dataclass
class ScrapeResult:
    url: str
    fields: dict
    scraped_at: str


def scrape(
    start_url: str,
    fields: list[str],
    llm_client: LLMClient,
    *,
    max_pages: int = 1,
    max_input_tokens: int = 6000,
) -> list[ScrapeResult]:
    """Scrapes start_url, extracts the requested fields via llm_client, and
    follows a detected "next page" link up to max_pages pages total."""
    results: list[ScrapeResult] = []
    url: Optional[str] = start_url
    pages_done = 0

    while url and pages_done < max_pages:
        html = fetch_html(url)
        text = clean_html_to_text(html)
        extracted = llm_client.extract(text, fields, max_input_tokens=max_input_tokens)
        results.append(
            ScrapeResult(
                url=url,
                fields=extracted,
                scraped_at=datetime.now(timezone.utc).isoformat(),
            )
        )
        pages_done += 1
        url = detect_next_page_url(url, html) if pages_done < max_pages else None

    return results
