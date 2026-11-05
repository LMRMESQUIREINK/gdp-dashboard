"""Real tests against the real compiled canary -- no mocks for the parts
that matter (the compiler, AddressSanitizer, the subprocess boundary).
Run with:  python3 tests/test_defender_loop.py
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_stub import ScriptedDiscoveryAgent, propose_bad_fix_alpha, propose_fix_alpha
from dispatcher import AllowListDispatcher, ToolSpec
from run_defender_loop import CANARY_BIN, CANARY_SRC, build_canary, write_poc
from verifier import detonate, grade_patch, verify_crash


class TestCanaryBuilds(unittest.TestCase):
    def test_canary_compiles_with_asan(self) -> None:
        self.assertTrue(build_canary(CANARY_SRC, CANARY_BIN))
        self.assertTrue(os.path.exists(CANARY_BIN))


class TestDetonation(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(build_canary(CANARY_SRC, CANARY_BIN))
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_alpha_heap_overflow_detected(self) -> None:
        poc = write_poc(self.tmp.name, "a.bin", b"A" + bytes([255]) + b"\x00" * 40)
        r = detonate(CANARY_BIN, poc)
        self.assertTrue(r.crashed)
        self.assertEqual(r.crash_type, "heap-buffer-overflow")
        self.assertIn("canary.c", r.top_frame or "")

    def test_bravo_use_after_free_detected(self) -> None:
        poc = write_poc(self.tmp.name, "b.bin", b"B" + bytes([255]) + b"A")
        r = detonate(CANARY_BIN, poc)
        self.assertTrue(r.crashed)
        self.assertEqual(r.crash_type, "heap-use-after-free")

    def test_benign_input_does_not_crash(self) -> None:
        poc = write_poc(self.tmp.name, "benign.bin", b"A\x02xx")
        r = detonate(CANARY_BIN, poc)
        self.assertFalse(r.crashed)
        self.assertEqual(r.exit_code, 0)

    def test_unroutable_byte_is_a_clean_noop(self) -> None:
        poc = write_poc(self.tmp.name, "z.bin", b"Z\x02xx")
        r = detonate(CANARY_BIN, poc)
        self.assertFalse(r.crashed)

    def test_verify_crash_requires_majority_of_reruns(self) -> None:
        poc = write_poc(self.tmp.name, "a.bin", b"A" + bytes([255]) + b"\x00" * 40)
        verdict = verify_crash(CANARY_BIN, poc, runs=3)
        self.assertTrue(verdict.passed)
        self.assertEqual(verdict.reproductions, 3)


class TestHostNeverTrustsTheAgentsClaim(unittest.TestCase):
    """The one rule this build exists to prove: whatever the agent says
    about whether its PoC crashed, the host's own independent detonation
    is the only thing that decides the verdict."""

    def setUp(self) -> None:
        self.assertTrue(build_canary(CANARY_SRC, CANARY_BIN))
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_dishonest_agent_denying_a_real_crash_is_still_caught(self) -> None:
        poc_bytes = b"B" + bytes([255]) + b"A"
        agent = ScriptedDiscoveryAgent("parse_bravo", poc_bytes, honest=False)
        poc = write_poc(self.tmp.name, "b.bin", agent.poc_bytes)
        real = detonate(CANARY_BIN, poc)
        claim = agent.claim(actually_crashed=real.crashed)

        self.assertTrue(real.crashed)                 # ground truth: it really crashes
        self.assertFalse(claim.self_reported_crash)    # the agent lied and said it didn't
        verdict = verify_crash(CANARY_BIN, poc)
        self.assertTrue(verdict.passed)                # the host's verdict ignores the lie entirely

    def test_dishonest_agent_claiming_a_fake_crash_is_also_caught(self) -> None:
        benign_bytes = b"A\x02xx"
        agent = ScriptedDiscoveryAgent("parse_alpha", benign_bytes, honest=False)
        poc = write_poc(self.tmp.name, "benign.bin", agent.poc_bytes)
        real = detonate(CANARY_BIN, poc)
        claim = agent.claim(actually_crashed=real.crashed)

        self.assertFalse(real.crashed)                 # ground truth: this input is harmless
        self.assertTrue(claim.self_reported_crash)      # the agent lied and claimed a crash
        verdict = verify_crash(CANARY_BIN, poc)
        self.assertFalse(verdict.passed)                # the host's verdict ignores the lie entirely


class TestPatchLadder(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        with open(CANARY_SRC) as fh:
            self.source = fh.read()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_root_cause_patch_passes_the_full_ladder(self) -> None:
        good = propose_fix_alpha(self.source)
        self.assertIn("if (claimed > 8) claimed = 8;", good.patched_source)
        src = write_poc(self.tmp.name, "good.c", good.patched_source.encode())
        binp = os.path.join(self.tmp.name, "good_entry")
        verdict = grade_patch(
            build_fn=lambda: build_canary(src, binp),
            patched_binary=binp,
            poc_path=write_poc(self.tmp.name, "poc.bin", b"A" + bytes([255]) + b"\x00" * 40),
            benign_path=write_poc(self.tmp.name, "benign.bin", b"A\x02xx"),
        )
        self.assertTrue(verdict.builds)
        self.assertTrue(verdict.poc_stops)
        self.assertTrue(verdict.benign_still_works)
        self.assertTrue(verdict.passed)

    def test_cosmetic_non_fix_is_rejected_by_the_ladder(self) -> None:
        bad = propose_bad_fix_alpha(self.source)
        self.assertNotIn("if (claimed > 8) claimed = 8;", bad.patched_source)
        src = write_poc(self.tmp.name, "bad.c", bad.patched_source.encode())
        binp = os.path.join(self.tmp.name, "bad_entry")
        verdict = grade_patch(
            build_fn=lambda: build_canary(src, binp),
            patched_binary=binp,
            poc_path=write_poc(self.tmp.name, "poc.bin", b"A" + bytes([255]) + b"\x00" * 40),
            benign_path=write_poc(self.tmp.name, "benign.bin", b"A\x02xx"),
        )
        self.assertTrue(verdict.builds)        # it compiles fine
        self.assertFalse(verdict.poc_stops)    # but the real overflow is untouched
        self.assertFalse(verdict.passed)       # so the ladder correctly rejects it


class TestAllowListDispatcher(unittest.TestCase):
    def _make(self, allow_mutating=False, allow_egress=False) -> AllowListDispatcher:
        tools = {
            "safe_read": ToolSpec("safe_read", lambda **kw: "read-ok"),
            "write_poc": ToolSpec("write_poc", lambda **kw: "write-ok", mutating=True),
            "post_to_slack": ToolSpec("post_to_slack", lambda **kw: "post-ok", egress=True),
        }
        return AllowListDispatcher(
            tools, allowed_names=set(tools),
            allow_mutating=allow_mutating, allow_egress=allow_egress,
        )

    def test_unknown_tool_is_rejected(self) -> None:
        r = self._make().dispatch("rm_rf_root")
        self.assertFalse(r.ok)
        self.assertIn("unknown tool", r.error)

    def test_not_on_allow_list_is_rejected(self) -> None:
        d = self._make()
        d._allowed_names = {"safe_read"}
        r = d.dispatch("write_poc", data=b"x")
        self.assertFalse(r.ok)
        self.assertIn("not allowed", r.error)

    def test_mutating_tool_blocked_by_default(self) -> None:
        r = self._make(allow_mutating=False).dispatch("write_poc", data=b"x")
        self.assertFalse(r.ok)
        self.assertIn("mutating", r.error)

    def test_mutating_tool_allowed_when_enabled(self) -> None:
        r = self._make(allow_mutating=True).dispatch("write_poc", data=b"x")
        self.assertTrue(r.ok)

    def test_egress_blocked_by_default(self) -> None:
        r = self._make(allow_egress=False).dispatch("post_to_slack", to="#team")
        self.assertFalse(r.ok)
        self.assertIn("egress is disabled", r.error)

    def test_egress_allowed_when_enabled(self) -> None:
        r = self._make(allow_egress=True).dispatch("post_to_slack", to="#team")
        self.assertTrue(r.ok)

    def test_safe_read_tool_always_allowed(self) -> None:
        r = self._make().dispatch("safe_read")
        self.assertTrue(r.ok)
        self.assertEqual(r.content, "read-ok")

    def test_tool_exception_becomes_a_failure_result_not_a_crash(self) -> None:
        tools = {"boom": ToolSpec("boom", lambda **kw: (_ for _ in ()).throw(ValueError("x")))}
        d = AllowListDispatcher(tools, allowed_names={"boom"})
        r = d.dispatch("boom")
        self.assertFalse(r.ok)
        self.assertIn("ValueError", r.error)


if __name__ == "__main__":
    unittest.main(verbosity=2)
