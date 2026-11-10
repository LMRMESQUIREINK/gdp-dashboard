"""
Structured Error Framework (SERF-lite), scoped down from the pattern in
/notes/production-grade-mcp-server-analysis.md.

An agent calling this server over MCP cannot usefully recover from a raw
Python traceback. What it can recover from is a small, fixed vocabulary:
what went wrong (code), whether retrying would help (retryable), and what
to do differently (hint).

IMPORTANT — this does NOT match the source article's wire format, and
that's a verified finding, not a guess: the article's `mcp>=1.2.0` let a
tool handler return an `ErrorData` object that rode in the JSON-RPC
`error.data` field. The `mcp` SDK actually installed in this sandbox
(2.3.0) is a different, newer API (`mcp.server.mcpserver.MCPServer`) whose
`ToolError` instead returns a normal, successful-at-the-protocol-level
`CallToolResult` with `isError=True` and the message as plain text content
— confirmed by actually running a probe server+client over real stdio
before writing this file (see the build's README). So our SERF payload is
JSON-encoded into that message string instead of a structured `data`
field. An agent still gets the full `{code, retryable, hint}` vocabulary;
it just has to parse it out of the text rather than read a dedicated
field. Stated here so nobody mistakes this for faithfully reproducing the
article's exact wire shape.

Scoped down from the source article's version: no AuthError (this server
has no auth layer — see README), no CircuitOpenError/TimeoutError_ (no
circuit breaker here — PropFirmAccount/PassSimulator are pure local
computation, nothing upstream to protect against).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from mcp.server.mcpserver.exceptions import ToolError as _MCPToolError


@dataclass
class ToolError(Exception):
    code: str
    retryable: bool = False
    hint: str | None = None
    context: dict[str, Any] | None = None

    def __str__(self) -> str:
        return f"{self.code}: {self.hint or ''}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "retryable": self.retryable,
            "hint": self.hint,
            "context": self.context or {},
        }

    def to_mcp(self) -> _MCPToolError:
        """Raise this instead: `raise err.to_mcp()`. Encodes the SERF
        payload as JSON in the message text — see module docstring for
        why this, and not a structured `error.data` field, is what the
        installed SDK version actually supports."""
        return _MCPToolError(json.dumps(self.to_dict()))


class ValidationError(ToolError):
    """Input failed Pydantic validation or an explicit domain check
    (e.g. an unknown tier). Never retryable — the same arguments will
    fail the same way; the agent must change them."""


class RateLimitError(ToolError):
    """Per-process token bucket exhausted. See ratelimit.py — this is an
    in-process bucket, not the article's Redis/Lua version; see README
    for why, and what that limitation actually means here."""

    def __init__(self, retry_after_seconds: float):
        super().__init__(
            code="rate_limited",
            retryable=True,
            hint=f"retry after {retry_after_seconds:.1f}s",
            context={"retry_after_seconds": retry_after_seconds},
        )
