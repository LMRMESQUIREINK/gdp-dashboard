"""
Structured audit log — newline-delimited JSON, one line per tool call.
Directly adapted from the source article's pattern
(/notes/production-grade-mcp-server-analysis.md): never log raw arguments
(hash them instead), always log outcome and duration, make every line
machine-parseable.

Scoped down: no `trace_id`/`delegator`/`tenant` fields — this server has
no distributed tracing, no multi-agent delegation chain, and no
multi-tenancy (see README for why each was cut). What's kept — tool name,
args hash, duration, status, error code — is exactly what you'd want to
answer "what did this tool get called with and did it work" for a
single-user local tool, which is the actual job here.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class AuditLogger:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(
        self,
        *,
        tool: str,
        arguments: dict[str, Any],
        duration_ms: float,
        status: str,
        error_code: str | None = None,
    ) -> None:
        event = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "tool": tool,
            "args_hash": _hash_args(arguments),
            "duration_ms": round(duration_ms, 3),
            "status": status,
            "error_code": error_code,
        }
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, default=str) + "\n")


def _hash_args(arguments: dict[str, Any]) -> str:
    payload = json.dumps(arguments, sort_keys=True, default=str).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()
