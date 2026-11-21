// RUTHLESS GATE ledger for "The $1M+ Solo Grok Bot Business (Full Course)"
// -- a PDF upload whose actual content, measured directly, is a single
// transcribed podcast episode (Greg Isenberg's "Startup Ideas" show,
// interviewing Nick Vasilescu, co-founder of Orgo) run through an
// automated PDF office-converter, with an AI-generated "Key Points" /
// "Numbered Section Summaries" layer bolted on top of the raw,
// ASR-garbled transcript below it.
window.GATE_DATA = {
  source: {
    title: "The $1M+ Solo Grok Bot Business (Full Course)",
    filename: "r_The_1M_Solo_Grok_Bot_Business_Full_Course.pdf",
    producer: "PDFTron built-in office converter, V9.4.2-a2633dd18a",
    pages: 23,
    fileBytes: 94099,
    fileSha256: "4548181dc235edae32df814ccad7520ea043ecfa34351a63844ac0128c29cd24",
    extractedText: { lines: 834, words: 9702, chars: 50152, tool: "pdftotext -layout" },
    extractedSha256: "808432d6dc9a0bda6a4a26219edfc9eabac5a4588d6f26231452de3d9a087bba",
    fingerprint: "8d69750c1c396346",
    fingerprintMethod: "sha256(sorted 'filename sha256' rows), first 16 chars -- single-file source, one row",
    fetchedAt: "2026-11-04",
    pdfCreated: "2026-11-04T18:48:53Z",
    note: "PDF metadata's own CreationDate/ModDate is the same calendar day as this audit -- a freshly-generated conversion, not an archival document.",
  },

  coverage: [
    "No video, audio, image, or interactive element exists in this PDF -- confirmed by per-page word count across all 23 pages (pdftotext -layout -f N -l N for N in 1..23), every page text-dense (323-490 words; page 23, the closing, is shorter at 85 words). Nothing was missed by reading text only.",
    "The guest's and host's claimed public profiles (Nick Vasilescu / Orgo, Greg Isenberg's podcast) were checked by web search only far enough to confirm Nick's real identity and Orgo's real product description -- their other claims (customer counts, revenue, the specific insurance-agency customer mentioned in the transcript) were not independently verified and are not the subject of any finding below.",
    "The claimed open-source 'Bops' repository was never given a URL or name anywhere in the source text (see deeper-04), so it could not be cloned, read, or verified in any way this round -- the audit stops at 'the source never supplies a locatable address,' not at an attempt to guess one.",
    "'Agent Mail' and 'Agent Phone' were checked only against general web search for products of similar function and near-identical name (AgenticMail, AgentPhone) -- no attempt was made to find an exact literal product named 'Agent Mail' or 'Agent Phone', since the close-but-not-exact naming is itself the finding (see deeper-03).",
    "The a16z 'State of Markets' report cited in the transcript was not fetched directly -- the 2% statistic was checked against secondary press coverage only (see deepest-est-01); the report itself should be read before quoting the exact percentage in any further use of this material.",
  ],

  businessRules: [
    {
      rule: "Nothing released publicly except lead magnets; everything else is paid.",
      verdict: "n/a",
      evidence: "This source proposes a business model to adopt (sell a custom agent platform to SMBs for $25K+$3K/mo); it is not itself a product being released publicly from this project, so the rule doesn't describe a situation that exists here.",
    },
    {
      rule: "Any AI usage is on the user's own key, never the operator's.",
      verdict: "clears",
      evidence: "source/raw.txt line 51: T3 Chat 'is simple, free, and works with a Claude subscription' -- the course's own recommended stack runs AI usage on the builder's own Claude subscription, not a shared operator key. This is the one rule the course's own stack choice genuinely satisfies.",
    },
    {
      rule: "Sell from the operator's own site, not a storefront that captures the lead.",
      verdict: "clears",
      evidence: "The pitched model (lines 63-70, 488-532) is a direct $25K-upfront sale negotiated person-to-person with the SMB owner, not a listing on a marketplace or storefront that would capture the lead -- the course's own recommended sales motion clears this rule.",
    },
  ],

  findings: [
    // ---------------- DEEP (what it is, what it does when actually run) ----------------
    {
      id: "deep-01", level: "DEEP", type: "credit", category: "identity",
      title: "The named guest and his company are real, not invented",
      evidence: "Web search, Nov 2026: Nick Vasilescu is a real, publicly-documented co-founder of Orgo, an AI-agent cloud-computer company (co-founded with Spencer Kinney). Matches source/raw.txt line 3's claim ('Nick, co-founder of Orgo') exactly.",
      provenance: "sourced-dated",
    },
    {
      id: "deep-02", level: "DEEP", type: "credit", category: "practical-advice",
      title: "The client-acquisition sequence is concrete and actionable, not vague hustle advice",
      evidence: "source/raw.txt lines 721-744: call 50 people you personally know who run or work high up in a business, do the first build free in exchange for a case study and 3 warm intros, and let the niche emerge from who responds rather than picking one in advance. Specific, sequenced, and falsifiable (you either made the 50 calls or you didn't) -- a genuine credit distinct from the headline's unsubstantiated dollar claim (see deep-03).",
      provenance: "sourced",
    },
    {
      id: "deep-03", level: "DEEP", type: "stop", category: "headline-vs-body",
      title: "The title's '$1M+' claim never appears again anywhere in the 834-line transcript",
      evidence: "grep -in 'million|\\$1M|1,000,000' source/raw.txt: the only hit is the title itself (line 1). No revenue figure, timeline, or calculation anywhere in the body ever adds up to, references, or substantiates a $1,000,000 number -- the single biggest number on the cover page is asserted nowhere else in the material.",
      provenance: "sourced",
    },
    {
      id: "deep-04", level: "DEEP", type: "stop", category: "artifact-structure",
      title: "This is an unedited ASR transcript with a cleaned AI-generated summary pasted on top, not a 'Full Course'",
      evidence: "grep -o '[Gg]rok[Bb]ot' source/raw.txt: 7 hits, all at or before line 80 (the 'Key Points' and 'Numbered Section Summaries' block). grep -o '[Gg]rock[Bb]ot' source/raw.txt: 29 hits, all after line 80 -- the exact point where the raw podcast transcript begins ('If you wanted to make money selling AI agents...'). Zero overlap either direction. The product's own name is spelled correctly only in the machine-cleaned summary layer and garbled throughout the raw transcript beneath it -- two visibly different levels of editing in one document, not one coherent 'course.'",
      provenance: "sourced",
    },

    // ---------------- DEEPER (the engineering/stack, measured against outside sources) ----------------
    {
      id: "deeper-01", level: "DEEPER", type: "credit", category: "web-verified",
      title: "Orgo is accurately described, not oversold",
      evidence: "Web search, Nov 2026: Orgo gives AI agents a full persistent cloud desktop (REST API, Python/TypeScript SDKs, MCP support) -- matching source/raw.txt lines 59-61, 474-476's claim that it gives each bot 'its own computer... for privacy and multitasking' rather than just a screen. The transcript's technical description of the product its own guest co-founded checks out.",
      provenance: "sourced-dated",
    },
    {
      id: "deeper-02", level: "DEEPER", type: "credit", category: "web-verified",
      title: "Paper is a real, current design tool with a real MCP server, matching the claimed workflow",
      evidence: "Web search, Nov 2026: paper.design ships a real MCP server (paper.design/docs/mcp) marketed as well-suited to solo builders using coding agents -- consistent with source/raw.txt lines 346-406's 'diverge and then converge' claim (ask for 3-4 design variations through the MCP, then combine the best parts). The named tool and its claimed use pattern both check out.",
      provenance: "sourced-dated",
    },
    {
      id: "deeper-03", level: "DEEPER", type: "stop", category: "naming-precision",
      title: "'Agent Mail' and 'Agent Phone' are close to, but not exact matches for, any findable real product",
      evidence: "source/raw.txt lines 23-24, 419-420 name 'Agent Mail' and 'Agent Phone' as the email/phone providers. Web search finds real, similar products under adjacent names only: AgentPhone (an API platform for dedicated AI-agent phone numbers) and AgenticMail (an open-source agent-email/SMS platform) -- neither spelled or branded exactly as the transcript states. Plausibly an ASR rendering of the real product names rather than a fabrication, but not independently confirmed as the literal products named.",
      provenance: "source-is-silent",
    },
    {
      id: "deeper-04", level: "DEEPER", type: "stop", category: "unlocatable-claim",
      title: "The pitch's single most actionable promise -- 'fork the open-source repo today' -- never gives a repo name or URL",
      evidence: "grep -in 'github|\\.com/|http' source/raw.txt: exactly two hits in 834 lines. Line 331: 'I didn't even connect it to GitHub.' Line 814: 'It's on GitHub. It's you literally go to like uh the you can go to bops.' Neither supplies an owner/repo, a URL, or any string a reader could actually type into a browser or a coding agent -- the one concrete, free, immediately-actionable deliverable this whole episode promises is never given a locatable address anywhere in the source.",
      provenance: "sourced",
    },

    // ---------------- DEEPEREST (arithmetic and internal seams that don't close) ----------------
    {
      id: "deepest-01", level: "DEEPEREST", type: "stop", category: "structural-gap",
      title: "The 'Numbered Section Summaries' list silently skips sections 5, 6, and 7",
      evidence: "grep -n '^[0-9]+\\. ' source/raw.txt: the numbered list runs 1 (line 34), 2 (line 44), 3 (line 53), 4 (line 63), then jumps straight to 8 (line 72) -- no line anywhere in the file begins '5. ', '6. ', or '7. '. Three of the eight sections this summary structure claims to have are simply missing, not merely unlabeled -- a reader skimming only the summary layer has no way to know 3 of 8 promised sections don't exist.",
      provenance: "sourced",
    },
    {
      id: "deepest-02", level: "DEEPEREST", type: "stop", category: "arithmetic-error",
      title: "A stated sum in the transcript is wrong by $10,000",
      evidence: "source/raw.txt lines 502-503: 'how am I going to be able to make... $36,000 plus 25K, $51,000 of value from from this?' 36,000 + 25,000 = 61,000, not 51,000 -- confirmed by direct recomputation. Whether this is the speaker's own arithmetic slip or an ASR digit substitution (51 for 61) cannot be determined from the text alone, but the number printed on the page is wrong either way.",
      provenance: "computed",
    },
    {
      id: "deepest-03", level: "DEEPEREST", type: "stop", category: "unstated-assumption",
      title: "The '$3,000/month is like $12/hour' claim is exact only under a hidden, never-stated assumption",
      evidence: "source/raw.txt lines 548-553. $3,000 / $12 = exactly 250 hours. 250 hours/month implies roughly 8.3 hours of billable work every single day of the month, weekends included -- a specific, non-obvious assumption. A standard full-time month (173.3 hours) gives $17.31/hour instead; full calendar-month coverage (730 hours) gives $4.11/hour. The speaker frames $12/hour as a casual, rounded guess ('I don't know, $12 an hour or something like that') when it is in fact an exact figure that only works for one specific, unstated hours assumption.",
      provenance: "computed",
    },
    {
      id: "deepest-04", level: "DEEPEREST", type: "credit", category: "arithmetic-consistency",
      title: "The '10 to 20x niche pricing power' claim is internally consistent with the actual price sold elsewhere in the same transcript",
      evidence: "source/raw.txt line 591 ('I'm going to say it's 10 to 20x') against GrokBot's own stated baseline of $200/month (line 589) gives a derived range of $2,000-$4,000/month. The actual retainer price pitched throughout the rest of the transcript, $3,000/month (lines 26, 66, 497), falls cleanly inside that derived range -- two separately-stated figures that check out against each other on recomputation, not a dangling claim.",
      provenance: "computed",
    },

    // ---------------- DEEPEREST-EST (what the source is actually for) ----------------
    {
      id: "deepest-est-01", level: "DEEPEREST-EST", type: "credit", category: "web-verified",
      title: "The '2% of US households pay for AI tools' statistic is real and dated",
      evidence: "Web search, Nov 2026: Andreessen Horowitz's own 2026 'State of Markets' report (covered by multiple outlets, Sept-Oct 2026) states roughly 2-2.2% of US households were paying for AI services as of mid-2026. Matches source/raw.txt line 644's '2% of the US pays for AI tools' closely enough to credit as real and current, not invented.",
      provenance: "sourced-dated",
    },
    {
      id: "deepest-est-02", level: "DEEPEREST-EST", type: "stop", category: "misattribution",
      title: "The real statistic above is attributed on the page to a person who doesn't appear to exist",
      evidence: "source/raw.txt line 643: 'did you see that Andre Horowitz post.' No individual named 'Andre Horowitz' turned up in the same web search that confirmed the statistic itself -- the real source is the VC firm Andreessen Horowitz's own institutional report, not a named individual's social-media post. 'Andre Horowitz' reads as an ASR rendering of 'Andreessen Horowitz' clipped into a plausible-sounding but fictional person -- the same transcription-garbling pattern already confirmed in this document for 'GrokBot'/'Grockbot' (deep-04) and 'T3 Chat'/'T3 Code', now misattributing a firm's research to a nonexistent individual rather than just misspelling a product name.",
      provenance: "computed",
    },
    {
      id: "deepest-est-03", level: "DEEPEREST-EST", type: "stop", category: "commercial-reading",
      title: "This is lead generation for the guest's own company, not neutral business education",
      evidence: "The guest recommending the entire pitched stack's core infrastructure (the 'computer' every bot runs on) is Orgo, the company he co-founded (source/raw.txt lines 3-4, 59-61, 350-351, 416-418, 477-479 all name Orgo as the recommended host). The episode is structured as 'here is a $25K-$3K/mo business anyone can start,' but the single component with no substitute offered anywhere in the transcript is the guest's own product -- a real, checkable commercial incentive underneath the educational framing, not an accusation that the advice itself is false.",
      provenance: "sourced",
    },
  ],
};
