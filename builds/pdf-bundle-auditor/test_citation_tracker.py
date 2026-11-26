import unittest

from citation_tracker import (
    Claim,
    CitationStatus,
    summarize,
    require_minimum_confirmed,
    find_cross_document_echoes,
)


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


def real_seven_elements_dollar_claim() -> Claim:
    """The exact same $2.01B / datascienceassn.org claim as
    real_empowering_innovation_claims()'s second entry, reappearing nearly
    verbatim -- with one added detail ("$56,000 more annual revenue per
    employee") -- in a second, separate Cloudera ebook."""
    return Claim(
        text="If the median Fortune 1000 firm increased the usability of its "
        "data by just 10%, equivalent to nearly $56,000 more annual revenue "
        "per employee, it would translate to $2.01B in additional total revenue.",
        source_url="https://www.datascienceassn.org/sites/default/files/"
        "Measuring%20Business%20Impacts%20%20of%20Effective%20Data%20I.pdf",
        status=CitationStatus.UNCONFIRMED,
        reason="Same unreachable datascienceassn.org source as the "
        "Empowering Innovation claim above; still no independent source "
        "found repeating this figure, now seen recycled across a second "
        "Cloudera document.",
        document="7-elements-of-a-winning-data-strategy",
    )


def real_newvantage_claims() -> list[Claim]:
    """Three claims from a different Cloudera ebook ("How to Build a
    Foundation for Exploratory Data Science with CML on AWS", 2022),
    footnoted to NewVantage Partners' real 2022 "Data and AI Executive
    Survey." All three checked out exactly against the primary report once
    actually found (a first search was contaminated by an unrelated firm's
    coincidentally similar 92.1% figure for a different question; a second,
    targeted search found the real NewVantage release)."""
    return [
        Claim(
            text="92.1% of organizations say they are achieving measurable "
            "results from their data and AI investments.",
            source_url="https://www.businesswire.com/news/home/20220103005036/"
            "en/NewVantage-Partners-Releases-2022-Data-And-AI-Executive-Survey",
            status=CitationStatus.CONFIRMED_EXACT,
            reason="NewVantage's own 2022 release states exactly 92.1% "
            "report realizing measurable business benefits from data/AI "
            "investments (94 Fortune 1000 / leading-organization respondents).",
            document="exploratory-data-science-cml-aws",
        ),
        Claim(
            text="92% of executives say cultural challenges are the greatest "
            "impediment to becoming more data-driven.",
            source_url="https://www.businesswire.com/news/home/20220103005036/"
            "en/NewVantage-Partners-Releases-2022-Data-And-AI-Executive-Survey",
            status=CitationStatus.CONFIRMED_APPROXIMATE,
            reason="Real figure is 91.9% citing culture as the greatest "
            "impediment (vs. 8.1% citing technology) -- rounds to 92% exactly.",
            document="exploratory-data-science-cml-aws",
        ),
        Claim(
            text="Just 27% said they've created a data-driven organization.",
            source_url="https://www.businesswire.com/news/home/20220103005036/"
            "en/NewVantage-Partners-Releases-2022-Data-And-AI-Executive-Survey",
            status=CitationStatus.CONFIRMED_APPROXIMATE,
            reason="Real 2022 figure is 26.5% -- rounds to 27%.",
            document="exploratory-data-science-cml-aws",
        ),
    ]


def real_globe_telecom_claim() -> Claim:
    return Claim(
        text="Globe Telecom manages 600PB of data with CML on AWS, driving "
        "66% year-over-year growth in mobile data volume.",
        source_url=None,
        status=CitationStatus.UNCONFIRMED,
        reason="The Globe Telecom / Cloudera customer-segmentation "
        "relationship itself is real and well-documented across many "
        "independent sources (AWS, Cloudera, Light Reading, PRNewswire), "
        "but none of them repeats either the 600PB or 66% YoY figure "
        "specifically -- the broad story checks out, these two numbers don't.",
        document="exploratory-data-science-cml-aws",
    )


