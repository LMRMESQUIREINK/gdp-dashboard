#!/usr/bin/env python3
"""
Agent Readiness Scorecard — a vendor-neutral, locally-checkable scorer
inspired by Factory.ai's Autonomy Maturity Model (AMM) white paper
("Software Factory: An Autonomy Maturity Model for the Enterprise").

This is an INDEPENDENT reinterpretation, not a reproduction of Factory.ai's
actual scoring rubric — their full signal set isn't published (see
/notes/software-factory-autonomy-maturity-model-analysis.md). It borrows
the AMM's genuinely useful structure (binary signals, escalating per-level
point weights, a readiness-percentage headline metric) and applies it with
an original signal set chosen for what's actually checkable from a static
repo checkout, with no GitHub API or live telemetry access.

Level thresholds (from the source paper, used as-is): L1=5, L2=19, L3=36,
L4=60, L5=100. Per-signal point values by level: L1=1, L2=2, L3=4, L4=8,
L5=16.

IMPORTANT, stated plainly rather than silently: Level 4 and 5 in the
source framework are operational/telemetry signals (sub-minute feedback
loops, tickets auto-picked from Linear/Jira, multi-day mission
reliability) that cannot be observed from files on disk. This scorer only
assesses signals up through Level 3 and reports L4/L5 as not assessable,
rather than inventing proxies for things it cannot actually see.

Usage:
    python3 score_repo.py [REPO_PATH] [--json]
"""
import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

LEVEL_POINTS = {1: 1, 2: 2, 3: 4, 4: 8, 5: 16}
LEVEL_THRESHOLDS = {1: 5, 2: 19, 3: 36, 4: 60, 5: 100}
LEVEL_NAMES = {
    1: "Functional",
    2: "Documented",
    3: "Standardized (minimum production-grade bar)",
    4: "Optimized",
    5: "Software Factory (autonomous)",
}

CODE_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".tmp"}


@dataclass
class Signal:
    id: str
    level: int
    description: str
    check: Callable[[Path], Optional[bool]]
    result: Optional[bool] = field(default=None, init=False)
    detail: str = field(default="", init=False)


