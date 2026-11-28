"""Tests for checkpoint/mandate.py -- the Mandate-revalidation-on-resume
mode this build was missing, per /builds/dsh-thread-mandate/'s own
README (itself read from /builds/policy-control-plane/
policy/mandate_store.py, itself read from deepseek-ai/
dsh-superagent-prototype's domain model). Mirrors
/builds/policy-control-plane/test_mandate_store.py's structure, adapted
from a `PolicyEvaluator` to this module's generic `revalidate_fn`
callable and from a standing tool-call authorization to a checkpointed
run's approval.

Covers, in order:
  1. The module in isolation, with a scripted baseline/stricter
     revalidate_fn (no prop-firm coupling at all).
  2. A real end-to-end section reusing evaluate_size()/PropFirmAccount
     directly, with TPT_TIERS' real '100K' tier TEMPORARILY tightened
     (and always restored, even on failure) to simulate an actual rules
     change between grant and resume -- the same discipline as every
     other mutation-based test in this project.
  3. workflow.py's own wiring (grant_approval_mandate + advance()'s
     optional mandate_store param) end to end, via real cli.py
     subprocess calls, same convention as test_checkpoint.py.

Run with: python3 test_mandate.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from checkpoint.mandate import MandateRevoked, MandateStore
from checkpoint.store import CheckpointStore
from prop_firm_position_sizing import AccountRules, evaluate_size
from prop_firm_sizing import PropFirmAccount, TPT_TIERS
from workflow import advance, create, grant_approval_mandate

FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}" + (f" -- {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(label)


def always_ok(context: dict) -> tuple[bool, str]:
    return True, "baseline: always ok"


def always_revoke(context: dict) -> tuple[bool, str]:
    return False, "stricter: contracts no longer approved"


def main() -> None:
    tmpdir = tempfile.mkdtemp()

    # === Section 1: the module in isolation ================================
    print("=== grant() records an active Mandate under the run's exact context ===")
    store = MandateStore(Path(tmpdir) / "mandates1.sqlite3")
    context = {"tier": "50K", "symbol": "ES", "contracts": 2}
    mandate_id = store.grant("run-abc", context)
    record = store.get(mandate_id)
    check("the Mandate is active", record.status == "active")
    check("the Mandate's context round-trips exactly", record.context == context)
    check("get_for_run() finds it by run_id alone, no mandate_id needed",
          store.get_for_run("run-abc").mandate_id == mandate_id)

    print("\n=== end_unit_of_work() never touches status, never consults revalidate_fn ===")
    store.end_unit_of_work(mandate_id)
    after_end = store.get(mandate_id)
    check("the Mandate is STILL active after its unit of work ends", after_end.status == "active")

    print("\n=== resume_unit_of_work() under a permissive revalidate_fn succeeds ===")
    resumed = store.resume_unit_of_work(mandate_id, always_ok)
    check("resuming keeps the Mandate active", resumed.status == "active")

    print("\n=== A stricter revalidate_fn is never checked except at an explicit resume ===")
    untouched = store.get(mandate_id)
    check("merely having a stricter revalidate_fn in hand, without calling resume with it, "
          "leaves the Mandate exactly as it was", untouched.status == "active")

    print("\n=== resume_unit_of_work() under a NOW-stricter revalidate_fn revokes the Mandate ===")
    raised_revoked = False
    try:
        store.resume_unit_of_work(mandate_id, always_revoke)
    except MandateRevoked as exc:
        raised_revoked = True
        check("the revocation reason names revalidate_fn's own stated reason",
              "contracts no longer approved" in str(exc))
    check("resume_unit_of_work() raised MandateRevoked under the stricter revalidate_fn", raised_revoked)
    revoked_record = store.get(mandate_id)
    check("the Mandate's own stored status is now 'revoked'", revoked_record.status == "revoked")
    check("the revocation reason is persisted, not just raised and lost", bool(revoked_record.revoked_reason))

    print("\n=== A revoked Mandate cannot resume again, even under a permissive revalidate_fn ===")
    raised_again = False
    try:
        store.resume_unit_of_work(mandate_id, always_ok)
    except MandateRevoked:
        raised_again = True
    check("resuming the already-revoked Mandate against a now-permissive revalidate_fn still fails -- "
          "revocation is a real, final state transition, not re-evaluated fresh every time", raised_again)

    print("\n=== withdraw() revokes unconditionally, never consulting revalidate_fn ===")
    second_mandate_id = store.grant("run-def", {"tier": "50K", "symbol": "ES", "contracts": 1})
    store.withdraw(second_mandate_id, reason="trader asked to stop")
    withdrawn_record = store.get(second_mandate_id)
    check("withdraw() sets status to 'withdrawn'", withdrawn_record.status == "withdrawn")
    check("withdraw()'s reason is stored verbatim", withdrawn_record.revoked_reason == "trader asked to stop")

    raised_on_withdrawn_resume = False
    try:
        store.resume_unit_of_work(second_mandate_id, always_ok)
    except MandateRevoked as exc:
        raised_on_withdrawn_resume = True
        check("resuming a withdrawn Mandate fails on the withdrawal check BEFORE revalidate_fn is even "
              "called -- a permissive revalidate_fn would still say ok, proving the withdrawal, not "
              "a rules result, is what blocks this", "withdrawn" in str(exc).lower())
    check("resuming a withdrawn Mandate raises MandateRevoked", raised_on_withdrawn_resume)

    print("\n=== A fresh MandateStore against the same file sees the same durable state ===")
    store.close()
    reopened = MandateStore(Path(tmpdir) / "mandates1.sqlite3")
    check("the revoked Mandate's status survived a store close/reopen",
          reopened.get(mandate_id).status == "revoked")
    check("the withdrawn Mandate's status survived a store close/reopen",
          reopened.get(second_mandate_id).status == "withdrawn")
    reopened.close()

    # === Section 2: real end-to-end against evaluate_size(), with a REAL
    # rules change simulated by temporarily tightening TPT_TIERS['100K'] ====
    print("\n=== End-to-end: real evaluate_size() behind a Mandate, revoked by a real tier tightening ===")
    e2e_store = MandateStore(Path(tmpdir) / "mandates2.sqlite3")
    e2e_context = {"tier": "100K", "symbol": "MES", "contracts": 3}

    def revalidate_from_real_rules(ctx: dict) -> tuple[bool, str]:
        account = PropFirmAccount(tier=ctx["tier"], symbol=ctx["symbol"])
        rules = AccountRules(account_equity=account.starting_balance, daily_loss_limit=account.daily_loss_limit,
                              eod_trailing_drawdown=account.eod_trailing_dd, max_contracts=account.max_contracts,
                              point_value=account.point_value)
        fresh = evaluate_size(rules, ctx["contracts"], average_daily_range_points=None)
        return fresh["size_rule"]["within_rule"], f"within_rule={fresh['size_rule']['within_rule']}"

    direct_at_grant = evaluate_size(
        AccountRules(account_equity=100000, daily_loss_limit=2500, eod_trailing_drawdown=3000,
                     max_contracts=TPT_TIERS["100K"]["max_contracts"], point_value=5.0),
        3, average_daily_range_points=None,
    )
    check("3 contracts of MES under the REAL, untouched 100K tier is within the 25% rule right now",
          direct_at_grant["size_rule"]["within_rule"] is True, detail=str(direct_at_grant["size_rule"]))

    e2e_mandate = e2e_store.grant("run-e2e", e2e_context)
    resumed_unchanged = e2e_store.resume_unit_of_work(e2e_mandate, revalidate_from_real_rules)
    check("resuming immediately, before any rules change, keeps the real Mandate active",
          resumed_unchanged.status == "active")

    original_max_contracts = TPT_TIERS["100K"]["max_contracts"]
    try:
        print("  (temporarily tightening the REAL TPT_TIERS['100K']['max_contracts'] "
              f"from {original_max_contracts} to 8 -- always restored below)")
        TPT_TIERS["100K"]["max_contracts"] = 8
        raised_e2e = False
        try:
            e2e_store.resume_unit_of_work(e2e_mandate, revalidate_from_real_rules)
        except MandateRevoked as exc:
            raised_e2e = True
            check("the e2e revocation reason names the real, now-False within_rule result",
                  "within_rule=False" in str(exc))
        check("the exact same 3-contract MES Mandate that was fine under the original 100K rules is "
              "correctly revoked on resume once TPT_TIERS['100K']['max_contracts'] really tightens "
              "from 12 to 8", raised_e2e)
    finally:
        TPT_TIERS["100K"]["max_contracts"] = original_max_contracts
    check("TPT_TIERS['100K']['max_contracts'] was restored to its original real value afterward",
          TPT_TIERS["100K"]["max_contracts"] == original_max_contracts)
    e2e_store.close()

    # === Section 3a: workflow.py's own wiring, in-process (a real rules
    # change via monkeypatch is only visible to code in THIS process --
    # see Section 3b below for the separate, subprocess-based CLI proof
    # that only needs the normal, unchanged path) ===========================
    print("\n=== workflow.py's grant_approval_mandate()/advance(mandate_store=...), in-process, real revocation ===")
    wf_store = CheckpointStore(Path(tmpdir) / "wf_runs.db")
    wf_mandate_store = MandateStore(Path(tmpdir) / "wf_mandates.db")

    run_id3 = create(wf_store, tier="100K", symbol="MES", contracts=3)
    paused3 = advance(wf_store, run_id3)
    check("the run pauses for approval exactly as before this round's change",
          paused3["status"] == "paused_for_approval", detail=str(paused3))

    wf_store.grant_approval(run_id3, note="approved for the in-process mandate test")
    granted_mandate_id = grant_approval_mandate(wf_store, wf_mandate_store, run_id3)
    check("grant_approval_mandate() returns a real mandate_id",
          wf_mandate_store.get(granted_mandate_id) is not None)
    check("the granted mandate's context matches this run's real tier/symbol/contracts",
          wf_mandate_store.get(granted_mandate_id).context == {"tier": "100K", "symbol": "MES", "contracts": 3})

    completed3 = advance(wf_store, run_id3, mandate_store=wf_mandate_store)
    check("resuming with mandate_store set, under the real UNCHANGED rules, completes normally",
          completed3["status"] == "completed", detail=str(completed3))

    run_id4 = create(wf_store, tier="100K", symbol="MES", contracts=3)
    advance(wf_store, run_id4)
    wf_store.grant_approval(run_id4, note="approved before the tier tightens")
    mandate_id4 = grant_approval_mandate(wf_store, wf_mandate_store, run_id4)

    original_max_contracts2 = TPT_TIERS["100K"]["max_contracts"]
    try:
        print(f"  (temporarily tightening the REAL TPT_TIERS['100K']['max_contracts'] from "
              f"{original_max_contracts2} to 8 -- always restored below)")
        TPT_TIERS["100K"]["max_contracts"] = 8
        revoked_result = advance(wf_store, run_id4, mandate_store=wf_mandate_store)
        check("advance() returns 'approval_revoked', not an uncaught MandateRevoked exception, once "
              "the real tier really tightened between approval and resume",
              revoked_result["status"] == "approval_revoked", detail=str(revoked_result))
        check("the returned reason names the real, now-failing 25% rule check by name",
              "25% rule" in revoked_result.get("reason", ""), detail=str(revoked_result))
    finally:
        TPT_TIERS["100K"]["max_contracts"] = original_max_contracts2
    check("TPT_TIERS['100K']['max_contracts'] was restored to its original real value afterward",
          TPT_TIERS["100K"]["max_contracts"] == original_max_contracts2)

    persisted_state4 = wf_store.load(run_id4)
    check("the checkpoint itself persists 'approval_revoked', not silently left at 'running'/'completed'",
          persisted_state4.status == "approval_revoked", detail=str(persisted_state4))
    check("finalize never actually ran -- the revoked mandate blocked it before _run_stage('finalize')",
          "finalize" not in persisted_state4.context["results"], detail=str(persisted_state4.context))

    re_resumed4 = advance(wf_store, run_id4, mandate_store=wf_mandate_store)
    check("resuming an approval_revoked run again stays revoked (the Mandate is final, same as Section 1's "
          "'a revoked Mandate cannot resume again' property)",
          re_resumed4["status"] == "approval_revoked", detail=str(re_resumed4))

    wf_store.close()
    wf_mandate_store.close()

    # === Section 3b: cli.py's --mandate-db flag, real subprocess calls,
    # the normal (unchanged-rules) path only -- proves the flag is really
    # parsed and really threaded through to advance(), not just present
    # in --help ================================================================
    print("\n=== cli.py's --mandate-db flag, real subprocess calls, the normal path ===")
    db = str(Path(tmpdir) / "cli_runs.db")
    mandate_db = str(Path(tmpdir) / "cli_mandates.db")

    def run_cli(*args: str) -> list[dict]:
        proc = subprocess.run([sys.executable, "cli.py", *args, "--db", db],
                               capture_output=True, text=True)
        return [json.loads(line) for line in proc.stdout.strip().splitlines() if line.strip()]

    out = run_cli("start", "--tier", "100K", "--symbol", "MES", "--contracts", "3")
    run_id = out[0]["run_id"]
    check("run pauses for approval exactly as before this round's change",
          out[1]["status"] == "paused_for_approval", detail=str(out[1]))

    approved = run_cli("approve", run_id, "--mandate-db", mandate_db)[0]
    check("approve --mandate-db grants a real mandate_id", bool(approved.get("mandate_id")))

    completed = run_cli("resume", run_id, "--mandate-db", mandate_db)[0]
    check("resuming with --mandate-db, under the real unchanged rules, completes normally",
          completed["status"] == "completed", detail=str(completed))

    omitted = run_cli("resume", run_id)[0]
    check("omitting --mandate-db entirely on an already-completed run is unaffected either way",
          omitted["status"] == "completed", detail=str(omitted))

    print(f"\n{'='*60}")
    if FAILURES:
        print(f"{len(FAILURES)} CHECK(S) FAILED: {FAILURES}")
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
