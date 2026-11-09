# Analysis: "Testing AI Agents: A Practical Quality Engineering Journey" Part 4 — "Writing Our First Functional Test for an AI Agent" (rajesh yemul, Medium)

Source: a pasted Medium article, Part 4 of the same series Parts 1-3 of
which are already analyzed and built from this session
(`/notes/ai-agent-testing-framework-analysis.md`,
`/notes/ai-agent-testing-framework-part2-analysis.md`,
`/notes/ai-agent-testing-framework-part3-analysis.md`,
`/builds/ai-agent-testing-framework/`) — the direct continuation of the
same TypeScript project, same repo, same `requirement-analyzer` agent.
Same treatment as Parts 2-3: extending the existing build, not forking.

## What Part 4 actually adds

Part 3 defined the Required/Allowed/Forbidden framework and named TC001's
own 8-item checklist, but deferred actually writing the test. Part 4
writes it, literally, as real Vitest code against the real runtime path
(`AgentConfigLoader` → `AgentRuntime` → `LLMClient` → `AgentResult`) —
unlike Part 3, this is real runnable code shown in full, the same
treatment this project already gave Parts 1-2.

The literal TC001 groups the same 8 checklist items into 7 named layers
(Execution, Identity, Output, Structure, Contract, Semantics, Behavioral
expectation) — Part 3's items 4 ("Output is valid JSON") and 5 ("Required
fields exist") are kept as two genuinely separate assertion blocks here
(Structure vs. Contract), where this project's own Part 3 oracle merged
them into one check via `parseAgentOutput()`, stated plainly at the time
as a deliberate simplification. Reproduced faithfully in
`TC001.test.ts`'s Layer 4/Layer 5 tests as two separate blocks, matching
the article's own literal code, rather than forcing fidelity to the
earlier simplification.

## The central lesson, now demonstrated rather than just described

Part 3 already established, in the abstract, that a test must not
require behavior the requirement gives no evidence for — this project's
own Part 3 build (`requirementAnalyzerOracle.ts`) already implemented
that by deliberately never requiring `negativeScenarios.length > 0`.

Part 4 arrives at the **same conclusion**, independently, through a
concrete walkthrough: write the tempting assertion
(`expect(parsed.negativeScenarios.length).toBeGreaterThan(0)`), watch it
fail against the agent's real, otherwise-correct output, then run a
4-step investigation (inspect the requirement, inspect the contract,
inspect the actual output, ask whether the empty list is defensible)
before concluding the assertion — not the agent — was wrong, and remove
it. This is **independent confirmation of a design decision already
shipped**, not a new finding changing anything: this round's
`TC001.test.ts` adds a dedicated test
(`cross-checks against the Part 3 oracle`) proving the Part 3 oracle
(built and committed before this round ever read Part 4's text) and
Part 4's own literal, hand-written TC001 reach the same verdict on the
same real pipeline output — the two were built from the same source
series without one ever generating the other, so their agreement is
real evidence, not a restated premise.

## A real, verified precision gap in the article's own stated reasoning

The article flags an "incorrect pattern":

```ts
const parsed = JSON.parse(result.output);
expect(() => parsed).not.toThrow();
```

and explains it as: "the parsing has already happened before the
assertion... if `JSON.parse()` fails, the test has already thrown." True,
but checked directly with code (`TC001.test.ts`'s
"a real, verified precision gap" block) rather than taken at face value,
and found to understate the actual problem: `() => parsed` is a closure
that simply returns an already-captured value — it can **never** throw,
for *any* value of `parsed`, including a value that parsed successfully
but is structurally nonsensical. So the flagged pattern isn't just "too
late" on the failure path — it's a tautology that reports "no exception"
unconditionally, even on the success path, verifying nothing at all.
Reproduced directly: `expect(() => parsed).not.toThrow()` passes for
`parsed = { this: "is not a RequirementAnalysis at all" }`, proving the
assertion carries zero information regardless of what `parsed` actually
is. The article's own corrected pattern (wrapping the parse call itself
inside the closure) is verified separately to genuinely distinguish
valid from invalid JSON — confirmed this build's own
`src/output/parseAgentOutput.ts` (built in Part 2) already follows the
correct discipline, since its `JSON.parse` call sits directly inside the
try/catch it throws from; no change was needed there.

## A real, stated design divergence (not a bug) between the article's literal checks and this project's Part 3 oracle

The article's Layer 6 ("Semantics") checks are narrower than this
project's own Part 3 lexical-grounding checks: the article hardcodes a
single literal substring per field (`actor.toLowerCase().toContain("user")`,
`feature.toLowerCase().toContain("password")`) — tied to this one specific
requirement's exact vocabulary — while Part 3's `isGroundedField()` checks
for *any* shared significant word against the full requirement text
(with simple singular/plural handling), which generalizes to a
differently-worded requirement without rewriting the check. Neither is
wrong for its own stated scope — the article's TC001 is deliberately
scoped to this one requirement; the oracle built from Part 3's framework
was deliberately built to generalize — but it's worth stating plainly
rather than silently assuming one subsumes the other.

## No new external claim to verify

Read in full: Part 4 is entirely about this project's own already-built
agent and test code, with no new company, product, or statistic named
beyond what Parts 1-3 already verified (Gemini's endpoint, Vitest's
`fileParallelism`). No web verification needed this round.

## Build (extending `/builds/ai-agent-testing-framework/`, not a new build)

- **`tests/requirement-analyzer/TC001.test.ts`** — a faithful,
  literal reproduction of the article's own TC001, laid out by its exact
  7-layer structure, run against the real pipeline (real
  `AgentConfigLoader`, real `AgentRuntime`, a mocked `LLMClient` — same
  standing no-live-API-access convention as every build here), plus:
  - the investigation tests proving the removed assertion really would
    have failed on this exact real output, and that the requirement
    genuinely gives no negative-path evidence to justify it;
  - the cross-check against the Part 3 oracle, confirming independent
    agreement;
  - the JSON.parse-assertion tautology finding, reproduced directly
    rather than taken on the article's word.

13 new Vitest assertions (59/59 total, up from 46), `tsc --strict
--noEmit` clean, `npm run build` clean, `npm audit` 0 vulnerabilities.

## What's still deliberately not built

Unchanged from Part 3's own list — true semantic correctness beyond
lexical grounding, a live-fired TC001 against a real Gemini call, and
instruction-following as its own correctness dimension. Part 4's own
closing section previews negative testing (empty input, off-domain
input, nonsense input) as the next part's subject — not built here,
since the article itself defers it to a future part.
