#!/usr/bin/env python3
"""
CLI for listicle_checker.py.

Usage:
    python3 cli.py listicles.json

Input JSON shape (a list of listicle objects):
[
  {
    "title": "...",
    "publisher": "...",
    "published_date": "2026-09-05",   // optional, ISO 8601
    "total_count": 10,                 // optional
    "entries": [
      {"name": "...", "rank": 1, "title_link": "https://...", "metric_value": 23900}
    ]
  },
  ...
]
"""
import json
import sys

from listicle_checker import Entry, Listicle, audit


def load_listicles(path: str) -> list[Listicle]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    listicles = []
    for item in raw:
        entries = [
            Entry(
                name=e["name"],
                rank=e["rank"],
                title_link=e.get("title_link"),
                metric_value=e.get("metric_value"),
                metric_label=e.get("metric_label", "stars"),
            )
            for e in item["entries"]
        ]
        listicles.append(
            Listicle(
                title=item["title"],
                publisher=item["publisher"],
                entries=entries,
                published_date=item.get("published_date"),
                total_count=item.get("total_count"),
            )
        )
    return listicles


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 cli.py <listicles.json>", file=sys.stderr)
        return 2

    try:
        listicles = load_listicles(sys.argv[1])
    except FileNotFoundError:
        print(f"File not found: {sys.argv[1]}", file=sys.stderr)
        return 1
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Malformed input: {e}", file=sys.stderr)
        return 1

    report = audit(listicles)

    if report.is_clean:
        print(f"Clean: {len(listicles)} listicle(s) checked, no findings.")
        return 0

    if report.self_references:
        print(f"\n== Self-referential ranking ({len(report.self_references)}) ==")
        for f in report.self_references:
            print(f"  - {f.summary}")

    if report.link_collisions:
        print(f"\n== Link collisions ({len(report.link_collisions)}) ==")
        for f in report.link_collisions:
            print(f"  - {f.summary}")

    if report.metric_regressions:
        print(f"\n== Metric regressions ({len(report.metric_regressions)}) ==")
        for f in report.metric_regressions:
            print(f"  - {f.summary}")

    print()
    return 1


if __name__ == "__main__":
    sys.exit(main())
