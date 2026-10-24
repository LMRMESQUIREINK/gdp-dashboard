"""
run_chain — adapted from the source article's toolkit/chain.py. Lets a
caller (the model, in a real deployment; the skill compiler or a test,
in this build) write a whole dependent sequence of tool calls at once,
with "$id.field[.field...]" references resolved between steps, instead
of paying a round trip per tool. The chain stops at the first failed
check (a tool's own check failing, not a raised exception — the article's
"the chain stops at the first failed check" is about the result
contract's `ok` flag), and any outward step holds for approval exactly
like a standalone call through run_agent would.
"""
from __future__ import annotations

import re
from typing import Any

from .approval import ApprovalGate
from .registry import ToolRegistry

_REF = re.compile(r"^\$([A-Za-z0-9_]+)\.(.+)$")


def _resolve(value: Any, done: dict) -> Any:
    if isinstance(value, str):
        m = _REF.match(value)
        if m:
            step_id, path = m.groups()
            node = done[step_id]
            for part in path.split("."):
                node = node[part]
            return node
    return value


def run_chain(registry: ToolRegistry, gate: ApprovalGate, steps: list[dict]) -> dict:
    """steps: [{"id", "tool", "args"}], in order. An argument written
    "$id.files.kind" is replaced by that field from an earlier step's
    result dict."""
    done: dict[str, Any] = {}
    for step in steps:
        tool_name = step["tool"]
        args = {k: _resolve(v, done) for k, v in step.get("args", {}).items()}
        if registry.effect_of(tool_name) == "outward" and not gate.consume(tool_name, args):
            return {"ok": True, "pending": {"tool": tool_name, "args": args}, "done": done}
        out = registry.call(tool_name, **args)
        done[step["id"]] = out
        if not out.get("ok", True):
            return {"ok": False, "failed": step["id"], "done": done}
    return {"ok": True, "done": done}
