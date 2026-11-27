"""
Tool registry — adapted from the source article's toolkit/registry.py
(see /notes/interface-lifting-fast-computer-agents-analysis.md). Two
deliberate changes from the article's version:

1. Schemas come out in Anthropic's native tool-use shape
   ({"name", "description", "input_schema": {...}}), matching the format
   /builds/trading-jarvis/jarvis_orchestrator.py's TOOLS list already
   uses, rather than the article's OpenAI-shaped {"parameters": {...}} —
   so a tool registered here goes straight into a real
   client.messages.create(tools=...) call with no translation step.
2. One registry instance per agent, not a module-level global dict — so
   a test and the real app (or two agents in the same process) never
   collide on the same TOOLS dict, the one sharp edge the article's
   version has.
"""
from __future__ import annotations

import inspect
import typing
from dataclasses import dataclass
from typing import Any, Callable, Optional


def _json_type_for(hint: Any) -> str:
    origin = typing.get_origin(hint)
    if origin is typing.Union:
        args = [a for a in typing.get_args(hint) if a is not type(None)]
        return _json_type_for(args[0]) if len(args) == 1 else "string"
    if origin in (list, tuple, set, frozenset):
        return "array"
    if origin is dict:
        return "object"
    return {str: "string", int: "integer", float: "number", bool: "boolean",
            list: "array", dict: "object"}.get(hint, "string")


@dataclass
class ToolSpec:
    fn: Callable
    effect: str  # "local" or "outward"
    schema: dict


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolSpec] = {}

    def tool(self, effect: str = "local"):
        """Register a function as a tool. Its name, docstring and type hints
        become the schema the model reads — same mechanic as the article's
        @tool() decorator."""
        if effect not in ("local", "outward"):
            raise ValueError(f"effect must be 'local' or 'outward', got {effect!r}")

        def register(fn: Callable) -> Callable:
            self._tools[fn.__name__] = ToolSpec(fn=fn, effect=effect, schema=self._schema_for(fn))
            return fn

        return register

    def register_raw(self, name: str, fn: Callable, effect: str, schema: dict) -> None:
        """Register a tool with a hand-built schema instead of deriving one
        from type hints — needed for compiled skills (skill_compiler.py),
        whose replay function takes **kwargs and has nothing for
        typing.get_type_hints() to introspect."""
        if effect not in ("local", "outward"):
            raise ValueError(f"effect must be 'local' or 'outward', got {effect!r}")
        self._tools[name] = ToolSpec(fn=fn, effect=effect, schema=schema)

    def _schema_for(self, fn: Callable) -> dict:
        hints = typing.get_type_hints(fn)
        params = inspect.signature(fn).parameters
        props: dict[str, Any] = {}
        required: list[str] = []
        for name, p in params.items():
            props[name] = {"type": _json_type_for(hints.get(name, str))}
            if p.default is p.empty:
                required.append(name)
        return {
            "name": fn.__name__,
            "description": inspect.getdoc(fn) or "",
            "input_schema": {"type": "object", "properties": props, "required": required},
        }

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def names(self) -> list[str]:
        return list(self._tools.keys())

    def schemas(self, names: Optional[list[str]] = None) -> list[dict]:
        keys = names if names is not None else list(self._tools.keys())
        return [self._tools[n].schema for n in keys]

    def call(self, name: str, **kwargs) -> Any:
        return self._tools[name].fn(**kwargs)

    def effect_of(self, name: str) -> str:
        return self._tools[name].effect
