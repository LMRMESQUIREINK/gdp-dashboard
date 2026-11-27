"""A real, dependency-free Python scorer for the 9-skill rubric from "Data
Science Is Changing. These Are the Skills I'd Learn in 2027" (Codebook Fusion,
Medium) -- see /notes/ds-2027-skills-analysis.md.

Same move as /builds/agent-readiness-scorecard/ (Factory.ai's Autonomy
Maturity Model) and /builds/ten-k-website-grader/ (the "$10K Websites"
8-pillar checklist): extract a source's checklist/rubric structure and build
an honest, locally-checkable scorer for it, rather than trusting a human's
self-report. Honest about which of the article's 9 skills a machine can
actually observe from a repo's files on disk:

- Problem framing, communication/storytelling, and domain knowledge (skills
  1, 7, 9) are about judgment and context that cannot be read off a
  directory listing -- always reported `not_assessable`, same discipline as
  agent-readiness-scorecard's Level 4/5 operational-telemetry signals and
  ten-k-website-grader's "point of view" pillar.
- The remaining 6 skills get real checks, each returning matched evidence
  (file paths, matched lines), never a bare pass/fail with no proof. Two of
  them (LLM/agent usage, evaluation harness) are explicitly marked as
  heuristic proxies -- keyword/structure presence, not a verified capability
  -- the same honesty ten-k-website-grader applies to its own hierarchy/
  imagery/motion proxies.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".pytest_cache", "venv", ".venv", "dist", "build"}

# This tool's own directory -- excluded from scans by default (see
# run_scorecard's `exclude_self` parameter). A repo-wide scanner that doesn't
# exclude itself will match its own detection-pattern source text and its own
# test fixtures as if they were real signal in the target repo. Caught for
# real, not hypothetically: scanning this project's own repo (which contains
# this tool) originally reported a false PASS on the data-pipeline skill,
# traced to two sources -- this file's own `airflow_pattern` regex literally
# spelling "from airflow"/"import airflow" in its source, and
# test_ds_skills_scorecard.py's own Airflow-fixture test writing that exact
# string as fixture content. See test_real_run_against_this_repo_matches_hand_checked_ground_truth.
_SELF_DIR = Path(__file__).resolve().parent


@dataclass
class SkillResult:
    skill_id: int
    name: str
    status: str  # "pass" | "fail" | "not_assessable"
    evidence: list[str] = field(default_factory=list)
    note: str = ""


def _walk_files(root: Path, exclude_self: bool = True):
    self_dir_resolved = _SELF_DIR
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if exclude_self:
            try:
                resolved = path.resolve()
            except OSError:
                resolved = path
            if resolved == self_dir_resolved or self_dir_resolved in resolved.parents:
                continue
        yield path


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _grep_files(files: list[Path], root: Path, pattern: re.Pattern, max_hits: int = 5) -> list[str]:
    hits = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                hits.append(f"{_rel(root, path)}:{i}")
                if len(hits) >= max_hits:
                    return hits
                break  # one hit per file is enough evidence
    return hits


def check_code_quality_and_testing(root: Path, files: list[Path]) -> SkillResult:
    """Skill 2: Python, SQL, and reading code critically -- proxied by the
    presence of real tests and SQL, not by code style (unobservable without
    actually reading every line, which this checks separately via other
    builds' discrimination tests, not here)."""
    test_files = [f for f in files if re.match(r"^(test_.*|.*_test)\.(py|ts|js|mjs)$", f.name) or f.name.endswith(".test.ts")]
    sql_files = [f for f in files if f.suffix.lower() == ".sql"]
    evidence = [_rel(root, f) for f in test_files[:3]] + [_rel(root, f) for f in sql_files[:2]]
    if test_files:
        return SkillResult(2, "Python/SQL and reading code critically", "pass", evidence,
                            f"{len(test_files)} test file(s) found" + (f", {len(sql_files)} SQL file(s)" if sql_files else ""))
    return SkillResult(2, "Python/SQL and reading code critically", "fail", [],
                        "no test_*.py / *_test.py / *.test.ts files found anywhere")


def check_llm_agent_patterns(root: Path, files: list[Path]) -> SkillResult:
    """Skill 3: Working with LLMs, RAG, and agents -- a HEURISTIC proxy only.
    Keyword presence proves someone wrote code that MENTIONS these concepts,
    not that the system actually works or is evaluated well (that's skill 4,
    checked separately). Stated plainly, same caveat ten-k-website-grader
    gives its own heuristic pillars."""
    code_files = [f for f in files if f.suffix in (".py", ".ts", ".js", ".mjs")]
    pattern = re.compile(r"\b(embedding|vector[_ ]?(store|db|search)|rag\b|retrieval|anthropic|openai|mcp\.server|tool_use|run_agent)\b", re.I)
    hits = _grep_files(code_files, root, pattern)
    if hits:
        return SkillResult(3, "Working with LLMs, RAG, and agents (heuristic)", "pass", hits,
                            "keyword/import evidence of LLM or agent-tool code -- NOT a verified capability, "
                            "just presence of the pattern")
    return SkillResult(3, "Working with LLMs, RAG, and agents (heuristic)", "fail", [],
                        "no embedding/RAG/agent-tool keyword or import found in any code file")


def check_evaluation_harness(root: Path, files: list[Path]) -> SkillResult:
    """Skill 4: Evaluation, testing, experimentation -- a HEURISTIC proxy.
    Looks for a file whose own name says "eval"/"benchmark"/"fixture" AND
    whose content contains an assertion or an expected/actual comparison --
    distinct from check_code_quality_and_testing's bare test-file count,
    since a plain unit test is not the same as an evaluation harness against
    real-world examples."""
    candidates = [f for f in files if re.search(r"(eval|benchmark|fixture|golden|ground_?truth)", f.stem, re.I)
                  and f.suffix in (".py", ".ts", ".js", ".json", ".csv")]
    assertion_pattern = re.compile(r"\b(assert|expect\(|toEqual|toBe\b)", re.I)
    hits = []
    for f in candidates:
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if assertion_pattern.search(text) or f.suffix in (".json", ".csv"):
            hits.append(_rel(root, f))
        if len(hits) >= 5:
            break
    if hits:
        return SkillResult(4, "Evaluation, testing, and experimentation (heuristic)", "pass", hits,
                            "found eval/benchmark/fixture-named file(s) with real assertions or data -- "
                            "NOT a verified evaluation methodology, just presence of the pattern")
    return SkillResult(4, "Evaluation, testing, and experimentation (heuristic)", "fail", [],
                        "no eval/benchmark/fixture/golden-named file with assertions or data found")


def check_data_pipeline(root: Path, files: list[Path]) -> SkillResult:
    """Skill 5: Data engineering and data quality -- looks for real pipeline/
    orchestration markers (Airflow DAGs, dbt projects) or a conventionally-
    named pipeline module with fetch/clean/validate structure."""
    dbt_files = [f for f in files if f.name == "dbt_project.yml"]
    if dbt_files:
        return SkillResult(5, "Data engineering and data quality", "pass", [_rel(root, f) for f in dbt_files],
                            "dbt_project.yml found")
    code_files = [f for f in files if f.suffix == ".py"]
    airflow_pattern = re.compile(r"\bDAG\(|from airflow\b|import airflow\b")
    airflow_hits = _grep_files(code_files, root, airflow_pattern, max_hits=3)
    if airflow_hits:
        return SkillResult(5, "Data engineering and data quality", "pass", airflow_hits, "Airflow DAG usage found")
    pipeline_files = [f for f in code_files if re.search(r"(^|_)pipeline(\.py)?$", f.stem, re.I)]
    validate_pattern = re.compile(r"\b(validate|fetch|clean)\w*\s*\(")
    hits = []
    for f in pipeline_files:
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if validate_pattern.search(text):
            hits.append(_rel(root, f))
        if len(hits) >= 5:
            break
    if hits:
        return SkillResult(5, "Data engineering and data quality", "pass", hits,
                            "pipeline-named module(s) with fetch/clean/validate functions found")
    return SkillResult(5, "Data engineering and data quality", "fail", [],
                        "no dbt project, Airflow DAG, or pipeline-named module with fetch/clean/validate found")


def check_deployment_and_mlops(root: Path, files: list[Path]) -> SkillResult:
    """Skill 6: MLOps, deployment, and cost awareness -- looks for a
    Dockerfile, a CI workflow, or a real API-serving import (FastAPI, Flask,
    the MCP server SDK)."""
    docker_files = [f for f in files if f.name.lower().startswith("dockerfile")]
    ci_files = [f for f in files if ".github/workflows" in str(f) and f.suffix in (".yml", ".yaml")]
    evidence = [_rel(root, f) for f in (docker_files + ci_files)[:5]]
    if docker_files or ci_files:
        return SkillResult(6, "MLOps, deployment, and cost awareness", "pass", evidence,
                            "Dockerfile and/or CI workflow found")
    code_files = [f for f in files if f.suffix == ".py"]
    serving_pattern = re.compile(r"\b(fastapi|from flask|import flask|from mcp\.server|from mcp import server)\b", re.I)
    hits = _grep_files(code_files, root, serving_pattern, max_hits=5)
    if hits:
        return SkillResult(6, "MLOps, deployment, and cost awareness", "pass", hits,
                            "no Dockerfile/CI, but a real API-serving import (FastAPI/Flask/MCP server) found")
    return SkillResult(6, "MLOps, deployment, and cost awareness", "fail", [],
                        "no Dockerfile, CI workflow, or API-serving import (FastAPI/Flask/MCP server) found")


def check_responsible_ai_governance(root: Path, files: list[Path]) -> SkillResult:
    """Skill 8: Responsible AI, privacy, and governance -- looks for a
    LICENSE file and/or a model-card-style document."""
    license_files = [f for f in files if re.match(r"^LICEN[CS]E(\..*)?$", f.name, re.I)]
    model_card_files = [f for f in files if re.search(r"model[_-]?card", f.name, re.I)]
    evidence = [_rel(root, f) for f in (license_files + model_card_files)[:5]]
    if license_files and model_card_files:
        return SkillResult(8, "Responsible AI, privacy, and governance", "pass", evidence,
                            "LICENSE and a model-card-style document both found")
    if license_files:
        return SkillResult(8, "Responsible AI, privacy, and governance", "fail", evidence,
                            "LICENSE found, but no model-card-style document -- partial coverage, "
                            "a licence alone doesn't document a model's data/limits/risks")
    return SkillResult(8, "Responsible AI, privacy, and governance", "fail", [],
                        "no LICENSE and no model-card-style document found")


NOT_ASSESSABLE = [
    (1, "Problem framing and business judgment",
     "about understanding what decision a project is meant to support -- not observable from files on disk"),
    (7, "Communication and data storytelling",
     "about how results are explained to a specific audience -- requires judging quality of prose/visuals, not just presence"),
    (9, "Domain knowledge in one industry",
     "depth of real industry context cannot be verified from a repo; a README mentioning a domain's vocabulary is not evidence of real expertise"),
]


def run_scorecard(root: Path, exclude_self: bool = True) -> list[SkillResult]:
    files = list(_walk_files(root, exclude_self=exclude_self))
    results = [
        check_code_quality_and_testing(root, files),
        check_llm_agent_patterns(root, files),
        check_evaluation_harness(root, files),
        check_data_pipeline(root, files),
        check_deployment_and_mlops(root, files),
        check_responsible_ai_governance(root, files),
    ]
    for skill_id, name, note in NOT_ASSESSABLE:
        results.append(SkillResult(skill_id, name, "not_assessable", [], note))
    results.sort(key=lambda r: r.skill_id)
    return results


def format_report(results: list[SkillResult]) -> str:
    lines = []
    assessable = [r for r in results if r.status != "not_assessable"]
    passed = sum(1 for r in assessable if r.status == "pass")
    for r in results:
        label = {"pass": "PASS", "fail": "FAIL", "not_assessable": "N/A "}[r.status]
        lines.append(f"[{label}] Skill {r.skill_id}: {r.name}")
        if r.note:
            lines.append(f"       {r.note}")
        for ev in r.evidence:
            lines.append(f"       - {ev}")
    lines.append("")
    lines.append(f"{passed}/{len(assessable)} assessable skills show observable signal "
                  f"({len(results) - len(assessable)} skill(s) not assessable from files alone)")
    return "\n".join(lines)


def _main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Score a repo against the 'Data Science 2027' 9-skill rubric.")
    parser.add_argument("root", type=Path, help="repository root to scan")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--include-self", action="store_true",
                         help="also scan this tool's own directory (off by default -- see _SELF_DIR's comment)")
    args = parser.parse_args(argv)

    if not args.root.is_dir():
        print(f"not a directory: {args.root}")
        return 2

    results = run_scorecard(args.root, exclude_self=not args.include_self)
    if args.json:
        print(json.dumps([
            {"skill_id": r.skill_id, "name": r.name, "status": r.status, "evidence": r.evidence, "note": r.note}
            for r in results
        ], indent=2))
    else:
        print(format_report(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
