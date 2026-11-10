"""A real, dependency-free linter for Claude Code's SKILL.md format.

Built from reading this project's own eleven real skills
(.claude/skills/*/SKILL.md) rather than from AgentsKit.co's own
"SKILL.md validator" free tool -- that tool is a web product with no
inspectable source, so this is an independent reimplementation of the
idea, grounded in observed real files, not a port. See
/notes/agentskit-claude-tooling-bundle-analysis.md.

Checks, in the order a human reviewing a new skill would actually hit
them:
  1. The SKILL.md file exists and has parseable frontmatter.
  2. `name` exists, is lowercase-hyphenated (no spaces/underscores/caps),
     and matches the skill's own directory name exactly -- a real,
     structural requirement, not a style preference: a mismatch means
     the skill's own folder name and its declared identity disagree.
  3. `description` exists and is non-empty.
  4. `description` length falls in a reasonable range. The lower bound
     is this project's own heuristic (too short to plausibly state both
     what a skill does and when to use it). The upper bounds are no
     longer a guess this build "could not independently confirm" -- a
     later round read `coreyhaines31/marketingskills`
     (`/notes/marketingskills-analysis.md`), whose own
     `evals/triggers/README.md` gives a real, dated measurement: Claude
     Code caps the whole skill listing it sends the model at roughly
     30,000 characters, skills past that cap show as a bare name with
     no description, and the source's own recommendation (confirmed
     against real counts of its skill-listing dump, Claude Code 2.1.319,
     checked 2026-11-09) is to keep each description at 500 characters
     or fewer. `RECOMMENDED_DESCRIPTION_LEN` (500, a separate, informational
     warning) and `check_pack_description_budget()` (the aggregate check
     across a whole skill library) both come from that real source,
     cited there rather than claimed independently verified from this
     session -- this build has no access to its own skill_listing dump
     the way the source did. The original, looser `max_description_len`
     (1500) stays as this project's own pre-existing ceiling, unchanged.
  5. `description` names a trigger condition (a "when"/"use"/"triggers
     on" style phrase) -- advisory, not a hard failure, since this is a
     best-practice observed across every one of this project's own
     skills, not a documented requirement.
  6. The body (everything after the closing `---`) is non-empty and
     isn't just the description restated with nothing added.
  7. Any relative file reference in the body (a path-shaped token in
     backticks or a markdown link, e.g. `references/foo.md`) resolves
     to a real file under the skill's own directory -- the same
     "broken local reference" check this project's
     /builds/ten-k-website-grader/ already runs against HTML pages,
     applied here to skills instead.
  8. No two sibling skills declare the same `name`. deer-flow's own repo
     (analyzed in an earlier round of this project,
     /notes/deer-flow-analysis.md) documents exactly this failure class
     in `docs/SKILL_NAME_CONFLICT_FIX.md` -- this check exists because
     that's a real, previously-documented bug category, not a
     hypothetical one.

Two pack-level checks (via `validate_pack()`, not per-skill):
  9. `check_pack_description_budget()` -- the aggregate character budget
     across every skill's description, warning/erroring against the
     real thresholds the marketingskills source measured (see point 4
     above), not a per-skill bound.
  10. `check_description_overlap()` -- a HEURISTIC proxy only, not a real
      trigger-accuracy test: two sibling skills whose descriptions share
      an unusually high fraction of significant (non-stopword) words are
      flagged as a trigger-collision risk. marketingskills' own real
      mechanism for this (`evals/triggers/`) runs hundreds of held-out
      prompts through a live model and scores which skill actually
      fires -- genuinely more informative, but needs a live model this
      build doesn't run against on its own. Word overlap is a cheap,
      model-free approximation of the same risk, nothing more.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
TRIGGER_WORDS = (
    "use when", "use this", "use it", "use while", "use during",
    "triggers on", "trigger", "when the user", "use before", "use after",
    "use for", "before calling",
)
# Matches a path-shaped token: at least one "/" or a recognizable
# references/scripts/templates/assets/evals prefix, inside backticks or
# a markdown link target. Deliberately conservative -- false negatives
# (missing a real reference) are safer here than false positives (flagging
# prose that merely contains a slash, e.g. "pass/fail").
REFERENCE_PATTERN = re.compile(
    r"(?:`([\w./-]+/[\w.-]+)`|\]\(([\w./-]+/[\w.-]+)\))"
)
KNOWN_REFERENCE_DIRS = ("references/", "scripts/", "templates/", "assets/", "evals/")

# From coreyhaines31/marketingskills' evals/triggers/README.md (real, dated
# measurement -- see the module docstring, point 4): keep each description
# at 500 chars or fewer; Claude Code's whole skill-listing cap sits around
# 30,000 chars, with real degradation starting well before that (2/53
# skills lost their description at 19,259 total chars under 90 other
# installed skills).
RECOMMENDED_DESCRIPTION_LEN = 500
PACK_BUDGET_WARN_CHARS = 19_000
PACK_BUDGET_CAP_CHARS = 30_000

# Generic connective/boilerplate words, plus this project's own trigger
# phrasing, stripped before computing description overlap -- otherwise
# every pair of skills "overlaps" just by both saying "use when the user
# wants to" or "or asks". Deliberately small and conservative: dropping a
# real content word would hide a genuine collision.
OVERLAP_STOPWORDS = frozenset({
    "a", "an", "and", "or", "the", "to", "of", "in", "on", "for", "with",
    "this", "that", "it", "is", "are", "or", "use", "uses", "using", "used",
    "when", "while", "before", "after", "during", "user", "users", "wants",
    "want", "asks", "ask", "about", "what", "which", "whether", "how",
    "not", "any", "real", "its", "their", "you", "your", "do", "does",
})


class FrontmatterParseError(ValueError):
    pass


@dataclass
class Frontmatter:
    raw: dict[str, str]
    body: str


def parse_skill_md(text: str) -> Frontmatter:
    """Deliberately minimal: handles exactly the shape this project's
    own skills use (simple `key: value` pairs, one per line, values
    never spanning multiple lines). Anything more exotic (YAML lists,
    block scalars, nested maps) raises rather than silently
    mis-parsing -- a validator that misreads its own input is worse
    than one that admits it can't read it."""
    if not text.startswith("---"):
        raise FrontmatterParseError("file does not start with '---' frontmatter delimiter")
    lines = text.splitlines()
    if lines[0].strip() != "---":
        raise FrontmatterParseError("first line is not a bare '---'")
    try:
        close_idx = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        raise FrontmatterParseError("no closing '---' found for frontmatter block") from None

    raw: dict[str, str] = {}
    for line in lines[1:close_idx]:
        if not line.strip():
            continue
        if ":" not in line:
            raise FrontmatterParseError(f"unparseable frontmatter line (no ':'): {line!r}")
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if not key or not re.match(r"^[a-zA-Z_][a-zA-Z0-9_-]*$", key):
            raise FrontmatterParseError(f"unparseable frontmatter key: {key!r}")
        if key in raw:
            raise FrontmatterParseError(f"duplicate frontmatter key: {key!r}")
        raw[key] = value

    body = "\n".join(lines[close_idx + 1:])
    return Frontmatter(raw=raw, body=body)


