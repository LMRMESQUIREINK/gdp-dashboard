"""Tests for okf_navigator.py.

Two kinds of fixtures, kept in clearly separate directories:

- fixtures/real-google-samples/ -- actual files copied, unmodified, from
  Google's real GoogleCloudPlatform/knowledge-catalog repo (Apache 2.0; see
  UPSTREAM-LICENSE.md in that directory), used so this module is proven
  against real OKF content, not only invented fixtures.
- fixtures/auth-scenario/ -- a reconstruction of the article's own described
  worked example (an Authentication Service whose token-expiration setting
  changes, discovered by following links to Token Policy / API Gateway /
  Customer Login rather than loading an entire knowledge base). This is this
  build's own content, written from the article's narrative description of
  the scenario, not a verbatim transcript of file contents the article never
  actually printed -- stated plainly per this project's established
  precedent (ai-agent-testing-framework's requirement_analyzer.md
  placeholder) for the difference between a source's literal content and a
  reconstruction built from its own description.
"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from pathlib import Path

from okf_navigator import (
    Concept,
    OkfParseError,
    impact_report,
    is_stale,
    load_bundle,
    navigate,
    parse_concept,
    resolve_link,
    trust_tier,
)

FIXTURES = Path(__file__).parent / "fixtures"
REAL_SAMPLES = FIXTURES / "real-google-samples"
AUTH_SCENARIO = FIXTURES / "auth-scenario"


class TestParseConcept(unittest.TestCase):
    def test_missing_frontmatter_raises(self):
        with self.assertRaises(OkfParseError):
            parse_concept("# just a heading, no frontmatter\n", "bad.md")

    def test_malformed_yaml_raises(self):
        text = "---\ntype: [unterminated\n---\nbody\n"
        with self.assertRaises(OkfParseError):
            parse_concept(text, "bad.md")

    def test_non_mapping_frontmatter_raises(self):
        text = "---\n- just\n- a\n- list\n---\nbody\n"
        with self.assertRaises(OkfParseError):
            parse_concept(text, "bad.md")

    def test_parses_type_and_title(self):
        text = "---\ntype: Service\ntitle: Authentication Service\n---\nbody text\n"
        c = parse_concept(text, "auth.md")
        self.assertEqual(c.type, "Service")
        self.assertEqual(c.title, "Authentication Service")
        self.assertEqual(c.body.strip(), "body text")

    def test_extracts_links_from_body(self):
        text = (
            "---\ntype: Service\n---\n"
            "See [Token Policy](./token-policy.md) and "
            "[API Gateway](/services/api-gateway.md) and an "
            "[external site](https://example.com/not-a-concept).\n"
        )
        c = parse_concept(text, "auth.md")
        self.assertEqual(
            c.links,
            ("./token-policy.md", "/services/api-gateway.md", "https://example.com/not-a-concept"),
        )


class TestStatusDefault(unittest.TestCase):
    def test_absent_status_defaults_to_stable(self):
        c = parse_concept("---\ntype: Service\n---\nbody\n", "x.md")
        self.assertEqual(c.status, "stable")

    def test_explicit_status_is_respected(self):
        c = parse_concept("---\ntype: Service\nstatus: deprecated\n---\nbody\n", "x.md")
        self.assertEqual(c.status, "deprecated")


class TestResolveLink(unittest.TestCase):
    def test_external_url_is_not_a_concept_link(self):
        self.assertIsNone(resolve_link("a/b.md", "https://example.com/x"))
        self.assertIsNone(resolve_link("a/b.md", "http://example.com/x"))

    def test_non_markdown_target_is_not_a_concept_link(self):
        self.assertIsNone(resolve_link("a/b.md", "./diagram.png"))

    def test_absolute_bundle_relative_form(self):
        # SPEC.md 6.1's "recommended" form: a leading "/" is bundle-root-relative,
        # regardless of where the linking concept itself lives.
        self.assertEqual(resolve_link("deep/nested/file.md", "/services/auth.md"), "services/auth.md")

    def test_relative_same_directory(self):
        self.assertEqual(resolve_link("metrics/gross-margin.md", "./revenue.md"), "metrics/revenue.md")

    def test_relative_parent_directory(self):
        self.assertEqual(
            resolve_link("metrics/gross-margin.md", "../computations/gross-margin-period.md"),
            "computations/gross-margin-period.md",
        )

    def test_relative_from_root_level_file(self):
        self.assertEqual(resolve_link("index.md", "./services/auth.md"), "services/auth.md")

    def test_double_parent_traversal(self):
        self.assertEqual(
            resolve_link("a/b/c.md", "../../x.md"),
            "x.md",
        )


class TestTrustTier(unittest.TestCase):
    """SPEC.md 5.3's exact three-tier model."""

    def test_no_verified_key_is_unverified(self):
        c = parse_concept("---\ntype: Service\ngenerated: { by: process:ingest, at: 2026-01-01T00:00:00Z }\n---\nbody\n", "x.md")
        self.assertEqual(trust_tier(c), "unverified")

    def test_verified_by_non_human_only_is_machine_confirmed(self):
        text = (
            "---\ntype: Service\n"
            "verified:\n  - { by: process:nightly-check, at: 2026-01-02T00:00:00Z }\n"
            "---\nbody\n"
        )
        c = parse_concept(text, "x.md")
        self.assertEqual(trust_tier(c), "machine-confirmed")

    def test_verified_by_at_least_one_human_is_human_reviewed(self):
        text = (
            "---\ntype: Service\n"
            "verified:\n"
            "  - { by: process:nightly-check, at: 2026-01-02T00:00:00Z }\n"
            "  - { by: human:jsmith@acme, at: 2026-01-03T00:00:00Z }\n"
            "---\nbody\n"
        )
        c = parse_concept(text, "x.md")
        self.assertEqual(trust_tier(c), "human-reviewed")

    def test_verified_as_single_mapping_not_a_list(self):
        # The spec shows `verified` as a list, but a single-entry mapping
        # should still be handled rather than silently mis-tiered.
        text = "---\ntype: Service\nverified: { by: human:x, at: 2026-01-01T00:00:00Z }\n---\nbody\n"
        c = parse_concept(text, "x.md")
        self.assertEqual(trust_tier(c), "human-reviewed")

    def test_empty_verified_list_is_unverified(self):
        text = "---\ntype: Service\nverified: []\n---\nbody\n"
        c = parse_concept(text, "x.md")
        self.assertEqual(trust_tier(c), "unverified")

    def test_real_sample_gross_margin_is_human_reviewed(self):
        bundle = load_bundle(REAL_SAMPLES)
        c = bundle["gross-margin.md"]
        self.assertEqual(trust_tier(c), "human-reviewed")

    def test_real_sample_bad_question_flag_ratio_is_unverified(self):
        # This real Google-authored sample has `generated` but deliberately
        # no `verified` key at all -- the real-world unverified case.
        bundle = load_bundle(REAL_SAMPLES)
        c = bundle["bad_question_flag_ratio.md"]
        self.assertEqual(trust_tier(c), "unverified")


