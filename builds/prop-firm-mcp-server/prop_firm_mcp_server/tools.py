"""
The four MCP tools this server exposes. Each wraps an already-proven
function/class from the sibling `prop_firm_sizing.py` /
`prop_firm_position_sizing.py` / `prop_pass_simulator.py` files (copied
unmodified from `/builds/prop-firm-sizing/`) — no sizing math is
reimplemented here, only MCP plumbing around it.

This is the "atomic tool" tier only from the source article's three-level
hierarchy (atomic/composed/workflow) — see README for why a composed or
workflow tier isn't warranted at this scale (four independent, already-
narrow calculations with no natural fan-out between them).
"""
from __future__ import annotations

import time
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from prop_firm_sizing import PropFirmAccount, SessionState, TPT_TIERS, CONTRACT_SPECS
from prop_firm_position_sizing import AccountRules, evaluate_size
from prop_pass_simulator import PassSimulator

from .audit import AuditLogger
from .errors import RateLimitError, ValidationError
from .ratelimit import RateLimiter

TIERS = list(TPT_TIERS.keys())
SYMBOLS = list(CONTRACT_SPECS.keys())


def _build_account(tier: str, symbol: str) -> PropFirmAccount:
    if tier not in TPT_TIERS:
        raise ValidationError(
            code="unknown_tier", hint=f"tier must be one of {TIERS}", context={"tier": tier}
        )
    if symbol not in CONTRACT_SPECS:
        raise ValidationError(
            code="unknown_symbol",
            hint=f"symbol must be one of {SYMBOLS}",
            context={"symbol": symbol},
        )
    return PropFirmAccount(tier=tier, symbol=symbol)


# ── Tool 1: prop_firm_size_check ────────────────────────────────────────

class SizeCheckInput(BaseModel):
    tier: str = Field(..., description=f"TPT account tier: one of {TIERS}")
    symbol: str = Field("ES", description=f"Futures contract: one of {SYMBOLS}")
    contracts: int = Field(..., ge=1, description="Contract count to check")
    average_daily_range_points: Optional[float] = Field(
        None, description="Optional current ADR in points, for the stop-room check"
    )


def run_size_check(args: SizeCheckInput) -> dict:
    account = _build_account(args.tier, args.symbol)
    rules = AccountRules(
        account_equity=account.starting_balance,
        daily_loss_limit=account.daily_loss_limit,
        eod_trailing_drawdown=account.eod_trailing_dd,
        max_contracts=account.max_contracts,
        point_value=account.point_value,
    )
    return evaluate_size(rules, args.contracts, average_daily_range_points=args.average_daily_range_points)


# ── Tool 2: prop_firm_session_report ────────────────────────────────────

class SessionReportInput(BaseModel):
    tier: str = Field(..., description=f"TPT account tier: one of {TIERS}")
    symbol: str = Field("ES", description=f"Futures contract: one of {SYMBOLS}")
    intraday_pnl: float = Field(0.0, description="Today's P&L so far, negative if down")
    high_water_mark: Optional[float] = Field(
        None, description="Highest balance today. Omit to derive from intraday_pnl."
    )
    session_start_balance: Optional[float] = Field(
        None, description="Balance at start of today's session. Omit to use the account's starting balance."
    )


def run_session_report(args: SessionReportInput) -> dict:
    account = _build_account(args.tier, args.symbol)
    session_start_balance = args.session_start_balance or account.starting_balance
    high_water_mark = args.high_water_mark or (session_start_balance + max(0.0, args.intraday_pnl))
    state = SessionState(
        account=account,
        session_start_balance=session_start_balance,
        high_water_mark=high_water_mark,
        intraday_pnl=args.intraday_pnl,
    )
    return {
        "tier": args.tier, "symbol": args.symbol,
        "current_balance": round(state.current_balance, 2),
        "trailing_dd_floor": round(state.trailing_dd_floor, 2),
        "gap_to_trailing_floor": round(state.gap_to_trailing_floor, 2),
        "remaining_daily_loss": round(state.remaining_daily_loss, 2),
        "binding_loss_limit": round(state.binding_loss_limit, 2),
        "safe_contracts": state.safe_contracts,
        "effective_points_per_contract": round(state.effective_points_per_contract, 2),
        "warning_level": state.warning_level(),
    }


# ── Tool 3: prop_firm_pass_probability ──────────────────────────────────

