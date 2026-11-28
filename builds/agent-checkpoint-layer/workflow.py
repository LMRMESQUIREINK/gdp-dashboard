"""
A minimal, real multi-stage workflow modeled on
/builds/trading-jarvis/jarvis_swamp_bridge.py's route_through_bus(): a
risk-sizing step computes a real suggestion (via the same already-proven
prop_firm_position_sizing.evaluate_size used everywhere else in this
project), and acting on it is hard-gated behind human approval — same
shape jarvis_swamp_bridge.py uses, with `approval_required=True` on its
step 3.

The difference from jarvis_swamp_bridge.py, and the actual point of this
build: there, reaching that gate with no approval raises a
`GovernanceError` and the run is simply gone — nothing is saved, nothing
can be resumed. Here, reaching the gate persists the run via
CheckpointStore and returns a "paused_for_approval" status; a completely
separate process, any amount of time later, can load that run by its UUID
and continue from exactly that point — the checkpoint/pause/resume
pattern /notes/agentic-harness-frameworks-analysis.md's source article
calls non-negotiable.
"""
from __future__ import annotations

from typing import Any, Optional

from prop_firm_position_sizing import AccountRules, evaluate_size
from prop_firm_sizing import CONTRACT_SPECS, PropFirmAccount, TPT_TIERS

from checkpoint.mandate import MandateRevoked, MandateStore
from checkpoint.store import CheckpointStore

STAGES = ["signal_check", "risk_sizing", "finalize"]
APPROVAL_REQUIRED_STAGE = "finalize"  # computing a suggestion is safe; acting on it is not


def _revalidate_against_current_rules(context: dict[str, Any]) -> tuple[bool, str]:
    """The real revalidation check `advance()` wires into
    `MandateStore.resume_unit_of_work()` -- reruns the SAME
    `evaluate_size()` call this build already uses everywhere, against
    whatever `TPT_TIERS`/`CONTRACT_SPECS` say RIGHT NOW, not the context's
    own cached `risk_sizing` result from when the Mandate was granted. A
    prop firm withdrawing a tier/symbol, or tightening a tier's
    `max_contracts`, between approval and resume both show up here
    exactly the way a Policy version no longer granting a scope does in
    `/builds/policy-control-plane/policy/mandate_store.py`.
    """
    tier, symbol, contracts = context["tier"], context["symbol"], context["contracts"]
    if tier not in TPT_TIERS:
        return False, f"tier {tier!r} no longer exists in the current rule set"
    if symbol not in CONTRACT_SPECS:
        return False, f"symbol {symbol!r} no longer exists in the current rule set"
    account = PropFirmAccount(tier=tier, symbol=symbol)
    rules = AccountRules(
        account_equity=account.starting_balance, daily_loss_limit=account.daily_loss_limit,
        eod_trailing_drawdown=account.eod_trailing_dd, max_contracts=account.max_contracts,
        point_value=account.point_value,
    )
    fresh = evaluate_size(rules, contracts, average_daily_range_points=None)
    within_rule = fresh["size_rule"]["within_rule"]
    if not within_rule:
        return False, (
            f"re-sizing {contracts} contracts of {symbol!r} under the CURRENT {tier!r} rules "
            f"no longer stays within the 25% rule"
        )
    return True, "still within the current rules"


def grant_approval_mandate(store: CheckpointStore, mandate_store: MandateStore, run_id: str) -> str:
    """Called at the moment a human approves a run -- the same moment
    `store.grant_approval()` records the boolean flag `advance()` already
    checks. Grants a real, durable Mandate recording the run's context
    (tier, symbol, contracts) AS IT STOOD at approval time, which is what
    later gets revalidated at resume, not whatever the rules happen to be
    by then."""
    state = store.load(run_id)
    if state is None:
        raise ValueError(f"no such run: {run_id}")
    context = {"tier": state.context["tier"], "symbol": state.context["symbol"],
               "contracts": state.context["contracts"]}
    return mandate_store.grant(run_id, context)


def create(store: CheckpointStore, tier: str, symbol: str, contracts: int) -> str:
    """Persist a brand-new run's initial context and return its UUID,
    with no stages run yet. Split out from advancing it so the caller
    (cli.py) always has the run_id in hand — and can print it — before
    any crash-injection point inside advance() could possibly fire."""
    run_id = store.new_run_id()
    context: dict[str, Any] = {"tier": tier, "symbol": symbol, "contracts": contracts, "results": {}}
    store.save(run_id, stage="created", status="running", context=context, note="run created")
    return run_id


