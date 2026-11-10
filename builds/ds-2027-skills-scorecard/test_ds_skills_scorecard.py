import json
import subprocess
import sys
from pathlib import Path

from ds_skills_scorecard import run_scorecard, format_report, NOT_ASSESSABLE

THIS_DIR = Path(__file__).parent
REPO_ROOT = THIS_DIR.parents[1]


def _status(results, skill_id):
    return next(r for r in results if r.skill_id == skill_id).status


def build_strong_fixture(tmp_path: Path) -> Path:
    """A fixture with real, deliberate signal for every assessable skill."""
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_pipeline.py").write_text(
        "def test_fetch():\n    assert fetch() is not None\n", encoding="utf-8"
    )
    (tmp_path / "queries.sql").write_text("SELECT * FROM users;\n", encoding="utf-8")
    (tmp_path / "agent.py").write_text(
        "from anthropic import Anthropic\n"
        "def run_agent(prompt):\n"
        "    return vector_store.search(prompt)\n",
        encoding="utf-8",
    )
    (tmp_path / "eval_benchmark.py").write_text(
        "def test_eval():\n    assert model_output == expected_answer\n", encoding="utf-8"
    )
    (tmp_path / "data_pipeline.py").write_text(
        "def fetch_raw():\n    pass\n\ndef validate_schema(df):\n    pass\n", encoding="utf-8"
    )
    (tmp_path / "Dockerfile").write_text("FROM python:3.11\n", encoding="utf-8")
    (tmp_path / "LICENSE").write_text("MIT License\n", encoding="utf-8")
    (tmp_path / "MODEL_CARD.md").write_text("# Model Card\n\nIntended use: ...\n", encoding="utf-8")
    return tmp_path


def build_weak_fixture(tmp_path: Path) -> Path:
    """A fixture with NO signal for any assessable skill -- a bare script."""
    (tmp_path / "script.py").write_text("print('hello world')\n", encoding="utf-8")
    (tmp_path / "README.md").write_text(
        "This project uses problem framing, communication, and domain knowledge.\n",
        encoding="utf-8",
    )
    return tmp_path


def test_strong_fixture_passes_every_assessable_skill(tmp_path):
    build_strong_fixture(tmp_path)
    results = run_scorecard(tmp_path)
    assessable = [r for r in results if r.status != "not_assessable"]
    assert len(assessable) == 6
    for r in assessable:
        assert r.status == "pass", f"skill {r.skill_id} ({r.name}) unexpectedly failed: {r.note}"
        assert r.evidence, f"skill {r.skill_id} passed with no evidence"


def test_weak_fixture_fails_every_assessable_skill():
    """Discrimination test: a bare script with no real signal must fail every
    assessable skill, including one whose README literally contains the
    not-assessable skills' own names -- proving the tool checks for real file
    structure, not keyword-matching against skill names themselves."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        build_weak_fixture(tmp_path)
        results = run_scorecard(tmp_path)
        assessable = [r for r in results if r.status != "not_assessable"]
        assert len(assessable) == 6
        for r in assessable:
            assert r.status == "fail", f"skill {r.skill_id} ({r.name}) unexpectedly passed: {r.evidence}"


def test_not_assessable_skills_are_always_not_assessable_regardless_of_content(tmp_path):
    """Even when a fixture's content directly names skills 1/7/9, they must
    never be reported pass/fail -- they are not file-observable by design."""
    (tmp_path / "README.md").write_text(
        "Great problem framing here. Clear communication and storytelling. "
        "Deep domain knowledge in finance.\n",
        encoding="utf-8",
    )
    results = run_scorecard(tmp_path)
    for skill_id, _, _ in NOT_ASSESSABLE:
        assert _status(results, skill_id) == "not_assessable"


def test_license_without_model_card_is_a_partial_fail(tmp_path):
    (tmp_path / "LICENSE").write_text("MIT\n", encoding="utf-8")
    results = run_scorecard(tmp_path)
    governance = next(r for r in results if r.skill_id == 8)
    assert governance.status == "fail"
    assert "LICENSE found" in governance.note
    assert any("LICENSE" in e for e in governance.evidence)


def test_plain_unit_test_alone_does_not_satisfy_evaluation_harness(tmp_path):
    """A plain test file (satisfies skill 2) must NOT, by itself, satisfy
    skill 4's evaluation-harness check -- the two are deliberately distinct
    checks, per the module's own docstring."""
    (tmp_path / "test_basic.py").write_text("def test_add():\n    assert 1 + 1 == 2\n", encoding="utf-8")
    results = run_scorecard(tmp_path)
    assert _status(results, 2) == "pass"
    assert _status(results, 4) == "fail"


