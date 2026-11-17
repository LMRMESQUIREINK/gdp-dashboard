"""Unattended batch scraping -- the triggerable unit a scheduler points at.

This sandbox can't run a real cron daemon or Windows Task Scheduler, so
following this project's own established convention (`/builds/
prop-firm-dashboard`'s "the daily-check script fits a scheduled job rather
than a long-running server"), this is the script itself, invocable by any
real scheduler, not a faked scheduling layer:

    python3 batch_scrape.py --urls urls.txt --fields title,price \
        --provider openai --out results.csv

`urls.txt` is one URL per line (blank lines and lines starting with "#"
ignored). `--out` ending in .xlsx writes Excel instead of CSV.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from api_management import LLMClient, MissingAPIKeyError
from scraper import FetchError, batch_scrape


def _read_urls(path: Path) -> list[str]:
    urls = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(line)
    return urls


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scrape a list of URLs unattended, one field set, one output sheet.")
    parser.add_argument("--urls", required=True, type=Path, help="Path to a file with one URL per line")
    parser.add_argument("--fields", required=True, help="Comma-separated field names to extract")
    parser.add_argument("--provider", default="openai", choices=["openai", "groq", "gemini"])
    parser.add_argument("--model", default=None)
    parser.add_argument("--max-pages", type=int, default=1)
    parser.add_argument("--use-selenium", action="store_true", help="Fetch via a real browser for JS-heavy sites")
    parser.add_argument("--stop-on-error", action="store_true", help="Stop the batch on the first fetch failure")
    parser.add_argument("--out", required=True, type=Path, help="Output path (.csv or .xlsx)")
    args = parser.parse_args(argv)

    if not args.urls.is_file():
        print(f"No such file: {args.urls}", file=sys.stderr)
        return 1

    urls = _read_urls(args.urls)
    if not urls:
        print(f"No URLs found in {args.urls}", file=sys.stderr)
        return 1

    fields = [f.strip() for f in args.fields.split(",") if f.strip()]
    if not fields:
        print("No fields given", file=sys.stderr)
        return 1

    try:
        client = LLMClient.for_provider(args.provider, model=args.model)
    except MissingAPIKeyError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    try:
        results = batch_scrape(
            urls,
            fields,
            client,
            max_pages=args.max_pages,
            use_selenium=args.use_selenium,
            on_url_error="raise" if args.stop_on_error else "skip",
        )
    except FetchError as exc:
        print(f"Batch stopped: {exc}", file=sys.stderr)
        return 1

    if not results:
        print("No pages were scraped.", file=sys.stderr)
        return 1

    rows = [{"url": r.url, "scraped_at": r.scraped_at, **r.fields} for r in results]
    df = pd.DataFrame(rows)

    if args.out.suffix.lower() == ".xlsx":
        df.to_excel(args.out, index=False, engine="openpyxl")
    else:
        df.to_csv(args.out, index=False)

    print(f"Wrote {len(df)} rows from {len(urls)} URL(s) to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