def advance(
    store: CheckpointStore,
    run_id: str,
    crash_after_stage: Optional[str] = None,
    mandate_store: Optional[MandateStore] = None,
) -> dict[str, Any]:
    """Run every stage the current checkpoint hasn't completed yet, in
    order, stopping at the first one that needs approval it doesn't have.

    `crash_after_stage` is a deliberate, test-only crash-injection hook
    (see test_checkpoint.py): the process exits immediately after that
    stage's result is computed but BEFORE its checkpoint is written —
    exactly what a real `kill -9` would do — to prove a later resume
    recovers from exactly the last durably-saved stage, re-running
    nothing it already completed and losing nothing it didn't.

    `mandate_store` is strictly OPTIONAL and defaults to `None`, which
    preserves this function's exact pre-existing behavior (the boolean
    `is_approved()` check alone decides whether the approval-gated stage
    runs) -- every existing caller that omits it, including every
    pre-existing test, sees zero change. When given, and the run IS
    approved, the Mandate granted at approval time (via
    `grant_approval_mandate()`) is revalidated against the CURRENT rules
    before the gated stage runs; `MandateRevoked` becomes a real, new
    `approval_revoked` checkpoint status rather than an uncaught
    exception, since this is an ordinary, expected outcome of the rules
    having changed since approval, not a bug."""
    state = store.load(run_id)
    if state is None:
        raise ValueError(f"no such run: {run_id}")
    if state.status == "completed":
        return {"status": "completed", "run_id": run_id, "context": state.context}

    context = state.context
    start_index = STAGES.index(state.stage) + 1 if state.stage in STAGES else 0
    # Tracks the actual last-completed stage AS THE LOOP PROGRESSES, not
    # just where this particular resume started — a resume that completes
    # several stages before hitting the next pause point must record the
    # LATEST one, or the next resume after that would recompute stages it
    # already finished. (A real bug caught by test_checkpoint.py's own
    # multi-stage crash-recovery check before this comment existed.)
    last_completed = state.stage

    for stage in STAGES[start_index:]:
        if stage == APPROVAL_REQUIRED_STAGE and not store.is_approved(run_id):
            store.request_approval(run_id)
            store.save(run_id, stage=last_completed, status="paused_for_approval", context=context,
                       note=f"paused before {stage}: needs human approval")
            return {"status": "paused_for_approval", "run_id": run_id, "next_stage": stage}

        if stage == APPROVAL_REQUIRED_STAGE and mandate_store is not None:
            mandate_record = mandate_store.get_for_run(run_id)
            if mandate_record is not None:
                try:
                    mandate_store.resume_unit_of_work(mandate_record.mandate_id,
                                                        _revalidate_against_current_rules)
                except MandateRevoked as exc:
                    store.save(run_id, stage=last_completed, status="approval_revoked", context=context,
                               note=f"mandate revoked on resume: {exc}")
                    return {"status": "approval_revoked", "run_id": run_id, "next_stage": stage,
                            "reason": str(exc)}

        result = _run_stage(stage, context)
        context["results"][stage] = result

        if crash_after_stage == stage:
            import os
            os._exit(1)  # see docstring — a deliberate, test-only crash point

        last_completed = stage
        store.save(run_id, stage=stage, status="running", context=context, note=f"completed {stage}")

    store.save(run_id, stage=STAGES[-1], status="completed", context=context, note="workflow completed")
    return {"status": "completed", "run_id": run_id, "context": context}


def _run_stage(stage: str, context: dict[str, Any]) -> dict[str, Any]:
    if stage == "signal_check":
        return {"worth_sizing": context["contracts"] > 0}

    if stage == "risk_sizing":
        tier, symbol, contracts = context["tier"], context["symbol"], context["contracts"]
        if tier not in TPT_TIERS:
            raise ValueError(f"unknown tier {tier!r}, must be one of {list(TPT_TIERS)}")
        if symbol not in CONTRACT_SPECS:
            raise ValueError(f"unknown symbol {symbol!r}, must be one of {list(CONTRACT_SPECS)}")
        account = PropFirmAccount(tier=tier, symbol=symbol)
        rules = AccountRules(
            account_equity=account.starting_balance, daily_loss_limit=account.daily_loss_limit,
            eod_trailing_drawdown=account.eod_trailing_dd, max_contracts=account.max_contracts,
            point_value=account.point_value,
        )
        return evaluate_size(rules, contracts, average_daily_range_points=None)

    if stage == "finalize":
        sizing = context["results"]["risk_sizing"]
        within_rule = sizing["size_rule"]["within_rule"]
        return {"suggestion": "approved to size as requested" if within_rule else "reduce size: exceeds 25% rule"}

    raise ValueError(f"unknown stage {stage!r}")
