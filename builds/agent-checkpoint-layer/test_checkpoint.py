"""
Real end-to-end tests of the checkpoint/pause/resume layer — every step
below is a genuine separate subprocess (`subprocess.run([sys.executable,
"cli.py", ...])`), not a function call inside one long-lived Python
process, because the entire point of this build is proving state
survives a process boundary. The only thing carrying state between calls
is the SQLite file on disk.

Covers, in order:
  1. A run pauses for approval exactly where expected, with the
     already-computed risk-sizing suggestion persisted and visible.
  2. Resuming without approval stays paused (never silently proceeds).
  3. Approving in one process and resuming in a different one completes
     the run, with the final numbers matching a DIRECT call to the same
     evaluate_size() function — same discipline as every other build in
     this project.
  4. Real crash recovery: a deliberate os._exit() right after a stage's
     result is computed but before its checkpoint write (see
     workflow.advance()'s crash_after_stage), then a resume from a fresh
     process that correctly recovers from the last DURABLE checkpoint —
     re-running the lost stage, not skipping it or duplicating work.
  5. Resuming an already-crashed run twice is idempotent (no duplicate
     side effects, same answer both times).

Run with:
    python3 test_checkpoint.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from checkpoint.store import CheckpointStore
from prop_firm_position_sizing import AccountRules, evaluate_size
from prop_firm_sizing import PropFirmAccount

FAILURES: list[str] = []
DB = "test_runs.db"


def check(label: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}" + (f" — {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(label)


def run_cli(*args: str) -> list[dict]:
    proc = subprocess.run([sys.executable, "cli.py", *args, "--db", DB],
                           capture_output=True, text=True)
    lines = [json.loads(line) for line in proc.stdout.strip().splitlines() if line.strip()]
    return lines


def main() -> None:
    Path(DB).unlink(missing_ok=True)
    for suffix in ("", "-wal", "-shm"):
        Path(DB + suffix).unlink(missing_ok=True)

    print("=== a run pauses for approval with the suggestion already computed ===")
    out = run_cli("start", "--tier", "50K", "--symbol", "ES", "--contracts", "2")
    run_id = out[0]["run_id"]
    paused = out[1]
    check("run paused at finalize", paused == {"status": "paused_for_approval", "run_id": run_id, "next_stage": "finalize"},
          detail=str(paused))

    status = run_cli("status", run_id)[0]
    check("risk_sizing result already computed and persisted",
          "risk_sizing" in status["context"]["results"], detail=str(status))
    check("the over-25%-rule flag actually fired (2 contracts on 50K is over the limit)",
          status["context"]["results"]["risk_sizing"]["size_rule"]["within_rule"] is False,
          detail=str(status["context"]["results"]["risk_sizing"]))

    print("\n=== resuming without approval stays paused, never silently proceeds ===")
    still_paused = run_cli("resume", run_id)[0]
    check("still paused_for_approval with no approval granted", still_paused["status"] == "paused_for_approval",
          detail=str(still_paused))

    print("\n=== approve in one process, resume in another, matches a direct evaluate_size() call ===")
    approved = run_cli("approve", run_id)[0]
    check("approval recorded", approved["approved"] is True)
    completed = run_cli("resume", run_id)[0]
    check("run completed", completed["status"] == "completed", detail=str(completed))

    account = PropFirmAccount(tier="50K", symbol="ES")
    rules = AccountRules(account_equity=account.starting_balance, daily_loss_limit=account.daily_loss_limit,
                          eod_trailing_drawdown=account.eod_trailing_dd, max_contracts=account.max_contracts,
                          point_value=account.point_value)
    direct = evaluate_size(rules, 2, average_daily_range_points=None)
    check("checkpointed risk_sizing result matches a direct evaluate_size() call",
          completed["context"]["results"]["risk_sizing"]["size_rule"] == direct["size_rule"],
          detail=f"checkpointed={completed['context']['results']['risk_sizing']['size_rule']} direct={direct['size_rule']}")
    check("finalize suggestion reflects the over-limit flag",
          "reduce size" in completed["context"]["results"]["finalize"]["suggestion"])

    print("\n=== real crash recovery: os._exit after risk_sizing, before its checkpoint write ===")
    out2 = run_cli("start", "--tier", "50K", "--symbol", "ES", "--contracts", "1",
                    "--crash-after-stage", "risk_sizing")
    run_id2 = out2[0]["run_id"]
    check("exactly one line printed before the crash (run_id only — advance() never returned)",
          len(out2) == 1, detail=str(out2))

    post_crash_status = run_cli("status", run_id2)[0]
    check("the crashed stage's checkpoint was NOT written (stage is still signal_check)",
          post_crash_status["stage"] == "signal_check", detail=str(post_crash_status))
    check("the crashed stage's result is NOT in the persisted context either",
          "risk_sizing" not in post_crash_status["context"]["results"], detail=str(post_crash_status))

    resumed = run_cli("resume", run_id2)[0]
    check("resume recovers past the crash and reaches the approval gate",
          resumed == {"status": "paused_for_approval", "run_id": run_id2, "next_stage": "finalize"},
          detail=str(resumed))

    resumed_again = run_cli("resume", run_id2)[0]
    check("resuming an already-paused run twice is idempotent (same result both times)",
          resumed_again == resumed, detail=f"first={resumed} second={resumed_again}")

    run_cli("approve", run_id2)
    finished2 = run_cli("resume", run_id2)[0]
    account1 = PropFirmAccount(tier="50K", symbol="ES")
    rules1 = AccountRules(account_equity=account1.starting_balance, daily_loss_limit=account1.daily_loss_limit,
                           eod_trailing_drawdown=account1.eod_trailing_dd, max_contracts=account1.max_contracts,
                           point_value=account1.point_value)
    direct1 = evaluate_size(rules1, 1, average_daily_range_points=None)
    check("post-crash-recovery run reaches the same final answer a direct call would, despite the crash",
          finished2["context"]["results"]["risk_sizing"]["size_rule"] == direct1["size_rule"],
          detail=f"recovered={finished2['context']['results']['risk_sizing']['size_rule']} direct={direct1['size_rule']}")

    print("\n=== the WAL has a full, ordered history of this run — not just the latest snapshot ===")
    store = CheckpointStore(DB)
    wal = store.wal_for(run_id2)
    stages_in_order = [row["stage"] for row in wal]
    # created -> signal_check (pre-crash) -> [crash loses risk_sizing's own
    # row] -> risk_sizing (post-resume) -> risk_sizing (paused before
    # finalize, recorded as last-completed) x2 (two resume calls while
    # still unapproved) -> finalize (running) -> finalize (completed).
    check("WAL records the full real sequence, including the crash gap and both pause cycles",
          stages_in_order == ["created", "signal_check", "risk_sizing", "risk_sizing",
                               "risk_sizing", "finalize", "finalize"],
          detail=str(stages_in_order))
    check("signal_check appears only ONCE in the WAL (never recomputed after the crash — "
          "only risk_sizing, the stage that actually lost its checkpoint, was)",
          stages_in_order.count("signal_check") == 1, detail=str(stages_in_order))
    store.close()

    print(f"\n{'='*60}")
    if FAILURES:
        print(f"{len(FAILURES)} CHECK(S) FAILED: {FAILURES}")
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
