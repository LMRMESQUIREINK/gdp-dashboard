"""
Skill compiler — adapted from the source article's skill-compiler idea: a
task that worked once becomes a new tool the model can call, so the next
run is one call instead of a re-explored sequence. This is the piece that
answers the article's fifth named cost of the screen loop ("nothing is
remembered — every run explores the program again").

Scope, stated plainly rather than silently narrowed: the article compiles
a screen-agent run — concrete UI-tree locators and literal values get
turned into typed placeholders. There is no screen loop in this toolkit
to compile from (see this build's README for why — no GUI programs exist
in this sandbox to drive one against), so this version compiles from a
recorded run_chain-shaped `steps` list instead: a chain that already ran
successfully once, with specific literal argument values named as the
ones that should become parameters next time. The mechanism — turn one
successful concrete run into a reusable, parametrized tool — is identical;
what gets parametrized is chain arguments instead of UI locators, because
that's the layer this toolkit actually operates at.
"""
from __future__ import annotations

from typing import Any

from .approval import ApprovalGate
from .chain import run_chain
from .registry import ToolRegistry


def _substitute(value: Any, params: dict[Any, str]) -> Any:
    if isinstance(value, dict):
        return {k: _substitute(v, params) for k, v in value.items()}
    if isinstance(value, list):
        return [_substitute(v, params) for v in value]
    for literal, name in params.items():
        # type(...) is type(...) guards against Python's bool/int equality
        # (True == 1) matching the wrong recorded literal.
        if type(value) is type(literal) and value == literal:
            return "{" + name + "}"
    return value


def _fill(value: Any, kwargs: dict[str, Any]) -> Any:
    if isinstance(value, dict):
        return {k: _fill(v, kwargs) for k, v in value.items()}
    if isinstance(value, list):
        return [_fill(v, kwargs) for v in value]
    if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
        name = value[1:-1]
        if name in kwargs:
            return kwargs[name]
    return value


def compile_skill(registry: ToolRegistry, gate: ApprovalGate, name: str,
                   steps: list[dict], params: dict[Any, str], effect: str = "local") -> None:
    """Record `steps` (a run_chain-shaped list that already ran
    successfully once) as a new tool called `name`, registered into
    `registry`. `params` maps a literal value seen in `steps` to the
    parameter name it should become — e.g. {"50K": "tier", 1: "contracts"}.
    The compiled tool takes those parameter names as keyword arguments and
    replays the same chain with them substituted back in. Each step inside
    the replayed chain keeps its OWN registered effect (local/outward) —
    `effect` here only labels the compiled tool itself, for when it's
    called from inside a further run_agent/run_chain."""
    templated_steps = [{**step, "args": _substitute(step.get("args", {}), params)} for step in steps]
    param_names = list(dict.fromkeys(params.values()))

    def compiled_tool(**kwargs: Any) -> dict:
        missing = [p for p in param_names if p not in kwargs]
        if missing:
            raise TypeError(f"{name} missing required argument(s): {missing}")
        filled_steps = [{**step, "args": _fill(step["args"], kwargs)} for step in templated_steps]
        return run_chain(registry, gate, filled_steps)

    compiled_tool.__name__ = name
    doc = f"Compiled skill, replaying a {len(steps)}-step chain recorded once. Parameters: {', '.join(param_names)}."
    compiled_tool.__doc__ = doc

    registry.register_raw(
        name=name, fn=compiled_tool, effect=effect,
        schema={
            "name": name,
            "description": doc,
            "input_schema": {
                "type": "object",
                "properties": {p: {"type": "string"} for p in param_names},
                "required": param_names,
            },
        },
    )
