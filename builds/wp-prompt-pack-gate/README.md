# RUTHLESS GATE — WordPress Prompt Pack

A verdict page auditing `Claude_WordPress_Prompt_Pack2.pdf` ("Build a
WordPress website using Claude AI — Free Prompt Pack", Metics Media, 9
pages), built with the `ruthless-gate` procedure: four escalating levels
of analysis, every verdict carrying named evidence, a test suite that
locks the findings to the page, and a self-check of the source against
its own stated rules.

Open `index.html` in a browser, or see `data.js` for the raw ledger.

## Coverage — what this audit did not check

- No live WordPress install, Astra theme, Elementor (v3 or v4), WPForms,
  NovaMira connector, or Instant Images plugin exists in this sandbox —
  none of the 10 prompts were run against a real site. Every claim about
  what Elementor/Astra actually does is source-stated or web-verified
  against documentation, never reproduced live.
- The source video ("the tutorial," referenced repeatedly in the pack's
  own text) was not supplied and was not watched. This audit covers the
  PDF only.
- Elementor's full current catalog of V4 atomic elements was not
  enumerated page by page from Elementor's own docs — characterized via
  one third-party vendor blog and Elementor's own v4-faq page, not
  cross-checked against each other line by line.
- "Large PNGs cause the Elementor editor to fail to paint images" (pack
  page 4) was not independently reproduced — no live Elementor editor
  exists here. Treated as plausible, standard web-performance advice,
  source-is-silent (the pack names no source and none was independently
  confirmed).
- Metics Media's legal identity, and whether this PDF's author(s) are the
  same individual(s) behind any of the three YouTube creators in this
  project's earlier `/notes/wordpress-claude-elementor-tutorials-analysis.md`,
  is not confirmed — only a shared domain and affiliate-link pattern
  across two artifacts analyzed in this project is observed and stated
  as such.
- Hostinger's and Artlist's actual current pricing, and the real size of
  the "additional 10% off" claimed on page 9, were not checked against
  either vendor's live pricing page.

## Findings (summary — full ledger with evidence in `data.js`)

**DEEP** — what the source is, run through once:
- **Stop**: the cover claims "9 prompts" / "Nine prompts"; the pack's own
  table of contents and body deliver exactly 10 numbered prompts. A real
  off-by-one in the source's own self-description, confirmed by direct
  count, not a transcription artifact.
- **Credit** (×2): the pack's claim about its own recovery-prompt count
  ("prompts 5 and 6... the two most common problems") checks out exactly,
  and every prompt's Claude Design/Claude Code label is internally
  consistent with its actual content.

**DEEPER** — the framework, measured:
- **Credit**: "Elementor version 4 atomic elements" is a real, current,
  correctly-named feature (web-verified) — not an invented term.
- **Stop**: that same V4 atomic system is, per independent third-party
  review, still Beta as of its own cited changelog dates, with the
  reviewer's own advice being "wait and test" for revenue-critical
  sites — a hedge this pack never surfaces anywhere in its 9 pages.
- **Credit** (×3): the pack's copy-voice ban (no em dashes, no
  "unlock"/"elevate"/"seamless"/etc.) is independently, mechanically
  enforceable — this project's own `/builds/humanizer/` already tracks
  every one of the exact terms the pack bans, with zero changes needed;
  running it against the pack's own text confirms the pack's prose is
  clean of its own banned words (the 5 raw hits are all inside the rule's
  own example text, a checked, not assumed, false positive); and the 3
  real em dashes that do exist in the PDF were checked against the
  rule's actual scope and correctly found not to violate it.
- **Stop**: the NovaMira connector — infrastructure every Claude Code
  prompt in the pack silently depends on — is named exactly once, in
  six-point type on the final page, with zero setup instructions
  anywhere in the document.

**DEEPEREST** — arithmetic and internal seams:
- **Stop**: prompt 9 (image generation) requires an optional paid tool
  (Artlist) but sits in the main numbered sequence with no re-routing
  instruction for a reader without it, despite an earlier build rule
  explicitly covering that exact case.
- **Credit**: the pack's own chapter-sequencing claim holds — every
  prompt's stated video chapter is monotonically consistent with its
  numbered order.
