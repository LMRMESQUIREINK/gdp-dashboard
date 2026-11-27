"""Proves stale_after actually catches something -- not just that the
clock arithmetic in is_stale() works (test_okf_navigator.py's own
suite already covers that trivial case), but that the fresh/stale
transition genuinely gates whether a bundle's "## Consumers" claims
can still be trusted.

None of this project's three existing OKF bundles (this one's own
fixtures, trading-jarvis's, interface-lift-toolkit's -- and now
policy-control-plane's) has ever actually been re-grepped after a
later real code change, so there was no real evidence that catching
staleness in time would have caught real drift, as opposed to a
countdown nobody ever acts on. This test builds the smallest real
scenario that can demonstrate it directly:

  1. A real two-file module pair (fixtures/drift-scenario/code/) with
     one real import edge, documented by a real OKF bundle
     (fixtures/drift-scenario/bundle/) at generation time.
  2. A real code change: a THIRD file is added that imports the same
     target module -- the bundle's own "## Consumers" section was
     never updated to say so, the exact "core file missing, only
     consumers uploaded"/"a new upload doesn't carry forward a prior
     fix" pattern this project has hit for real, over and over, across
     every Trading Jarvis round.
  3. Before stale_after: impact_report() reports the module "fresh" --
     even though real drift already exists on disk. This is the risk
     stale_after exists to bound, demonstrated rather than asserted.
  4. After stale_after: impact_report() reports it "stale" -- the
     signal that should trigger a re-check.
  5. A real re-grep at that point (a small, honest helper -- not the
     general reusable tool; that's drift_check.py, built separately
     and proven against this same scenario) DOES catch the exact
     drift, and a control run against the UNCHANGED code finds none --
     proving the check discriminates rather than always firing.

Run with: python3 test_staleness_value.py
"""
from __future__ import annotations

import ast
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from okf_navigator import impact_report, is_stale, load_bundle

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "drift-scenario"
BUNDLE_DIR = FIXTURE_ROOT / "bundle"
CODE_DIR = FIXTURE_ROOT / "code"

FAILURES: list[str] = []


def check(cond, name, detail=""):
    status = "ok  " if cond else "FAIL"
    print(f"{status} - {name}" + (f" ({detail})" if detail and not cond else ""))
    if not cond:
        FAILURES.append(name)


def _real_consumers(code_dir: Path, target_stem: str) -> set[str]:
    """The small, honest re-grep this test needs: which .py files in
    code_dir actually import target_stem, right now, on disk? Uses a
    real AST parse (not a regex) so it isn't fooled by a module name
    appearing in a comment or string."""
    consumers = set()
    for py_file in sorted(code_dir.glob("*.py")):
        if py_file.stem == target_stem:
            continue
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == target_stem:
                consumers.add(py_file.stem)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == target_stem:
                        consumers.add(py_file.stem)
    return consumers


def main() -> None:
    t_before_change = datetime(2026, 11, 27, 6, 0, tzinfo=timezone.utc)   # before the code change, before stale_after
    t_after_change_still_fresh = datetime(2026, 11, 27, 18, 0, tzinfo=timezone.utc)  # after the change, STILL before stale_after
    t_stale = datetime(2026, 11, 28, 1, 0, tzinfo=timezone.utc)           # after stale_after

    # --- sanity: the real fixture code starts with only the documented edge
    print("=== before any change: the fixture's own real import graph matches the bundle ===")
    real_before = _real_consumers(CODE_DIR, "payment_processor")
    check(real_before == {"checkout_flow"}, "real AST grep finds exactly the one documented consumer", real_before)

    bundle = load_bundle(BUNDLE_DIR)
    report_before = impact_report(bundle, "payment-processor.md", max_hops=1, now=t_before_change)
    check("checkout-flow.md" in report_before, "the bundle's own documented consumer appears in the report")
    check("lifecycle=fresh" in report_before, "before stale_after, the module reports fresh", report_before)

    # --- the real code change: a genuinely new file is added, mimicking
    # the exact "a later upload/edit adds a real new consumer, the
    # existing docs never get told" pattern this project has hit for
    # real on every Trading Jarvis round -- done in a TEMP COPY, never
    # touching the committed fixture.
    print("\n=== a real code change: a new consumer file is added, undocumented ===")
    with tempfile.TemporaryDirectory() as tmp:
        work_code = Path(tmp) / "code"
        shutil.copytree(CODE_DIR, work_code)
        (work_code / "refund_handler.py").write_text(
            '"""A genuinely new real file, added after the bundle was written -- '
            'the bundle\'s own "## Consumers" section was never updated to say so."""\n'
            "from payment_processor import charge\n\n\n"
            "def issue_refund(amount_cents: int) -> dict:\n"
            "    return charge(-amount_cents)\n"
        )

        real_after = _real_consumers(work_code, "payment_processor")
        check(real_after == {"checkout_flow", "refund_handler"},
              "the real AST grep now finds the genuinely new consumer", real_after)

        # The bundle text itself hasn't changed -- nobody edited it.
        # --- the risk window: drift exists, but the bundle still says fresh
        report_after_still_fresh = impact_report(bundle, "payment-processor.md", max_hops=1, now=t_after_change_still_fresh)
        check("lifecycle=fresh" in report_after_still_fresh,
              "immediately after the undocumented change, but still before stale_after, "
              "the module STILL reports fresh -- this is the real risk window stale_after exists to bound",
              report_after_still_fresh)
        check("refund-handler.md" not in report_after_still_fresh,
              "the report (built only from the bundle's own text) has no way to know about "
              "the new file on its own -- it can only ever report what's documented")
        drifted_while_fresh = real_after != {c.replace("-", "_") for c in {"checkout_flow"}}
        check(drifted_while_fresh,
              "real drift exists on disk right now, while the bundle still reports itself fresh")

        # --- the trigger: once stale_after passes, the module reports stale
        print("\n=== once stale_after passes, the module correctly reports stale ===")
        report_stale = impact_report(bundle, "payment-processor.md", max_hops=1, now=t_stale)
        check("lifecycle=stale" in report_stale, "after stale_after, the same unmodified bundle now reports stale", report_stale)

        # --- the payoff: re-checking AT that trigger point catches the real drift
        print("\n=== re-checking at the stale trigger catches the exact real drift ===")
        documented = set()
        for raw_target in bundle["payment-processor.md"].links:
            target = raw_target
            if target.endswith(".md"):
                documented.add(Path(target).name[:-3].replace("-", "_"))
        real_now = _real_consumers(work_code, "payment_processor")
        missing_from_docs = real_now - documented
        check(missing_from_docs == {"refund_handler"},
              "a re-grep performed at the stale trigger finds exactly the one real, "
              "undocumented consumer the code change introduced", missing_from_docs)

        # --- the control: re-checking UNCHANGED code at the same trigger finds nothing
        print("\n=== control: re-checking unmodified code at the same trigger finds no drift ===")
        real_unchanged = _real_consumers(CODE_DIR, "payment_processor")
        missing_unchanged = real_unchanged - documented
        check(missing_unchanged == set(),
              "the same check against the real, unmodified fixture code (no drift introduced) "
              "finds nothing -- the check discriminates rather than always firing", missing_unchanged)

    print(f"\n{len(FAILURES)} failed" if FAILURES else "\nALL CHECKS PASSED")
    if FAILURES:
        sys.exit(1)


if __name__ == "__main__":
    main()
