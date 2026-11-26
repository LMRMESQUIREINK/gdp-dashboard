import unittest
from datetime import date

from vintage_check import PdfRecord, check_spread, check_lapsed_forecasts


class TestRealBundleFromThisRound(unittest.TestCase):
    """The actual three PDFs uploaded together this round, with their real
    CreationDate metadata (read via `pdfinfo`), not synthetic dates."""

    def setUp(self):
        self.pdfs = [
            PdfRecord("the-great-ai-re-architecture", date(2026, 8, 6)),
            PdfRecord("msft-cloudera-edge-ebook", date(2019, 8, 9)),
            PdfRecord("empowering-innovation", date(2022, 7, 25)),
        ]

    def test_real_bundle_trips_the_default_spread_threshold(self):
        findings = check_spread(self.pdfs, max_spread_days=730)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].kind, "spread")
        self.assertIn("msft-cloudera-edge-ebook", findings[0].detail)
        self.assertIn("the-great-ai-re-architecture", findings[0].detail)
        self.assertIn("2554", findings[0].detail)  # real day count, recomputed by hand first

    def test_real_bundle_edge_ebook_forecast_has_lapsed(self):
        # The edge/IoT ebook forecasts "30 billion connected devices by 2020".
        pairs = [(self.pdfs[1], 2020)]
        findings = check_lapsed_forecasts(pairs, as_of=date(2026, 11, 26))
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].kind, "lapsed_forecast")
        self.assertIn("6 year(s)", findings[0].detail)

    def test_survey_report_own_forecast_has_not_lapsed(self):
        # The 2026 survey report makes no forward-dated forecast of this kind;
        # as a control, a forecast dated to a future year should not fire.
        pairs = [(self.pdfs[0], 2028)]
        findings = check_lapsed_forecasts(pairs, as_of=date(2026, 11, 26))
        self.assertEqual(findings, [])


class TestDiscrimination(unittest.TestCase):
    """A clean bundle -- PDFs created close together, with no lapsed
    forecasts -- must not be flagged."""

    def test_pdfs_created_the_same_week_are_not_flagged(self):
        pdfs = [
            PdfRecord("a", date(2026, 1, 1)),
            PdfRecord("b", date(2026, 1, 3)),
            PdfRecord("c", date(2026, 1, 5)),
        ]
        self.assertEqual(check_spread(pdfs), [])

    def test_single_pdf_cannot_have_a_spread(self):
        self.assertEqual(check_spread([PdfRecord("solo", date(2020, 1, 1))]), [])

    def test_empty_bundle_is_fine(self):
        self.assertEqual(check_spread([]), [])
        self.assertEqual(check_lapsed_forecasts([], as_of=date.today()), [])

    def test_custom_threshold_can_tighten_or_loosen(self):
        pdfs = [PdfRecord("a", date(2024, 1, 1)), PdfRecord("b", date(2026, 1, 1))]
        # ~2 years apart: flagged at a 1-year threshold, not at a 3-year one.
        self.assertEqual(len(check_spread(pdfs, max_spread_days=365)), 1)
        self.assertEqual(check_spread(pdfs, max_spread_days=365 * 3), [])


if __name__ == "__main__":
    unittest.main()
