"""
run_agent — the agent loop, adapted from the source article's
toolkit/loop.py. Kept close to the article's structure (model decides,
tool executes, result goes back as text, repeat) because the mechanism
is already the right size. Two deliberate changes:

1. Uses Anthropic's real tool-use message shape — matching
   /builds/trading-jarvis/jarvis_orchestrator.py's established
   ask_jarvis() convention — rather than inventing a second shape.
2. An outward tool call is never executed inline: it's held, and a
   {"pending": ...} preview comes back as the tool result, so the model
   can tell the person what's waiting and why — the same deferred
   behavior the article's post_file shows in its own single-call loop.
"""
from __future__ import annotations

import json
from typing import Any, Optional

from .approval import ApprovalGate
from .ledger import TaskCounters
from .registry import ToolRegistry


def run_agent(request: str, client: Any, model: str, registry: ToolRegistry, gate: ApprovalGate,
               system: str = "", tool_names: Optional[list[str]] = None, max_turns: int = 8,
               counters: Optional[TaskCounters] = None, max_tokens: int = 1024) -> str:
    messages: list[dict] = [{"role": "user", "content": request}]
    schemas = registry.schemas(tool_names)

    for _ in range(max_turns):
        response = client.messages.create(
            model=model, max_tokens=max_tokens, system=system, tools=schemas, messages=messages,
        )
        if counters is not None:
            counters.model_calls += 1

        if response.stop_reason != "tool_use":
            return "".join(b.text for b in response.content if b.type == "text")

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            if registry.effect_of(block.name) == "outward" and not gate.consume(block.name, block.input):
                out: dict = {"ok": True, "pending": {"tool": block.name, "args": block.input}}
                is_error = False
            else:
                try:
                    out = registry.call(block.name, **block.input)
                    is_error = False
                except Exception as exc:
                    out = {"error": str(exc)}
                    is_error = True
                if counters is not None:
                    counters.tool_calls += 1
            tool_results.append({
                "type": "tool_result", "tool_use_id": block.id,
                "content": json.dumps(out, default=str), "is_error": is_error,
            })
        messages.append({"role": "user", "content": tool_results})

    return "stopped after too many turns"
