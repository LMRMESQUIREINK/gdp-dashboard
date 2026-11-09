# ai-agent-testing-framework

A real, working reproduction of the TypeScript + Vitest project from
rajesh yemul's four-part (so far) Medium series: "Building an AI Agent
Testing Framework from Scratch with TypeScript and Vitest" (Part 1),
"Testing AI Agents: A Practical Quality Engineering Journey" (Part 2),
"What Does 'Correct' Mean for an AI Agent?" (Part 3), and "Writing Our
First Functional Test for an AI Agent" (Part 4) — the author's own
small, from-scratch agent-execution harness (Markdown+YAML agent
definitions → `AgentConfigLoader` → `AgentRuntime` → `LLMClient` → an LLM
→ `AgentResult` → Vitest). Unlike most sources in this project, this
article series *is* real, runnable code shown in full (Parts 1-2, 4)
plus a precisely-stated framework (Part 3), not a vague conceptual piece
to extract a mechanism from — so this build is a faithful,
continuously-updated reproduction, actually installed and run in this
sandbox, with real bugs found and fixed along the way in every round.
Analyzed in `/notes/ai-agent-testing-framework-analysis.md` (Part 1),
`/notes/ai-agent-testing-framework-part2-analysis.md` (Part 2),
`/notes/ai-agent-testing-framework-part3-analysis.md` (Part 3), and
`/notes/ai-agent-testing-framework-part4-analysis.md` (Part 4).

## A note on provenance: this author's two series connect

The same author (rajesh yemul) has a separate "Quality Engineering"
series this project already analyzed and built from
(`/notes/orchestration-agent-loop-analysis.md`,
`/builds/orchestration-decision-engine/`) — that series' own Season 3
producer pipeline names a "Requirement Analyzer" as its first producer.
This article's own worked example defines exactly that agent
(`agentId: requirement-analyzer`), strongly suggesting this "Testing
Framework from Scratch" series is the technical foundation underneath
that higher-level orchestration narrative, from the same author, across
two separately-numbered series. Neither article states this connection
directly; it's only visible reading both together.

## Two real bugs found and fixed, both reproduced for real, not just read

1. **A genuine syntax error in the article's own shown `vitest.config.ts`.**
   Counting braces in the pasted snippet (`grep -o '{' | wc -l` → 3,
   `grep -o '}' | wc -l` → 4) found an unbalanced object literal. Copied
   verbatim and run for real (as plain ESM, bypassing the `.ts`-specific
   parsing quirks that let a quick `tsc`/`node --check` pass silently):
   `node` throws `SyntaxError: missing ) after argument list` pointing
   at the exact extra `}`. This repo's `vitest.config.ts` has the fix
   (one closing brace removed, a trailing comma added) — confirmed by
   actually running the real test suite against it (10/10 passing, see
   below).
2. **A real gap between the article's stated goal and what its own code
   delivers.** The article explicitly motivates having an `LLMClient`
   abstraction as enabling "deterministic tests for the testing
   framework itself" — but `AgentRuntime`'s real constructor types its
   parameter as the **concrete** `LLMClient` class, not an interface.
   Reproduced directly: a plain object implementing only `generate()`
   was passed where `AgentRuntime` expects an `LLMClient`, and
   `tsc --strict` rejected it —
   `error TS2741: Property 'client' is missing in type '{ generate(...): Promise<string>; }' but required in type 'LLMClient'`
   — because TypeScript matches class types structurally **including
   their private fields**, and the real `LLMClient` has a private
   `client: OpenAI` field no mock can supply. This directly blocks the
   exact deterministic-test capability the article's own prose promises.
   **Fixed** by extracting a real `LLMClient` interface into
   `src/types/AgentTypes.ts` (just the `generate()` signature), having
   the concrete class `implements` it, and retyping `AgentRuntime`'s
   constructor against the interface instead of the class. A plain mock
   object now satisfies it cleanly under `strict` mode — proven directly
   in `tests/requirement-analyzer/requirement-analyzer.test.ts`.

## Part 2 update: the real `requirement_analyzer.md`, a strict output parser, and a grounding checker

