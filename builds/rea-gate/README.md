# Gate: REA (Reverse Engineer Anything)

A `RUTHLESS GATE` audit of [`morluto/rea`](https://github.com/morluto/rea),
a public GitHub repository already given this project's lighter
`/analyze-and-ship` treatment in an earlier round
(`/notes/rea-reverse-engineer-anything-analysis.md`,
`/builds/go-buildinfo-extractor/`) — re-cloned fresh and run through the
stricter four-level gate this time, which that earlier round never used.

Open `index.html` locally (served, not `file://`), or run the tests below.
`data.js` is the full ledger; `test.js` is the suite that locks it.

## Coverage, before the verdict

6,905 TypeScript source files and the native Swift/C/Smali components
under `native/` were **not** read individually — only a small number of
named mechanisms were read in full: `src/python/PythonPycParser.ts` (the
CPython pyc magic-number table), the two Stryker configs, and
`SECURITY.md` / `DISCLAIMER.md` / `THIRD_PARTY_NOTICES.md` / `README.md`
in full. REA's own code was never executed in this sandbox — this
session's own auto-mode classifier denies running an untrusted cloned
repo's own code at all ("Code from External"), the same restriction
already documented in this project's `oil-oil/oil-ui` round. Every
mechanism-level finding below comes from reading source text and
cross-checking it against independently-sourced outside facts, never from
running REA. Two commentary pieces explicitly questioning star
authenticity were surfaced by web search but could not be fetched at all
(both domains are network-blocked from this sandbox) — reported as "a
source raises this," never read in full.

## The headline finding: the README understates its own star count

README.md line 444 states "400,000 GitHub stars." Independent trackers
queried the same week (star-history.com, repowise.dev, beeknoee.com)
converge on 461,800–462,500 as of Nov 15–16 2026 — 60,000+ **more** than
the repo's own README states. Direction: understatement, not
inflation — the opposite of this project's usual "marketing number is
padded" finding. The growth rate recomputed from two independently-dated
snapshots (453,918 on ~Nov 12 → ~462,000 on Nov 16) gives roughly
14.1k/week, the same order of magnitude as star-history.com's own
separately-stated "+19.4k this week" — consistent with the README text
simply lagging genuine, fast growth rather than a data error on either
side. Two independent commentary pieces (a dev.to post, a magazine
article with a "Fake Stars?" section) explicitly question the count's
authenticity, surfaced by search but network-blocked from this sandbox —
reported as a named, unread suspicion, with the understatement direction
above stated as mild evidence against it (a project padding its own
number would typically round up, not quote one already 60,000 below the
live count), never as a rebuttal.

## A concrete engineering claim, checked and found partially precise

`src/python/PythonPycParser.ts` pins CPython pyc magics 3627 (3.14) and
3666 (3.15). 3627 is independently corroborated (xdis's public magics
table, a secondary blog's version table). But a cited morluto/rea PR and
CPython's own 3.14.0rc3 release announcement confirm 3.14 actually
churned through at least two earlier magic numbers across its own
release-candidate cycle before landing on 3627 — REA's parser correctly
pins the final, shipped value, but a `.pyc` compiled under an early 3.14
release candidate is not recognized, a narrower real scope than the
module's own error text states at a glance. 3666 (3.15) could not be
independently corroborated at all (3.15 is itself still pre-release) —
reported as unconfirmed, not disputed.

## What else the audit found

15 findings across all four levels (10 credit, 5 stop) — an honest,
credit-heavy ratio for a source that is both genuinely growing fast and
disclosure-heavy about its own limits, not a forced balance. Credits
include: the Stryker mutation-testing configs still present after the
codebase more than doubled; `SECURITY.md`'s explicit, verbatim
prompt-injection-defense instruction to downstream agents; `DISCLAIMER.md`'s
lawful-use boundary held steady across 113%+ growth; and
`THIRD_PARTY_NOTICES.md` naming its own supply-chain gaps (two
declared-but-unverified license documents, one explicit LGPL dependency)
rather than folding everything into a blanket MIT claim. Stops include
the pyc-magic scope gap above, the unread fake-stars commentary, and a
genuine, repo-disclosed licensing grey area: the Windows native-addon
build statically links GCC runtime libraries under GPLv3 + the GCC
Runtime Library Exception 3.1, and the notices file itself states "the
exception governs eligible compiled combinations; it does not relicense
the runtime itself under MIT" without certifying every shipped release
meets it.

## Rights

`LICENSE`: MIT, copyright 2026 morluto. A rights table is included on the
page: MIT permits broad reuse/modification/redistribution of REA's own
authored code; `THIRD_PARTY_NOTICES.md`'s own text forbids using REA's or
any integrated product's name to imply affiliation/endorsement; one grey
row for the Windows-addon GPLv3-exception eligibility question above —
not legal advice. Consistent with this project's standing practice of
extracting the generalizable finding rather than copying a vendor's own
branded instance: nothing from the repo's own source files is committed
here. `source/measurements.json` holds only this round's own measurements
(counts, dates, short quoted phrases cited by file:line), never REA's
actual TypeScript — checked directly in `test.js` (no copied import/export/
require statements, no `PythonPycParser.ts`/`GoBinaryImage.ts` copied in).

## Proven

```bash
node test.js
```

**181/181 assertions pass**, including:

- Every finding carries real evidence, a valid provenance state
  (arithmetic/inference findings labelled `computed`, never `sourced`;
  the one genuinely unreadable source labelled `not-checked`, distinct
  from `source-is-silent`), and a valid level.
- The round's headline finding (the star-count understatement) is
  recomputed independently against every tracker figure in
  `source/measurements.json`, required to exceed the README's stated
  figure in each case, with the exact gap against `repowise.dev`
  recomputed and matched to the recorded high estimate.
- The independently-derived weekly growth rate is recomputed from two
  dated snapshots and cross-checked against star-history.com's own
  separately-stated weekly figure for the same order of magnitude.
- The 6.9.0 changelog's PR/issue velocity (244 PRs, 110 issues, 17 days)
  is recomputed to the exact `~14.35 PRs/day` figure.
- The pyc-magic claim is cross-checked structurally: the top of the real
  3.14 prerelease magic range is required to equal REA's own pinned
  final value, and the 3.15 claim is required to be recorded as
  uncorroborated rather than assumed correct by extension.
- A rights table with exactly one genuinely grey row, at least one
  permits and one forbids row, each citing a real basis.
- METAL HEAVY palette contrast (WCAG, independently recomputed) and ≥30°
  hue separation between go/caution/stop.
- A real Chromium render at 1280px and 375px (`review/screenshots/`):
  zero console errors, zero overflow, coverage renders above the verdict
  by real `getBoundingClientRect`, `--stop` never appears as a text
  colour on any rendered element.

**One real bug found and fixed during verification**: the first
Chromium pass failed with a 136px mobile overflow at 375px, traced to a
coverage item containing a slash-joined list of four filenames
(`SECURITY.md/DISCLAIMER.md/THIRD_PARTY_NOTICES.md/README.md`) with no
word-break opportunity — the `.evidence`/coverage-list CSS lacked the
`overflow-wrap`/`word-break` rules the rules table already had. Fixed by
adding those rules to the missing selectors (the same fix class this
project has hit on long unbroken tokens before) and adding spaces around
the slashes in the source text as a second line of defense; re-verified
clean on the next pass. A second, smaller fix made while writing the
suite itself: the stop-evidence assertion's first draft only recognized
file:line citations or shell commands as valid evidence, which correctly
failed on a stop whose real evidence is a cited PR number and an official
release announcement — widened to recognize named outside sources too,
per the gate's own "fix the value, never the threshold" rule.
