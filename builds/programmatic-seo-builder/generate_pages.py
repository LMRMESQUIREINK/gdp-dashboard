#!/usr/bin/env python3
"""
Generates real static HTML pages from pseo_dataset.py's rows: one page per
(tier, symbol) combination, each with genuinely distinct computed numbers,
internal links to a tier-index and a symbol-index page, and a top-level
index. Runs the thin-page guard on every page before writing anything, and
refuses to write if any page fails it or any two pages are duplicate
content — "strict about one thing: no thin pages," the article's own rule,
enforced as a real check, not a guideline.

Styling reuses the already-established RUTHLESS TRADING GOLD palette
(design-rules.md) since this dataset is real prop-firm-sizing data from
that portfolio — not a generic template with invented branding.

Usage:
    python3 generate_pages.py [output_dir]   # default: ./output
"""
from __future__ import annotations

import sys
from pathlib import Path

from pseo_dataset import PageRow, build_rows, unique_facts
from pseo_guard import check_no_duplicate_facts, check_page

STYLE = """
:root { --bg: #0A0A0A; --surface: #141414; --gold: #C9A84C; --gold-bright: #F0C040;
        --text: #E8E8E8; --text-dim: #A0A0A0; }
body { background: var(--bg); color: var(--text); font-family: 'IBM Plex Mono', monospace;
       max-width: 760px; margin: 0 auto; padding: 2rem 1.25rem; line-height: 1.6; }
h1 { color: var(--gold-bright); font-size: 1.4rem; }
table { width: 100%; border-collapse: collapse; margin: 1.5rem 0; }
td, th { border: 1px solid var(--gold); padding: 0.5rem 0.75rem; text-align: left; }
th { color: var(--gold-bright); }
a { color: var(--gold); }
.related { margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--surface); }
"""


def page_title(row: PageRow) -> str:
    return f"Can I Trade {row.symbol_name} on a ${row.tier} TPT Account?"


def page_description(row: PageRow) -> str:
    return (
        f"${row.tier} TPT account, {row.symbol} ({row.symbol_name}): daily loss limit "
        f"${row.daily_loss_limit:,.0f} ({row.daily_loss_in_points:.1f} {row.symbol} points), "
        f"{row.max_contracts} max contracts, {row.safe_contracts} under the 25% sizing rule."
    )


def page_body_text(row: PageRow) -> str:
    """The real body copy, as plain text (used for both the HTML body and
    the thin-page word-count check, so the check measures what a reader
    actually reads, not markup noise)."""
    return (
        f"On a ${row.tier:} TPT evaluation account, {row.symbol} ({row.symbol_name}) is tradeable "
        f"under the firm's standard rules. The starting balance is ${row.starting_balance:,.0f} "
        f"against a profit target of ${row.profit_target:,.0f}. "
        f"The daily loss limit is ${row.daily_loss_limit:,.0f}, which works out to "
        f"{row.daily_loss_in_points:.1f} {row.symbol} points before the day's trading is cut off — "
        f"a hard number worth knowing before sizing a position, not an estimate. "
        f"The end-of-day trailing drawdown floor is ${row.eod_trailing_dd:,.0f}, measured from the "
        f"account's high-water mark, not its starting balance — the detail most sizing guides "
        f"under-explain and the one that actually determines how much room there is left on a "
        f"losing streak. "
        f"The account's own rules allow up to {row.max_contracts} contracts of {row.symbol} at once; "
        f"the commonly used 25% sizing rule brings that down to {row.safe_contracts} contract(s) as "
        f"a day-to-day working size, trading some upside for a real cushion against a single bad day "
        f"wiping out the daily loss limit. The one-time evaluation fee for this tier is ${row.fee:,.0f}."
    )


def related_links(row: PageRow, rows: list[PageRow]) -> str:
    same_tier = [r for r in rows if r.tier == row.tier and r.symbol != row.symbol][:3]
    same_symbol = [r for r in rows if r.symbol == row.symbol and r.tier != row.tier][:3]
    items = [f'<li><a href="tier-{row.tier.lower()}.html">All {row.tier} contract limits</a></li>']
    items.append(f'<li><a href="symbol-{row.symbol.lower()}.html">All {row.symbol} tiers</a></li>')
    for r in same_tier:
        items.append(f'<li><a href="{r.slug}.html">{r.symbol} on ${r.tier}</a></li>')
    for r in same_symbol:
        items.append(f'<li><a href="{r.slug}.html">{row.symbol} on ${r.tier}</a></li>')
    return "<ul>" + "".join(items) + "</ul>"


