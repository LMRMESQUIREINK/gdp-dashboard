"""
♛ RUTHLESS TRADING GOLD — prop-firm-mcp-server

A real MCP server (stdio transport, official `mcp` SDK) exposing the
already-proven `/builds/prop-firm-sizing/` toolkit as four tools. Built
from the pattern analysis in
`/notes/production-grade-mcp-server-analysis.md` — see that file and this
build's README for exactly what was kept, what was cut, and why.

Run it:
    pip install -r requirements.txt
    python3 -m prop_firm_mcp_server.server

Point an MCP host (Claude Desktop, a test client, etc.) at this command
over stdio.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from mcp.server.mcpserver import MCPServer

from .audit import AuditLogger
from .ratelimit import Quota, RateLimiter
from .tools import (
    CompareSizesInput,
    PassProbabilityInput,
    SessionReportInput,
    SizeCheckInput,
    run_compare_sizes,
    run_pass_probability,
    run_session_report,
    run_size_check,
    run_with_guards,
)

BUILD_DIR = Path(__file__).resolve().parent.parent
AUDIT_LOG_PATH = BUILD_DIR / "audit.jsonl"

server = MCPServer("prop-firm-mcp-server", version="0.1.0")

audit = AuditLogger(AUDIT_LOG_PATH)

# Per-tool quotas. prop_firm_compare_sizes runs up to 10 Monte Carlo
# simulations per call (vs. 1 for pass_probability), so it gets a tighter
# bucket — same reasoning as the source article's research.topic override,
# scaled to this tool's actual cost instead of a hypothetical LLM call.
limiter = RateLimiter(
    default_quota=Quota(capacity=30, refill_per_minute=60),
    overrides={
        "prop_firm_compare_sizes": Quota(capacity=5, refill_per_minute=10),
    },
)


@server.tool()
def prop_firm_size_check(args: SizeCheckInput) -> dict:
    """For a TPT (Take Profit Trader) funded/evaluation futures account:
    point-risk-per-contract at a given size, the 25%-of-max-contracts rule
    check (TPT's own stated preference, not a universal rule), and an
    optional stop-room-vs-average-daily-range check. A static, start-of-day
    check — for a mid-session check that accounts for today's P&L and the
    trailing drawdown floor, use prop_firm_session_report instead."""
    return run_with_guards(limiter, audit, "prop_firm_size_check", run_size_check, args)


@server.tool()
def prop_firm_session_report(args: SessionReportInput) -> dict:
    """Full session state for a TPT funded/evaluation account: the EOD
    trailing drawdown floor (follows the HIGH-WATER MARK, not the starting
    balance — a good morning shrinks room, it doesn't grow it), the binding
    loss limit, safe contract count right now, and a SAFE/WARNING/
    CRITICAL/BREACHED status."""
    return run_with_guards(limiter, audit, "prop_firm_session_report", run_session_report, args)


@server.tool()
def prop_firm_pass_probability(args: PassProbabilityInput) -> dict:
    """Monte Carlo estimate of the probability of passing a TPT evaluation,
    given the trader's OWN recent average daily P&L and its standard
    deviation — never estimated by this tool, always supplied by the
    caller from real trading history. Also reports the drawdown-fail vs.
    time-fail split."""
    return run_with_guards(limiter, audit, "prop_firm_pass_probability", run_pass_probability, args)


@server.tool()
def prop_firm_compare_sizes(args: CompareSizesInput) -> dict:
    """Run prop_firm_pass_probability across several contract-count
    scenarios in one call, so sizing decisions are made by comparing real
    numbers side by side instead of one at a time."""
    return run_with_guards(limiter, audit, "prop_firm_compare_sizes", run_compare_sizes, args)


def main() -> None:
    asyncio.run(server.run_stdio_async())


if __name__ == "__main__":
    main()
