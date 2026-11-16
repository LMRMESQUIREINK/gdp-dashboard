# Deep analysis: `morluto/rea`, via `ruthless-gate` this time

Source: `https://github.com/morluto/rea.git`, a bare repo link with the
`ruthless-gate` trigger phrase and no other instruction. This repo already
got this project's lighter `/analyze-and-ship` treatment in an earlier
round (`/notes/rea-reverse-engineer-anything-analysis.md`,
`/builds/go-buildinfo-extractor/`) — confirmed by title before touching
anything, and run again anyway because the earlier round used the
lightweight loop, never the stricter four-level gate. The full audit —
every finding with its evidence, a locked test suite, and a real
self-contained page — lives at `/builds/rea-gate/`; this file is the
project-convention summary pointer.

## What changed since this project's own last clone (29 days)

Re-cloned fresh rather than reused: the prior clone was 2026-10-18,
version 6.7.0 (confirmed exactly by the CHANGELOG's own dated entry).
This clone is 2026-11-16, version 6.9.0. TypeScript source files more
than doubled (3,235 → 6,905, +113.5%), test files grew even faster
(1,582 → 3,735, +136.0%), and the 6.9.0 release alone (17 days of work)
carries 244 precisely-counted unique PR links and 110 unique issue
links. The previously-credited Stryker mutation-testing configs are
still present, unchanged in kind. A new file, `SECURITY.md`, states an
explicit threat model with a direct prompt-injection-defense
instruction to downstream agents — not mentioned in this project's own
earlier reading of this repo.

## The headline finding: the README understates its own star count

The real surprise this round, found by checking the updated "Star
history" claim rather than assuming it just scaled up proportionally:
the README now says **"400,000 GitHub stars"** — but independent
trackers queried the same week (star-history.com, repowise.dev,
beeknoee.com) converge on **461,800–462,500** as of Nov 15–16, 60,000+
stars above what the repo's own README states. Direction: understatement,
not inflation — the opposite of this project's usual "marketing number
is padded" finding. Recomputing the growth rate from two dated
snapshots (453,918 on ~Nov 12 → ~462,000 on Nov 16) gives roughly
14.1k/week, the same order of magnitude as star-history.com's own
separately-stated "+19.4k this week" — the gap looks like README text
lagging genuine, fast growth, not a data error.

Two independent commentary pieces explicitly questioning star
authenticity surfaced in the same search (a dev.to post, a magazine
article with a "Fake Stars?" section) — both domains are network-blocked
from this sandbox (`getaddrinfo ENOTFOUND` for both), so neither could
be read. Reported as "a source raises this," never adopted as fact. The
understatement direction found above is stated as mild evidence against
the suspicion (a project padding its own number would typically round
up, not quote one already 60,000 below the live count) — not a
rebuttal, a weighed inference.

## A concrete engineering claim, checked and found partially precise

`src/python/PythonPycParser.ts` claims pinned CPython pyc magic numbers
3627 (3.14) and 3666 (3.15). 3627 for 3.14 is independently corroborated
(xdis's own magics table, a secondary blog's version table). But a
cited morluto/rea PR and CPython's own 3.14.0rc3 announcement confirm
3.14 actually churned through at least two earlier magic numbers across
its release-candidate cycle before landing on 3627 — REA's parser
correctly pins the final, shipped value, but not the narrower real
scope that implies. 3666 for 3.15 could not be independently
corroborated at all (3.15 is itself still pre-release); reported as
unconfirmed, not disputed.

## A genuine, repo-disclosed licensing grey area

`THIRD_PARTY_NOTICES.md` states the Windows native-addon build statically
links GCC runtime libraries under GPLv3 + the GCC Runtime Library
Exception 3.1, adding plainly: "the exception governs eligible compiled
combinations; it does not relicense the runtime itself under MIT." The
repo discloses the condition exists without separately certifying every
shipped release meets it — a real, named grey area in the rights table,
not a flat pass.

## What's built from this

Per the gate procedure's own method, the verdict page itself is the
deliverable — no new companion Python/JS tool this round, same call as
`wp-prompt-pack-gate`/`agentic-concepts-gate` (the "README text stale
against a live external metric" mechanism doesn't yet have a second,
clearly-needed use case elsewhere in this project the way the
ontology-gate's fingerprint-drift finding did). 181/181 assertions pass
on the real run, including the star-count understatement recomputed
independently from the tracker figures (not trusted from the ledger's
own prose), the growth-rate cross-check between two independently-dated
snapshots, and a real Chromium render at 1280px and 375px — one real
mobile-overflow bug found and fixed during verification (a slash-joined
file-name list in a coverage item had no word-break opportunity at
375px; fixed with `overflow-wrap:anywhere` on the coverage/evidence
CSS, the same fix class this project has hit before on long unbroken
tokens).
