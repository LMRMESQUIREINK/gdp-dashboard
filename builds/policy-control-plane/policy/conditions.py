"""
A safe condition-tree evaluator for policy rules — the ACP article never
says how its "condition tree evaluates to true" is actually implemented.
Deliberately NOT Python's eval() against a string expression: a policy's
condition is data a non-engineer (an "AI Administrator" or "Security/
Compliance Officer," per the article's own role list) would plausibly
edit through a UI, and eval() against untrusted/semi-trusted text is a
real code-execution vulnerability, not a hypothetical one. Conditions
here are plain nested dicts/lists — JSON-serializable, safe to store,
safe to edit, and only ever interpreted by the fixed set of operators
below, never executed as code.

Shape:
    {"field": "amount", "op": ">", "value": 1000}
    {"all": [cond, cond, ...]}   # AND
    {"any": [cond, cond, ...]}   # OR
    {"not": cond}                # NOT
"""
from __future__ import annotations

from typing import Any

_OPS = {
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    "in": lambda a, b: a in b,
    "not_in": lambda a, b: a not in b,
}


def evaluate(condition: dict[str, Any] | None, context: dict[str, Any]) -> bool:
    """A missing condition (None) always matches — a policy with no
    condition applies to every request that already matched its
    agent/tool/operation selector."""
    if condition is None:
        return True

    if "all" in condition:
        return all(evaluate(c, context) for c in condition["all"])
    if "any" in condition:
        return any(evaluate(c, context) for c in condition["any"])
    if "not" in condition:
        return not evaluate(condition["not"], context)

    field, op, value = condition["field"], condition["op"], condition["value"]
    if op not in _OPS:
        raise ValueError(f"unsupported condition operator: {op!r}")
    if field not in context:
        # A condition referencing a field the request doesn't have never
        # matches — fail closed (the condition is simply not satisfied),
        # rather than raising and potentially crashing the whole
        # evaluation for an unrelated policy.
        return False
    return _OPS[op](context[field], value)
