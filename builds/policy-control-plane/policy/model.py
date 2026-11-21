"""
The Policy model — matches the ACP article's own vocabulary (effect,
priority, condition, applies-to selector) so a policy written down here
reads the same way the article describes one:
"Billing Agent → Telco Billing MCP → createRefund → amount > 1000 →
REQUIRES_APPROVAL → Finance".
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class Effect(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"


# DENY beats REQUIRES_APPROVAL beats ALLOW — the article's own stated
# tie-break rule when two applicable policies share the same priority.
_EFFECT_PRECEDENCE = {Effect.DENY: 2, Effect.REQUIRES_APPROVAL: 1, Effect.ALLOW: 0}


@dataclass
class Policy:
    id: str
    name: str
    effect: Effect
    priority: int = 0
    enabled: bool = True
    version: int = 1
    agent: str = "*"       # "*" matches any agent
    tool: str = "*"
    operation: str = "*"
    condition: Optional[dict[str, Any]] = None
    approval_role: Optional[str] = None  # e.g. "Finance" — carried through, not enforced here

    def matches_selector(self, agent: str, tool: str, operation: str) -> bool:
        return ((self.agent == "*" or self.agent == agent)
                and (self.tool == "*" or self.tool == tool)
                and (self.operation == "*" or self.operation == operation))
