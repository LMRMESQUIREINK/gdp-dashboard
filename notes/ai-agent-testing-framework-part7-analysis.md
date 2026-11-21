# Analysis: "Testing AI Agents: A Practical Quality Engineering Journey" Part 7 — "True Ambiguity: Can an AI Agent Recognize Multiple Valid Interpretations?" (rajesh yemul, Medium)

Source: a pasted Medium article, Part 7 of the same series Parts 1-6 of
which are already analyzed and built from this session
(`/notes/ai-agent-testing-framework-analysis.md` through
`/notes/ai-agent-testing-framework-part6-analysis.md`,
`/builds/ai-agent-testing-framework/`) — the direct continuation of the
same TypeScript project, same repo, same `requirement-analyzer` agent.
Same treatment as Parts 2-6: extending the existing build, not forking.

## What Part 7 actually adds: TC006, true ambiguity

Distinct from Part 6's TC005 (a subjective, undefined term — "quickly"),
TC006 tests a requirement that supports **multiple concrete,
competing** interpretations: `"...allow customers to cancel an order
within one day of placing it."` — does "one day" mean 24 hours from the
order timestamp, or a calendar-day boundary? The real, actually-quoted
agent output correctly names both candidate interpretations inside
`ambiguities` without selecting either as fact.

## The round's central event: Part 7 names a real gap in its OWN test, and this project checked whether that gap exists in its own oracle too

Part 7's most important move is self-critical: it states plainly that
its own TC006, as written, only verifies that the agent **acknowledges**
the ambiguity — it does not prove the agent never asserts one
interpretation (e.g. "24 hours") as fact elsewhere in the response.
"A Test Can Be Correct and Still Be Incomplete."

This project turned that exact question on its own code rather than
only narrating it:

1. **Confirmed Part 6's hedge-detection fix generalizes to this new,
   independent real example** — but doing so surfaced **a second real
   bug in the Part 6 fix itself**, caught immediately when the first
   test in this round failed unexpectedly. The real TC006 ambiguity
   string hedges "24 hours" only via `"is ambiguous (e.g., ..."`, with no
   `"not specified"`/`"unclear"`/`"unspecified"` phrase anywhere in that
   sentence (unlike Part 6's own TC005 fixture, which happened to carry
   both `"e.g."` and `"is not specified"` in the same sentence,
   masking the problem). Investigating found two real defects in
   `HEDGE_PATTERN`: (a) `\be\.g\.\b` never matches **anything**, because
   a literal `.` is not a word character, so the trailing `\b` can never
   find a word/non-word transition immediately after it — dead code
   since the moment it was written in Part 6, invisible until a fixture
   relied on it alone; (b) `"ambiguous"`/`"ambiguity"` — arguably the
   single clearest possible hedge word there is — was never in the list
   at all. Both fixed: dropped the unmatchable trailing `\b`, added
   `\bambigu\w*\b`. Confirmed the fix doesn't loosen true-positive
   detection with two new dedicated regression tests, plus re-ran every
   existing fabrication fixture from Parts 2 and 6 (all still correctly
   flag).

2. **Turned the article's own "a test can be correct and still
   incomplete" lesson on this project's own `requirementAnalyzerOracle`**,
   with real constructed counterexamples (the article's own named
   "Behavior A" and "Behavior B"):
   - **Behavior A** — an unhedged, unsupported *numeric* interpretation
     asserted as fact (`"The customer can cancel the order within 24
     hours..."`) — confirmed, not assumed, to already be caught by the
     existing numeric-claim mechanism from Parts 2/6. A genuinely
     positive finding: part of the property Part 7 names as untested is
     already covered here.
   - **Behavior B** — an unhedged, unsupported *non-numeric*
     interpretation asserted as fact (`"...until midnight on the
     following calendar day."`) — demonstrated to **slip through
     undetected**. This is a real, honestly-tracked limitation, not
     silently papered over: closing it generally would need a mechanism
     for "does this field assert a specific interpretation as fact the
     requirement never specified" that goes beyond numeric/technical-term
     pattern matching — the same general semantic-correctness problem
     Part 3 already named as unsolved (no algorithm supplied by the
     source beyond one worked example). Tracked with a test asserting
     the *current* (gap) behavior explicitly, so a future fix shows up as
     an intentional change to a named test, not a silent behavior shift.

## The Contract defect recurs on an independent second example

Same observation as Part 6, now reproduced on TC006's real output
without assuming it would recur: the real `ambiguities` array again
mixes genuine ambiguity (`"the term 'one day' is ambiguous"`) with plain
missing information (the starting event for "placed," behavior on an
already-shipped order, refund/notification behavior). Confirmed with a
test against the real output; no `missingInformation` field added, same
reasoning as Part 6 — the real schema is the source series' own file.

## No new external claim to verify

Read in full: Part 7 is entirely about this project's own already-built
agent and test code, with no new company, product, or statistic named.
No web verification needed this round.

## Build (extending `/builds/ai-agent-testing-framework/`, not a new build)

- **`src/grounding/checkGrounding.ts`** — the second hedge-pattern fix
  (dropped the unmatchable `\b` after `e\.g\.`, added `\bambigu\w*\b`).
- **`tests/grounding/checkGrounding.test.ts`** — a new "Part 7 fix"
  block proving the `e.g.`-alone and `ambiguous`-alone cases now
  correctly exempt, isolated from any other hedge phrase.
- **`tests/requirement-analyzer/true-ambiguity-testing.test.ts`** — TC006
  at the full pipeline level: the real output passes `checkGrounding()`
  and the full `requirementAnalyzerOracle` cleanly; a literal
  reproduction of the article's own flagged-as-dangerous assertion,
  shown genuinely failing against this real output; Behavior A
  confirmed caught; Behavior B honestly demonstrated as an open, tracked
  gap; and the Contract-defect finding reconfirmed on independent real
  data.

10 new Vitest assertions (87/87 total, up from 79 — 8 from the TC006
test file, 2 regression tests for the hedge-pattern fix itself), `tsc
--strict --noEmit` clean, `npm run build` clean, `npm audit` 0
vulnerabilities. **A real, second-order bug found and fixed this
round** — in code this project itself wrote and shipped only one round
earlier, surfaced only because new real material exercised a path the
original fix's own test fixture happened not to.

## What's still deliberately not built

Unchanged from Part 6's list, plus: **closing the Behavior B gap** —
general detection of a specific non-numeric interpretation asserted as
fact without evidence — deliberately left open and tracked rather than
force-closed with a fragile keyword heuristic; and **groundedness/
hallucination testing as its own category** — Part 7's own closing
section previews this as the next part's subject (the series' stated
transition from "does the agent recognize bad/ambiguous input" to "is
the agent's own output content actually supported by evidence"),
explicitly deferred by the article itself.
