"""Real subprocess CLI tests."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REAL_EVAL = os.path.join(HERE, "fixtures", "transportive_eval.json")
SAMPLE_CLAIMS = os.path.join(HERE, "fixtures", "sample_claims.json")


def run_cli(*args):
    return subprocess.run(
        [sys.executable, os.path.join(ROOT, "cli.py"), *args],
        capture_output=True,
        text=True,
    )


class TestCli(unittest.TestCase):
    def test_one_disclosed_one_not_against_real_fixture(self):
        result = run_cli("check", REAL_EVAL, SAMPLE_CLAIMS)
        self.assertEqual(result.returncode, 1)
        self.assertIn("a4-opus-pass", result.stdout)
        self.assertNotIn("[UNDISCLOSED] a1-opus-pass", result.stdout)
        self.assertIn("1 undisclosed", result.stdout)

    def test_everything_disclosed_passes_clean(self):
        with open(SAMPLE_CLAIMS) as f:
            claims = json.load(f)
        for c in claims:
            c["disclosed"] = True
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(claims, f)
            path = f.name
        try:
            result = run_cli("check", REAL_EVAL, path)
            self.assertEqual(result.returncode, 0)
            self.assertIn("Clean", result.stdout)
        finally:
            os.unlink(path)

    def test_missing_results_file_clean_error(self):
        result = run_cli("check", "/tmp/does-not-exist-provisional-gate.json", SAMPLE_CLAIMS)
        self.assertEqual(result.returncode, 1)
        self.assertIn("File not found", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_bad_path_in_claims_clean_error(self):
        bad = [{"claim_id": "x", "text": "y", "path": "arms.nope.nope.nope", "disclosed": False}]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(bad, f)
            path = f.name
        try:
            result = run_cli("check", REAL_EVAL, path)
            self.assertEqual(result.returncode, 1)
            self.assertIn("Malformed input", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
        finally:
            os.unlink(path)

    def test_malformed_json_clean_error(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write("{not json")
            path = f.name
        try:
            result = run_cli("check", path, SAMPLE_CLAIMS)
            self.assertEqual(result.returncode, 1)
            self.assertIn("Malformed results JSON", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
        finally:
            os.unlink(path)

    def test_bad_usage(self):
        result = run_cli("check", "only-one-arg")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Usage:", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