@dataclass
class Finding:
    severity: str  # "error" | "warning"
    code: str
    message: str


@dataclass
class SkillReport:
    skill_dir: Path
    findings: list[Finding] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(f.severity == "error" for f in self.findings)

    def error(self, code: str, message: str) -> None:
        self.findings.append(Finding("error", code, message))

    def warn(self, code: str, message: str) -> None:
        self.findings.append(Finding("warning", code, message))


def _extract_references(body: str) -> list[str]:
    refs = []
    for m in REFERENCE_PATTERN.finditer(body):
        path = m.group(1) or m.group(2)
        if path.startswith(("http://", "https://", "#")):
            continue
        if any(path.startswith(d) for d in KNOWN_REFERENCE_DIRS) or path.count("/") >= 1:
            refs.append(path)
    return refs


def validate_skill_dir(skill_dir: Path, *, min_description_len: int = 40, max_description_len: int = 1500,
                        recommended_description_len: int = RECOMMENDED_DESCRIPTION_LEN, repo_root: Path | None = None) -> SkillReport:
    report = SkillReport(skill_dir=skill_dir)
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        report.error("missing-skill-md", f"no SKILL.md found in {skill_dir}")
        return report

    text = skill_md.read_text(encoding="utf-8")
    try:
        fm = parse_skill_md(text)
    except FrontmatterParseError as e:
        report.error("unparseable-frontmatter", str(e))
        return report

    name = fm.raw.get("name")
    if not name:
        report.error("missing-name", "frontmatter has no 'name' field")
    else:
        if not NAME_PATTERN.match(name):
            report.error("bad-name-format", f"name {name!r} is not lowercase-hyphenated (expected e.g. 'my-skill-name')")
        if name != skill_dir.name:
            report.error("name-directory-mismatch", f"name {name!r} does not match directory name {skill_dir.name!r}")

    description = fm.raw.get("description")
    if not description:
        report.error("missing-description", "frontmatter has no 'description' field")
    else:
        if len(description) < min_description_len:
            report.error("description-too-short", f"description is {len(description)} chars (minimum {min_description_len}) -- likely too vague to trigger reliably")
        elif len(description) > max_description_len:
            report.warn("description-too-long", f"description is {len(description)} chars (over {max_description_len}) -- risks crowding the always-loaded skill index")
        elif len(description) > recommended_description_len:
            report.warn(
                "description-over-recommended",
                f"description is {len(description)} chars (over the {recommended_description_len}-char "
                "recommendation from coreyhaines31/marketingskills' own dated measurement -- see "
                "/notes/marketingskills-analysis.md) -- still under this project's own looser ceiling, but "
                "worth trimming if this pack grows",
            )
        lowered = description.lower()
        if not any(w in lowered for w in TRIGGER_WORDS):
            report.warn("no-trigger-condition", "description doesn't obviously state WHEN to use this skill (no 'use when'/'triggers on'/similar phrase found)")

    body = fm.body.strip()
    if not body:
        report.error("empty-body", "no content after the frontmatter block")
    elif description:
        # Thin-skill check: does the body's first paragraph just restate
        # the description with nothing added?
        first_para = next((p.strip() for p in body.split("\n\n") if p.strip() and not p.strip().startswith("#")), "")
        if first_para and _similarity(first_para.lower(), description.lower()) > 0.85:
            report.warn("thin-body", "the body's first paragraph is nearly identical to the description -- the skill may not add anything beyond its own one-line summary")

    for ref in _extract_references(body):
        if not _reference_resolves(ref, skill_dir, repo_root):
            report.error("broken-reference", f"body references {ref!r}, which resolves under neither {skill_dir} nor the repo root")

    return report