def render_page(row: PageRow, rows: list[PageRow]) -> str:
    body_text = page_body_text(row)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{page_title(row)} | Contract Limits &amp; Daily Loss</title>
<meta name="description" content="{page_description(row)}">
<style>{STYLE}</style>
</head>
<body>
<h1>{page_title(row)}</h1>
<p>{body_text}</p>
<table>
<tr><th>Starting balance</th><td>${row.starting_balance:,.0f}</td></tr>
<tr><th>Profit target</th><td>${row.profit_target:,.0f}</td></tr>
<tr><th>Daily loss limit</th><td>${row.daily_loss_limit:,.0f} ({row.daily_loss_in_points:.1f} pts)</td></tr>
<tr><th>EOD trailing drawdown</th><td>${row.eod_trailing_dd:,.0f}</td></tr>
<tr><th>Max contracts</th><td>{row.max_contracts}</td></tr>
<tr><th>Safe contracts (25% rule)</th><td>{row.safe_contracts}</td></tr>
<tr><th>Evaluation fee</th><td>${row.fee:,.0f}</td></tr>
</table>
<nav class="related"><strong>Related</strong>{related_links(row, rows)}</nav>
</body>
</html>"""


def render_tier_index(tier: str, rows: list[PageRow]) -> str:
    tier_rows = [r for r in rows if r.tier == tier]
    items = "".join(f'<li><a href="{r.slug}.html">{r.symbol} ({r.symbol_name})</a></li>' for r in tier_rows)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>${tier} TPT Account: All Contract Limits</title>
<style>{STYLE}</style></head>
<body><h1>${tier} TPT Account — Contract Limits by Symbol</h1><ul>{items}</ul>
<p><a href="index.html">All tiers</a></p></body></html>"""


def render_symbol_index(symbol: str, rows: list[PageRow]) -> str:
    symbol_rows = [r for r in rows if r.symbol == symbol]
    items = "".join(f'<li><a href="{r.slug}.html">${r.tier} tier</a></li>' for r in symbol_rows)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{symbol} TPT Limits by Tier</title>
<style>{STYLE}</style></head>
<body><h1>{symbol} — TPT Contract Limits by Tier</h1><ul>{items}</ul>
<p><a href="index.html">All symbols</a></p></body></html>"""


def render_index(rows: list[PageRow]) -> str:
    items = "".join(f'<li><a href="{r.slug}.html">{r.symbol} on ${r.tier}</a></li>' for r in rows)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>TPT Contract Limits &amp; Daily Loss, by Tier and Symbol</title>
<style>{STYLE}</style></head>
<body><h1>TPT Contract Limits &amp; Daily Loss</h1><p>{len(rows)} pages, one per tier/symbol combination.</p>
<ul>{items}</ul></body></html>"""


def generate(output_dir: Path) -> None:
    rows = build_rows()

    all_facts = [unique_facts(r) for r in rows]
    duplicates = check_no_duplicate_facts(all_facts)
    if duplicates:
        raise SystemExit(f"Refusing to generate: duplicate-content pages found at indices {duplicates}")

    thin_pages = []
    for row in rows:
        report = check_page(page_body_text(row), unique_facts(row))
        if report.is_thin:
            thin_pages.append((row.slug, report.reasons))
    if thin_pages:
        raise SystemExit(f"Refusing to generate: thin page(s) found: {thin_pages}")

    output_dir.mkdir(parents=True, exist_ok=True)
    for row in rows:
        (output_dir / f"{row.slug}.html").write_text(render_page(row, rows), encoding="utf-8")
    for tier in sorted({r.tier for r in rows}, key=lambda t: int(t.rstrip("Kk"))):
        (output_dir / f"tier-{tier.lower()}.html").write_text(render_tier_index(tier, rows), encoding="utf-8")
    for symbol in sorted({r.symbol for r in rows}):
        (output_dir / f"symbol-{symbol.lower()}.html").write_text(render_symbol_index(symbol, rows), encoding="utf-8")
    (output_dir / "index.html").write_text(render_index(rows), encoding="utf-8")

    print(f"Wrote {len(rows)} pages + {len({r.tier for r in rows})} tier indexes + "
          f"{len({r.symbol for r in rows})} symbol indexes + 1 top index to {output_dir}")


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "output"
    generate(out)
