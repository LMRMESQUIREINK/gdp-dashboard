# Analysis: "Testing AI Agents: A Practical Quality Engineering Journey" Part 5 — "Negative Testing: What Happens When the Input Is Bad?" (rajesh yemul, Medium)

Source: a pasted Medium article, Part 5 of the same series Parts 1-4 of
which are already analyzed and built from this session
(`/notes/ai-agent-testing-framework-analysis.md`,
`/notes/ai-agent-testing-framework-part2-analysis.md`,
`/notes/ai-agent-testing-framework-part3-analysis.md`,
`/notes/ai-agent-testing-framework-part4-analysis.md`,
`/builds/ai-agent-testing-framework/`) — the direct continuation of the
same TypeScript project, same repo, same `requirement-analyzer` agent.
Same treatment as Parts 2-4: extending the existing build, not forking.

## What Part 5 actually adds

Three negative-input tests (TC002-TC004), each challenging a different
boundary, with the agent's own real, actually-quoted output for each:

- **TC002 — empty input (`""`)**: tests whether the agent recognizes
  *missing evidence*. Real output: `actor`/`feature` both `"Unknown"`,
  `ambiguities: ["No requirement text was provided for analysis."]`.
- **TC003 — wrong-domain input** (`"Bananas are yellow and elephants
  are large."`): tests *scope adherence* — meaningful English, but
  outside the agent's declared responsibility. Real output: same
  `"Unknown"`/`"Unknown"` pattern, `ambiguities` naming the scope
  violation directly.
- **TC004 — nonsense input** (`"asdfghjkl 123 xyz qwerty"`): tests
  *semantic validity* — syntactically a valid string, semantically
  empty. Same safe-failure shape again.

The article's own named principle, common to all three: **"the agent
must not convert insufficient evidence into invented facts."** The real
code it gives for asserting this is the round's most reusable
contribution:

```ts
const serializedOutput = JSON.stringify(parsed).toLowerCase();
expect(serializedOutput).toMatch(
  /unknown|missing|not specified|not provided|insufficient|empty|ambiguous/
);
expect(serializedOutput).not.toContain("banana management");
expect(serializedOutput).not.toContain("password reset");
```

This is exactly the same Required+Forbidden shape Part 3's
`qualityBoundary.ts` already generalizes — a required "safe-failure
signal present" check, plus one or more forbidden "invented concept"
checks — just applied to a new behavioral property (graceful
degradation on bad input) instead of TC001's structural/semantic
checklist. Recognized directly rather than treated as a brand-new
mechanism to hand-roll separately.

## No new external claim to verify

Read in full: Part 5 is entirely about this project's own already-built
agent and test code (plus a worked pipeline-propagation thought
experiment — Requirement Analyzer → Test Planner → Test Generator →
Test Executor), with no new company, product, or statistic named. No
web verification needed this round.

## Build (extending `/builds/ai-agent-testing-framework/`, not a new build)

- **`src/oracle/safeFailureOracle.ts`** — the generalized mechanism,
  built on Part 3's existing `evaluateBoundary()`/`QualityBoundary<T>`
  rather than a parallel implementation: one Required check (the
  safe-failure signal regex, applied to `JSON.stringify(parsed
  ?? rawOutput).toLowerCase()`), and a Forbidden check generated per
  named invented-concept string. The one real addition beyond the
  article's own literal code: `serialize()` falls back to the raw,
  unparsed output string if the response isn't valid JSON at all,
  rather than letting a direct `JSON.parse()` call throw before any
  safe-failure assertion gets to run — the same class of problem Part
  4's JSON.parse-assertion finding was about, closed here architecturally
  instead of repeated.
- **`tests/requirement-analyzer/negative-testing.test.ts`** — TC002-TC004,
  each tested two ways against the real pipeline (real
  `AgentConfigLoader` → `AgentRuntime`, a mocked `LLMClient`, same
  standing no-live-API-access convention as every build here):
  1. A literal reproduction of the article's own exact assertion
     pattern, using the article's own real, quoted agent output for
     that exact input.
  2. The same case through `evaluateSafeFailure()`, confirming the
     generalized oracle reaches the same verdict as the literal code.

  Each TC also gets a **discrimination check** — a planted, hallucinated
  "bad" response the agent did NOT actually produce (inventing a
  password-reset feature from empty input; inventing "banana management"
  from an off-domain statement about elephants; inventing a login feature
  from pure gibberish) — proving the oracle actually fails these, not
  just passes everything handed to it. Same discipline this project
  applies throughout (`humanizer`, `ten-k-website-grader`,
  `voice-extractor` all proved discrimination with a real counterexample,
  not just a happy-path test).

  A further edge case not covered by the article's own literal pattern:
  a response that isn't valid JSON at all. `evaluateSafeFailure()`
  still produces a clean, correctly-failing verdict rather than an
  uncaught exception, proving the fallback-serialization fix actually
  does something observable.

10 new Vitest assertions (69/69 total, up from 59), `tsc --strict
--noEmit` clean, `npm run build` clean, `npm audit` 0 vulnerabilities.
**No bug found this round** — everything passed on the first real run,
an honest outcome stated plainly rather than manufactured, same as this
project's prior clean-first-run rounds (e.g. the "Agentic Engineering
Concepts" `ruthless-gate` round).

## What's still deliberately not built

Unchanged from Part 4's list, plus: **ambiguity testing** — Part 5's own
closing section previews the next part's subject directly (a requirement
containing subjective, interpretable terms like "quickly" and "using
email"), explicitly deferred by the article itself to Part 6, not built
here.
