# Analysis: "Testing AI Agents: A Practical Quality Engineering Journey" Part 6 — "Testing Ambiguity in AI Agents" (rajesh yemul, Medium)

Source: a pasted Medium article, Part 6 of the same series Parts 1-5 of
which are already analyzed and built from this session
(`/notes/ai-agent-testing-framework-analysis.md`,
`/notes/ai-agent-testing-framework-part2-analysis.md`,
`/notes/ai-agent-testing-framework-part3-analysis.md`,
`/notes/ai-agent-testing-framework-part4-analysis.md`,
`/notes/ai-agent-testing-framework-part5-analysis.md`,
`/builds/ai-agent-testing-framework/`) — the direct continuation of the
same TypeScript project, same repo, same `requirement-analyzer` agent.
Same treatment as Parts 2-5: extending the existing build, not forking.

## What Part 6 actually adds: TC005, subjective ambiguity

Input: `"The system should allow users to reset their password quickly
using email."` — valid, meaningful, on-domain, but containing a
subjective term ("quickly") with no measurable definition, and an
underspecified mechanism ("using email" — link, OTP, temporary
password?). The real, actually-quoted agent output correctly identifies
the actor/feature, one positive scenario, and names four items in
`ambiguities`, including the subjective-term flag and a hedged mention
of possible mechanisms ("e.g., one-time link, temporary password, OTP").

## The round's central event: a real bug found by running this project's own existing code against new real material

The article's own narrative: a naive forbidden-term assertion
(`expect(output).not.toContain("otp")`) **failed** against the agent's
own correct output, because the word "OTP" appeared — not as a claim,
but as a hedged example of an unspecified possibility. The article
frames this as a hypothetical lesson about test-oracle design.

This project checked it directly instead of treating it as hypothetical:
**this project's own `checkGrounding()` module (built in Part 2, already
shipped, already used as Part 3's one Forbidden check and reused again
in Part 5's `safeFailureOracle`) has exactly this bug.** Reproduced
before touching any code — running the real TC005 output through the
unmodified, already-shipped `checkGrounding()` returned:

```json
[{ "field": "ambiguities", "index": 1, "term": "OTP", "kind": "technical-term" }]
```

A genuine false positive in code this project had already tested,
documented, and shipped across three prior rounds, surfaced only because
Part 6 supplied a new real example that happened to exercise a path the
Part 2 regression fixtures never did (neither of Part 2's two original
fabrication examples hedges its invented term at all).

## The fix: hedge detection, not a weaker check

The article's own Required/Allowed/Forbidden framing (the same shape
this project already generalized in Part 3): Required — identify the
ambiguity; **Allowed** — mention possible interpretations, provided
they're clearly labeled as unspecified/hypothetical; Forbidden — state
an unsupported detail as though the requirement specified it.

`checkGrounding.ts` now exempts a claim/term from being flagged when the
**same** field/array-item text also contains hedging language (`"not
specified"`, `"unspecified"`, `"possibly"`, `"e.g."`, `"for example"`,
`"hypothetical"`, `"unclear"`, etc. — `HEDGE_PATTERN`). This widens what
counts as Allowed; it does **not** narrow what's Forbidden — verified
directly, not assumed: both of Part 2's own original fabrication
examples contain no hedge language, so both still flag correctly after
the fix (regression tests added specifically to prove this, not just
asserted in prose). A new test also confirms the article's own named
"Response A vs. Response B" distinction holds at the oracle level: "The
system sends an OTP to the user's email" (an unhedged claim) still
correctly fails; the real hedged TC005 response correctly passes.

## A second finding, documented rather than "fixed": the Contract defect

Part 6 itself observes that the real schema's single `ambiguities` array
conflates two different problem categories: true ambiguity (`"quickly"`
is subjective — multiple valid readings) and plain missing information
(password strength rules, error handling — no competing interpretation,
just an absence). The article explicitly says this doesn't mean TC005
failed; it means the agent's contract itself could be improved with a
separate field (e.g. `missingInformation`).

This project does **not** add that field. `requirement_analyzer.md` is
the real, authoritative file given by the source series (swapped in
during Part 2); inventing a new field for it here would be fabricating
spec the article never actually supplies, the same discipline this
project applies to every "named but unspecified" gap (Part 3's semantic-
correctness gap, Part 4's instruction-following gap). The finding is
instead documented directly — a test confirms the real TC005 output
genuinely contains both category types, reproducibly, without inventing
new code to "solve" a contract question that isn't this project's to
answer.

## No new external claim to verify

Read in full: Part 6 is entirely about this project's own already-built
agent and test code, with no new company, product, or statistic named.
No web verification needed this round.

## Build (extending `/builds/ai-agent-testing-framework/`, not a new build)

- **`src/grounding/checkGrounding.ts`** — the hedge-detection fix
  (`HEDGE_PATTERN`, `isHedged()`), applied uniformly to both numeric
  claims and technical terms.
- **`tests/grounding/checkGrounding.test.ts`** — a new "Part 6 fix"
  block: the real TC005 output now passes cleanly; the article's own
  Response A (unhedged claim) still correctly fails; both of Part 2's
  original fabrication fixtures still correctly fail (no hedge language
  present in either); a hedged numeric claim is exempted too, proving
  the fix isn't technical-term-only.
- **`tests/requirement-analyzer/ambiguity-testing.test.ts`** — TC005
  proven at the full pipeline level (real `AgentConfigLoader` →
  `AgentRuntime` → mocked `LLMClient`, same standing no-live-API-access
  convention as every build here): the real output passes
  `checkGrounding()` and the full `requirementAnalyzerOracle` (Part 3)
  cleanly; a literal reproduction of the article's own flagged-as-
  too-weak assertion, shown genuinely failing against this real output
  (proving the "before" picture is real, not illustrative); the
  Response A/B distinction proven at the oracle level, not just the unit
  level; and the Contract-defect finding, confirmed with code against
  the real output rather than only stated in prose.

10 new Vitest assertions (79/79 total, up from 69), `tsc --strict
--noEmit` clean, `npm run build` clean, `npm audit` 0 vulnerabilities.
**A real, pre-existing bug found and fixed this round** — unlike Part
5, which found none.

## What's still deliberately not built

Unchanged from Part 5's list, plus: **true ambiguity / multiple
concrete interpretations** (TC006, e.g. "within one day" meaning either
24 hours from the order timestamp or midnight the following calendar
day) — Part 6's own closing section previews this as the next part's
subject, explicitly deferred by the article itself. A
`missingInformation` schema field — the Contract defect above,
deliberately documented rather than invented.
