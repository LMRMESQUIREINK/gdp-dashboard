import unittest

from citation_tracker import Claim, CitationStatus, summarize, require_minimum_confirmed


def real_empowering_innovation_claims() -> list[Claim]:
    """The four footnoted quantitative claims from "Empowering Innovation"
    (2022), checked for real this round -- not a synthetic fixture."""
    return [
        Claim(
            text="Successful application of data science could lead to a 17.9% "
            "uptick in revenue for organizations with a 'mature' data science capability.",
            source_url="https://www.dataiq.co.uk/reports/delivering-value-through-data-science",
            status=CitationStatus.CONFIRMED_APPROXIMATE,
            reason="Matches a real 2021 DataIQ/Mango Solutions survey of 103 "
            "data practitioners: 'advanced'-tier orgs expected 17.9% of "
            "revenue from data science. It's a self-reported expectation, "
            "not a measured outcome -- and the ebook's own 'could lead to' "
            "hedge already matches that, not oversold.",
        ),
        Claim(
            text="If the median Fortune 1000 business increased the usability "
            "of its data by just 10%, it would translate to an increase of "
            "$2.01 billion in total revenue every year.",
            source_url="https://www.datascienceassn.org/sites/default/files/"
            "Measuring%20Business%20Impacts%20%20of%20Effective%20Data%20I.pdf",
            status=CitationStatus.UNCONFIRMED,
            reason="Named source URL is specific, but datascienceassn.org is "
            "blocked by this sandbox's egress proxy, and no independent "
            "secondary source repeats this exact figure either.",
        ),
        Claim(
            text="87 percent of business executives say frontline staff would "
            "benefit from improved insights.",
            source_url="https://media.thoughtspot.com/pdf/HBR-ThoughtSpot-The-New-Decision-Makers.pdf",
            status=CitationStatus.CONFIRMED_APPROXIMATE,
            reason="Real 2020 HBR Analytic Services report sponsored by "
            "ThoughtSpot (464 executives, 16 sectors); the 87% figure is "
            "confirmed via ThoughtSpot's own blog and Inc. coverage, though "
            "the exact survey-question wording varies slightly across "
            "restatements ('more successful' vs. 'benefit from improved insights').",
        ),
        Claim(
            text="CDP Public Cloud has enabled R&D staff to improve productivity "
            "by 20% to 40%, reducing preclinical trials from eight months at "
            "the high end down to two months at the low end. We've also "
            "doubled the probability that a development is successful at "
            "trials, moving from 5% to 10% likelihood. -- Chief data and "
            "analytics officer, pharmaceuticals",
            source_url="https://de.cloudera.com/content/dam/www/marketing/"
            "resources/analyst-reports/total-economic-impact-cdp-public-cloud.pdf",
            status=CitationStatus.SOURCE_LOCATED_UNVERIFIED,
            reason="A real Forrester Total Economic Impact study for CDP "
            "Public Cloud exists at this URL (confirmed via web search), but "
            "de.cloudera.com is blocked by this sandbox's egress proxy, so "
            "the specific preclinical-trial and trial-success figures inside "
            "it were not independently read.",
        ),
    ]


def real_idc_claim_from_edge_ebook() -> Claim:
    return Claim(
        text="IDC anticipates there will be at least 30 billion connected "
        "devices worldwide by 2020 -- providing 440 times more data than "
        "was possible in 2006.",
        source_url="https://www.cs.princeton.edu/courses/archive/spring13/"
        "cos598C/idc-the-digital-universe-in-2020.pdf",
        status=CitationStatus.CONTRADICTED,
        reason="The '30 billion devices by 2020' half is a real, well-"
        "documented IDC forecast. But the closest real IDC 'Digital "
        "Universe' figure found is a 300x growth from 2005 to 2020 (130 to "
        "40,000 exabytes) -- a different base year (2005, not 2006) and a "
        "different multiplier (300x, not 440x) from the same family of "
        "IDC studies.",
    )


class TestRealFindingsFromThisRound(unittest.TestCase):
    def test_empowering_innovation_claims_span_three_distinct_outcomes(self):
        claims = real_empowering_innovation_claims()
        counts = summarize(claims)
        self.assertEqual(counts["confirmed_exact"], 0)
        self.assertEqual(counts["confirmed_approximate"], 2)
        self.assertEqual(counts["source_located_unverified"], 1)
        self.assertEqual(counts["unconfirmed"], 1)
        self.assertEqual(counts["contradicted"], 0)

    def test_empowering_innovation_claims_clear_the_minimum_confirmed_bar(self):
        self.assertTrue(require_minimum_confirmed(real_empowering_innovation_claims(), minimum=1))

    def test_idc_claim_is_recorded_as_contradicted_not_unconfirmed(self):
        claim = real_idc_claim_from_edge_ebook()
        self.assertEqual(claim.status, CitationStatus.CONTRADICTED)
        counts = summarize([claim])
        self.assertEqual(counts["contradicted"], 1)
        self.assertEqual(counts["unconfirmed"], 0)


class TestDiscrimination(unittest.TestCase):
    def test_a_claim_with_no_reason_is_rejected(self):
        with self.assertRaises(ValueError):
            Claim("x", "https://example.com", CitationStatus.CONFIRMED_EXACT, reason="   ")

    def test_a_confirmed_claim_with_no_source_is_rejected(self):
        with self.assertRaises(ValueError):
            Claim("x", None, CitationStatus.CONFIRMED_EXACT, reason="found it")

    def test_an_unconfirmed_claim_may_have_no_source_at_all(self):
        # UNCONFIRMED doesn't require a source_url -- a document can make a
        # bare claim with no footnote whatsoever, which is its own finding.
        claim = Claim("bare assertion, no footnote", None, CitationStatus.UNCONFIRMED,
                       reason="no footnote given anywhere in the source document")
        self.assertIsNone(claim.source_url)

    def test_require_minimum_confirmed_fails_on_an_all_unconfirmed_set(self):
        claims = [
            Claim("a", None, CitationStatus.UNCONFIRMED, reason="no footnote"),
            Claim("b", None, CitationStatus.UNCONFIRMED, reason="no footnote"),
        ]
        self.assertFalse(require_minimum_confirmed(claims, minimum=1))

    def test_summarize_on_empty_list_is_all_zero(self):
        counts = summarize([])
        self.assertTrue(all(v == 0 for v in counts.values()))


if __name__ == "__main__":
    unittest.main()