- **Stop**: prompt 7 depends on a real, necessary manual WordPress-admin
  step (building the menu by hand) that gets a one-line warning instead
  of a numbered prompt of its own — an inconsistent treatment of
  outside-Claude dependencies compared to the rest of the pack.

**DEEPEREST-EST** — the commercial reading, cross-source:
- **Credit**: this pack resolves a real three-way contradiction this
  project already found across three earlier-analyzed WordPress/Claude
  tutorials (Astra's built-in header/footer builder vs. a separate XPro
  plugin) — it sides cleanly with Astra, no XPro plugin anywhere.
  Neither artifact states this connection; it's only visible reading
  both together.
- **Stop**: the same operator domain (`meticsmedia.com`) and the same
  core Hostinger affiliate product appear in this pack and in the
  separate "10k-websites" Higgsfield Claude Skill analyzed in this
  project's prior round — different campaign-tracking URL suffix per
  artifact, confirming one operator running parallel "build a $X website
  with Claude" funnels, not stated by either artifact on its own.
- **Stop**: the pack's own disclosed economics confirm Hostinger
  affiliate revenue, not the free PDF itself, is the real commercial
  driver — the one truly unavoidable paid purchase (Claude Pro) carries
  no tracking link at all.

**Verdict counts**: 15 findings total — 8 credit, 7 stop — across all
four levels, plus 3 operator-business-rule checks (2 clear, 1 COLLIDES).

## Real bugs found and fixed while building this page

Two issues surfaced by actually running the test suite, not by
inspection — isolated before being reported, per the procedure's own
rule that a harness failure is not a finding about the source:

1. **A real layout bug, not a harness artifact**: the first mobile
   screenshot came back 455px wide instead of 375px. Traced to
   `table.rules` — a plain `<table>` with `width:100%` still grows to
   fit unwrapped long evidence strings (URLs like
   `meticsmedia.com/hostinger-HZU`) rather than respecting its
   container, and `overflow-x:clip` on `html`/`body` hid this from
   `document.documentElement.scrollWidth` while `document.body.scrollWidth`
   (what the real fullPage screenshot actually measures) still showed
   455px. Fixed with `table-layout:fixed` plus `overflow-wrap:anywhere`
   on table cells, and the test's own overflow check was tightened to
   compare both `documentElement` and `body` width going forward, so a
   regression of this exact bug can't hide again.
2. **A harness artifact, correctly not reported as a source finding**:
   an initial regex (`"9 prompts"`, "nine prompts"` as literal-space
   phrases) failed to recompute the cover's own 9-vs-10 claim, because
   `pdftotext -layout` wraps the cover sentence across a line break
   ("...ready to copy. Nine\nprompts, in the order..."). Confirmed by
   inspecting the raw extracted bytes before concluding the regex, not
   the source, was wrong; fixed with `\s+` in place of a literal space.

## Verification

```bash
node test.js
```

104/104 assertions pass on the real run: every finding's evidence
string and provenance state, the credit/stop balance (8 ≥ 7, so this
isn't one-sided), the 9-vs-10 count and the em-dash/banned-word counts
independently recomputed from the raw extracted text (not trusted from
`data.js`'s own claim about itself), WCAG contrast computed for the
palette (`--stop` on `--panel` measures 4.49:1 exactly as the spec
states; body and secondary text both clear their floors), ≥30° hue
separation between go/caution/stop, zero external scripts, zero base64
blobs, a real Chromium render (desktop 1280px + mobile 375px) with
rendered DOM counts checked against the ledger exactly, zero console
errors, and no horizontal overflow at 375px.

## Sources

- The audited PDF: `source/extracted-text.txt` (extracted via
  `pdftotext -layout`; sha256 of the original PDF recorded in `data.js`).
- This project's prior rounds, read against this one for the
  DEEPEREST-EST cross-source findings:
  `/notes/wordpress-claude-elementor-tutorials-analysis.md`,
  `/notes/10k-websites-higgsfield-skill-analysis.md`.
- Elementor V4/atomic elements, web-verified: theplusaddons.com/blog/elementor-atomic-editor-explained,
  theplusaddons.com/blog/elementor-v4-production-ready,
  elementor.com/products/website-builder/v4-faq.
- This project's own `/builds/humanizer/patterns.py`, used directly (no
  modification) to check the pack's copy-voice rule against its own text.
