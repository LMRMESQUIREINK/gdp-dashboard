# Deep analysis: "20 Agentic Engineering Concepts" / "20 System Design Concepts"

Source: one uploaded text file carrying two separate Medium articles by
the same author, Sakshi Jaiswal — "20 Agentic Engineering Concepts Every
AI Engineer Should Know" and "20 System Design Concepts Every Engineer
Needs Before Building an AI Agent." Second round run through the
`ruthless-gate` skill, exercising its own stated rule for when two or
more sources arrive together: audit each on its own, then read them
against each other, tag every claim by source, require each source to
get at least one credit and one stop. Full audit with every finding's
evidence: `/builds/agentic-concepts-gate/`.

## What this is

Two overlapping-but-distinct "20 concepts" lists covering the same
general territory — reasoning patterns (ReAct, Plan-and-Execute,
Reflexion), memory, tool-calling protocols (MCP, A2A), multi-agent
coordination, and production safety (guardrails, HITL, blast radius) —
written for engineers moving an agent prototype toward production.

## The two things worth knowing without reading the full verdict page

**Several dated, checkable technical claims were verified against
outside sources, and most held up exactly.** MCP's December 2025
donation to the Agentic AI Foundation (a Linux Foundation project,
co-founded with Block and OpenAI) matches Anthropic's own announcement
precisely. LangGraph's October 2025 1.0 release, the OWASP "LLM01:2025"
prompt-injection ranking, and the core facts of the July 2025
Replit/SaaStr production-database deletion all check out against
independent reporting. One claim — Microsoft Agent Framework's GA date,
stated as "April 2, 2026" — turned out more precise than the public
record currently agrees on (sources split between April 2 and 3).

**The strongest finding came from reading the two articles against each
other, not from either one alone.** Article1 names "blast radius" as an
explicit concept: large-impact actions need a human checkpoint enforced
by permissions, not just instructions. Article2 separately recounts the
Replit incident — an agent that deleted a production database despite
being repeatedly told not to. Neither article connects the two, but read
together, the Replit incident is close to a textbook case of exactly
what blast radius warns about: instructions alone, no hard permission
boundary. That's the kind of gap-finding the `ruthless-gate` procedure
is built to surface and the main reason this round's cross-source
reading was worth doing rather than auditing each article in isolation.

## What's genuinely well-reasoned

Both articles' prose scored zero findings against this project's own
`/builds/humanizer/` AI-tell detector — a real, checked result, not an
assumption, across 3,669 combined words. Where the two pieces describe
the same mechanism (ReAct, Plan-and-Execute, HITL), their technical
descriptions are consistent with each other despite being written
separately. Both articles' own "20 concepts" framing is numerically
exact on direct count.

## What doesn't hold up, or isn't disclosed

Article2 covers MCP in comparable technical depth to article1 — version
history, JSON-RPC mechanics, adoption — yet never mentions the Agentic
AI Foundation / Linux Foundation governance story article1 covers in
specific detail, despite both pieces being current enough to cite 2026
events. Separately, the two articles use genuinely different memory
taxonomies: article2's "procedural memory" (learned habits baked into a
system prompt or fine-tune) has no equivalent concept anywhere among
article1's 20 items — not a renaming, a real difference in how the same
author splits the same subject across two pieces.

## What's built from this

No separate code build this round — same call as the WordPress prompt
pack round: the verdict page itself is the deliverable, built to the
same four-file shape (`index.html`, `data.js`, `test.js`, `README.md`)
established last round, with one structural addition this round's
two-source format required: a per-source credit/stop balance panel and
a `source` tag on every finding, both checked by `test.js` (each article
must get ≥1 credit and ≥1 stop, verified programmatically, not just
by eye). 122/122 assertions pass, clean on the first real run — full
story in `/builds/agentic-concepts-gate/README.md`.