def test_airflow_dag_satisfies_data_pipeline_skill(tmp_path):
    (tmp_path / "dag.py").write_text(
        "from airflow import DAG\n\ndag = DAG('x', schedule_interval=None)\n", encoding="utf-8"
    )
    results = run_scorecard(tmp_path)
    data_eng = next(r for r in results if r.skill_id == 5)
    assert data_eng.status == "pass"
    assert "Airflow" in data_eng.note


def test_real_run_against_this_repo_matches_hand_checked_ground_truth():
    """The real deliverable: run against this project's own repo and confirm
    the result matches ground truth confirmed by hand (ls/find/grep) before
    this test was written, not just whatever the tool itself reports.

    Skill 5's expected "pass" was corrected mid-build: the first draft of
    this test assumed "fail" from checking only for literal airflow/dbt
    markers (there are none), without separately checking the pipeline-file
    fallback path -- running the real tool surfaced two genuine, legitimate
    data-pipeline modules this project already has
    (trading-jarvis/data_pipeline.py, recovery-desk/data_pipeline.py, both
    with real fetch/clean/validate-shaped functions per their own READMEs).
    Corrected to match the verified truth rather than forcing the tool to
    report "fail" to satisfy a wrong assumption -- same discipline as
    paired-bootstrap-ratchet's own mid-build test corrections."""
    results = run_scorecard(REPO_ROOT)
    # Ground truth confirmed by hand: this repo has 61+ test files, a real
    # LICENSE file, no Dockerfile/CI workflow anywhere, no dbt/Airflow
    # literal markers anywhere, but two real pipeline modules with
    # fetch/clean/validate functions.
    assert _status(results, 2) == "pass"  # tests exist
    assert _status(results, 5) == "pass"  # real pipeline modules, not a self-match (see test below)
    data_eng = next(r for r in results if r.skill_id == 5)
    assert "fetch/clean/validate" in data_eng.note
    assert any("data_pipeline.py" in e for e in data_eng.evidence)
    assert not any("ds-2027-skills-scorecard" in e for e in data_eng.evidence)
    assert _status(results, 8) == "fail"  # LICENSE exists but no model card anywhere
    governance = next(r for r in results if r.skill_id == 8)
    assert any("LICENSE" in e for e in governance.evidence)
    for skill_id, _, _ in NOT_ASSESSABLE:
        assert _status(results, skill_id) == "not_assessable"


def test_exclude_self_fixes_a_real_self_matching_bug_found_during_this_round():
    """Proves the bug was real, not hypothetical: scanning this exact repo
    WITHOUT excluding this tool's own directory reproduces the original false
    PASS on the data-pipeline skill, caught the first time this test file was
    written (this tool's own airflow_pattern regex literally spells "from
    airflow"/"import airflow" in its own source line, and this very test
    file's test_airflow_dag_satisfies_data_pipeline_skill fixture writes that
    exact string). With exclude_self (the real default), it's gone."""
    contaminated = run_scorecard(REPO_ROOT, exclude_self=False)
    assert _status(contaminated, 5) == "pass", (
        "if this assertion itself starts failing, the self-matching bug this round found "
        "and fixed may have been removed or changed -- re-verify before loosening this test"
    )
    data_eng = next(r for r in contaminated if r.skill_id == 5)
    assert any("ds-2027-skills-scorecard" in e for e in data_eng.evidence), (
        "the contaminated run should point back at this tool's own files as the false evidence"
    )

    clean = run_scorecard(REPO_ROOT, exclude_self=True)
    clean_data_eng = next(r for r in clean if r.skill_id == 5)
    assert not any("ds-2027-skills-scorecard" in e for e in clean_data_eng.evidence), (
        "the clean run must not point at this tool's own files as evidence"
    )
    # Still "pass", but now for a real, independently-confirmed reason (see
    # test_real_run_against_this_repo_matches_hand_checked_ground_truth) --
    # excluding self removes the FALSE evidence, it doesn't force a "fail".
    assert clean_data_eng.status == "pass"
    assert any("data_pipeline.py" in e for e in clean_data_eng.evidence)


def test_cli_json_mode(tmp_path):
    build_strong_fixture(tmp_path)
    result = subprocess.run(
        [sys.executable, str(THIS_DIR / "ds_skills_scorecard.py"), str(tmp_path), "--json"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert len(data) == 9
    assert all("evidence" in entry for entry in data)


def test_format_report_includes_a_summary_line(tmp_path):
    build_strong_fixture(tmp_path)
    results = run_scorecard(tmp_path)
    text = format_report(results)
    assert "assessable skills show observable signal" in text
    assert "6/6" in text
