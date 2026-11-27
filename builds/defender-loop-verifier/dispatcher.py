"""Allow-list tool dispatcher: the gate between an agent's requested action
and anything that actually runs, enforced in code below the model -- never
in a prompt a clever input could talk its way around.

Pulled from the same article as verifier.py. Four checks, in order: is the
tool known, is it on the allow list, is mutation permitted if the tool
mutates, is egress permitted if the tool reaches the network (default
deny). A tool that throws must never crash the caller -- it becomes a
failure result the caller can react to.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class ToolSpec:
    name: str
    fn: Callable[..., str]
    mutating: bool = False
    egress: bool = False


@dataclass
class ToolResult:
    ok: bool
    content: str = ""
    error: str = ""

    @classmethod
    def success(cls, content: str) -> "ToolResult":
        return cls(ok=True, content=content)

    @classmethod
    def failure(cls, error: str) -> "ToolResult":
        return cls(ok=False, error=error)


class AllowListDispatcher:
    def __init__(
        self,
        tools: dict[str, ToolSpec],
        allowed_names: set[str],
        allow_mutating: bool = False,
        allow_egress: bool = False,
    ) -> None:
        self._tools = tools
        self._allowed_names = allowed_names
        self._allow_mutating = allow_mutating
        self._allow_egress = allow_egress

    def dispatch(self, name: str, **kwargs) -> ToolResult:
        tool = self._tools.get(name)
        if tool is None:
            return ToolResult.failure(f"unknown tool: {name!r}")
        if name not in self._allowed_names:
            return ToolResult.failure(f"tool not allowed: {name!r}")
        if tool.mutating and not self._allow_mutating:
            return ToolResult.failure(f"mutating tools are disabled: {name!r}")
        if tool.egress and not self._allow_egress:
            return ToolResult.failure(f"egress is disabled (default-deny): {name!r}")
        try:
            return ToolResult.success(tool.fn(**kwargs))
        except Exception as exc:  # a tool failure must never crash the caller
            return ToolResult.failure(f"{type(exc).__name__}: {exc}")
