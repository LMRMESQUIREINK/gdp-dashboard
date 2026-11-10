import subprocess
import sys
from pathlib import Path

import pytest

from agent_md_validator import (
    parse_frontmatter,
    FrontmatterParseError,
    validate_agent_file,
    validate_agents_root,
    format_report,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REAL_AGENTS_DIR = REPO_ROOT / ".claude" / "agents"

VALID_FIXTURE = """---
name: example-reviewer
description: Use proactively after any change. Reviews code; never edits it.
tools: Read, Grep, Glob
model: opus
effort: high
---

# Role
You review code and report findings.
"""


def write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def test_parses_valid_frontmatter():
    fm = parse_frontmatter(VALID_FIXTURE)
    assert fm.raw["name"] == "example-reviewer"
    assert fm.raw["model"] == "opus"
    assert "You review code" in fm.body


def test_strips_trailing_yaml_comment_the_articles_own_example_uses():
    fm = parse_frontmatter(
        "---\nname: x\ndescription: d\ntools: Read, Grep, Glob        # read-only\n---\nbody\n"
    )
    assert fm.raw["tools"] == "Read, Grep, Glob"


def test_rejects_missing_closing_delimiter():
    with pytest.raises(FrontmatterParseError):
        parse_frontmatter("---\nname: x\n")


def test_valid_fixture_passes_clean(tmp_path):
    f = write(tmp_path, "example-reviewer.md", VALID_FIXTURE)
    report = validate_agent_file(f)
    assert report.ok
    assert report.findings == []


def test_missing_name_and_description_are_errors(tmp_path):
    f = write(tmp_path, "bad.md", "---\ntools: Read\n---\nbody\n")
    report = validate_agent_file(f)
    assert not report.ok
    codes = {finding.code for finding in report.findings}
    assert "missing-name" in codes
    assert "missing-description" in codes


def test_empty_body_is_an_error(tmp_path):
    f = write(tmp_path, "empty-body.md", "---\nname: empty-body\ndescription: d\n---\n")
    report = validate_agent_file(f)
    assert any(finding.code == "empty-body" for finding in report.findings)


def test_invalid_effort_value_is_an_error(tmp_path):
    f = write(
        tmp_path, "bad-effort.md",
        "---\nname: bad-effort\ndescription: d\neffort: extreme\n---\nbody\n",
    )
    report = validate_agent_file(f)
    assert any(finding.code == "invalid-effort" for finding in report.findings)
    assert not report.ok


def test_unrecognized_field_is_warned_not_silently_accepted(tmp_path):
    # The single most concrete finding this round's verification
    # produced: Claude Code itself silently ignores a typo'd field.
    # This is the one check that exists specifically to close that gap.
    f = write(
        tmp_path, "typo.md",
        "---\nname: typo\ndiscription: d\n---\nbody\n",
    )
    report = validate_agent_file(f)
    codes = {finding.code for finding in report.findings}
    assert "unrecognized-field" in codes
    # "discription" (the typo) means there's still no real "description"
    assert "missing-description" in codes


def test_pointless_always_stripped_tool_is_warned(tmp_path):
    f = write(
        tmp_path, "pointless-tool.md",
        "---\nname: pointless-tool\ndescription: d\ntools: Read, AskUserQuestion\n---\nbody\n",
    )
    report = validate_agent_file(f)
    assert any(finding.code == "pointless-tool-listed" for finding in report.findings)


def test_invalid_permission_mode_is_an_error(tmp_path):
    f = write(
        tmp_path, "bad-perm.md",
        "---\nname: bad-perm\ndescription: d\npermissionMode: godmode\n---\nbody\n",
    )
    report = validate_agent_file(f)
    assert any(finding.code == "invalid-permission-mode" for finding in report.findings)


def test_name_filename_mismatch_is_a_warning_not_an_error(tmp_path):
    f = write(
        tmp_path, "actual-filename.md",
        "---\nname: different-name\ndescription: d\n---\nbody\n",
    )
    report = validate_agent_file(f)
    assert report.ok  # a warning, not an error
    assert any(finding.code == "name-filename-mismatch" for finding in report.findings)


def test_discrimination_planted_bad_fixture_produces_exactly_the_expected_findings(tmp_path):
    """Plant three distinct, deliberate problems in one file and confirm
    all three -- and only those -- surface, proving the checks actually
    fire rather than rubber-stamping everything."""
    planted = (
        "---\n"
        "name: broken-example\n"
        "discription: a deliberate typo of 'description'\n"
        "tools: Read, AskUserQuestion\n"
        "effort: extreme\n"
        "---\n"
        "body\n"
    )
    f = write(tmp_path, "broken-example.md", planted)
    report = validate_agent_file(f)
    codes = {finding.code for finding in report.findings}
    assert "missing-description" in codes  # the typo means no real description
    assert "unrecognized-field" in codes  # discription itself
    assert "pointless-tool-listed" in codes  # AskUserQuestion
    assert "invalid-effort" in codes  # extreme
    assert not report.ok


def test_real_agent_files_in_this_repo_pass_clean():
    """The actual deliverable: this project's own two new real agent
    files, checked for real, not just against synthetic fixtures."""
    assert REAL_AGENTS_DIR.is_dir(), f"{REAL_AGENTS_DIR} does not exist"
    reports = validate_agents_root(REAL_AGENTS_DIR)
    assert len(reports) == 2
    for report in reports:
        assert report.ok, f"{report.agent_file} failed: {report.findings}"


def test_cli_runs_against_real_agents_dir_and_exits_zero():
    result = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "agent_md_validator.py"), str(REAL_AGENTS_DIR)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "2 agent file(s) checked, 0 error(s)" in result.stdout


def test_cli_json_mode_produces_valid_json():
    import json

    result = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "agent_md_validator.py"), str(REAL_AGENTS_DIR), "--json"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert len(data) == 2
    assert all(entry["ok"] for entry in data)


def test_format_report_reads_cleanly():
    reports = validate_agents_root(REAL_AGENTS_DIR)
    text = format_report(reports)
    assert "PASS" in text
    assert "0 error(s)" in text
