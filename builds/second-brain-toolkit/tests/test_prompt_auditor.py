import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompt_auditor import ALL_CHECKS, Status, audit, summarize

# The article's own real, verbatim custom-instructions text (Step 4).
REAL_ARTICLE_TEXT = (
    "You are my second brain. Answer only from the sources in this notebook. "
    'For every answer: start with the direct answer in 2-3 sentences, then '
    "give the supporting points with citations. If the sources don't contain "
    'the answer, say "Not in my sources" and suggest what kind of source I '
    "should add.\n\n"
    "Use plain English. No filler. Point out when two sources disagree."
)

# A naive instruction block missing every required property on purpose.
NAIVE_TEXT = "You are a helpful assistant. Answer my questions about these documents."


class TestRealArticleTextPassesEverything(unittest.TestCase):
    def test_all_checks_pass_or_warn_never_fail(self):
        findings = audit(REAL_ARTICLE_TEXT)
        fails = [f for f in findings if f.status == Status.FAIL]
        self.assertEqual(fails, [], f"real article text should not FAIL any check, got: {fails}")

    def test_every_check_fires_pass_on_real_text(self):
        # The real text implements all six properties -- every check should PASS.
        findings = audit(REAL_ARTICLE_TEXT)
        for f in findings:
            self.assertEqual(f.status, Status.PASS, f"{f.rule_id} should PASS on the real article text: {f.detail}")

    def test_summary_counts(self):
        counts = summarize(audit(REAL_ARTICLE_TEXT))
        self.assertEqual(counts, {"pass": 6, "fail": 0, "warn": 0})


class TestNaiveTextFailsOrWarnsOnEverything(unittest.TestCase):
    def test_no_check_passes(self):
        findings = audit(NAIVE_TEXT)
        passes = [f for f in findings if f.status == Status.PASS]
        self.assertEqual(passes, [], f"naive text should not PASS anything, got: {passes}")

    def test_load_bearing_checks_fail_not_warn(self):
        findings = {f.rule_id: f for f in audit(NAIVE_TEXT)}
        self.assertEqual(findings["grounding_only"].status, Status.FAIL)
        self.assertEqual(findings["fallback_phrase"].status, Status.FAIL)
        self.assertEqual(findings["citation_required"].status, Status.FAIL)

    def test_softer_checks_warn_not_fail(self):
        findings = {f.rule_id: f for f in audit(NAIVE_TEXT)}
        self.assertEqual(findings["suggests_missing_source_type"].status, Status.WARN)
        self.assertEqual(findings["disagreement_surfacing"].status, Status.WARN)
        self.assertEqual(findings["plain_english"].status, Status.WARN)


class TestIndividualCheckLogic(unittest.TestCase):
    def test_grounding_only_recognizes_variant_phrasing(self):
        from prompt_auditor import check_grounding_only

        self.assertEqual(
            check_grounding_only("Only answer from the documents I gave you.").status, Status.PASS
        )
        self.assertEqual(check_grounding_only("Answer whatever you think is best.").status, Status.FAIL)

    def test_fallback_phrase_specific_wording(self):
        from prompt_auditor import check_fallback_phrase

        self.assertEqual(
            check_fallback_phrase('If the sources don\'t contain the answer, say so.').status, Status.PASS
        )
        self.assertEqual(check_fallback_phrase("Just do your best.").status, Status.FAIL)

    def test_six_checks_registered(self):
        self.assertEqual(len(ALL_CHECKS), 6)


if __name__ == "__main__":
    unittest.main(verbosity=2)
