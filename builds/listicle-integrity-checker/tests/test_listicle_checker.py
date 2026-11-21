"""
Tests for listicle_checker.py, run against REAL data transcribed from four
actual NocoBase-published articles (not synthetic fixtures), plus
discrimination fixtures proving the checks don't fire on clean input.

Run with: python3 -m pytest tests/ -v   (or just: python3 tests/test_listicle_checker.py)
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from listicle_checker import (
    Entry,
    Listicle,
    check_self_reference,
    check_link_collisions,
    check_metric_monotonicity,
    audit,
)


# ---------------------------------------------------------------------
# Real fixtures: the four articles, transcribed directly from the
# pasted source text (ranks/links/star counts as actually printed).
# ---------------------------------------------------------------------

ADMIN_DASHBOARD = Listicle(
    title="Top 11 Open-Source Admin Dashboard Projects on GitHub",
    publisher="NocoBase",
    published_date="2024-12-27",
    total_count=11,
    entries=[
        Entry("NocoBase", rank=11, title_link="https://www.nocobase.com/", metric_value=13000),
        Entry("APITable", rank=10, title_link="https://aitable.ai/", metric_value=13500),
        Entry("Vue-Admin-Better", rank=9, title_link=None, metric_value=17100),
        Entry("Gentelella", rank=8, title_link="https://marmelab.com/react-admin/", metric_value=20000),
        Entry("React-Admin", rank=7, title_link=None, metric_value=25100),
        Entry("Ngx-admin", rank=6, title_link="https://marmelab.com/react-admin/", metric_value=25300),
        Entry("Appsmith", rank=5, title_link="https://www.appsmith.com/", metric_value=35000),
        Entry("Tabler", rank=4, title_link="https://tabler.io/admin-template", metric_value=44200),
        Entry("AdminLTE", rank=3, title_link="https://adminlte.io/", metric_value=44200),
        Entry("NocoDB", rank=2, title_link="https://nocodb.com/", metric_value=50400),
        Entry("Vue-Element-Admin", rank=1, title_link=None, metric_value=88300),
    ],
)

ERP_CRM = Listicle(
    title="Top 10 Most-Starred Open-Source ERP and CRM on GitHub",
    publisher="NocoBase",
    published_date="2025-05-06",
    total_count=10,
    entries=[
        Entry("Odoo", rank=1, metric_value=42600),
        Entry("Twenty", rank=2, metric_value=27700),
        Entry("ERPNext", rank=3, metric_value=24700),
        Entry("Monica", rank=4, metric_value=22700),
        Entry("Huly Platform", rank=5, metric_value=20600),
        Entry("NocoBase", rank=6, metric_value=15500),
        Entry("Krayin CRM", rank=7, metric_value=14400),
        Entry("Akaunting", rank=8, metric_value=8600),
        Entry("Grocy", rank=9, metric_value=7500),
        Entry("iDURAR ERP/CRM", rank=10, metric_value=7300),
    ],
)

AI_AGENT_PLATFORMS = Listicle(
    title="10 Open-Source AI Agent Platforms for Business: From Automation to Internal Apps",
    publisher="NocoBase",
    published_date="2026-09-05",
    total_count=10,
    entries=[
        Entry("NocoBase", rank=1, metric_value=23900),
        Entry("Activepieces", rank=2, metric_value=24000),
        Entry("Kestra", rank=3, metric_value=28000),
        Entry("Windmill", rank=4, metric_value=17700),
        Entry("Coze Studio", rank=5, metric_value=21500),
        Entry("Langflow", rank=6, metric_value=153900),
        Entry("Dify", rank=7, metric_value=154000),
        Entry("MaxKB", rank=8, metric_value=22600),
        Entry("AnythingLLM", rank=9, metric_value=65400),
        Entry("RAGFlow", rank=10, metric_value=89700),
    ],
)

ENTERPRISE_AI = Listicle(
    title="10 Open-Source Enterprise AI Platforms You Can Self-Host",
    publisher="NocoBase",
    published_date="2026-11-17",
    total_count=10,
    entries=[
        Entry("NocoBase", rank=1, metric_value=24800),
        Entry("Activepieces", rank=2, metric_value=23700),
        Entry("Windmill", rank=3, metric_value=17500),
        Entry("Sim", rank=4, metric_value=29400),
        Entry("Mastra", rank=5, metric_value=28000),
        Entry("MaxKB", rank=6, metric_value=23200),
        Entry("RAGFlow", rank=7, metric_value=94000),
        Entry("LiteLLM", rank=8, metric_value=60000),
        Entry("MLflow", rank=9, metric_value=28800),
        Entry("Langfuse", rank=10, metric_value=32800),
    ],
)

ALL_FOUR = [ADMIN_DASHBOARD, ERP_CRM, AI_AGENT_PLATFORMS, ENTERPRISE_AI]


class TestSelfReference(unittest.TestCase):
    def test_nocobase_flagged_in_all_four_real_articles(self):
        for listicle in ALL_FOUR:
            with self.subTest(listicle=listicle.title):
                findings = check_self_reference(listicle)
                self.assertEqual(len(findings), 1)
                self.assertEqual(findings[0].matched_entry, "NocoBase")

    def test_admin_dashboard_reports_last_place_of_eleven(self):
        findings = check_self_reference(ADMIN_DASHBOARD)
        self.assertEqual(findings[0].rank, 11)
        self.assertEqual(findings[0].total_count, 11)
        self.assertIn("#11 of 11", findings[0].summary)

    def test_erp_crm_reports_rank_six_of_ten(self):
        findings = check_self_reference(ERP_CRM)
        self.assertEqual(findings[0].rank, 6)
        self.assertIn("#6 of 10", findings[0].summary)

    def test_clean_listicle_with_no_self_reference(self):
        clean = Listicle(
            title="Top 5 Open-Source Password Managers",
            publisher="Bitwarden",
            entries=[
                Entry("Vaultwarden", rank=1),
                Entry("KeePassXC", rank=2),
                Entry("Padloc", rank=3),
            ],
        )
        self.assertEqual(check_self_reference(clean), [])

    def test_short_name_does_not_false_positive(self):
        # A publisher named "Sim" should not flag every entry containing
        # the substring "sim" (e.g. "Simba") -- the >=4 char guard exists
        # for exactly this reason.
        listicle = Listicle(
            title="Top 3 Database Tools",
            publisher="Sim",
            entries=[Entry("Simba Driver Suite", rank=1), Entry("Postgres", rank=2)],
        )
        self.assertEqual(check_self_reference(listicle), [])


class TestLinkCollisions(unittest.TestCase):
    def test_real_gentelella_ngx_admin_collision_is_caught(self):
        findings = check_link_collisions(ADMIN_DASHBOARD)
        self.assertEqual(len(findings), 1)
        finding = findings[0]
        self.assertEqual(finding.url, "https://marmelab.com/react-admin/")
        self.assertEqual(set(finding.entries), {"Gentelella", "Ngx-admin"})
        self.assertIn("Gentelella", finding.summary)
        self.assertIn("Ngx-admin", finding.summary)

    def test_other_three_articles_have_no_link_collisions(self):
        # None of ERP_CRM/AI_AGENT_PLATFORMS/ENTERPRISE_AI carry title
        # links in this transcription (that article format used plain
        # GitHub/Website lines, not bracketed title links) -- confirming
        # the checker reports nothing where there is nothing to report.
        for listicle in (ERP_CRM, AI_AGENT_PLATFORMS, ENTERPRISE_AI):
            with self.subTest(listicle=listicle.title):
                self.assertEqual(check_link_collisions(listicle), [])

    def test_same_entry_reusing_its_own_link_is_not_a_collision(self):
        listicle = Listicle(
            title="Test",
            publisher="Nobody",
            entries=[
                Entry("ProjectA", rank=1, title_link="https://a.example.com/"),
                Entry("ProjectB", rank=2, title_link="https://b.example.com/"),
            ],
        )
        self.assertEqual(check_link_collisions(listicle), [])

    def test_three_way_collision_lists_all_three_names(self):
        listicle = Listicle(
            title="Test",
            publisher="Nobody",
            entries=[
                Entry("ProjectA", rank=1, title_link="https://x.example.com/"),
                Entry("ProjectB", rank=2, title_link="https://x.example.com/"),
                Entry("ProjectC", rank=3, title_link="https://x.example.com/"),
            ],
        )
        findings = check_link_collisions(listicle)
        self.assertEqual(len(findings), 1)
        self.assertEqual(set(findings[0].entries), {"ProjectA", "ProjectB", "ProjectC"})


class TestMetricMonotonicity(unittest.TestCase):
    def test_real_windmill_regression_between_ai_agent_and_enterprise_ai(self):
        findings = check_metric_monotonicity([AI_AGENT_PLATFORMS, ENTERPRISE_AI])
        windmill = [f for f in findings if f.project_name == "Windmill"]
        self.assertEqual(len(windmill), 1)
        f = windmill[0]
        self.assertEqual(f.earlier_value, 17700)
        self.assertEqual(f.later_value, 17500)
        self.assertEqual(f.direction, "decreased")
        self.assertAlmostEqual(f.delta, -200)

    def test_real_activepieces_regression_between_ai_agent_and_enterprise_ai(self):
        findings = check_metric_monotonicity([AI_AGENT_PLATFORMS, ENTERPRISE_AI])
        activepieces = [f for f in findings if f.project_name == "Activepieces"]
        self.assertEqual(len(activepieces), 1)
        f = activepieces[0]
        self.assertEqual(f.earlier_value, 24000)
        self.assertEqual(f.later_value, 23700)
        self.assertAlmostEqual(f.delta, -300)

    def test_real_ragflow_and_maxkb_increases_are_not_flagged(self):
        # RAGFlow 89700 -> 94000 and MaxKB 22600 -> 23200 both went UP,
        # which is the expected, unremarkable case under
        # expect_increasing=True -- they must NOT appear in the report.
        findings = check_metric_monotonicity([AI_AGENT_PLATFORMS, ENTERPRISE_AI])
        flagged_names = {f.project_name for f in findings}
        self.assertNotIn("RAGFlow", flagged_names)
        self.assertNotIn("MaxKB", flagged_names)

    def test_real_nocobase_growth_across_all_four_dated_articles_is_clean(self):
        # 13000 -> 15500 -> 23900 -> 24800: monotonically increasing, so
        # this project must generate ZERO regression findings across the
        # full real four-article timeline -- the honest negative result.
        findings = check_metric_monotonicity(ALL_FOUR)
        nocobase_findings = [f for f in findings if f.project_name == "NocoBase"]
        self.assertEqual(nocobase_findings, [])

    def test_undated_listicle_is_excluded_from_ordering(self):
        dated = Listicle(
            title="Dated", publisher="X", published_date="2026-01-01",
            entries=[Entry("Foo", rank=1, metric_value=100)],
        )
        undated = Listicle(
            title="Undated", publisher="X", published_date=None,
            entries=[Entry("Foo", rank=1, metric_value=50)],
        )
        # With the undated one excluded, there is only one dated snapshot
        # of "Foo", so there is nothing to compare -- no finding at all,
        # rather than silently treating None as earliest or latest.
        self.assertEqual(check_metric_monotonicity([dated, undated]), [])

    def test_discrimination_pair_regression_detected_vs_not(self):
        early = Listicle(
            title="Early", publisher="X", published_date="2026-01-01",
            entries=[Entry("Grower", rank=1, metric_value=100), Entry("Shrinker", rank=2, metric_value=100)],
        )
        late = Listicle(
            title="Late", publisher="X", published_date="2026-02-01",
            entries=[Entry("Grower", rank=1, metric_value=150), Entry("Shrinker", rank=2, metric_value=80)],
        )
        findings = check_metric_monotonicity([early, late])
        names = {f.project_name for f in findings}
        self.assertIn("Shrinker", names)
        self.assertNotIn("Grower", names)


class TestFullAudit(unittest.TestCase):
    def test_real_four_article_audit_matches_every_individual_finding(self):
        report = audit(ALL_FOUR)
        self.assertEqual(len(report.self_references), 4)  # one per article
        self.assertEqual(len(report.link_collisions), 1)  # Gentelella/Ngx-admin
        self.assertEqual(len(report.metric_regressions), 2)  # Windmill + Activepieces
        self.assertFalse(report.is_clean)

    def test_clean_single_listicle_audit_is_clean(self):
        clean = Listicle(
            title="Top 3 Open-Source Note Apps",
            publisher="An Unrelated Blog",
            entries=[Entry("Joplin", rank=1, title_link="https://joplinapp.org/"),
                     Entry("Logseq", rank=2, title_link="https://logseq.com/")],
        )
        report = audit([clean])
        self.assertTrue(report.is_clean)
        self.assertEqual(report.self_references, [])
        self.assertEqual(report.link_collisions, [])
        self.assertEqual(report.metric_regressions, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
