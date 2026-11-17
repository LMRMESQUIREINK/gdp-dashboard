# Scrapling ecosystem — analysis

Two sources arrived in the same round, confirmed to be unrelated after
checking rather than assuming: a pasted Apify "E-commerce Scraping Tool"
marketing/FAQ page, then — mid-turn, with the correction "HUSH MY BAD!!"
implying the first paste wasn't the real intended source — three real
GitHub repos about an unrelated open-source scraping library, Scrapling.

## The Apify page: measured, then set aside

`apify/e-commerce-scraping-tool` is Apify's own hosted, closed-source
"Actor" — pure marketing/FAQ copy (scrape mode AUTO/HTTP/BROWSER,
pay-per-event pricing, a self-serving "Competitors" comparison table, an
MCP endpoint at `mcp.apify.com?tools=apify/e-commerce-scraping-tool`).
No code is shown anywhere in the page, and a direct web search found no
source connecting it to either Scrapling or Crawlee (Crawlee shows up in
several *other*, community-built Apify e-commerce actors, never this
official one) — checked rather than assumed either way, since the page's
own "Scrape Mode: AUTO/HTTP/BROWSER" terminology is superficially similar
to naming elsewhere in this space. The page's legality FAQ ("doesn't
access data behind login," "all publicly visible data") is accurate and
standard for the space, and the "pay-per-event" pricing model and
`apify-client` packages are real, well-known facts, not claims worth
independently re-verifying. Beyond that, there's nothing executable or
specific enough to extract a generalizable, testable mechanism from —
the same call this project made on the Week 19/20 and Week 23 newsletter
survey rounds (a page describing mature, independently-documented
platforms with no code shown has no gap to build against). No build from
this page.

## The real source: three repos about Scrapling

- **`D4Vinci/Scrapling`** — a real, independently popular Python web-
  scraping library (Trendshift-badged, a published PyPI package, a Docker
  image, translated READMEs in nine languages), not affiliated with
  Apify. Ships its own **official, author-maintained** Claude Code skill
  at `agent-skill/Scrapling-Skill/`.
- **`Cedriccmh/claude-code-skill-scrapling`** — a separate, **third-party**
  Claude Code skill for the same library, written primarily in Chinese,
  with its own `references/security.md`.
- **`cyberchitta/scrapling-fetch-mcp`** — a third, **third-party** MCP
  server wrapping Scrapling specifically for low-volume, bot-protected
  documentation fetching, explicitly scoped in its own README: "Not
  designed for high-volume scraping or data harvesting."

### Credited

- **A real, specific, independently-verified prompt-injection defense.**
  The official skill's text says, in capitals: "you MUST use the
  commandline argument `--ai-targeted` to protect from Prompt
  Injection." Checked directly in the source rather than taken on faith
  — and a first pass through `cli.py` alone looked like this claim was
  overstated (the basic HTTP command path only wires `--ai-targeted`
  into `main_content_only`, which just restricts markdown conversion to
  `<body>` content, nothing injection-specific). Reading further found
  the real mechanism: `Convertor.write_content_to_file` also calls
  `Convertor._sanitize_for_ai()` in `scrapling/core/shell.py`, which
  strips elements matched by a real XPath (`_HIDDEN_XPATH`) for
  CSS-hidden (`display:none`/`visibility:hidden`), `aria-hidden="true"`,
  hidden `<slot>`, and `<template>` elements — a genuine, specific,
  checkable defense against the common "hide the injected instruction
  from a human skimming the page, but a scraper feeding raw text to an
  LLM still sees it" attack pattern. The CLI's own `--help` text ("sanitize
  hidden elements for AI consumption") matches the real implementation
  exactly, not oversold. **The honest boundary of that defense, stated
  rather than assumed closed**: `_HIDING_DECLARATIONS` only matches two
  CSS declarations (`display:none`, `visibility:hidden`) plus
  `aria-hidden`/`<template>`/hidden `<slot>` — it would not catch text
  hidden by other common visual tricks (zero font-size, off-screen
  absolute positioning, a colour matching the background, zero
  opacity) that never set those specific properties. Not a flaw in the
  library — a real, named scope boundary on a genuinely well-built
  defense, same discipline this project has applied to every other
  "credit the real mechanism, then name where it stops" finding.
- **A real, concrete AI-contribution disclosure policy with a visible
  enforcement mechanism.** `AI_POLICY.md` requires disclosing any AI
  assistance in a PR/issue, states what "good" AI-assisted disclosure
  looks like (human understanding, concrete evidence, the contributor's
  own analysis), and backs it with a real, checkable enforcement signal:
  undisclosed AI output is labelled `AI-Slop` and closed, with the label
  itself browsable on the real repo's issue tracker. Directly relevant
  to a project like this one that works almost entirely through
  AI-authored contributions — a well-reasoned policy worth reading, not
  just citing.
- **Two independently-written skills for the same library, genuinely
  complementary rather than duplicative.** The official skill is in
  English, a flat reference document; the third-party skill is in
  Chinese, structured as an explicit Fetcher-selection decision tree
  (plain `Fetcher` → `FetcherSession` → `StealthyFetcher` →
  `DynamicFetcher`, by site characteristics) with its own
  `references/security.md` adding authorization/robots.txt/ToS
  checks, a cookie-redaction rule, and the same `--ai-targeted`-by-default
  recommendation the official skill makes — independently arriving at
  the same real defense, not copying it uncredited (no reference to the
  official skill anywhere in the third-party repo).
