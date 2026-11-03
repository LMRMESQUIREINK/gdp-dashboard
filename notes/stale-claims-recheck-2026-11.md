# Re-checking this project's own previously-flagged unverified claims

A follow-up pass, not a new source: re-checking three specific
self-reported figures this project flagged in earlier rounds as
`source-is-silent`/unreconciled, to see whether anything has drifted
since the original check. All three re-checked live (web search plus,
for n8n, a fresh shallow clone) rather than re-stated from memory.

## `bytedance/deer-flow` — "41,700 stars" (claimed #1 GitHub Trending, Feb 28 2026)

Original round (`/notes/deer-flow-analysis.md`) flagged this as
`source-is-silent`: a web search found the same figure mirrored across
other sites, reading as an echo of the project's own announcement, not
an independent second measurement.

Re-checked now: no single figure from Feb 28 2026 is independently
confirmable even today. Sources disagree with each other on multiple
dates — one directory page cites "nearly 30K" at the moment it hit #1
Trending; a later snapshot (indexed June 7, 2026) shows 67,767 stars;
other write-ups independently cite "59k+" and "over 72,000." The
figures are inconsistent between sources, but all point the same
direction: real, continued growth past the original claim, not evidence
the original number was fabricated. Conclusion: still `source-is-silent`
on the specific Feb 28 figure — that status hasn't changed and
realistically can't be settled retroactively — but the broader "this
repo is popular and growing fast" claim is corroborated by multiple
independent, mutually-disagreeing-on-specifics sources, which is weaker
confirmation than the REA case below but still not nothing.

## `morluto/rea` — "300,000 GitHub stars"

Original round (`/notes/rea-reverse-engineer-anything-analysis.md`)
checked this via web search at the time: independent sources (an
Italian fact-check site, ossinsight.io, trendshift.io) corroborated
real growth from ~30,000 (Oct 9) to ~234,000 (Oct 14), and judged
"~300,000 by the clone date [Oct ~22] plausible" rather than confirmed.

Re-checked now: a later source (ASCII.jp, published Oct 21, citing the
GitHub API directly for its underlying numbers) reports the repo
**surpassed 300,000 stars on October 17** and reached **347,802 by
October 21** — a stronger, more precise independent confirmation than
was available in the original round. The original "plausible" judgment
holds up and was, if anything, conservative: the real count had already
cleared 300,000 several days before this project's own clone date, not
merely approaching it. One new caveat this re-check surfaced that the
original round didn't have: the same fact-check source that reported
the 234,477-star figure also states "nobody can say how many of those
stars come from real readers" — a real, named concern about possible
star-count inflation that applies to the underlying number itself, not
just to whether this project reported it correctly. Worth folding into
the original analysis as an addendum rather than silently added here.

## `n8n-io/n8n` — "1,500+ integrations"

Original round (`/notes/oss-ai-engineering-stack-week21-analysis.md`)
found a real, stated discrepancy: n8n's README claims "1500+
integrations" in three places, but a direct count of the real core
package (`packages/nodes-base/nodes`) found only 308 node directories
and 563 total `.node.ts` files — left explicitly unreconciled (most
likely a counting-methodology difference, e.g. per-operation counting
or an uncounted community-node ecosystem, not an accusation of a false
claim).

Re-checked now with a fresh shallow clone: the README still states
"1500+ Integrations" verbatim, and the real core package now has **309**
node directories (one more than before — ordinary incremental
development) and the same **563** `.node.ts` files. The gap is
essentially unchanged, neither narrowing nor widening — confirming this
is a stable, structural counting difference rather than a transient
snapshot artifact from the original round.

## What this re-check pass is for

None of the three original findings needed correcting — this is the
"no changes needed is a common, correct outcome" case applied to
*claims* rather than to a repeat source upload, the same discipline
`.claude/commands/analyze-and-ship.md` states for re-uploaded sources.
The value here is confirming that what was reported as uncertain is
still honestly uncertain (deer-flow), that a "plausible, not confirmed"
judgment held up under a later, stronger source (REA — and even
surfaced a new, worth-recording caveat about star-count inflation), and
that a flagged discrepancy is a stable structural fact rather than a
timing fluke (n8n).
