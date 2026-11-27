"""Real subprocess CLI tests -- not just in-process function calls."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIXTURE = os.path.join(HERE, "fixtures", "nocobase_four_articles.json")


def run_cli(*args):
    return subprocess.run(
        [sys.executable, os.path.join(ROOT, "cli.py"), *args],
        capture_output=True,
        text=True,
    )


class TestCli(unittest.TestCase):
    def test_real_four_article_fixture_reproduces_all_findings(self):
        result = run_cli(FIXTURE)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Self-referential ranking (4)", result.stdout)
        self.assertIn("Link collisions (1)", result.stdout)
        self.assertIn("Metric regressions (2)", result.stdout)
        self.assertIn("Gentelella", result.stdout)
        self.assertIn("Ngx-admin", result.stdout)
        self.assertIn("Windmill", result.stdout)
        self.assertIn("Activepieces", result.stdout)

    def test_clean_input_exits_zero(self):
        clean = [
            {
                "title": "Top 2 Open-Source Note Apps",
                "publisher": "An Unrelated Blog",
                "entries": [
                    {"name": "Joplin", "rank": 1},
                    {"name": "Logseq", "rank": 2},
                ],
            }
        ]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(clean, f)
            path = f.name
        try:
            result = run_cli(path)
            self.assertEqual(result.returncode, 0)
            self.assertIn("Clean:", result.stdout)
        finally:
            os.unlink(path)

    def test_missing_file_gives_clean_error_not_traceback(self):
        result = run_cli("/tmp/definitely-does-not-exist-12345.json")
        self.assertEqual(result.returncode, 1)
        self.assertIn("File not found", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_malformed_json_gives_clean_error_not_traceback(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write("{not valid json")
            path = f.name
        try:
            result = run_cli(path)
            self.assertEqual(result.returncode, 1)
            self.assertIn("Malformed input", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
        finally:
            os.unlink(path)

    def test_no_args_prints_usage(self):
        result = run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertIn("Usage:", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
