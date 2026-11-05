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

from checkpoint.store import CheckpointStore

STAGES = ["signal_check", "risk_sizing", "finalize"]
APPROVAL_REQUIRED_STAGE = "finalize"  # computing a suggestion is safe; acting on it is not


def create(store: CheckpointStore, tier: str, symbol: str, contracts: int) -> str:
    """Persist a brand-new run's initial context and return its UUID,
    with no stages run yet. Split out from advancing it so the caller
    (cli.py) always has the run_id in hand — and can print it — before
    any crash-injection point inside advance() could possibly fire."""
    run_id = store.new_run_id()
    context: dict[str, Any] = {"tier": tier, "symbol": symbol, "contracts": contracts, "results": {}}
    store.save(run_id, stage="created", status="running", context=context, note="run created")
    return run_id


def advance(store: CheckpointStore, run_id: str, crash_after_stage: Optional[str] = None) -> dict[str, Any]:
    """Run every stage the current checkpoint hasn't completed yet, in
    order, stopping at the first one that needs approval it doesn't have.

    `crash_after_stage` is a deliberate, test-only crash-injection hook
    (see test_checkpoint.py): the process exits immediately after that
    stage's result is computed but BEFORE its checkpoint is written —
    exactly what a real `kill -9` would do — to prove a later resume
    recovers from exactly the last durably-saved stage, re-running
    nothing it already completed and losing nothing it didn't."""
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
