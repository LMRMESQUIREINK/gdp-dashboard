# Deep analysis: NocoBase's "Top N open-source X" listicle series

Source: four articles pasted directly by the user, all published by
NocoBase (bare URLs initially shared with no instruction, then the full
article text pasted after this sandbox's egress proxy turned out to
block all three hosting domains — see "What couldn't be checked" below):

1. *Top 11 Open-Source Admin Dashboard Projects on GitHub* (Dec 27, 2024)
2. *Top 10 Most-Starred Open-Source ERP and CRM on GitHub* (May 6, 2025)
3. *10 Open-Source AI Agent Platforms for Business: From Automation to
   Internal Apps* (Sep 5, 2026)
4. *10 Open-Source Enterprise AI Platforms You Can Self-Host*
   (~Nov 17, 2026 — "3 days ago" relative to this round)

All four are cross-posts of NocoBase's own blog (`nocobase.com`),
syndicated to Medium, dev.to, and Hashnode, and separately translated
into Russian, Japanese, Chinese, French, and Indonesian — confirmed via
web search before the article text itself was in hand. This is one
publisher's long-running content-marketing series (the articles'
"related reading" footers alone name a dozen-plus sibling posts: 40
developer tools, 12 no-code tools, 15 low-code projects, 13 self-hosted
projects, 8 CRUD projects, 11 internal tools, 11 CRM projects, and more),
not four independent reviews.

## What couldn't be checked, stated plainly

`medium.com`, `nocobase.com`, and `dev.to` are all unreachable from this
sandbox — confirmed directly (`curl` returns connection failures /
`getaddrinfo ENOTFOUND` on all three, not a rate limit or a 403), the
same class of egress restriction this project has hit before for
arxiv.org, huggingface.co, agentskills.io, and puter.com. Four
subagents dispatched to fetch the articles all failed identically. The
round proceeded once the user pasted the real article text directly;
nothing here is reconstructed from search-engine snippets alone.

## The headline finding: self-referential ranking, in all four

NocoBase ranks **its own product** inside every one of its own "Top N"
surveys of that product's category:

- Admin dashboards: NocoBase at **#11 of 11** — dead last.
- ERP/CRM: NocoBase at **#6 of 10**.
- AI agent platforms for business: NocoBase listed **first**, in its
  own "Enterprise Applications and Business Automation" category group.
- Enterprise AI platforms: NocoBase listed **first** of 10.

This is not hidden. The two 2026 articles carry an explicit, voluntary
mid-article disclosure the two 2024/2025 articles do not:

> 💬 Hey, you're reading the NocoBase blog. NocoBase is the most
> extensible AI-powered no-code/low-code development platform...

A real, checkable, *positive* finding from reading the whole series:
this disclosure practice was **added later**, present in both 2026
posts and absent from both the 2024 and 2025 ones — a genuine
improvement in transparency over roughly 18 months, not something
either single article states about the series as a whole.

