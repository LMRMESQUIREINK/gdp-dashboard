"""The stage/confirm/commit write-tier pattern — from "A Blueprint for
Production Agentic AI Systems in the Enterprise" (Natarajan Selvaraj),
part of the 5-article bundle analyzed in
/notes/okf-rag-agentic-bundle-analysis.md. Credited there as "the single
most load-bearing mechanism across all five articles" — this round's
"2-3 week" next move, built as an extension of this project's existing
governance build rather than a new one (checked /builds/ first: the
closest adjacent coverage is right here, in `governed_call.py`/
`approval_store.py`).

The article's own description: every write carries a backend-signed
context pinning EXACTLY what will be written, classified into one of
three risk tiers (`immediate` / `confirm` / `step_up`), enforced outside
the model by a `guard_write()` function — never by a prompt instruction
asking the model to be careful.

How this differs from `governed_call`'s existing REQUIRES_APPROVAL path,
deliberately, not redundantly:
  - `governed_call` answers "is a HUMAN allowed to approve this at all,"
    gated by a policy the organization wrote (contracts > 5 -> Risk Desk).
  - `write_tiers` answers "once something IS going to be written, how
    much friction does committing it need" -- a classification the
    article ties to risk, independent of whether a separate human
    approval workflow exists. The two can be combined (a REQUIRES_APPROVAL
    policy plus a step_up-tier write), but neither implies the other.

The `step_up` tier is the one place this module reaches into
`identity_bridge.py`, tying the Blueprint's write-tier pattern directly
to the VIAB mechanism built in the same round: committing a `step_up`
write requires a FRESH `VerifiedIdentity` -- re-authentication performed
after the write was staged, not reused from whenever the agent's session
first started. This operationalizes the article's own phrase for this
tier ("step_up") literally, rather than treating it as a bigger rubber
stamp on the same identity.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional

from policy.approval_store import canonical_hash
from policy.conditions import evaluate as evaluate_condition
from policy.identity_bridge import VerifiedIdentity


class RiskTier(str, Enum):
    IMMEDIATE = "immediate"   # commits the moment it's requested, no staging at all
    CONFIRM = "confirm"       # must be staged, then confirmed against the exact pinned payload
    STEP_UP = "step_up"       # confirm, PLUS a fresh re-verified identity at commit time


class StepUpRequired(ValueError):
    pass


class WriteNotFound(ValueError):
    pass


class PayloadMismatch(ValueError):
    pass


class WriteAlreadyConsumed(ValueError):
    pass


@dataclass
class TierRule:
    """A classification rule, matching conditions.py's shape exactly so
    an organization can configure "what counts as step_up" the same way
    it configures a Policy's own condition — plain data, never eval()."""
    tier: RiskTier
    condition: Optional[dict[str, Any]]  # None matches everything; checked in declaration order


def classify_tier(rules: list[TierRule], operation: str, payload: dict[str, Any]) -> RiskTier:
    """Returns the first matching rule's tier, in declaration order,
    defaulting to STEP_UP (fail toward MORE friction, never less) if
    nothing matches -- an unclassified write is the one case this module
    refuses to treat as low-risk by default."""
    context = {"operation": operation, **payload}
    for rule in rules:
        if evaluate_condition(rule.condition, context):
            return rule.tier
    return RiskTier.STEP_UP


@dataclass
class StagedWrite:
    write_id: str
    operation: str
    payload_hash: str
    tier: RiskTier
    actor: str
    staged_at: float
    status: str  # "staged" | "consumed"


class WriteStager:
    """The 'backend-signed context pinning exactly what will be written.'
    In-memory on purpose (a staged write is meant to be short-lived,
    confirmed within the same interaction, unlike an `ApprovalStore`
    record which can sit pending for hours) -- `canonical_hash()` is
    reused directly from approval_store.py rather than reimplemented, so
    the two modules' notion of 'the same payload' can never drift apart."""

    def __init__(self) -> None:
        self._writes: dict[str, StagedWrite] = {}
        self._counter = 0

    def stage(self, *, operation: str, payload: dict[str, Any], actor: str, tier: RiskTier) -> StagedWrite:
        self._counter += 1
        write_id = f"write-{self._counter}"
        record = StagedWrite(
            write_id=write_id, operation=operation, payload_hash=canonical_hash(payload),
            tier=tier, actor=actor, staged_at=time.time(), status="staged",
        )
        self._writes[write_id] = record
        return record

    def get(self, write_id: str) -> Optional[StagedWrite]:
        return self._writes.get(write_id)

    def verify_and_consume(self, write_id: str, payload: dict[str, Any], *,
                            fresh_identity: Optional[VerifiedIdentity] = None,
                            step_up_freshness_seconds: float = 60.0) -> StagedWrite:
        """Raises if the write doesn't exist, was already consumed, the
        payload being committed doesn't match what was pinned at staging
        time, or -- for a step_up write -- no sufficiently fresh verified
        identity is supplied. Never silently downgrades a step_up write
        to a plain confirm for lack of an identity; it refuses instead."""
        record = self._writes.get(write_id)
        if record is None:
            raise WriteNotFound(f"no such staged write: {write_id}")
        if record.status == "consumed":
            raise WriteAlreadyConsumed(f"write {write_id} was already consumed")
        actual_hash = canonical_hash(payload)
        if actual_hash != record.payload_hash:
            raise PayloadMismatch(
                f"payload hash mismatch for write {write_id}: pinned {record.payload_hash[:12]}... "
                f"!= actual {actual_hash[:12]}... — refusing to commit a different write than the "
                f"one that was staged"
            )
        if record.tier == RiskTier.STEP_UP:
            if fresh_identity is None:
                raise StepUpRequired(f"write {write_id} is step_up tier and requires a fresh re-verified identity")
            age = time.time() - fresh_identity.verified_at
            if age > step_up_freshness_seconds:
                raise StepUpRequired(
                    f"write {write_id} requires re-verification within {step_up_freshness_seconds}s; "
                    f"supplied identity was verified {age:.1f}s ago"
                )
        record.status = "consumed"
        return record


def guard_write(*, stager: WriteStager, rules: list[TierRule], operation: str,
                 payload: dict[str, Any], actor: str) -> dict[str, Any]:
    """The enforcement entry point, matching the article's own named
    function exactly. An `immediate`-tier write is never staged at all —
    it's classified and returned as already-cleared-to-commit; `confirm`
    and `step_up` writes are staged and must go through
    `commit_write()`/`WriteStager.verify_and_consume()` before the real
    tool function is ever called."""
    tier = classify_tier(rules, operation, payload)
    if tier == RiskTier.IMMEDIATE:
        return {"status": "cleared", "tier": tier.value}
    record = stager.stage(operation=operation, payload=payload, actor=actor, tier=tier)
    return {"status": "staged", "write_id": record.write_id, "tier": tier.value}


def commit_write(stager: WriteStager, write_id: str, *, payload: dict[str, Any],
                  fn: Callable[..., dict], fresh_identity: Optional[VerifiedIdentity] = None) -> dict[str, Any]:
    """Commits a staged write — the real tool function `fn` is only ever
    reached after `verify_and_consume()` succeeds."""
    stager.verify_and_consume(write_id, payload, fresh_identity=fresh_identity)
    result = fn(**payload)
    return {"status": "executed", "write_id": write_id, "result": result}
