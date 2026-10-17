"""
Real end-to-end test of the Streamable HTTP transport + Redis-backed rate
limiter — spawns the server as a real subprocess bound to a real TCP port
with `--transport http --redis-url ...`, drives it with the `mcp` SDK's
own streamable-HTTP client over a real HTTP connection, and verifies the
rate limit is actually shared Redis state (not per-connection) by opening
TWO separate client sessions against the SAME running server process and
showing the second session inherits the first session's consumed quota.

Requires a reachable Redis (REDIS_URL, default redis://localhost:6379/0)
and a free TCP port. Skips with a clear message if Redis isn't reachable
rather than failing confusingly.

Run with:
    python3 test_http_client.py
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import time

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
HOST = "127.0.0.1"
PORT = 8765
URL = f"http://{HOST}:{PORT}/mcp"

FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}" + (f" — {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(label)


def _text(result) -> str:
    return "".join(c.text for c in result.content if hasattr(c, "text"))


async def _call_compare_sizes(session: ClientSession):
    one_scenario = [{"contracts": 1, "avg_daily_pnl": 90, "daily_pnl_std": 275}]
    return await session.call_tool(
        "prop_firm_compare_sizes",
        {"args": {"tier": "50K", "symbol": "ES", "current_balance": 50_000,
                  "high_water_mark": 50_000, "days_remaining": 11,
                  "scenarios": one_scenario}},
    )


async def main() -> None:
    try:
        import redis
        redis.Redis.from_url(REDIS_URL).ping()
    except Exception as exc:
        print(f"Redis not reachable at {REDIS_URL} ({exc}) — skipping HTTP/Redis test.")
        return

    proc = subprocess.Popen(
        [sys.executable, "-m", "prop_firm_mcp_server.server",
         "--transport", "http", "--host", HOST, "--port", str(PORT), "--redis-url", REDIS_URL],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    try:
        # Give the ASGI server a moment to bind the port.
        for _ in range(50):
            time.sleep(0.1)
            if proc.poll() is not None:
                out = proc.stdout.read()
                raise RuntimeError(f"server exited early:\n{out}")
            import socket
            with socket.socket() as s:
                s.settimeout(0.1)
                if s.connect_ex((HOST, PORT)) == 0:
                    break

        print("=== Streamable HTTP: basic tool call ===")
        async with streamable_http_client(URL) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                names = {t.name for t in tools.tools}
                check("all four tools registered over HTTP",
                      names == {"prop_firm_size_check", "prop_firm_session_report",
                                "prop_firm_pass_probability", "prop_firm_compare_sizes"},
                      detail=str(names))

                result = await _call_compare_sizes(session)
                check("compare_sizes over HTTP not an error", not result.is_error)
                via_http = json.loads(_text(result))
                check("compare_sizes over HTTP matches previously-verified figure (1.7%)",
                      abs(via_http["comparison"][0]["pass_probability"] - 0.017) < 0.01,
                      detail=str(via_http))

        print("\n=== Redis-backed rate limit is SHARED across separate client sessions ===")
        # prop_firm_compare_sizes bucket capacity is 5. Reset it (the basic
        # call above already spent one token from it), drain it fresh from
        # session A, then open a brand-new session B (a fresh HTTP
        # connection) and show it's still rate-limited — proving the bucket
        # lives in Redis, not in per-connection server memory.
        import redis as _redis
        _redis.Redis.from_url(REDIS_URL).delete("prop_firm_mcp:ratelimit:prop_firm_compare_sizes")
        drained_in_a = 0
        async with streamable_http_client(URL) as (read, write):
            async with ClientSession(read, write) as session_a:
                await session_a.initialize()
                for _ in range(5):
                    r = await _call_compare_sizes(session_a)
                    if not r.is_error:
                        drained_in_a += 1
        check("session A could spend the full bucket of 5", drained_in_a == 5,
              detail=f"spent {drained_in_a}/5")

        async with streamable_http_client(URL) as (read, write):
            async with ClientSession(read, write) as session_b:
                await session_b.initialize()
                r = await _call_compare_sizes(session_b)
                text = _text(r) if r.is_error else ""
                check("a fresh session B is still rate-limited (bucket shared via Redis)",
                      r.is_error, detail="session B call was NOT an error — bucket was per-connection, not shared")
                if r.is_error:
                    check("rate-limit error carries SERF code", '"code": "rate_limited"' in text, detail=text)

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    print(f"\n{'='*60}")
    if FAILURES:
        print(f"{len(FAILURES)} CHECK(S) FAILED: {FAILURES}")
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    asyncio.run(main())
