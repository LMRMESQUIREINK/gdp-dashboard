"""
Per-task measurement ledger — adapted from the source article's
speed_ledger.py. Exists so a claimed speed/cost improvement for this
toolkit is a number in a table, not an assertion in prose — the same
discipline the article itself uses (and the same discipline this
project's own README's always demand: numbers, not "it feels faster").
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TaskCounters:
    """Live counters for one in-progress task, incremented by run_agent /
    run_chain as they go, then turned into a LedgerRow with Ledger.record()."""
    model_calls: int = 0
    tool_calls: int = 0
    ui_actions: int = 0


@dataclass
class LedgerRow:
    task: str
    model_calls: int
    tool_calls: int
    ui_actions: int
    tokens: str
    seconds: str
    checks: str


class Ledger:
    def __init__(self):
        self.rows: list[LedgerRow] = []

    def add(self, task: str, model_calls, tool_calls, ui_actions, tokens: str,
             seconds: str, checks: str) -> None:
        self.rows.append(LedgerRow(task, model_calls, tool_calls, ui_actions, tokens, seconds, checks))

    def record(self, task: str, counters: TaskCounters, tokens: str, seconds: str, checks: str) -> None:
        self.add(task, counters.model_calls, counters.tool_calls, counters.ui_actions, tokens, seconds, checks)

    def show(self) -> str:
        header = f"{'task':<42} {'model':>6} {'tools':>6} {'UI':>4} {'tokens':>10} {'seconds':>10} {'checks':>10}"
        lines = [header]
        for r in self.rows:
            lines.append(
                f"{r.task:<42} {str(r.model_calls):>6} {str(r.tool_calls):>6} {str(r.ui_actions):>4} "
                f"{r.tokens:>10} {r.seconds:>10} {r.checks:>10}"
            )
        text = "\n".join(lines)
        print(text)
        return text
