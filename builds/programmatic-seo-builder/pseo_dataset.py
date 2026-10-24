"""
Builds the row dataset the generator turns into pages: one row per
(tier, symbol) combination from this project's own already-proven
`PropFirmAccount`/`TPT_TIERS`/`CONTRACT_SPECS` (`prop_firm_sizing.py`,
copied here unmodified, same convention every other build in this
project follows). 5 tiers x 6 symbols = 30 real rows, each with genuinely
distinct computed numbers (not the same boilerplate restated) — the
actual shape the article's own "cheat code if you build them right"
claim needs to be true.
"""

from __future__ import annotations

from dataclasses import dataclass

from prop_firm_sizing import CONTRACT_SPECS, TPT_TIERS, PropFirmAccount


@dataclass(frozen=True)
class PageRow:
    tier: str
    symbol: str
    symbol_name: str
    slug: str
    starting_balance: float
    profit_target: float
    daily_loss_limit: float
    daily_loss_in_points: float
    eod_trailing_dd: float
    fee: float
    max_contracts: int
    safe_contracts: int


def build_rows() -> list[PageRow]:
    rows: list[PageRow] = []
    for tier in TPT_TIERS:
        for symbol in CONTRACT_SPECS:
            account = PropFirmAccount(tier=tier, symbol=symbol)
            rows.append(
                PageRow(
                    tier=tier,
                    symbol=symbol,
                    symbol_name=CONTRACT_SPECS[symbol]["name"],
                    slug=f"{tier.lower()}-{symbol.lower()}",
                    starting_balance=account.starting_balance,
                    profit_target=account.profit_target,
                    daily_loss_limit=account.daily_loss_limit,
                    daily_loss_in_points=account.daily_loss_in_points,
                    eod_trailing_dd=account.eod_trailing_dd,
                    fee=account.fee,
                    max_contracts=account.max_contracts,
                    safe_contracts=account.safe_contracts,
                )
            )
    return rows


def unique_facts(row: PageRow) -> dict:
    """The data-derived facts that make this row's page different from
    every other page the template produces — fed to pseo_guard's
    duplicate-content and minimum-fact checks."""
    return {
        "tier": row.tier,
        "symbol": row.symbol,
        "starting_balance": row.starting_balance,
        "profit_target": row.profit_target,
        "daily_loss_limit": row.daily_loss_limit,
        "daily_loss_in_points": round(row.daily_loss_in_points, 1),
        "eod_trailing_dd": row.eod_trailing_dd,
        "max_contracts": row.max_contracts,
        "safe_contracts": row.safe_contracts,
    }
