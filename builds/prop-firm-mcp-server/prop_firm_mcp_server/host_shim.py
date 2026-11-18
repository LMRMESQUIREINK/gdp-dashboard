"""A minimal MCP-host-side enforcement shim.

Probing the real `mcp` SDK (2.3.0) before writing anything here showed
it does NOT enforce visibility filtering itself: `list_tools()` returns
every registered tool regardless of `_meta.ui.visibility`, and
`call_tool()` will happily run a `visibility: ["app"]` tool even when
nothing marked the caller as "the app." That's correct and expected --
the real MCP Apps spec (`specification/2026-01-26/apps.mdx`, §"Resource
Discovery" > "Visibility") states both rules as HOST requirements, not
server requirements:

  "tools/list behavior: Host MUST NOT include tools in the agent's tool
  list when their visibility does not include 'model'"

  "tools/call behavior: Host MUST reject tools/call requests from apps
  for tools that don't include 'app' in visibility"

This sandbox has no live MCP-Apps-compatible host (Claude.ai, ChatGPT,
VS Code) to test those two MUST rules against. This module is the
smallest faithful stand-in: it wraps a raw `tools/list` result and a
`tools/call` dispatch with exactly those two rules, so this server's own
test suite can prove the full contract end-to-end over a real stdio
connection, rather than trusting the spec prose alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

Caller = Literal["model", "app"]


class HostRejection(Exception):
    """Raised when a caller tries to invoke a tool its role isn't
    permitted to call, per the real spec's tools/call MUST rule."""


@dataclass
class ToolDescriptor:
    name: str
    visibility: list[str]


def _visibility(tool_meta: dict[str, Any] | None) -> list[str]:
    # § "Visibility defaults to ['model', 'app'] if omitted" -- applies
    # whether _meta is absent entirely or _meta.ui.visibility is absent.
    if not tool_meta:
        return ["model", "app"]
    ui_meta = tool_meta.get("ui") or {}
    return list(ui_meta.get("visibility", ["model", "app"]))


def filter_tools_for_model(raw_tools: list[Any]) -> list[ToolDescriptor]:
    """§ tools/list behavior: exclude any tool whose visibility doesn't
    include "model" -- what the agent's own tool-selection context sees.
    """
    out = []
    for t in raw_tools:
        vis = _visibility(getattr(t, "meta", None))
        if "model" in vis:
            out.append(ToolDescriptor(name=t.name, visibility=vis))
    return out


def all_tools_with_visibility(raw_tools: list[Any]) -> list[ToolDescriptor]:
    """What an App view is allowed to discover: every tool, each tagged
    with its real visibility -- the App itself still needs to know
    which ones it may call (those including "app")."""
    return [ToolDescriptor(name=t.name, visibility=_visibility(getattr(t, "meta", None))) for t in raw_tools]


async def call_tool_as(session, raw_tools: list[Any], caller: Caller, name: str, arguments: dict) -> Any:
    """§ tools/call behavior: reject a call if the caller's role isn't
    in the tool's declared visibility. caller="model" simulates the
    agent calling through the normal reasoning loop; caller="app"
    simulates the running MCP App calling back through the host via
    `window.parent.postMessage` (see ui_resources.py).
    """
    by_name = {t.name: t for t in raw_tools}
    if name not in by_name:
        raise HostRejection(f"no such tool: {name}")
    vis = _visibility(getattr(by_name[name], "meta", None))
    if caller not in vis:
        raise HostRejection(
            f"tool '{name}' has visibility {vis}; a '{caller}' caller is not permitted to invoke it"
        )
    return await session.call_tool(name, arguments)
