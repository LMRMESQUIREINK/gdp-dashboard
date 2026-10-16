"""
PolicyEvaluator — implements the ACP article's own decision rules
literally:

    1. Disabled policies are discarded.
    2. A policy is applicable when its (agent, tool, operation) selector
       matches AND its condition tree evaluates to true.
    3. The highest-priority applicable policy wins.
    4. Ties resolve by effect precedence: DENY > REQUIRES_APPROVAL > ALLOW.
    5. No applicable policy results in default DENY.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .conditions import evaluate as evaluate_condition
from .model import Effect, Policy, _EFFECT_PRECEDENCE


@dataclass
class Decision:
    effect: Effect
    policy_id: Optional[str]
    policy_version: Optional[int]
    reason: str
    approval_role: Optional[str] = None


class PolicyEvaluator:
    def __init__(self, policies: list[Policy]):
        self.policies = policies

    def evaluate(self, *, agent: str, tool: str, operation: str, context: dict[str, Any]) -> Decision:
        applicable = [
            p for p in self.policies
            if p.enabled
            and p.matches_selector(agent, tool, operation)
            and evaluate_condition(p.condition, context)
        ]
        if not applicable:
            return Decision(effect=Effect.DENY, policy_id=None, policy_version=None,
                             reason="no applicable policy (default DENY)")

        applicable.sort(key=lambda p: (p.priority, _EFFECT_PRECEDENCE[p.effect]), reverse=True)
        winner = applicable[0]
        return Decision(
            effect=winner.effect, policy_id=winner.id, policy_version=winner.version,
            reason=f"policy {winner.id!r} (priority={winner.priority}) matched",
            approval_role=winner.approval_role,
        )