def _iter_files(root: Path, max_files: int = 20000):
    count = 0
    for p in root.rglob("*"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.is_file():
            yield p
            count += 1
            if count >= max_files:
                return


def _any_exists(root: Path, *names: str) -> bool:
    return any((root / n).exists() for n in names)


def _grep_files(root: Path, pattern: str, extensions: set, max_hits: int = 1) -> bool:
    regex = re.compile(pattern)
    hits = 0
    for p in _iter_files(root):
        if p.suffix not in extensions:
            continue
        try:
            text = p.read_text(errors="ignore")
        except OSError:
            continue
        if regex.search(text):
            hits += 1
            if hits >= max_hits:
                return True
    return False


def _toml_has_section(root: Path, filename: str, *sections: str) -> bool:
    path = root / filename
    if not path.exists():
        return False
    try:
        text = path.read_text(errors="ignore")
    except OSError:
        return False
    return any(f"[{s}]" in text or f"[tool.{s}]" in text for s in sections)


# --- L1 checks -------------------------------------------------------------

def check_readme(root: Path) -> bool:
    return _any_exists(root, "README.md", "README.rst", "README.txt", "README")


def check_linter_config(root: Path) -> bool:
    if _any_exists(root, ".flake8", "ruff.toml", ".ruff.toml"):
        return True
    if _toml_has_section(root, "pyproject.toml", "ruff", "flake8"):
        return True
    if list(root.glob(".eslintrc*")):
        return True
    return False


def check_type_checker_config(root: Path) -> bool:
    if _any_exists(root, "mypy.ini", "pyrightconfig.json"):
        return True
    if _toml_has_section(root, "pyproject.toml", "mypy"):
        return True
    ts = root / "tsconfig.json"
    if ts.exists():
        try:
            return '"strict": true' in ts.read_text(errors="ignore")
        except OSError:
            return False
    return False


def check_formatter_config(root: Path) -> bool:
    if list(root.glob(".prettierrc*")) or _any_exists(root, ".editorconfig"):
        return True
    if _toml_has_section(root, "pyproject.toml", "black"):
        return True
    return False


def check_unit_tests_exist(root: Path) -> bool:
    for p in _iter_files(root):
        name = p.name
        if re.match(r"^test_.+\.py$", name) or re.match(r".+_test\.py$", name):
            return True
        if re.match(r".+\.(test|spec)\.(js|ts|jsx|tsx)$", name):
            return True
    return False


# --- L2 checks -------------------------------------------------------------

def check_agent_instructions(root: Path) -> bool:
    return _any_exists(root, "AGENTS.md", "CLAUDE.md")


def check_reproducible_dev_env(root: Path) -> bool:
    return (
        (root / ".devcontainer").exists()
        or _any_exists(root, "Dockerfile", "Pipfile", "environment.yml", "flake.nix")
    )


def check_pre_commit_hooks(root: Path) -> bool:
    return _any_exists(root, ".pre-commit-config.yaml") or (root / ".husky").exists()


def check_documented_build_command(root: Path) -> bool:
    pattern = re.compile(
        r"(pip install|npm install|npm run|yarn install|make\s|streamlit run|python[3]?\s+\S+\.py)"
    )
    for name in ("README.md", "AGENTS.md", "CLAUDE.md"):
        p = root / name
        if p.exists():
            try:
                if pattern.search(p.read_text(errors="ignore")):
                    return True
            except OSError:
                continue
    return False


def check_branch_protection(root: Path) -> Optional[bool]:
    return None  # requires GitHub admin API access; not checkable from a local clone


def check_structured_logging(root: Path) -> bool:
    return _grep_files(
        root, r"\blogging\.getLogger\(|\bwinston\.createLogger\(|\bpino\(", {".py", ".js", ".ts"}
    )


def check_codeowners(root: Path) -> bool:
    return _any_exists(root, "CODEOWNERS") or (root / ".github" / "CODEOWNERS").exists()


# --- L3 checks -------------------------------------------------------------

def check_integration_or_e2e_tests(root: Path) -> bool:
    test_files = [
        p for p in _iter_files(root)
        if re.match(r"^test_.+\.py$", p.name) or re.match(r".+_test\.py$", p.name)
        or re.match(r".+\.(test|spec)\.(js|ts|jsx|tsx)$", p.name)
    ]
    return len(test_files) > 1


def check_docs_freshness(root: Path) -> Optional[bool]:
    docs_dirs = [d for d in ("docs", "notes") if (root / d).exists()]
    if not docs_dirs:
        return False
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "log", "-1", "--format=%ct"] + docs_dirs,
            capture_output=True, text=True, timeout=10,
        )
        if out.returncode != 0 or not out.stdout.strip():
            return None
        import time
        last_commit_age_days = (time.time() - float(out.stdout.strip())) / 86400
        return last_commit_age_days <= 30
    except (subprocess.SubprocessError, OSError, ValueError):
        return None


def check_security_scanning_config(root: Path) -> bool:
    if (root / ".github" / "dependabot.yml").exists():
        return True
    if _any_exists(root, "SECURITY.md"):
        return True
    workflows = root / ".github" / "workflows"
    if workflows.exists():
        for p in workflows.glob("*.y*ml"):
            try:
                if "codeql" in p.read_text(errors="ignore").lower():
                    return True
            except OSError:
                continue
    return False


def check_observability_config(root: Path) -> bool:
    return _grep_files(
        root, r"\bopentelemetry\b|\bprometheus_client\b|\bsentry_sdk\b", {".py", ".js", ".ts"}
    )


def check_ci_config(root: Path) -> bool:
    workflows = root / ".github" / "workflows"
    return workflows.exists() and any(workflows.glob("*.y*ml"))


