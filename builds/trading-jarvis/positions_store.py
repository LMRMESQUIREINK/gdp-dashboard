# ═══════════════════════════════════════════════════════════════
#  ♛  RUTHLESS TRADING GOLD  ♛
#  ───────────────────────────────────────────────────────────
#  Positions store — the missing wire between risk_manager.py's
#  existing_positions parameter and an actual list of open positions
#  Data Layer: none (local JSON file)
#  Generated: 2026-09-19 (completes the Trading Jarvis build)
# ═══════════════════════════════════════════════════════════════
"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              ♛  RUTHLESS TRADING GOLD  ♛                      ║
║                                                               ║
║      Component: positions_store.py                            ║
║      Role:      Track open positions so portfolio_heat() in    ║
║                  risk_manager.py means the whole portfolio,    ║
║                  not just the trade being checked right now    ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

risk_manager.evaluate_trade() already accepts existing_positions — the
capability was always there. What's added here is a place for those
positions to actually come from, so check_risk / run_strategy.py can
pass real exposure instead of always implicitly "no other positions
open."

DESIGN PRINCIPLE — same one every other file in this system follows:
this module NEVER adds a position on its own. add_position() is only
ever called from an explicit, human-typed command (run_strategy.py
--add-position ...), recording a trade the human already made
elsewhere — never inferred from a BUY signal or a "approved" risk
check. Signals and risk checks stay suggestions; this just lets the
suggestion account for what's already on, if you choose to tell it.
"""

import json
from pathlib import Path

POSITIONS_FILE = Path("open_positions.json")


def load_positions() -> list:
    """[{"symbol": str, "shares": int, "entry": float, "stop": float}, ...]"""
    if not POSITIONS_FILE.exists():
        return []
    try:
        return json.loads(POSITIONS_FILE.read_text())
    except Exception:
        return []


def save_positions(positions: list) -> None:
    POSITIONS_FILE.write_text(json.dumps(positions, indent=2))


def positions_for_heat_check(exclude_symbol: str = None) -> list:
    """What to pass as existing_positions to evaluate_trade() — every
    open position EXCEPT the symbol currently being checked, so a
    re-check of a position you already hold doesn't double-count it."""
    positions = load_positions()
    if exclude_symbol is None:
        return positions
    return [p for p in positions if p.get("symbol") != exclude_symbol]


def add_position(symbol: str, shares: int, entry: float, stop: float) -> list:
    """Record a position you already took, outside this system. Never
    call this automatically off of a signal or an 'approved' risk check."""
    positions = load_positions()
    positions = [p for p in positions if p.get("symbol") != symbol]  # replace, don't duplicate
    positions.append({"symbol": symbol, "shares": shares, "entry": entry, "stop": stop})
    save_positions(positions)
    return positions


def remove_position(symbol: str) -> list:
    positions = [p for p in load_positions() if p.get("symbol") != symbol]
    save_positions(positions)
    return positions


if __name__ == "__main__":
    print(f"♛ Open positions ({POSITIONS_FILE}):")
    for p in load_positions():
        print(f"  {p}")
