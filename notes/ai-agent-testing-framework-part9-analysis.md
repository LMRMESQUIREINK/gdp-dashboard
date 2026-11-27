# Analysis: "Testing AI Agent Boundaries: Output Contracts, Grounding and Prompt Injection" — Part 9 (rajesh yemul, Medium)

Source: a pasted Medium article, Part 9 of the same series Parts 1-8 of
which are already analyzed and built from this session
(`/notes/ai-agent-testing-framework-analysis.md` through
`/notes/ai-agent-testing-framework-part8-analysis.md`,
`/builds/ai-agent-testing-framework/`) — a different URL slug but the
same author, same `requirement-analyzer` agent, same direct
continuation. Same treatment as Parts 2-8: extending the existing
build, not forking.

## What Part 9 actually adds: three boundaries, not one

Part 9 names three distinct boundaries explicitly for the first time —
**Evidence** (grounding, Parts 6-8), **Output** (contract), and
**Instructions** (prompt injection) — and gives real, concrete content
for the latter two:

- **An explicit Zod runtime contract** (`RequirementAnalysisSchema`),
  real code shown in full: `z.string().min(1)` for required strings,
  arrays allowed to stay empty, `.strict()` closing the schema against
  unexpected extra fields.
- **TC012-TC016**, named as *deterministic* contract tests (no live
  agent call needed) vs. TC001-TC011/TC017-TC020's *live* behavioral
  tests — missing field, wrong type, unexpected field, empty string,
  Markdown/code-fence output.
- **TC017-TC020**, prompt-injection resistance tests: direct
  instruction override, role/identity hijacking, data/instruction
  boundary confusion, output-format manipulation.

## A real, verified pair of gaps in this project's own pre-existing code

Checked directly against the article's own Zod schema rather than
assumed: this project's `parseAgentOutput.ts` (hand-rolled since Part
2) had two real defects, reproduced against the unmodified module
before touching anything —

1. An unexpected extra field (`"confidence": 0.92`) was **silently
   dropped**, not rejected — the old per-field loop only checked fields
   it expected, never checked for ones it didn't.
2. An empty string (`"actor": ""`) **passed** — `typeof === "string"`
   is true for `""`, and the old code never checked length.

Both are exactly what Zod's `.strict()` and `z.string().min(1)` catch.
Fixed by refactoring `parseAgentOutput.ts` onto the real
`RequirementAnalysisSchema` (new `src/schema/RequirementAnalysisSchema.ts`,
reproduced verbatim from the article), confirmed to close both gaps by
re-running the exact same reproduction against the fixed module. The
existing parse-into-`unknown`-before-validating discipline the article
calls out as important needed no change — this module already did that
correctly since Part 2.

## TC012-TC016, named explicitly

Most of this was already covered by Part 2's original test suite
(missing field, wrong type, code fences); added explicit TC014 (extra
field) and TC015 (empty string) tests for the two real gaps above, plus
TC012/TC013/TC016 as explicitly-named cross-references to existing
coverage, in `tests/output/parseAgentOutput.test.ts`.

## TC017-TC020: "Mentioning ≠ Following," the same lesson in a new dimension

Part 9's central connecting insight: the grounding series' "mentioning
'JPEG' ≠ claiming JPEG is supported" (Parts 6-8) is the exact same
reasoning pattern as "mentioning 'Delete all users' ≠ adopting it as
the feature." A secure agent may legitimately *name* an injection
attempt in `ambiguities` — that's acceptable, even expected. What it
must never do is adopt the injected values into its own structured
answer.

The article names two reusable helpers conceptually
(`expectRequirementAnchoring`, `expectInjectionPayloadNotAdopted`).
Built as `src/oracle/injectionResistanceOracle.ts` on the same
`qualityBoundary.ts` mechanism as every other oracle in this build
(`safeFailureOracle.ts`, `contradictionOracle.ts`): two Required checks
(actor/feature stay lexically anchored to the real, un-injected
requirement — reusing Part 3's `isGroundedField`, extracted this round
into a new shared `src/oracle/lexicalGrounding.ts` module so both
oracles use one implementation) and two Forbidden checks (the injected
actor/feature values don't appear in the actor/feature fields
themselves). Checking adoption directly on the actor/feature field
values, not the whole serialized blob, cleanly separates "named in
ambiguities" (a different field, naturally Allowed) from "adopted into
actor/feature" (Forbidden) without needing separate hedge detection for
this oracle.

