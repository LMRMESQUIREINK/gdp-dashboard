"""Tests for policy/write_tiers.py, including the real end-to-end
demo_write_tiers.py classification against the real size_check_tool()."""
from __future__ import annotations

import time
import unittest

from demo_write_tiers import WRITE_TIER_RULES, set_position_size
from policy.identity_bridge import IdentityBridge, SimulatedIdP, generate_pkce_pair
from policy.write_tiers import (
    PayloadMismatch,
    RiskTier,
    StepUpRequired,
    TierRule,
    WriteAlreadyConsumed,
    WriteNotFound,
    WriteStager,
    classify_tier,
    commit_write,
    guard_write,
)


def _verified_identity(idp, bridge, subject_id="risk-desk-user"):
    verifier, challenge = generate_pkce_pair()
    code = idp.issue_authorization_code(subject_id, challenge)
    return bridge.verify(code, verifier)


class TestClassifyTier(unittest.TestCase):
    def test_small_size_is_immediate(self):
        self.assertEqual(
            classify_tier(WRITE_TIER_RULES, "set_position_size", {"contracts": 1}),
            RiskTier.IMMEDIATE,
        )

    def test_medium_size_is_confirm(self):
        self.assertEqual(
            classify_tier(WRITE_TIER_RULES, "set_position_size", {"contracts": 4}),
            RiskTier.CONFIRM,
        )

    def test_large_size_is_step_up(self):
        self.assertEqual(
            classify_tier(WRITE_TIER_RULES, "set_position_size", {"contracts": 10}),
            RiskTier.STEP_UP,
        )

    def test_unmatched_input_defaults_to_step_up_not_immediate(self):
        """Fail toward more friction, never less, for anything a rule
        set doesn't explicitly classify."""
        self.assertEqual(classify_tier([], "unclassified_op", {"x": 1}), RiskTier.STEP_UP)


class TestImmediateTierNeverStages(unittest.TestCase):
    def test_immediate_write_is_cleared_with_no_write_id(self):
        stager = WriteStager()
        result = guard_write(
            stager=stager, rules=WRITE_TIER_RULES, operation="set_position_size",
            payload={"tier": "50K", "symbol": "NQ", "contracts": 1}, actor="trader-1",
        )
        self.assertEqual(result["status"], "cleared")
        self.assertEqual(result["tier"], "immediate")
        self.assertNotIn("write_id", result)


class TestConfirmTierStageAndCommit(unittest.TestCase):
    def setUp(self):
        self.stager = WriteStager()
        self.payload = {"tier": "50K", "symbol": "NQ", "contracts": 3}

    def test_stage_then_commit_executes_the_real_tool(self):
        staged = guard_write(
            stager=self.stager, rules=WRITE_TIER_RULES, operation="set_position_size",
            payload=self.payload, actor="trader-1",
        )
        self.assertEqual(staged["status"], "staged")
        self.assertEqual(staged["tier"], "confirm")

        result = commit_write(self.stager, staged["write_id"], payload=self.payload, fn=set_position_size)
        self.assertEqual(result["status"], "executed")
        # the real size_check_tool() output, not a stub
        self.assertIn("size_rule", result["result"])
        self.assertEqual(result["result"]["size_rule"]["max_contracts"], 6)

    def test_committing_a_different_payload_is_rejected(self):
        staged = guard_write(
            stager=self.stager, rules=WRITE_TIER_RULES, operation="set_position_size",
            payload=self.payload, actor="trader-1",
        )
        tampered_payload = {**self.payload, "contracts": 999}
        with self.assertRaises(PayloadMismatch):
            commit_write(self.stager, staged["write_id"], payload=tampered_payload, fn=set_position_size)

    def test_a_write_cannot_be_committed_twice(self):
        staged = guard_write(
            stager=self.stager, rules=WRITE_TIER_RULES, operation="set_position_size",
            payload=self.payload, actor="trader-1",
        )
        commit_write(self.stager, staged["write_id"], payload=self.payload, fn=set_position_size)
        with self.assertRaises(WriteAlreadyConsumed):
            commit_write(self.stager, staged["write_id"], payload=self.payload, fn=set_position_size)

    def test_committing_an_unknown_write_id_is_rejected(self):
        with self.assertRaises(WriteNotFound):
            commit_write(self.stager, "write-does-not-exist", payload=self.payload, fn=set_position_size)

    def test_fn_is_never_called_on_a_rejected_commit(self):
        """The invariant that actually matters: a tampered payload must
        never reach the real tool, checked with a call counter, not just
        the exception type."""
        calls = []

        def spy_fn(**kwargs):
            calls.append(kwargs)
            return {"ok": True}

        staged = guard_write(
            stager=self.stager, rules=WRITE_TIER_RULES, operation="set_position_size",
            payload=self.payload, actor="trader-1",
        )
        tampered = {**self.payload, "contracts": 999}
        with self.assertRaises(PayloadMismatch):
            commit_write(self.stager, staged["write_id"], payload=tampered, fn=spy_fn)
        self.assertEqual(calls, [])


