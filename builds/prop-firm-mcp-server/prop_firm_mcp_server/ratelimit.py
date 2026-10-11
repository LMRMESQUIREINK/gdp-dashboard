"""
In-process token bucket rate limiter — scoped down from the source
article's Redis-token-bucket-via-Lua-script pattern (see
/notes/production-grade-mcp-server-analysis.md).

HONEST LIMITATION, stated rather than hidden: this bucket lives in one
Python process's memory. The article's version is correct precisely
because it solves a problem this server doesn't have — multiple replicas
behind a load balancer, where an in-process counter lets a caller N-x
their quota by hitting different replicas. This server runs as a single
stdio subprocess per client (that's what MCP stdio transport means), so
there is exactly one replica by construction, and the article's reason
for needing Redis doesn't apply. If this server is ever reworked to serve
multiple concurrent clients over Streamable HTTP, this limiter stops being
sufficient and the Redis/Lua version becomes necessary again — not a
hypothetical, a real trigger condition worth remembering.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from .errors import RateLimitError


@dataclass
class Quota:
    capacity: int
    refill_per_minute: int


class TokenBucket:
    def __init__(self, quota: Quota):
        self.capacity = quota.capacity
        self.refill_per_s = quota.refill_per_minute / 60.0
        self.tokens = float(quota.capacity)
        self.last_refill = time.monotonic()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_s)
        self.last_refill = now

    def acquire(self, cost: int = 1) -> None:
        self._refill()
        if self.tokens >= cost:
            self.tokens -= cost
            return
        deficit = cost - self.tokens
        retry_after = deficit / self.refill_per_s
        raise RateLimitError(retry_after_seconds=retry_after)


class RateLimiter:
    """One bucket per tool name, lazily created on first call."""

    def __init__(self, default_quota: Quota, overrides: dict[str, Quota] | None = None):
        self.default_quota = default_quota
        self.overrides = overrides or {}
        self._buckets: dict[str, TokenBucket] = {}

    def acquire(self, tool: str, cost: int = 1) -> None:
        bucket = self._buckets.get(tool)
        if bucket is None:
            bucket = TokenBucket(self.overrides.get(tool, self.default_quota))
            self._buckets[tool] = bucket
        bucket.acquire(cost)
