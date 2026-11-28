"""Tests for assessment.py and run_gate_eval()'s hand-off to it -- proving
IGNORE now distinguishes "no gate rule, no assessment layer configured"
from "no gate rule, a real assessment layer was consulted and declined,"
and that the assessment layer can genuinely ACCEPT/STOP with INFERRED
strength where the gate layer alone would have stopped at IGNORE.

No live model exists in this sandbox (same standing restriction as every
other build here needing one), so every "assessor" here is a scripted
stand-in -- same mocking convention this project uses throughout for a
model-dependent component (e.g. the mocked-Anthropic-client tests in
/builds/trading-jarvis/, /builds/interface-lift-toolkit/).

Run with: python3 test_assessment.py
"""
from __future__ import annotations

import sys

from assessment import AssessmentRequest, AssessmentResult, Strength
from eval_gate import EvalResult, GateRule, run_gate_eval
from thread_mandate import ActorKind, Decision, EvalBatch, Policy, Trigger

FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}" + (f" -- {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(label)


POLICY = Policy(version="v1", granted_scopes=frozenset({"repo:fix-bugs", "repo:triage"}))
GATE_RULES = [GateRule(scope="repo:fix-bugs", originators=frozenset({"alice"}))]


def unmatched_batch(actor: str = "someone-not-in-any-gate-rule") -> EvalBatch:
    return EvalBatch(triggers=[Trigger(id="t1", actor=actor, actor_kind=ActorKind.PERSON)])


def main() -> None:
    # --- with no assessor, IGNORE now says plainly that none was asked --
    print("=== No assessor configured: IGNORE names the real reason ===")
    no_assessor_result = run_gate_eval(unmatched_batch(), POLICY, GATE_RULES)
    check("decision is IGNORE", no_assessor_result.decision is Decision.IGNORE)
    check(
        "the reason explicitly says no assessment layer was even configured, "
        "not a bare 'ignore' with no explanation",
        "no assessment layer is configured" in no_assessor_result.reason,
    )

    # --- a scripted assessor that ACCEPTs grants INFERRED strength, which
    # the gate layer alone can never produce ------------------------------
    print("\n=== A real assessor can ACCEPT where the gate layer alone would IGNORE ===")

    def accepting_assessor(request: AssessmentRequest) -> AssessmentResult:
        check(
            "the assessor receives the real batch and real declined-scopes tuple",
            request.batch.triggers[0].actor == "someone-not-in-any-gate-rule"
            and request.gate_declined_scopes == ("repo:fix-bugs",),
        )
        return AssessmentResult(decision=Decision.ACCEPT, scope="repo:triage",
                                 reason="model judged this a routine triage request")

    accepted = run_gate_eval(unmatched_batch(), POLICY, GATE_RULES, assessor=accepting_assessor)
    check("decision is ACCEPT via the assessment layer", accepted.decision is Decision.ACCEPT)
    check("a real Mandate was granted", accepted.mandate is not None
          and accepted.mandate.scope == "repo:triage")
    check(
        "strength is INFERRED -- only the assessment layer can ever grant this, "
        "never the gate layer alone",
        accepted.strength is Strength.INFERRED,
    )
    check("the reason names the assessor's own stated reason", "routine triage request" in accepted.reason)

    # --- an assessor's STOP is honored the same way -----------------------
    print("\n=== A real assessor can STOP where the gate layer alone would IGNORE ===")

    def stopping_assessor(request: AssessmentRequest) -> AssessmentResult:
        return AssessmentResult(decision=Decision.STOP, scope="repo:triage",
                                 reason="model judged this a withdrawal request")

    stopped = run_gate_eval(unmatched_batch(), POLICY, GATE_RULES, assessor=stopping_assessor)
    check("decision is STOP via the assessment layer", stopped.decision is Decision.STOP)
    check("STOP carries no Mandate, same as a gate-layer STOP", stopped.mandate is None)
    check("the reason names the assessor's own stated reason", "withdrawal request" in stopped.reason)

    # --- an assessor that declines still produces IGNORE, but with a
    # DIFFERENT, distinguishable reason than "no assessor at all" ----------
    print("\n=== A real, consulted assessor that declines gives a DIFFERENT IGNORE reason ===")

    def declining_assessor(request: AssessmentRequest) -> AssessmentResult:
        return AssessmentResult(decision=Decision.IGNORE, reason="nothing actionable here")

    declined = run_gate_eval(unmatched_batch(), POLICY, GATE_RULES, assessor=declining_assessor)
    check("decision is IGNORE", declined.decision is Decision.IGNORE)
    check(
        "the reason says a real assessment layer was consulted and declined -- "
        "genuinely different text from the no-assessor-configured case above",
        "consulted and declined" in declined.reason and declined.reason != no_assessor_result.reason,
    )
    check("the assessor's own stated reason is carried through", "nothing actionable here" in declined.reason)

    # --- an assessor cannot grant a scope the current Policy doesn't allow,
    # even if it tries to -- the same check the gate layer already enforces
    print("\n=== An assessor cannot grant a scope the current Policy doesn't allow ===")

    def overreaching_assessor(request: AssessmentRequest) -> AssessmentResult:
        return AssessmentResult(decision=Decision.ACCEPT, scope="repo:admin-delete-everything",
                                 reason="model tried to grant an ungranted scope")

    overreach_result = run_gate_eval(unmatched_batch(), POLICY, GATE_RULES, assessor=overreaching_assessor)
    check(
        "the overreaching ACCEPT is refused and falls through to IGNORE, exactly like the gate "
        "layer's own 'policy no longer grants this rule's scope' rule",
        overreach_result.decision is Decision.IGNORE,
    )
    check("no Mandate was granted for the disallowed scope", overreach_result.mandate is None)

    # --- the gate layer's own ACCEPT/STOP still short-circuits BEFORE the
    # assessor is ever even called -------------------------------------------
    print("\n=== A matching gate rule is decided WITHOUT ever consulting the assessor ===")
    assessor_was_called = []

    def assessor_that_should_never_run(request: AssessmentRequest) -> AssessmentResult:
        assessor_was_called.append(True)
        return AssessmentResult(decision=Decision.ACCEPT, scope="repo:fix-bugs", reason="should not run")

    gate_matched_batch = EvalBatch(triggers=[Trigger(id="t2", actor="alice", actor_kind=ActorKind.PERSON)])
    gate_result = run_gate_eval(gate_matched_batch, POLICY, GATE_RULES, assessor=assessor_that_should_never_run)
    check("the gate layer's own rule decides this, with EXPLICIT strength",
          gate_result.decision is Decision.ACCEPT and gate_result.strength is Strength.EXPLICIT)
    check("the assessor was never called at all when the gate layer already matched",
          len(assessor_was_called) == 0)

    # --- the expired-attempts timeout short-circuits BEFORE either layer
    # runs, same as before this round's change -------------------------------
    print("\n=== expired_attempts>=2 still short-circuits before gate OR assessment run ===")
    unavailable = run_gate_eval(unmatched_batch(), POLICY, GATE_RULES, expired_attempts=2,
                                 assessor=assessor_that_should_never_run)
    check("decision is UNAVAILABLE", unavailable.decision is Decision.UNAVAILABLE)
    check("the assessor still was never called", len(assessor_was_called) == 0)

    print(f"\n{'='*60}")
    if FAILURES:
        print(f"{len(FAILURES)} CHECK(S) FAILED: {FAILURES}")
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