class TestStaleness(unittest.TestCase):
    def test_no_stale_after_returns_none(self):
        c = parse_concept("---\ntype: Service\n---\nbody\n", "x.md")
        self.assertIsNone(is_stale(c, datetime(2026, 1, 1, tzinfo=timezone.utc)))

    def test_now_before_stale_after_is_not_stale(self):
        c = parse_concept("---\ntype: Metric\nstale_after: 2026-12-31T00:00:00Z\n---\nbody\n", "x.md")
        self.assertFalse(is_stale(c, datetime(2026, 6, 1, tzinfo=timezone.utc)))

    def test_now_equal_to_stale_after_is_stale(self):
        # SPEC.md 5.5: stale iff now >= stale_after -- the boundary itself counts.
        c = parse_concept("---\ntype: Metric\nstale_after: 2026-12-31T00:00:00Z\n---\nbody\n", "x.md")
        self.assertTrue(is_stale(c, datetime(2026, 12, 31, 0, 0, 0, tzinfo=timezone.utc)))

    def test_now_after_stale_after_is_stale(self):
        c = parse_concept("---\ntype: Metric\nstale_after: 2026-12-31T00:00:00Z\n---\nbody\n", "x.md")
        self.assertTrue(is_stale(c, datetime(2027, 1, 1, tzinfo=timezone.utc)))

    def test_naive_now_is_treated_as_utc(self):
        c = parse_concept("---\ntype: Metric\nstale_after: 2026-12-31T00:00:00Z\n---\nbody\n", "x.md")
        self.assertTrue(is_stale(c, datetime(2027, 1, 1)))

    def test_real_sample_gross_margin_stale_after_year_end(self):
        bundle = load_bundle(REAL_SAMPLES)
        c = bundle["gross-margin.md"]
        self.assertFalse(is_stale(c, datetime(2026, 11, 26, tzinfo=timezone.utc)))
        self.assertTrue(is_stale(c, datetime(2027, 1, 1, tzinfo=timezone.utc)))


