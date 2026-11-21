// RUTHLESS GATE ledger for "Claude_WordPress_Prompt_Pack2.pdf"
// Every entry's `evidence` string is a command, a file:line, or a named
// outside source. Nothing here is coloured without one.
window.GATE_DATA = {
  source: {
    title: "Build a WordPress website using Claude AI — Free Prompt Pack",
    filename: "Claude_WordPress_Prompt_Pack2.pdf",
    author: "Metics Media",
    pages: 9,
    fileBytes: 1167200,
    fileSha256: "df6c15668d6b0ba5a2974b4c20d711168df7a9aaa74aa051fed719e140b052af",
    extractedText: { lines: 415, words: 2370, chars: 15407, tool: "pdftotext -layout" },
    fingerprint: "df49c3a405547ca5",
    fingerprintMethod: "sha256(sorted 'filename sha256' rows), first 16 chars — single-file source, one row",
    fetchedAt: "2026-10-23",
  },

  coverage: [
    "No live WordPress install, Astra theme, Elementor (v3 or v4), WPForms, NovaMira connector, or Instant Images plugin exists in this sandbox — none of the 10 prompts were executed against a real site. Every claim about what Elementor/Astra actually does when a prompt runs is reported as source-stated or web-verified against documentation, never reproduced live.",
    "The source video the pack was extracted from (\"the tutorial\", referenced repeatedly in the pack's own text) was not supplied and was not watched. This audit covers the PDF only.",
    "Elementor's full, current catalog of V4 atomic elements was not enumerated from Elementor's own official docs page by page — characterized via one third-party vendor blog (TheplusAddons) and Elementor's own v4-faq page, both found via web search, not independently cross-checked against each other line by line.",
    "The claim \"Large PNGs cause the Elementor editor to fail to paint images\" (pack page 4) was not independently reproduced — no live Elementor editor exists here to test it against. Treated as source-is-silent: plausible, standard web-performance advice, but the pack names no source and this audit confirms no independent one.",
    "Metics Media's actual legal identity, and whether the individual(s) behind this PDF are the same individual(s) behind any of the three YouTube creators in this project's earlier /notes/wordpress-claude-elementor-tutorials-analysis.md round, is not confirmed — only a shared domain (meticsmedia.com) and a shared affiliate-link pattern across two separate artifacts analyzed in this project are noted as a real, observed connection.",
    "Hostinger's and Artlist's actual current pricing and the real size of the \"additional 10% off\" discount claimed on page 9 were not checked against either vendor's live pricing page — this sandbox's egress restrictions on checking live commercial pricing pages are the same ones already documented elsewhere in this project.",
  ],

  businessRules: [
    {
      rule: "Nothing released publicly except lead magnets; everything else is paid.",
      verdict: "clears",
      evidence: "PDF page 1 title: \"Free prompt pack\"; page 9 names Hostinger, Artlist, and Claude Pro as paid, plainly labelled as such, not disguised as free.",
    },
    {
      rule: "Any AI usage is on the user's own key, never the operator's.",
      verdict: "clears",
      evidence: "Page 9: \"Claude — Pro plan or above. Required for both Claude Design and the Code tab. There is no free route through this build.\" The reader pays Anthropic directly; Metics Media is not an intermediary for the AI spend.",
    },
    {
      rule: "Sell from the operator's own site, not a storefront that captures the lead.",
      verdict: "COLLIDES",
      evidence: "Page 9: meticsmedia.com/hostinger-HZU and meticsmedia.com/artlist-HZU are tracked redirect links; the actual purchase completes on hostinger.com / artlist.io, not meticsmedia.com. Stated plainly as a collision against this specific rule's literal wording — also simply the structural shape of affiliate marketing, not evidence of bad faith on its own.",
    },
  ],

  findings: [
    // ---------------- DEEP ----------------
    {
      id: "deep-01", level: "DEEP", type: "stop", category: "arithmetic",
      title: "Cover claims \"9 prompts\" / \"Nine prompts\"; the pack delivers 10",
      evidence: "pdftotext -layout, lines 9 and 15 (\"Nine prompts\", \"9 prompts\") vs. the pack's own table of contents and body, lines 48–75, ten numbered items 1 through 10 (Design your website … Add a blog). Direct count: grep -c on the ten table rows returns 10.",
      provenance: "sourced",
      note: "An off-by-one in the source's own self-description, not a transcription artifact — both the cover and the running sub-header repeat \"9\" independently, and the table of contents genuinely lists ten.",
    },
    {
      id: "deep-02", level: "DEEP", type: "credit", category: "structure",
      title: "The pack's own claim \"Prompts 5 and 6 are ready-made versions for the two most common problems\" checks out exactly",
      evidence: "pdftotext -layout line 40 states the claim; lines 60–63 and 272–298 show exactly two recovery prompts exist, titled \"Recovery: it came in as raw code\" and \"Recovery: a stylesheet is overruling Elementor\" — no more, no fewer.",
      provenance: "sourced",
    },
    {
      id: "deep-03", level: "DEEP", type: "credit", category: "structure",
      title: "Every prompt is correctly labelled by tool (Claude Design vs. Claude Code) and the labels are internally consistent with the content of each prompt",
      evidence: "pdftotext -layout: prompts 1–2 labelled \"Claude Design\" (lines 77, 177) produce design/visual output only (no WordPress/Elementor instructions appear in either); prompts 3–10 labelled \"Claude Code\" (lines 191, 199, 273, 286, 301, 311, 350, 359) all reference WordPress/Elementor/the site directly. No mislabel found across all 10.",
      provenance: "sourced",
    },

    // ---------------- DEEPER (the engineering/framework, measured) ----------------
    {
      id: "deeper-01", level: "DEEPER", type: "credit", category: "web-verified",
      title: "\"Elementor version 4 atomic elements\" — a real, current, correctly-named feature, not an invented or hallucinated term",
      evidence: "Web search, Oct 2026: Elementor 4.0 is live; atomic elements are its defining change (a leaner set of building blocks styled via Classes/Variables/Components, replacing heavily pre-styled widgets). Elementor has announced all new sites default to V4 starting April 2026. Sources: theplusaddons.com/blog/elementor-atomic-editor-explained, elementor.com/products/website-builder/v4-faq.",
      provenance: "sourced",
    },
    {
      id: "deeper-02", level: "DEEPER", type: "stop", category: "web-verified",
      title: "The same V4 atomic system the pack mandates exclusively is, by independent review, still Beta — with zero hedge anywhere in the pack",
      evidence: "Web search, Oct 2026: a third-party vendor review (theplusaddons.com/blog/elementor-v4-production-ready) states Elementor's atomic editor moved from Alpha to Beta only at v3.35 (Feb 2026), and its own stated advice for \"a large, high-traffic, or revenue-critical site\" already on V3 is \"wait and test.\" The pack's own worked example is a small local business (five pages: Home/Services/Gallery/About/Contact, pdftotext line 160) being steered onto this same Beta system with no maturity disclosure anywhere in its 9 pages.",
      provenance: "sourced-dated",
      note: "Dated to Feb–Jul 2026 per the same source's own changelog references (Pro changelog lists a 4.1.5 entry dated 2026-07-14) — recent, not stale, but still an opinionated third-party \"wait and test\" call the pack never surfaces.",
    },
    {
      id: "deeper-03", level: "DEEPER", type: "credit", category: "self-check",
      title: "Copy-voice ban (no em dashes, no \"unlock\"/\"elevate\"/\"seamless\"/\"in today's fast-paced world\"/\"it's not just X, it's Y\") is independently, mechanically enforceable — not just a stated preference",
      evidence: "python3 builds/humanizer/humanizer.py /tmp/wp-prompt-pack.txt --json — this project's own existing AI-tell detector (/builds/humanizer/patterns.py) already tracks every one of these five exact terms (buzzword rule lines 105–106 cover unlock/elevate/seamless; filler-opener covers the fast-paced-world opener; false-contrast-triplet covers the not-X-but-Y pattern) with zero changes needed to check this pack's own stated rule.",
      provenance: "sourced",
    },
    {
      id: "deeper-04", level: "DEEPER", type: "credit", category: "self-check",
      title: "The pack's own prose is clean of its own banned words — on inspection, not just on the grep's raw count",
      evidence: "The Humanizer run above (deeper-03) returns exactly 5 findings; all 5 fall at character offsets 6213–6310 of the extracted text, which is pdftotext -layout lines 168–170 — the pack's own rule text, quoting \"unlock\", \"elevate\", \"seamless\", \"in today's fast-paced world\", and \"it's not just X, it's Y\" BY NAME to state the ban. Confirmed by reading the context, not assumed: zero instances of these words/phrases appear anywhere else in the document's 2,370 words. Same false-positive class already documented in this project for Recovery Desk's negated \"diagnose\"/\"treat\" language and the launch-kit's own checklist quoting its banned-word list.",
      provenance: "sourced",
    },
    {
      id: "deeper-05", level: "DEEPER", type: "credit", category: "self-check",
      title: "Three real em dashes exist in the PDF's own marketing copy (page 9) — checked against the stated rule's actual scope and correctly NOT a violation",
      evidence: "grep -n \"—\" /tmp/wp-prompt-pack.txt finds three em dashes at lines 392, 399, 406 (\"Hostinger — hosting and your free domain\", etc.). The no-em-dash rule (pdftotext line 168: \"Copy voice: ... Do not use em dashes anywhere in the copy\") sits inside Prompt 1's \"THE WEBSITE\" section and is explicitly scoped to the copy Claude writes FOR the reader's business website — not to Metics Media's own PDF. Read in context before reporting, per the isolate-before-reporting rule: this is not a self-contradiction.",
      provenance: "sourced",
    },
    {
      id: "deeper-06", level: "DEEPER", type: "stop", category: "structure",
      title: "The NovaMira connector — load-bearing infrastructure every Claude Code prompt silently depends on — is named exactly once, with zero setup instructions anywhere in the pack",
      evidence: "pdftotext -layout line 413: \"Free tools used in the video: the Astra theme, Elementor, WPForms, the NovaMira connector, and the Instant Images plugin.\" That is the only appearance of the word \"NovaMira\" in the entire 415-line extracted text (grep -c NovaMira returns 1). Prompt 3 (line 197, \"Are you connected to my WordPress site?\") presupposes a working connection but no prompt anywhere walks through installing or authenticating it.",
      provenance: "sourced",
      note: "Same \"referenced but never actually supplied\" pattern already documented repeatedly elsewhere in this project (Trading Jarvis's missing core files across multiple rounds, the un-walked Build Brain DNA Lock stage) — flagged as a real documentation gap, not assumed malicious.",
    },

    // ---------------- DEEPEREST (arithmetic / internal seams) ----------------
    {
      id: "deepest-01", level: "DEEPEREST", type: "stop", category: "internal-seam",
      title: "A build rule and an image-generation rule are in tension for any reader without an Artlist connector",
      evidence: "pdftotext lines 120–137: \"I have attached my own photos and my logo. Use them... If no image generation connector is available, use only my attached photos and do not substitute or invent other images.\" Yet prompt 9 (lines 349–357) is titled \"Generate images for a page / Needs Artlist connected\" and is presented as prompt 9 of 10 in the main numbered sequence, not as an optional appendix — a reader following the pack strictly in order, without Artlist (an explicitly optional paid tool per page 9), hits a prompt that cannot do anything useful for them with no re-routing instruction back to their own photos.",
      provenance: "sourced",
    },
    {
      id: "deepest-02", level: "DEEPEREST", type: "credit", category: "internal-seam",
      title: "The pack's own sequencing note (\"numbered in the order they appear in the video\") is consistent with its internal chapter labels",
      evidence: "pdftotext line 17 states prompts are numbered in video order. The pack's own chapter labels on each prompt (lines 77, 177, 191, 199, 273, 286, 301, 311, 350, 359: Chapter 5, 5, 6, 7, 7, 7, 8, 11, 11, 11) are monotonically non-decreasing across the ten prompts in numeric order — no prompt is out of sequence relative to its stated chapter.",
      provenance: "sourced",
    },
    {
      id: "deepest-03", level: "DEEPEREST", type: "stop", category: "internal-seam",
      title: "Prompt 7 depends on a manual step the pack mentions only as a one-line warning, not a numbered prompt of its own",
      evidence: "pdftotext lines 303–304: \"Build the menu by hand at Appearance then Menus before you run this, otherwise WordPress orders your pages alphabetically.\" This is real, necessary, manual WordPress-admin work with no corresponding prompt — unlike every other manual dependency in the pack (e.g. prompt 3's connection check, prompt 2's visual review), it gets a warning sentence instead of a numbered step, which is an inconsistent treatment of \"things the reader must do outside Claude\" across the same document.",
      provenance: "sourced",
    },

    // ---------------- DEEPEREST-EST (commercial reading, cross-source) ----------------
    {
      id: "deepest-est-01", level: "DEEPEREST-EST", type: "credit", category: "cross-source",
      title: "This pack resolves a real three-way contradiction this project already found across three earlier-analyzed WordPress/Claude tutorials",
      evidence: "/notes/wordpress-claude-elementor-tutorials-analysis.md (this project, prior round) flagged a direct, unresolved contradiction among three video creators over header/footer tooling: \"Astra's built-in builder vs. a separate XPro plugin, each creator's own stated reason for their choice directly contradicting the other's.\" This pack's prompt 7 (pdftotext lines 300–309) instructs \"Set up the Astra header and footer to match the design\" — no XPro plugin anywhere in this document (grep -i xpro on the extracted text: zero matches). Neither artifact states this connection; it is only visible by reading both together.",
      provenance: "sourced",
    },
    {
      id: "deepest-est-02", level: "DEEPEREST-EST", type: "stop", category: "cross-source",
      title: "Same operator domain, same core affiliate product, two separate funnels — confirmed by direct comparison across this project's two rounds",
      evidence: "This round: meticsmedia.com/hostinger-HZU, meticsmedia.com/artlist-HZU (pdftotext lines 394, 401). Prior round (this project, /notes/10k-websites-higgsfield-skill-analysis.md): meticsmedia.com/higgsfield-ESVT, meticsmedia.com/hostinger-ESVT, both hard-coded into that round's \"10k-websites\" Claude Skill files. Same domain (meticsmedia.com), same Hostinger affiliate product in both, different campaign-tracking URL suffix per artifact (-HZU here vs. -ESVT there) — one operator running parallel \"build a $X website with Claude\" funnels across at least two distinct tutorials/products, not independently stated by either artifact.",
      provenance: "sourced",
    },
    {
      id: "deepest-est-03", level: "DEEPEREST-EST", type: "stop", category: "commercial",
      title: "The free lead magnet's own disclosed economics confirm the real commercial driver is Hostinger affiliate revenue, not the PDF itself",
      evidence: "Page 9 (pdftotext lines 391–415): three entries total, in this order — Hostinger (hosting, an extra 10% off \"applied automatically\"), Artlist (optional), Claude (named but carries no meticsmedia.com link at all — \"claude.ai\" bare). The one mandatory paid purchase every reader following this pack must make through an operator-tracked link is Hostinger; Claude's own purchase, also mandatory (\"There is no free route through this build\", line 407), is pointed at the vendor directly with no tracking link, meaning Metics Media earns nothing from the one unavoidable AI expense and earns only from the hosting choice — consistent with the stated business-rule check above (own-key AI usage, hosting monetized via affiliate).",
      provenance: "sourced",
    },
  ],
};
