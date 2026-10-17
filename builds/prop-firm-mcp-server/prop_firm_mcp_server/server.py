"""
♛ RUTHLESS TRADING GOLD — prop-firm-mcp-server

A real MCP server (official `mcp` SDK) exposing the already-proven
`/builds/prop-firm-sizing/` toolkit as four tools. Built from the pattern
analysis in `/notes/production-grade-mcp-server-analysis.md` — see that
file and this build's README for exactly what was kept, what was cut,
and why.

Two transports, picked with `--transport`:
  stdio (default) — one subprocess per client. Rate limiting stays
      in-process (TokenBucket); there's exactly one replica per client by
      construction, so there's nothing for Redis to protect against.
  http — Streamable HTTP, serving multiple concurrent clients from one
      process (or more than one process behind a real deployment). This
      is the real trigger condition `ratelimit.py` names for needing
      Redis-backed rate limiting, so http mode prefers Redis when it's
      reachable and only falls back to the (now per-process, no longer
      correct across processes) in-process bucket with an explicit
      warning if it isn't.

Run it:
    pip install -r requirements.txt
    python3 -m prop_firm_mcp_server.server                     # stdio
    python3 -m prop_firm_mcp_server.server --transport http    # HTTP, port 8000
    python3 -m prop_firm_mcp_server.server --transport http --redis-url redis://localhost:6379/0

Point an MCP host (Claude Desktop, a test client, etc.) at this command.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
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


def _make_redis_client(redis_url: str | None):
    """Returns a pinged, working redis client, or None (with a printed
    reason) if no URL was given or the ping failed. Never raises — a
    Redis outage degrades rate-limit correctness under multiple
    processes, it shouldn't take the whole server down."""
    if not redis_url:
        return None
    try:
        import redis
    except ImportError:
        print("redis package not installed (pip install redis) — "
              "falling back to in-process rate limiting.", file=sys.stderr)
        return None
    client = redis.Redis.from_url(redis_url)
    try:
        client.ping()
    except redis.RedisError as exc:
        print(f"Could not reach Redis at {redis_url} ({exc}) — "
              "falling back to in-process rate limiting.", file=sys.stderr)
        return None
    return client


def _build_limiter(redis_url: str | None) -> RateLimiter:
    # Per-tool quotas. prop_firm_compare_sizes runs up to 10 Monte Carlo
    # simulations per call (vs. 1 for pass_probability), so it gets a
    # tighter bucket — same reasoning as the source article's
    # research.topic override, scaled to this tool's actual cost instead
    # of a hypothetical LLM call.
    return RateLimiter(
        default_quota=Quota(capacity=30, refill_per_minute=60),
        overrides={
            "prop_firm_compare_sizes": Quota(capacity=5, refill_per_minute=10),
        },
        redis_client=_make_redis_client(redis_url),
    )


limiter = _build_limiter(os.environ.get("REDIS_URL"))


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


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="prop_firm_mcp_server")
    parser.add_argument("--transport", choices=["stdio", "http"], default="stdio")
    parser.add_argument("--host", default="127.0.0.1", help="http transport only")
    parser.add_argument("--port", type=int, default=8000, help="http transport only")
    parser.add_argument(
        "--redis-url", default=os.environ.get("REDIS_URL"),
        help="e.g. redis://localhost:6379/0 — defaults to $REDIS_URL. "
             "Only matters for http transport; stdio's in-process limiter "
             "is already correct (one replica per client) and Redis would "
             "add nothing.",
    )
    return parser.parse_args(argv)


def main() -> None:
    global limiter
    args = _parse_args()

    if args.transport == "http":
        limiter = _build_limiter(args.redis_url)
        asyncio.run(server.run_streamable_http_async(host=args.host, port=args.port))
    else:
        # stdio: in-process limiter is already correct for one replica per
        # client, so only honor --redis-url if the caller explicitly wants
        # it (e.g. testing the Redis path without starting an HTTP server).
        if args.redis_url:
            limiter = _build_limiter(args.redis_url)
        asyncio.run(server.run_stdio_async())


if __name__ == "__main__":
    main()
