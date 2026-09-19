# ═══════════════════════════════════════════════════════════════
#  ♛  RUTHLESS TRADING GOLD  ♛  ×  SWAMP INTELLIGENCE
#  ───────────────────────────────────────────────────────────
#  Generic reasoning/coordination engine — implements the Swamp
#  Intelligence Core Brain Spec (decompose → assign → sequence →
#  event-structure → govern). Domain-agnostic: Jarvis is just one
#  tenant that plugs in via jarvis_swamp_bridge.py.
#  Data Layer: N/A (reasoning layer only, no data fetch)
#  Generated: 2026-07-28
# ═══════════════════════════════════════════════════════════════
"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              ♛  SWAMP INTELLIGENCE — CORE  ♛                  ║
║                                                               ║
║      Role: Multi-Agent Reasoning & Coordination Engine         ║
║      Layer: Intelligence (above execution, below Council)      ║
║      Function: objectives -> structured, routable workflows    ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

Core directive (non-negotiable, mirrors 01_brain/swamp_intelligence_core.md):

    Swamp Intelligence does NOT execute tasks.
    It THINKS, STRUCTURES, and ROUTES.

This module never calls out to a broker, an order API, or anything
that moves money. It only produces TaskTree / ExecutionFlow / EventPacket
objects. Whatever consumes them (a bridge, an orchestrator, a human)
is responsible for execution and remains bound by its own safety rules.

NOTE ON ActivationGate — checked against actual usage in this build:
nothing currently calls should_activate(). It needs step_count as an
input, which is only known once a TaskTree already exists, so it can't
gate the decision to decompose in the first place (only whether to use
a tree once built). jarvis_orchestrator.py's system prompt instead
routes every symbol check through swamp_decompose unconditionally. Left
as-is here rather than force a wiring decision that wasn't asked for —
see /notes/trading-jarvis-analysis.md. Checked against the actual Brain
Spec text once it became available: Trading Jarvis only ever decomposes
one objective shape (a single-symbol check, always the same 4 steps),
so there's no varying complexity for this gate to distinguish between —
its dormancy here isn't a missed wiring step, it's that this domain
doesn't have the objective variety the spec's originating (broader,
business/funnel-agent) domain was built for.

Task.risk_score is now validated against the spec's stated 1-100 range
(OUTPUT FORMAT: "Risk: [Score 1–100]") — added once the real spec text
confirmed that range; a prior fix in this build had, without the spec
in hand, guessed the range as 0-100 to match a since-corrected caller
bug. See /notes/trading-jarvis-analysis.md, Addendum 3.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class Priority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class RiskBand(str, Enum):
    """Coarse governance band — separate from any trading risk_pct."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Task:
    """One node in a Task Tree."""
    step: int
    task: str
    agent: str
    priority: Priority
    risk_score: int  # 1-100 per Brain Spec Section: OUTPUT FORMAT ("Risk: [Score 1–100]")
    approval_required: bool
    depends_on: tuple[int, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not 1 <= self.risk_score <= 100:
            raise ValueError(
                f"Task step {self.step}: risk_score={self.risk_score} is outside "
                f"the Brain Spec's stated 1-100 range."
            )

    def render(self) -> str:
        return (
            f"Step {self.step}:\n"
            f"  * Task: {self.task}\n"
            f"  * Agent: {self.agent}\n"
            f"  * Priority: {self.priority.value}\n"
            f"  * Risk: {self.risk_score}\n"
            f"  * Approval: {'Yes' if self.approval_required else 'No'}"
        )


@dataclass
class EventPacket:
    """Bus-native structure — every Task must be convertible to one."""
    event_type: str
    priority_level: Priority
    risk_score: int
    domain: str  # startup/domain lock
    assigned_agent: str
    expected_output: str
    approval_required: bool
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "event_type": self.event_type,
            "priority_level": self.priority_level.value,
            "risk_score": self.risk_score,
            "domain": self.domain,
            "assigned_agent": self.assigned_agent,
            "expected_output": self.expected_output,
            "approval_required": self.approval_required,
            "generated_at": self.generated_at,
        }


@dataclass
class TaskTree:
    objective: str
    domain: str
    tasks: list[Task] = field(default_factory=list)

    def add(self, task: Task) -> "TaskTree":
        self.tasks.append(task)
        return self

    def execution_flow(self) -> str:
        order = " → ".join(str(t.step) for t in self.tasks)
        return f"Ordered sequence:\n\n{order}"

    def event_packets(self) -> list[EventPacket]:
        return [
            EventPacket(
                event_type=t.task,
                priority_level=t.priority,
                risk_score=t.risk_score,
                domain=self.domain,
                assigned_agent=t.agent,
                expected_output=f"Structured result for: {t.task}",
                approval_required=t.approval_required,
            )
            for t in self.tasks
        ]

    def render(self) -> str:
        header = f"### TASK TREE — {self.objective}\n"
        body = "\n\n".join(t.render() for t in self.tasks)
        flow = "\n\n### EXECUTION FLOW\n\n" + self.execution_flow()
        return header + "\n" + body + flow


class ActivationGate:
    """Section: ACTIVATION CONDITIONS.

    Swamp Intelligence activates only when task complexity exceeds a
    single agent's scope. Simple, single-step asks should route directly
    to the relevant agent instead of paying the reasoning-layer overhead.
    """

    @staticmethod
    def should_activate(step_count: int, cross_domain: bool, ambiguous: bool) -> bool:
        return step_count > 1 or cross_domain or ambiguous


class GovernanceError(RuntimeError):
    """Raised when a caller tries to make Swamp Intelligence do something
    its Core Brain Spec explicitly prohibits (execute, bypass approval,
    bypass the bus, etc.)."""


class SwampIntelligence:
    """Thin coordination shell around TaskTree construction.

    Decision hierarchy (Section: DECISION LOGIC), highest priority first:
        1. Revenue impact
        2. Risk mitigation
        3. Execution efficiency
        4. Resource allocation

    On conflict: Revenue > Speed, Governance > Autonomy, Clarity > Creativity.
    """

    PROHIBITED = (
        "execute_trade",
        "place_order",
        "execute_task",
        "bypass_approval",
        "bypass_bus",
    )

    def __init__(self, domain: str):
        self.domain = domain

    def guard(self, action_name: str) -> None:
        if action_name in self.PROHIBITED:
            raise GovernanceError(
                f"Swamp Intelligence cannot perform '{action_name}': "
                "it thinks, structures, and routes — it does not execute. "
                "Route this to a human-approved execution surface instead."
            )

    def build_tree(self, objective: str) -> TaskTree:
        return TaskTree(objective=objective, domain=self.domain)


if __name__ == "__main__":
    swamp = SwampIntelligence(domain="demo")
    tree = swamp.build_tree(objective="Demo objective")
    tree.add(Task(step=1, task="Do a thing", agent="Demo Agent",
                   priority=Priority.LOW, risk_score=5, approval_required=False))
    tree.add(Task(step=2, task="Do a risky thing", agent="Demo Agent",
                   priority=Priority.HIGH, risk_score=80, approval_required=True,
                   depends_on=(1,)))
    print(tree.render())
    for p in tree.event_packets():
        print(p.to_dict())
    try:
        swamp.guard("bypass_approval")
    except GovernanceError as e:
        print(f"Correctly blocked: {e}")
