# Analysis: "Testing AI Agents: A Practical Quality Engineering Journey" Part 3 — "What Does 'Correct' Mean for an AI Agent?" (rajesh yemul, Medium)

Source: a pasted Medium article, Part 3 of the same series Parts 1-2 of
which are already analyzed and built from this session
(`/notes/ai-agent-testing-framework-analysis.md`,
`/notes/ai-agent-testing-framework-part2-analysis.md`,
`/builds/ai-agent-testing-framework/`) — the direct continuation of the
same TypeScript project, same repo, same `requirement-analyzer` agent. Same
treatment as Part 2: this is a continuation upload, not a new independent
source, so the work is extending the existing build, not forking a new one.

## What Part 3 actually adds

Unlike Parts 1-2, Part 3 has no new runnable code of its own — it's the
conceptual bridge between "the agent produces valid-JSON output" (Part 2)
and "we know whether that output is actually correct" (the series' own
named "test oracle problem," deferred since Part 1). Its real content is a
framework, stated precisely enough to implement directly:

- **Required / Allowed / Forbidden**, as three named categories: things
  the response must satisfy, things that may legitimately vary (wording),
  and things that must never happen.
- **Four correctness dimensions**: structural correctness, semantic
  correctness, groundedness, instruction following.
- **TC001's own exact 8-item Required checklist** for the canonical
  password-reset requirement (reproduced verbatim in
  `src/oracle/requirementAnalyzerOracle.ts`'s own docstring).
- **The central lesson (Sections 5-7), restated as two labeled
  situations**: a test must never require behavior the requirement gives
  no evidence for. The article's own worked case: `negativeScenarios` being
  empty for a requirement that describes no negative path is **not** a
  failure — requiring `negativeScenarios.length > 0` here would be "the
  test inventing an expectation," the article's own words, not the agent
  failing. "We should not weaken a test because the AI failed. We should
  change an assertion only when our expectation was stronger than the
  evidence justified."
- **Section 11, on inference**: legitimate summarization (an order
  cancellation window stated as "within the allowed period" when the
  source says "within one day") is fine; adding a condition the source
  never stated ("provided the order has not been shipped") is forbidden
  invention, not inference.

## A real, honestly-stated gap found while trying to implement this

Checklist items 6 and 7 ("Actor represents the user," "Feature represents
password reset") sit squarely inside what Part 3 itself names "semantic
correctness" (Section 9.2): "if the requirement identifies User but the
agent identifies Administrator... the meaning does not [pass]." But
nowhere in Part 3 — or Parts 1-2 — is there an algorithm, or even a sketch
of one, for how an automated oracle is supposed to make that
determination beyond the one worked example being obviously wrong. This
is the same shape of gap as Part 1's YAML-config-vs-prose-reasoning
mismatch found in the "Quality Engineering" series: a real capability is
named as necessary, but the mechanism to automate it is never supplied.

Stated plainly in `requirementAnalyzerOracle.ts`'s own docstring rather
than hidden: checks 6 and 7 are built as **lexical-grounding** checks
(non-empty, and shares at least one significant word with the requirement
text, allowing simple singular/plural variation) — not a claim of real
semantic understanding. This is the same honestly-scoped approach
`checkGrounding()` already took in Part 2's build for the opposite
direction (catching fabrication, not verifying meaning).

## A real bug found while building this, caught by the test suite itself

The first version of the lexical-grounding check used exact `Set`
intersection on tokenized words. Running it against the article's own
most basic passing case — `actor: "User"` for a requirement that only
ever says "**users**" (plural) — failed: `{user}` and `{system, users,
reset, password, email}` share no exact token, so the clearest possible
grounded case was wrongly rejected. Caught immediately by
`requirementAnalyzerOracle.test.ts`'s first test failing, not by
inspection. Fixed with the simplest stemming that resolves it (strip a
trailing "s" from either side before comparing) rather than reaching for
a real stemmer library for a check this deliberately narrow.

A second, smaller bug from the same test run: three of the "fails when
result is null/missing" Required checks (`Correct agent is executed`,
`Output exists`) assumed `ctx.result` was always a real object and threw
a raw `TypeError` instead of returning `false` when it wasn't — `evaluateBoundary`
runs every check regardless of whether an earlier one failed (by design,
per the module's own docstring: "never a single pass/fail boolean... see
EXACTLY which check failed"), so a check can't assume a prior one already
guarded the input. Fixed by adding null guards to the three checks (and
`tryParse`) that touch `ctx.result` directly.

## Build (extending `/builds/ai-agent-testing-framework/`, not a new build)

- **`src/oracle/qualityBoundary.ts`** — the generic mechanism:
  `BoundaryCheck<T>`, `QualityBoundary<T>` (a `required` list and a
  `forbidden` list, each named, independently reportable checks),
  `evaluateBoundary()` returning a `Verdict` with every failing check
  named, never a bare boolean. "Allowed" has no list of its own anywhere
  in the API — by design, it's the implicit complement of Required +
  Forbidden, matching the article's own point that fragile exact-string
  assertions are the wrong tool.
- **`src/oracle/requirementAnalyzerOracle.ts`** — the concrete TC001
  oracle, instantiating the article's own exact 8-item Required checklist
  (with items 4 "Output is valid JSON" and 5 "Required fields exist"
  evaluated together via one `parseAgentOutput()` call, which already
  enforces both atomically — stated as a deliberate simplification, not
  hidden), reusing Part 2's `checkGrounding()` directly as the one
  Forbidden check rather than reimplementing fabrication detection.
  **Deliberately does not require `negativeScenarios.length > 0`
  anywhere** — the single most important design decision in this file,
  directly implementing the article's own central lesson.

Tested against: the real canonical requirement passing all 8 Required
items cleanly; the article's own Situation A (empty `negativeScenarios`
must pass, not fail); a constructed Situation B (a fabricated,
ungrounded negative scenario must fail as a Forbidden violation, not
pass as a Required success); the real Part 2 paraphrase-equivalence
example (must stay Allowed, not flagged); each of the 8 Required items
failing one at a time, independently; and both of Part 2's real
fabrication examples (OTP/5-minutes, OAuth 2.0/AES-256) correctly
triggering the Forbidden check through the reused `checkGrounding()`
module rather than a new one.

46/46 Vitest assertions pass (up from 25), `tsc --strict --noEmit`
clean, `npm run build` produces real output, `npm audit` reports 0
vulnerabilities.

## What's still deliberately not built

- **True semantic correctness** for checks 6/7 — stated above as a real,
  unresolved gap in the source itself, not papered over with an
  overclaimed algorithm.
- **TC001 itself, executed against a live agent** — still blocked on the
  same standing no-live-API-access restriction as every build in this
  project; this oracle is the acceptance criteria TC001 would check
  against, not a live-fired test.
- **Instruction-following as its own dimension** — Part 3 names it as
  one of four correctness dimensions but gives no worked example distinct
  from groundedness/structural correctness to build against; left
  unbuilt rather than invented.
