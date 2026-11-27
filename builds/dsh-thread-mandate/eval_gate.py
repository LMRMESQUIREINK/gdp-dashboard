"""eval_gate -- the GATE layer of the real repo's two-layer Eval concept,
wired on top of `thread_mandate.py` so a Trigger batch taken off a Thread
(via `Thread.start_eval()`) actually produces a real `Decision`, instead of
stopping at "here is a batch of Triggers" the way the original build left
it.

Real repo, `docs/001-domain.md`: "Eval -- The judgement on a batch of
Triggers, in two layers: gate and assessment... Output: a Decision." and
"Gate -- The deterministic first layer of Eval: who may originate work,
and with what strength." This module implements ONLY the gate layer --
deterministic, rule-based, no model call. The real repo's second layer,
assessment ("The model's judgement during Eval"), needs a live model and
is deliberately NOT built here, same standing restriction as every other
build in this project needing a live model call.

One direct, real consequence of gate-only: the real repo's Strength group
is `explicit` / `inferred`, and only the gate layer can ever grant
`explicit` strength (a Trigger's actor is named directly in a rule) --
`inferred` strength needs the model's judgement, so this module never
produces it. That's a real, stated scope limit, not an oversight.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from thread_mandate import (
    Decision,
    EvalBatch,
    Mandate,
    Policy,
    Thread,
    Ticket,
    TicketRegistry,
)


class Strength(Enum):
    EXPLICIT = "explicit"
    INFERRED = "inferred"


@dataclass(frozen=True)
class GateRule:
    """Real repo: Policy covers "who may originate work through that
    Source, in that Source's own identities." `originators` is that
    allow-list for one scope; `stoppers` is a second, separate allow-list
    for who may end work under that scope -- distinct because the real
    repo rejects "An Executor declaring that a person asked it to stop":
    "Only Eval decides the strength of an end," so stopping, like
    accepting, is a gate decision with its own authorized set of actors,
    never something a Ticket/Executor grants itself.
    """
    scope: str
    originators: frozenset[str]
    stoppers: frozenset[str] = frozenset()


@dataclass
class EvalResult:
    """Output of the gate layer. `mandate`/`strength`/`matched_scope` are
    only ever set together, and only on ACCEPT."""
    decision: Decision
    mandate: Optional[Mandate] = None
    strength: Optional[Strength] = None
    matched_scope: Optional[str] = None


def run_gate_eval(
    batch: EvalBatch,
    policy: Policy,
    gate_rules: list[GateRule],
    *,
    expired_attempts: int = 0,
) -> EvalResult:
    """The deterministic gate pass over one already-taken EvalBatch (see
    `Thread.start_eval()`). Real repo: "An expired Eval queues its
    Triggers for another attempt. After two consecutive retries, the
    third expiry records unavailable" -- `expired_attempts` lets a caller
    model exactly that: 0 and 1 are live retries, 2 or more always records
    UNAVAILABLE regardless of what the batch actually contains, since the
    real rule is about the Eval itself timing out, not about anything the
    Triggers say.

    A rule whose scope the CURRENT Policy no longer grants is treated as
    if it didn't exist at all -- the gate never falls back to some other
    meaning for a withdrawn scope.

    When both a stop-authorized and an originate-authorized Trigger land
    in the same batch, STOP is decided first: real repo rejects "Ticket
    state that follows the DSH Session" and "Cancelling running Tickets
    on a Policy change" because half-finished, uncoordinated work is
    worse than a clean stop -- the same reasoning favors resolving an
    explicit stop request before starting anything new in the same batch.
    """
    if expired_attempts >= 2:
        return EvalResult(decision=Decision.UNAVAILABLE)

    for trigger in batch.triggers:
        for rule in gate_rules:
            if not policy.grants(rule.scope):
                continue
            if trigger.actor in rule.stoppers:
                return EvalResult(decision=Decision.STOP, matched_scope=rule.scope)

    for trigger in batch.triggers:
        for rule in gate_rules:
            if not policy.grants(rule.scope):
                continue
            if trigger.actor in rule.originators:
                mandate = Mandate(scope=rule.scope, policy_version=policy.version)
                return EvalResult(
                    decision=Decision.ACCEPT,
                    mandate=mandate,
                    strength=Strength.EXPLICIT,
                    matched_scope=rule.scope,
                )

    return EvalResult(decision=Decision.IGNORE)


def accept_ticket(
    thread: Thread,
    registry: TicketRegistry,
    result: EvalResult,
    ticket_id: str,
) -> Ticket:
    """Real repo: "When Eval accepts, it creates a Ticket with a Mandate"
    -- the one, specific thing an ACCEPT decision does. Raises on any
    other decision rather than silently no-op'ing, since calling this on
    a non-ACCEPT result would be a caller bug, not a legitimate branch.
    The new Ticket is immediately subscribed to the Thread it was decided
    on, so it starts perceiving later Triggers the same way every other
    subscribed Ticket does -- no special-casing for a freshly-accepted one.
    """
    if result.decision is not Decision.ACCEPT or result.mandate is None:
        raise ValueError(f"accept_ticket() called on a non-ACCEPT result: {result.decision!r}")
    ticket = Ticket(id=ticket_id, mandate=result.mandate)
    registry.add(ticket)
    thread.subscribe(ticket_id)
    return ticket


def apply_stop(
    registry: TicketRegistry,
    result: EvalResult,
    ticket_id: str,
) -> Ticket:
    """Real repo: stopping withdraws the targeted Ticket's Mandate (see
    `Ticket.stop()`). Raises on any decision other than STOP, and raises
    if the named ticket_id isn't a real, registered Ticket -- a STOP
    decision with nothing real to apply it to is a caller bug, not
    something to swallow silently.
    """
    if result.decision is not Decision.STOP:
        raise ValueError(f"apply_stop() called on a non-STOP result: {result.decision!r}")
    ticket = registry.get(ticket_id)
    if ticket is None:
        raise ValueError(f"apply_stop() target ticket {ticket_id!r} is not registered")
    ticket.stop()
    return ticket
