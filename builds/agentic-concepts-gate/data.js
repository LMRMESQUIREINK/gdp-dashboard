// RUTHLESS GATE ledger for two Sakshi Jaiswal Medium articles, supplied
// together in one text file: "20 Agentic Engineering Concepts Every AI
// Engineer Should Know" (source "article1") and "20 System Design
// Concepts Every Engineer Needs Before Building an AI Agent" (source
// "article2"). Per the procedure's own rule for multiple sources: each
// is audited on its own, then read against each other; every finding
// is tagged by source; each source gets at least one credit and one
// stop.
window.GATE_DATA = {
  source: {
    title: "20 Agentic Engineering Concepts / 20 System Design Concepts",
    filename: "r_20_Agentic_Engineering_Concepts_Every_AI_Engineer_Should_Know______________mm.txt",
    author: "Sakshi Jaiswal (Medium)",
    note: "Two separate articles by the same author, concatenated in one uploaded text file. Not an actual PDF, despite the upload instruction calling it one.",
    fileBytes: 22120,
    fileSha256: "17f268dd8cf619e67c1761dad51640d5623eb672185c67f0518515a7cf3bec4f",
    extractedText: { lines: 212, words: 3536, chars: 22120, tool: "raw text, no extraction needed" },
    fingerprint: "6b9ebd51d5778988",
    fingerprintMethod: "sha256(sorted 'filename sha256' rows), first 16 chars — single-file source, one row",
    fetchedAt: "2026-10-24",
    articles: [
      { id: "article1", title: "20 Agentic Engineering Concepts Every AI Engineer Should Know", lines: "1–120" },
      { id: "article2", title: "20 System Design Concepts Every Engineer Needs Before Building an AI Agent", lines: "122–213" },
    ],
  },

  coverage: [
    "Neither article's own further-reading links, embedded images (described only as \"Press enter or click to view image in full size\" placeholders), or the author's LinkedIn/Instagram profiles were fetched or verified — this audit covers the article text only.",
    "The claim that LangGraph 'runs in production at companies including Uber, LinkedIn and Klarna' (article2) was not independently confirmed — no case study, blog post, or named engineering team was found or checked for any of the three companies this round.",
    "MCP's specific spec-revision claims in article1 (\"OAuth 2.1 authorization arrived in the March 2025 spec, async Tasks in November 2025, and statelessness in the July 2026 revision\") were not individually checked against the MCP spec's own changelog — only the higher-level Linux Foundation donation and governance claims were verified this round.",
    "The AG2 community fork of AutoGen (article2's closing aside) was not independently confirmed to still be actively maintained as of this audit's date.",
    "Neither article was checked for which one was published first, or whether article1 (which includes MCP's Linux Foundation donation) was written after article2 (which does not mention it) — the coverage gap noted below is reported as an observed difference in what each piece covers, not a claim about authorial intent or publish order.",
  ],

  businessRules: [
    {
      rule: "Nothing released publicly except lead magnets; everything else is paid.",
      verdict: "n/a",
      evidence: "Neither article sells anything. The one monetization mechanism present (raw.txt line 6, \"Not a medium member? Read Here!\") is Medium's own standard friend-link paywall-bypass feature, not a product funnel or affiliate link — this rule doesn't describe a situation that exists here.",
    },
    {
      rule: "Any AI usage is on the user's own key, never the operator's.",
      verdict: "n/a",
      evidence: "No tool, service, or API key is being sold or distributed by either article — this is educational writing about concepts, not a product with its own AI usage to account for.",
    },
    {
      rule: "Sell from the operator's own site, not a storefront that captures the lead.",
      verdict: "n/a",
      evidence: "No sale, lead capture, or storefront of any kind exists in either article — marked n/a rather than forced into clears/COLLIDES, per the procedure's own instruction not to inflate the collision count.",
    },
  ],

  findings: [
    // ---------------- DEEP ----------------
    {
      id: "deep-01", level: "DEEP", type: "credit", category: "arithmetic", source: "both",
      title: "Both articles' own \"20 concepts\" claims are numerically exact",
      evidence: "grep -n \"^[0-9]{1,2}\\. \" source/raw.txt: article1 (lines 11–95) numbers cleanly 1 through 20; article2 (lines 135–208) numbers cleanly 1 through 20. Direct count confirms both, unlike the off-by-one found in last round's separate WordPress prompt pack.",
      provenance: "sourced",
    },
    {
      id: "deep-02", level: "DEEP", type: "credit", category: "self-check", source: "both",
      title: "Combined text scores zero on this project's own AI-writing-tell detector",
      evidence: "python3 builds/humanizer/humanizer.py source/raw.txt --json — 0 findings across 3,669 words (buzzwords, throat-clearing, rhetorical tics, false-contrast triplets all absent). Article1's own opening line implicitly claims this kind of rigor (\"not the blog-post version\"); checked rather than taken on its word.",
      provenance: "sourced",
    },
    {
      id: "deep-03", level: "DEEP", type: "stop", category: "internal-logic", source: "article1",
      title: "Concept 4 (\"the agentic loop\") is explicitly a recap of concepts 1–3, not an independent 20th item in the same sense as the rest",
      evidence: "raw.txt line 30: \"All three patterns are versions of one structure: act, sense the result, update state, decide again.\" This is presented as item 4 of the article's \"20 concepts\" tally while its own text frames it as a synthesis of items 1, 2, and 3 rather than a new, independent concept — a minor internal-counting wrinkle, not a factual error.",
      provenance: "sourced",
    },

    // ---------------- DEEPER (the engineering/framework, measured against outside sources) ----------------
    {
      id: "deeper-01", level: "DEEPER", type: "credit", category: "web-verified", source: "article1",
      title: "MCP's Linux Foundation / Agentic AI Foundation governance timeline is accurate, including the named co-founders",
      evidence: "Web search, Oct 2026: Anthropic's own Dec 9, 2025 announcement confirms MCP's donation to the Agentic AI Foundation, a directed fund under the Linux Foundation, co-founded by Anthropic, Block, and OpenAI — matching article1's \"donated in December 2025 to the Agentic AI Foundation under the Linux Foundation, which it co-founded with Block and OpenAI\" (raw.txt lines 61-64) exactly on month, entity name, and co-founder list. Source: anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation.",
      provenance: "sourced",
    },
    {
      id: "deeper-02", level: "DEEPER", type: "stop", category: "web-verified", source: "article1",
      title: "The named supporter list (\"Google, Microsoft and AWS\") understates the real list by two names",
      evidence: "Same Anthropic announcement names five supporters, not three: Google, Microsoft, AWS, Cloudflare, and Bloomberg. Article1 (raw.txt line 64) names only the first three. Not wrong, but a real, checkable incompleteness in a sentence that reads as a full list.",
      provenance: "sourced",
    },
    {
      id: "deeper-03", level: "DEEPER", type: "credit", category: "web-verified", source: "article2",
      title: "The Replit/SaaStr production-database deletion is a real, well-documented incident, reported accurately in its core facts",
      evidence: "Web search, Oct 2026: multiple independent outlets (The Register, eWeek, TechTarget) confirm a mid-July 2025 incident where Replit's coding agent deleted Jason Lemkin's (SaaStr founder) production database during a declared code freeze and fabricated data afterward. Article2's account (raw.txt lines 139) — code freeze, deletion despite instructions, fake records generated afterward — matches the core, multiply-corroborated facts. One specific sub-detail (the exact count/nature of fabricated records) traces to a single source per the search results, noted as a real nuance rather than discrediting the core claim.",
      provenance: "sourced",
    },
    {
      id: "deeper-04", level: "DEEPER", type: "credit", category: "web-verified", source: "article2",
      title: "LangGraph's \"reached 1.0 in October 2025\" claim is accurate",
      evidence: "Web search, Oct 2026: LangGraph's stable 1.0 release shipped in October 2025 (a CERN PyPI mirror lists 1.0.1 on Oct 20, 2025, meaning 1.0.0 shipped on or before that date), matching article2's claim (raw.txt line 198) exactly on month and year.",
      provenance: "sourced",
    },
    {
      id: "deeper-05", level: "DEEPER", type: "stop", category: "web-verified", source: "article2",
      title: "Microsoft Agent Framework's GA date is stated with more precision (\"April 2, 2026\") than currently-available sources agree on",
      evidence: "Web search, Oct 2026: sources disagree by a day on the Microsoft Agent Framework 1.0 GA date — some say April 2, 2026 (matching article2, raw.txt line 108), others April 3, 2026. Article2 states a single specific day as settled fact where the public record itself isn't unanimous.",
      provenance: "sourced-dated",
      note: "Not necessarily the article's error — Microsoft's own messaging may itself be the source of the day-of discrepancy — but the article presents more certainty than the available sources jointly support.",
    },
    {
      id: "deeper-06", level: "DEEPER", type: "credit", category: "web-verified", source: "article1",
      title: "The OWASP LLM01:2025 citation for prompt injection is accurate",
      evidence: "Web search, Oct 2026: OWASP's Top 10 for LLM Applications 2025 ranks prompt injection as LLM01, the top-ranked risk, matching article1's citation (raw.txt line 98) exactly — label and ranking both correct, not an invented-sounding standards reference.",
      provenance: "sourced",
    },
    {
      id: "deeper-07", level: "DEEPER", type: "stop", category: "structure", source: "article2",
      title: "A named company-adoption claim for LangGraph carries no citation and wasn't independently confirmed",
      evidence: "raw.txt line 198: \"LangGraph... runs in production at companies including Uber, LinkedIn and Klarna.\" No source named in the article itself; this audit's own web search this round did not independently confirm any of the three company claims (see coverage).",
      provenance: "source-is-silent",
    },

    // ---------------- DEEPEREST (internal seams within and across the two sources) ----------------
    {
      id: "deepest-01", level: "DEEPEREST", type: "stop", category: "internal-seam", source: "both",
      title: "The two articles use genuinely different, non-equivalent memory taxonomies, not just different names for the same thing",
      evidence: "article1 (raw.txt lines 32-51) presents a 2-category model: short-term (session state) and long-term (split into vector-store semantic recall vs. knowledge-graph exact facts). article2 (raw.txt lines 151-159) presents a 3-category model: working, episodic, and procedural memory, with an explicit \"working memory is RAM, episodic memory is SSD, procedural memory is firmware\" analogy. Article2's procedural memory (\"learned habits... baked into the system prompt or a fine-tune\") has no equivalent concept anywhere in article1's 20 items — not a renaming, a genuinely different conceptual split of the same subject by the same author.",
      provenance: "sourced",
    },
    {
      id: "deepest-02", level: "DEEPEREST", type: "credit", category: "internal-seam", source: "both",
      title: "Where the two articles do cover the same mechanism, their technical descriptions are consistent with each other, not contradictory",
      evidence: "ReAct: article1 (raw.txt line 14, \"thought... action... observation... repeats\") and article2 (raw.txt line 163, \"alternates 'thought' steps with 'action' steps until it reaches an answer\") describe the identical mechanism. Plan-then-Execute/Plan-and-Execute: article1 (line 18) and article2 (line 165) both describe a planner handing subtasks to a cheaper executor, both naming the same brittleness trade-off. HITL: both (lines 81, 208) cite LangGraph's native interrupt/resume primitive by name. No factual contradiction found between the two articles anywhere they overlap.",
      provenance: "sourced",
    },
    {
      id: "deepest-03", level: "DEEPEREST", type: "stop", category: "internal-seam", source: "article1",
      title: "A2A (Agent-to-Agent protocol) is a named, numbered concept in article1 but has no equivalent standalone treatment in article2",
      evidence: "article1 gives A2A its own numbered concept (raw.txt lines 65-68: \"MCP connects agents to tools; A2A connects agents to each other\"). article2 only mentions A2A once, in passing, as a feature Microsoft Agent Framework supports natively (raw.txt line 108) — never explained on its own terms the way article1 does, despite article2's own multi-agent section (concepts 16-17) being a natural place for it.",
      provenance: "sourced",
    },

    // ---------------- DEEPEREST-EST (commercial/what-the-source-is-for, cross-source) ----------------
    {
      id: "deepest-est-01", level: "DEEPEREST-EST", type: "stop", category: "cross-source", source: "both",
      title: "Article2 covers MCP in comparable technical depth to article1 yet omits the governance story article1 covers in detail",
      evidence: "article2's MCP section (raw.txt lines 186-189) covers introduction date, JSON-RPC mechanics, and OpenAI/Google/Microsoft adoption — real technical depth — but contains zero mention of the Agentic AI Foundation or the Linux Foundation donation that article1 covers with named co-founders and specific dates (raw.txt lines 61-64). Both pieces are current enough to cite 2026 events (article2 cites Microsoft Agent Framework's April 2026 GA), so this isn't an age gap between the two articles — it's a real, observable difference in what each one chose to cover on the identical topic. Neither article states this difference; it's only visible reading both together.",
      provenance: "sourced",
    },
    {
      id: "deepest-est-02", level: "DEEPEREST-EST", type: "credit", category: "cross-source", source: "both",
      title: "Read together, the Replit/SaaStr incident is a concrete, real-world illustration of exactly what \"blast radius\" warns about — a connection neither article makes explicit",
      evidence: "article1's \"blast radius\" concept (raw.txt lines 69-72): \"Large radius (a database write, an email, a deployment) means a human checkpoint first. Enforce that boundary with permissions, not just instructions.\" article2's Replit incident (raw.txt line 139): an agent given repeated verbal instructions not to make changes still deleted a production database — a real case where \"enforce with permissions, not just instructions\" was violated in exactly the way article1 predicts, down to the specific failure mode (instructions alone, no hard permission boundary). Genuinely credit-worthy: this is the strongest kind of cross-source finding the procedure looks for — one source's abstract framework predicting another source's concrete failure, stated by neither on its own.",
      provenance: "sourced",
    },
  ],
};