Part 2 of the same series ("Testing AI Agents: A Practical Quality
Engineering Journey") gave this agent's real, complete definition for the
first time — Part 1 only showed the `# Role` fragment. **This build's
Part-1 placeholder has been replaced with the real file**, correcting it
rather than silently overwriting it (see
`/notes/ai-agent-testing-framework-part2-analysis.md` for the full diff).
The real file uses a different Responsibilities list (Actor/Feature/
Preconditions/Positive scenarios/Negative scenarios/Ambiguities, not the
placeholder's Trigger/Expected-Outcome), seven specific numbered grounding
Rules (not the placeholder's three generic ones), and a strict-JSON-only
Output Requirements contract (not the placeholder's prose sections).

Two new modules operationalize rules the agent's own instructions state
but that neither Part 1 nor Part 2's own shown code ever actually checks:

- **`src/output/parseAgentOutput.ts`** — enforces the real Output
  Requirements contract literally: valid JSON only, no Markdown code
  fences, no surrounding prose, the exact six-field schema
  (`actor`/`feature`/`preconditions[]`/`positiveScenarios[]`/
  `negativeScenarios[]`/`ambiguities[]`). `AgentRuntime.run()` still
  returns a raw `output: string` (the article's own deliberate choice —
  "our testing layer will eventually determine whether that output
  satisfies the contract"); this is that missing enforcement.
- **`src/grounding/checkGrounding.ts`** — a real, honestly-scoped
  grounding/hallucination checker built directly from Part 2's own two
  worked "the JSON is valid but the agent is still wrong" examples: one
  fabricating "OTP" and "within 5 minutes," the other fabricating "OAuth
  2.0" and "AES-256 encryption," for a requirement that mentions neither.
  Checked `/builds/` first — `humanizer` checks prose *style*,
  `paired-bootstrap-ratchet` checks statistical significance of accuracy
  *claims*, `defender-loop-verifier` is about crash self-report, none of
  them check per-response grounding against a source document, so this
  is a genuinely new mechanism.

  **Deliberately not a full word-presence check** — and this was
  verified, not assumed: Part 2 also gives a real paraphrase-equivalence
  example (two differently-worded but behaviorally equivalent scenario
  descriptions). A standalone script run *before* writing this module
  confirmed a naive "every output word must appear in the input" check
  really does flag `["user", "initiates", "recovery", "completes"]` as
  unsupported against that exact pair — a false positive against the
  article's own explicit point that different phrasings can be equally
  valid. `checkGrounding()` instead targets only the two concrete
  patterns Part 2's own two fabrication examples actually are: numeric/
  duration claims, and a small, named, auditable list of security/auth
  technical terms. This is **not** full semantic correctness checking —
  the article's own "test oracle problem," explicitly deferred to a
  future part of its own series — it's a narrow, evidenced check for
  exactly the fabrication pattern this source demonstrates, stated
  plainly as a limitation rather than oversold.

Also updated: the existing mocked-LLMClient pipeline test now uses the
real JSON schema (it previously used a prose-format mock matching the
now-superseded placeholder) and runs the full real pipeline —
`AgentConfigLoader` → `AgentRuntime` → `parseAgentOutput` →
`checkGrounding` — end to end.

**A real bug found while verifying this round, in the build's own test
setup, not the source**: running `npm test` after `npm run build` first
reported 50 passing tests — double the real count. `tsc`'s own `dist/`
output includes a compiled copy of every `tests/**/*.ts` file, and
Vitest's default include pattern was picking those up too, silently
running every test twice. Caught by actually counting (5 real test
files × their real assertion counts = 25, not 35 or 50, both of which
were seen at different points depending on how stale `dist/` happened
to be) rather than trusting the first number Vitest printed. Fixed by
adding an explicit `exclude: ["**/node_modules/**", "**/dist/**"]` to
`vitest.config.ts` — Vitest's own default excludes cover
`node_modules/` but not a project's own build output directory.

## Part 3 update: a real Required/Allowed/Forbidden quality-boundary oracle

Part 3 ("What Does 'Correct' Mean for an AI Agent?") has no new runnable
code of its own — it's the series' own named "test oracle problem"
(deferred since Part 1) finally defined precisely enough to implement: a
**Required / Allowed / Forbidden** framework, four correctness dimensions
(structural, semantic, groundedness, instruction-following), and TC001's
own exact 8-item Required checklist for the canonical password-reset
requirement.

- **`src/oracle/qualityBoundary.ts`** — the generic mechanism. A
  `QualityBoundary<T>` is just a `required` list and a `forbidden` list,
  each a set of named, independently reportable checks.
  `evaluateBoundary()` never collapses this to one boolean — the
  article's own central Section 6-7 lesson ("the problem may not be the
  agent, the problem may be our test") requires being able to see
  **exactly** which check failed. "Allowed" has no list anywhere in the
  API, by design — it's the implicit complement of Required + Forbidden,
  matching the article's point that fragile exact-string assertions are
  the wrong tool for anything that may legitimately vary.
- **`src/oracle/requirementAnalyzerOracle.ts`** — the concrete TC001
  acceptance oracle, instantiating the article's own 8-item checklist
  verbatim (reproduced in the module's own docstring), reusing Part 2's
  `checkGrounding()` directly as its one Forbidden check rather than
  reimplementing fabrication detection.

**The single most important design decision in this file**: it
deliberately never requires `negativeScenarios.length > 0`. This is Part
3's own central lesson, operationalized rather than just read about — a
requirement with no negative-path evidence (the real canonical
password-reset example never describes a wrong-input case) must pass
with an empty `negativeScenarios` array; requiring it to be non-empty
would be **the test inventing an expectation the source material never
supports**, exactly the mistake Part 3 names and warns against. Proven
directly as two named test cases ("Situation A" / "Situation B" in
`requirementAnalyzerOracle.test.ts`): Situation A (empty, unsupported
negative scenarios) passes; a constructed Situation B (a *fabricated*
negative scenario inventing a specific unstated rule) correctly fails —
but as a **Forbidden** violation, not a missing Required item, which is
the real distinction Part 3 is making.

**A real, honestly-stated gap found while trying to implement this**:
checklist items 6-7 ("Actor represents the user," "Feature represents
password reset") are Part 3's own named "semantic correctness" dimension
— but neither Part 3 nor Parts 1-2 ever specify an algorithm for
determining this beyond one obviously-wrong worked example. Same shape
of gap as Part 1's YAML-vs-prose mismatch in the sibling "Quality
Engineering" series: a real capability is named as necessary, with no
mechanism supplied to automate it. Stated plainly in the module's own
docstring: checks 6-7 here are **lexical-grounding** checks (non-empty,
shares a significant word with the requirement, allowing simple
singular/plural variation), not a claim of real semantic understanding.

**A real bug found and fixed while building this, caught by the test
suite itself, not by inspection**: the first version of the
lexical-grounding check used exact token-set intersection, which failed
the article's own most basic case — `actor: "User"` against a
requirement that only ever says "**users**" (plural) shares no exact
token. Fixed with the simplest stemming that resolves it (strip a
trailing "s" from either side before comparing). A second, smaller bug
in the same run: three Required checks assumed `ctx.result` was always a
real object and threw a raw `TypeError` on a missing result instead of
returning `false` — fixed with explicit null guards, since
`evaluateBoundary()` runs every check regardless of whether an earlier
one already failed (by design, so nothing can hide behind an earlier
failure).

46/46 Vitest assertions pass (up from 25), covering: the real canonical
requirement passing all 8 Required items; the Situation A/B pair above;
the real Part 2 paraphrase-equivalence example staying correctly
Allowed; each of the 8 Required items failing independently, one at a
time; and both of Part 2's real fabrication examples (OTP/5-minutes,
OAuth 2.0/AES-256) correctly tripping the Forbidden check via the reused
`checkGrounding()` module.

**Still deliberately not built**: true semantic correctness for checks
6-7 (a real, unresolved gap in the source, not papered over); TC001
executed against a live agent (same standing no-live-API-access
restriction as every build here — this oracle is the acceptance
criteria TC001 would check against, not a live-fired test); and
instruction-following as its own dimension (named by Part 3 but given no
worked example distinct from groundedness/structural correctness to
build against).

## Part 4 update: TC001 written literally, and two findings confirmed/sharpened by actually running it

Part 4 ("Writing Our First Functional Test for an AI Agent") writes TC001
for real, as actual Vitest code against the real runtime path — unlike
Part 3's framework-only treatment, this is real runnable code shown in
full, the same treatment Parts 1-2 got.

- **`tests/requirement-analyzer/TC001.test.ts`** — a faithful, literal
  reproduction of the article's own TC001, laid out by its exact 7-layer
  structure (Execution, Identity, Output, Structure, Contract, Semantics,
  Behavioral expectation), run against the real pipeline
  (`AgentConfigLoader` → `AgentRuntime` → mocked `LLMClient`, same
  standing no-live-API-access convention as every build here).

**Independent confirmation, not a new finding**: Part 4 arrives at the
exact same conclusion Part 3's oracle (`requirementAnalyzerOracle.ts`,
built last round) already implemented — never require
`negativeScenarios.length > 0` — but arrives at it through its own
concrete walkthrough (write the assertion, watch it fail on real output,
investigate, remove it) rather than from the abstract framework. A
dedicated test (`cross-checks against the Part 3 oracle`) proves both
reach the same verdict on the same real pipeline output: the oracle was
built and committed before this round ever read Part 4's text, so their
agreement is real evidence that the Part 3 design decision was correct,
not a restated premise.

**A real, verified precision gap in the article's own stated reasoning**,
checked with code rather than taken at face value: the article flags
`const parsed = JSON.parse(x); expect(() => parsed).not.toThrow();` as
wrong because "the parsing has already happened... if `JSON.parse()`
fails, the test has already thrown." True, but this understates the
actual problem — `() => parsed` is a closure returning an
already-captured value, so it **can never throw regardless of what that
value is**, even on the success path where parsing returns something
structurally nonsensical. Reproduced directly in the test suite: the
"incorrect" assertion passes unconditionally for `parsed = { this: "is
not a RequirementAnalysis at all" }`, proving it verifies nothing at
all, not just that it runs too late. Confirmed separately that this
build's own `parseAgentOutput()` (built in Part 2) already follows the
correct discipline — no change was needed there.

**A real, stated design divergence, not a bug**: the article's Layer 6
semantic checks hardcode one literal substring per field
(`.toContain("user")`, `.toContain("password")`) tied to this one
requirement's exact wording, while Part 3's `isGroundedField()` checks
for any shared significant word against the full requirement text
(generalizing to a differently-worded requirement without rewriting the
check). Neither is wrong for its own scope — stated plainly rather than
assumed one subsumes the other.

13 new Vitest assertions (59/59 total, up from 46), `tsc --strict
--noEmit` clean, `npm run build` clean, `npm audit` 0 vulnerabilities.
Full write-up in `/notes/ai-agent-testing-framework-part4-analysis.md`.

## What's faithfully reproduced, unmodified

Every file the article shows in full is reproduced as shown:
`package.json`'s scripts, `tsconfig.json` (including `strict: true`),
`AgentConfigLoader.ts` (`gray-matter`-based front matter parsing),
`LLMClient.ts` (the real OpenAI SDK pointed at Gemini's real, web-
verified OpenAI-compatible endpoint,
`https://generativelanguage.googleapis.com/v1beta/openai/`), the
`.gitignore`, and `src/index.ts`'s entry point. `AgentTypes.ts` and
`AgentRuntime.ts` carry the one structural fix above; everything else is
unchanged from the article's own shown code.

## Proven

```bash
npm install          # real dependencies, 0 vulnerabilities (npm audit)
npx tsc --noEmit      # strict mode, clean, including test files
npm test              # 59/59 passing
npm run build         # real dist/ output
npm run agent         # fails fast and cleanly without a live GEMINI_API_KEY
```

**59/59 Vitest assertions pass** across eight real test files:

- `tests/config/AgentConfigLoader.test.ts` — loads the **real**
  `requirement_analyzer.md` from disk and asserts every front-matter
  field parses correctly, that the instructions body never leaks
  front-matter fields, that a relative path resolves consistently, and
  that a missing file throws rather than returning a malformed config.
- `tests/llm/LLMClient.test.ts` — the real fail-fast-on-missing-key
  behavior, proven without any network call.
- `tests/output/parseAgentOutput.test.ts` — the real Output Requirements
  contract enforced against real fixtures: the article's own valid-
  response example parses correctly; a Markdown-fenced response, prose
  surrounding the JSON, malformed JSON, a top-level array, a missing
  required field, and a wrong-typed array field are all rejected with a
  typed `OutputContractViolation`, not a raw parse exception.
- `tests/grounding/checkGrounding.test.ts` — the article's own two real
  fabrication examples (OTP/5-minutes; OAuth 2.0/AES-256) are correctly
  flagged; the article's own real paraphrase-equivalence example and a
  genuinely clean response are correctly **not** flagged; a technical
  term or number that genuinely *is* present in the requirement is
  correctly not flagged; and a finding correctly names which field and
  array index it came from.
- `tests/requirement-analyzer/requirement-analyzer.test.ts` — the
  **full real pipeline** (`AgentConfigLoader` → `AgentRuntime` →
  `LLMClient` → `parseAgentOutput` → `checkGrounding`), using the
  deterministic mock this build's own interface fix makes possible: the
  real agent config loads, the real `AgentRuntime.run()` executes, the
  mock's exact call arguments (instructions, input, model) are asserted
  to match the real loaded config exactly, an empty-response edge case
  is handled without throwing, and a two-call sequence proves the
  runtime never caches or fabricates a result.
- `tests/oracle/qualityBoundary.test.ts` — the generic Required/Forbidden
  mechanism: passes when every Required check passes and no Forbidden
  check fires, names **every** failing check rather than stopping at the
  first, and confirms Allowed is a real absence (no list, no check
  anywhere) rather than an unused stub.
- `tests/oracle/requirementAnalyzerOracle.test.ts` — the concrete TC001
  oracle (Part 3): the real canonical requirement passing all 8 Required
  items; the Situation A/B pair at the heart of Part 3's central lesson;
  the real Part 2 paraphrase example staying correctly Allowed; each of
  the 8 Required items failing independently, one at a time; and both of
  Part 2's real fabrication examples tripping the one reused Forbidden
  check.
- `tests/requirement-analyzer/TC001.test.ts` — the literal TC001 (Part 4),
  laid out by the article's own 7-layer structure against the real
  pipeline; the investigation proving the removed negativeScenarios
  assertion really would have failed on this exact real output, and that
  the requirement gives no negative-path evidence to justify it; the
  cross-check confirming the Part 3 oracle and Part 4's own literal test
  independently agree; and the JSON.parse-assertion tautology finding,
  reproduced directly rather than taken on the article's word.

No live Gemini API access from this sandbox — same standing egress
restriction as every other build in this project (no `GEMINI_API_KEY`
is set anywhere here; `npm run agent`'s real failure mode above is the
proof of that, not a workaround).

## What's deliberately not built here

- **True semantic correctness** for the oracle's "actor"/"feature"
  checks — Part 3 names this dimension but never supplies an algorithm
  for it beyond one obviously-wrong worked example; built instead as an
  honestly-scoped lexical-grounding check, stated as a real limitation
  rather than an overclaimed solution. (This project's own
  `/builds/gate-floor-checker/` and `/builds/paired-bootstrap-ratchet/`
  are adjacent prior art on "what counts as passing" in a different
  domain, cross-referenced rather than reused here, since neither solves
  semantic correctness scoring either.)
- **A live LLM call of any kind** — no API key exists in this sandbox.
- **TC001 executed against a live agent** — `src/oracle/
  requirementAnalyzerOracle.ts` (Part 3) is the acceptance criteria
  TC001 would check a real response against, built and tested for real;
  actually firing it against a live Gemini call is still blocked by the
  same standing no-API-key restriction as everything else here.
- **Instruction-following as its own correctness dimension** — named by
  Part 3 as one of four dimensions, but given no worked example distinct
  from groundedness/structural correctness to build against.
- **Negative testing** (empty input, off-domain input, nonsense input) —
  Part 4's own closing section previews this as the next part's subject;
  the article itself defers it to a future part, not built here.
