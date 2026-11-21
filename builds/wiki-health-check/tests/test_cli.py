"""Real subprocess CLI tests."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

HEALTHY_WIKI = {
    "raw_sources": [
        {
            "name": "obsidian-pricing-page.md",
            "added_on": "2027-01-01",
            "topics": ["obsidian-setup"],
            "claims": [{"subject": "sync-price", "value": "$5/month", "asserted_on": "2027-01-01"}],
        }
    ],
    "notes": [
        {
            "topic": "obsidian-setup",
            "source_names": ["obsidian-pricing-page.md"],
            "claims": [{"subject": "sync-price", "value": "$5/month", "asserted_on": "2027-01-01"}],
        }
    ],
}

BROKEN_WIKI = {
    "raw_sources": [
        {
            "name": "march-meeting.md",
            "added_on": "2027-03-10",
            "topics": ["budget"],
            "claims": [{"subject": "budget-cap", "value": "$50k", "asserted_on": "2027-03-10"}],
        },
        {
            "name": "june-meeting.md",
            "added_on": "2027-06-02",
            "topics": ["budget"],
            "claims": [{"subject": "budget-cap", "value": "$80k", "asserted_on": "2027-06-02"}],
        },
    ],
    "notes": [
        {
            "topic": "q1-budget",
            "source_names": ["march-meeting.md"],
            "claims": [{"subject": "budget-cap", "value": "$50k", "asserted_on": "2027-03-10"}],
        }
    ],
}


def run_cli(*args):
    return subprocess.run(
        [sys.executable, os.path.join(ROOT, "cli.py"), *args],
        capture_output=True,
        text=True,
    )


def write_json(data):
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump(data, f)
    f.close()
    return f.name


class TestCli(unittest.TestCase):
    def test_healthy_wiki_reports_clean(self):
        path = write_json(HEALTHY_WIKI)
        try:
            result = run_cli(path)
            self.assertEqual(result.returncode, 0)
            self.assertIn("Clean", result.stdout)
        finally:
            os.unlink(path)

    def test_broken_wiki_reports_findings_and_nonzero_exit(self):
        path = write_json(BROKEN_WIKI)
        try:
            result = run_cli(path)
            self.assertEqual(result.returncode, 1)
            self.assertIn("[staleness]", result.stdout)
            self.assertIn("1 finding(s)", result.stdout)
        finally:
            os.unlink(path)

    def test_missing_file_clean_error(self):
        result = run_cli("/tmp/definitely-does-not-exist-wiki-health.json")
        self.assertEqual(result.returncode, 1)
        self.assertIn("File not found", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_malformed_json_clean_error(self):
        f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        f.write("{not json")
        f.close()
        try:
            result = run_cli(f.name)
            self.assertEqual(result.returncode, 1)
            self.assertIn("Malformed input", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
        finally:
            os.unlink(f.name)

    def test_bad_date_clean_error(self):
        bad = {"raw_sources": [{"name": "x.md", "added_on": "not-a-date", "topics": []}], "notes": []}
        path = write_json(bad)
        try:
            result = run_cli(path)
            self.assertEqual(result.returncode, 1)
            self.assertIn("Malformed input", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
        finally:
            os.unlink(path)

    def test_no_args_usage(self):
        result = run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertIn("Usage:", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
