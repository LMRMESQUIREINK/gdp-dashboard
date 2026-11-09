"""A real, dependency-free linter for Claude Code's subagent definition
format (`.claude/agents/*.md`).

Built directly from a round of verification against the real Claude
Code docs (code.claude.com/docs/en/sub-agents.md, checked 2026-11-09
via this session's own claude-code-guide subagent), prompted by a
Medium article's claims about this feature -- see
/notes/claude-code-agents-ai-team-analysis.md. Not a port of anything:
this project had zero `.claude/agents/` files before this round, so
there was no existing validator to extend and nothing to compare
against except the real docs.

The single most concrete, actionable fact that verification surfaced,
and the reason this tool exists at all: Claude Code silently IGNORES
an unrecognized frontmatter field rather than raising an error, so a
typo'd field name (`discription` instead of `description`) fails
invisibly with no warning anywhere in the product itself. Everything
else this checks is secondary to that one check.

The frontmatter parser below is a close structural copy of
`skill_md_validator.py`'s `parse_skill_md` (same project, a few rounds
earlier) -- that function was always generic despite its name (simple
`key: value` frontmatter, nothing SKILL.md-specific about it). Copied
rather than imported across build directories, per this project's own
established convention (`prop_firm_*.py` copied unmodified into
`trading-jarvis/`, `interface-lift-toolkit/`, etc.) rather than a
fragile cross-build import.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# Built from the real, documented field list confirmed during this
# round's verification -- see the module docstring and the analysis
# note. Anything not in this set is flagged: either a real field this
# list hasn't caught up with yet, or a silent typo Claude Code itself
# will never warn about.
KNOWN_FIELDS = {
    "name",
    "description",
    "tools",
    "disallowedTools",
    "model",
    "effort",
    "permissionMode",
    "maxTurns",
    "skills",
    "mcpServers",
    "hooks",
    "memory",
    "background",
    "isolation",
    "color",
    "initialPrompt",
}

VALID_EFFORT = {"low", "medium", "high", "xhigh", "max"}
VALID_MODEL_ALIASES = {"sonnet", "opus", "haiku", "fable", "inherit"}
VALID_PERMISSION_MODES = {"default", "plan", "acceptEdits", "dontAsk", "bypassPermissions", "auto"}
VALID_ISOLATION = {"worktree"}

# Confirmed during verification: these are always stripped from a
# subagent's tool list regardless of what `tools` names, so listing
# them is a real, harmless-but-pointless no-op worth flagging --
# plan-mode tools and `Agent` recurse into territory a subagent by
# definition can't reach (no interactive user, no further nesting at
# the depth limit).
ALWAYS_STRIPPED_TOOLS = {"AskUserQuestion", "EnterPlanMode", "ExitPlanMode", "Agent"}


class FrontmatterParseError(ValueError):
    pass


@dataclass
class Frontmatter:
    raw: dict[str, str]
    body: str


def parse_frontmatter(text: str) -> Frontmatter:
    """Deliberately minimal, same shape as skill_md_validator.py's
    parse_skill_md: simple `key: value` pairs, one per line, trailing
    `# comment` stripped. Anything more exotic (YAML lists spanning
    multiple lines, block scalars) raises rather than silently
    mis-parsing."""
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
        value = _strip_trailing_comment(value.strip())
        if not key or not re.match(r"^[a-zA-Z_][a-zA-Z0-9_-]*$", key):
            raise FrontmatterParseError(f"unparseable frontmatter key: {key!r}")
        if key in raw:
            raise FrontmatterParseError(f"duplicate frontmatter key: {key!r}")
        raw[key] = value

    body = "\n".join(lines[close_idx + 1:])
    return Frontmatter(raw=raw, body=body)


def _strip_trailing_comment(value: str) -> str:
    """A bare, unquoted `#` starts a YAML comment -- the article's own
    example uses this (`tools: Read, Grep, Glob        # read-only`),
    and real YAML parses it that way, so this validator must too."""
    if "#" in value:
        value = value.split("#", 1)[0].rstrip()
    return value


@dataclass
class Finding:
    severity: str  # "error" | "warning"
    code: str
    message: str


@dataclass
class AgentReport:
    agent_file: Path
    findings: list[Finding] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(f.severity == "error" for f in self.findings)

    def error(self, code: str, message: str) -> None:
        self.findings.append(Finding("error", code, message))

    def warn(self, code: str, message: str) -> None:
        self.findings.append(Finding("warning", code, message))


def _looks_like_real_model_id(value: str) -> bool:
    """Not an exhaustive ID list (model IDs change) -- just enough to
    not false-positive on a real one. A known alias, 'inherit', or
    anything starting with 'claude-' is accepted."""
    return value in VALID_MODEL_ALIASES or value.startswith("claude-")


def validate_agent_file(agent_file: Path) -> AgentReport:
    report = AgentReport(agent_file=agent_file)
    if not agent_file.is_file():
        report.error("missing-file", f"no such file: {agent_file}")
        return report

    text = agent_file.read_text(encoding="utf-8")
    try:
        fm = parse_frontmatter(text)
    except FrontmatterParseError as e:
        report.error("unparseable-frontmatter", str(e))
        return report

    name = fm.raw.get("name")
    if not name:
        report.error("missing-name", "frontmatter has no 'name' field")
    else:
        if not NAME_PATTERN.match(name):
            report.error("bad-name-format", f"name {name!r} is not lowercase-hyphenated")
        expected_stem = agent_file.stem
        if name != expected_stem:
            report.warn(
                "name-filename-mismatch",
                f"name {name!r} does not match filename {agent_file.name!r} -- "
                "identity comes from 'name', not the filename, but a mismatch invites confusion",
            )

    description = fm.raw.get("description")
    if not description:
        report.error("missing-description", "frontmatter has no 'description' field")

    effort = fm.raw.get("effort")
    if effort is not None and effort not in VALID_EFFORT:
        report.error("invalid-effort", f"effort {effort!r} is not one of {sorted(VALID_EFFORT)}")

    model = fm.raw.get("model")
    if model is not None and not _looks_like_real_model_id(model):
        report.warn(
            "unrecognized-model",
            f"model {model!r} is not a known alias ({sorted(VALID_MODEL_ALIASES)}) "
            "and doesn't look like a real model ID (expected to start with 'claude-')",
        )

    permission_mode = fm.raw.get("permissionMode")
    if permission_mode is not None and permission_mode not in VALID_PERMISSION_MODES:
        report.error(
            "invalid-permission-mode",
            f"permissionMode {permission_mode!r} is not one of {sorted(VALID_PERMISSION_MODES)}",
        )

    isolation = fm.raw.get("isolation")
    if isolation is not None and isolation not in VALID_ISOLATION:
        report.error("invalid-isolation", f"isolation {isolation!r} is not one of {sorted(VALID_ISOLATION)}")

    tools = fm.raw.get("tools")
    if tools:
        listed = {t.strip() for t in tools.split(",") if t.strip()}
        stripped_anyway = listed & ALWAYS_STRIPPED_TOOLS
        if stripped_anyway:
            report.warn(
                "pointless-tool-listed",
                f"tool(s) {sorted(stripped_anyway)} are always stripped from subagents "
                "regardless of this list -- listing them has no effect",
            )

    for key in fm.raw:
        if key not in KNOWN_FIELDS:
            report.warn(
                "unrecognized-field",
                f"field {key!r} is not a documented subagent field -- Claude Code will "
                "SILENTLY IGNORE it rather than erroring, so confirm this isn't a typo "
                f"(known fields: {sorted(KNOWN_FIELDS)})",
            )

    body = fm.body.strip()
    if not body:
        report.error("empty-body", "no system prompt after the frontmatter block")

    return report


def validate_agents_root(root: Path) -> list[AgentReport]:
    return [validate_agent_file(p) for p in sorted(root.glob("*.md"))]


def format_report(reports: list[AgentReport]) -> str:
    lines = []
    total_errors = sum(1 for r in reports for f in r.findings if f.severity == "error")
    total_warnings = sum(1 for r in reports for f in r.findings if f.severity == "warning")
    for report in reports:
        status = "PASS" if report.ok else "FAIL"
        lines.append(f"[{status}] {report.agent_file}")
        for f in report.findings:
            lines.append(f"    {f.severity.upper():7s} {f.code}: {f.message}")
    lines.append("")
    lines.append(f"{len(reports)} agent file(s) checked, {total_errors} error(s), {total_warnings} warning(s)")
    return "\n".join(lines)


def _main(argv=None):
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Lint Claude Code .claude/agents/*.md files.")
    parser.add_argument("path", help="an agent .md file, or a directory of them (e.g. .claude/agents)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    target = Path(args.path)
    if target.is_dir():
        reports = validate_agents_root(target)
        if not reports:
            print(f"no agent .md files found under {target}")
            return 2
    elif target.is_file():
        reports = [validate_agent_file(target)]
    else:
        print(f"not a file or directory: {target}")
        return 2

    if args.json:
        print(json.dumps(
            [
                {
                    "agent_file": str(r.agent_file),
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
