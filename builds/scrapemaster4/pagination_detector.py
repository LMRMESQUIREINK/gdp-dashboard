"""Finds the next page's URL in a listing page, if there is one.

A real heuristic, not an LLM call: `rel="next"` first (the standards-based
signal, when a site bothers to set it), then common "next page" link text,
checked in that order so a page that sets both never gets two different
answers from two separate passes.
"""

from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

_NEXT_TEXT_PATTERN = re.compile(r"^\s*(next|older|more|›|»|→)\b|^\s*(›|»|→)\s*$", re.IGNORECASE)


def detect_next_page_url(current_url: str, html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")

    rel_next = soup.find("a", attrs={"rel": re.compile(r"\bnext\b", re.IGNORECASE)})
    if rel_next and rel_next.get("href"):
        return urljoin(current_url, rel_next["href"])

    link_next = soup.find("link", attrs={"rel": re.compile(r"\bnext\b", re.IGNORECASE)})
    if link_next and link_next.get("href"):
        return urljoin(current_url, link_next["href"])

    for anchor in soup.find_all("a", href=True):
        text = anchor.get_text(strip=True)
        if text and _NEXT_TEXT_PATTERN.match(text):
            return urljoin(current_url, anchor["href"])

    return None