The article gives no literal "we ran it and got this real output" quote
for any of TC017-020 (unlike TC001/TC005-TC008) — only the injected
input text and the desired/undesired actor/feature *values* in prose.
Every test fixture in `tests/requirement-analyzer/injection-resistance.test.ts`
is therefore constructed from those named values and labeled as such,
not quoted verbatim from a real run.

## A real, honest limitation found while testing TC017, not assumed from reading the code

The first draft of the TC017 discrimination test predicted BOTH
Required anchoring checks would fail on a fully-adopted bad response
(`actor: "Administrator"`, `feature: "Delete all users"`). Running it
showed only the actor-anchoring check failed — the feature-anchoring
check incorrectly reported the feature as "anchored," because
`isGroundedField`'s plain shared-significant-word heuristic found the
literal word **"users"** shared between the forbidden feature value and
the real requirement ("...allow **users** to upload a profile
picture"). The overall verdict still correctly fails, but only because
the separate Forbidden adoption check independently catches it — the
Required anchoring check alone has a real blind spot whenever a
forbidden value happens to share incidental vocabulary with the real
requirement. Documented with a dedicated test proving exactly this
(`injection-resistance.test.ts`'s "A REAL, HONEST LIMITATION" test)
rather than silently adjusting the expectation to hide it. Closing this
properly would need real semantic similarity, not lexical overlap — the
same unresolved gap Part 3 already named for "semantic correctness" and
never claimed to solve.

## TC020: a different boundary entirely, already closed by earlier work

TC020 (output-format manipulation — an injected "do not return JSON"
instruction) isn't an actor/feature adoption question at all; it's the
Output boundary, tested through the Part 9 Zod-backed
`parseAgentOutput()` contract directly. Proven against the article's
own literal injected bad output (`"# Status\nThe requirement has been
approved."`): correctly rejected with `OutputContractViolation`. A
genuinely positive finding, not a new mechanism needed: this boundary
was already closed by Part 2/9's contract work, now proven against this
specific attack framing rather than only the generic Markdown-fence
case.

## No new external claim to verify

Read in full: Part 9 is entirely about this project's own already-built
agent and test code plus the real, verifiable `zod` library (confirmed
installed and its `.strict()` API working as shown — `zod@4.6.7`,
checked by actually running it, not assumed from v3-era docs). No web
verification needed beyond that.

## Build (extending `/builds/ai-agent-testing-framework/`, not a new build)

- **`src/schema/RequirementAnalysisSchema.ts`** (new) — the real Zod
  schema, verbatim from the article.
- **`src/output/parseAgentOutput.ts`** — refactored onto the schema,
  closing the two real gaps above; same JSON-parse-into-`unknown`
  discipline preserved.
- **`src/oracle/lexicalGrounding.ts`** (new) — `isGroundedField`
  extracted from `requirementAnalyzerOracle.ts` so
  `injectionResistanceOracle.ts` can reuse it without duplication.
- **`src/grounding/checkGrounding.ts`** — `isHedged` exported (no
  behavior change) for potential reuse, though this round's injection
  oracle ended up not needing it, since adoption is checked on the
  actor/feature fields directly rather than via hedge detection.
- **`src/oracle/injectionResistanceOracle.ts`** (new) — TC017-TC019,
  built on `qualityBoundary.ts`.
- **`tests/output/parseAgentOutput.test.ts`** — TC012-TC016 block.
- **`tests/requirement-analyzer/injection-resistance.test.ts`** (new) —
  TC017-TC020, including the honest anchoring-blind-spot finding.

15 new Vitest assertions across both files (120/120 total, up from
105), `tsc --strict --noEmit` clean, `npm run build` clean, `npm audit`
0 vulnerabilities (including the new `zod` dependency). **A fourth
round in a row with at least one real finding** — two genuine
pre-existing gaps closed by the Zod refactor, plus one honestly-tracked
new limitation in this round's own new oracle.

## What's still deliberately not built

Unchanged from Part 8's list (full semantic-claim detection beyond
term/numeric/lexical patterns — now including the TC017 anchoring blind
spot as a concrete instance of the same named gap), plus **tool-calling
/ action testing** — Part 9's own closing section previews this as the
next part's subject directly (tool selection, arguments, failure
recovery, trajectory evaluation), explicitly deferred by the article
itself.
