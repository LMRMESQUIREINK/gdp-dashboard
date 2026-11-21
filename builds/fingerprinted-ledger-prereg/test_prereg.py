import unittest

from prereg import Preregistration, PreregistrationError, resume_holds


class TestDecide(unittest.TestCase):
    def setUp(self):
        self.prereg = Preregistration(
            "test suite",
            [
                {"id": "H1", "claim": "the workflow finds more bugs than one agent"},
                {"id": "H8", "claim": "a crashed run resumes without paying twice"},
            ],
        )

    def test_true_is_supported(self):
        v = self.prereg.decide("H1", True, "D 0.74, A 0.02")
        self.assertEqual(v["verdict"], "SUPPORTED")
        self.assertEqual(v["claim"], "the workflow finds more bugs than one agent")

    def test_false_is_not_supported(self):
        v = self.prereg.decide("H1", False, "D 0.02, A 0.02")
        self.assertEqual(v["verdict"], "NOT SUPPORTED")

    def test_none_is_reported_not_decided(self):
        v = self.prereg.decide("H1", None, "no comparison data this run")
        self.assertEqual(v["verdict"], "REPORTED")

    def test_an_unregistered_id_raises(self):
        with self.assertRaises(PreregistrationError):
            self.prereg.decide("H99", True, "anything")


class TestHashLock(unittest.TestCase):
    def test_the_same_hypotheses_reproduce_the_same_hash(self):
        a = Preregistration("t", [{"id": "H1", "claim": "x"}])
        b = Preregistration("t", [{"id": "H1", "claim": "x"}])
        self.assertEqual(a.sha256, b.sha256)

    def test_verify_unchanged_passes_against_its_own_hash(self):
        p = Preregistration("t", [{"id": "H1", "claim": "x"}])
        p.verify_unchanged(p.sha256)  # must not raise

    def test_a_changed_claim_is_caught_by_verify_unchanged(self):
        pinned_hash = Preregistration("t", [{"id": "H1", "claim": "x"}]).sha256
        loosened = Preregistration("t", [{"id": "H1", "claim": "x, but easier to satisfy"}])
        with self.assertRaises(PreregistrationError):
            loosened.verify_unchanged(pinned_hash)

    def test_an_added_hypothesis_is_caught_by_verify_unchanged(self):
        pinned_hash = Preregistration("t", [{"id": "H1", "claim": "x"}]).sha256
        expanded = Preregistration("t", [{"id": "H1", "claim": "x"}, {"id": "H2", "claim": "y"}])
        with self.assertRaises(PreregistrationError):
            expanded.verify_unchanged(pinned_hash)


class TestResumeHolds(unittest.TestCase):
    """resume_holds() against real numbers, not just synthetic ones: the toy
    demo (S28) and the formal test (H8) from FareedKhan-dev/dynamic-workflow-agents'
    own two editions, read directly from their notebooks/artifacts."""

    def test_the_source_s28_toy_demo_genuinely_passes(self):
        # paid_before=35, paid_after=25, total=60 (the notebook's own worked numbers)
        self.assertTrue(resume_holds("cancelled", 35, 25, 60, repeat_paid=0, same_report=True))

    def test_the_source_claude_h8_run_correctly_fails_zero_evidence(self):
        # Claude edition's real exp_claims.json: "paid 0 + 0 = 56 calls; same report: True"
        # Nothing was genuinely exercised live on either side of the "crash" — a
        # fully-cached replay proves nothing about double payment, so this must
        # NOT be allowed to pass despite the outcome matching.
        self.assertFalse(resume_holds("cancelled", 0, 0, 56, repeat_paid=0, same_report=True))

    def test_the_source_qwen_h8_run_also_correctly_fails_zero_evidence(self):
        # Qwen edition's real exp_claims.json: "paid 0 + 1 = 20 calls; same report: True"
        self.assertFalse(resume_holds("cancelled", 0, 1, 20, repeat_paid=0, same_report=True))

    def test_a_genuine_split_that_sums_to_total_passes(self):
        self.assertTrue(resume_holds("cancelled", 12, 8, 20, repeat_paid=0, same_report=True))

    def test_a_double_charge_is_caught(self):
        # 30 paid before + 30 paid after = 60, but the uninterrupted total is only 50:
        # 10 calls were answered live twice.
        self.assertFalse(resume_holds("cancelled", 30, 30, 50, repeat_paid=0, same_report=True))

    def test_a_repeat_run_that_still_pays_fails(self):
        self.assertFalse(resume_holds("cancelled", 12, 8, 20, repeat_paid=3, same_report=True))

    def test_a_mismatched_report_fails_even_with_perfect_accounting(self):
        self.assertFalse(resume_holds("cancelled", 12, 8, 20, repeat_paid=0, same_report=False))

    def test_a_run_that_never_actually_crashed_fails(self):
        self.assertFalse(resume_holds("completed", 20, 0, 20, repeat_paid=0, same_report=True))


if __name__ == "__main__":
    unittest.main()
