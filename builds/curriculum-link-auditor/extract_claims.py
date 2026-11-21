"""Auto-extract RepoClaim entries from a curated list's own raw text,
instead of hand-writing each one -- the drop-in step this build was
missing for `/analyze-and-ship` when a source IS a curated list rather
than a single repo/tool.

Deliberately narrow about what it auto-extracts. A curated-list article
makes some claims in a shape regular enough to extract reliably
(a github.com link, a stated "N lesson(s)" figure, an archived/retired/
deprecated mention, a numbered-heading "by <Name>" byline) and some in a
shape that isn't (a claimed internal structure like "three parts: X, Y,
Z" varies too much in phrasing to regex reliably without false
positives). This module only extracts the first kind. Structure-keyword
claims stay a manual `RepoClaim` field, same as before -- extracting
them badly would be worse than not extracting them, the same "a
flagged mismatch should be strong evidence, not a guess" discipline
`check_author_attribution` already follows.
"""

from __future__ import annotations

import re

from curriculum_auditor import RepoClaim

_REPO_LINK_RE = re.compile(
    r"github\.com/([A-Za-z0-9][\w.-]*)/([A-Za-z0-9][\w.-]*?)"
    r"(?:\.git)?(?:[/?#][^\s)\]]*)?(?=[\s)\]]|$)"
)

_SECTION_HEADING_RE = re.compile(r"^\s*\d+\.\s+.+$", re.MULTILINE)

_LESSON_COUNT_RE = re.compile(r"(\d+)[\s-]*lesson", re.IGNORECASE)

_ARCHIVED_HINT_RE = re.compile(
    r"\barchived\b|\bretired\b|\bdeprecated\b|no longer maintained",
    re.IGNORECASE,
)

# "5. LLM Course by Maarten Grootendorst" / "## X by Jane Doe" --
# a numbered or markdown heading ending in "by <Name>". Capped at 4
# capitalized words so it doesn't run on into the next sentence.
_BYLINE_RE = re.compile(
    r"^\s*(?:#{1,6}\s*)?\d*\.?\s*.*?\bby\s+"
    r"([A-Z][\w.'-]*(?:\s+[A-Z][\w.'-]*){0,3})\s*$",
    re.MULTILINE,
)


def extract_repo_links(text: str) -> list[str]:
    """Every distinct "owner/repo" named by a github.com link in
    `text`, in first-seen order. A link into a sub-path of the repo
    (`.../issues/12`, `.../blob/main/x.py`, `.../tree/main/docs`) still
    resolves to that same repo -- the owner/repo pair is unambiguous
    from the URL regardless of what sub-path follows it, so a listicle
    linking to a repo's issues page is still citing that repo, not a
    different one."""
    seen: dict[str, None] = {}
    for match in _REPO_LINK_RE.finditer(text):
        owner, repo = match.group(1), match.group(2).rstrip(".")
        if not repo:
            continue
        seen.setdefault(f"{owner}/{repo}", None)
    return list(seen)


def split_into_sections(text: str) -> list[str]:
    """Split a curated-list article into one block per numbered-heading
    item ("1. Foo", "2. Bar", ...), the shape this kind of listicle
    almost always uses. Text before the first such heading (an intro)
    is dropped -- it names no specific repo to extract claims about."""
    starts = [m.start() for m in _SECTION_HEADING_RE.finditer(text)]
    if not starts:
        return [text]
    starts.append(len(text))
    return [text[starts[i]:starts[i + 1]] for i in range(len(starts) - 1)]


def extract_lesson_count_claim(section_text: str) -> int | None:
    match = _LESSON_COUNT_RE.search(section_text)
    return int(match.group(1)) if match else None


def extract_archived_claim(section_text: str) -> bool | None:
    """True if the section explicitly claims archived/retired/
    deprecated status; None (not False) when it says nothing either
    way -- silence isn't a claim of "not archived," so audit_repo_claim
    should skip the check rather than assert a claim nobody made."""
    return True if _ARCHIVED_HINT_RE.search(section_text) else None


def extract_author_byline(section_text: str) -> str | None:
    """The first "<heading> by <Name>" byline in the section, if the
    section's own heading line states one. Only looks at the first
    non-empty line (the heading itself), not the whole section, so a
    sentence elsewhere ending in "... written by the community" can't
    be mistaken for an authorship claim about the repo."""
    first_line = next((ln for ln in section_text.splitlines() if ln.strip()), "")
    match = _BYLINE_RE.match(first_line)
    return match.group(1).strip() if match else None


def auto_extract_manifest(text: str) -> list[RepoClaim]:
    """The full pipeline: split into sections, find each section's repo
    link(s), and build a RepoClaim per repo from whatever claims that
    section's text actually states. A section naming more than one repo
    link (rare, but the 10/12/20-repo listicles this applies to
    sometimes cross-reference an earlier entry) attaches its extracted
    claims to the FIRST repo link only, since the claims are stated
    about the section's own subject, not every link it happens to
    mention."""
    claims = []
    for section in split_into_sections(text):
        repos = extract_repo_links(section)
        if not repos:
            continue
        repo = repos[0]
        claims.append(
            RepoClaim(
                repo=repo,
                claimed_author=extract_author_byline(section),
                claimed_lesson_count=extract_lesson_count_claim(section),
                claimed_archived=extract_archived_claim(section),
            )
        )
    return claims
