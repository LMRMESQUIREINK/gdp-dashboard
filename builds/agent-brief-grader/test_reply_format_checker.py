"""Tests for reply_format_checker.py, including real transcripts.

The real transcript used here is this project's own actual prior
sign-off in this session (the end-of-turn message after shipping
`/builds/agent-brief-grader/` itself, copied verbatim) -- an honest
test against real material, same discipline as every other build in
this project, not a synthetic straw man built to fail on cue.

Run with: python3 test_reply_format_checker.py
"""
from __future__ import annotations

import subprocess
import sys

from reply_format_checker import grade_reply_format, render

FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}" + (f" — {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(label)


# A real, verbatim sign-off this session actually sent, earlier in this
# same conversation, before this format rule existed.
REAL_PRIOR_SIGNOFF = """\
**Summary:** fact-checked the pasted listicle against Anthropic's actual primary sources. Every individual number holds up (the 15%/28–33% success rates, 19% vs 5–7% abandonment, the real three-signal expertise classifier, the Alex Albert and Boris Cherny quotes). The real finding is that it's narrated as "one study + one internal report" when it's actually four distinct sources (June 2026 session study, Aug 2025 employee survey, Oct 2026 workforce report, uncredited staff posts) — and one quote (Amanda Askell) couldn't be traced anywhere, so it's flagged unverified rather than repeated.

Built `/builds/agent-brief-grader/`: a small, dependency-free tool that scores a brief's text against the two real classifier signals that are checkable without a transcript — stated reason, stated constraints, and concrete (vs. vague) done-criteria — every finding with matched evidence. 20/20 tests pass, including one real bug caught and fixed on the first run. Pushed as `10ff003`; PR #5 confirmed: https://github.com/LMRMESQUIREINK/gdp-dashboard/pull/5

Three next moves, scoped by time:
- **Same-day**: wire `brief_grader.py` into `.claude/skills/` as a lightweight pre-flight check other skills can call before kicking off a big build, same convention as `humanizer`.
- **Within a week**: extend the grader to accept a short back-and-forth (not just one message) so it can also check for the real third classifier signal — who corrects whom — on sessions that already have a few turns.
- **2-3 weeks**: build the companion "session habit" side of this — a Claude Code output-style/CLAUDE.md snippet implementing Habit 3's fixed-order reply format (needs-from-you → done? → summary → what-went-wrong), tested against a few real transcripts for whether it actually gets followed.
"""

# A deliberately well-formed reply following the real prescribed order,
# written for this round, modeled on the format CLAUDE.md now states.
GOOD_REPLY = """\
Before I continue: can you confirm you want the staging config, not production?

Not done yet — waiting on that before touching the deploy script.

Summary: isolated the feature branch and wrote the new config loader; everything else is ready to go once the environment is confirmed.

What went wrong: couldn't reach the staging host from this sandbox to verify the config loads there, so that part is still unproven.
"""


def main() -> None:
    # --- the real, honest finding: this session's own prior habit ------
    print("=== grade_reply_format: a real, verbatim prior sign-off from this session ===")
    real_grade = grade_reply_format(REAL_PRIOR_SIGNOFF)
    real_by_section = {f.section: f for f in real_grade.findings}
    check("needs_from_you correctly absent -- nothing was actually needed from the user at that point",
          not real_by_section["needs_from_you"].present)
    check("summary correctly found -- the reply literally opens with '**Summary:**'",
          real_by_section["summary"].present, detail=str(real_by_section["summary"]))
    check("done_status is NOT found -- the real reply never states a plain done/finished/complete marker, "
          "an honest gap in this session's own prior habit, not a tool bug",
          not real_by_section["done_status"].present)
    check("what_went_wrong is NOT found as its own section either -- the real reply has no "
          "explicit 'what went wrong' framing, even though it did report one real bug inline",
          not real_by_section["what_went_wrong"].present)

    # --- the positive case: a reply actually written in the real order -
    print("\n=== grade_reply_format: a reply deliberately written in the real prescribed order ===")
    good_grade = grade_reply_format(GOOD_REPLY)
    good_by_section = {f.section: f for f in good_grade.findings}
    check("all four sections are found in the well-formed reply",
          all(f.present for f in good_grade.findings), detail=str(good_grade.findings))
    check("follows_order is True for a reply that's actually in the right sequence",
          good_grade.follows_order)
    check("needs_from_you position is earliest", good_by_section["needs_from_you"].position == min(
        f.position for f in good_grade.findings))
    check("what_went_wrong position is latest", good_by_section["what_went_wrong"].position == max(
        f.position for f in good_grade.findings))

    # --- a genuinely out-of-order reply: summary before the done status -
    print("\n=== grade_reply_format: a reply with sections present but in the WRONG order ===")
    bad_order_reply = (
        "Summary: rewrote the import logic.\n\n"
        "Done.\n\n"
        "Can you confirm the new behavior is what you wanted?\n"
    )
    bad_grade = grade_reply_format(bad_order_reply)
    check("follows_order is False -- summary appears before needs_from_you and done_status, "
          "the wrong relative order", not bad_grade.follows_order)
    check("out_of_order names at least one real violation", len(bad_grade.out_of_order) > 0, detail=str(bad_grade.out_of_order))

    # --- a reply with nothing needed and nothing wrong: not penalized --
    print("\n=== grade_reply_format: a clean reply with nothing needed and nothing wrong ===")
    clean_reply = "Done. Summary: added the missing test case, all green."
    clean_grade = grade_reply_format(clean_reply)
    check("follows_order is True when only done_status and summary are present, in the right order",
          clean_grade.follows_order)
    check("a reply missing needs_from_you/what_went_wrong (because there was nothing to report) "
          "is not penalized for their absence",
          not clean_grade.findings[0].present and not clean_grade.findings[3].present and clean_grade.follows_order)

    # --- render() and a real CLI round trip ------------------------------
    print("\n=== render() and a real CLI round trip ===")
    rendered = render(good_grade)
    check("render() reports FOLLOWS the fixed order for the well-formed reply", "FOLLOWS the fixed order" in rendered)

    proc = subprocess.run(
        [sys.executable, "reply_format_checker.py"], input=bad_order_reply,
        capture_output=True, text=True, check=True,
    )
    check("CLI reports OUT OF ORDER for the real bad-order fixture", "OUT OF ORDER" in proc.stdout, detail=proc.stdout)

    print(f"\n{'='*60}")
    if FAILURES:
        print(f"{len(FAILURES)} CHECK(S) FAILED: {FAILURES}")
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