SIGNALS = [
    Signal("readme_present", 1, "README present", check_readme),
    Signal("linter_config", 1, "Linter configured", check_linter_config),
    Signal("type_checker_config", 1, "Type checker active", check_type_checker_config),
    Signal("formatter_config", 1, "Formatter standardized", check_formatter_config),
    Signal("unit_tests_exist", 1, "Unit tests exist", check_unit_tests_exist),

    Signal("agent_instructions", 2, "AGENTS.md / CLAUDE.md present", check_agent_instructions),
    Signal("reproducible_dev_env", 2, "Reproducible dev environment config", check_reproducible_dev_env),
    Signal("pre_commit_hooks", 2, "Pre-commit hooks configured", check_pre_commit_hooks),
    Signal("documented_build", 2, "Build/run command documented", check_documented_build_command),
    Signal("branch_protection", 2, "Branch protection enabled", check_branch_protection),
    Signal("structured_logging", 2, "Structured logging in use", check_structured_logging),
    Signal("codeowners", 2, "CODEOWNERS present", check_codeowners),

    Signal("integration_e2e_tests", 3, "Integration/E2E tests (beyond one test file)", check_integration_or_e2e_tests),
    Signal("docs_freshness", 3, "Docs updated within the last 30 days", check_docs_freshness),
    Signal("security_scanning", 3, "Security scanning configured", check_security_scanning_config),
    Signal("observability", 3, "Observability/tracing library in use", check_observability_config),
    Signal("ci_config", 3, "CI workflow configured", check_ci_config),
]


def level_for_points(points: int) -> int:
    level = 0
    for lvl in sorted(LEVEL_THRESHOLDS):
        if points >= LEVEL_THRESHOLDS[lvl]:
            level = lvl
    return level


def score(root: Path) -> dict:
    total_points = 0
    max_assessable_points = 0
    results = []
    for sig in SIGNALS:
        sig.result = sig.check(root)
        pts = LEVEL_POINTS[sig.level]
        if sig.result is True:
            total_points += pts
        if sig.result is not None:
            max_assessable_points += pts
        results.append({
            "id": sig.id, "level": sig.level, "description": sig.description,
            "status": "pass" if sig.result is True else ("fail" if sig.result is False else "unknown"),
            "points": pts,
        })
    return {
        "total_points": total_points,
        "max_assessable_points": max_assessable_points,
        "level": level_for_points(total_points),
        "signals": results,
    }


def render(result: dict, repo_name: str) -> str:
    lines = []
    lines.append(f"Agent Readiness Scorecard — {repo_name}")
    lines.append("=" * 60)
    lines.append(
        f"Score: {result['total_points']} pts "
        f"(of {result['max_assessable_points']} assessable from this checkout) "
        f"-> Level {result['level']} ({LEVEL_NAMES.get(result['level'], 'Below Level 1')})"
    )
    lines.append("")
    by_level = {}
    for s in result["signals"]:
        by_level.setdefault(s["level"], []).append(s)
    for lvl in sorted(by_level):
        lines.append(f"Level {lvl} signals ({LEVEL_POINTS[lvl]} pt each, threshold {LEVEL_THRESHOLDS[lvl]} pts cumulative):")
        for s in by_level[lvl]:
            mark = {"pass": "[x]", "fail": "[ ]", "unknown": "[?]"}[s["status"]]
            note = ""
            if s["status"] == "unknown":
                note = "  (not checkable from a local clone)"
            lines.append(f"  {mark} {s['description']}{note}")
        lines.append("")
    lines.append(
        "Level 4 (Optimized) and Level 5 (Software Factory) are not scored: "
        "their signals in the source framework are operational/telemetry-based "
        "(sub-minute feedback, auto-picked-up tickets, multi-day mission reliability) "
        "and cannot be observed from files on disk."
    )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_path", nargs="?", default=".", help="Path to the repo to score")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of the rendered scorecard")
    args = parser.parse_args()

    root = Path(args.repo_path).resolve()
    if not root.exists():
        print(f"error: {root} does not exist", file=sys.stderr)
        sys.exit(1)

    result = score(root)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(render(result, root.name))


if __name__ == "__main__":
    main()