def _reference_resolves(ref: str, skill_dir: Path, repo_root: Path | None) -> bool:
    """A real finding from running this against this project's own
    skills, not a guess made up front: this project's skills mix two
    genuinely different reference conventions in the same body text --
    `references/foo.md`-style paths relative to the skill's OWN
    directory, and repo-root-relative paths (a leading '/', or a bare
    `.claude/skills/other-skill`, `builds/...`, `notes/...`,
    `prompts/...`) pointing elsewhere in the whole repo. Resolving only
    one of the two conventions produced 16 false-positive
    broken-reference errors across 7 real, correct skills on the first
    run. Try every plausible resolution; only fail if none of them
    exist."""
    candidates = [skill_dir / ref]
    if repo_root is not None:
        candidates.append(repo_root / ref.lstrip("/"))
        candidates.append(repo_root / ref)
    return any(c.exists() for c in candidates)


def _find_repo_root(start: Path) -> Path | None:
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def _similarity(a: str, b: str) -> float:
    """Cheap token-overlap similarity (Jaccard on word sets) -- not
    meant to be a precise text-similarity metric, just enough to flag
    an obvious near-duplicate without a fuzzy-matching dependency."""
    tokens_a, tokens_b = set(a.split()), set(b.split())
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / len(tokens_a | tokens_b)


