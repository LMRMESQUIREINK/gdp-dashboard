"""Tests for eval_gate.py -- each reproduces a specific, named rule from
the real repo's docs/001-domain.md (the Eval/Gate/Strength/Decision
concepts and the "Rejected concepts" table), the same discipline as
test_thread_mandate.py.

Run with: python3 test_eval_gate.py
"""
from __future__ import annotations

import sys

from eval_gate import EvalResult, GateRule, Strength, accept_ticket, apply_stop, run_gate_eval
from thread_mandate import (
    ActorKind,
    Decision,
    EvalBatch,
    Mandate,
    Policy,
    Thread,
    Ticket,
    TicketRegistry,
    Trigger,
)

FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}" + (f" -- {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(label)


def trig(tid: str, actor: str, kind: ActorKind = ActorKind.PERSON) -> Trigger:
    return Trigger(id=tid, actor=actor, actor_kind=kind)


def main() -> None:
    policy = Policy(version="v1", granted_scopes=frozenset({"repo:fix-bugs"}))
    rules = [GateRule(scope="repo:fix-bugs", originators=frozenset({"alice"}), stoppers=frozenset({"bob"}))]

    # --- a known originator actor gets ACCEPT with explicit strength ----
    print("=== A named originator actor's Trigger is ACCEPTed with EXPLICIT strength ===")
    batch = EvalBatch(triggers=[trig("t1", "alice")])
    result = run_gate_eval(batch, policy, rules)
    check("decision is ACCEPT", result.decision is Decision.ACCEPT)
    check("a real Mandate was granted", isinstance(result.mandate, Mandate))
    check("the Mandate's scope matches the rule's scope", result.mandate.scope == "repo:fix-bugs")
    check("the Mandate records the Policy version it was granted under", result.mandate.policy_version == "v1")
    check(
        "strength is EXPLICIT -- the gate layer alone can never grant INFERRED strength, "
        "since that needs the model's judgement (the assessment layer), not built here",
        result.strength is Strength.EXPLICIT,
    )

    # --- an unknown actor is ignored ---------------------------------------
    print("\n=== An actor named in no rule at all is IGNOREd ===")
    unknown_batch = EvalBatch(triggers=[trig("t2", "mallory")])
    unknown_result = run_gate_eval(unknown_batch, policy, rules)
    check("decision is IGNORE", unknown_result.decision is Decision.IGNORE)
    check("no Mandate is granted on IGNORE", unknown_result.mandate is None)

    # --- a known stopper actor gets STOP, not ACCEPT ------------------------
    print("\n=== A named stopper actor's Trigger is recorded as STOP ===")
    stop_batch = EvalBatch(triggers=[trig("t3", "bob")])
    stop_result = run_gate_eval(stop_batch, policy, rules)
    check("decision is STOP", stop_result.decision is Decision.STOP)
    check("STOP carries no Mandate of its own", stop_result.mandate is None)
    check("STOP still names which scope it matched", stop_result.matched_scope == "repo:fix-bugs")

    # --- STOP takes priority over ACCEPT in the same batch ------------------
    print("\n=== A batch with BOTH a stopper and an originator Trigger resolves to STOP first ===")
    mixed_batch = EvalBatch(triggers=[trig("t4", "alice"), trig("t5", "bob")])
    mixed_result = run_gate_eval(mixed_batch, policy, rules)
    check(
        "STOP wins over ACCEPT when both are present -- real repo rejects leaving half-finished "
        "work running past an explicit stop",
        mixed_result.decision is Decision.STOP,
    )

    # --- a rule for a scope the CURRENT policy no longer grants is dead ----
    print("\n=== A gate rule whose scope the current Policy no longer grants is inert ===")
    narrower_policy = Policy(version="v2", granted_scopes=frozenset({"repo:read-only"}))
    narrowed_result = run_gate_eval(batch, narrower_policy, rules)
    check(
        "the same originator Trigger that was ACCEPTed under policy v1 is IGNOREd under policy v2, "
        "since v2 no longer grants the rule's scope at all -- the rule is treated as nonexistent, "
        "not reinterpreted some other way",
        narrowed_result.decision is Decision.IGNORE,
    )

    # --- real repo: "After two consecutive retries, the third expiry
    # records unavailable" -- regardless of what the batch holds ----------
    print("\n=== Two or more expired attempts always record UNAVAILABLE, regardless of content ===")
    unavailable_result = run_gate_eval(batch, policy, rules, expired_attempts=2)
    check(
        "UNAVAILABLE is recorded even though this exact batch would otherwise ACCEPT -- "
        "the real rule is about the Eval itself timing out, not the Triggers' content",
        unavailable_result.decision is Decision.UNAVAILABLE,
    )
    check("no Mandate is granted on UNAVAILABLE", unavailable_result.mandate is None)
    one_retry_result = run_gate_eval(batch, policy, rules, expired_attempts=1)
    check("a single retry (expired_attempts=1) does NOT force UNAVAILABLE", one_retry_result.decision is Decision.ACCEPT)

    # --- accept_ticket(): the real repo's "When Eval accepts, it creates
    # a Ticket with a Mandate" ------------------------------------------
    print("\n=== accept_ticket() creates a real, subscribed Ticket from an ACCEPT result ===")
    registry = TicketRegistry()
    thread = Thread("thread-1", registry)
    new_ticket = accept_ticket(thread, registry, result, "ticket-new")
    check("the new Ticket carries the exact Mandate the gate granted", new_ticket.mandate is result.mandate)
    check("the new Ticket is registered and retrievable", registry.get("ticket-new") is new_ticket)
    check("the new Ticket is subscribed to the Thread it was accepted on", "ticket-new" in thread.subscriptions)

    raised_on_non_accept = False
    try:
        accept_ticket(thread, registry, unknown_result, "ticket-bad")
    except ValueError:
        raised_on_non_accept = True
    check("accept_ticket() refuses to run on a non-ACCEPT result", raised_on_non_accept)

    # --- the newly-accepted Ticket actually perceives later fan-out, same
    # as any other subscribed Ticket -- closing the loop end to end -------
    print("\n=== The newly-accepted Ticket perceives a LATER Trigger via ordinary Subscription fan-out ===")
    later_trigger = trig("t6", "someone-else", ActorKind.CI)
    thread.ingest(later_trigger)
    check(
        "the Ticket that Eval itself just created receives later Thread activity exactly like any "
        "other subscribed Ticket -- no special-casing for a freshly-ACCEPTed one",
        later_trigger in new_ticket.inputs,
    )

    # --- apply_stop(): withdraws the targeted Ticket's Mandate -------------
    print("\n=== apply_stop() withdraws the targeted Ticket's Mandate via a real STOP decision ===")
    target_ticket = Ticket(id="ticket-target", mandate=Mandate(scope="repo:fix-bugs", policy_version="v1"))
    registry.add(target_ticket)
    stopped = apply_stop(registry, stop_result, "ticket-target")
    check("apply_stop() returns the same Ticket it stopped", stopped is target_ticket)
    check("the targeted Ticket's Mandate is withdrawn", target_ticket.mandate.withdrawn)
    check("the targeted Ticket is marked stopped and ended", target_ticket.stopped and target_ticket.ended)

    raised_on_non_stop = False
    try:
        apply_stop(registry, result, "ticket-target")
    except ValueError:
        raised_on_non_stop = True
    check("apply_stop() refuses to run on a non-STOP result", raised_on_non_stop)

    raised_on_missing_ticket = False
    try:
        apply_stop(registry, stop_result, "ticket-does-not-exist")
    except ValueError:
        raised_on_missing_ticket = True
    check("apply_stop() refuses when the named ticket_id isn't registered", raised_on_missing_ticket)

    print(f"\n{'='*60}")
    if FAILURES:
        print(f"{len(FAILURES)} CHECK(S) FAILED: {FAILURES}")
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
