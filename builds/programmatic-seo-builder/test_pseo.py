"""
Real tests: builds the real dataset (from the already-proven
PropFirmAccount, not synthetic rows), checks every page against the
thin-page guard with no overrides, and generates the actual files to a
temp directory, then reads them back and checks the real content —
internal links resolve to files that were actually written, and no two
pages render identical body text.

Run with:
    python3 -m unittest test_pseo -v
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from generate_pages import generate, page_body_text, render_page
from pseo_dataset import build_rows, unique_facts
from pseo_guard import check_no_duplicate_facts, check_page, word_count


class TestDataset(unittest.TestCase):
    def test_30_rows_from_5_tiers_and_6_symbols(self) -> None:
        rows = build_rows()
        self.assertEqual(len(rows), 30)

    def test_every_row_has_a_unique_slug(self) -> None:
        rows = build_rows()
        slugs = [r.slug for r in rows]
        self.assertEqual(len(slugs), len(set(slugs)))

    def test_no_duplicate_facts_across_real_rows(self) -> None:
        rows = build_rows()
        facts = [unique_facts(r) for r in rows]
        self.assertEqual(check_no_duplicate_facts(facts), [])


class TestThinPageGuard(unittest.TestCase):
    def test_every_real_page_passes_the_guard(self) -> None:
        rows = build_rows()
        for row in rows:
            report = check_page(page_body_text(row), unique_facts(row))
            self.assertFalse(report.is_thin, f"{row.slug}: {report.reasons}")

    def test_guard_actually_rejects_a_thin_page(self) -> None:
        report = check_page("Short page.", {"a": 1})
        self.assertTrue(report.is_thin)
        self.assertEqual(len(report.reasons), 2)

    def test_guard_accepts_a_page_meeting_both_minimums(self) -> None:
        long_text = " ".join(["word"] * 200)
        report = check_page(long_text, {"a": 1, "b": 2, "c": 3, "d": 4})
        self.assertFalse(report.is_thin)

    def test_word_count_is_accurate(self) -> None:
        self.assertEqual(word_count("one two three"), 3)


class TestRealGeneration(unittest.TestCase):
    def test_generates_real_files_with_real_internal_links(self) -> None:
        rows = build_rows()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            generate(out)

            page_files = {f.name for f in out.glob("*.html")}
            # 30 pages + 5 tier indexes + 6 symbol indexes + 1 top index
            self.assertEqual(len(page_files), 30 + 5 + 6 + 1)

            sample = rows[0]
            sample_html = (out / f"{sample.slug}.html").read_text(encoding="utf-8")
            self.assertIn(f"tier-{sample.tier.lower()}.html", sample_html)
            self.assertIn(f"symbol-{sample.symbol.lower()}.html", sample_html)

            # Every file an <a href="..."> points at inside this page must
            # actually exist on disk — a real, not assumed, internal-link check.
            import re

            for href in re.findall(r'href="([\w.-]+\.html)"', sample_html):
                self.assertTrue((out / href).exists(), f"linked file {href} was not generated")

    def test_no_two_pages_render_identical_body_text(self) -> None:
        rows = build_rows()
        bodies = [page_body_text(r) for r in rows]
        self.assertEqual(len(bodies), len(set(bodies)))

    def test_rendered_html_contains_the_pages_own_real_numbers(self) -> None:
        rows = build_rows()
        sample = rows[0]
        html = render_page(sample, rows)
        self.assertIn(f"${sample.starting_balance:,.0f}", html)
        self.assertIn(f"{sample.safe_contracts}", html)


if __name__ == "__main__":
    unittest.main()