class TestCrossDocumentEcho(unittest.TestCase):
    """The round's strongest finding: the same unreachable source backing
    the same unverified claim in two separate Cloudera documents is not
    independent corroboration."""

    def test_the_real_2point01b_claim_is_flagged_as_an_echo_across_two_documents(self):
        empowering_innovation_dollar_claim = real_empowering_innovation_claims()[1]
        self.assertIsNone(empowering_innovation_dollar_claim.document)
        # Give it a document label for this cross-document test, since the
        # original fixture function predates the `document` field.
        tagged = Claim(
            text=empowering_innovation_dollar_claim.text,
            source_url=empowering_innovation_dollar_claim.source_url,
            status=empowering_innovation_dollar_claim.status,
            reason=empowering_innovation_dollar_claim.reason,
            document="empowering-innovation",
        )
        echoes = find_cross_document_echoes([tagged, real_seven_elements_dollar_claim()])
        self.assertEqual(len(echoes), 1)
        echo = echoes[0]
        self.assertEqual(echo.source_url, tagged.source_url)
        self.assertEqual(
            set(echo.documents), {"empowering-innovation", "7-elements-of-a-winning-data-strategy"}
        )
        self.assertEqual(len(echo.claim_texts), 2)

    def test_newvantage_claims_are_not_flagged_as_echoes_even_though_they_share_a_source(self):
        # Three claims share one source_url across the same single document
        # -- not a cross-document echo at all (only one document), and two
        # of the three are CONFIRMED anyway.
        echoes = find_cross_document_echoes(real_newvantage_claims())
        self.assertEqual(echoes, [])

    def test_a_source_that_reaches_confirmed_anywhere_is_not_flagged(self):
        shared_url = "https://example.com/report.pdf"
        confirmed_elsewhere = Claim(
            "claim A", shared_url, CitationStatus.CONFIRMED_EXACT,
            reason="checked directly", document="doc-1",
        )
        unconfirmed_here = Claim(
            "claim B", shared_url, CitationStatus.UNCONFIRMED,
            reason="not independently checked", document="doc-2",
        )
        self.assertEqual(find_cross_document_echoes([confirmed_elsewhere, unconfirmed_here]), [])

    def test_a_within_one_document_repeat_is_not_an_echo(self):
        shared_url = "https://example.com/report.pdf"
        a = Claim("claim A", shared_url, CitationStatus.UNCONFIRMED, reason="r1", document="doc-1")
        b = Claim("claim B", shared_url, CitationStatus.UNCONFIRMED, reason="r2", document="doc-1")
        self.assertEqual(find_cross_document_echoes([a, b]), [])

    def test_two_unconfirmed_claims_from_two_documents_on_the_same_source_are_flagged(self):
        shared_url = "https://example.com/report.pdf"
        a = Claim("claim A", shared_url, CitationStatus.SOURCE_LOCATED_UNVERIFIED,
                  reason="r1", document="doc-1")
        b = Claim("claim B", shared_url, CitationStatus.UNCONFIRMED,
                  reason="r2", document="doc-2")
        echoes = find_cross_document_echoes([a, b])
        self.assertEqual(len(echoes), 1)
        self.assertEqual(set(echoes[0].documents), {"doc-1", "doc-2"})

    def test_claims_with_no_source_url_are_never_grouped(self):
        a = Claim("a", None, CitationStatus.UNCONFIRMED, reason="r", document="doc-1")
        b = Claim("b", None, CitationStatus.UNCONFIRMED, reason="r", document="doc-2")
        self.assertEqual(find_cross_document_echoes([a, b]), [])


class TestRealNewVantageClaimsAllConfirmed(unittest.TestCase):
    def test_all_three_newvantage_claims_are_confirmed(self):
        claims = real_newvantage_claims()
        counts = summarize(claims)
        self.assertEqual(counts["confirmed_exact"] + counts["confirmed_approximate"], 3)
        self.assertTrue(require_minimum_confirmed(claims, minimum=3))

    def test_a_real_relationship_can_still_carry_unconfirmed_specific_numbers(self):
        # Globe Telecom/Cloudera is real and well-documented; the 600PB and
        # 66% YoY figures specifically aren't -- a document-level claim can
        # be broadly true while a sharper number layered onto it isn't.
        globe = real_globe_telecom_claim()
        self.assertEqual(globe.status, CitationStatus.UNCONFIRMED)
        self.assertIsNone(globe.source_url)


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