- **The MCP server's own honest scope disclaimer** ("Not designed for
  high-volume scraping or data harvesting") — stated plainly rather than
  oversold, consistent with this project's own standing credit for
  sources that name their own limits unprompted.

### A real finding, from reading the third-party skill's own files
### directly rather than its README summary

`claude-code-skill-scrapling`'s `references/cookie-vault.local.md` and
`references/site-patterns.local.md`, both referenced in its `SKILL.md`
body as where to write real credentials, are **not present in the
clone** — confirmed, before assuming it was a packaging mistake, against
the repo's own `.gitignore`, which excludes exactly those two filenames
by name. By design: the committed templates are the non-`.local`
siblings (`cookie-vault.md`, `site-patterns.md`), and the `.local.md`
variants exist only on a contributor's own machine, never in the repo.
This is the same class of thing the broken-reference checker below was
extended to recognize, not just a one-off observation.

## Built: extended `/builds/skill-md-validator/` (not a new build)

Checked `/builds/` first: this project already has a real SKILL.md
linter, built from a different source (`coreyhaines31/marketingskills`)
several rounds ago. Running it, unmodified, against all three of these
genuinely new external skills — a kind of material it had never been
tested against (not this project's own skills, not synthetic fixtures)
— found **three more real gaps**, the same way the marketingskills and
mattpocock-skills rounds each found real gaps this way before:

1. A real YAML block scalar (`description: |`, the third-party skill's
   actual syntax) crashed the frontmatter parser outright.
2. A real nested YAML map with a leaf key repeated at two depths (the
   *official* skill's own `metadata.homepage`/`metadata.openclaw.homepage`)
   crashed it too, with a misleading "duplicate key" message for input
   that was never actually a duplicate top-level key.
3. The broken-reference checker's broad "any slash" fallback produced
   two more real false positives for two different reasons: a quoted
   runtime-path fragment (`` `bin/python3` ``, from the MCP server's
   skill) that was never a file reference at all, and the real,
   by-design-gitignored `.local.md` credential-overlay files found
   above, which are references to real files that are legitimately,
   deliberately absent in a fresh checkout.

All three fixed in `skill_md_validator.py`, with regression tests built
from the real triggering text in each case
(`tests/fixtures/block-scalar-description/`,
`tests/fixtures/nested-map-metadata/`,
`tests/fixtures/gitignored-reference/`, plus a direct
`_extract_references()` unit test for the `bin/python3` case). 35/35
tests pass, up from 31; this project's own twelve real skills re-checked
clean afterward, confirming none of the three fixes changes anything
for material the validator already handled correctly. Full writeup in
`/builds/skill-md-validator/README.md`.

## Not built in the first round; built, and a real correction, in the second

The first round left a standalone, independent reimplementation of
`_sanitize_for_ai()` as a named next-move rather than building it
reflexively (the extend-the-existing-validator path above was more
proportionate to what the three repos actually surfaced that round).
Picked up directly on request ("Build the standalone \_sanitize_for_ai
tool!") in a follow-up round.

Before writing anything, `pip install scrapling` was run for real,
landing on the current release (0.5.1) — rather than relying on this
project's own memory of the earlier round's reading. Running the
installed package's own code was then denied by this sandbox's auto-mode
classifier ("Unauthorized Access"), the same restriction already
documented for `morluto/rea`'s cloned code — so the real
`scrapling/core/shell.py` was read directly off disk (Grep + Read)
instead of imported.

**That direct read surfaces a real correction to this note's own earlier
scope statement, recorded here rather than quietly edited away**: the
real, current `_is_hidden_element()` also treats zero-value `opacity`,
`font-size`, `height`, `width`, `max-height`, or `max-width` as hiding
(declaration-aware, so `opacity:0.95`/`line-height:0.9` stay correctly
unflagged, exactly as the real source's own docstring states); the real
`_sanitize_for_ai()` also strips zero-width Unicode characters and
XML-illegal control characters from every surviving text node and drops
HTML comments outright; `_strip_noise_tags()` removes `svg` alongside
`script`/`style`/`noscript`; and — the sharpest correction — sanitization
in Scrapling's own extraction pipeline only ever runs at all when
`main_content_only`/`--ai-targeted` is set; without it, nothing is
sanitized. None of this was known when the earlier credit/boundary
finding was written. The remaining real boundary is narrower than
previously stated, but still real: off-screen hiding via
`position`+a large negative offset, and anything needing full
CSS-cascade resolution (a stylesheet rule, or `color` matching
`background-color`) — the last of which is a blind spot Scrapling's own
real code shares, confirmed directly, not unique to this reimplementation.

**Built**: `/builds/html-ai-sanitizer/` — a fresh, dependency-free
(`html.parser.HTMLParser`, no `lxml`) Python reimplementation of the real,
now-corrected scope, in a faithful mode (including staying
case-sensitive on `aria-hidden`, matching the real source exactly) plus
one clearly-separate, opt-in extended mode (negative `text-indent`).
37/37 tests pass on the real run, including a true discrimination pair
locking in the real remaining boundary (off-screen positioning and
color-matching-background both proven *not* caught in either mode;
negative text-indent proven caught only in extended mode) rather than
leaving the boundary as unverified prose. Full writeup in
`/builds/html-ai-sanitizer/README.md`. No bug found in this build's own
first draft, stated plainly.

Also not built, in either round: any actual scraping, live or
otherwise — this sandbox has the same standing no-live-network-access
restriction as every other build here, and neither Scrapling's own
fetchers nor the Apify page's hosted actor were exercised against a real
target site.
