# ai-agent-testing-framework

A real, working reproduction of the TypeScript + Vitest project from
rajesh yemul's two-part (so far) Medium series: "Building an AI Agent
Testing Framework from Scratch with TypeScript and Vitest" (Part 1) and
"Testing AI Agents: A Practical Quality Engineering Journey" (Part 2) —
the author's own small, from-scratch agent-execution harness
(Markdown+YAML agent definitions → `AgentConfigLoader` → `AgentRuntime` →
`LLMClient` → an LLM → `AgentResult` → Vitest). Unlike most sources in
this project, this article series *is* real, runnable code shown in
full, not a conceptual framework to extract a mechanism from — so this
build is a faithful, continuously-updated reproduction, actually
installed and run in this sandbox, with real bugs found and fixed along
the way in both rounds. Analyzed in
`/notes/ai-agent-testing-framework-analysis.md` (Part 1) and
`/notes/ai-agent-testing-framework-part2-analysis.md` (Part 2).

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
npm test              # 25/25 passing
npm run build         # real dist/ output
npm run agent         # fails fast and cleanly without a live GEMINI_API_KEY
```

**25/25 Vitest assertions pass** across five real test files:

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

No live Gemini API access from this sandbox — same standing egress
restriction as every other build in this project (no `GEMINI_API_KEY`
is set anywhere here; `npm run agent`'s real failure mode above is the
proof of that, not a workaround).

## What's deliberately not built here

- **The actual test-oracle problem** — "how do we define the boundary
  between a correct AI response and an incorrect one" — the article's
  own explicitly-stated next challenge, deferred by Part 2 to a future
  part of its own series. `checkGrounding()` above is a narrow,
  evidenced step toward this (catching the two concrete fabrication
  patterns Part 2 demonstrates), explicitly **not** a full semantic
  correctness oracle. (This project's own `/builds/gate-floor-checker/`
  and `/builds/paired-bootstrap-ratchet/` are adjacent prior art on
  "what counts as passing" in a different domain, cross-referenced
  rather than reused here, since neither solves semantic correctness
  scoring either.)
- **A live LLM call of any kind** — no API key exists in this sandbox.
- **TC001**, the article's own promised first real functional test —
  the article itself defers writing it to a future part.
