# ═══════════════════════════════════════════════════════════════
#  ♛  RUTHLESS TRADING GOLD  ♛  ×  SWAMP INTELLIGENCE
#  ───────────────────────────────────────────────────────────
#  Jarvis orchestrator — Claude API reasoning core + tool dispatch
#  PATCHED (2): Swamp Intelligence decomposition is now a callable
#  tool (swamp_decompose), so Event Packets + the approval gate show
#  up inside natural-language --ask answers, not just --swamp mode.
#  Also hardens check_risk: it now VERIFIES a live BUY signal itself
#  before sizing anything, instead of trusting the system prompt to
#  ask nicely first. approval_required=True is enforced in code here,
#  matching jarvis_swamp_bridge.py's own hard-coded gate.
#  Data Layer: EODHD+FMP (via data_pipeline.py)
#  Generated: 2026-07-18 | Patched: 2026-08-03 | Patched again: 2026-08-04
#  | Pro fixes applied: see README.md
# ═══════════════════════════════════════════════════════════════
"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              ♛  RUTHLESS TRADING GOLD  ♛                      ║
║                                                               ║
║      Component: jarvis_orchestrator.py                         ║
║      Role:      Natural-language front end over the RUTHLESS   ║
║                  signal/risk pipeline + Swamp Intelligence      ║
║      Interface: text query in this build (see note below on    ║
║                  why voice is deliberately out of scope here)  ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

SETUP
    pip install -r requirements.txt   (inside the isolated .venv — see README.md)
    Windows PowerShell:  setx ANTHROPIC_API_KEY "your_key_here"
    bash:                export ANTHROPIC_API_KEY="your_key_here"
    Optional override:   set JARVIS_MODEL to pin a specific model id
                          (defaults to claude-opus-5)

WHAT'S NEW IN THIS PATCH
    A new tool, swamp_decompose, wraps jarvis_swamp_bridge.py's Task
    Tree builder. The system prompt now instructs Claude to call it
    FIRST for any per-symbol trading question, so the same Event
    Packets / approval-gate structure visible in `--swamp` mode now
    surfaces inside `--ask` answers too.

    check_risk also changed: it used to size a position for whatever
    symbol it was given, trusting the system prompt's instruction not
    to call it without a prior BUY. It now checks the signal itself
    and refuses (returns an explicit rejection, not a sizing result)
    if there isn't a live BUY — a code-level gate, not a polite ask.

WHY THIS BUILD IS TEXT-ONLY, NOT VOICE, AND NEVER PLACES ORDERS
    1. Voice-to-intent errors (misheard ticker, size, or direction) are a
       real failure mode when the next step is capital movement. Text input
       removes that entire error class; add voice as a transcription layer
       ON TOP of this text interface once you've built confidence in it,
       not as a replacement for reviewing what Claude is about to do.
    2. This file's tools stop at "signal" and "suggested size" — there is
       no execute_order tool wired in. If you build one, put a mandatory
       human confirmation step between Jarvis's suggestion and any call to
       a broker API, and treat that step as non-negotiable, not a formality
       to streamline away later.

WHAT CHANGED IN THIS BUILD (on top of the patch above)
    - MODEL was hardcoded to "claude-sonnet-4-6" with no override path.
      Now defaults to "claude-opus-5" and is overridable via the
      JARVIS_MODEL env var.
    - check_risk now passes real existing_positions (via
      positions_store.py) into evaluate_trade(), so portfolio_heat
      reflects other open positions the user has recorded, not just
      the trade being checked.
