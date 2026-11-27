# Analysis: "Testing AI Agents: A Practical Quality Engineering Journey" Part 2 (rajesh yemul, Medium)

Source: a pasted Medium article, Part 2 of the same series Part 1 of
which was already analyzed and built from this session
(`/notes/ai-agent-testing-framework-analysis.md`,
`/builds/ai-agent-testing-framework/`) — the direct continuation of the
same TypeScript project, same repo, same `requirement-analyzer` agent.
This is a continuation upload, not a new independent source, so the
treatment here differs from a normal round: confirm what actually
changed (diff against what's already built) before doing anything else.

## The real finding: Part 1's own placeholder was substantially wrong

Part 1 only showed a fragment of `requirement_analyzer.md` — the `# Role`
section alone. Last round's build had to write a reasonable placeholder
for the rest, explicitly flagged in that round's README as "this build's
own content, not a guess at not-yet-published text." Part 2 now gives
the real, complete file verbatim. Diffed directly (`diff` against the
placeholder actually on disk, not from memory) and confirmed
substantially different:

- **Responsibilities**: the real file lists Actor/Feature/Preconditions/
  Positive scenarios/Negative scenarios/Ambiguities — the placeholder
  had invented a different taxonomy (Trigger/Expected Outcome).
- **Rules**: the real file has seven specific numbered grounding rules
  ("do not invent business rules," "do not invent technical
  implementation details," "do not treat assumptions as facts," etc.) —
  the placeholder had three generic ones.
- **Output contract**: the real file requires strict JSON only, no
  Markdown fences, no surrounding prose, a specific six-field schema —
  the placeholder had invented a prose-section format entirely.

The real file replaced the placeholder, stated as a correction, same as
every "real file arrived later" precedent in this project's history
(every Trading Jarvis round).

## No new external claim to check

Read the whole article before concluding this: Part 2 is otherwise
conceptual (agent design principles — narrow responsibility, versioned
agent-as-system-component, grounding over invention, uncertainty
preservation) with nothing beyond what Part 1 already verified (Gemini's
OpenAI-compatible endpoint, Vitest's `fileParallelism` option). No new
company, product, or statistic is named.

## The real, buildable content: two worked fabrication examples, plus a real false-positive trap

Part 2 gives two concrete "the JSON is valid but the agent is still
wrong" examples, both against the same requirement ("The system should
allow users to reset their password using email."):

1. A response fabricating "OTP" and "within 5 minutes" — neither
   mentioned in the requirement.
2. A response fabricating "OAuth 2.0" and "AES-256 encryption" — neither
   mentioned either.

Both directly operationalize the real file's own Rules 1–4 and 7 (use
only supported information, don't invent business/technical details,
don't assume, don't treat assumptions as facts) — a genuine test
fixture, not a hypothetical.

Part 2 **also** gives a real paraphrase-equivalence example — two
differently-worded but behaviorally equivalent scenario descriptions
("User requests a password reset using email and successfully resets
the password." vs. "The user initiates password recovery through email
and completes the reset.") — explicitly stated by the article as "not
textually identical" but "may both satisfy the same behavioral
requirements." This is a real trap for any grounding checker built
naively from the two fabrication examples: a plain "every output word
must appear in the input" check would flag the paraphrase as fabrication
too. Verified this directly with a standalone script **before** writing
any module code: a naive full-word-presence check against that exact
pair really does flag `["user", "initiates", "recovery", "completes"]`
as unsupported — a genuine false positive, not a hypothetical risk.

## Build (extending `/builds/ai-agent-testing-framework/`, not a new build)

Same project, same repo — extended in place rather than forked, matching
this project's established convention for same-project follow-up rounds
(`prop-firm-mcp-server`, `trading-jarvis`, `agent-memory-layer` were all
extended, not reforked).

- **Real `requirement_analyzer.md` swapped in**, replacing the Part-1
  placeholder.
- **`src/output/parseAgentOutput.ts`** — enforces the real Output
  Requirements contract (valid JSON, no code fences, no surrounding
  prose, the exact six-field schema) — a rule the agent's own
  instructions state but neither Part 1 nor Part 2's own shown code ever
  checks anywhere.
- **`src/grounding/checkGrounding.ts`** — a real grounding checker built
  from the two fabrication examples, deliberately scoped to numeric/
  duration claims and a curated technical-term list (not full word
  presence), precisely because the false-positive check above showed a
  naive version would fail against the article's own paraphrase example.
  Explicitly **not** full semantic correctness checking — the article's
  own "test oracle problem," which it states is still future work for
  its own series.

Tested against the article's own real fixtures throughout: both
fabrication examples correctly flagged, the paraphrase pair and a clean
response correctly **not** flagged, a technical term/number genuinely
present in the requirement correctly not flagged, and finding reports
correctly name which field/index a fabrication came from. The existing
mocked-LLMClient pipeline test was also updated to use the real JSON
schema (it previously mocked the now-superseded placeholder's prose
format) and now runs the full real pipeline — config load → runtime →
output parsing → grounding check — end to end.

25/25 Vitest assertions pass (up from 10), `tsc --strict --noEmit`
clean, `npm run build` produces real output, `npm audit` reports 0
vulnerabilities.

**A real bug found while verifying, in this round's own test setup, not
the source article**: `npm test` run right after `npm run build`
reported 50 passing tests — exactly double. `tsc`'s compiled `dist/`
output includes copies of every `tests/**/*.ts` file, and Vitest's
default include pattern was silently matching those too, double-running
every test. Caught by actually counting the real assertions (5 files ×
their real counts = 25) rather than trusting the first printed number —
two different inflated totals (35, then 50) were seen at different
points depending on how stale `dist/` happened to be, which was itself
the tell that something was wrong. Fixed with an explicit
`exclude: ["**/node_modules/**", "**/dist/**"]` in `vitest.config.ts`.
