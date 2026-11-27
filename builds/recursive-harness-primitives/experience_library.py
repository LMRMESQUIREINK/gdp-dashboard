"""experience_library.py -- a real, independent reimplementation of the
ordered, no-future-leakage per-domain experience library in Google
Research's Harness² (`core/library.py` + its real call site in
`core/schedule.py`, `google-research/harness2`, Apache 2.0,
arXiv:2610.14224) -- read in full, not guessed from `library.py`'s own
docstring alone, which is what surfaced the real finding below.

WHAT THE REAL MECHANISM IS
`Library.retain(task_ids)` keeps only the entries for the given task
ids, dropping everything else. `schedule.py`'s real sweep loop calls it
like this, once per task, BEFORE processing that task:

    for i, tid in enumerate(task_ids, 1):
        for lib in libs.values():
            lib.retain(task_ids[: i - 1])
        ... run_task(tid, ...) ...

`task_ids[: i - 1]` is every task strictly before the current one in
`stream_order()` order -- so by construction, a task can only ever see
experience from tasks that ran before it, never one that runs later.

A REAL, FOUND LIMITATION IN THE ORIGINAL DESIGN
`Library.retain()` itself takes an arbitrary list of task ids and trims
to exactly that list -- it has no idea what order tasks actually run
in, and nothing in `Library` stops a caller from passing a list that
includes a LATER task's id. The no-future-leakage guarantee is real and
is correctly implemented in `schedule.py`'s one call site, but it's a
CALLER CONVENTION, not a structural invariant of `Library` itself: a
different or future call site that got the slicing wrong (`task_ids[:i]`
instead of `task_ids[:i - 1]`, say, which would leak the CURRENT task's
own just-written entry into its own context) would silently violate the
guarantee with no error from `Library` -- it would simply retain
whatever it was told to.

THIS BUILD'S FIX, not in the original
`OrderedStream` below wraps an `ExperienceLibrary` with an explicit,
fixed `task_order` and makes the guarantee structural: it computes
`task_order[:index]` ITSELF on every step (never trusting a caller-
supplied slice), and refuses to process a task out of its declared
order. `test_experience_library.py` proves this two ways: (1) the
underlying `ExperienceLibrary.retain()` on its own, called directly
exactly as the real `Library.retain()` is specified, DOES leak a future
task's entry if a caller passes the wrong list -- reproducing the real
design's real gap, not a strawman; (2) `OrderedStream` refuses the same
attack by construction.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class Entry:
    task_id: str
    harness_summary: str
    why: str
    lesson: Optional[str] = None


class OutOfOrderError(RuntimeError):
    """A task was processed out of its declared stream order."""


@dataclass
class ExperienceLibrary:
    """One (run, domain) library -- same shape as the real `Library`:
    read before each task, appended after. `retain()` behaves exactly
    as the real one does, including the real gap described above: it
    trusts whatever task-id list it's given.
    """

    domain: str
    entries: dict[str, Entry] = field(default_factory=dict)

    def add(self, task_id: str, harness_summary: str, why: str, lesson: str | None = None) -> None:
        self.entries[task_id] = Entry(task_id, harness_summary, why, lesson)

    def retain(self, task_ids: list[str]) -> None:
        """Keep only entries for these task ids, dropping everything
        else -- exactly the real `Library.retain()`'s contract. Trusts
        the caller completely; see the module docstring for why that's
        a real limitation.
        """
        keep = set(task_ids)
        for tid in list(self.entries):
            if tid not in keep:
                del self.entries[tid]

    def context_for(self, task_ids: list[str]) -> list[Entry]:
        """Entries for exactly these task ids, in `task_ids` order --
        what an improver session would actually be shown."""
        return [self.entries[tid] for tid in task_ids if tid in self.entries]

    def all_entries(self) -> list[Entry]:
        return list(self.entries.values())


class OrderedStream:
    """A domain's tasks, processed strictly in `task_order`, with the
    no-future-leakage guarantee enforced structurally rather than left
    to the caller to get right at each call site -- the fix for the
    real gap found in the original `Library`/`schedule.py` split (see
    module docstring).
    """

    def __init__(self, library: ExperienceLibrary, task_order: list[str]):
        if len(set(task_order)) != len(task_order):
            raise ValueError(f"task_order has duplicate task ids: {task_order}")
        self.library = library
        self.task_order = list(task_order)
        self._next_index = 0

    def run(self, task_id: str, process_fn: Callable[[str, list[Entry]], Optional[dict]]) -> Optional[dict]:
        """Process exactly the next task in `task_order`. Before calling
        `process_fn`, retains the library down to strictly-prior tasks
        ONLY -- computed internally from `task_order`, never from a
        value the caller supplies, which is what makes this structural
        rather than conventional.

        `process_fn(task_id, prior_entries) -> {"harness_summary", "why",
        "lesson"} | None`. A `None` return means nothing worth recording
        for this task (matching the real `Library.add()`'s own
        `has_experience()` gate -- not every task produces a
        transferable lesson).

        Raises `OutOfOrderError` if `task_id` isn't the declared next
        task, or isn't in `task_order` at all.
        """
        if self._next_index >= len(self.task_order):
            raise OutOfOrderError(f"stream for domain {self.library.domain!r} is already exhausted")
        expected = self.task_order[self._next_index]
        if task_id != expected:
            raise OutOfOrderError(
                f"expected task {expected!r} next in domain {self.library.domain!r}, got {task_id!r}"
            )

        prior_ids = self.task_order[: self._next_index]  # strictly before this task, computed here, not supplied
        self.library.retain(prior_ids)
        prior_entries = self.library.context_for(prior_ids)

        result = process_fn(task_id, prior_entries)
        if result is not None:
            self.library.add(
                task_id,
                harness_summary=result["harness_summary"],
                why=result.get("why", ""),
                lesson=result.get("lesson"),
            )
        self._next_index += 1
        return result

    @property
    def done(self) -> bool:
        return self._next_index >= len(self.task_order)
