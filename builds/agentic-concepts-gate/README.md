# RUTHLESS GATE — Agentic Engineering Concepts

A verdict page auditing two Sakshi Jaiswal Medium articles, uploaded
together in one text file: "20 Agentic Engineering Concepts Every AI
Engineer Should Know" (article1) and "20 System Design Concepts Every
Engineer Needs Before Building an AI Agent" (article2). Built with the
`ruthless-gate` procedure's own rule for multi-source rounds: each
article audited on its own, then read against each other, every finding
tagged by which source it came from, and each source required to get at
least one credit and one stop of its own.

Open `index.html` in a browser, or see `data.js` for the raw ledger.

## Coverage — what this audit did not check

- Neither article's embedded images, further-reading links, or the
  author's LinkedIn/Instagram profiles were fetched — this audit covers
  the article text only.
- Article2's claim that LangGraph "runs in production at companies
  including Uber, LinkedIn and Klarna" was not independently confirmed —
  no case study or named engineering team was found or checked for any
  of the three companies.
- Article1's specific MCP spec-revision claims (OAuth 2.1 in the March
  2025 spec, async Tasks in November 2025, statelessness in the July
  2026 revision) were not individually checked against the MCP spec's
  own changelog — only the higher-level Linux Foundation donation and
  governance claims were verified.
- The AG2 community fork of AutoGen (article2's closing aside) was not
  independently confirmed as still actively maintained.
- Whether article1 was written after article2 — which would explain why
  only article1 covers MCP's December 2025 Foundation donation — was not
  confirmed; the coverage gap below is reported as an observed
  difference in what each piece covers, not a claim about intent or
  publish order.

## Findings (summary — full ledger with evidence in `data.js`)

**DEEP** — what each source is, measured:
- **Credit** (both): both articles' own "20 concepts" claims are
  numerically exact — confirmed by direct count, unlike the off-by-one
  found in the separate WordPress prompt pack audited last round.
- **Credit** (both): the combined 3,669-word text scores zero on this
  project's own `/builds/humanizer/` AI-writing-tell detector — article1's
  own implicit claim to rigor ("not the blog-post version") checked, not
  just taken on its word.
- **Stop** (article1): concept 4, "the agentic loop," is explicitly
  framed as a synthesis of concepts 1–3 rather than an independent 20th
  item — a minor internal-counting wrinkle.

**DEEPER** — the framework, web-verified against outside sources:
- **Credit** (article1): MCP's Linux Foundation / Agentic AI Foundation
  governance timeline — December 2025, co-founded with Block and
  OpenAI — matches Anthropic's own announcement exactly.
- **Stop** (article1): the named supporter list ("Google, Microsoft and
  AWS") omits two of the real five supporters (Cloudflare, Bloomberg).
- **Credit** (article2): the Replit/SaaStr production-database deletion
  is a real, multiply-corroborated July 2025 incident, reported
  accurately in its core facts.
- **Credit** (article2): "LangGraph reached 1.0 in October 2025" is
  accurate.
- **Stop** (article2): Microsoft Agent Framework's GA date is stated
  with more precision ("April 2, 2026") than independent sources
  currently agree on (some say April 3).
- **Credit** (article1): the OWASP "LLM01:2025" citation for prompt
  injection is accurate — both the label and the #1 ranking.
- **Stop** (article2): the LangGraph company-adoption claim (Uber,
  LinkedIn, Klarna) carries no citation and wasn't independently
  confirmed.

**DEEPEREST** — internal seams, within and across the two pieces:
- **Stop** (both): the two articles use genuinely different, non-
  equivalent memory taxonomies — article1's 2-category model has no
  concept matching article2's "procedural memory" at all, not a renaming.
- **Credit** (both): everywhere the two articles do cover the same
  mechanism (ReAct, Plan-and-Execute, HITL), their technical descriptions
  are consistent, not contradictory.
- **Stop** (article1): A2A gets its own named, numbered concept in
  article1 but no equivalent standalone treatment anywhere in article2,
  despite article2 having a natural home for it in its own multi-agent
  section.

**DEEPEREST-EST** — the cross-source reading:
- **Stop** (both): article2 covers MCP in comparable technical depth to
  article1 yet never mentions the governance story (Foundation donation,
  named co-founders) that article1 covers in detail — a real, observable
  coverage gap on the identical topic, visible only reading both
  together.
- **Credit** (both): read together, the Replit/SaaStr incident is a
  concrete, real-world illustration of exactly what article1's "blast
  radius" concept warns about — instructions alone, no hard permission
  boundary — a connection neither article makes explicit. This is the
  strongest finding this round: one source's abstract framework
  predicting another source's documented failure.

**Verdict counts**: 15 findings — 8 credit, 7 stop. Per-source balance:
article1 6 credit / 5 stop, article2 6 credit / 4 stop (both ≥1 each,
required by the procedure). Business rules: all three marked n/a — this
is educational writing with a standard Medium friend-link, not a product
funnel, so the rule table doesn't describe a situation that exists here
(marked n/a rather than forced into clears/COLLIDES, per the procedure's
own instruction not to inflate the collision count).

## Verification

```bash
node test.js
```

122/122 assertions pass on the real run, clean on the first pass (no
bugs found this round, unlike last round's table-overflow fix) — every
finding's evidence string, provenance, and source tag; the per-source
credit≥1/stop≥1 requirement checked programmatically for both articles;
both articles' "20 concepts" counts independently recomputed from the
raw text; the Humanizer zero-finding claim re-run live inside the test
(not trusted from `data.js`'s cached report of an earlier run); the
"procedural memory" cross-source claim recomputed with a direct regex
check against each article's own text; WCAG contrast computed for the
required palette; ≥30° hue separation between go/caution/stop; a real
Chromium render at desktop and mobile widths with zero console errors
and no overflow.

## Sources

- The audited text: `source/raw.txt` (as-uploaded; sha256 recorded in
  `data.js`).
- This project's own `/builds/humanizer/patterns.py`, re-run live by
  `test.js` against the combined article text.
- MCP governance: anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation.
- The Replit/SaaStr incident: theregister.com/2025/07/21/replit_saastr_vibe_coding_incident,
  eweek.com/news/replit-ai-coding-assistant-failure, techtarget.com/it-infrastructure/news/366627829.
- LangGraph 1.0 and Microsoft Agent Framework GA dates: realpython.com/ref/ai-coding-tools/langgraph,
  devblogs.microsoft.com/agent-framework.
- OWASP LLM01:2025: coralogix.com/ai-blog/owasp-top-10-for-llm-applications,
  guptadeepak.com/agent-security/threats/llm01.
