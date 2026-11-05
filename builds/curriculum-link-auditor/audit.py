#!/usr/bin/env python3
"""CLI: audit a curated list's claims about external repos against
locally-cloned copies of those repos.

Usage:
    python3 audit.py manifest.json --repos-dir /path/to/clones
    python3 audit.py manifest.json --repos-dir /path/to/clones --check-live

manifest.json shape: {"claims": [{"repo": "owner/name", "claimed_author":
"...", "claimed_lesson_count": N, "claimed_archived": true|false,
"claimed_structure_keywords": [...]}, ...]}. Any claim field may be
omitted; only the fields present are checked.

--repos-dir expects a subdirectory per repo (owner/name's last path
segment, e.g. "llm-course" for "mlabonne/llm-course") each containing a
README.md -- the shape every plain `git clone` produces.
"""

import argparse
import json
import os
import sys

from curriculum_auditor import RepoClaim, audit_manifest, check_repo_exists_live


def _load_claims(manifest_path: str) -> list[RepoClaim]:
    with open(manifest_path, encoding="utf-8") as f:
        data = json.load(f)
    return [
        RepoClaim(
            repo=entry["repo"],
            claimed_author=entry.get("claimed_author"),
            claimed_lesson_count=entry.get("claimed_lesson_count"),
            claimed_archived=entry.get("claimed_archived"),
            claimed_structure_keywords=entry.get("claimed_structure_keywords", []),
        )
        for entry in data["claims"]
    ]


def _load_readmes(claims: list[RepoClaim], repos_dir: str) -> dict[str, str]:
    readmes = {}
    for claim in claims:
        folder = claim.repo.split("/")[-1]
        for candidate in ("README.md", "readme.md", "Readme.md"):
            path = os.path.join(repos_dir, folder, candidate)
            if os.path.isfile(path):
                with open(path, encoding="utf-8") as f:
                    readmes[claim.repo] = f.read()
                break
    return readmes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", help="path to a claims manifest JSON file")
    parser.add_argument("--repos-dir", required=True, help="directory containing one cloned-repo folder per claim")
    parser.add_argument("--check-live", action="store_true", help="also check each repo exists via a live git ls-remote")
    args = parser.parse_args()

    claims = _load_claims(args.manifest)
    readmes = _load_readmes(claims, args.repos_dir)
    results = audit_manifest(claims, readmes)

    exit_code = 0
    for claim, result in zip(claims, results):
        print(f"\n== {result.repo} ==")
        if args.check_live:
            exists = check_repo_exists_live(claim.repo)
            print(f"  live existence: {'OK' if exists else 'NOT FOUND'}")
            if not exists:
                exit_code = 1
        for m in result.matches:
            print(f"  MATCH:     {m}")
        for m in result.mismatches:
            print(f"  MISMATCH:  {m}")
            exit_code = 1
        for f in result.flags:
            print(f"  FLAG:      {f}")

    print(f"\n{len(results)} repo(s) audited.")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
