"""Check a curated list's claims about external repos against the repos
themselves -- built from a real gap found while running the
deep-analysis-and-ship loop on a 12-repo "learn AI/LLM engineering"
roadmap article (see /notes/learning-path-12-repos-analysis.md).

That article got most of its checkable claims right (all 12 repos are
real, no link rot; huggingface/ml-intern really is archived, down to the
exact repo it moved to; microsoft/AI-For-Beginners really is a 24-lesson
curriculum; mlabonne/llm-course really is split into the three named
parts) -- but one claim was a real, well-evidenced error: it attributes
mlabonne/llm-course to "Maarten Grootendorst" (a real, different AI
figure -- BERTopic/KeyBERT's creator, now a Developer Relations Engineer
at Google DeepMind, co-author of a *different* LLM book). The repo's own
README names its actual author, Maxime Labonne (@maximelabonne), in
three places. Two real people, both real LLM-space authors, swapped.

This module is the reusable version of the by-hand check that found
that: given a repo's README text and a curated list's claims about it
(lesson count, archived status, structure keywords, claimed author),
report what holds up and what doesn't -- without a live network call,
so it's fully testable against committed fixture READMEs. A live
existence check (via `git ls-remote`, no GitHub API/token needed) is
kept as a separate, optional function so the deterministic checks never
depend on network access.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field


@dataclass
class RepoClaim:
    repo: str  # "owner/name"
    claimed_author: str | None = None
    claimed_lesson_count: int | None = None
    claimed_archived: bool | None = None
    claimed_structure_keywords: list[str] = field(default_factory=list)


@dataclass
class AuditResult:
    repo: str
    matches: list[str] = field(default_factory=list)
    mismatches: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return not self.mismatches and not self.flags


_LESSON_COUNT_RE = re.compile(r"(\d+)[\s-]*lesson", re.IGNORECASE)

_ARCHIVED_RE = re.compile(
    r"this (repo|repository|project) is archived|has been archived|"
    r"no longer maintained|is deprecated|has been retired|is retired",
    re.IGNORECASE,
)

def extract_lesson_count(readme_text: str) -> int | None:
    """The first "N lesson(s)" / "N-lesson" figure the README states
    about itself, or None if it never states one."""
    match = _LESSON_COUNT_RE.search(readme_text)
    return int(match.group(1)) if match else None


def detect_archived_banner(readme_text: str) -> tuple[bool, str | None]:
    """Whether the README itself declares the repo archived/retired/
    deprecated, and the matching line as evidence."""
    match = _ARCHIVED_RE.search(readme_text)
    if not match:
        return False, None
    line_start = readme_text.rfind("\n", 0, match.start()) + 1
    line_end = readme_text.find("\n", match.end())
    if line_end == -1:
        line_end = len(readme_text)
    return True, readme_text[line_start:line_end].strip()


# Hugging Face path segments that are site sections, not usernames --
# matching these as "handles" would be noise, not a real identity signal.
_HF_RESERVED_SEGMENTS = {
    "blog", "docs", "learn", "models", "spaces", "datasets", "papers",
    "posts", "join", "inference-api", "pricing", "about", "privacy",
    "terms", "chat",
}


def extract_maintainer_handles(readme_text: str) -> set[str]:
    """Candidate real-identity signals the README names about its own
    maintainer: X/Twitter handles and Hugging Face usernames found in
    its own links. Deliberately narrow (only two reliable, structured
    link patterns, with known Hugging Face site-section paths excluded)
    rather than a broad name-matching heuristic, so a hit is strong
    evidence, not noise from a site's own navigation links."""
    handles = set()
    for match in re.finditer(r"(?:twitter\.com|x\.com)/(\w+)", readme_text, re.IGNORECASE):
        handles.add(match.group(1).lower())
    for match in re.finditer(r"huggingface\.co/([\w-]+)", readme_text, re.IGNORECASE):
        handle = match.group(1).lower()
        if handle not in _HF_RESERVED_SEGMENTS:
            handles.add(handle)
    return handles


def _normalize_name(name: str) -> str:
    return re.sub(r"[^a-z]", "", name.lower())


