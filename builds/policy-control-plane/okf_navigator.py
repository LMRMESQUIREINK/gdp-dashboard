"""A standalone, independent implementation of Google's real Open Knowledge
Format (OKF) v0.2 navigation, trust-tier, and lifecycle-staleness rules.

Built from a pasted article bundle ("Google's New OKF Could Change How We
Build RAG Systems for AI Agents," plus four companion articles by Natarajan
Selvaraj). Before writing any code, Google's real repo
(`GoogleCloudPlatform/knowledge-catalog`, Apache 2.0) was cloned and its real
`okf/SPEC.md` (v0.2) read in full -- every mechanism below is implemented
against that spec text, not the article's paraphrase of it, and not copied
from the real reference agent's own Python code (which also exists in that
repo but was not read).

Three mechanisms, each tied to a specific spec section:

- Concept parsing (YAML frontmatter + Markdown body) and link resolution,
  per SPEC.md section 6 -- both the "recommended" absolute bundle-relative
  form (a link beginning with "/") and the ordinary relative form
  ("./other.md", "../dir/other.md") are supported, and a link to a concept
  that doesn't exist in the bundle is tolerated, not treated as an error --
  the spec states this explicitly ("not-yet-written knowledge").
- Trust tiers, per SPEC.md section 5.3: exactly three tiers (unverified,
  machine-confirmed, human-reviewed), derived from whether any `verified`
  entry's `by` field starts with "human:". A concept with no trust
  frontmatter at all is still a valid, consumable concept (the spec is
  explicit that consumers MUST NOT reject it) -- this module never raises on
  an untrusted or unverified concept, only reports its tier.
- Lifecycle staleness, per SPEC.md section 5.5: a concept is stale exactly
  when `now >= stale_after` (an absolute instant, never a relative TTL).

The fourth mechanism -- bounded-depth link navigation -- is this project's own
addition, built directly from the article's own worked example (an
authentication-token-expiration change, discovered by following
Authentication Service -> Token Policy / API Gateway / Customer Login rather
than loading an entire knowledge base into context): "progressive disclosure"
as the article names it, implemented here as a real breadth-first traversal
bounded by hop count, never a full-bundle context dump.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import re

import yaml

_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")
_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n?(.*)\Z", re.DOTALL)


class OkfParseError(ValueError):
    """Raised only for genuinely malformed input (unparsable YAML frontmatter
    or a missing frontmatter block) -- never for a concept that is merely
    unverified, untrusted, or carries a broken link. Per SPEC.md section 11,
    those are all normal, consumable states, not errors."""


@dataclass(frozen=True)
class Concept:
    path: str  # bundle-relative, forward-slash, normalized (no leading "/")
    frontmatter: dict
    body: str
    links: tuple[str, ...]  # raw link targets as written, unresolved

    @property
    def type(self) -> str | None:
        return self.frontmatter.get("type")

    @property
    def title(self) -> str | None:
        return self.frontmatter.get("title")

    @property
    def status(self) -> str:
        # SPEC.md 5.4: absent status => "stable".
        return self.frontmatter.get("status", "stable")


def parse_concept(text: str, path: str) -> Concept:
    """Parses one OKF concept file's raw text. `path` is this concept's own
    bundle-relative path, used only to label the result (link resolution
    happens separately, in resolve_link)."""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        raise OkfParseError(f"{path}: no YAML frontmatter block found")
    raw_frontmatter, body = m.group(1), m.group(2)
    try:
        frontmatter = yaml.safe_load(raw_frontmatter) or {}
    except yaml.YAMLError as exc:
        raise OkfParseError(f"{path}: invalid YAML frontmatter: {exc}") from exc
    if not isinstance(frontmatter, dict):
        raise OkfParseError(f"{path}: frontmatter must be a YAML mapping")
    links = tuple(target for _text, target in _LINK_RE.findall(body))
    return Concept(path=path.lstrip("/"), frontmatter=frontmatter, body=body, links=links)


def load_bundle(root: Path) -> dict[str, Concept]:
    """Walks root for every .md file and parses the ones that are OKF
    concepts. Keys are bundle-relative, forward-slash paths.

    Not every .md file in a real bundle's directory tree is necessarily an
    OKF concept -- a plain README or, as here, a copied upstream LICENSE file
    carries no frontmatter block at all. Such a file is silently skipped, not
    treated as an error: it was never a concept to begin with. A file that
    DOES open a frontmatter block (starts with "---") but then fails to parse
    -- invalid YAML, or a non-mapping frontmatter -- is a genuinely malformed
    concept file, and that still raises immediately (OkfParseError), naming
    the file. SPEC.md's tolerance is for broken *links* between concepts, not
    for a malformed concept file."""
    bundle: dict[str, Concept] = {}
    for md_path in sorted(root.rglob("*.md")):
        rel = md_path.relative_to(root).as_posix()
        text = md_path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            continue
        bundle[rel] = parse_concept(text, rel)
    return bundle


def resolve_link(from_path: str, target: str) -> str | None:
    """Resolves one markdown link target against the concept that contains it,
    per SPEC.md section 6.1/6.2. Returns None for anything that isn't a
    same-bundle markdown-file reference (an external http(s) URL, or a link
    with no .md extension) -- those aren't concept links to navigate.

    - A leading "/" is bundle-root-relative (the spec's "recommended" form).
    - Anything else is resolved relative to from_path's own directory,
      including ".." segments.
    """
    if target.startswith(("http://", "https://")):
        return None
    if not target.endswith(".md"):
        return None
    if target.startswith("/"):
        resolved = Path(target.lstrip("/"))
    else:
        resolved = (Path(from_path).parent / target)
    # Normalize ".." / "." segments without touching the real filesystem.
    parts: list[str] = []
    for part in resolved.as_posix().split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    return "/".join(parts)


_HUMAN_PREFIX = "human:"


def trust_tier(concept: Concept) -> str:
    """SPEC.md 5.3, implemented exactly: no `verified` key => "unverified";
    verified by non-human: actors only => "machine-confirmed"; verified by at
    least one human:<id> actor => "human-reviewed". This is purely advisory
    (the spec says so explicitly) -- never used here to gate access or raise."""
    verified = concept.frontmatter.get("verified")
    if not verified:
        return "unverified"
    if isinstance(verified, dict):
        verified = [verified]
    for entry in verified:
        by = (entry or {}).get("by", "")
        if isinstance(by, str) and by.startswith(_HUMAN_PREFIX):
            return "human-reviewed"
    return "machine-confirmed"


def is_stale(concept: Concept, now: datetime) -> bool | None:
    """SPEC.md 5.5: stale iff now >= stale_after (an absolute instant).
    Returns None when the concept declares no stale_after at all -- that is
    not the same as "not stale"; it means staleness is simply undeclared."""
    raw = concept.frontmatter.get("stale_after")
    if raw is None:
        return None
    stale_after = raw if isinstance(raw, datetime) else datetime.fromisoformat(str(raw))
    if stale_after.tzinfo is None:
        stale_after = stale_after.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return now >= stale_after


@dataclass(frozen=True)
class NavigationStep:
    path: str
    depth: int
    via: str | None  # the concept path that linked here, or None for the start


def navigate(bundle: dict[str, Concept], start: str, max_hops: int) -> list[NavigationStep]:
    """Breadth-first traversal of documented links only, bounded to max_hops
    -- the article's own "progressive disclosure" idea made concrete: this
    never returns more of the bundle than the documented relationships within
    max_hops actually reach, and it never raises on a dangling link (SPEC.md
    6.1's explicit tolerance) -- it simply isn't a step anywhere."""
    if start not in bundle:
        raise KeyError(f"{start!r} is not in this bundle")
    visited = {start}
    steps = [NavigationStep(path=start, depth=0, via=None)]
    frontier = [start]
    for depth in range(1, max_hops + 1):
        next_frontier: list[str] = []
        for current in frontier:
            for raw_target in bundle[current].links:
                target = resolve_link(current, raw_target)
                if target is None or target in visited or target not in bundle:
                    continue
                visited.add(target)
                steps.append(NavigationStep(path=target, depth=depth, via=current))
                next_frontier.append(target)
        frontier = next_frontier
        if not frontier:
            break
    return steps


def impact_report(bundle: dict[str, Concept], start: str, max_hops: int, now: datetime) -> str:
    """Reproduces the article's own worked scenario directly: starting from
    one concept (e.g. the Authentication Service), report every concept
    reachable within max_hops, each with its trust tier and staleness, so a
    reader can see at a glance which parts of the discovered impact surface
    are freshly human-reviewed and which are stale or never verified."""
    lines = [f"Impact report from {start!r} (max {max_hops} hop(s)):"]
    for step in navigate(bundle, start, max_hops):
        concept = bundle[step.path]
        tier = trust_tier(concept)
        stale = is_stale(concept, now)
        stale_label = "stale" if stale else ("fresh" if stale is False else "no-staleness-declared")
        via = f" (via {step.via})" if step.via else ""
        lines.append(
            f"  [{step.depth}] {step.path} -- type={concept.type} "
            f"trust={tier} lifecycle={stale_label}{via}"
        )
    return "\n".join(lines)