class TestLoadBundle(unittest.TestCase):
    def test_loads_all_real_samples(self):
        bundle = load_bundle(REAL_SAMPLES)
        self.assertIn("gross-margin.md", bundle)
        self.assertIn("bad_question_flag_ratio.md", bundle)

    def test_real_index_md_sample_has_no_frontmatter_and_is_not_a_concept(self):
        # A real, checked finding, not an assumption: the actual Google
        # sample index.md (bundles/stackoverflow/references/index.md) is a
        # plain bullet list of links with NO frontmatter block at all --
        # confirmed by reading the file directly. SPEC.md's index.md
        # convention is a lightweight directory-listing entry point, not a
        # concept carrying trust/staleness metadata, and this module
        # correctly treats it as non-concept content (skipped by
        # load_bundle, per the no-frontmatter rule above) rather than as a
        # malformed concept. Its own links are therefore not currently
        # walked by navigate() -- a real, stated scope boundary (see
        # README), not a silent gap.
        bundle = load_bundle(REAL_SAMPLES)
        self.assertNotIn("references-index.md", bundle)
        raw = (REAL_SAMPLES / "references-index.md").read_text(encoding="utf-8")
        self.assertFalse(raw.startswith("---\n"))

    def test_non_concept_md_file_is_skipped_not_raised(self):
        # Real bug found on the first real run against these fixtures:
        # load_bundle's first draft called parse_concept unconditionally on
        # every .md file, so the real upstream LICENSE.md copy sitting
        # alongside the real concept samples (a plain .md file with no OKF
        # frontmatter at all) raised OkfParseError and crashed the whole
        # load. A license file, README, or other plain markdown document is
        # simply not a concept -- it should be skipped quietly, not treated
        # as a malformed one. Fixed in load_bundle(), not by removing the
        # real fixture.
        bundle = load_bundle(REAL_SAMPLES)
        self.assertNotIn("UPSTREAM-LICENSE.md", bundle)

    def test_a_file_that_opens_frontmatter_but_is_malformed_still_raises(self):
        # The fix must not swallow genuine malformation -- only a file with
        # NO frontmatter block at all is skipped.
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "broken.md").write_text("---\ntype: [unterminated\n---\nbody\n", encoding="utf-8")
            with self.assertRaises(OkfParseError):
                load_bundle(root)

    def test_real_sample_has_expected_type_and_title(self):
        bundle = load_bundle(REAL_SAMPLES)
        c = bundle["gross-margin.md"]
        self.assertEqual(c.type, "Metric")
        self.assertEqual(c.title, "Gross Margin")


class TestNavigateAndBrokenLinks(unittest.TestCase):
    def _toy_bundle(self) -> dict[str, Concept]:
        return {
            "a.md": parse_concept(
                "---\ntype: Service\ntitle: A\n---\nSee [B](./b.md) and [missing](./nope.md).\n",
                "a.md",
            ),
            "b.md": parse_concept(
                "---\ntype: Service\ntitle: B\n---\nSee [C](./c.md) and back to [A](/a.md).\n",
                "b.md",
            ),
            "c.md": parse_concept("---\ntype: Service\ntitle: C\n---\nNo further links.\n", "c.md"),
        }

    def test_navigate_unknown_start_raises(self):
        bundle = self._toy_bundle()
        with self.assertRaises(KeyError):
            navigate(bundle, "missing.md", max_hops=2)

    def test_broken_link_is_tolerated_not_raised(self):
        # SPEC.md 6.1: "Consumers MUST tolerate broken links." Must not raise,
        # and the dangling target must simply not appear as a step.
        bundle = self._toy_bundle()
        steps = navigate(bundle, "a.md", max_hops=1)
        paths = [s.path for s in steps]
        self.assertIn("b.md", paths)
        self.assertNotIn("nope.md", paths)

    def test_bounded_depth_actually_stops(self):
        bundle = self._toy_bundle()
        one_hop = navigate(bundle, "a.md", max_hops=1)
        self.assertEqual({s.path for s in one_hop}, {"a.md", "b.md"})

        two_hops = navigate(bundle, "a.md", max_hops=2)
        self.assertEqual({s.path for s in two_hops}, {"a.md", "b.md", "c.md"})

    def test_cycle_does_not_revisit_or_loop_forever(self):
        # b.md links back to a.md (via the absolute form) -- must not be
        # revisited or cause infinite traversal.
        bundle = self._toy_bundle()
        steps = navigate(bundle, "a.md", max_hops=5)
        paths = [s.path for s in steps]
        self.assertEqual(paths.count("a.md"), 1)

    def test_depth_recorded_correctly(self):
        bundle = self._toy_bundle()
        steps = navigate(bundle, "a.md", max_hops=3)
        by_path = {s.path: s for s in steps}
        self.assertEqual(by_path["a.md"].depth, 0)
        self.assertEqual(by_path["b.md"].depth, 1)
        self.assertEqual(by_path["c.md"].depth, 2)
        self.assertEqual(by_path["b.md"].via, "a.md")
        self.assertEqual(by_path["c.md"].via, "b.md")


