"""Tests for drift_check.py -- the generalized, reusable version of
the comparison test_staleness_value.py proved has real value. Run
against both the synthetic drift-scenario fixture (proving it fires on
real, deliberately-introduced drift and stays quiet otherwise) AND
every real okf_knowledge/ bundle already shipped in this project
(proving it's a real drop-in tool, not just plausible on one fixture).

Run with: python3 test_drift_check.py
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

from drift_check import check_drift

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "drift-scenario"
REPO_BUILDS = Path(__file__).resolve().parents[1]  # /home/user/gdp-dashboard/builds

FAILURES: list[str] = []


def check(cond, name, detail=""):
    status = "ok  " if cond else "FAIL"
    print(f"{status} - {name}" + (f" ({detail})" if detail and not cond else ""))
    if not cond:
        FAILURES.append(name)


def main() -> None:
    # --- the synthetic scenario, unchanged: no drift ------------------
    print("=== check_drift against the real, unmodified drift-scenario fixture ===")
    clean_results = check_drift(FIXTURE_ROOT / "code", FIXTURE_ROOT / "bundle")
    clean_by_stem = {d.module_stem: d for d in clean_results}
    check("payment_processor" in clean_by_stem, "payment_processor.py is checked")
    check(not clean_by_stem["payment_processor"].has_drift,
          "no drift against the real, unmodified fixture", clean_by_stem["payment_processor"])

    # --- the synthetic scenario, with the same real drift introduced --
    print("\n=== check_drift catches the same real drift test_staleness_value.py proved stale_after would flag ===")
    with tempfile.TemporaryDirectory() as tmp:
        work_code = Path(tmp) / "code"
        shutil.copytree(FIXTURE_ROOT / "code", work_code)
        (work_code / "refund_handler.py").write_text(
            "from payment_processor import charge\n\n\ndef issue_refund(c):\n    return charge(-c)\n"
        )
        drifted_results = check_drift(work_code, FIXTURE_ROOT / "bundle")
        drifted_by_stem = {d.module_stem: d for d in drifted_results}
        check(drifted_by_stem["payment_processor"].has_drift, "drift is detected once the new file exists")
        check(drifted_by_stem["payment_processor"].undocumented == {"refund_handler"},
              "the exact new, undocumented consumer is named", drifted_by_stem["payment_processor"].undocumented)
        check(drifted_by_stem["payment_processor"].stale_claims == set(),
              "no stale claim is raised -- checkout_flow.py still really imports it too",
              drifted_by_stem["payment_processor"].stale_claims)

        rendered = __import__("drift_check").render(drifted_results)
        check("UNDOCUMENTED: refund_handler.py" in rendered, "the rendered report names the real finding in plain text", rendered)

    # --- a stale CLAIM, the other half of a drift: documented but no longer real
    print("\n=== check_drift separately catches a stale claim (documented but no longer a real import) ===")
    with tempfile.TemporaryDirectory() as tmp:
        work_code = Path(tmp) / "code"
        shutil.copytree(FIXTURE_ROOT / "code", work_code)
        # checkout_flow.py no longer actually imports payment_processor --
        # simulates the module being refactored to use a different path,
        # with the bundle never updated to match.
        (work_code / "checkout_flow.py").write_text(
            '"""No longer imports payment_processor at all."""\n'
            "def complete_checkout(amount_cents: int) -> dict:\n"
            "    return {'charged': amount_cents}\n"
        )
        results = check_drift(work_code, FIXTURE_ROOT / "bundle")
        by_stem = {d.module_stem: d for d in results}
        check(by_stem["payment_processor"].stale_claims == {"checkout_flow"},
              "the stale, no-longer-real consumer claim is caught", by_stem["payment_processor"].stale_claims)
        check(by_stem["payment_processor"].undocumented == set(),
              "no undocumented-consumer finding is raised in this scenario")

    # --- the real deliverable: every real okf_knowledge/ bundle already
    # shipped in this project reports clean against its own real source.
    print("\n=== check_drift against every real okf_knowledge/ bundle already shipped in this project ===")
    real_targets = [
        ("trading-jarvis", REPO_BUILDS / "trading-jarvis", REPO_BUILDS / "trading-jarvis" / "okf_knowledge"),
        ("interface-lift-toolkit", REPO_BUILDS / "interface-lift-toolkit", REPO_BUILDS / "interface-lift-toolkit" / "okf_knowledge"),
        ("policy-control-plane", REPO_BUILDS / "policy-control-plane", REPO_BUILDS / "policy-control-plane" / "okf_knowledge"),
    ]
    for name, source_dir, bundle_dir in real_targets:
        if not bundle_dir.is_dir():
            check(False, f"{name}'s okf_knowledge/ bundle exists", detail=str(bundle_dir))
            continue
        results = check_drift(source_dir, bundle_dir)
        checked_count = len(results)
        drifted = [d for d in results if d.has_drift]
        check(checked_count > 0, f"{name}: at least one real module was checked against its own real bundle", checked_count)
        check(drifted == [], f"{name}: zero drift found against its own real, current source — "
              "a real, non-manufactured clean result, same as every other real check this project runs",
              [(d.concept_path, sorted(d.undocumented), sorted(d.stale_claims)) for d in drifted])

    # --- a real CLI round trip ----------------------------------------
    print("\n=== a real CLI round trip ===")
    import subprocess

    proc_clean = subprocess.run(
        [sys.executable, "drift_check.py", str(FIXTURE_ROOT / "code"), str(FIXTURE_ROOT / "bundle")],
        capture_output=True, text=True,
    )
    check(proc_clean.returncode == 0 and "No drift found" in proc_clean.stdout,
          "CLI exits 0 and reports no drift against the clean fixture", proc_clean.stdout)

    with tempfile.TemporaryDirectory() as tmp:
        work_code = Path(tmp) / "code"
        shutil.copytree(FIXTURE_ROOT / "code", work_code)
        (work_code / "refund_handler.py").write_text("from payment_processor import charge\n")
        proc_drift = subprocess.run(
            [sys.executable, "drift_check.py", str(work_code), str(FIXTURE_ROOT / "bundle")],
            capture_output=True, text=True,
        )
        check(proc_drift.returncode == 1 and "UNDOCUMENTED: refund_handler.py" in proc_drift.stdout,
              "CLI exits 1 and names the real finding when drift exists", proc_drift.stdout)

    print(f"\n{len(FAILURES)} failed" if FAILURES else "\nALL CHECKS PASSED")
    if FAILURES:
        sys.exit(1)


if __name__ == "__main__":
    main()
