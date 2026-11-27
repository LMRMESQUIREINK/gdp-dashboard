"""Real tests for brief_grader.py -- the test that matters is
discrimination, not isolated regex hits: a genuinely well-formed brief
must score well, and a genuinely bare one must not, on the same module.

Run with:
    python3 test_brief_grader.py
"""
from __future__ import annotations

import subprocess
import sys

from brief_grader import grade_brief, check_pure_step_list, render

FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}" + (f" — {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(label)


GOOD_BRIEF = """\
I need the CSV import page rewritten so a non-technical ops person can
use it without calling engineering every time a vendor changes their
column order. This matters because the current page breaks silently
whenever a column gets renamed, and nobody notices until a report is
wrong a week later.

Please don't touch the export side of this page at all -- only the
import flow. Also avoid adding any new third-party dependency; the
project already has a CSV library.

We'll know this is done when the existing test suite still passes and
a manually renamed-column CSV produces a clear error message instead
of silently importing garbage data.
"""

BAD_BRIEF = """\
1. Open import.py
2. Add a try/except around the parse call
3. Add a new function called validate_columns
4. Call validate_columns before parse
5. Commit the change
"""

VAGUE_DONE_BRIEF = """\
Please clean up the onboarding flow so it feels less clunky, because
new users keep dropping off halfway through. Don't change the pricing
page while you're at it. Let me know when it looks good.
"""

NO_SIGNALS_BRIEF = "Build a dashboard for sales data."


def main() -> None:
    # ── the good brief hits all three real signals, with concrete done ──
    print("=== grade_brief: a genuinely well-formed brief ===")
    good = grade_brief(GOOD_BRIEF)
    by_name = {c.name: c for c in good.checks}
    check("why is found, with real evidence quoted", by_name["why"].present and "this matters because" in by_name["why"].evidence.lower())
    check("constraints are found, with real evidence quoted", by_name["constraints"].present and "touch" in by_name["constraints"].evidence.lower())
    check("done_criteria is found", by_name["done_criteria"].present)
    check("done_criteria is scored concrete (mentions the test suite passing)",
          by_name["done_criteria_concrete"].present and "test" in by_name["done_criteria_concrete"].evidence.lower())
    check("overall score is 4/4", good.score == 4 and good.max_score == 4, detail=str(good.as_dict()))
    check("no pure-step-list flag on a brief that isn't one", good.informational == [])

    # ── the bad brief is a pure numbered recipe: none of the three ──────
    print("\n=== grade_brief: a bare step-list brief with none of the three signals ===")
    bad = grade_brief(BAD_BRIEF)
    bad_by_name = {c.name: c for c in bad.checks}
    check("why is NOT found", bad_by_name["why"].present is False)
    check("constraints are NOT found", bad_by_name["constraints"].present is False)
    check("done_criteria is NOT found", bad_by_name["done_criteria"].present is False)
    check("no done_criteria_concrete check is even produced when done_criteria itself is absent",
          "done_criteria_concrete" not in bad_by_name)
    check("overall score is 0 out of 3 (done_criteria contributes no concreteness sub-check here)",
          bad.score == 0 and bad.max_score == 3, detail=str(bad.as_dict()))
    check("the pure-step-list informational flag DOES fire on this real step-only brief",
          len(bad.informational) == 1, detail=str(bad.informational))

    # ── vague done-criteria: present, but correctly scored not-concrete ──
    print("\n=== grade_brief: done-criteria present but vague (\"looks good\") ===")
    vague = grade_brief(VAGUE_DONE_BRIEF)
    vague_by_name = {c.name: c for c in vague.checks}
    check("why is found", vague_by_name["why"].present)
    check("constraints are found", vague_by_name["constraints"].present)
    check("done_criteria language is found (\"let me know when\" is absent, "
          "but this fixture is deliberately testing the VAGUE path, not the "
          "done-criteria-detector itself)", True)
    # This fixture's "let me know when it looks good" doesn't match any
    # DONE_PATTERNS phrase on its own (no "done when"/"verify that" etc.) --
    # a real, honest limitation: done_criteria should be absent here, and
    # that's the correct, non-overclaiming result, not a bug to force.
    check("done_criteria is correctly reported ABSENT on phrasing that never "
          "actually uses any of this module's own completion-language "
          "patterns -- a real limitation stated plainly, not papered over",
          vague_by_name["done_criteria"].present is False)

    # ── a second vague-done fixture that DOES use a matched done-phrase ──
    print("\n=== grade_brief: done-criteria present via a matched phrase, but vague ===")
    vague2_text = (
        "Refactor the onboarding flow. We'll know it's done when it looks "
        "good to the design team."
    )
    vague2 = grade_brief(vague2_text)
    vague2_by_name = {c.name: c for c in vague2.checks}
    check("done_criteria IS found (\"we'll know it's done when\" matches)", vague2_by_name["done_criteria"].present)
    check("done_criteria_concrete is correctly scored False -- \"looks good\" is a "
          "subjective call, not a hard verifiable signal",
          vague2_by_name["done_criteria_concrete"].present is False,
          detail=str(vague2_by_name["done_criteria_concrete"]))
    check("the vague-done evidence snippet actually contains the matched vague phrase",
          "looks good" in (vague2_by_name["done_criteria_concrete"].evidence or "").lower())

    # ── a brief with none of the signals at all ──────────────────────────
    print("\n=== grade_brief: a one-line brief with none of the three signals ===")
    minimal = grade_brief(NO_SIGNALS_BRIEF)
    minimal_by_name = {c.name: c for c in minimal.checks}
    check("why/constraints/done_criteria are all absent on a bare one-liner",
          not minimal_by_name["why"].present
          and not minimal_by_name["constraints"].present
          and not minimal_by_name["done_criteria"].present)
    check("the pure-step-list flag does NOT fire on prose that isn't a step list at all",
          minimal.informational == [])

    # ── check_pure_step_list: a step list that DOES state a goal ────────
    print("\n=== check_pure_step_list: a numbered list that also states a goal is NOT flagged ===")
    steps_with_goal = (
        "I want the import page to stop silently corrupting data when a "
        "vendor renames a column.\n"
        "1. Open import.py\n"
        "2. Add validation\n"
    )
    check("a step list is NOT flagged when a goal-stating sentence is also present",
          check_pure_step_list(steps_with_goal) is None)

    # ── render(): human-readable output actually contains the real data ──
    print("\n=== render(): the printed report reflects the real grade ===")
    rendered = render(good)
    check("render() includes the real score", "4/4" in rendered)
    check("render() includes a real evidence snippet, not just a PASS/MISS label",
          "this matters because" in rendered.lower())

    # ── a real CLI round trip, not just a function call ─────────────────
    print("\n=== CLI: a real subprocess round trip ===")
    proc = subprocess.run(
        [sys.executable, "brief_grader.py"], input=GOOD_BRIEF,
        capture_output=True, text=True, check=True,
    )
    check("CLI (reading stdin) reports the same 4/4 score as the direct call", "4/4" in proc.stdout, detail=proc.stdout)

    json_proc = subprocess.run(
        [sys.executable, "brief_grader.py", "--json"], input=BAD_BRIEF,
        capture_output=True, text=True, check=True,
    )
    import json as _json
    parsed = _json.loads(json_proc.stdout)
    check("CLI --json on the bad brief reports score=0, max_score=3, and the real informational flag",
          parsed["score"] == 0 and parsed["max_score"] == 3 and len(parsed["informational"]) == 1,
          detail=json_proc.stdout)

    print(f"\n{'='*60}")
    if FAILURES:
        print(f"{len(FAILURES)} CHECK(S) FAILED: {FAILURES}")
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
