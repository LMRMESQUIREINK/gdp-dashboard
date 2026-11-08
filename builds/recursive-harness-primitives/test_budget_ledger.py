"""Tests for budget_ledger.py, checked against the real Harness² budget
identity (R=4k, P=3k) confirmed directly from google-research/harness2's
core/ledger.py.

Run with: python3 test_budget_ledger.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from budget_ledger import Ledger, BudgetError, expected_rollouts, expected_sessions  # noqa: E402

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


# --- The formula itself, hand-recomputed for several k values ----------
for k in (1, 2, 3, 5, 10):
    check(expected_rollouts(k) == 4 * k, f"expected_rollouts({k}) == 4*{k}", expected_rollouts(k))
    check(expected_sessions(k) == 3 * k, f"expected_sessions({k}) == 3*{k}", expected_sessions(k))
check(expected_rollouts(2) == 8 and expected_sessions(2) == 6, "the article's own worked example (k=2 -> 8 rollouts, 6 improvement stages) matches exactly")

# --- A correctly-recorded ledger passes ---------------------------------
ledger = Ledger(mode="seq", task_id="task-1", k=1)  # k=1 -> R=4, P=3
for i in range(4):
    ledger.rollout(f"rollout-{i}", cost=0.10)
for i in range(3):
    ledger.session(f"session-{i}", cost=0.05)
ledger.assert_identity()
check(True, "a ledger with exactly R=4k and P=3k, no duplicate labels, passes assert_identity()")
check(ledger.R == 4 and ledger.P == 3, "R and P read back correctly")
check(abs(ledger.cost - (4 * 0.10 + 3 * 0.05)) < 1e-9, "total cost sums rollout+session cost exactly", ledger.cost)
check(abs(ledger.rollout_cost - 0.40) < 1e-9, "rollout_cost sums only rollout entries")
check(abs(ledger.session_cost - 0.15) < 1e-9, "session_cost sums only session entries")

# --- A short ledger (missing a rollout) fails on COUNT -------------------
short = Ledger(mode="seq", task_id="task-2", k=1)  # k=1 -> want R=4
for i in range(3):  # one short of 4k=4
    short.rollout(f"rollout-{i}")
for i in range(3):
    short.session(f"session-{i}")
try:
    short.assert_identity()
    check(False, "a ledger with R=3 (want 4) raises BudgetError", "no exception")
except BudgetError as e:
    check("R=3 (want 4)" in str(e), "the raised BudgetError names the real vs. expected rollout count", str(e))

# --- THE case the real module's own docstring specifically warns about:
# a duplicate label can make the COUNT come out right while a real
# candidate silently never happened. -------------------------------------
masked = Ledger(mode="seq", task_id="task-3", k=1)  # k=1 -> want R=4, P=3
masked.rollout("base")
masked.rollout("inv-candidate")
masked.rollout("dom-candidate")
masked.rollout("dom-candidate")  # duplicate: this should have been "final", but overwrote dom-candidate's slot
for i in range(3):
    masked.session(f"session-{i}")
check(masked.R == 4, "the duplicate-masked ledger's RAW COUNT matches want_r=4 numerically", masked.R)
try:
    masked.assert_identity()
    check(False, "a ledger whose count is numerically right but hides a duplicate label still raises BudgetError", "no exception -- the exact failure mode the real module exists to catch was missed")
except BudgetError as e:
    check("DUPLICATE" in str(e) and "dom-candidate" in str(e), "assert_identity() catches the duplicate even though R==4k, and names the repeated label", str(e))

# --- Duplicate detection fires even when counts are ALSO wrong, and the
# duplicate note appears in the raised message either way -----------------
both_wrong = Ledger(mode="seq", task_id="task-4", k=1)
both_wrong.rollout("x")
both_wrong.rollout("x")  # duplicate, and only 2 total rollouts when 4*1=4 are wanted
try:
    both_wrong.assert_identity()
    check(False, "a ledger with both wrong counts AND a duplicate raises", "no exception")
except BudgetError as e:
    check("DUPLICATE" in str(e) and "R=2 (want 4)" in str(e), "the error reports both the duplicate and the count mismatch together", str(e))

# --- A duplicate SESSION label is caught the same way as a duplicate
# rollout label (the real module checks both kinds) -----------------------
dup_session = Ledger(mode="seq", task_id="task-5", k=1)
for i in range(4):
    dup_session.rollout(f"r{i}")
dup_session.session("inv")
dup_session.session("inv")  # duplicate session label
dup_session.session("dom")
try:
    dup_session.assert_identity()
    check(False, "a duplicate SESSION label also raises", "no exception")
except BudgetError as e:
    check("inv" in str(e), "duplicate session labels are caught exactly like duplicate rollout labels", str(e))

# --- to_dict() produces a sane, complete summary --------------------------
d = ledger.to_dict()
check(d["R"] == 4 and d["expected_R"] == 4, "to_dict()'s R/expected_R reflect this ledger's own k=1", d)
check(set(d["rollouts"]) == {f"rollout-{i}" for i in range(4)}, "to_dict() lists the real rollout labels")
check(d["session_attempts"] == 3, "session_attempts sums per-entry attempts (default 1 each) correctly")

print(f"\n{passed} passed, {failed} failed.")
if failed:
    sys.exit(1)
