"""
The local/outward approval gate — adapted from the source article's
pattern (post_file's effect="outward", held for a human "yes" before it
ever runs). Kept as its own small module rather than folded into the
agent loop, since both run_agent (one tool at a time) and run_chain
(several dependent tools planned in a single model call) need the same
hold-for-approval behavior.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PendingApproval:
    tool: str
    args: dict


class ApprovalGate:
    """A call is approved only if its exact (tool, args) pair was
    explicitly granted — approving one call never silently approves a
    different one, even to the same tool. Approvals are single-use:
    consuming one requires granting it again for the next call, matching
    the article's reasoning that an approval is for the specific preview
    shown, not a standing grant."""

    def __init__(self):
        self._approved: set[tuple] = set()

    @staticmethod
    def _key(tool: str, args: dict) -> tuple:
        return (tool, tuple(sorted(args.items())))

    def approve(self, tool: str, args: dict) -> None:
        self._approved.add(self._key(tool, args))

    def is_approved(self, tool: str, args: dict) -> bool:
        return self._key(tool, args) in self._approved

    def consume(self, tool: str, args: dict) -> bool:
        key = self._key(tool, args)
        if key in self._approved:
            self._approved.discard(key)
            return True
        return False