"""

import os
import json

from anthropic import Anthropic

from data_pipeline import get_recent_ohlcv, fetch_quote, fetch_ratios_ttm
from signal_generator import generate_signals, latest_signal
from risk_manager import evaluate_trade
from jarvis_swamp_bridge import decompose_objective
import positions_store as positions
import pandas as pd

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_KEY"))
MODEL = os.getenv("JARVIS_MODEL", "claude-opus-5")

DEFAULT_EQUITY = 50_000  # override per-user in a real deployment


# ───────────────────────────────────────────────────────────────
# Tool definitions exposed to Claude
# ───────────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "swamp_decompose",
        "description": (
            "Run any per-symbol trading objective through the Swamp "
            "Intelligence reasoning layer BEFORE touching signal or risk "
            "tools. Returns a Task Tree (steps, assigned agents, priority, "
            "risk score, approval_required) and Event Packets describing "
            "exactly what will happen and in what order. This does not "
            "fetch data or compute anything itself — it only plans."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string",
                           "description": "EODHD symbol format, e.g. 'AAPL.US'"},
                "risk_pct": {"type": "number", "default": 1.0},
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "check_signal",
        "description": (
            "Fetch recent price/volume data for a symbol and compute the "
            "RSI-cross + volume-confirmation signal. Returns BUY/SELL/HOLD."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string",
                           "description": "EODHD symbol format, e.g. 'AAPL.US'"},
                "rsi_threshold": {"type": "number", "default": 65},
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "check_risk",
        "description": (
            "Given a symbol, verify it currently shows a live BUY signal, "
            "then compute ATR-based stop, fixed-fractional position size at "
            "a given risk percent, and whether portfolio heat (including any "
            "other recorded open positions) allows the trade. Refuses "
            "(returns no sizing) if there is no live BUY signal — this check "
            "happens in code, not just by instruction. Never places an order."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "equity": {"type": "number", "default": DEFAULT_EQUITY},
                "risk_pct": {"type": "number", "default": 1.0},
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "check_fundamentals",
        "description": "Fetch a quick fundamentals snapshot (quote + TTM ratios) via FMP.",
        "input_schema": {
            "type": "object",
            "properties": {"symbol": {"type": "string",
                                       "description": "Bare ticker, e.g. 'AAPL'"}},
            "required": ["symbol"],
        },
    },
]


# ───────────────────────────────────────────────────────────────
# Tool execution — the actual Python behind each tool name
# ───────────────────────────────────────────────────────────────

def _run_tool(name: str, tool_input: dict) -> dict:
    if name == "swamp_decompose":
        symbol = tool_input["symbol"]
        risk_pct = tool_input.get("risk_pct", 1.0)
        tree = decompose_objective(symbol, risk_pct)
        return {
            "task_tree": tree.render(),
            "event_packets": [p.to_dict() for p in tree.event_packets()],
        }

    if name == "check_signal":
        symbol = tool_input["symbol"]
        ohlcv = get_recent_ohlcv(symbol, lookback_days=120)
        signaled = generate_signals(ohlcv, rsi_threshold=tool_input.get("rsi_threshold", 65))
        return {
            "symbol": symbol,
            "signal": latest_signal(signaled),
            "latest_rsi": round(float(signaled["rsi"].iloc[-1]), 2)
            if not pd.isna(signaled["rsi"].iloc[-1]) else None,
            "latest_close": round(float(ohlcv["adjusted_close"].iloc[-1]), 2),
            "volume_confirmed": bool(signaled["vol_confirm"].iloc[-1]),
        }

    if name == "check_risk":
        symbol = tool_input["symbol"]
        equity = tool_input.get("equity", DEFAULT_EQUITY)
        risk_pct = tool_input.get("risk_pct", 1.0)

        # ── Code-level gate (not just a system-prompt instruction) ──
        # Re-derive the signal here, independent of whatever Claude
        # believes the signal to be from an earlier tool call. This
        # mirrors jarvis_swamp_bridge.py's hard skip on Step 3 when
        # there's no BUY — approval_required stays meaningful even if
        # a future prompt edit forgets to mention the ordering rule.
        ohlcv = get_recent_ohlcv(symbol, lookback_days=120)
        signaled = generate_signals(ohlcv)
        current_signal = latest_signal(signaled)

        if current_signal != "BUY":
            return {
                "approved": False,
                "refused": True,
                "reason": (
                    f"No live BUY signal for {symbol} (current signal: "
                    f"{current_signal}). Risk/position sizing is refused "
                    "by design — approval_required governance gate, "
                    "enforced in code, not just by instruction."
                ),
                "signal": current_signal,
            }

        existing = positions.positions_for_heat_check(exclude_symbol=symbol)
        result = evaluate_trade(ohlcv, equity=equity, risk_pct=risk_pct, existing_positions=existing)
        result["refused"] = False
        return result

    if name == "check_fundamentals":
        symbol = tool_input["symbol"]
        quote = fetch_quote(symbol)
        ratios = fetch_ratios_ttm(symbol)
        return {"quote": quote, "ratios_ttm": ratios}

    return {"error": f"Unknown tool: {name}"}


# ───────────────────────────────────────────────────────────────
# Orchestration loop — Claude decides which tools to call, in what order
# ───────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are the RUTHLESS Jarvis trading assistant, running on
top of the Swamp Intelligence reasoning layer.

TOOL ORDER (follow this every time a user asks about a specific symbol):
1. Call swamp_decompose FIRST. Show the user the Task Tree and Event
   Packets it returns — this is Swamp Intelligence structuring the
   workflow before anything runs. Don't skip this even for a quick check.
2. Then call check_signal.
3. Only call check_risk if check_signal returned BUY. check_risk will
   independently re-verify this and refuse (refused: true) if it disagrees
   — if that happens, report the refusal plainly, don't argue with it or
   retry with different parameters to force a result.
4. Never call anything resembling order execution — no such tool exists.
   If a user asks you to "execute", "buy", or "sell" for real, tell them
   clearly that this build is signal-and-risk-analysis only, and that
   order execution requires a separate, explicitly human-reviewed
   integration they would need to build and approve themselves.

Present findings plainly: the Task Tree, then signal, price, RSI, and
(only if applicable) suggested size, stop, 2R target, and portfolio heat
(this trade plus any other open positions the user has recorded). Flag
clearly if portfolio heat exceeds the 5% limit. If the user hasn't
recorded any open positions, note that the heat shown only reflects this
one trade. Every sizing output is a suggestion for a human to review —
never phrase it as an instruction that has been or will be carried out.
"""


def ask_jarvis(user_query: str, max_tool_rounds: int = 6) -> str:
    """Run one user query through Claude with tool access; return final text."""
    messages = [{"role": "user", "content": user_query}]

    for _ in range(max_tool_rounds):
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            # Final text answer
            return "".join(block.text for block in response.content if block.type == "text")

        # Execute every tool_use block Claude asked for, feed results back
        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                try:
                    result = _run_tool(block.name, block.input)
                    is_error = False
                except Exception as exc:
                    result = {"error": str(exc)}
                    is_error = True
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, default=str),
                    "is_error": is_error,
                })
        messages.append({"role": "user", "content": tool_results})

    return "♛ Jarvis stopped after max tool rounds without a final answer — check tool logs."


if __name__ == "__main__":
    query = "Check AAPL for a signal, and if it's a buy, size the position at 1% risk on a $50,000 account."
    print(f"> {query}\n")
    print(ask_jarvis(query))
