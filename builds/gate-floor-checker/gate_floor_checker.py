"""gate-floor-checker: tell "needs more work" apart from "can never pass as written."

Built from a real finding in ayghri/i-have-adhd's evals/RESULTS.md
(analyzed in /notes/week23-github-repos-analysis.md): a weighted,
continuous eval scoring rubric (Correctness/Autonomy/Actionability/
Safety/Concision) sits alongside one absolute veto rule -- "it has no
blocking findings" -- and a release gate that fails on that rule even
though the candidate improved on every weighted dimension and more than
halved its blocker count (7 -> 3). The repo's own RESULTS.md traces this
to one test case that cannot be passed by any run given how the harness
is wired (tools are stripped, so "acts on the repo" can never be true),
and states the consequence plainly: "no candidate can ever pass while
any blocker survives anywhere in the case set, however much it
improves." That is a structural property of the gate, not a quality
signal about the candidate -- and nothing in the repo (or any eval
framework this project has read) names that distinction as a thing to
check for before shipping a gate shaped this way.

This module is that check: given per-case trial outcomes, tell whether
a currently-failing absolute gate is improvable (more/better runs could
plausibly clear it) or structural (at least one case has never once
cleared it across every trial recorded, so by the gate's own logic no
future run can pass either, until the case itself is fixed or excluded).

Zero dependencies beyond the standard library.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CaseTrials:
    """One case's pass/fail record across its recorded trials.

    `blocked` is True for a trial where this case drew at least one
    blocking finding under the gate's own criteria -- not a quality
    score, just whether the absolute rule's condition held for that run.

    `known_structural`, if set True, overrides the trial-based inference
    below. This matters because the real source this tool was built from
    (ayghri/i-have-adhd's evals/RESULTS.md) calls its own unpassable case
    structural on an *architectural* fact stated outside the trial data
    -- the harness runs with `--tools ""`, so a criterion requiring the
    agent to "act on the repository" literally cannot be met, confirmed
    by reading the fixture, not inferred by counting trials. Three
    trials, blocked or not, can only ever support a *weaker*, provisional
    claim than that; `known_structural` is how a human who has actually
    confirmed the architectural cause records the stronger one, while
    plain trial history remains the fallback signal for a case nobody
    has investigated yet.
    """
    case_id: str
    blocked: list[bool]
    known_structural: bool = False

    def __post_init__(self) -> None:
        if not self.blocked:
            raise ValueError(f"case {self.case_id!r} has zero recorded trials")

    @property
    def trial_count(self) -> int:
        return len(self.blocked)

    @property
    def blocked_count(self) -> int:
        return sum(1 for b in self.blocked if b)

    @property
    def ever_cleared(self) -> bool:
        """True if at least one recorded trial had zero blocking findings."""
        return any(not b for b in self.blocked)

    @property
    def never_cleared(self) -> bool:
        """True if this case is confirmed structural (known_structural),
        or every recorded trial drew a blocking finding -- the empirical
        signature of a structurally unpassable case, GIVEN the trials on
        record. The empirical path is evidence, not proof, exactly as
        the source material's own 'three trials is few' caveat states;
        known_structural is how stronger, out-of-band evidence overrides
        a trial history that hasn't (or can't, in three runs) prove it."""
        return self.known_structural or not self.ever_cleared


@dataclass
class GateFloorReport:
    total_cases: int
    currently_passing: bool
    blocked_case_ids: list[str]
    never_cleared_case_ids: list[str]
    verdict: str  # "PASS" | "FAIL_IMPROVABLE" | "FAIL_STRUCTURAL"
    excluding_never_cleared: "GateFloorReport | None" = field(default=None, repr=False)

    def summary(self) -> str:
        if self.verdict == "PASS":
            return f"PASS: 0 of {self.total_cases} cases blocked."
        lines = [
            f"{self.verdict}: {len(self.blocked_case_ids)} of {self.total_cases} cases blocked "
            f"this run ({', '.join(self.blocked_case_ids)})."
        ]
        if self.verdict == "FAIL_STRUCTURAL":
            lines.append(
                "Structurally unpassable, given the trials on record: "
                + ", ".join(self.never_cleared_case_ids)
                + " never once cleared across all recorded trials. "
                "The absolute rule cannot be satisfied by re-running or "
                "improving the candidate alone while these stand -- fix the "
                "case's own fixture/criteria, or make an explicit, named "
                "decision to exclude it, before treating 'still failing' as "
                "a verdict on the candidate's quality."
            )
            if self.excluding_never_cleared is not None:
                lines.append(
                    "Excluding those cases: " + self.excluding_never_cleared.summary()
                )
        return "\n".join(lines)


def check_gate_floor(cases: list[CaseTrials]) -> GateFloorReport:
    """Evaluate the absolute 'zero blocking findings' gate against every
    case's full recorded trial batch, and classify a failure as
    improvable or structural.

    This mirrors the real source's own gate semantics (ayghri/i-have-adhd
    runs N trials of ONE candidate and sums blockers across the whole
    batch, not just a single run): a case counts as currently blocking
    the gate if ANY of its recorded trials drew a blocker, or if it is
    `known_structural`. "Never cleared" is a separate, stricter question
    -- whether EVERY recorded trial blocked -- used only to classify a
    blocking case as structural rather than to decide if it blocks at
    all.

    A `known_structural` case always counts as blocking, even if every
    one of its own recorded trials happened to clear: a trial batch that
    reads clean on a case confirmed architecturally unpassable is more
    likely judge noise than a real fix (the source material's own
    "three trials is few, per-case SD reaches 0.95" caveat is exactly
    this risk) -- the confirmed fact outranks the trial reading.
    """
    if not cases:
        raise ValueError("no cases supplied")

    blocked_now = [c.case_id for c in cases if c.blocked_count > 0 or c.known_structural]
    never_cleared = [c.case_id for c in cases if c.never_cleared]

    if not blocked_now:
        verdict = "PASS"
    elif any(cid in never_cleared for cid in blocked_now):
        verdict = "FAIL_STRUCTURAL"
    else:
        verdict = "FAIL_IMPROVABLE"

    excluding = None
    if verdict == "FAIL_STRUCTURAL":
        remaining = [c for c in cases if c.case_id not in never_cleared]
        if remaining:
            excluding = check_gate_floor(remaining)

    return GateFloorReport(
        total_cases=len(cases),
        currently_passing=(verdict == "PASS"),
        blocked_case_ids=blocked_now,
        never_cleared_case_ids=never_cleared,
        verdict=verdict,
        excluding_never_cleared=excluding,
    )
