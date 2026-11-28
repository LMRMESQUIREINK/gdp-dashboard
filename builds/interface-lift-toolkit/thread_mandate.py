"""thread_mandate -- a standalone, dependency-free reimplementation of the
one mechanism in `deepseek-ai/dsh-superagent-prototype` (read directly from
its real `docs/001-domain.md` domain model, not guessed from the Medium
article that pointed at it) that is both genuinely new to this project and
fully specified enough to build for real: Thread Subscription fan-out, and
the Policy/Eval/Mandate authorization split.

This is NOT a port of dsh-superagent's actual GitHub/Feishu integration --
that needs a live GitHub App and a live model, neither available here. It
is the domain model underneath it, independently reimplemented from reading
the real repo's docs/001-domain.md table (concepts, rules, and the
"Rejected concepts" table) rather than copied from its TypeScript source.

The property this operationalizes, read directly from the real repo: a
Worker-equivalent (Ticket) perceives related activity -- including another
Worker's activity -- purely by SUBSCRIBING to the same Thread, with no
central coordinator polling for conflicts and no admission check on who
sent the triggering message. Authorization (Mandate) is a SEPARATE concept
from context delivery (Subscription): a Trigger reaching a Ticket through a
Subscription is handed over as context only, and never itself triggers a
new Eval or grants new authority -- matching the real repo's own rejected
design ("Admission checks on Subscriptions" -- rejected, with the reason
"A Subscription covers the whole Thread; the Mandate separates
authorization from context").
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ActorKind(Enum):
    PERSON = "person"
    BOT = "bot"
    CI = "ci"


class Decision(Enum):
    ACCEPT = "accept"
    STOP = "stop"
    IGNORE = "ignore"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class Trigger:
    id: str
    actor: str
    actor_kind: ActorKind
    payload: object = None


@dataclass(frozen=True)
class Policy:
    """A versioned set of scopes this Policy version is willing to grant.
    Real repo: "The Policy version covers the rules, the accept mode and
    the Source parts." Simplified here to the one property this build
    tests: whether a given scope is still supported by THIS version.
    """
    version: str
    granted_scopes: frozenset[str]

    def grants(self, scope: str) -> bool:
        return scope in self.granted_scopes


class MandateRevoked(Exception):
    """Raised when a Mandate is revalidated against a Policy version that
    no longer grants its scope. Real repo: "a Policy that no longer holds
    it revokes it. Revalidated against the current Policy before an ended
    Ticket resumes." """


@dataclass
class Mandate:
    """What an accept grants. Real repo: "Immutable; wider scope means a
    new Ticket. A Ticket's end does not end it: only a person's stop
    withdraws it, and a Policy that no longer holds it revokes it."
    """
    scope: str
    policy_version: str
    withdrawn: bool = False

    def withdraw(self) -> None:
        """Only a person's explicit stop may call this -- see Ticket.stop()."""
        self.withdrawn = True

    def revalidate(self, current_policy: Policy) -> None:
        """Checked before an ended Ticket resumes. Raises if the CURRENT
        policy no longer grants this Mandate's scope, even though the
        Mandate was valid under the policy version it was created under."""
        if self.withdrawn:
            raise MandateRevoked(f"mandate for scope {self.scope!r} was withdrawn by a person")
        if not current_policy.grants(self.scope):
            raise MandateRevoked(
                f"policy {current_policy.version!r} no longer grants scope {self.scope!r} "
                f"(mandate was granted under policy {self.policy_version!r})"
            )


@dataclass
class Ticket:
    """A unit of authorized work. Real repo: "Goes open -> ended, and back
    to open when a person's message on one of its Threads resumes it,
    unless a person stopped it."
    """
    id: str
    mandate: Mandate
    ended: bool = False
    stopped: bool = False
    inputs: list = field(default_factory=list)

    def stop(self) -> None:
        """A person's explicit stop. Withdraws the Mandate -- distinct from
        the Ticket simply ending normally, which does NOT withdraw it."""
        self.stopped = True
        self.ended = True
        self.mandate.withdraw()

    def receive_context(self, trigger: Trigger) -> None:
        """Context delivered via Subscription fan-out. Never triggers a new
        Eval, never grants new authority -- just an Input. Real repo: "a
        person's message that reaches a Ticket this way takes no Eval." """
        self.inputs.append(trigger)


class TicketRegistry:
    def __init__(self) -> None:
        self._tickets: dict[str, Ticket] = {}

    def add(self, ticket: Ticket) -> None:
        self._tickets[ticket.id] = ticket

    def get(self, ticket_id: str) -> Optional[Ticket]:
        return self._tickets.get(ticket_id)


class EvalAlreadyRunning(Exception):
    """Real repo: "At most one Eval runs on it at a time." """


@dataclass
class EvalBatch:
    triggers: list[Trigger]


class Thread:
    """Triggers in time order, plus the Subscriptions that fan them out as
    context. Real repo: "At most one Eval runs on it at a time... Its
    running Eval... runs serially and merges Triggers that arrive meanwhile
    into the next batch." """

    def __init__(self, thread_id: str, registry: TicketRegistry):
        self.id = thread_id
        self._registry = registry
        self.triggers: list[Trigger] = []
        self.subscriptions: set[str] = set()
        self._eval_running = False
        self._pending_batch: list[Trigger] = []

    def subscribe(self, ticket_id: str) -> None:
        """Many-to-many: a Thread may have several subscribed Tickets at
        once. Real repo rejects "At most one live Ticket per Thread" --
        "One Thread can carry several independent pieces of work." """
        self.subscriptions.add(ticket_id)

    def unsubscribe(self, ticket_id: str) -> None:
        self.subscriptions.discard(ticket_id)

    def ingest(self, trigger: Trigger) -> None:
        """Record the Trigger, fan it out to every live subscribed Ticket
        as context (no admission check -- real repo: "with no check of
        who sent it"), and queue it for the next Eval batch. A Ticket a
        person stopped receives nothing. A bot/CI trigger reaching an
        ENDED ticket's subscription does not resume it -- only a person's
        message does (real repo: "messages from bots and CI do not reach
        it, since its Executor reads its Threads again when it resumes").
        """
        self.triggers.append(trigger)
        for ticket_id in self.subscriptions:
            ticket = self._registry.get(ticket_id)
            if ticket is None or ticket.stopped:
                continue
            if ticket.ended and trigger.actor_kind is not ActorKind.PERSON:
                continue
            if ticket.ended and trigger.actor_kind is ActorKind.PERSON:
                ticket.ended = False  # resumed under the SAME mandate, no new Eval
            ticket.receive_context(trigger)
        self._pending_batch.append(trigger)

    def start_eval(self) -> EvalBatch:
        """Takes the pending batch to run an Eval against. Raises if an
        Eval is already running on this Thread -- the real repo's own
        single-Eval-per-Thread invariant."""
        if self._eval_running:
            raise EvalAlreadyRunning(f"thread {self.id!r} already has a running Eval")
        self._eval_running = True
        batch, self._pending_batch = self._pending_batch, []
        return EvalBatch(batch)

    def end_eval(self) -> None:
        """Marks the running Eval finished. Triggers that arrived meanwhile
        are already sitting in `_pending_batch` for the NEXT Eval -- they
        were never merged into the batch the just-finished Eval saw."""
        self._eval_running = False

    @property
    def eval_running(self) -> bool:
        return self._eval_running
