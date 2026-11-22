# Deep analysis: "Make Claude Design From Real References" (the Motion Sites Method)

Source: a bare PDF upload, "INSPO_Guide.pdf," no accompanying
instruction — per this project's convention, the upload itself is the
instruction. A 9-page guide (sha256 `bf70d77a...a6a36dbca3`) teaching a
4-step workflow (study references → write a spec → build → screenshot
and fix) for getting Claude Code to build above-average web pages, by
installing Anthropic's real `frontend-design` skill plus Microsoft's
real Playwright MCP, then adding a self-built "reference library" skill
modeled on Motion Sites' own paid product.

## What was measured first

380 lines, 2,635 words. Unlike most sources this project analyzes, this
one runs a real self-correction on itself: a boxed "THE HONEST NUMBERS"
section states that Motion Sites' free skill has "40 example designs...
50+ hero videos, 30 3D cut-out images and 55+ technique recipes, not 700
designs" — implying the guide is correcting an inflated number from
whatever promotional reel it's responding to (not itself included in
this upload). Worth checking whether the *correction* itself holds up,
not just assuming it does because it reads as the honest side of the
pair.

## Verified directly against the real, cloned source repo

Cloned `Motionsites-AI/claude-skill` (not trusted on the guide's word)
and counted every real file rather than estimating:

- **"40 example designs"** — exact match. `examples/` holds exactly 40
  `.md` files, excluding `INDEX.md`.
- **"50+ hero videos"** — the real `media/MEDIA.md` table has 50 rows
  typed `video` plus 2 typed `video (HLS)` (52 total) — a correct,
  slightly conservative "50+."
- **"30 3D cut-out images"** — exact match. Exactly 30 rows are typed
  `image (alpha)` (the transparent cut-outs the guide means by "3D
  cut-out").
- **"55+ technique recipes"** — the real `references/techniques/
  INDEX.md` states its own exact count in its own first line: "58
  tested recipes in 7 files." The guide's "55+" is correct but
  understates the real figure by 3 — the only one of the four numbers
  that isn't exact, and still in the honest (under-, not over-stated)
  direction.
- **Repo age** — the real (shallow-clone) commit is dated 2026-10-26;
  today is 2026-11-22, 27 days later, matching "under a month old"
  exactly.
- **Star count** — the guide's "about 2,300" matches the one
  independent third-party listing found (Claude Marketplaces, ~2K),
  consistent but not independently confirmable against GitHub's own
  count from this sandbox without minting push-level API credentials —
  the same disproportionate-step call this project has made before
  (`curriculum-link-auditor`, AutoGen's archive-banner check).

Three of four counted claims are exact; the fourth is a correct, minor
understatement. This is the most precisely self-verified "honest
numbers" callout this project has checked in any source to date.

## The one real flaw found: the guide's own trust argument slightly overstates its two trusted numbers

The guide justifies skipping Motion Sites' skill (and building the same
4-step machine from "trusted" parts instead) on a star-count threshold:
"we only install code from projects with 5,000+ stars... Anthropic's
official frontend-design skill (197,000+ stars)... Microsoft's official
Playwright browser tool (39K+ stars)." Checked both via web search:

- `anthropics/skills`' real current star count is reported in the
  170k-180k range across several aggregators (dated mid-to-late 2026) —
  below the guide's claimed "197,000+."
- `microsoft/playwright-mcp`'s real current count is reported in the
  32k-37k range, most recently 35,937 (dated Nov 6, 2026) — below the
  guide's claimed "39K+."

Both real figures remain enormously above the guide's own 5,000-star
threshold, so the practical conclusion (these are legitimate,
well-trusted projects, safe to install) is unaffected — but the two
specific numbers used to make that case are each higher than any
current independent aggregate found, the opposite direction from the
careful, mostly-exact "Honest Numbers" box two sections earlier in the
same document. Not flagged as fabrication — aggregator snapshots
disagree with each other by thousands of stars depending on date, and
this sandbox can't query GitHub's own live count without a
disproportionate credential step — but worth stating plainly rather
than repeating the two numbers as fact.

## Credited: the install commands are exactly correct

Cloned `anthropics/skills` directly and read its real
`.claude-plugin/marketplace.json`: the marketplace is genuinely named
`anthropic-agent-skills`, and the plugin bundling `frontend-design` is
genuinely named `example-skills`. The guide's two commands —
`/plugin marketplace add anthropics/skills` and
`/plugin install example-skills@anthropic-agent-skills` — match this
exactly, in the correct `plugin@marketplace` form. A real, positive
contrast with an earlier round in this project
(`/notes/mattpocock-skills-analysis.md`), where a different article got
this exact command form wrong (`claude plugins install` instead of
`claude plugin install ...@marketplace`).

## Checked `.claude/skills/` first

None of the three skills vendored two rounds ago (`impeccable`,
`emil-design-eng`, `design-taste-frontend`) implement this guide's core
mechanism — a personal, curated multi-reference library (several real
screenshots, each annotated with a one-line "steal: X") picked against
a brief's category and mood *before* writing a spec. `impeccable`'s own
`reference/new-work-comp.md` explicitly distinguishes its single
approved-comp mechanism from a mood board rather than implementing one.
A genuinely new gap.

## Built

`.claude/skills/reference-builder/` — the guide's own given skill file
(Payload 1) and INDEX.md format (Payload 2), vendored per its own
instruction to create the file "with exactly this content," adapted
only with two necessary project-specific notes: `design-rules.md`'s
locked brands win over this skill's generic font/colour guidance (same
precedence rule already stated for the other three vendored skills),
and this sandbox's existing direct-Playwright screenshot workflow
(used in every visual build to date) stands in for the guide's separate
`claude mcp add playwright` step, which is for a user's own local
install, not this session.

**`references/INDEX.md` deliberately left as a template, not
populated** — the guide's own first rule is "study references," and
this sandbox has no real screenshots of actual award-winning sites to
add honestly (no live browser access to motionsites.ai/awwwards.com/
land-book.com to collect them, the same standing restriction as every
other no-live-browsing case in this project). Inventing placeholder
"steal: X" entries for images that don't exist would violate the
method's own first and most important rule.

**A real bug found in this build's own first draft, copied verbatim
from the source** — the guide's Payload 1 itself has invalid YAML
frontmatter: its `description:` field is wrapped across three lines
with no block-scalar indicator (`>-` or `|`) and no continuation
indentation, which `skill_md_validator.py` correctly rejected with
`unparseable-frontmatter` on the very first run against the literal
copy. Fixed by collapsing the description onto one line — the only
change needed; the guide's own 4-step body content is otherwise sound
and left untouched. Verified clean afterward: all 16 real skills in
this project (12 written here, 4 vendored) pass with zero errors except
the two already-documented partial vendor copies from the prior round
(`design-taste-frontend`, `emil-design-eng`), zero unexpected overlap,
well under the pack description budget. Updated five existing tests
whose assertions hardcoded "15 skills" (now 16). 37/37 tests pass.

## Deliberately not built

- Microsoft's Playwright MCP server itself (`claude mcp add
  playwright...`) — this is a Claude Code harness configuration step
  for the user's own local install; this sandbox session already has
  direct Playwright access via Bash, used in every visual build this
  project has shipped.
- Motion Sites' own `motionsites-web-builder` skill — the guide's own
  stated reason for not installing it (under its 5,000-star threshold)
  checks out, and duplicating a skill the guide itself declines to
  install would defeat the point of the round.
- Populating `references/INDEX.md` with fabricated entries — stated
  above, a direct violation of the method's own first rule rather than
  a scope cut.