def check_author_attribution(readme_text: str, claimed_author: str) -> tuple[bool, str]:
    """Does the README's own self-named handles plausibly match the
    claimed author? This is intentionally conservative: it only flags
    a mismatch when the README names real handles that share *none* of
    their normalized letters with the claimed name -- avoiding a false
    accusation when a README simply doesn't link any handle at all, or
    when the comparison itself is unreliable (e.g. no handles found)."""
    handles = extract_maintainer_handles(readme_text)
    if not handles:
        return True, "no self-named handle found in README; attribution not checkable from this signal"
    claimed_norm = _normalize_name(claimed_author)
    for handle in handles:
        if handle in claimed_norm or claimed_norm in handle:
            return True, f"README's own handle '{handle}' is consistent with claimed author '{claimed_author}'"
    return (
        False,
        f"README names handle(s) {sorted(handles)!r}, none consistent with "
        f"claimed author '{claimed_author}' -- likely misattribution",
    )


def check_structure_keywords(readme_text: str, keywords: list[str]) -> list[str]:
    """Keywords the curated list claims the repo's own structure uses
    (e.g. named section headers) that are NOT actually found in the
    README. An empty return means every claimed keyword checked out."""
    missing = []
    for kw in keywords:
        if kw.lower() not in readme_text.lower():
            missing.append(kw)
    return missing


def audit_repo_claim(readme_text: str, claim: RepoClaim) -> AuditResult:
    result = AuditResult(repo=claim.repo)

    if claim.claimed_lesson_count is not None:
        real_count = extract_lesson_count(readme_text)
        if real_count is None:
            result.flags.append("claimed a lesson count, but README states none to check against")
        elif real_count == claim.claimed_lesson_count:
            result.matches.append(f"lesson count: README itself states {real_count}, matching the claim")
        else:
            result.mismatches.append(
                f"lesson count: claim says {claim.claimed_lesson_count}, README states {real_count}"
            )

    if claim.claimed_archived is not None:
        is_archived, evidence = detect_archived_banner(readme_text)
        if is_archived == claim.claimed_archived:
            result.matches.append(
                f"archived status: claim says {claim.claimed_archived}, confirmed" + (f" ({evidence!r})" if evidence else "")
            )
        else:
            result.mismatches.append(
                f"archived status: claim says {claim.claimed_archived}, "
                f"README {'does' if is_archived else 'does not'} show an archived banner"
            )

    if claim.claimed_author is not None:
        ok, reason = check_author_attribution(readme_text, claim.claimed_author)
        if ok:
            result.matches.append(f"author attribution: {reason}")
        else:
            result.mismatches.append(f"author attribution: {reason}")

    if claim.claimed_structure_keywords:
        missing = check_structure_keywords(readme_text, claim.claimed_structure_keywords)
        if not missing:
            result.matches.append(
                f"structure: all {len(claim.claimed_structure_keywords)} claimed keyword(s) found in README"
            )
        else:
            result.mismatches.append(f"structure: missing claimed keyword(s) {missing!r}")

    return result


def audit_manifest(claims: list[RepoClaim], readme_by_repo: dict[str, str]) -> list[AuditResult]:
    results = []
    for claim in claims:
        readme_text = readme_by_repo.get(claim.repo)
        if readme_text is None:
            result = AuditResult(repo=claim.repo)
            result.flags.append("no README text supplied for this repo; nothing checked")
            results.append(result)
            continue
        results.append(audit_repo_claim(readme_text, claim))
    return results


def check_repo_exists_live(repo: str, timeout: float = 15.0) -> bool:
    """Live, no-token existence check via `git ls-remote` -- the only
    network call in this module, kept separate from the deterministic
    checks above so tests never depend on it."""
    try:
        proc = subprocess.run(
            ["git", "ls-remote", f"https://github.com/{repo}.git", "HEAD"],
            capture_output=True,
            timeout=timeout,
        )
        return proc.returncode == 0 and bool(proc.stdout.strip())
    except (subprocess.TimeoutExpired, OSError):
        return False
