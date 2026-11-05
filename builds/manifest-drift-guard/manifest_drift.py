"""manifest-drift-guard: catch a fingerprint manifest that has gone stale.

Built from a real finding in the ontology-driven-observability ruthless-gate
round (/notes/ontology-driven-observability-gate-analysis.md): a repository
committed artifacts/run_manifest.json recording a sha256[:16] fingerprint
for each of its three ontology files, matching exactly what the notebook
printed when it last ran -- but the actually-committed ontology files no
longer hash to those recorded values, for all three files. The manifest
fingerprints itself; nothing re-checks the fingerprint against the files it
describes before trusting it. This module is that missing check, applicable
to any project that ships a "this is what we measured" manifest next to the
files it describes.

Zero dependencies beyond the standard library.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path


def file_hash(path: Path, trunc: int = 16) -> str:
    """sha256 over raw bytes, hex digest truncated to `trunc` chars.

    Matches the exact algorithm used by the real repository this tool was
    built from (notebook/ontology_observability.py's own file_hash()), so a
    manifest produced by that pattern can be checked without modification.
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:trunc]


@dataclass
class DriftResult:
    matched: list[str] = field(default_factory=list)
    drifted: list[tuple[str, str, str]] = field(default_factory=list)  # (name, recorded, actual)
    missing: list[str] = field(default_factory=list)  # listed in manifest, file absent
    unlisted: list[str] = field(default_factory=list)  # present on disk, not in manifest

    @property
    def clean(self) -> bool:
        return not self.drifted and not self.missing

    @property
    def clean_strict(self) -> bool:
        return self.clean and not self.unlisted

    def report(self) -> str:
        lines = []
        lines.append(f"  {len(self.matched)} matched, {len(self.drifted)} drifted, "
                      f"{len(self.missing)} missing, {len(self.unlisted)} unlisted")
        for name, recorded, actual in self.drifted:
            lines.append(f"  DRIFT   {name}: manifest says {recorded}, file actually hashes to {actual}")
        for name in self.missing:
            lines.append(f"  MISSING {name}: listed in manifest, no such file on disk")
        for name in self.unlisted:
            lines.append(f"  UNLISTED {name}: present on disk, not in manifest")
        return "\n".join(lines) if lines else "  clean"


def check_drift(recorded: dict[str, str], directory: Path, trunc: int = 16) -> DriftResult:
    """Compare a {filename: recorded_hash} manifest against the real files
    in `directory`. Recomputes every hash directly; never trusts the
    manifest's own claim about itself."""
    result = DriftResult()
    on_disk = {p.name for p in directory.iterdir() if p.is_file()} if directory.is_dir() else set()

    for name, recorded_hash in recorded.items():
        path = directory / name
        if not path.is_file():
            result.missing.append(name)
            continue
        actual_hash = file_hash(path, trunc=trunc)
        if actual_hash == recorded_hash:
            result.matched.append(name)
        else:
            result.drifted.append((name, recorded_hash, actual_hash))

    result.unlisted = sorted(on_disk - set(recorded.keys()))
    return result


class KeyPathError(Exception):
    pass


def _dig(data: dict, dotted_key: str | None):
    if not dotted_key:
        return data
    cur = data
    for part in dotted_key.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise KeyPathError(f"'{part}' not found while resolving --key '{dotted_key}'")
        cur = cur[part]
    return cur


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("manifest", type=Path, help="JSON file holding the recorded {filename: hash} mapping")
    parser.add_argument("--dir", type=Path, required=True, help="directory the manifest describes")
    parser.add_argument("--key", default=None, help="dotted path to the {filename: hash} dict inside the manifest JSON (default: the manifest IS that dict)")
    parser.add_argument("--trunc", type=int, default=16, help="hash truncation length (default 16, matching sha256[:16])")
    parser.add_argument("--strict", action="store_true", help="also fail on files present on disk but not listed in the manifest")
    args = parser.parse_args(argv)

    data = json.loads(args.manifest.read_text())
    try:
        recorded = _dig(data, args.key)
    except KeyPathError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if not isinstance(recorded, dict):
        print(f"error: --key '{args.key}' did not resolve to a {{filename: hash}} dict", file=sys.stderr)
        return 2

    result = check_drift(recorded, args.dir, trunc=args.trunc)
    print(result.report())

    if args.strict:
        return 0 if result.clean_strict else 1
    return 0 if result.clean else 1


if __name__ == "__main__":
    raise SystemExit(main())
