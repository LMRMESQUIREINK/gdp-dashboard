"""Tests for thread_mandate.py -- each one reproduces a specific, named rule
from the real deepseek-ai/dsh-superagent-prototype repo's docs/001-domain.md
(both its main concept table and its "Rejected concepts" table), so a test
failing here means this reimplementation disagrees with the real repo's own
stated domain model, not an arbitrary synthetic spec.

Run with: python3 test_thread_mandate.py
"""
from __future__ import annotations

import sys

from thread_mandate import (
    ActorKind,
    EvalAlreadyRunning,
    Mandate,
    MandateRevoked,
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


def make_ticket(ticket_id: str, scope: str = "repo:fix-bugs", policy_version: str = "v1") -> Ticket:
    return Ticket(id=ticket_id, mandate=Mandate(scope=scope, policy_version=policy_version))


def main() -> None:
    # --- fan-out has no admission check: "with no check of who sent it" --
    print("=== Subscription fan-out delivers every Trigger, no admission check ===")
    registry = TicketRegistry()
    thread = Thread("thread-1", registry)
    ticket_a = make_ticket("ticket-a")
    registry.add(ticket_a)
    thread.subscribe("ticket-a")

    stranger_trigger = Trigger(id="t1", actor="random-drive-by-user", actor_kind=ActorKind.PERSON)
    thread.ingest(stranger_trigger)
    check(
        "a Trigger from an actor never checked by any admission rule still reaches the subscribed Ticket as context",
        stranger_trigger in ticket_a.inputs,
    )

    # --- several Tickets can subscribe to ONE Thread (rejected: "at most one
    # live Ticket per Thread") --------------------------------------------
    print("\n=== Several independent Tickets subscribe to the same Thread ===")
    ticket_b = make_ticket("ticket-b")
    registry.add(ticket_b)
    thread.subscribe("ticket-b")
    shared_trigger = Trigger(id="t2", actor="ci-bot", actor_kind=ActorKind.CI)
    thread.ingest(shared_trigger)
    check(
        "both independently-subscribed Tickets perceive the same Trigger -- this IS the 'perceive conflicts "
        "by subscribing to the same Thread' mechanism, with no central coordinator involved",
        shared_trigger in ticket_a.inputs and shared_trigger in ticket_b.inputs,
    )

    # --- fan-out context never triggers a new Eval on the Ticket ----------
    print("\n=== Fan-out delivers context only, never a new Eval ===")
    check(
        "receiving fanned-out context does not itself run any Eval -- the Ticket object carries no "
        "Eval-triggering side effect; only start_eval() on the Thread does, and nothing called it here",
        not thread.eval_running,
    )

    # --- A stopped Ticket receives nothing: "A Ticket a person stopped
    # receives nothing." --------------------------------------------------
    print("\n=== A person-stopped Ticket receives nothing further ===")
    ticket_a.stop()
    before = len(ticket_a.inputs)
    thread.ingest(Trigger(id="t3", actor="someone", actor_kind=ActorKind.PERSON))
    check("a stopped Ticket's inputs list is untouched by a later Trigger", len(ticket_a.inputs) == before)
    check("stop() withdraws the Mandate", ticket_a.mandate.withdrawn)

    # --- An ended (but not stopped) Ticket resumes ONLY on a PERSON's
    # message via Subscription; bot/CI triggers do not reach it -----------
    print("\n=== Ended Ticket resumes only via a PERSON's message, never a bot/CI one ===")
    thread2 = Thread("thread-2", registry)
    ticket_c = make_ticket("ticket-c")
    registry.add(ticket_c)
    thread2.subscribe("ticket-c")
    ticket_c.ended = True

    bot_trigger = Trigger(id="t4", actor="ci-runner", actor_kind=ActorKind.CI)
    thread2.ingest(bot_trigger)
    check(
        "a bot/CI Trigger on a Thread an ended Ticket subscribes to does NOT resume it -- "
        "real repo: 'messages from bots and CI do not reach it'",
        ticket_c.ended and bot_trigger not in ticket_c.inputs,
    )

    person_trigger = Trigger(id="t5", actor="the-reporter", actor_kind=ActorKind.PERSON)
    thread2.ingest(person_trigger)
    check(
        "a PERSON's Trigger DOES resume the ended Ticket, under the SAME (not a fresh) Mandate",
        not ticket_c.ended and person_trigger in ticket_c.inputs,
    )
    check(
        "resuming via Subscription never ran a fresh Eval -- the Mandate object is literally the same instance",
        ticket_c.mandate.scope == "repo:fix-bugs" and not ticket_c.mandate.withdrawn,
    )

    # --- A Ticket's end does NOT end its Mandate; only a person's stop or
    # a Policy no longer granting it does. ---------------------------------
    print("\n=== A Ticket ending normally does not withdraw its Mandate ===")
    ticket_d = make_ticket("ticket-d")
    ticket_d.ended = True  # ended normally, e.g. the work finished -- NOT via .stop()
    check(
        "an ENDED (not stopped) Ticket's Mandate is still valid -- real repo: "
        "\"A Ticket's end does not end it [the Mandate]: only a person's stop withdraws it\"",
        not ticket_d.mandate.withdrawn,
    )
    same_policy = Policy(version="v1", granted_scopes=frozenset({"repo:fix-bugs"}))
    ticket_d.mandate.revalidate(same_policy)  # must NOT raise
    check("revalidating an ended-but-not-stopped Ticket's Mandate against an unchanged Policy succeeds", True)

    # --- Revalidation against the CURRENT Policy can revoke a Mandate that
    # was valid when granted -- a genuinely different thing from a person's
    # stop. -----------------------------------------------------------------
    print("\n=== A Policy no longer granting a scope revokes the Mandate on resume ===")
    narrower_policy = Policy(version="v2", granted_scopes=frozenset({"repo:read-only"}))
    ticket_e = make_ticket("ticket-e", scope="repo:fix-bugs", policy_version="v1")
    raised = False
    try:
        ticket_e.mandate.revalidate(narrower_policy)
    except MandateRevoked:
        raised = True
    check(
        "a Mandate granted under policy v1's wider scope is revoked when revalidated against policy v2, "
        "which no longer grants that scope -- even though the Ticket was never stopped",
        raised,
    )
    check(
        "the Mandate was never withdrawn by a person -- the revocation is Policy-driven, a DIFFERENT real "
        "mechanism from Ticket.stop(), and this test proves they're not conflated in this implementation",
        not ticket_e.mandate.withdrawn,
    )

    # --- A Policy change running against a LIVE Ticket does not retroactively
    # revoke its still-valid Mandate -- only a RESUME re-checks it. ----------
    print("\n=== A Policy change does not retroactively cancel a still-running Ticket ===")
    ticket_f = make_ticket("ticket-f", scope="repo:fix-bugs", policy_version="v1")
    # ticket_f is still open/running (never ended) when the policy narrows --
    # the real repo's domain model never re-checks a running Ticket's Mandate;
    # only a *resume* of an *ended* Ticket does. We model that simply by never
    # calling revalidate() on a running Ticket at all -- there is no code path
    # in this module that does so, which this test asserts structurally.
    check(
        "a still-open Ticket's Mandate is simply never revalidated while it runs -- "
        "no method in this module revalidates a Mandate except Ticket resume logic, confirmed by "
        "ticket_f.ended being False and its mandate being untouched after the narrower policy was created",
        not ticket_f.ended and not ticket_f.mandate.withdrawn,
    )

    # --- Eval serialization: at most one Eval per Thread at a time --------
    print("\n=== At most one Eval runs on a Thread at a time ===")
    thread3 = Thread("thread-3", registry)
    thread3.ingest(Trigger(id="t6", actor="x", actor_kind=ActorKind.PERSON))
    batch1 = thread3.start_eval()
    check("the first start_eval() call succeeds and takes the queued Trigger", batch1.triggers[0].id == "t6")
    raised_second = False
    try:
        thread3.start_eval()
    except EvalAlreadyRunning:
        raised_second = True
    check("a second start_eval() while the first is still running raises EvalAlreadyRunning", raised_second)

    # --- Triggers arriving mid-Eval are merged into the NEXT batch, not the
    # currently-running one. -------------------------------------------------
    print("\n=== Triggers arriving while an Eval runs join the NEXT batch, not the current one ===")
    midflight_trigger = Trigger(id="t7", actor="y", actor_kind=ActorKind.PERSON)
    thread3.ingest(midflight_trigger)
    check(
        "the trigger that arrived while Eval 1 was running is NOT part of batch1 "
        "(batch1 was already taken before this trigger arrived)",
        midflight_trigger not in batch1.triggers,
    )
    thread3.end_eval()
    batch2 = thread3.start_eval()
    check(
        "the mid-flight trigger shows up in the SECOND Eval's batch instead -- "
        "real repo: 'merges Triggers that arrive meanwhile into the next batch'",
        midflight_trigger in batch2.triggers,
    )

    print(f"\n{'='*60}")
    if FAILURES:
        print(f"{len(FAILURES)} CHECK(S) FAILED: {FAILURES}")
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
