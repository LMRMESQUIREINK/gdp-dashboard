# Analysis: "Building an AI Agent Testing Framework from Scratch with TypeScript and Vitest" (rajesh yemul, Medium)

Source: a pasted Medium article, Part 1 of a new series by an author this
project has already analyzed once this session — the "Quality
Engineering"/Season 4 orchestration series
(`/notes/orchestration-agent-loop-analysis.md`,
`/builds/orchestration-decision-engine/`). Unlike that article, this one
is real, complete, runnable TypeScript code shown in full (every file's
exact contents given), not a conceptual framework — closer in kind to
the WordPress-tutorial or scroll-scrub-hero rounds (a real project to
actually build and run) than the GitHub-repo or pure-conceptual rounds.

## A real connection between this author's two series

This article's own worked example defines an agent with
`agentId: requirement-analyzer`. The previously-analyzed "Quality
Engineering" series' Season 3 producer pipeline names "Requirement
Analyzer" as its first stage. Neither article cites the other, but read
together they strongly suggest this "Testing Framework from Scratch"
series is the technical foundation underneath that higher-level
orchestration narrative — visible only by having analyzed both in the
same session.

## What checked out

Two specific technical claims web-verified against primary sources:

- **Gemini's OpenAI-compatible endpoint**
  (`https://generativelanguage.googleapis.com/v1beta/openai/`) — real
  and current, confirmed against Google's own documentation
  (`ai.google.dev/gemini-api/docs/openai`). The article's exact base URL
  matches, including the trailing slash.
- **Vitest's `fileParallelism` config option** — real, confirmed against
  the official Vitest docs: boolean, default `true`, and setting it
  `false` forces `maxWorkers` to 1 — exactly matching the article's own
  comment ("runs one test file at a time").

Also confirmed correct throughout (not just asserted, cross-checked
against `tsconfig.json`'s own `"module": "NodeNext"` setting): every
shown import uses a `.js` extension on a `.ts` source file
(`from "../types/AgentTypes.js"`) — the correct, frequently-gotten-wrong
requirement for NodeNext module resolution. The article gets this right
consistently across every file it shows.

## Two real bugs found, both reproduced directly rather than spotted by eye alone

1. **A genuine syntax error in the shown `vitest.config.ts`.** Counted
   braces in the pasted snippet: 3 `{` to 4 `}` — an unbalanced object
   literal. Confirmed as a real bug, not a transcription artifact, by
   actually running the snippet as plain ESM:
   `SyntaxError: missing ) after argument list`, pointing exactly at the
   extra closing brace. (A first attempt to check this with
   `tsc --noEmit`/`node --check` directly on the `.ts` file silently
   passed — a dead end worth noting: this sandbox's TypeScript-file
   handling doesn't reliably syntax-check a bare snippet outside a real
   project context, so the real repro needed to strip the file down to
   plain JS and actually execute it.)
2. **A real gap between the article's own stated motivation and what
   its own shown code delivers.** The article explicitly credits the
   `LLMClient` abstraction with enabling "deterministic tests for the
   testing framework itself" — but `AgentRuntime`'s constructor types
   its parameter as the **concrete** `LLMClient` class. Reproduced
   directly: constructing `AgentRuntime` with a plain object
   implementing only `generate()` fails `tsc --strict` with
   `error TS2741: Property 'client' is missing in type '...' but required in type 'LLMClient'`
   — TypeScript class types are matched structurally **including
   private fields**, and the real class has a private `client: OpenAI`
   field. The article's own stated reason for the abstraction
   (swap in a mock, write deterministic tests) is exactly what this
   concrete-class typing blocks.

## Build: `ai-agent-testing-framework`

`/builds/ai-agent-testing-framework/` — not a generalized mechanism
extracted from the article (unlike most rounds in this project), but a
faithful, actually-installed, actually-run reproduction of the real
project the article builds, since the source itself is concrete runnable
code rather than a vendor product or a conceptual framework. Every file
the article shows is reproduced as shown; the two bugs above are fixed
(`vitest.config.ts`'s brace balanced; `AgentRuntime` now depends on a
real `LLMClient` interface extracted into `AgentTypes.ts`, with the
concrete class `implements`-ing it).

Installed for real (`npm install`, 0 vulnerabilities per `npm audit`),
compiled under `strict` mode cleanly (`tsc --noEmit`), and proven with a
real 10-assertion Vitest suite across three files — including the test
the article's own interface fix makes possible for the first time: the
real `AgentConfigLoader` loading a real `requirement_analyzer.md`,
wired through the real `AgentRuntime`, against a deterministic mock
`LLMClient` (no live Gemini access from this sandbox, same standing
restriction as every build here) — with the mock's exact call arguments
asserted to match the real loaded config, not just "didn't crash."
`npm run build` produces a real `dist/` output; `npm run agent` fails
fast and cleanly without a live API key, proven as a real subprocess
run matching the article's own stated fail-fast design.

One piece filled in rather than left a stub: `requirement_analyzer.md`'s
full instructions (the article shows only a fragment, deferring the
full agent definition to Part 2 of its own series) — written as this
build's own reasonable content, stated plainly rather than presented as
the article's actual not-yet-published text.

Not built: the article's own explicitly-stated next challenge (the
test-oracle problem — scoring whether an AI response is semantically
correct) and TC001, both deferred by the source itself to a future
part of its own series, so out of scope for a faithful Part 1
reproduction.
