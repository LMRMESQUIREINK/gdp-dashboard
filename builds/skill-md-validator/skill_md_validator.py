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
  4. `description` length falls in a reasonable range. These bounds are
     this project's own stated heuristic, not a cited Anthropic hard
     limit this build could not independently confirm -- too short to
     plausibly state both what the skill does and when to use it, or
     long enough to start crowding the always-loaded skill index.
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


def validate_skill_dir(skill_dir: Path, *, min_description_len: int = 40, max_description_len: int = 1500, repo_root: Path | None = None) -> SkillReport:
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

    if (target / "SKILL.md").is_file():
        reports = [validate_skill_dir(target, repo_root=repo_root)]
    else:
        reports = validate_skills_root(target, repo_root=repo_root)

    if not reports:
        print(f"no skills found under {target}")
        return 2

    if args.json:
        print(json.dumps(
            [
                {
                    "skill_dir": str(r.skill_dir),
                    "ok": r.ok,
                    "findings": [{"severity": f.severity, "code": f.code, "message": f.message} for f in r.findings],
                }
                for r in reports
            ],
            indent=2,
        ))
    else:
        print(format_report(reports))

    return 0 if all(r.ok for r in reports) else 1


if __name__ == "__main__":
    raise SystemExit(_main())
