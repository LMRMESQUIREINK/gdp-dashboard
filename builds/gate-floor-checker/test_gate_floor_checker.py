"""Tests for gate_floor_checker.py, including a reconstruction of the
real published numbers from ayghri/i-have-adhd's evals/RESULTS.md (the
source this tool was built from).

Run with: python3 test_gate_floor_checker.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from gate_floor_checker import CaseTrials, check_gate_floor  # noqa: E402

passed = 0
failed = 0


def check(cond, name, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print("ok   - " + name)
    else:
        failed += 1
        print("FAIL - " + name + (f" ({detail})" if detail else ""))


# --- CaseTrials basics ---------------------------------------------
c = CaseTrials("x", [False, False, True])
check(c.trial_count == 3, "trial_count counts every recorded trial")
check(c.blocked_count == 1, "blocked_count counts only the blocked trials")
check(c.ever_cleared is True, "ever_cleared is True when at least one trial had zero blockers")
check(c.never_cleared is False, "never_cleared is the negation of ever_cleared")

c2 = CaseTrials("y", [True, True, True])
check(c2.ever_cleared is False, "a case blocked on every trial never cleared")
check(c2.never_cleared is True, "never_cleared is True when every trial was blocked")

try:
    CaseTrials("empty", [])
    check(False, "an empty trial list raises", "no exception raised")
except ValueError:
    check(True, "an empty trial list raises ValueError rather than silently modeling zero evidence as a pass")

# --- check_gate_floor: PASS -----------------------------------------
clean = [CaseTrials("a", [False, False]), CaseTrials("b", [False, False, False])]
r = check_gate_floor(clean)
check(r.verdict == "PASS", "a run where every case's every trial was clean passes")
check(r.currently_passing is True, "currently_passing matches the PASS verdict")
check(r.blocked_case_ids == [], "no case ids are listed as blocked on a PASS")

# --- check_gate_floor: FAIL_IMPROVABLE -------------------------------
improvable = [
    CaseTrials("a", [True, False, False]),   # blocked once, cleared twice -- real signal exists, improvable
    CaseTrials("b", [False, False, True]),   # blocked once, cleared twice -- same
]
r2 = check_gate_floor(improvable)
check(r2.verdict == "FAIL_IMPROVABLE", "a run whose blocking cases have each cleared at least once elsewhere is classified improvable", r2.verdict)
check(set(r2.blocked_case_ids) == {"a", "b"}, "both cases drew a blocker somewhere in their trial batch, so both are reported as currently blocking")
check(r2.never_cleared_case_ids == [], "neither case is in never_cleared, since both have a clean trial on record")

# --- check_gate_floor: FAIL_STRUCTURAL -------------------------------
structural = [
    CaseTrials("good", [False, False, False]),
    CaseTrials("unpassable", [True, True, True]),   # blocked on every recorded trial
    CaseTrials("clean-elsewhere", [False, False, False]),  # never blocked at all -- not implicated here
]
r3 = check_gate_floor(structural)
check(r3.verdict == "FAIL_STRUCTURAL", "a run blocked by a case that never once cleared is classified structural", r3.verdict)
check(r3.blocked_case_ids == ["unpassable"], "only the structurally-unpassable case is reported as blocking THIS run")
check(r3.never_cleared_case_ids == ["unpassable"], "never_cleared correctly names the one case with zero clean trials")
check(r3.excluding_never_cleared is not None, "a structural failure computes an 'excluding' sub-report")
check(r3.excluding_never_cleared.verdict == "PASS", "excluding the unpassable case, the remaining cases pass on their own")

# --- a run where BOTH an improvable and a structural case block together
mixed = [
    CaseTrials("unpassable", [True, True, True]),
    CaseTrials("improvable", [True, False, True]),  # blocked now, but cleared trial 1 -- real signal exists
]
r4 = check_gate_floor(mixed)
check(r4.verdict == "FAIL_STRUCTURAL", "if ANY currently-blocking case is structural, the overall verdict is structural, not improvable")
check(set(r4.blocked_case_ids) == {"unpassable", "improvable"}, "both currently-blocking cases are listed, even though only one is structural")
check(r4.excluding_never_cleared.verdict == "FAIL_IMPROVABLE", "excluding the structural case, the remaining real regression is still correctly flagged as improvable, not swept away")

try:
    check_gate_floor([])
    check(False, "an empty case list raises", "no exception raised")
except ValueError:
    check(True, "an empty case list raises ValueError rather than vacuously reporting PASS")

# --- known_structural overrides trial-based inference -----------------
# A case that cleared on ITS trials can still be confirmed structural by
# an out-of-band architectural fact a human has actually verified --
# the exact situation the real i-have-adhd case is in (see below): three
# trials cannot prove impossibility on their own; known_structural is
# how stronger evidence overrides a trial history that can't.
ambiguous_but_confirmed = CaseTrials("broken-by-design", [True, True, False], known_structural=True)
check(ambiguous_but_confirmed.ever_cleared is True, "sanity: this case DID clear on one of its three trials")
check(ambiguous_but_confirmed.never_cleared is True, "known_structural overrides a trial history that includes a clean run")
r5 = check_gate_floor([CaseTrials("ok", [False]), ambiguous_but_confirmed])
check(r5.verdict == "FAIL_STRUCTURAL", "a known_structural case still yields FAIL_STRUCTURAL even though its own trial history alone would only support FAIL_IMPROVABLE")

# ---------------------------------------------------------------------
# Real-data reconstruction: ayghri/i-have-adhd evals/RESULTS.md,
# recorded run dated 2026-08-02, 14 cases, 3 trials each.
#
# Numbers STATED EXACTLY in the source: baseline 7 total blockers,
# candidate 3 total blockers; the section heading "agent-owned-edit
# cannot be passed by any run" (by construction -- the harness runs
# with --tools "", so its pass criterion can never be met) and "Both
# conditions draw blockers on it in most trials"; "two of the three
# candidate blockers come from" that case, leaving candidate 1 / baseline
# 5 once it's excluded -- both stated exactly ("Excluding that case the
# count is baseline 5, candidate 1"); the sole remaining candidate
# blocker is named as landing on partial-success, with three per-trial
# deltas given (+0.05, -0.70, -1.25) showing a real, directionally-
# consistent regression, not simulated as "most trials" the way
# agent-owned-edit is.
#
# What's RECONSTRUCTED rather than published verbatim: the source gives
# "most trials" for agent-owned-edit, not an exact per-trial pattern, and
# states the total candidate-blocker arithmetic in prose ("two of the
# three candidate blockers come from" it, leaving 1 for partial-success)
# rather than a full case-by-trial matrix. The reconstruction below picks
# the one pattern per case consistent with every number actually
# published -- 2 blocked trials for agent-owned-edit ("most" of 3), 1 for
# partial-success, 0 for the other 12, summing to the stated candidate
# total of 3 -- and marks agent-owned-edit's case-level blockedness with
# known_structural=True rather than forcing its trial pattern to read as
# 3-for-3: the source's "cannot be passed by any run" claim is explicitly
# an architectural one (the harness runs with --tools "", confirmed by
# reading the fixture), not an induction over three trials, so it belongs
# behind the field this tool built specifically to carry that distinction
# (see CaseTrials.known_structural) rather than faked into the trial data.
REAL_IHA_CASES = [
    CaseTrials("multi-step-progress", [False, False, False]),
    CaseTrials("error-report", [False, False, False]),
    CaseTrials("medical-boundary", [False, False, False]),
    CaseTrials("destructive-action", [False, False, False]),
    CaseTrials("debugging-cause", [False, False, False]),
    CaseTrials("casual-message", [False, False, False]),
    CaseTrials("real-ambiguity", [False, False, False]),
    CaseTrials("concept-explanation", [False, False, False]),
    CaseTrials("direct-answer", [False, False, False]),
    CaseTrials("complex-plan", [False, False, False]),
    CaseTrials("long-form-request", [False, False, False]),
    CaseTrials("code-answer", [False, False, False]),
    CaseTrials("agent-owned-edit", [True, True, False], known_structural=True),  # "most trials" blocked + confirmed architecturally unpassable
    CaseTrials("partial-success", [True, False, False]),  # 1 of 3 candidate trials blocked (the sole non-structural blocker)
]

iha_total_candidate_blockers = sum(1 for c in REAL_IHA_CASES for b in c.blocked if b)
check(iha_total_candidate_blockers == 3, "reconstruction sanity: total candidate blockers across all cases/trials sums to the source's own published 3", f"got {iha_total_candidate_blockers}")

iha_report = check_gate_floor(REAL_IHA_CASES)
check(iha_report.verdict == "FAIL_STRUCTURAL", "real data: ayghri/i-have-adhd's own candidate run is correctly classified FAIL_STRUCTURAL, not just FAIL", iha_report.verdict)
check(iha_report.never_cleared_case_ids == ["agent-owned-edit"], "real data: agent-owned-edit is the one and only case flagged as never-cleared, matching the source's own 'cannot be passed by any run' finding")
check("partial-success" in iha_report.blocked_case_ids, "real data: partial-success is still reported as blocking this run (it's a real regression, just not a structural one)")
check(iha_report.excluding_never_cleared.verdict == "FAIL_IMPROVABLE", "real data: excluding the structural case, the gate is still failing but now correctly classified improvable (the real partial-success regression), matching the source's own conclusion that the gate 'still fails, on the same rule' even after excluding the unpassable case")

print(f"\n{passed} passed, {failed} failed.")
if failed:
    sys.exit(1)
