"""
Rate limiting for prop-firm-mcp-server — two implementations behind one
interface, selected by whether a Redis client is wired in.

HISTORY, stated rather than hidden: the first version of this file only
had `TokenBucket` (in-process, one Python dict in memory) with a comment
explaining that the source article's Redis+Lua-script version was
overkill for a single stdio subprocess per client, and naming the real
trigger condition for needing it: serving multiple concurrent clients
over Streamable HTTP, where an in-process counter lets a caller N-x their
quota by hitting different server processes behind a load balancer.

That trigger condition is now real — `server.py` can run over Streamable
HTTP, serving more than one client from one process (or, behind a real
deployment, more than one process). So `RedisTokenBucket` below is now
built for real, using the same atomic refill+acquire-in-one-round-trip
Lua script pattern the article describes, not a simplified imitation of
it. `TokenBucket` stays as the fallback for stdio (still exactly one
replica per client, so it's still correct and still simpler) and for
when no Redis is configured for the HTTP case either.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from .errors import RateLimitError

# KEYS[1] = bucket key. ARGV = [capacity, refill_per_second, cost, now_seconds].
# Returns {allowed (0/1), tokens_remaining_or_retry_after_seconds}.
# Runs as one atomic Lua script server-side so refill+check+decrement can't
# race across concurrent callers hitting the same bucket — the actual reason
# the article reaches for Redis+Lua instead of a plain INCR.
_LUA_TOKEN_BUCKET = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_per_s = tonumber(ARGV[2])
local cost = tonumber(ARGV[3])
local now = tonumber(ARGV[4])

local data = redis.call('HMGET', key, 'tokens', 'ts')
local tokens = tonumber(data[1])
local ts = tonumber(data[2])
if tokens == nil then
    tokens = capacity
    ts = now
end

local elapsed = math.max(0, now - ts)
tokens = math.min(capacity, tokens + elapsed * refill_per_s)

if tokens >= cost then
    tokens = tokens - cost
    redis.call('HMSET', key, 'tokens', tostring(tokens), 'ts', tostring(now))
    redis.call('EXPIRE', key, 3600)
    return {1, tostring(tokens)}
else
    local deficit = cost - tokens
    local retry_after = deficit / refill_per_s
    redis.call('HMSET', key, 'tokens', tostring(tokens), 'ts', tostring(now))
    redis.call('EXPIRE', key, 3600)
    return {0, tostring(retry_after)}
end
"""


@dataclass
class Quota:
    capacity: int
    refill_per_minute: int


class TokenBucket:
    """In-process fallback. Correct for exactly one replica per client
    (stdio transport) or for a single-process HTTP deployment with no
    Redis configured — wrong the moment there's more than one process
    sharing a quota, which is exactly why RateLimiter picks RedisTokenBucket
    instead whenever a Redis client is available."""

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


class RedisTokenBucket:
    """Shared-state token bucket backed by Redis, atomic via a server-side
    Lua script. Correct across multiple server processes/replicas sharing
    the same quota per tool — the case the source article's version
    actually solves, and the case this server didn't have until it could
    also run over Streamable HTTP."""

    def __init__(self, redis_client, script, key: str, quota: Quota):
        self._redis = redis_client
        self._script = script
        self._key = key
        self.capacity = quota.capacity
        self.refill_per_s = quota.refill_per_minute / 60.0

    def acquire(self, cost: int = 1) -> None:
        allowed, value = self._script(
            keys=[self._key],
            args=[self.capacity, self.refill_per_s, cost, time.time()],
        )
        if int(allowed) == 1:
            return
        raise RateLimitError(retry_after_seconds=float(value))


class RateLimiter:
    """One bucket per tool name. Backed by Redis when a (already-pinged)
    redis client is supplied; otherwise falls back to the in-process
    TokenBucket, lazily created on first call per tool."""

    def __init__(self, default_quota: Quota, overrides: dict[str, Quota] | None = None,
                 redis_client=None, key_prefix: str = "prop_firm_mcp:ratelimit"):
        self.default_quota = default_quota
        self.overrides = overrides or {}
        self.redis_client = redis_client
        self.key_prefix = key_prefix
        self._script = redis_client.register_script(_LUA_TOKEN_BUCKET) if redis_client else None
        self._local_buckets: dict[str, TokenBucket] = {}

    def acquire(self, tool: str, cost: int = 1) -> None:
        quota = self.overrides.get(tool, self.default_quota)
        if self.redis_client is not None:
            bucket = RedisTokenBucket(self.redis_client, self._script, f"{self.key_prefix}:{tool}", quota)
            bucket.acquire(cost)
            return
        bucket = self._local_buckets.get(tool)
        if bucket is None:
            bucket = TokenBucket(quota)
            self._local_buckets[tool] = bucket
        bucket.acquire(cost)
