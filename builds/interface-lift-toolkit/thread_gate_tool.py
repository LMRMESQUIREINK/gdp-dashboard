"""thread_gate_tool -- wires /builds/dsh-thread-mandate/'s gate-only Eval
(eval_gate.py's run_gate_eval/accept_ticket/apply_stop, run against the
real thread_mandate.py Thread/Ticket/Mandate model, both copied in
unmodified, same convention okf_navigator.py already follows here) onto
THIS TOOLKIT's own real ToolRegistry, so last round's gate mechanism
actually governs real tool dispatch instead of staying a standalone demo.

The real distinguishing property over this toolkit's existing
`toolkit/approval.py` ApprovalGate: an ApprovalGate approval is single-use,
consumed by the one (tool, args) pair it was granted for. A Mandate here
is granted ONCE per Eval decision and then backs MANY calls to any tool
within its granted scope, until a person explicitly stops it or a Policy
change revokes it on resume -- the real Eval-decides-once /
Ticket-executes-many-times split this project's dsh-superagent analysis
found, not a second implementation of the same single-use idea.

Two new tools, registered against the SAME real registry whose other
tools they dispatch into:

  - thread_gate_request(actor, actor_kind, scope, existing_ticket_id="")
    Runs a real Trigger through the real gate-only Eval. On ACCEPT,
    creates and registers a real Ticket holding the granted Mandate and
    returns its ticket_id. With existing_ticket_id set, a stop-authorized
    actor can instead STOP that specific Ticket (withdrawing its Mandate).
  - thread_gate_execute(ticket_id, tool, args)
    Dispatches `tool` through the REAL registry (registry.call(tool,
    **args)) only if ticket_id names a live Ticket whose Mandate is not
    withdrawn and whose granted scope actually covers that tool -- the
    real tool call happens for real, not a stub.
"""
from __future__ import annotations

import uuid
from typing import Optional

from eval_gate import GateRule, accept_ticket, apply_stop, run_gate_eval
from thread_mandate import ActorKind, Decision, Policy, Thread, TicketRegistry, Trigger

from toolkit.registry import ToolRegistry
from toolkit.result import result

# A real policy for this toolkit: one scope, "prop-firm-sizing", covering
# the already-registered, already-tested prop_firm_size_check tool --
# not a toy scope invented just for this module.
SCOPE_TOOLS = {
    "prop-firm-sizing": frozenset({"prop_firm_size_check"}),
}
GATE_RULES = [
    GateRule(
        scope="prop-firm-sizing",
        originators=frozenset({"risk-analyst"}),
        stoppers=frozenset({"risk-lead"}),
    ),
]
POLICY = Policy(version="v1", granted_scopes=frozenset(SCOPE_TOOLS))

_REGISTRY = TicketRegistry()
_THREADS: dict[str, Thread] = {}


def _thread_for(scope: str) -> Thread:
    if scope not in _THREADS:
        _THREADS[scope] = Thread(f"thread-{scope}", _REGISTRY)
    return _THREADS[scope]


def register_thread_gate_tools(registry: ToolRegistry) -> None:
    @registry.tool(effect="local")
    def thread_gate_request(actor: str, actor_kind: str, scope: str,
                             existing_ticket_id: str = "") -> dict:
        """Submit a real Trigger to the gate-only Eval for a given scope
        (e.g. 'prop-firm-sizing') and get back a real Decision
        (accept/stop/ignore/unavailable). actor_kind: 'person', 'bot', or
        'ci'. On accept, a new Ticket is created holding a real Mandate
        for that scope and its id is returned for use with
        thread_gate_execute. Pass existing_ticket_id to target a STOP
        decision at a specific already-live Ticket instead of starting
        new work."""
        try:
            kind = ActorKind(actor_kind)
        except ValueError:
            return result(
                f"unknown actor_kind {actor_kind!r}, must be one of "
                f"{[k.value for k in ActorKind]}",
                checks=[("known actor_kind", False)],
            )
        if scope not in SCOPE_TOOLS:
            return result(
                f"unknown scope {scope!r}, must be one of {sorted(SCOPE_TOOLS)}",
                checks=[("known scope", False)],
            )

        thread = _thread_for(scope)
        trigger = Trigger(id=str(uuid.uuid4()), actor=actor, actor_kind=kind)
        thread.ingest(trigger)
        batch = thread.start_eval()
        decision_result = run_gate_eval(batch, POLICY, GATE_RULES)
        thread.end_eval()

        if decision_result.decision is Decision.ACCEPT:
            ticket_id = f"ticket-{uuid.uuid4()}"
            accept_ticket(thread, _REGISTRY, decision_result, ticket_id)
            return result(
                f"accepted: Ticket {ticket_id} now holds a Mandate for scope {scope!r}",
                checks=[("decision", True)],
                decision="accept", ticket_id=ticket_id, scope=scope,
                allowed_tools=sorted(SCOPE_TOOLS[scope]),
            )
        if decision_result.decision is Decision.STOP:
            if not existing_ticket_id:
                return result(
                    "a stop-authorized actor must name existing_ticket_id to stop",
                    checks=[("ticket named", False)],
                )
            stopped = apply_stop(_REGISTRY, decision_result, existing_ticket_id)
            return result(
                f"stopped: Ticket {stopped.id}'s Mandate withdrawn",
                checks=[("decision", True)],
                decision="stop", ticket_id=stopped.id,
            )
        return result(
            f"{decision_result.decision.value}: no Ticket created",
            checks=[("decision", True)],
            decision=decision_result.decision.value,
        )

    @registry.tool(effect="local")
    def thread_gate_execute(ticket_id: str, tool: str, args: dict) -> dict:
        """Dispatch a real registered tool through the REAL registry, but
        only if ticket_id names a live Ticket (from thread_gate_request)
        whose Mandate has not been withdrawn and whose granted scope
        actually covers that tool name. The named tool's own real result
        is returned unmodified -- this never re-implements the tool."""
        ticket = _REGISTRY.get(ticket_id)
        if ticket is None:
            return result(f"no such ticket: {ticket_id!r}", checks=[("ticket exists", False)])
        if ticket.mandate.withdrawn:
            return result(
                f"ticket {ticket_id!r}'s Mandate was withdrawn -- refusing to dispatch {tool!r}",
                checks=[("mandate valid", False)],
            )
        allowed = SCOPE_TOOLS.get(ticket.mandate.scope, frozenset())
        if tool not in allowed:
            return result(
                f"ticket {ticket_id!r}'s Mandate (scope={ticket.mandate.scope!r}) does not "
                f"cover tool {tool!r}; allowed: {sorted(allowed)}",
                checks=[("tool covered by mandate", False)],
            )
        real_result = registry.call(tool, **args)
        return result(
            f"dispatched {tool!r} under ticket {ticket_id!r}'s Mandate",
            checks=[("mandate valid", True), ("tool covered by mandate", True)],
            tool=tool, ticket_id=ticket_id, real_result=real_result,
        )
