#!/usr/bin/env python3
"""
CLI front end for patterns.py. Reads a text file (or stdin), reports every
AI-writing-tell match with its location and a one-line fix suggestion, and
exits 1 if the text is above the (configurable) density threshold — so it
can gate a build the same way the sales-page-engine/launch-pad skills'
don't-say-list grep already does for brand voice.

Usage:
    python3 humanizer.py draft.md
    python3 humanizer.py draft.md --max-per-1000-words 5
    cat draft.md | python3 humanizer.py -
"""
from __future__ import annotations

import argparse
import sys

from patterns import score


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="File to scan, or '-' for stdin")
    parser.add_argument(
        "--max-per-1000-words",
        type=float,
        default=None,
        help="Exit 1 if findings-per-1000-words exceeds this. Omit to just report.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of text")
    args = parser.parse_args()

    text = sys.stdin.read() if args.path == "-" else open(args.path, encoding="utf-8").read()
    result = score(text)

    if args.json:
        import json

        payload = {
            "word_count": result["word_count"],
            "finding_count": result["finding_count"],
            "findings_per_1000_words": result["findings_per_1000_words"],
            "by_category": result["by_category"],
            "em_dash_per_100_words": result["em_dash_per_100_words"],
            "findings": [
                {
                    "rule": f.rule_name,
                    "category": f.category,
                    "text": f.matched_text,
                    "start": f.start,
                    "end": f.end,
                    "suggestion": f.suggestion,
                }
                for f in result["findings"]
            ],
        }
        print(json.dumps(payload, indent=2))
    else:
        print(f"{result['word_count']} words, {result['finding_count']} finding(s) "
              f"({result['findings_per_1000_words']}/1000 words), "
              f"{result['em_dash_per_100_words']} em/en dashes per 100 words")
        for category, count in sorted(result["by_category"].items(), key=lambda kv: -kv[1]):
            print(f"  {category}: {count}")
        for f in result["findings"]:
            print(f"  [{f.rule_name}] {f.matched_text!r} — {f.suggestion}")

    if args.max_per_1000_words is not None and result["findings_per_1000_words"] > args.max_per_1000_words:
        print(
            f"\nFAIL: {result['findings_per_1000_words']}/1000 words exceeds the "
            f"{args.max_per_1000_words} threshold",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
