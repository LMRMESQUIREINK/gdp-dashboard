#!/usr/bin/env python3
"""
CLI for winston_checker.py.

Usage:
    python3 cli.py deck.json

Input JSON shape:
{
  "main_idea": "optional short phrase",
  "five_elements": {"symbol": "...", "slogan": "...", ...},   // optional
  "slides": [
    {"title": "...", "bullets": ["..."], "notes": "...", "has_logo_or_clutter": false}
  ]
}
"""
import json
import sys

from winston_checker import Deck, Slide, Status, run_all_checks, summarize


def load_deck(path: str) -> Deck:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    slides = [
        Slide(
            title=s.get("title", ""),
            bullets=s.get("bullets", []),
            notes=s.get("notes", ""),
            has_logo_or_clutter=s.get("has_logo_or_clutter"),
        )
        for s in raw.get("slides", [])
    ]
    return Deck(
        slides=slides,
        main_idea=raw.get("main_idea"),
        five_elements=raw.get("five_elements", {}),
    )


SYMBOLS = {
    Status.PASS: "PASS",
    Status.FAIL: "FAIL",
    Status.WARN: "WARN",
    Status.NOT_ASSESSABLE: "N/A ",
}


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 cli.py <deck.json>", file=sys.stderr)
        return 2

    try:
        deck = load_deck(sys.argv[1])
    except FileNotFoundError:
        print(f"File not found: {sys.argv[1]}", file=sys.stderr)
        return 1
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Malformed input: {e}", file=sys.stderr)
        return 1

    findings = run_all_checks(deck)
    for f in findings:
        print(f"[{SYMBOLS[f.status]}] {f.rule_id}: {f.detail}")

    counts = summarize(findings)
    print(f"\n{counts['pass']} pass, {counts['warn']} warn, {counts['fail']} fail, {counts['not_assessable']} not assessable")

    return 1 if counts["fail"] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
