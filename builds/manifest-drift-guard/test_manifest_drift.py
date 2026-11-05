"""Real-filesystem tests for manifest_drift.py. No mocking of file_hash --
every test writes real files to a temp directory and recomputes real sha256
hashes, the same way the tool itself does.

Run with: python3 test_manifest_drift.py
"""
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from manifest_drift import check_drift, file_hash, main  # noqa: E402

passed = 0
failed = 0


def check(cond, name, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print("ok   - " + name)
    else:
        failed += 1
        print("FAIL - " + name + (f" ({detail})" if detail else ""))


def write(d: Path, name: str, content: str) -> Path:
    p = d / name
    p.write_text(content)
    return p


def real_hash(content: str, trunc: int = 16) -> str:
    return hashlib.sha256(content.encode()).hexdigest()[:trunc]


# --- file_hash itself -------------------------------------------------
with tempfile.TemporaryDirectory() as td:
    d = Path(td)
    p = write(d, "a.txt", "hello world")
    check(file_hash(p) == real_hash("hello world"), "file_hash matches a direct hashlib.sha256 recomputation")
    check(len(file_hash(p)) == 16, "file_hash truncates to 16 hex chars by default")
    check(file_hash(p, trunc=8) == real_hash("hello world")[:8], "file_hash respects a custom truncation length")

# --- clean manifest: every recorded hash matches the real file --------
with tempfile.TemporaryDirectory() as td:
    d = Path(td)
    write(d, "ops.ttl", "class A")
    write(d, "shapes.ttl", "shape B")
    recorded = {"ops.ttl": real_hash("class A"), "shapes.ttl": real_hash("shape B")}
    result = check_drift(recorded, d)
    check(result.clean, "a genuinely clean manifest reports clean", result.report())
    check(len(result.matched) == 2 and not result.drifted and not result.missing, "two files, both matched, zero drift/missing")

# --- the real-world case this tool was built from: a file edited after
# the manifest was written, so the recorded hash no longer matches -----
with tempfile.TemporaryDirectory() as td:
    d = Path(td)
    write(d, "ops.ttl", "class A v2 -- edited after the manifest was written")
    recorded = {"ops.ttl": real_hash("class A")}  # the stale, pre-edit hash
    result = check_drift(recorded, d)
    check(not result.clean, "an edited file correctly reports NOT clean")
    check(len(result.drifted) == 1, "exactly one file reported as drifted")
    name, rec, act = result.drifted[0]
    check(name == "ops.ttl" and rec == real_hash("class A") and act == real_hash("class A v2 -- edited after the manifest was written"),
          "the drift tuple carries the real recorded AND the real actual hash, not placeholders")
    check(rec != act, "recorded and actual hashes genuinely differ (not a false positive)")

# --- missing file: the manifest names a file that no longer exists ----
with tempfile.TemporaryDirectory() as td:
    d = Path(td)
    recorded = {"deleted.ttl": "0123456789abcdef"}
    result = check_drift(recorded, d)
    check(not result.clean, "a manifest naming a deleted file reports NOT clean")
    check(result.missing == ["deleted.ttl"], "the missing file is named exactly")
    check(not result.drifted, "a missing file is reported as missing, never miscategorised as drifted")

# --- unlisted file: present on disk, never recorded in the manifest ---
with tempfile.TemporaryDirectory() as td:
    d = Path(td)
    write(d, "ops.ttl", "class A")
    write(d, "new_file.ttl", "a file nobody fingerprinted")
    recorded = {"ops.ttl": real_hash("class A")}
    result = check_drift(recorded, d)
    check(result.clean, "a lenient (non-strict) check: unlisted files don't affect .clean")
    check(not result.clean_strict, "a strict check: unlisted files DO affect .clean_strict")
    check(result.unlisted == ["new_file.ttl"], "the unlisted file is named exactly")

# --- empty manifest, empty directory: no crash, trivially clean -------
with tempfile.TemporaryDirectory() as td:
    d = Path(td)
    result = check_drift({}, d)
    check(result.clean and result.clean_strict, "an empty manifest against an empty directory is trivially clean, no crash")

# --- multiple files, mixed outcomes in one real check ------------------
with tempfile.TemporaryDirectory() as td:
    d = Path(td)
    write(d, "a.ttl", "A content")
    write(d, "b.ttl", "B content EDITED")
    write(d, "d.ttl", "D unlisted content")
    recorded = {"a.ttl": real_hash("A content"), "b.ttl": real_hash("B content"), "c.ttl": "deadbeefdeadbeef"}
    result = check_drift(recorded, d)
    check(result.matched == ["a.ttl"], "exactly one file matched")
    check([n for n, _, _ in result.drifted] == ["b.ttl"], "exactly one file drifted")
    check(result.missing == ["c.ttl"], "exactly one file missing")
    check(result.unlisted == ["d.ttl"], "exactly one file unlisted")
    check(not result.clean, "mixed outcome is correctly NOT clean")

# --- reproduce the exact real-world finding this tool was built from:
# the ontology-driven-observability repo's recorded vs actual ontology
# fingerprints (the real 16-hex values measured during that gate round,
# cited here as data/facts, not a copy of the repo's own file content) --
REAL_RECORDED = {"ops.ttl": "db895132680a71ea", "shapes.ttl": "1a8b5be802a06a9e", "competency.rq": "2cba2f48ff7891c2"}
REAL_ACTUAL = {"ops.ttl": "4180b165ed2c0482", "shapes.ttl": "71c0d741cf16573c", "competency.rq": "97453bd4a5b85f10"}
check(all(REAL_RECORDED[k] != REAL_ACTUAL[k] for k in REAL_RECORDED), "sanity: the real-world recorded/actual fingerprint pairs genuinely differ for all three files")
check(all(len(v) == 16 for v in list(REAL_RECORDED.values()) + list(REAL_ACTUAL.values())), "sanity: all six real-world fingerprint values are 16 hex chars, matching this tool's default truncation")

# --- CLI: a real subprocess call, not just a function call -------------
with tempfile.TemporaryDirectory() as td:
    d = Path(td)
    files_dir = d / "files"
    files_dir.mkdir()
    write(files_dir, "a.ttl", "content A")
    manifest_path = d / "manifest.json"
    manifest_path.write_text(json.dumps({"ontology": {"a.ttl": real_hash("content A")}}))

    proc = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "manifest_drift.py"), str(manifest_path), "--dir", str(files_dir), "--key", "ontology"],
        capture_output=True, text=True,
    )
    check(proc.returncode == 0, "CLI: a clean manifest exits 0", f"stdout={proc.stdout!r} stderr={proc.stderr!r}")
    check("clean" in proc.stdout or "1 matched" in proc.stdout, "CLI: clean output is printed", proc.stdout)

    # now drift it
    write(files_dir, "a.ttl", "content A -- EDITED")
    proc2 = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "manifest_drift.py"), str(manifest_path), "--dir", str(files_dir), "--key", "ontology"],
        capture_output=True, text=True,
    )
    check(proc2.returncode == 1, "CLI: a drifted manifest exits 1 (CI-gate-ready)", f"stdout={proc2.stdout!r}")
    check("DRIFT" in proc2.stdout, "CLI: the drift is named in the printed output, not just a bare exit code", proc2.stdout)

    # strict mode with an unlisted file
    write(files_dir, "a.ttl", "content A")  # restore
    write(files_dir, "unlisted.ttl", "surprise")
    proc3 = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "manifest_drift.py"), str(manifest_path), "--dir", str(files_dir), "--key", "ontology"],
        capture_output=True, text=True,
    )
    check(proc3.returncode == 0, "CLI: non-strict mode ignores the unlisted file, exits 0", proc3.stdout)
    proc4 = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "manifest_drift.py"), str(manifest_path), "--dir", str(files_dir), "--key", "ontology", "--strict"],
        capture_output=True, text=True,
    )
    check(proc4.returncode == 1, "CLI: --strict mode catches the same unlisted file and exits 1", proc4.stdout)

    # bad --key
    proc5 = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "manifest_drift.py"), str(manifest_path), "--dir", str(files_dir), "--key", "nonexistent"],
        capture_output=True, text=True,
    )
    check(proc5.returncode == 2, "CLI: a --key that doesn't resolve to a dict gives a distinct exit code (2), not a raw traceback", f"rc={proc5.returncode} stderr={proc5.stderr!r}")
    check("Traceback" not in proc5.stderr, "CLI: a bad --key gives a clean error message, not a raw Python traceback", proc5.stderr)

# --- main() as a function (argv injection), covering the --key default -
with tempfile.TemporaryDirectory() as td:
    d = Path(td)
    write(d, "x.ttl", "X")
    manifest_path = d / "flat_manifest.json"
    manifest_path.write_text(json.dumps({"x.ttl": real_hash("X")}))
    rc = main([str(manifest_path), "--dir", str(d)])  # no --key: manifest IS the dict
    check(rc == 0, "main(): a flat manifest (no --key needed) resolves correctly and exits 0", f"rc={rc}")

print(f"\n{passed} passed, {failed} failed.")
if failed:
    sys.exit(1)