class TestStepUpTier(unittest.TestCase):
    def setUp(self):
        self.stager = WriteStager()
        self.idp = SimulatedIdP()
        self.idp.register_user("risk-desk-user", "Risk Desk Reviewer")
        self.bridge = IdentityBridge(self.idp)
        self.payload = {"tier": "50K", "symbol": "NQ", "contracts": 20}

    def test_large_write_is_classified_step_up(self):
        staged = guard_write(
            stager=self.stager, rules=WRITE_TIER_RULES, operation="set_position_size",
            payload=self.payload, actor="trader-1",
        )
        self.assertEqual(staged["tier"], "step_up")
        self.assertIn("write_id", staged)

    def test_commit_without_any_identity_is_refused(self):
        staged = guard_write(
            stager=self.stager, rules=WRITE_TIER_RULES, operation="set_position_size",
            payload=self.payload, actor="trader-1",
        )
        with self.assertRaises(StepUpRequired):
            commit_write(self.stager, staged["write_id"], payload=self.payload, fn=set_position_size)

    def test_commit_with_a_fresh_verified_identity_succeeds(self):
        staged = guard_write(
            stager=self.stager, rules=WRITE_TIER_RULES, operation="set_position_size",
            payload=self.payload, actor="trader-1",
        )
        identity = _verified_identity(self.idp, self.bridge)
        result = commit_write(
            self.stager, staged["write_id"], payload=self.payload,
            fn=set_position_size, fresh_identity=identity,
        )
        self.assertEqual(result["status"], "executed")

    def test_commit_with_a_stale_identity_is_refused(self):
        """A step_up write must not be satisfiable by reusing whatever
        identity the agent's session already had lying around — it must
        be RE-verified close to the moment of commit."""
        staged = guard_write(
            stager=self.stager, rules=WRITE_TIER_RULES, operation="set_position_size",
            payload=self.payload, actor="trader-1",
        )
        stale_identity = _verified_identity(self.idp, self.bridge)
        # force staleness directly rather than sleeping in a test
        stale_identity = stale_identity.__class__(
            subject_id=stale_identity.subject_id, display_name=stale_identity.display_name,
            verified_at=time.time() - 9999, verified_by=stale_identity.verified_by,
        )
        with self.assertRaises(StepUpRequired):
            commit_write(
                self.stager, staged["write_id"], payload=self.payload,
                fn=set_position_size, fresh_identity=stale_identity,
                # step_up_freshness_seconds stays at write_tiers.py's default
            )

    def test_fn_never_called_without_step_up_satisfied(self):
        calls = []

        def spy_fn(**kwargs):
            calls.append(kwargs)
            return {"ok": True}

        staged = guard_write(
            stager=self.stager, rules=WRITE_TIER_RULES, operation="set_position_size",
            payload=self.payload, actor="trader-1",
        )
        with self.assertRaises(StepUpRequired):
            commit_write(self.stager, staged["write_id"], payload=self.payload, fn=spy_fn)
        self.assertEqual(calls, [])


class TestTierRuleOrderingIsDeclarationOrder(unittest.TestCase):
    def test_first_matching_rule_wins(self):
        rules = [
            TierRule(tier=RiskTier.IMMEDIATE, condition={"field": "x", "op": ">=", "value": 0}),
            TierRule(tier=RiskTier.STEP_UP, condition=None),
        ]
        # Both rules match x=5, but the first (IMMEDIATE) must win.
        self.assertEqual(classify_tier(rules, "op", {"x": 5}), RiskTier.IMMEDIATE)


if __name__ == "__main__":
    unittest.main()
