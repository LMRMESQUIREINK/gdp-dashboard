"""Tests for thread_gate_tool.py -- proving the gate-only Eval from
/builds/dsh-thread-mandate/ actually governs dispatch through THIS
TOOLKIT's real ToolRegistry, not a standalone demo.

Run with: python3 test_thread_gate_tool.py
"""
from __future__ import annotations

import sys

from thread_gate_tool import register_thread_gate_tools
from tools_demo import register_demo_tools

from toolkit.registry import ToolRegistry

FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}" + (f" -- {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(label)


def main() -> None:
    registry = ToolRegistry()
    register_demo_tools(registry)       # the real prop_firm_size_check, etc.
    register_thread_gate_tools(registry)  # the new gate tools, same registry

    check("thread_gate_request and thread_gate_execute are real registered tools",
          "thread_gate_request" in registry and "thread_gate_execute" in registry)

    # --- an unauthorized actor gets IGNORE, no Ticket, dispatch refused --
    print("=== An unauthorized actor cannot request a Ticket, and dispatch is refused ===")
    ignored = registry.call("thread_gate_request", actor="mallory", actor_kind="person",
                             scope="prop-firm-sizing")
    check("unauthorized actor's request is IGNOREd", ignored["decision"] == "ignore")
    check("no ticket_id was granted", "ticket_id" not in ignored)
    refused = registry.call("thread_gate_execute", ticket_id="no-such-ticket",
                             tool="prop_firm_size_check", args={"tier": "50K", "symbol": "ES", "contracts": 1})
    check("dispatch against a nonexistent ticket is refused", refused["ok"] is False)

    # --- an authorized actor gets a real Ticket, and can dispatch the
    # real tool through it, matching a direct call exactly ----------------
    print("\n=== An authorized actor's Ticket really dispatches the real prop_firm_size_check ===")
    accepted = registry.call("thread_gate_request", actor="risk-analyst", actor_kind="person",
                              scope="prop-firm-sizing")
    check("authorized actor's request is ACCEPTed", accepted["decision"] == "accept")
    ticket_id = accepted["ticket_id"]
    check("a real ticket_id was granted", bool(ticket_id))

    gated = registry.call("thread_gate_execute", ticket_id=ticket_id, tool="prop_firm_size_check",
                           args={"tier": "50K", "symbol": "ES", "contracts": 3})
    direct = registry.call("prop_firm_size_check", tier="50K", symbol="ES", contracts=3)
    check("the gated dispatch succeeds", gated["ok"] is True)
    check(
        "the gated dispatch's real_result EXACTLY matches a direct call to the same real tool -- "
        "proof thread_gate_execute really dispatches, not a stub",
        gated["real_result"] == direct,
    )

    # --- the SAME ticket can dispatch MULTIPLE times -- the real
    # Eval-decides-once / Ticket-executes-many-times split -----------------
    print("\n=== The same Ticket authorizes a SECOND, different call without a fresh Eval ===")
    gated_again = registry.call("thread_gate_execute", ticket_id=ticket_id, tool="prop_firm_size_check",
                                 args={"tier": "100K", "symbol": "ES", "contracts": 2})
    direct_again = registry.call("prop_firm_size_check", tier="100K", symbol="ES", contracts=2)
    check(
        "a second, differently-parameterized call under the SAME ticket_id also succeeds and "
        "matches a direct call -- no fresh thread_gate_request was needed",
        gated_again["ok"] is True and gated_again["real_result"] == direct_again,
    )

    # --- a Mandate never authorizes a tool outside its own scope ----------
    print("\n=== A Mandate never authorizes a tool its scope doesn't cover ===")
    out_of_scope = registry.call("thread_gate_execute", ticket_id=ticket_id,
                                  tool="prop_firm_pass_probability", args={})
    check("dispatching a tool outside the ticket's granted scope is refused",
          out_of_scope["ok"] is False)

    # --- a stop-authorized actor can withdraw a specific Ticket's Mandate,
    # and dispatch through it is refused afterward --------------------------
    print("\n=== A stop-authorized actor withdraws the Ticket's Mandate; dispatch is refused after ===")
    stopped = registry.call("thread_gate_request", actor="risk-lead", actor_kind="person",
                             scope="prop-firm-sizing", existing_ticket_id=ticket_id)
    check("the stop-authorized actor's request is recorded as STOP", stopped["decision"] == "stop")
    post_stop = registry.call("thread_gate_execute", ticket_id=ticket_id, tool="prop_firm_size_check",
                               args={"tier": "50K", "symbol": "ES", "contracts": 1})
    check(
        "dispatch through the now-stopped ticket is refused, even though the exact same call "
        "succeeded earlier under the same ticket_id",
        post_stop["ok"] is False,
    )

    # --- an unknown scope/actor_kind are refused with a clean error, not
    # a raw exception --------------------------------------------------------
    print("\n=== Unknown scope/actor_kind fail cleanly, not with a raw exception ===")
    bad_scope = registry.call("thread_gate_request", actor="risk-analyst", actor_kind="person",
                               scope="not-a-real-scope")
    check("an unknown scope is refused cleanly", bad_scope["ok"] is False)
    bad_kind = registry.call("thread_gate_request", actor="risk-analyst", actor_kind="robot",
                              scope="prop-firm-sizing")
    check("an unknown actor_kind is refused cleanly", bad_kind["ok"] is False)

    print(f"\n{'='*60}")
    if FAILURES:
        print(f"{len(FAILURES)} CHECK(S) FAILED: {FAILURES}")
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
