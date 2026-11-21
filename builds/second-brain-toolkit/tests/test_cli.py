"""Real subprocess CLI tests."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

REAL_ARTICLE_TEXT = (
    "You are my second brain. Answer only from the sources in this notebook. "
    'For every answer: start with the direct answer in 2-3 sentences, then '
    "give the supporting points with citations. If the sources don't contain "
    'the answer, say "Not in my sources" and suggest what kind of source I '
    "should add.\n\n"
    "Use plain English. No filler. Point out when two sources disagree."
)


def run_cli(*args):
    return subprocess.run(
        [sys.executable, os.path.join(ROOT, "cli.py"), *args],
        capture_output=True,
        text=True,
    )


class TestCli(unittest.TestCase):
    def test_real_article_text_passes_cleanly(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write(REAL_ARTICLE_TEXT)
            path = f.name
        try:
            result = run_cli("audit-prompt", path)
            self.assertEqual(result.returncode, 0)
            self.assertIn("6 pass, 0 warn, 0 fail", result.stdout)
            self.assertNotIn("[FAIL]", result.stdout)
        finally:
            os.unlink(path)

    def test_naive_text_fails_with_nonzero_exit(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write("You are a helpful assistant. Answer my questions.")
            path = f.name
        try:
            result = run_cli("audit-prompt", path)
            self.assertEqual(result.returncode, 1)
            self.assertIn("[FAIL]", result.stdout)
        finally:
            os.unlink(path)

    def test_missing_file_clean_error(self):
        result = run_cli("audit-prompt", "/tmp/definitely-does-not-exist-second-brain.txt")
        self.assertEqual(result.returncode, 1)
        self.assertIn("File not found", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_lag_profile_real_json_output(self):
        result = run_cli("lag-profile")
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertEqual(data["worst_case_extra_delay_days"], 5)
        self.assertEqual(data["best_case_extra_delay_days"], -1)
        self.assertEqual(len(data["per_weekday"]), 7)

    def test_unknown_command(self):
        result = run_cli("nonsense")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Unknown command", result.stderr)

    def test_no_args_usage(self):
        result = run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertIn("Usage:", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
