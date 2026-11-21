"""Real subprocess CLI tests."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIXTURES = os.path.join(HERE, "fixtures")
MANIFEST = os.path.join(FIXTURES, "manifest.json")


def run_cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, os.path.join(ROOT, "cli.py"), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


class TestCli(unittest.TestCase):
    def test_real_manifest_flags_undisclosed_reuse(self):
        # relative paths in the fixture manifest resolve against the
        # fixtures directory itself
        result = run_cli("check", "manifest.json", cwd=FIXTURES)
        self.assertEqual(result.returncode, 1)
        self.assertIn("[UNDISCLOSED] langchain-rag-from-scratch", result.stdout)
        self.assertIn("1 source(s) reused with no disclosure", result.stdout)

    def test_honest_disclosure_passes_clean(self):
        with open(MANIFEST) as f:
            manifest = json.load(f)
        with tempfile.TemporaryDirectory() as tmp:
            honest_path = os.path.join(tmp, "honest_disclosure.txt")
            with open(honest_path, "w") as f:
                f.write("This builds on LangChain's own rag-from-scratch notebook series.")
            manifest["disclosure"] = honest_path
            manifest_path = os.path.join(tmp, "manifest.json")
            with open(manifest_path, "w") as f:
                json.dump(manifest, f)
            result = run_cli("check", manifest_path, cwd=FIXTURES)
            self.assertEqual(result.returncode, 0)
            self.assertIn("disclosed", result.stdout)
            self.assertNotIn("UNDISCLOSED", result.stdout)

    def test_no_reuse_reports_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate_path = os.path.join(tmp, "candidate.txt")
            disclosure_path = os.path.join(tmp, "disclosure.txt")
            reference_path = os.path.join(tmp, "reference.txt")
            with open(candidate_path, "w") as f:
                f.write("a completely unrelated paragraph about gardening and houseplants in spring")
            with open(disclosure_path, "w") as f:
                f.write("no sources to disclose here")
            with open(reference_path, "w") as f:
                f.write("the quick brown fox jumps over the lazy dog near the riverbank every morning")
            manifest = {
                "candidate": candidate_path,
                "disclosure": disclosure_path,
                "references": {"ref": reference_path},
                "markers": {"ref": ["some marker"]},
            }
            manifest_path = os.path.join(tmp, "manifest.json")
            with open(manifest_path, "w") as f:
                json.dump(manifest, f)
            result = run_cli("check", manifest_path)
            self.assertEqual(result.returncode, 0)
            self.assertIn("No verbatim reuse found", result.stdout)

    def test_missing_manifest_clean_error(self):
        result = run_cli("check", "/tmp/definitely-does-not-exist-provenance.json")
        self.assertEqual(result.returncode, 1)
        self.assertIn("File not found", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_missing_referenced_file_clean_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = {
                "candidate": os.path.join(tmp, "does-not-exist.txt"),
                "disclosure": os.path.join(tmp, "also-missing.txt"),
                "references": {},
            }
            manifest_path = os.path.join(tmp, "manifest.json")
            with open(manifest_path, "w") as f:
                json.dump(manifest, f)
            result = run_cli("check", manifest_path)
            self.assertEqual(result.returncode, 1)
            self.assertIn("File not found", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_malformed_manifest_clean_error(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write("{not json")
            path = f.name
        try:
            result = run_cli("check", path)
            self.assertEqual(result.returncode, 1)
            self.assertIn("Malformed manifest JSON", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
        finally:
            os.unlink(path)

    def test_bad_usage(self):
        result = run_cli("check")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Usage:", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
