# ai-agent-testing-framework

A real, working reproduction of the TypeScript + Vitest project from
"Building an AI Agent Testing Framework from Scratch with TypeScript and
Vitest" (rajesh yemul, Medium, Part 1) — the author's own small,
from-scratch agent-execution harness (Markdown+YAML agent definitions →
`AgentConfigLoader` → `AgentRuntime` → `LLMClient` → an LLM → `AgentResult`
→ Vitest). Unlike most sources in this project, this article *is* real,
runnable code shown in full, not a conceptual framework to extract a
mechanism from — so this build is a faithful reproduction, actually
installed and run in this sandbox, with two real bugs found and fixed
along the way. Analyzed in
`/notes/ai-agent-testing-framework-analysis.md`.

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

**One piece filled in rather than left as a stub**: the article shows
only a fragment of `requirement_analyzer.md`'s instructions ("we also
define responsibilities and rules" without full text — Part 2 of the
series promises to cover this agent definition in full). This build
wrote a complete, reasonable version (Role/Responsibilities/Rules/Output
Contract) so `AgentConfigLoader` has a real file to parse — stated
plainly as this build's own content, not a guess at the article's
actual, not-yet-published Part 2 text.

## Proven

```bash
npm install          # real dependencies, 0 vulnerabilities (npm audit)
npx tsc --noEmit      # strict mode, clean, including test files
npm test              # 10/10 passing
npm run build         # real dist/ output
npm run agent         # fails fast and cleanly without a live GEMINI_API_KEY
```

**10/10 Vitest assertions pass** across three real test files:

- `tests/config/AgentConfigLoader.test.ts` — loads the **real**
  `requirement_analyzer.md` from disk and asserts every front-matter
  field parses correctly, that the instructions body never leaks
  front-matter fields, that a relative path resolves consistently, and
  that a missing file throws rather than returning a malformed config.
- `tests/llm/LLMClient.test.ts` — the real fail-fast-on-missing-key
  behavior, proven without any network call.
- `tests/requirement-analyzer/requirement-analyzer.test.ts` — the
  **full real pipeline** (`AgentConfigLoader` → `AgentRuntime` →
  `LLMClient`), using the deterministic mock this build's own interface
  fix makes possible: the real agent config loads, the real
  `AgentRuntime.run()` executes, the mock's exact call arguments
  (instructions, input, model) are asserted to match the real loaded
  config exactly, an empty-response edge case is handled without
  throwing, and a two-call sequence proves the runtime never caches or
  fabricates a result.

No live Gemini API access from this sandbox — same standing egress
restriction as every other build in this project (no `GEMINI_API_KEY`
is set anywhere here; `npm run agent`'s real failure mode above is the
proof of that, not a workaround).

## What's deliberately not built here

- **The actual test-oracle problem** — "how do we define the boundary
  between a correct AI response and an incorrect one" — the article's
  own explicitly-stated next challenge, deferred to a future part of
  its own series. Nothing here scores or validates agent output
  semantically; that's out of scope for a Part 1 reproduction.
  (This project's own `/builds/gate-floor-checker/` and `/builds/
  paired-bootstrap-ratchet/` are adjacent prior art on "what counts as
  passing" in a different domain, cross-referenced rather than reused
  here, since neither solves semantic correctness scoring either.)
- **A live LLM call of any kind** — no API key exists in this sandbox.
- **TC001**, the article's own promised first real functional test —
  the article itself defers writing it to a future part.