class PassProbabilityInput(BaseModel):
    tier: str = Field(..., description=f"TPT account tier: one of {TIERS}")
    symbol: str = Field("ES", description=f"Futures contract: one of {SYMBOLS}")
    current_balance: float
    high_water_mark: float
    days_remaining: int = Field(..., ge=1)
    avg_daily_pnl: float = Field(..., description="Trader's own recent mean daily P&L in dollars — never estimated by this tool")
    daily_pnl_std: float = Field(..., gt=0, description="Trader's own recent daily P&L standard deviation in dollars")


def run_pass_probability(args: PassProbabilityInput) -> dict:
    account = _build_account(args.tier, args.symbol)
    sim = PassSimulator(
        account=account,
        current_balance=args.current_balance,
        high_water_mark=args.high_water_mark,
        days_remaining=args.days_remaining,
        avg_daily_pnl=args.avg_daily_pnl,
        daily_pnl_std=args.daily_pnl_std,
    )
    sim.run()
    return {
        "tier": args.tier, "symbol": args.symbol,
        "pass_probability": round(sim.pass_probability, 4),
        "fail_dd_probability": round(sim.fail_dd_probability, 4),
        "fail_time_probability": round(sim.fail_time_probability, 4),
        "median_days_to_pass": (
            round(sim.median_days_to_pass, 1) if sim.median_days_to_pass == sim.median_days_to_pass else None
        ),
        "pct5_final_balance": round(sim.pct5_final_balance, 2),
        "pct95_final_balance": round(sim.pct95_final_balance, 2),
        "simulations": sim.simulations,
    }


# ── Tool 4: prop_firm_compare_sizes ─────────────────────────────────────

class SizeScenario(BaseModel):
    contracts: int = Field(..., ge=1)
    avg_daily_pnl: float
    daily_pnl_std: float = Field(..., gt=0)


class CompareSizesInput(BaseModel):
    tier: str = Field(..., description=f"TPT account tier: one of {TIERS}")
    symbol: str = Field("ES", description=f"Futures contract: one of {SYMBOLS}")
    current_balance: float
    high_water_mark: float
    days_remaining: int = Field(..., ge=1)
    scenarios: list[SizeScenario] = Field(
        ..., min_length=1, max_length=10,
        description="Contract-count scenarios to compare, each with its own avg/std daily P&L",
    )

    @field_validator("scenarios")
    @classmethod
    def unique_contract_counts(cls, v: list[SizeScenario]) -> list[SizeScenario]:
        counts = [s.contracts for s in v]
        if len(counts) != len(set(counts)):
            raise ValueError("each scenario must use a distinct contract count")
        return v


def run_compare_sizes(args: CompareSizesInput) -> dict:
    account = _build_account(args.tier, args.symbol)
    rows = []
    for scenario in args.scenarios:
        sim = PassSimulator(
            account=account,
            current_balance=args.current_balance,
            high_water_mark=args.high_water_mark,
            days_remaining=args.days_remaining,
            avg_daily_pnl=scenario.avg_daily_pnl,
            daily_pnl_std=scenario.daily_pnl_std,
            simulations=20_000,
        )
        sim.run()
        rows.append({
            "contracts": scenario.contracts,
            "pass_probability": round(sim.pass_probability, 4),
            "fail_dd_probability": round(sim.fail_dd_probability, 4),
            "at_25pct_rule": scenario.contracts == account.safe_contracts,
        })
    return {"tier": args.tier, "symbol": args.symbol, "comparison": rows}


# ── Shared execution wrapper: rate limit + audit, for every tool ───────

def run_with_guards(limiter: RateLimiter, audit: AuditLogger, tool_name: str, fn, args: BaseModel) -> dict:
    """Every tool call goes through this: rate limit first (cheapest check,
    reject before doing any work), then execute, then audit — success or
    failure, same as the source article's dispatch-pipeline ordering
    reasoning (validate/authorize before paying for work; log regardless
    of outcome)."""
    started = time.monotonic()
    try:
        limiter.acquire(tool_name)
    except RateLimitError as exc:
        audit.record(tool=tool_name, arguments=args.model_dump(), duration_ms=0.0,
                      status="error", error_code=exc.code)
        raise exc.to_mcp()

    try:
        result = fn(args)
    except ValidationError as exc:
        audit.record(tool=tool_name, arguments=args.model_dump(),
                      duration_ms=(time.monotonic() - started) * 1000,
                      status="error", error_code=exc.code)
        raise exc.to_mcp()

    audit.record(tool=tool_name, arguments=args.model_dump(),
                  duration_ms=(time.monotonic() - started) * 1000, status="ok")
    return result