def validate_skills_root(root: Path, **kwargs) -> list[SkillReport]:
    reports = [
        validate_skill_dir(d, **kwargs)
        for d in sorted(p for p in root.iterdir() if p.is_dir())
        if (d / "SKILL.md").exists() or True  # still report missing-SKILL.md dirs
    ]
    names_seen: dict[str, list[Path]] = {}
    for report in reports:
        skill_md = report.skill_dir / "SKILL.md"
        if not skill_md.is_file():
            continue
        try:
            fm = parse_skill_md(skill_md.read_text(encoding="utf-8"))
        except FrontmatterParseError:
            continue
        name = fm.raw.get("name")
        if name:
            names_seen.setdefault(name, []).append(report.skill_dir)
    for name, dirs in names_seen.items():
        if len(dirs) > 1:
            for report in reports:
                if report.skill_dir in dirs:
                    report.error("duplicate-skill-name", f"name {name!r} is also declared by: {', '.join(str(d) for d in dirs if d != report.skill_dir)}")
    return reports


def _significant_words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9']+", text.lower()) if w not in OVERLAP_STOPWORDS}


def _collect_descriptions(root: Path) -> dict[Path, str]:
    """Re-reads and re-parses each skill's description -- cheap, since
    SKILL.md files are tiny, and keeps SkillReport (which only holds
    findings) unchanged for every existing caller."""
    descriptions: dict[Path, str] = {}
    for skill_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            continue
        try:
            fm = parse_skill_md(skill_md.read_text(encoding="utf-8"))
        except FrontmatterParseError:
            continue
        description = fm.raw.get("description")
        if description:
            descriptions[skill_dir] = description
    return descriptions


def check_pack_description_budget(descriptions: dict[Path, str], *, warn_at: int = PACK_BUDGET_WARN_CHARS,
                                   cap_at: int = PACK_BUDGET_CAP_CHARS) -> list[Finding]:
    """Aggregate character budget across every skill's description --
    see the module docstring, point 9, and
    /notes/marketingskills-analysis.md for where warn_at/cap_at come
    from. Deliberately never erroring: a pack over the real cap still
    works, it just means some descriptions start showing name-only to
    the model, which this project can act on or not."""
    total = sum(len(d) for d in descriptions.values())
    findings: list[Finding] = []
    if total > cap_at:
        findings.append(Finding(
            "warning", "pack-description-budget-exceeded",
            f"{len(descriptions)} skill description(s) total {total} chars, over the ~{cap_at}-char cap "
            "marketingskills measured for Claude Code's skill listing -- some descriptions may already be "
            "showing name-only to the model",
        ))
    elif total > warn_at:
        findings.append(Finding(
            "warning", "pack-description-budget-warning",
            f"{len(descriptions)} skill description(s) total {total} chars, over the ~{warn_at}-char point "
            "where marketingskills' own measurement found descriptions starting to drop under a crowded "
            "install -- still under the hard cap, worth watching as this pack grows",
        ))
    return findings


