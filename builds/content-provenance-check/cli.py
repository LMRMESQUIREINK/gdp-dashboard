#!/usr/bin/env python3
"""
CLI for content-provenance-check.

Usage:
    python3 cli.py check <manifest.json>

manifest.json shape:
{
  "candidate": "path/to/candidate.txt",
  "disclosure": "path/to/disclosure.txt",
  "references": {"name": "path/to/reference.txt", ...},
  "markers": {"name": ["marker1", "marker2"], ...},
  "n": 8
}
"""
import json
import sys

from provenance_check import check_provenance


def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] != "check":
        print("Usage: python3 cli.py check <manifest.json>", file=sys.stderr)
        return 2

    manifest_path = sys.argv[2]
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except FileNotFoundError:
        print(f"File not found: {manifest_path}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Malformed manifest JSON: {e}", file=sys.stderr)
        return 1

    try:
        candidate = read_file(manifest["candidate"])
        disclosure = read_file(manifest["disclosure"])
        references = {name: read_file(path) for name, path in manifest["references"].items()}
    except FileNotFoundError as e:
        print(f"File not found: {e.filename}", file=sys.stderr)
        return 1
    except KeyError as e:
        print(f"Malformed input: missing key {e}", file=sys.stderr)
        return 1

    markers = manifest.get("markers", {})
    n = manifest.get("n", 8)

    report = check_provenance(candidate, references, disclosure, markers, n=n)

    if not report.reuse:
        print("No verbatim reuse found against any reference.")
        return 0

    for match in report.reuse:
        status = "disclosed" if report.disclosed.get(match.reference_name) else "UNDISCLOSED"
        print(
            f"[{status}] {match.reference_name}: {match.shared_ngrams}/{match.candidate_ngrams} "
            f"n-grams match ({match.overlap_ratio:.1%})"
        )
        for sample in match.sample_matches:
            print(f'    e.g. "{sample}"')

    if report.undisclosed_reuse:
        print(f"\n{len(report.undisclosed_reuse)} source(s) reused with no disclosure found.")
        return 1

    print("\nAll reused sources are disclosed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
