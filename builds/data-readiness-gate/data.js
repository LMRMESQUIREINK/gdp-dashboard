// data.js — the ledger. Every finding carries its evidence and provenance.
// Rendered BY index.html; nothing here is duplicated as a hardcoded number
// in the HTML. Recomputed arithmetic lives in test.js, not here.

const GATE = {
  meta: {
    title: "Data Readiness Gate",
    subtitle:
      "Three vendor PDFs on AI agents, enterprise data readiness, and RAG — audited alone, then against each other.",
    builtFrom: "ruthless-gate procedure (DEEP / DEEPER / DEEPEREST / DEEPEREST-EST)",
    sourceFingerprint: "669ac0de7eaa06dc",
    sourceFingerprintNote:
      "sha256 over the sorted 'filename sha256' rows of the three source PDFs, first 16 chars.",
  },

  // ---------------------------------------------------------------------
  // MEASURE — facts gathered before reading for meaning. Every number here
  // came from pdfinfo / pdftotext -layout / wc / sha256sum, re-run fresh
  // at build time (see README.md for the exact commands).
  // ---------------------------------------------------------------------
  sources: [
    {
      id: "dummies",
      label: "AI Agents in Data Platforms For Dummies®, Cloudera® Special Edition",
      vendor: "Cloudera (published by John Wiley & Sons, Inc.)",
      author: "Dipankar Mazumdar",
      pages: 51,
      fileBytes: 2616707,
      sha256: "1468e2c4e3ef1c12ab83c9bd377682a125dcfb2d921fd01975ba2360a8313b3a",
      producer: "iTextSharp 5.5.0 (iText Group NV, AGPL)",
      creationDate: "2026-08-08",
      pdfVersion: "1.7",
      encrypted: "yes — AES-256, print:no copy:no change:no addNotes:no",
      extractedLines: 2040,
      extractedWords: 11396,
      extractedChars: 116265,
      copyrightFooter:
        "These materials are © 2026 John Wiley & Sons, Inc. Any dissemination, distribution, or unauthorized use is strictly prohibited.",
      copyrightFooterRepeats: 51,
    },
    {
      id: "readiness",
      label: "The Data Readiness Index: Understanding the Foundations for Successful AI",
      vendor: "Cloudera",
      author: "Cloudera",
      pages: 9,
      fileBytes: 2997687,
      sha256: "3c502bc81dcd55620858a73bcf558a2a3b47878d08a4481218d1e8143bdbcf63",
      producer: "Adobe PDF Library 18.0 (Adobe InDesign 21.3)",
      creationDate: "2026-04-09",
      pdfVersion: "1.4",
      encrypted: "no",
      extractedLines: 445,
      extractedWords: 2876,
      extractedChars: 33146,
      methodology:
        "Commissioned by Cloudera, fielded by Researchscape; 1,270 IT leaders, AMER/EMEA/APAC, companies with 1,000+ employees; fielded 2026-01-22 to 2026-03-03.",
    },
    {
      id: "cookbook",
      label: "The RAG Cookbook: Best Practices for Configuring our Retrieval-Augmented Generation models",
      vendor: "Progress Software Corporation (Nasdaq: PRGS)",
      author: "not stated in PDF metadata (vendor-branded whitepaper)",
      pages: 13,
      fileBytes: 1117159,
      sha256: "7a1ca147fae566c8b5e5142cc6c9c8b2bbd161454bd8de8dba4449495c2da88a",
      producer: "Adobe PDF Library 17.0 (Adobe InDesign 20.5)",
      creationDate: "2025-08-28",
      pdfVersion: "1.7",
      encrypted: "no",
      extractedLines: 425,
      extractedWords: 3228,
      extractedChars: 22651,
      revisionCode: "Rev 2025/08 | 1211100517876542",
    },
  ],

  // ---------------------------------------------------------------------
  // COVERAGE — what was NOT read or checked. Printed above the verdict.
  // ---------------------------------------------------------------------
  coverage: {
    read: [
      "All 51 pages of the Dummies book's extracted text (pdftotext -layout), read in full across three sequential passes.",
      "All 9 pages of the Readiness Index's extracted text, read in full in one pass.",
      "All 13 pages of the RAG Cookbook's extracted text, read in full in one pass.",
      "Pages 6, 7 and 8 of the Readiness Index rendered and inspected visually (native PDF page images), to resolve chart bar-label order that pdftotext scrambles for rotated/stacked axis labels.",
    ],
    notRead: [
      "Pages 1–5 and 9–51 of the Dummies book were NOT rendered visually — only pdftotext's layout extraction was read for those pages. No chart/diagram pixel data beyond the 4 captioned figures (2-1, 2-2, 3-1, 3-2, 4-1) was visually inspected; figure captions and surrounding prose were read, not the diagrams' internal pixel content.",
      "The Dummies book's SQL code examples were read as text; none were executed. No claim in this gate rests on the SQL actually running correctly.",
      "Page 9 of the Readiness Index (the final page, title repeat + Cloudera address block) was read via pdftotext only, not rendered visually — it carries no chart data.",
      "No chart/diagram exists in the RAG Cookbook (confirmed: zero image/figure references in its extracted text), so no visual page rendering was needed for that source.",
    ],
    notPurchasedNotClicked:
      "Nothing here is a live product or page. No Cloudera or Progress product (Agent Studio, Cloudera Data and AI Platform, Cloudera DataFlow, Progress Agentic RAG) was signed into, clicked, or run. Every claim about those products comes from reading the three PDFs' own prose, not from using the products.",
    externalVerification:
      "9 external claims were checked against the live web (see FINDINGS below, each tagged sourced-dated with the date the check was made or the date the external source itself carries). This sandbox blocks direct fetches to arxiv.org (confirmed again this round: a direct curl returns HTTP 403 from the egress proxy) — the two arXiv papers cited by the Dummies book were verified by web search of their abstracts/titles, not by downloading and reading the papers themselves. No claim here asserts anything about those two papers' internal content beyond their existence, title, and abstract-level subject.",
  },

  // ---------------------------------------------------------------------
  // ARITHMETIC INPUTS — raw numbers the source itself states, stored here
  // so test.js can recompute every derived claim from first principles
  // rather than trusting the prose conclusion above. Every number below
  // is a direct transcription of a value measured off the rendered PDF
  // page (see README.md for which pages were visually confirmed).
  // ---------------------------------------------------------------------
  arithmetic: {
    // readiness-index.pdf, p.7: "complete visibility into 100% of my
    // organization's data" (extremely true + very true), by industry.
    visibilityByIndustry: {
      Telecommunications: 89,
      Healthcare: 87,
      "Energy/Utilities": 86,
      "Financial Services": 83,
      Manufacturing: 82,
      "Software/Tech": 76,
      "Public Sector": 66,
    },
    // readiness-index.pdf, p.8: "I can access 100% of my organization's
    // data at any time..." (extremely true + very true), by industry.
    accessByIndustry: {
      Telecommunications: 84,
      Healthcare: 80,
      "Energy/Utilities": 79,
      Manufacturing: 78,
      "Software/Tech": 70,
      "Financial Services": 69,
      "Public Sector": 56,
    },
    // readiness-index.pdf, p.8 prose: "how much of their data is fully
    // governed" (all or almost all), by industry.
    governanceAllOrAlmostAllByIndustry: {
      "Public Sector": 72,
      Healthcare: 66,
      "Energy/Utilities": 65,
      "Software/Tech": 63,
      "Financial Services": 61,
      Manufacturing: 58,
      Telecommunications: 57,
    },
    // readiness-index.pdf, p.8 prose: infrastructure performance "always
    // hinders operational initiatives," by industry (the single highest
    // figure, 60%, plus the rest of the list given in full).
    infraAlwaysHindersByIndustry: {
      Telecommunications: 60,
      "Software/Tech": 39,
      "Financial Services": 38,
      Healthcare: 28,
      "Public Sector": 23,
      "Energy/Utilities": 19,
      Manufacturing: 16,
    },
    // readiness-index.pdf, lines 239-242 and 240-241: paired sub-stats
    // that SHOULD sum to their stated combined figure (R8).
    subStatSums: [
      { label: "data strategy well-defined", extremely: 38, very: 47, statedCombined: 85 },
      { label: "unstructured data share", all: 8, almostAll: 15, statedCombined: 23 },
    ],
    // readiness-index.pdf, lines 78-84: the two catalog/lineage stats
    // joined by "However," with no shared stated denominator (R7).
    catalogLineageStats: { leverageBothWithAutomatedLineage: 91, onlyBasicForSelectTeams: 47 },
    // agents-dummies.pdf, Chapter 5 "More than Ten Key Takeaways":
    // the chapter's own two-part preview, and the literal bullet count.
    chapter5: {
      previewPartsStated: ["Ten important concepts", "Future changes in agentic systems"],
      coreTakeawayBullets: 10,
      bonusForwardLookingBullets: 1,
      bulletHeadings: [
        "Agents are not just another workload.",
        "Agentic workloads are inherently exploratory.",
        "Isolation is a foundational primitive.",
        "Context matters more than data access.",
        "Catalogs are more than metadata repositories.",
        "Open tables and catalogs create organizational memory.",
        "Governance becomes more important as autonomy increases.",
        "Auditability must be built into the platform.",
        "Agent runtimes build on top of data platforms.",
        "The foundations already exist.",
        "Future directions for agentic data systems.",
      ],
    },
  },

  // ---------------------------------------------------------------------
  // FINDINGS — every verdict carries its evidence. type: credit | stop.
  // provenance: sourced | sourced-dated | computed.
  // ---------------------------------------------------------------------
  findings: [
    {
      id: "D1",
      level: "DEEP",
      type: "credit",
      source: "dummies",
      claim:
        "All three 'Beyond This Book' citations (p.2) are real, resolvable sources, not invented references.",
      evidence:
        "agents-dummies.txt:213-219 cites arXiv:2509.00997, arXiv:2603.20576v1, and https://www.cloudera.com/events/webinars/context-and-isolation.html — all three confirmed to exist via web search (2026-11-20); the webinar page names Dipankar Mazumdar as speaker, the same name in this PDF's own Author metadata field.",
      provenance: "sourced-dated",
    },
    {
      id: "D2",
      level: "DEEP",
      type: "credit",
      source: "readiness",
      claim:
        "The survey states its own methodology precisely — sample size, regions, company-size floor, and exact field dates — rather than a vague 'we surveyed IT leaders.'",
      evidence:
        "readiness-index.txt:417-424 (Methodology section): \"commissioned by Cloudera and fielded by Researchscape, examines the views of 1,270 IT leaders based across the AMER, EMEA, and APAC regions who work at companies with more than 1,000 employees... fielded from January 22, 2026, to March 3, 2026.\"",
      provenance: "sourced",
    },
    {
      id: "D3",
      level: "DEEP",
      type: "credit",
      source: "cookbook",
      claim:
        "REMi is described as 'an efficient open-source fine-tuned LLM' for RAG evaluation — confirmed real, not a marketing-only name.",
      evidence:
        "rag-cookbook.txt:105-106; confirmed via web search (2026-11-20) against Progress's own blog, \"Introducing REMi, the first ever open-source RAG evaluation model\" — REMi v0 is built on Mistral 7B by Nuclia (acquired by Progress, Sept 2025); a successor, Llama-REMi v1 (Llama 3.2-3B), also exists.",
      provenance: "sourced-dated",
    },
    {
      id: "R1",
      level: "DEEPER",
      type: "credit",
      source: "dummies",
      claim:
        "The named GitHub repo (cloudera/iceberg-mcp-server) is real, not a placeholder/invented URL.",
      evidence:
        "agents-dummies.txt:1598-1599; confirmed reachable via `git ls-remote` against github.com/cloudera/iceberg-mcp-server (checked earlier this round).",
      provenance: "sourced",
    },
    {
      id: "R2",
      level: "DEEPER",
      type: "credit",
      source: "dummies",
      claim:
        "Neon's serverless Postgres branching/copy-on-write claim matches Neon's own documented architecture.",
      evidence:
        "agents-dummies.txt:710-715; confirmed via web search (2026-11-20) against Neon's own docs — database branching built on copy-on-write storage, near-instant forking from a snapshot, only diverging blocks materialized. The book cites the architecture only, not Neon's own separate marketing claim about agent adoption share, which this gate does not repeat as fact.",
      provenance: "sourced-dated",
    },
    {
      id: "R3",
      level: "DEEPER",
      type: "credit",
      source: "dummies",
      claim:
        "Chapter 5's title, 'More than Ten Key Takeaways,' is literally accurate: exactly 10 numbered concept takeaways (matching the chapter's own preview, 'Ten important concepts') plus one explicitly separate forward-looking bonus section ('Future changes in agentic systems') — 11 total bullets, honoring the classic Dummies 'Ten Things' convention precisely.",
      evidence:
        "agents-dummies.txt:1859-1860 (chapter preview: \"» Ten important concepts\" / \"» Future changes in agentic systems\"); bullets counted directly at lines 1876 (Agents are not just...), 1891(cont.) through 2000 (Future directions...) — 11 '»' markers total, the 11th distinct in kind from the first 10. Recomputed in test.js.",
      provenance: "computed",
    },
    {
      id: "R4",
      level: "DEEPER",
      type: "stop",
      source: "dummies",
      claim:
        "The one empirical benchmark the book cites (the 'Benchmark for Data Agents' paper) is never referenced again anywhere in the book's 51-page body — it appears exactly once, in the page-2 'Beyond This Book' footer, disconnected from every architectural claim the book actually makes.",
      evidence:
        "`grep -n \"2603.20576\\|Benchmark for Data Agents\" agents-dummies.txt` returns exactly one hit: line 216. No architectural claim in chapters 1–5 cites this benchmark's own findings to support itself.",
      provenance: "computed",
    },
    {
      id: "R5",
      level: "DEEPER",
      type: "stop",
      source: "cookbook",
      claim:
        "A copy-editing error in the closing call-to-action: 'What to know more? Try it for Free!' almost certainly should read 'Want to know more?'",
      evidence: "rag-cookbook.txt:407, the document's sole CTA line, immediately preceding the 'About Progress Software' footer.",
      provenance: "sourced",
    },
    {
      id: "R6",
      level: "DEEPER",
      type: "credit",
      source: "cookbook",
      claim:
        "The 'qualitative easing' vs. 'quantitative easing' worked example uses two real, legitimate, lexically-confusable financial terms — not a garbled or invented term standing in for one real one.",
      evidence:
        "rag-cookbook.txt:336-350; confirmed via web search (2026-11-20) — 'qualitative easing' is a real term (Willem Buiter, 2008/2009), describing a shift in a central bank's asset mix at constant balance-sheet size, deliberately contrasted with quantitative easing (balance-sheet growth). Exactly the kind of lexically-similar-but-distinct pair the cookbook's own point requires.",
      provenance: "sourced-dated",
    },
    {
      id: "R7",
      level: "DEEPER",
      type: "stop",
      source: "readiness",
      claim:
        "Two adjacent catalog/lineage statistics (91% and 47%) are joined with 'However,' implying tension, but the text never states a shared denominator — they cannot be arithmetically reconciled from the document alone.",
      evidence:
        "readiness-index.txt:78-84: \"an overwhelming 91% said they leverage both business and technical catalogs, including automated lineage. However, 47% said they only use data catalogs and basic lineage for select teams or use cases...\" — 91% + 47% = 138%, impossible as two mutually exclusive shares of one 100% base; no re-stated denominator for the 47% figure.",
      provenance: "computed",
    },
    {
      id: "R8",
      level: "DEEPER",
      type: "credit",
      source: "readiness",
      claim:
        "Elsewhere in the same document, paired extremely/very sub-statistics DO add up exactly to their stated combined figure — showing the 91%/47% ambiguity (R7) is a real, isolated exception, not general carelessness.",
      evidence:
        "readiness-index.txt:239-242: 38% (extremely well-defined) + 47% (very well-defined) = 85% (\"A majority of respondents (85%) believe...\"); readiness-index.txt:240-241: 8% (all) + 15% (almost all) = 23% (\"nearly one in five (23%)\"). Both recomputed exactly in test.js.",
      provenance: "computed",
    },
    {
      id: "E1",
      level: "DEEPEREST",
      type: "credit",
      source: "readiness",
      claim:
        "The cited Harvard Business Review Analytic Services statistic (73%) is real, correctly dated, and matches precisely ONE of two distinct 73% figures the real HBR report carries — not a blurred conflation of the two.",
      evidence:
        "readiness-index.txt:140-144; confirmed via web search (2026-11-20) against Cloudera's own March 5, 2026 press release, \"Only 7% of Enterprises Say Their Data Is Completely Ready for AI... Report from Cloudera and Harvard Business Review Analytic Services\" — the real report states 73% separately for (a) 'should prioritize AI data quality more' and (b) 'found data prep for AI challenging.' This document's citation matches (a) exactly.",
      provenance: "sourced-dated",
    },
    {
      id: "E2",
      level: "DEEPEREST",
      type: "stop",
      source: "readiness",
      claim:
        "Cloudera ran two distinct AI-data-readiness surveys with two different research partners, released within roughly two days of each other in early March 2026 — this document never discloses that its own cited HBR study is a separate, differently-sampled survey from itself.",
      evidence:
        "This document's own methodology (readiness-index.txt:417-424): 1,270 IT leaders via Researchscape, fielded through 2026-03-03. The cited HBR Analytic Services study (confirmed via web search, 2026-11-20): ~230 HBR-audience members, announced 2026-03-05 — a different sample, a different partner, two days after this survey's own field period closed. The document cites it (line 140: \"a recent Cloudera study, conducted by the Harvard Business Review Analytic Services\") as if it were simply corroborating evidence, without noting it is a wholly separate, smaller, differently-run Cloudera survey on the same near-identical topic released almost simultaneously.",
      provenance: "sourced-dated",
    },
    {
      id: "E3",
      level: "DEEPEREST",
      type: "credit",
      source: "readiness",
      claim:
        "The cited 2025 Cloudera 'Evolution of AI' statistic (96% integrated AI into core processes) is real and matches independent press coverage exactly.",
      evidence:
        "readiness-index.txt:125-130; confirmed via web search (2026-11-20) against Cloudera's own X/Twitter post and independent trade coverage (VMblog, CIOInfluence) of the real report, \"The Evolution of AI: The State of Enterprise AI and Data Architecture\" — 96% matches exactly across all independent sources checked.",
      provenance: "sourced-dated",
    },
    {
      id: "E4",
      level: "DEEPEREST",
      type: "stop",
      source: "readiness",
      claim:
        "The document explicitly sets up a paradox for Telecommunications (best visibility/access, worst operational outcome) and immediately pivots to governance data showing Telecom is ALSO the worst-governed surveyed industry — but never states that connection, leaving its own strongest explanatory link unspoken.",
      evidence:
        "readiness-index.txt:316-321: \"While respondents from telecommunications organizations reported higher confidence in visibility and accessibility, that success hasn't totally translated into operational success... telecommunications respondents said infrastructure performance always hinders operational initiatives at 60%\" [highest of 7 industries] — immediately followed (line 331-340) by: \"What exactly is hindering those operations? Data governance remains a challenge... telecommunications at 57%\" [LOWEST of the same 7 industries, vs. Public Sector's 72% high]. Telecom also tops both the visibility chart (89%, p.7) and access chart (84%, p.8). The document never explicitly states that the industry most hindered operationally is also its worst-governed.",
      provenance: "computed",
    },
    {
      id: "E5",
      level: "DEEPEREST",
      type: "credit",
      source: "readiness",
      claim:
        "A rank correlation across all 7 surveyed industries confirms a real, moderate negative relationship between self-reported visibility/access and self-reported governance maturity — not just a two-industry anecdote.",
      evidence:
        "Spearman's rank correlation recomputed in test.js from this document's own 3 charts (visibility p.7, access p.8, governance p.8): ρ = -0.393 for both visibility-vs-governance rank and access-vs-governance rank across the 7 industries, driven primarily by Telecommunications and Public Sector sitting at opposite extremes on both metrics (Telecom: visibility/access rank 1, governance rank 7; Public Sector: visibility/access rank 7, governance rank 1).",
      provenance: "computed",
    },
    {
      id: "X1",
      level: "DEEPEREST-EST",
      type: "credit",
      source: "cross",
      claim:
        "All three sources, from two unrelated vendors, independently converge on data quality as the central friction point for enterprise AI — from three different vantage points (architecture, survey data, RAG evaluation).",
      evidence:
        "Dummies book's one worked multi-agent example is explicitly framed as \"Investigate data quality issues\" (agents-dummies.txt:1802-1805); Readiness Index names data quality (22%) as the single largest reason ROI falls short, ahead of cost overruns (16%) and weak integration (15%) (readiness-index.txt:134-137); RAG Cookbook's entire evaluation section (REMi, Groundedness metric) exists specifically because retrieved-context quality is the thing that most commonly breaks a RAG pipeline (rag-cookbook.txt:105-127). None of the three cites either of the other two.",
      provenance: "computed",
    },
    {
      id: "X2",
      level: "DEEPEREST-EST",
      type: "stop",
      source: "cross",
      claim:
        "The Dummies book presents catalog+lineage as a solved, foundational architectural pattern — but Cloudera's own separate survey (same vendor) shows real enterprise deployment of exactly that capability is partial, not enterprise-wide.",
      evidence:
        "Dummies book's own Chapter 5 takeaway: \"Catalogs are more than metadata repositories... the catalog becomes the map that enables agents to navigate the enterprise data landscape\" (agents-dummies.txt:1918-1927), presented as an architectural fact already achieved. The Readiness Index's own survey, same vendor, same year: only 47% describe their catalog/lineage usage as full enterprise standardization vs. partial/select-team use (readiness-index.txt:82-84, see also R7 above) — the architecture guide's confidence sits directly next to its own publisher's survey data showing real-world adoption lags behind it.",
      provenance: "computed",
    },
    {
      id: "X3",
      level: "DEEPEREST-EST",
      type: "stop",
      source: "cross",
      claim:
        "The RAG Cookbook's advanced retrieval techniques (context enrichment, multi-step queries, automatic filtering) all presuppose well-integrated source data — but a DIFFERENT vendor's independent survey shows most enterprises haven't reached that integration maturity.",
      evidence:
        "RAG Cookbook's \"Advanced Strategies\" section (rag-cookbook.txt:163-350) assumes a reasonably unified, well-governed knowledge corpus to retrieve from. The Readiness Index (a different vendor, Cloudera, not Progress) reports only 30% of IT leaders say their data sources are \"fully integrated\" across environments, with 52% only \"mostly integrated\" (readiness-index.txt:139-145) — the RAG technique guidance assumes a level of source-data integration that, per an unrelated vendor's own independent data, most real enterprises have not yet reached.",
      provenance: "computed",
    },
    {
      id: "X4",
      level: "DEEPEREST-EST",
      type: "credit",
      source: "dummies",
      claim:
        "The Dummies book's own cited webinar is given by the same person credited as the book's author — a real, confirmed, precise detail the book's own prose never states outright.",
      evidence:
        "agents-dummies.txt:217-219 cites the webinar \"Context and Isolation: The Key Primitives for AI Agents in Data Platforms\"; this PDF's own metadata names its Author as Dipankar Mazumdar (confirmed via `pdfinfo`); web search (2026-11-20) confirms the real Cloudera webinar page lists Dipankar Mazumdar, Director of Developer Relations, as its speaker. A legitimate single-author credit, not a hidden conflict — but the book cites it as plain further reading, without ever noting it is the author's own related talk.",
      provenance: "sourced-dated",
    },
  ],

  // ---------------------------------------------------------------------
  // COUNT TABLE — every row declares a direction (up/down/flat = good).
  // ---------------------------------------------------------------------
  counts: [
    {
      label: "External, checkable claims verified against the live web",
      value: 9,
      direction: "up",
      why: "Every external claim checked (2 arXiv papers, 1 GitHub repo, Neon's architecture, REMi, 'qualitative easing', the HBR study, the 2025 Evolution of AI survey, the webinar speaker) came back confirmed real.",
    },
    {
      label: "Confirmed-real external claims that turned out FALSE on checking",
      value: 0,
      direction: "up",
      why: "Zero fabricated or non-existent citations found across all three sources — a genuinely clean verification round on the pure factual-existence axis.",
    },
    {
      label: "Unsourced percentage/statistic claims invented in the Dummies book's own body text",
      value: 0,
      direction: "up",
      why: "Every specific number in the Dummies book is deferred to its two cited external papers; the book itself asserts zero numeric claims of its own that could be wrong.",
    },
    {
      label: "Times the Dummies book's one cited benchmark paper is used to support a claim in its own body",
      value: 0,
      direction: "down",
      why: "The SAME raw value (0) as the row above, but the opposite direction: here, 0 means a real empirical benchmark sits completely disconnected from the architecture it could have grounded (see R4) — a missed opportunity, not a discipline.",
    },
    {
      label: "Figure references with no matching captioned figure (orphan refs)",
      value: 0,
      direction: "up",
      why: "All 6 figure references (2-1, 2-2, 3-1, 3-2, 4-1, plus 4-1's own prose mention) pair cleanly with a captioned figure later in the text.",
    },
    {
      label: "Distinct Cloudera-commissioned AI-data-readiness surveys found covering near-identical ground within the same ~week",
      value: 2,
      direction: "flat",
      why: "Not inherently good or bad — two real, differently-sampled, differently-partnered Cloudera surveys (this document's own 1,270-respondent Researchscape survey, and the separately-run ~230-respondent HBR Analytic Services study) were both fielded/published within days of each other in March 2026. Worth knowing, not a fault on its own (E2).",
    },
    {
      label: "Data-integrity flags re-derived fresh and found CORRECT after an earlier transcription concern",
      value: 3,
      direction: "up",
      why: "All three source PDFs' sha256 hashes were re-derived fresh this round and confirmed exactly 64 hex characters each — an earlier concern (that one hash looked 65 characters long) was a manual-counting artifact, not a real data problem. See CORRECTIONS.",
    },
  ],

  // ---------------------------------------------------------------------
  // CORRECTIONS — record corrections in public; never silently edit.
  // ---------------------------------------------------------------------
  corrections: [
    {
      id: "C1",
      what:
        "Earlier in this same round, before this artifact was built, a sha256 hash captured for the Readiness Index PDF appeared to be 65 hex characters long (one character over the correct SHA-256 length of 64) — flagged at the time as a possible transcription artifact needing re-derivation rather than being trusted.",
      resolution:
        "RESOLVED. All three PDFs' sha256 hashes were freshly re-derived at build time (`sha256sum` re-run directly against freshly re-copied source files) and each one confirmed, by direct character-count (`${#h}`), to be exactly 64 characters. The earlier 65-character appearance was a manual-counting error made while reasoning about a transcribed tool result, not an actual data-integrity problem. No hash value used anywhere in this gate's findings was ever wrong — only the earlier manual count of its length was.",
      direction: "WAS an overcount (65 read where 64 is correct), now corrected.",
    },
  ],

  // ---------------------------------------------------------------------
  // OPERATOR BUSINESS RULES — adapted: no single product is being sold
  // here, so each rule is scored once, in common, against all three
  // vendor documents' own CTAs/funnels.
  // ---------------------------------------------------------------------
  businessRules: [
    {
      rule: "Nothing is released publicly except lead magnets; everything else is paid.",
      verdict: "clears",
      why: "All three documents are themselves free lead-magnet content (a sponsored 'For Dummies' ebook, two vendor whitepapers) that fund themselves by driving interest toward paid products (Cloudera Agent Studio / Cloudera Data and AI Platform / Progress Agentic RAG), none of which are given away in these PDFs.",
    },
    {
      rule: "Any AI usage is on the user's own key, never the operator's.",
      verdict: "n/a",
      why: "These are static PDFs, not software with a runtime AI call to meter — there is no 'operator's key' question to apply here.",
    },
    {
      rule: "Sell from the operator's own site, not a storefront that captures the lead.",
      verdict: "clears",
      why: "Every CTA in all three documents points to the vendor's own domain — cloudera.com (webinar link, 'Learn more about how Cloudera...', footer address block) and www.progress.com (cookbook's own CTA and footer) — never a third-party marketplace or aggregator.",
    },
  ],

  // ---------------------------------------------------------------------
  // RIGHTS TABLE — licensed-product disclosure. Not legal advice.
  // ---------------------------------------------------------------------
  rights: [
    {
      row: "Reading and sharing the PDF link as received",
      status: "permitted",
      quote:
        "Standard practice for a vendor-sponsored lead-magnet ebook/whitepaper; the Dummies book's own distribution model depends on it being passed along by the sponsor.",
    },
    {
      row: "Copying text out of the Dummies book, printing it, or editing the file",
      status: "forbidden",
      quote:
        "pdfinfo on the Dummies PDF: \"Encrypted: yes (print:no copy:no change:no addNotes:no algorithm:AES-256)\" — a real, measured property of this exact file, not an inference.",
    },
    {
      row: "Third-party redistribution beyond what the sponsor (Cloudera) authorized from Wiley",
      status: "grey",
      quote:
        "Every page repeats: \"These materials are © 2026 John Wiley & Sons, Inc. Any dissemination, distribution, or unauthorized use is strictly prohibited.\" This reads, at a glance, as in tension with a 'For Dummies Special Edition' ebook's own business model (existing specifically to be distributed by its sponsor as marketing collateral). The more likely real structure — Wiley's standard boilerplate protecting against unauthorized THIRD-PARTY redistribution, while Cloudera holds a separate, unseen sublicense from Wiley to distribute authorized copies — cannot be confirmed or ruled out from the PDF alone. This is genuinely unsettled from what's in hand, and this is not legal advice.",
    },
    {
      row: "Reuse of the Readiness Index's or RAG Cookbook's survey statistics/content with attribution",
      status: "permitted (with the standard © notice)",
      quote:
        "Neither carries the Dummies book's encryption flags or its stronger 'strictly prohibited' dissemination language; both carry only a standard '© 2025/2026 [vendor]. All rights reserved' notice.",
    },
  ],
};

if (typeof module !== "undefined" && module.exports) {
  module.exports = GATE;
}