def check_description_overlap(descriptions: dict[Path, str], *, threshold: float = 0.4) -> list[Finding]:
    """A HEURISTIC proxy only -- see the module docstring, point 10.
    Flags sibling-skill pairs whose descriptions share a suspiciously
    high fraction of significant words, as a cheap, model-free stand-in
    for the real trigger-collision risk marketingskills' own
    evals/triggers/ harness measures with a live model."""
    findings: list[Finding] = []
    items = sorted(descriptions.items())
    word_sets = {path: _significant_words(desc) for path, desc in items}
    seen_pairs: set[frozenset[Path]] = set()
    for i, (path_a, words_a) in enumerate(word_sets.items()):
        for path_b, words_b in list(word_sets.items())[i + 1:]:
            pair = frozenset({path_a, path_b})
            if pair in seen_pairs or not words_a or not words_b:
                continue
            seen_pairs.add(pair)
            overlap = len(words_a & words_b) / len(words_a | words_b)
            if overlap >= threshold:
                findings.append(Finding(
                    "warning", "description-overlap",
                    f"{path_a.name!r} and {path_b.name!r} share {overlap:.0%} of their significant "
                    f"description words -- a possible trigger-collision risk (shared words: "
                    f"{sorted(words_a & words_b)})",
                ))
    return findings


def validate_pack(root: Path, **kwargs) -> tuple[list[SkillReport], list[Finding]]:
    """The full pack validation: every per-skill SkillReport from
    validate_skills_root(), plus the two pack-level checks that need
    every skill's description at once. Returns both separately so
    validate_skills_root()'s own existing callers/return shape are
    untouched."""
    per_skill_kwargs = {k: v for k, v in kwargs.items() if k != "overlap_threshold"}
    reports = validate_skills_root(root, **per_skill_kwargs)
    descriptions = _collect_descriptions(root)
    pack_findings = check_pack_description_budget(descriptions)
    pack_findings += check_description_overlap(descriptions, threshold=kwargs.get("overlap_threshold", 0.4))
    return reports, pack_findings


def format_report(reports: list[SkillReport]) -> str:
    lines = []
    total_errors = sum(1 for r in reports for f in r.findings if f.severity == "error")
    total_warnings = sum(1 for r in reports for f in r.findings if f.severity == "warning")
    for report in reports:
        status = "PASS" if report.ok else "FAIL"
        lines.append(f"[{status}] {report.skill_dir}")
        for f in report.findings:
            lines.append(f"    {f.severity.upper():7s} {f.code}: {f.message}")
    lines.append("")
    lines.append(f"{len(reports)} skills checked, {total_errors} error(s), {total_warnings} warning(s)")
    return "\n".join(lines)


def _main(argv=None):
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="Lint Claude Code SKILL.md files.")
    parser.add_argument("path", help="a skill directory, or a directory of skill directories (e.g. .claude/skills)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    target = Path(args.path)
    if not target.is_dir():
        print(f"not a directory: {target}")
        return 2

    repo_root = _find_repo_root(target)
    if repo_root is not None and not args.json:
        print(f"(resolving repo-root-relative references against: {repo_root})")

    pack_findings: list[Finding] = []
    if (target / "SKILL.md").is_file():
        reports = [validate_skill_dir(target, repo_root=repo_root)]
    else:
        reports, pack_findings = validate_pack(target, repo_root=repo_root)

    if not reports:
        print(f"no skills found under {target}")
        return 2

    if args.json:
        print(json.dumps(
            {
                "skills": [
                    {
                        "skill_dir": str(r.skill_dir),
                        "ok": r.ok,
                        "findings": [{"severity": f.severity, "code": f.code, "message": f.message} for f in r.findings],
                    }
                    for r in reports
                ],
                "pack_level": [{"severity": f.severity, "code": f.code, "message": f.message} for f in pack_findings],
            },
            indent=2,
        ))
    else:
        print(format_report(reports))
        if pack_findings:
            print("\npack-level:")
            for f in pack_findings:
                print(f"    {f.severity.upper():7s} {f.code}: {f.message}")

    return 0 if all(r.ok for r in reports) and not any(f.severity == "error" for f in pack_findings) else 1


if __name__ == "__main__":
    raise SystemExit(_main())
