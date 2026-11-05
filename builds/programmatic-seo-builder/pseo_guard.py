"""
The thin-page guard the "Programmatic SEO Page Builder" article names as
its one hard rule ("strict about one thing: no thin pages"). Pure
functions, no file I/O, so they're directly unit-testable.

A page counts as thin when it has too little real body text, or when its
"unique facts" (the data-derived numbers/claims that make this page
different from every other page the template produces) fall below a
minimum — a page that's just the template's boilerplate with one word
swapped is exactly what this guard exists to catch.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

MIN_WORD_COUNT = 150
MIN_UNIQUE_FACTS = 4

_WORD_PATTERN = re.compile(r"\b\w+\b")


@dataclass(frozen=True)
class ThinPageReport:
    word_count: int
    unique_fact_count: int
    is_thin: bool
    reasons: tuple[str, ...]


def word_count(body_text: str) -> int:
    return len(_WORD_PATTERN.findall(body_text))


def check_page(
    body_text: str,
    unique_facts: dict,
    min_word_count: int = MIN_WORD_COUNT,
    min_unique_facts: int = MIN_UNIQUE_FACTS,
) -> ThinPageReport:
    reasons: list[str] = []
    count = word_count(body_text)
    if count < min_word_count:
        reasons.append(f"only {count} words (minimum {min_word_count})")

    fact_count = len(unique_facts)
    if fact_count < min_unique_facts:
        reasons.append(f"only {fact_count} unique data-derived fact(s) (minimum {min_unique_facts})")

    return ThinPageReport(
        word_count=count,
        unique_fact_count=fact_count,
        is_thin=len(reasons) > 0,
        reasons=tuple(reasons),
    )


def check_no_duplicate_facts(all_page_facts: list[dict]) -> list[tuple[int, int]]:
    """Returns (i, j) index pairs of pages whose fact dicts are byte-for-byte
    identical — a second real duplicate-content signal distinct from word
    count: two pages can both pass the word-count check while saying the
    exact same thing with different boilerplate wrapped around it."""
    duplicates: list[tuple[int, int]] = []
    for i in range(len(all_page_facts)):
        for j in range(i + 1, len(all_page_facts)):
            if all_page_facts[i] == all_page_facts[j]:
                duplicates.append((i, j))
    return duplicates
