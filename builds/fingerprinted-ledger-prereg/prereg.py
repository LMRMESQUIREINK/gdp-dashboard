"""A hash-locked pre-registration and verdict harness for a set of named
hypotheses — SUPPORTED / NOT SUPPORTED / REPORTED, decided against a rule
fixed before the numbers existed, with the rule set's own hash re-checked
at decision time so nothing can be loosened after seeing the result.

Also carries resume_holds(): the exact strict resume-rigor rule
FareedKhan-dev/dynamic-workflow-agents' own H8 hypothesis uses — found,
while verifying that source, to be stricter (and more correct) than the
obvious naive check. Independently reimplemented, not copied.
"""
import hashlib
import json


class PreregistrationError(Exception):
    pass


class Preregistration:
    def __init__(self, title, hypotheses):
        """hypotheses: a list of {"id", "claim"} dicts, fixed at construction.
        A 'rule' field describing how holds is computed is documentation only
        — the actual rule is a Python expression supplied by the caller at
        decide() time, scoped to that id by the caller's own code, the same
        separation the source notebook uses between its PREREG dict (data)
        and its decide() call sites (code)."""
        self.title = title
        self.hypotheses = {h["id"]: h for h in hypotheses}
        self._canonical = json.dumps(
            {"title": title, "hypotheses": hypotheses}, sort_keys=True, separators=(",", ":")
        )
        self.sha256 = hashlib.sha256(self._canonical.encode("utf-8")).hexdigest()

    def verify_unchanged(self, expected_sha256):
        """Refuses to decide anything if the hypothesis set drifted from what
        was pinned before results existed."""
        if self.sha256 != expected_sha256:
            raise PreregistrationError(
                "the hypothesis rules changed after pre-registration — "
                f"expected {expected_sha256[:12]}..., got {self.sha256[:12]}..."
            )

    def decide(self, hid, holds, measured):
        if hid not in self.hypotheses:
            raise PreregistrationError(f"{hid!r} was never pre-registered")
        verdict = "REPORTED" if holds is None else ("SUPPORTED" if holds else "NOT SUPPORTED")
        return {"id": hid, "claim": self.hypotheses[hid]["claim"], "measured": measured, "verdict": verdict}


def resume_holds(crash_status, paid_before, paid_after, total, repeat_paid, same_report):
    """Whether a crash-then-resume experiment actually supports "a crashed
    run resumes without paying twice."

    The naive version of this check is "did the final result match, and was
    nothing visibly double-charged" — but that passes just as happily on a
    run where NOTHING was paid at all, which proves nothing about double
    payment. Verifying a real source against this exact rule found that
    rule catching precisely that case in the wild, in two independent model
    editions of the same experiment: both recorded runs show
    paid_before + paid_after == 0 while total == 56 (and 20), i.e. the whole
    crash-and-resume sequence was answered entirely from a pre-populated
    cache with zero fresh evidence either side of the "crash" — so this
    rule correctly refuses to call the hypothesis supported, where an
    outcome-only check would have wrongly passed it.
    """
    return (
        crash_status == "cancelled"
        and paid_before + paid_after == total
        and repeat_paid == 0
        and same_report
    )
