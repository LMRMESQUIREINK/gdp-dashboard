import unittest

from citation_tracker import (
    Claim,
    CitationStatus,
    summarize,
    require_minimum_confirmed,
    find_cross_document_echoes,
    find_cross_document_text_echoes,
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


def real_globe_telecom_claim_round3() -> Claim:
    """The near-verbatim repeat of real_globe_telecom_claim() above, found in
    a THIRD round on a different Cloudera ebook ("How to Take AI Applications
    from Concept to Reality with CML on AWS", 2022-09-23 -- the same day, per
    each PDF's own CreationDate, as the ebook real_globe_telecom_claim() came
    from). Worded slightly differently ("driving a strategy that supports 66%
    year-over-year growth" vs. "driving 66% year-over-year growth") but the
    same two numbers, same customer, same claim, still with no source_url at
    all -- exactly the case find_cross_document_echoes() cannot catch,
    because there is no shared source_url to group on."""
    return Claim(
        text="Globe Telecom manages 600PB of data with CML on AWS, driving a "
        "strategy that supports 66% year-over-year growth in mobile data volume.",
        source_url=None,
        status=CitationStatus.UNCONFIRMED,
        reason="Same unconfirmed 600PB/66% YoY figures as the exploratory-"
        "data-science ebook's identical claim -- the Globe Telecom/Cloudera "
        "relationship is real, these two specific numbers still aren't "
        "independently corroborated anywhere, now seen recycled a second time.",
        document="concept-to-reality-cml-aws",
    )


def real_mckinsey_data_strategy_claim() -> Claim:
    """"How to Take AI Applications from Concept to Reality with CML on AWS"
    (2022) headlines, in large display type: "44% of high AI performers have
    a clear data strategy that supports and enables AI, compared to 21% of
    other respondents," footnoted to McKinsey's "The state of AI in 2020."
    The real 2020 report's own exhibit for this exact item ("a clear data
    strategy supports and enables AI") pairs 44% (AI high performers) with
    31% for all other respondents, confirmed by two independent secondary
    sources quoting the same exhibit -- not 21%. The 44% half is correct; the
    comparison figure is wrong, and wrong in a direction that inflates the
    apparent gap (44-21=23 points claimed vs. the real 44-31=13 points)."""
    return Claim(
        text="44% of high AI performers have a clear data strategy that "
        "supports and enables AI, compared to 21% of other respondents.",
        source_url="https://www.mckinsey.com/~/media/McKinsey/Business%20"
        "Functions/McKinsey%20Analytics/Our%20Insights/Global%20survey%20"
        "The%20state%20of%20AI%20in%202020/Global-survey-The-state-of-AI-in-2020",
        status=CitationStatus.CONTRADICTED,
        reason="McKinsey's own 2020 report pairs 44% (AI high performers) "
        "with 31% for all other respondents on this exact item -- confirmed "
        "via two independent secondary sources quoting the report's exhibit "
        "directly (mckinsey.com itself is blocked by this sandbox's egress "
        "proxy). The ebook's '21%' overstates the real 13-point gap as 23 "
        "points, nearly double.",
    )


def real_gartner_governance_claim() -> Claim:
    return Claim(
        text="80% of organizations seeking to scale digital business will "
        "fail because they do not take a modern approach to data and "
        "analytics governance.",
        source_url="https://www.gartner.com/en/newsroom/press-releases/"
        "2021-01-12-gartner-identifies-top-10-data-and-analytics-technology-trends-for-2021",
        status=CitationStatus.CONFIRMED_APPROXIMATE,
        reason="Matches a real Gartner forecast (2021 strategic planning "
        "assumption, tied to a 2021 Market Guide for Data and Analytics "
        "Governance Platforms) that 80% of organizations trying to scale "
        "digital business through 2025 will fail without modern data-and-"
        "analytics governance -- confirmed via independent secondary "
        "coverage (a PRNewswire release, Architecture & Governance "
        "Magazine). A DIFFERENT, later Gartner prediction (2024, for 2027) "
        "uses the same '80%' figure for a related but distinct claim -- not "
        "to be conflated with this one.",
    )


def real_algorithmia_deployment_claim() -> Claim:
    return Claim(
        text="40% of companies take more than 30 days to deploy a single ML model.",
        source_url="https://www.coriniumintelligence.com/hubfs/0284%20CDAO%20"
        "FS/Algorithmia_2020_State_of_Enterprise_ML.pdf?hsLang=en-gb",
        status=CitationStatus.CONFIRMED_APPROXIMATE,
        reason="Algorithmia's real 2020 State of Enterprise ML survey (745 "
        "respondents, Oct 2019) reports that on average 40% of companies "
        "say it takes more than a month to deploy an ML model into "
        "production -- 'more than a month' and 'more than 30 days' are the "
        "same claim, confirmed via the report's own hosted PDF.",
    )


def real_bt_group_roi_claim() -> Claim:
    return Claim(
        text="Cloudera provided an enterprise data hub to BT Group, which "
        "accelerates data velocity and fast-tracks delivery of new offerings "
        "to customers... seeing 200-250 percent ROI in one year.",
        source_url="https://www.cloudera.com/about/news-and-blogs/press-releases/"
        "2015-08-20-british-telecom-calls-cloudera.html",
        status=CitationStatus.SOURCE_LOCATED_UNVERIFIED,
        reason="Real, and traced to a specific quote from BT's own chief "
        "data architect in a 2015 Cloudera press release/slide deck ('Our "
        "one-year return on investment from Hadoop deployment is in the 200 "
        "percent to 250 percent range') -- but it's a vendor-channel "
        "customer quote, not an independently audited figure, and this "
        "2022 ebook presents a 7-year-old case study with no date given.",
    )


def real_western_union_blended_claims() -> list[Claim]:
    """"How to Take AI Applications from Concept to Reality with CML on AWS"
    presents Western Union's case as one seamless story ("processing 29
    transactions per second, Western Union's data set exceeds 100 terabytes
    ... 60X faster data loading") -- but the three numbers trace to at least
    two different, undated sources stitched together, not one unified
    Cloudera-verified figure set."""
    return [
        Claim(
            text="Western Union processes 29 transactions per second.",
            source_url="https://www.cloudera.com/about/news-and-blogs/press-releases/"
            "2014-02-18-western-union-leveraging-cloudera-data-analytics-solutions-to-enhance-the-customer-experience.html",
            status=CitationStatus.CONFIRMED_APPROXIMATE,
            reason="Real, from Cloudera's own Feb 2014 press release (29 "
            "transactions/second average across 200 countries, based on "
            "2013 data) -- a later 2018 Datanami piece gives 32/second for "
            "2017, so '29' is itself a 2013-era snapshot presented without "
            "a date in this 2022 ebook.",
        ),
        Claim(
            text="Western Union's data set exceeds 100 terabytes.",
            source_url="https://www.informationweek.com/software-services/"
            "informatica-self-service-platform-spots-sensitive-data",
            status=CitationStatus.SOURCE_LOCATED_UNVERIFIED,
            reason="This figure traces to an InformationWeek estimate "
            "('roughly 100 terabytes of data generated by 700 million "
            "transactions a year'), not to any Cloudera-published number -- "
            "a different outlet's figure blended into the same sentence as "
            "Cloudera's own '29 transactions per second' stat as if both "
            "came from one unified source.",
        ),
        Claim(
            text="60X faster data loading, enabling predictive analytics on "
            "structured and unstructured data sets at the time of the transaction.",
            source_url=None,
            status=CitationStatus.UNCONFIRMED,
            reason="No independent source found repeating a '60X faster "
            "data loading' figure for Western Union/Cloudera anywhere.",
        ),
    ]


class TestCrossDocumentTextEcho(unittest.TestCase):
    """This round's central finding: the Globe Telecom claim carries no
    source_url at all, so find_cross_document_echoes() (source_url-keyed)
    cannot catch it being recycled verbatim across two documents --
    find_cross_document_text_echoes() (text-keyed) closes that gap."""

    def test_find_cross_document_echoes_misses_the_globe_telecom_repeat(self):
        claims = [real_globe_telecom_claim(), real_globe_telecom_claim_round3()]
        self.assertEqual(find_cross_document_echoes(claims), [])

    def test_find_cross_document_text_echoes_catches_it(self):
        claims = [real_globe_telecom_claim(), real_globe_telecom_claim_round3()]
        findings = find_cross_document_text_echoes(claims)
        self.assertEqual(len(findings), 1)
        echo = findings[0]
        self.assertEqual(
            set(echo.documents), {"exploratory-data-science-cml-aws", "concept-to-reality-cml-aws"}
        )
        self.assertEqual(len(echo.claim_texts), 2)

    def test_a_confirmed_claim_is_not_flagged_even_if_text_echoes(self):
        shared_text = (
            "This specific sentence is long enough to clear the minimum length."
        )
        a = Claim(shared_text, "https://example.com/a", CitationStatus.CONFIRMED_EXACT,
                   reason="checked directly", document="doc-1")
        b = Claim(shared_text, None, CitationStatus.UNCONFIRMED,
                   reason="not checked", document="doc-2")
        self.assertEqual(find_cross_document_text_echoes([a, b]), [])

    def test_a_within_one_document_repeat_is_not_a_text_echo(self):
        shared_text = "This specific sentence is long enough to clear the minimum length."
        a = Claim(shared_text, None, CitationStatus.UNCONFIRMED, reason="r1", document="doc-1")
        b = Claim(shared_text, None, CitationStatus.UNCONFIRMED, reason="r2", document="doc-1")
        self.assertEqual(find_cross_document_text_echoes([a, b]), [])

    def test_short_claims_are_skipped_to_avoid_noise(self):
        a = Claim("CML on AWS", None, CitationStatus.UNCONFIRMED, reason="r1", document="doc-1")
        b = Claim("CML on AWS", None, CitationStatus.UNCONFIRMED, reason="r2", document="doc-2")
        self.assertEqual(find_cross_document_text_echoes([a, b]), [])

    def test_differently_worded_claims_about_the_same_fact_are_not_matched(self):
        a = Claim(
            "Globe Telecom manages 600PB of data on CML on AWS.", None,
            CitationStatus.UNCONFIRMED, reason="r1", document="doc-1",
        )
        b = Claim(
            "Globe Telecom is a leading provider in the Philippines using CDP.",
            None, CitationStatus.UNCONFIRMED, reason="r2", document="doc-2",
        )
        self.assertEqual(find_cross_document_text_echoes([a, b]), [])


class TestRealFindingsFromThirdRound(unittest.TestCase):
    """This round's own citation checks -- a genuine mix of outcomes, not a
    uniform verdict, matching this project's own established discipline."""

    def test_mckinsey_data_strategy_claim_is_contradicted_not_unconfirmed(self):
        claim = real_mckinsey_data_strategy_claim()
        self.assertEqual(claim.status, CitationStatus.CONTRADICTED)

    def test_gartner_and_algorithmia_claims_are_confirmed_approximate(self):
        self.assertEqual(real_gartner_governance_claim().status, CitationStatus.CONFIRMED_APPROXIMATE)
        self.assertEqual(real_algorithmia_deployment_claim().status, CitationStatus.CONFIRMED_APPROXIMATE)

    def test_bt_group_roi_is_source_located_unverified(self):
        self.assertEqual(real_bt_group_roi_claim().status, CitationStatus.SOURCE_LOCATED_UNVERIFIED)

    def test_western_union_blended_claims_have_three_distinct_outcomes(self):
        claims = real_western_union_blended_claims()
        counts = summarize(claims)
        self.assertEqual(counts["confirmed_approximate"], 1)
        self.assertEqual(counts["source_located_unverified"], 1)
        self.assertEqual(counts["unconfirmed"], 1)

    def test_third_round_claims_as_a_whole_clear_the_minimum_confirmed_bar(self):
        claims = (
            [real_mckinsey_data_strategy_claim(), real_gartner_governance_claim(),
             real_algorithmia_deployment_claim(), real_bt_group_roi_claim()]
            + real_western_union_blended_claims()
        )
        self.assertTrue(require_minimum_confirmed(claims, minimum=2))


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