class TestAuthScenario(unittest.TestCase):
    """The article's own worked example, reconstructed from its narrative
    description (see module docstring for why this is a reconstruction, not
    a literal transcript): changing the Authentication Service's token
    expiration setting. Following documented links surfaces Token Policy,
    API Gateway, and Customer Login as the real impact surface -- without
    loading the entire knowledge base into context, the article's central
    "progressive disclosure" claim."""

    @classmethod
    def setUpClass(cls):
        AUTH_SCENARIO.mkdir(parents=True, exist_ok=True)
        files = {
            "authentication-service.md": (
                "---\ntype: Service\ntitle: Authentication Service\n"
                "verified:\n  - { by: human:secteam@acme, at: 2026-05-01T00:00:00Z }\n"
                "stale_after: 2027-01-01T00:00:00Z\n---\n"
                "# Authentication Service\n"
                "Issues and validates session tokens for all customer-facing apps.\n"
                "Token lifetime is governed by [Token Policy](./token-policy.md).\n"
                "Consumed directly by the [API Gateway](./api-gateway.md).\n"
            ),
            "token-policy.md": (
                "---\ntype: Reference\ntitle: Token Policy\n"
                "generated: { by: reference_agent/gemini-3.0, at: 2026-05-01T00:00:00Z }\n"
                "---\n# Token Policy\nSession tokens expire after 30 minutes of inactivity.\n"
            ),
            "api-gateway.md": (
                "---\ntype: Service\ntitle: API Gateway\n"
                "verified:\n  - { by: process:ci-contract-check, at: 2026-05-02T00:00:00Z }\n"
                "stale_after: 2026-01-01T00:00:00Z\n---\n"
                "# API Gateway\nRejects any request bearing an [Authentication Service](./authentication-service.md) "
                "token past its expiry. Fronted by [Customer Login](./customer-login.md).\n"
            ),
            "customer-login.md": (
                "---\ntype: Flow\ntitle: Customer Login\n---\n"
                "# Customer Login\nRedirects to re-authenticate against the "
                "[Authentication Service](/authentication-service.md) on a rejected token.\n"
            ),
            "unrelated-billing.md": (
                "---\ntype: Service\ntitle: Billing\n---\n"
                "# Billing\nNo documented relationship to authentication.\n"
            ),
        }
        for name, text in files.items():
            (AUTH_SCENARIO / name).write_text(text, encoding="utf-8")

    def test_impact_surface_within_two_hops_excludes_unrelated_service(self):
        bundle = load_bundle(AUTH_SCENARIO)
        steps = navigate(bundle, "authentication-service.md", max_hops=2)
        paths = {s.path for s in steps}
        self.assertEqual(
            paths,
            {"authentication-service.md", "token-policy.md", "api-gateway.md", "customer-login.md"},
        )
        self.assertNotIn("unrelated-billing.md", paths)

    def test_one_hop_misses_customer_login(self):
        # Customer Login is reachable only via API Gateway -- two hops away,
        # not one. This is the concrete "progressive disclosure" check: a
        # shallow query legitimately sees less than a deep one.
        bundle = load_bundle(AUTH_SCENARIO)
        steps = navigate(bundle, "authentication-service.md", max_hops=1)
        paths = {s.path for s in steps}
        self.assertNotIn("customer-login.md", paths)

    def test_impact_report_flags_api_gateway_as_stale(self):
        bundle = load_bundle(AUTH_SCENARIO)
        now = datetime(2026, 11, 26, tzinfo=timezone.utc)
        report = impact_report(bundle, "authentication-service.md", max_hops=2, now=now)
        gateway_line = next(line for line in report.splitlines() if "api-gateway.md" in line)
        self.assertIn("lifecycle=stale", gateway_line)
        auth_line = next(line for line in report.splitlines() if line.strip().startswith("[0]"))
        self.assertIn("lifecycle=fresh", auth_line)

    def test_impact_report_distinguishes_all_three_trust_tiers(self):
        bundle = load_bundle(AUTH_SCENARIO)
        now = datetime(2026, 11, 26, tzinfo=timezone.utc)
        report = impact_report(bundle, "authentication-service.md", max_hops=2, now=now)
        self.assertIn("authentication-service.md -- type=Service trust=human-reviewed", report)
        self.assertIn("api-gateway.md -- type=Service trust=machine-confirmed", report)
        self.assertIn("token-policy.md -- type=Reference trust=unverified", report)


if __name__ == "__main__":
    unittest.main()
