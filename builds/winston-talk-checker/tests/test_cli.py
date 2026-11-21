"""Real subprocess CLI tests."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GOOD_FIXTURE = os.path.join(HERE, "fixtures", "good_deck.json")


def run_cli(*args):
    return subprocess.run(
        [sys.executable, os.path.join(ROOT, "cli.py"), *args],
        capture_output=True,
        text=True,
    )


class TestCli(unittest.TestCase):
    def test_real_good_deck_fixture_passes_everything(self):
        result = run_cli(GOOD_FIXTURE)
        self.assertEqual(result.returncode, 0)
        self.assertIn("11 pass, 0 warn, 0 fail, 0 not assessable", result.stdout)
        self.assertNotIn("[FAIL]", result.stdout)

    def test_fail_present_gives_nonzero_exit(self):
        bad = {
            "slides": [
                {"title": "Agenda", "bullets": ["topic A", "topic B"]},
                {"title": "Thank You", "notes": "thank you"},
            ]
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(bad, f)
            path = f.name
        try:
            result = run_cli(path)
            self.assertEqual(result.returncode, 1)
            self.assertIn("[FAIL]", result.stdout)
        finally:
            os.unlink(path)

    def test_missing_file_clean_error(self):
        result = run_cli("/tmp/definitely-does-not-exist-winston.json")
        self.assertEqual(result.returncode, 1)
        self.assertIn("File not found", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_malformed_json_clean_error(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write("{not json")
            path = f.name
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
