#!/usr/bin/env python3
"""
CLI for wiki-health-check.

Usage:
    python3 cli.py <wiki.json>

Input JSON shape:
{
  "raw_sources": [
    {"name": "...", "added_on": "YYYY-MM-DD", "topics": ["..."],
     "claims": [{"subject": "...", "value": "...", "asserted_on": "YYYY-MM-DD", "severity": "actionable"|"cosmetic"}]}
  ],
  "notes": [
    {"topic": "...", "source_names": ["..."],
     "claims": [{"subject": "...", "value": "...", "asserted_on": "YYYY-MM-DD", "severity": "actionable"|"cosmetic"}]}
  ],
  "min_mentions": 3
}
"""
import json
import sys
from datetime import date

from wiki_health import Claim, RawSource, Severity, WikiNote, run_health_check


def _parse_claim(raw: dict) -> Claim:
    return Claim(
        subject=raw["subject"],
        value=raw["value"],
        asserted_on=date.fromisoformat(raw["asserted_on"]),
        severity=Severity(raw.get("severity", "actionable")),
    )


def load(path: str) -> tuple[list[WikiNote], list[RawSource], int]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    raw_sources = [
        RawSource(
            name=s["name"],
            added_on=date.fromisoformat(s["added_on"]),
            topics=s.get("topics", []),
            claims=[_parse_claim(c) for c in s.get("claims", [])],
        )
        for s in raw.get("raw_sources", [])
    ]
    notes = [
        WikiNote(
            topic=n["topic"],
            source_names=n.get("source_names", []),
            claims=[_parse_claim(c) for c in n.get("claims", [])],
        )
        for n in raw.get("notes", [])
    ]
    return notes, raw_sources, raw.get("min_mentions", 3)


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 cli.py <wiki.json>", file=sys.stderr)
        return 2

    try:
        notes, raw_sources, min_mentions = load(sys.argv[1])
    except FileNotFoundError:
        print(f"File not found: {sys.argv[1]}", file=sys.stderr)
        return 1
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"Malformed input: {e}", file=sys.stderr)
        return 1

    findings = run_health_check(notes, raw_sources, min_mentions)
    if not findings:
        print("Clean -- nothing would mislead you today.")
        return 0

    for f in findings:
        print(f"[{f.kind}] {f.detail}")
    print(f"\n{len(findings)} finding(s).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
