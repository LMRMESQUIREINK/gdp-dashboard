# ═══════════════════════════════════════════════════════════════
#  ♛  RUTHLESS TRADING GOLD  ♛
#  ───────────────────────────────────────────────────────────
#  Jarvis orchestrator — Claude API reasoning core + tool dispatch
#  Data Layer: EODHD+FMP (via data_pipeline.py)
#  Generated: 2026-07-18 | Pro fixes applied: see README.md
# ═══════════════════════════════════════════════════════════════
"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              ♛  RUTHLESS TRADING GOLD  ♛                      ║
║                                                               ║
║      Component: jarvis_orchestrator.py                         ║
║      Role:      Natural-language front end over the RUTHLESS   ║
║                  signal/risk pipeline                          ║
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

WHAT THIS IS
    A Claude-powered "Jarvis" that takes a plain-English request like:
        "Check AAPL for a buy signal and tell me the position size at 1% risk"
    ...and lets Claude call real tools (data fetch, signal check, risk check)
    to answer it, the same tool-calling pattern the article's "MCP /
    multi-agent" framing is gesturing at.

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

WHAT CHANGED IN THIS BUILD
    - MODEL was hardcoded to "claude-sonnet-4-6" with no override path.
      Now defaults to "claude-opus-5" and is overridable via the
      JARVIS_MODEL env var.
    - check_signal / check_risk used to build a synthetic OHLCV frame
      (high = close*1.01, low = close*0.99, volume = constant). They now
      call data_pipeline.get_recent_ohlcv() for the real frame — see
      data_pipeline.py's own docstring for why that matters.
    - check_risk now passes real existing_positions (via
      positions_store.py) into evaluate_trade(), so portfolio_heat
      reflects other open positions the user has recorded, not just
      the trade being checked.
"""

import os
import json

import pandas as pd
from anthropic import Anthropic

from data_pipeline import get_recent_ohlcv, fetch_quote, fetch_ratios_ttm
from signal_generator import generate_signals, latest_signal
from risk_manager import evaluate_trade
import positions_store as positions

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_KEY"))
MODEL = os.getenv("JARVIS_MODEL", "claude-opus-5")

DEFAULT_EQUITY = 50_000  # override per-user in a real deployment


# ───────────────────────────────────────────────────────────────
# Tool definitions exposed to Claude
# ───────────────────────────────────────────────────────────────

TOOLS = [
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
            "Given a symbol showing a BUY signal, compute ATR-based stop, "
            "fixed-fractional position size at a given risk percent, and "
            "whether trade risk stays within the heat limit. Never places an order."
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
    if name == "check_signal":
        symbol = tool_input["symbol"]
        frame = get_recent_ohlcv(symbol, lookback_days=120)
        signaled = generate_signals(frame, rsi_threshold=tool_input.get("rsi_threshold", 65))
        latest_rsi = signaled["rsi"].iloc[-1]
        return {
            "symbol": symbol,
            "signal": latest_signal(signaled),
            "latest_rsi": round(float(latest_rsi), 2) if not pd.isna(latest_rsi) else None,
            "latest_close": round(float(frame["adjusted_close"].iloc[-1]), 2),
        }

    if name == "check_risk":
        symbol = tool_input["symbol"]
        equity = tool_input.get("equity", DEFAULT_EQUITY)
        risk_pct = tool_input.get("risk_pct", 1.0)
        frame = get_recent_ohlcv(symbol, lookback_days=60)
        existing = positions.positions_for_heat_check(exclude_symbol=symbol)
        result = evaluate_trade(frame, equity=equity, risk_pct=risk_pct, existing_positions=existing)
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

SYSTEM_PROMPT = """You are the RUTHLESS Jarvis trading assistant.

You have tools to check technical signals, run risk/position-sizing checks,
and pull fundamentals. You NEVER have the ability to place a trade — no
such tool exists. If a user asks you to "execute", "buy", or "sell" for
real, tell them clearly that this build is signal-and-risk-analysis only,
and that order execution requires a separate, explicitly human-reviewed
integration they would need to build and approve themselves.

Always run check_signal before check_risk for a given symbol — never
suggest a position size for a symbol that isn't currently showing a BUY
signal. Present findings plainly: signal, price, RSI, suggested size,
stop, 2R target, and portfolio heat (this trade plus any other open
positions the user has recorded). Flag clearly if portfolio heat
exceeds the 5% limit. If the user hasn't recorded any open positions,
note that the heat shown only reflects this one trade.
"""


def ask_jarvis(user_query: str, max_tool_rounds: int = 4) -> str:
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
