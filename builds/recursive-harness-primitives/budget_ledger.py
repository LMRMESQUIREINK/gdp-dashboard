"""budget_ledger.py -- a real, independent reimplementation of the
budget-accounting invariant in Google Research's Harness² (`core/ledger.py`,
`google-research/harness2`, Apache 2.0, arXiv:2610.14224) -- built from
reading the real 132-line file in full
(`/notes/harness2-recursive-agent-optimization-analysis.md` has the detail)
rather than copied verbatim, same convention this project follows for
every other permissively-licensed reference source
(go-buildinfo-extractor, run-terminal-ledger): an independent
implementation built from understanding the invariant means a shared bug
in the original isn't silently inherited, and the reference stays a
genuine comparison point rather than a fork nobody re-derives.

THE REAL INVARIANT, confirmed directly against the real
`core/ledger.py`: for a recursion budget `k`, a correct run of one mode
on one task produces exactly R = 4k execution rollouts and
P = 3k improvement stages (sessions). `assert_identity()` in the real
module raises unless BOTH counts match exactly AND no rollout/session
label repeats -- duplicates are checked FIRST, because a duplicate
write can silently satisfy the count check while actually meaning two
stages overwrote the same run id and one candidate was never really
produced. That ordering (duplicates before counts) is reproduced here
exactly, not simplified away, since it's the whole point of the check.
"""
from __future__ import annotations

from dataclasses import dataclass, field


def expected_rollouts(k: int) -> int:
    """R = 4k."""
    return 4 * int(k)


def expected_sessions(k: int) -> int:
    """P = 3k."""
    return 3 * int(k)


class BudgetError(AssertionError):
    """The ledger did not land on the budget identity."""


@dataclass
class Entry:
    kind: str  # "rollout" | "session"
    label: str
    cost: float = 0.0
    attempts: int = 1


@dataclass
class Ledger:
    """Everything one mode spent on one task, recorded as it happens."""

    mode: str
    task_id: str
    k: int
    entries: list[Entry] = field(default_factory=list)

    def rollout(self, label: str, cost: float = 0.0) -> None:
        self.entries.append(Entry("rollout", label, cost))

    def session(self, label: str, cost: float = 0.0, *, attempts: int = 1) -> None:
        self.entries.append(Entry("session", label, cost, attempts=attempts))

    @property
    def R(self) -> int:
        return sum(1 for e in self.entries if e.kind == "rollout")

    @property
    def P(self) -> int:
        return sum(1 for e in self.entries if e.kind == "session")

    @property
    def cost(self) -> float:
        return round(sum(e.cost for e in self.entries), 6)

    @property
    def rollout_cost(self) -> float:
        return round(sum(e.cost for e in self.entries if e.kind == "rollout"), 6)

    @property
    def session_cost(self) -> float:
        return round(sum(e.cost for e in self.entries if e.kind == "session"), 6)

    def labels(self, kind: str) -> list[str]:
        return [e.label for e in self.entries if e.kind == kind]

    def assert_identity(self) -> None:
        """Raise unless R=4k and P=3k exactly, with no duplicate label in
        either kind. Duplicate check runs BEFORE the count check: a
        duplicate rollout label can make R numerically equal 4k while one
        of the k "real" rollouts never actually happened and something
        else silently got recorded twice in its place -- a count match
        alone cannot tell the two situations apart, so it is not trusted
        alone.
        """
        want_r, want_p = expected_rollouts(self.k), expected_sessions(self.k)
        rl, sl = self.labels("rollout"), self.labels("session")
        dupes = sorted(
            {label for label in rl if rl.count(label) > 1}
            | {label for label in sl if sl.count(label) > 1}
        )
        if not dupes and self.R == want_r and self.P == want_p:
            return
        detail = [
            f"{self.mode}-{self.k} {self.task_id}: "
            f"R={self.R} (want {want_r}), P={self.P} (want {want_p})",
            f"  rollouts: {', '.join(rl) or '(none)'}",
            f"  sessions: {', '.join(sl) or '(none)'}",
        ]
        if dupes:
            detail.append(
                f"  DUPLICATE labels: {dupes} -- a repeated label means two stages "
                f"wrote the same run id and one silently overwrote the other, so a "
                f"candidate the ledger counts was never actually produced"
            )
        raise BudgetError("\n".join(detail))

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "task_id": self.task_id,
            "k": self.k,
            "R": self.R,
            "expected_R": expected_rollouts(self.k),
            "P": self.P,
            "session_attempts": sum(e.attempts for e in self.entries if e.kind == "session"),
            "expected_P": expected_sessions(self.k),
            "cost": self.cost,
            "rollout_cost": self.rollout_cost,
            "session_cost": self.session_cost,
            "rollouts": self.labels("rollout"),
            "sessions": self.labels("session"),
        }
