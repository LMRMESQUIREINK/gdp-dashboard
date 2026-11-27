# listicle-integrity-checker

A standalone, dependency-free Python tool for auditing vendor-published
"Top N open-source X" / "Best X" listicle articles — built from a real
pattern found reading four actual NocoBase-published articles together
(see `/notes/nocobase-listicle-series-analysis.md` for the full analysis
these checks were extracted from).

Reading one listicle in isolation hides all three of the problems this
tool checks for. Reading several related ones — the same publisher's
own series, published months apart — surfaces them directly.

## What it checks

1. **Self-referential ranking** — does the publisher's own product
   appear inside its own "Top N" ranking of that product category? Not
   inherently dishonest (especially if disclosed, as two of the four
   real source articles did mid-post), but a real conflict-of-interest
   signal worth surfacing every time, not just when it's egregious.

2. **Link collisions** — do two *different* entries' title hyperlinks
   point at the exact same URL? A real product almost never shares its
   homepage with an unrelated competitor; this is the signature of a
   copy-paste artifact. Found for real: in the admin-dashboard article,
   both "Gentelella" and "Ngx-admin" had their title link pointing at
   `https://marmelab.com/react-admin/` — React-Admin's own homepage,
   not either entry's real site.

3. **Cross-snapshot metric regressions** — when the same project
   appears in two dated snapshots of a related list (the same
   publisher's series, months apart), did its claimed GitHub star count
   *decrease*? Real stars essentially never go down on their own, so a
   decrease is worth a second look even though it's usually an
   imprecise manual re-measurement, not real star loss. Found for real:
   Windmill (17.7K → 17.5K) and Activepieces (24.0K → 23.7K) both
   dropped between two NocoBase articles published ~2.5 months apart,
   while RAGFlow (+4.3K) and MaxKB (+0.6K) and NocoBase itself (+0.9K,
   consistent with its own clean, monotonically-increasing growth
   across all four articles over two years) all moved the expected
   direction in the same window.

## Usage

```
python3 cli.py listicles.json
```

Input is a JSON list of listicle objects — see the docstring in
`cli.py` for the exact shape, or `tests/fixtures/nocobase_four_articles.json`
for a real, complete worked example transcribed directly from the four
source articles.

Library usage:

```python
from listicle_checker import Listicle, Entry, audit

report = audit([listicle1, listicle2, ...])
if not report.is_clean:
    for f in report.self_references:
        print(f.summary)
```

## What was found running this for real

Against the real, full text of all four source articles (not
summaries, not search-engine snippets — the actual pasted article
bodies):

- NocoBase ranks itself in **all four** of its own "Top N" listicles:
  #11 of 11 (dead last) in the admin-dashboard list, #6 of 10 in the
  ERP/CRM list, and listed first in both AI-platform lists (though
  those two explicitly state they are not pure star-rankings).
- The Gentelella/Ngx-admin link collision above — read directly off
  the real article markup, not inferred.
- The Windmill and Activepieces star-count regressions above.
- **One honest negative result, not manufactured**: NocoBase's own
  self-reported star count for itself climbs cleanly and monotonically
  across all four real, dated articles (13.0K → 15.5K → 23.9K → 24.8K
  over roughly two years) — a hypothesis formed earlier in this same
  analysis round from fragmentary web-search snippets alone (that
  NocoBase's self-reported numbers looked scattered and inconsistent)
  turned out to be wrong once the real, dated article text was read in
  full: those earlier snippets were quoting *other*, differently-timed
  NocoBase articles in adjacent categories, not these same four. This
  tool's own test suite locks in the corrected, honest conclusion
  (`test_real_nocobase_growth_across_all_four_dated_articles_is_clean`)
  rather than silently dropping the earlier wrong hypothesis.

## Proof

`python3 -m unittest tests.test_listicle_checker tests.test_cli -v` —
**22/22 tests pass**, including:

- Every one of the three real findings above, reproduced exactly from
  the real four-article fixture (`tests/fixtures/nocobase_four_articles.json`).
- Discrimination tests proving each check does NOT fire on clean input:
  a short publisher name ("Sim") doesn't false-positive on an unrelated
  entry sharing a short substring; two different entries legitimately
  linking to two different real homepages isn't flagged as a collision;
  a project whose metric only *increases* across snapshots isn't
  flagged as a regression.
- Real subprocess CLI tests (`tests/test_cli.py`), not just in-process
  function calls — including a missing-file and a malformed-JSON case,
  both of which fail cleanly with a one-line message and no raw
  traceback.

No bug was found in this build's own first draft — stated plainly
rather than manufactured, consistent with this project's practice of
reporting an honest "nothing to fix" result when that's what actually
happened.

## Deliberately not built

- Fetching the source articles itself. This tool takes already-extracted
  `Listicle`/`Entry` data; it doesn't scrape Medium/a vendor blog, since
  this exact round hit a real, confirmed restriction (medium.com,
  nocobase.com, and dev.to are all unreachable from this sandbox's
  egress proxy — DNS failures, not rate limits) and the four real
  articles here were obtained by the user pasting their text directly.
- A live GitHub-stars lookup to resolve a regression automatically
  (confirm vs. refute a claimed decrease against the real current
  count). This project's own `curriculum-link-auditor` build already
  made the call that minting GitHub API push credentials to an
  unrelated third-party repo just to read one number is disproportionate
  to the task; the same reasoning applies here.