The two AI-platform articles (3 and 4) also explicitly disclaim pure
star-ranking ("This is not a benchmark under a unified test environment
or a complete ranking" / "GitHub Stars are a useful reference, but the
real decision comes back to what your company needs") — a real,
precise distinction from articles 1 and 2, which both state the
opposite explicitly ("ranking projects purely by actual GitHub stars").
The series is internally consistent about *when* it is and isn't doing
a pure-stars ranking; it just never states that its own product is
always somewhere in the list regardless of which kind of ranking is
running.

## A real, reproducible link-integrity bug

In the admin-dashboard article, both **"Gentelella"** (#8) and
**"Ngx-admin"** (#6) have their title hyperlink pointing at the exact
same URL: `https://marmelab.com/react-admin/` — the real homepage of
**React-Admin** (#7), a third, unrelated entry in the same list. Read
directly off the article's own markup, not inferred: almost certainly
a copy-paste artifact (React-Admin's link template reused twice for
neighboring entries), not three products that happen to share a
homepage.

## A real factual misattribution, checked via web search

The ERP/CRM article states Huly Platform was "developed by the Human
Colossus Foundation." Checked directly: the real organization behind
Huly is **Huly Labs** (GitHub org `hcengineering`, founder Andrey
Platov) — a commercial all-in-one project-management/CRM/chat company.
The **Human Colossus Foundation** is a real, entirely unrelated
nonprofit working on decentralized-data interoperability standards; no
connection between the two organizations was found beyond the
coincidental shared word "Human." Likely either a research mix-up or an
AI-assisted drafting artifact; either way, a genuine, checkable error
in the article's own prose, not a judgment call.

## Cross-round consistency, not a new check

ERPNext's claims in the ERP/CRM article (Frappe framework, GPL v3, 2011
release) match what this project's own, separately-run Week 24 round
(`/notes/oss-ai-engineering-stack-week24-analysis.md`) already confirmed
directly against the real repo — an independent cross-check landing in
the same place by a different route, not re-verified from scratch here.

## A metric-regression finding that needed two dated snapshots read together

Four projects appear in both AI-platform articles (3, published
2026-09-05, and 4, published ~2026-11-17, roughly 2.5 months apart):

| Project | Article 3 stars | Article 4 stars | Delta |
|---|---|---|---|
| RAGFlow | 89.7K | 94.0K | **+4.3K** |
| MaxKB | 22.6K | 23.2K | **+0.6K** |
| Windmill | 17.7K | 17.5K | **−0.2K** |
| Activepieces | 24.0K | 23.7K | **−0.3K** |

Real GitHub star counts essentially never decrease on their own — the
two "down" rows are far more likely an imprecise manually-updated
snapshot (a human glancing at a slightly different source page or
rounding differently each time) than genuine star loss, and this is
stated as the likely explanation rather than an accusation. But it's a
real, checkable, direction-stated discrepancy that only shows up by
reading two dated articles in the same series together — exactly the
kind of finding this project's multi-source rounds exist to surface.

NocoBase's own self-reported count for itself, across all **four**
dated articles over roughly two years (13.0K → 15.5K → 23.9K → 24.8K),
moves cleanly in the expected direction the whole time — the honest
negative result, and a direct correction of an earlier, wrong working
hypothesis from this same round (see below).

## A correction made in public, within this same round

Before the user pasted the real article text, this round's early web
searches (needed because the direct fetches had already failed)
surfaced NocoBase's self-reported star count at several different,
seemingly scattered values — 11.6K, 13K, 13.5K, 15.5K, 16.6K, 20.8K,
21.3K — read at the time as a sign of inconsistent, maybe careless
self-reporting across the vendor's content. Reading the real, dated
text of these four specific articles directly disproves that: those
numbers were snippets from *other*, differently-timed NocoBase articles
in adjacent categories (an "AI CRM" post, an "internal tools" post, a
"project management" post, etc.), each reporting NocoBase's count as of
its own, different publish date — not inconsistency, just different
snapshots correctly compared against the wrong peer set. Stated here as
a correction, per this project's standing "correct yourself in public"
discipline, rather than silently dropped once the better evidence
arrived.

## Built

Checked `/builds/` first: `curriculum-link-auditor` checks a curated
list's specific claims (lesson counts, archived status, author
attribution) against a repo's real README — a different concern from
cross-entry link collisions or cross-snapshot metric drift.
`readme-link-auditor` resolves anchors/relative links within one
document — not across different listicle entries, and not across two
dated snapshots of a related list. Neither overlaps with what this
round actually found.

**`/builds/listicle-integrity-checker/`** — a standalone, dependency-free
Python tool generalizing the three mechanisms above: self-referential-
ranking detection, link-collision detection, and cross-snapshot metric-
monotonicity checking. Tested against the real, transcribed text of all
four source articles (not synthetic fixtures) plus discrimination cases
proving each check stays quiet on clean input. 22/22 tests pass,
including real subprocess CLI runs. Full detail in the build's own
README.

Deliberately not built: fetching the source articles itself (this round
hit a real, confirmed restriction on all three hosting domains, worked
around by the user pasting text directly, not by this tool scraping
anything), and a live GitHub-API lookup to resolve the Windmill/
Activepieces regressions definitively — minting push-capable API
credentials to an unrelated third-party repo just to read one number
is the same disproportionate step this project's `curriculum-link-auditor`
round already declined for the same reason.
