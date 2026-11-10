# Analysis: "Testing AI Agents: A Practical Quality Engineering Journey" Part 8 — "Testing Grounding: Can an AI Agent Stay Within the Evidence?" (rajesh yemul, Medium)

Source: a pasted Medium article, Part 8 of the same series Parts 1-7 of
which are already analyzed and built from this session
(`/notes/ai-agent-testing-framework-analysis.md` through
`/notes/ai-agent-testing-framework-part7-analysis.md`,
`/builds/ai-agent-testing-framework/`) — the direct continuation of the
same TypeScript project, same repo, same `requirement-analyzer` agent.
Same treatment as Parts 2-7: extending the existing build, not forking.

## What Part 8 actually adds: TC007-TC010, four evidence situations

A new requirement (`"...allow users to upload a profile picture."`)
tested across four scenarios:

- **TC007 — sparse evidence**: nothing about format/size/auth is
  specified; the agent should preserve the unknowns. Real quoted output
  hedges "JPEG, PNG" as an example of an unspecified format.
- **TC008 — explicit evidence**: the requirement adds `"...stored in
  Amazon S3."`; the agent must *use* that evidence, not discard it, and
  must not expand beyond it (bucket name, region, encryption, etc.).
- **TC009 — conflicting evidence**: the requirement adds contradictory
  storage statements (local device AND S3); the agent must surface the
  conflict, not silently resolve it.
- **TC010 — unsupported inference**: six named "reasonable-sounding but
  unsupported" claims (authentication required, JPEG/PNG support, a 5MB
  limit, S3 storage, an upload button, automatic thumbnail generation),
  none of which the agent should assert as fact.

## The round's central move: the article's own ad-hoc regexes vs. this project's already-generalized mechanism

The article's own TC007 narrative repeats Parts 6-7's exact lesson: a
naive "the word must not appear" assertion failed against the agent's
correct output (the word was a hedged example, not a claim). Its fix
was a set of **hand-written, per-claim regexes** — one for image
formats, one for file size, one for storage, one for resolution — each
narrowly scoped to the specific phrasing the article anticipated, with
the article itself naming the limitation plainly: a differently-phrased
claim could slip past a narrow pattern.

This project's `checkGrounding()` (built in Part 2, hedge-fixed in
Parts 6-7) already generalizes exactly this principle — a curated term
list plus hedge detection, not per-claim custom regexes — so this round
**extended the existing term list and numeric-unit list** with Part 8's
real new vocabulary (image formats, storage/cloud terms, UI/processing
terms, byte-size units) rather than writing six new one-off assertions.
TC010's own six named claim categories are proven caught by this one
mechanism in a single parameterized test loop, not six separate
hand-built checks.

## Two real bugs found while testing against this round's real/named material

1. **A real morphological-variant gap, same bug class as Part 3's
   "user"/"users" finding**: TC010's own named example is "Users must
   **authenticate** before uploading a picture" — the term list had
   "authentication" (the noun) but not "authenticate" (the verb), so
   this specific claim, lifted verbatim from the article, slipped
   through entirely on the first real run. `TECHNICAL_TERMS` does no
   stemming by design (it's a small, auditable, literal list), so
   morphological variants need listing explicitly — fixed by adding
   "authenticate" alongside "authentication," with the module comment
   naming this as the same category of gap as the earlier singular/
   plural bug, not a coincidence.

2. **A real, verified defect in the article's own TC009 regex,
   checked directly rather than trusted**: the article gives
   `/therefore.*s3|therefore.*local|must use s3|must use local
   storage/i` as its silent-resolution detector, and separately quotes
   its own two named "tempting but wrong" example responses — *"The
   system must store the profile picture in Amazon S3"* and *"The image
   is stored locally and then uploaded to S3."* Running the article's
   own regex against its own two named examples, via a standalone
   script before writing any code: **neither matches**. Confirmed, not
   assumed. `contradictionOracle.ts`'s `SILENT_RESOLUTION_PATTERNS`
   keeps the article's original four patterns and adds four more,
   specifically verified (again, with a standalone script, before
   trusting) to catch both of the article's own named examples.

## Build (extending `/builds/ai-agent-testing-framework/`, not a new build)

- **`src/grounding/checkGrounding.ts`** — `TECHNICAL_TERMS` extended
  with Part 8's real vocabulary (JPEG/PNG/GIF/WEBP, S3/Amazon S3/
  database/bucket/bucket name/AWS region/encryption/retention/CDN,
  thumbnail/upload button/browse button, authentication/authenticate/
  login); `NUMERIC_CLAIM_PATTERN`'s unit list extended with byte-size
  units (KB/MB/GB/TB/byte/pixel/px) so file-size and dimension claims
  are caught, not just durations.
- **`src/oracle/contradictionOracle.ts`** (new, TC009) — built on the
  same `qualityBoundary.ts` mechanism as `safeFailureOracle.ts` (Part
  5): one Required check (a conflict-signal word present) plus the
  corrected, broadened Forbidden checks (silent-resolution phrasing).
- **`tests/requirement-analyzer/grounding-testing.test.ts`** — TC007-
  TC010 against the real pipeline: TC007's real output passes cleanly
  (hedged format mentions correctly exempted) with a discrimination
  check for an unhedged format claim; TC008 proves explicit S3 evidence
  is both preserved (literal lexical check, matching the article's own
  appropriate use of word-presence here) and not over-expanded, plus a
  discrimination check for the "overly cautious agent" failure mode
  (discarding given evidence looks safe but is wrong); TC009 proves a
  constructed conflict-surfacing response passes and both of the
  article's own named bad examples are caught; TC010 proves all six
  named claim categories are caught by the one generalized mechanism,
  plus a clean baseline that correctly passes.
- **`tests/grounding/checkGrounding.test.ts`** — a new "Part 8 fix"
  regression test for the authenticate/authentication gap.

17 new Vitest assertions in the grounding test file plus 1 more in
checkGrounding.test.ts (105/105 total, up from 87), `tsc --strict
--noEmit` clean, `npm run build` clean, `npm audit` 0 vulnerabilities.
**Two real bugs found and fixed this round** — a third round in a row
with at least one real, evidenced defect found by testing against new
material rather than trusting it.

## What's still deliberately not built

Unchanged from Part 7's list (the Behavior B gap, general semantic
correctness). The article's own closing section previews a much larger
architectural shift — agents that act (tool calls, external systems,
observation-and-decision loops) rather than reason in one shot — as the
next major subject; nothing here anticipates that shift, since Part 8
itself only previews it without giving any concrete mechanism yet.
