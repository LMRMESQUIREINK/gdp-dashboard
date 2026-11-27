"""Tests for conversation_grader.py -- the real third classifier signal
("whether the user tends to correct Claude or Claude tends to correct
the user") made checkable now that a transcript, not just one message,
is in hand.

Run with: python3 test_conversation_grader.py
"""
from __future__ import annotations

import subprocess
import sys

from conversation_grader import Turn, check_correction_balance, grade_conversation, render

FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}" + (f" — {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(label)


GOOD_BRIEF_TEXT = (
    "Build a login page because users keep complaining about slow "
    "signups. Don't touch the signup flow. Done when the existing "
    "test suite still passes."
)


def main() -> None:
    # --- a clean transcript: zero corrections either way ----------------
    print("=== check_correction_balance: a clean transcript with no corrections ===")
    clean_turns = [
        Turn("user", GOOD_BRIEF_TEXT),
        Turn("assistant", "Done. The login page is live and the test suite passes."),
    ]
    clean_balance = check_correction_balance(clean_turns)
    check("zero user corrections on a transcript with none", clean_balance.user_count == 0)
    check("zero assistant corrections on a transcript with none", clean_balance.assistant_count == 0)
    check("a real 0-0 tie is reported as 'even', not an error or undefined state", clean_balance.balance == "even")

    # --- the user corrects Claude more than Claude corrects the user ----
    print("\n=== check_correction_balance: the user corrects Claude twice, Claude never corrects back ===")
    user_heavy_turns = [
        Turn("user", GOOD_BRIEF_TEXT),
        Turn("assistant", "Here's the signup page."),
        Turn("user", "No, that's wrong — I asked for the login page, not signup."),
        Turn("assistant", "Here's the login page now."),
        Turn("user", "Actually it should use the new auth library, not the old one."),
        Turn("assistant", "Updated to use the new auth library."),
    ]
    user_heavy = check_correction_balance(user_heavy_turns)
    check("exactly 2 real user corrections found", user_heavy.user_count == 2, detail=str(user_heavy.user_corrections))
    check("0 assistant corrections found", user_heavy.assistant_count == 0)
    check("balance correctly reports 'user'", user_heavy.balance == "user")
    check("the real matched text is the evidence, not a bare label",
          "login page" in user_heavy.user_corrections[0].evidence, detail=user_heavy.user_corrections[0].evidence)

    # --- Claude corrects itself / catches its own issue more often ------
    print("\n=== check_correction_balance: Claude corrects itself more than the user corrects Claude ===")
    assistant_heavy_turns = [
        Turn("user", GOOD_BRIEF_TEXT),
        Turn("assistant", "My mistake, I used the wrong field name — fixing that now."),
        Turn("user", "Thanks."),
        Turn("assistant", "Correction: the test I ran was against the wrong branch, re-running on main."),
    ]
    assistant_heavy = check_correction_balance(assistant_heavy_turns)
    check("exactly 2 real assistant corrections found", assistant_heavy.assistant_count == 2, detail=str(assistant_heavy.assistant_corrections))
    check("0 user corrections found", assistant_heavy.user_count == 0)
    check("balance correctly reports 'assistant'", assistant_heavy.balance == "assistant")

    # --- grade_conversation(): combines the brief grade + the balance ---
    print("\n=== grade_conversation: combines the first user turn's brief grade with the whole-transcript balance ===")
    combined = grade_conversation(user_heavy_turns)
    check("the brief grade is computed from the FIRST user turn only",
          combined.brief_grade.score == 4,  # why + constraints + done_criteria + done_criteria_concrete
          # (GOOD_BRIEF_TEXT's "the existing test suite still passes" is itself a concrete,
          # checkable done-criterion -- a real 4/4, not 3/4 as a first draft of this test
          # wrongly assumed before actually running it)
          detail=str(combined.brief_grade.as_dict()))
    check("the correction balance covers the whole transcript, not just the first turn",
          combined.correction_balance.user_count == 2)

    rendered = render(combined)
    check("render() includes both the brief grade and the correction balance", "Brief grade" in rendered and "Correction balance" in rendered)
    check("render() names the real balance", "balance: user" in rendered, detail=rendered)

    # --- a real CLI round trip, JSON in, JSON/text out -------------------
    print("\n=== CLI: a real subprocess round trip ===")
    import json as _json

    payload = _json.dumps([{"role": t.role, "text": t.text} for t in user_heavy_turns])
    proc = subprocess.run(
        [sys.executable, "conversation_grader.py"], input=payload,
        capture_output=True, text=True, check=True,
    )
    check("CLI (reading stdin JSON) reports balance: user", "balance: user" in proc.stdout, detail=proc.stdout)

    proc_json = subprocess.run(
        [sys.executable, "conversation_grader.py", "--json"], input=payload,
        capture_output=True, text=True, check=True,
    )
    parsed = _json.loads(proc_json.stdout)
    check("CLI --json reports the exact same real counts as the direct call",
          parsed["correction_balance"]["user_count"] == 2 and parsed["correction_balance"]["assistant_count"] == 0,
          detail=proc_json.stdout)

    print(f"\n{'='*60}")
    if FAILURES:
        print(f"{len(FAILURES)} CHECK(S) FAILED: {FAILURES}")
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
