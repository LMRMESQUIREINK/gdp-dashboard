# Deep analysis: "Build $10,000 Websites using Claude Code (Ultimate Guide)"

Source: a single YouTube transcript (`ae34ab0a-r_Build_10000_Websites_using_Claude_Code_Ultimate_Guide`),
plus two GitHub repos the video names and links directly — read in full
rather than taken on the video's word, per this project's standing rule
(same move as reading REA's actual source instead of its README table,
or the real `github-repo-manager` repo instead of its blog post):

- `anthropics/skills/skills/frontend-design` (cloned at
  `/home/user/anthropics/skills`, commit `dbd4588`)
- `nextlevelbuilder/ui-ux-pro-max-skill` (cloned at
  `/home/user/nextlevelbuilder/ui-ux-pro-max-skill`, commit `56ea9cf`,
  shallow depth-1 — no tag/release history available from this clone)

## What's genuinely well-reasoned

The video's core structure — an explicit 8-item checklist (point of
view, typography, colour, hierarchy, imagery, motion, mobile, "the
invisible stuff" / felt-quality-performance), grouped into taste,
substance, and felt quality — is a real, usable framework, not vague
hype. It's concrete enough to self-grade against, and the video shows
itself actually doing that mid-build ("Claude comes back with point of
view strong, colour strong, hierarchy strong, typography mixed...").
That's the same "turn a checklist into an actual self-check" move this
project credited the Factory.ai Autonomy Maturity Model paper for, and
it's the strongest, most buildable idea in this transcript.

The architecture-protection anecdote in Chapter 6 — Claude refusing to
drop a React-shaped 21st.dev component into a static single-file HTML
project, because that would change how the whole project works — is a
plausible, well-reasoned description of how Claude Code actually
behaves (it doesn't silently restructure a project's stack to satisfy
one request), not an invented capability. It can't be independently
replayed from this sandbox (no video, no access to the actual Claude
Code desktop session), so it's credited as "plausible and consistent,"
not verified.

The copy-quality framing ("Dry-Aged Ribeye, 16 ounce, 60-day,
hearth-fired" vs. generic AI copy that "over-explains, uses too many
adjectives, tries to sound impressive") is a reasonable, specific
observation about a real failure mode, and lines up with this
project's own Humanizer tool and don't-say-list discipline — different
build, same underlying diagnosis.

## What doesn't check out — checked directly against the two linked repos, not assumed

**Claim: Frontend Design "bans the most overused fonts on the
internet."** This is false as stated. `frontend-design/SKILL.md`
(the entire skill — it's a single file plus a license, no database)
never names or bans a single typeface. What it actually bans is five
*visual patterns*: the warm-cream-plus-terracotta palette (explicitly
naming `#F4F1EA`/`#D97757`, and flagging that the terracotta is
literally Anthropic's own UI accent colour), a near-black-plus-acid-
green/vermilion combo, broadsheet-hairline-rule layouts, the "SaaS-card
kit" (identical rounded cards, one shadow, gradient washes), and
"template chrome" (ALL-CAPS eyebrows, middle-dot-joined meta strings,
em-dash labels, a monospace face for data labels, arrow-suffixed
buttons). Typography guidance in the same file is about type *scale*
and *pairing discipline* ("use one family or two, clearly distinct"),
not a banned-fonts list. The video's separate claim later in Chapter 7
— that Inter specifically "is so overused on AI-generated sites it
instantly screams 'AI made this'" — is the video's own stated opinion,
not something `frontend-design` asserts; the skill doesn't mention
Inter, Geist, or any named font at all. Worth noting in passing: the
skill was clearly consulted by whoever wrote `design-rules.md` in this
project months ago — the overlap (cream/terracotta, ALL-CAPS eyebrows,
arrow-suffixed buttons) is close to word-for-word.

**Claim: UI/UX Pro Max "ships with 57 UI styles, 95 colour palettes and
56 font pairings."** Checked by direct row count against the real
data files, not the video's on-screen caption: `styles.csv` has 88 rows
(79 flagged `searchable` in `catalog-summary.json` — 50 `active`, 29
`supplemental`, 9 `deprecated`), `colors.csv` has 192 rows, and
`typography.csv` has 74 rows. None of the three numbers the video
states match current reality, and the real numbers are all
*higher* than claimed, not lower or mixed. The package's own
`plugin.json`/`marketplace.json`/`SKILL.md` all independently agree
with the counted CSV rows (79/192/74), which is itself a basic
internal-consistency check worth doing before trusting any of a
project's self-reported numbers. The most likely explanation, not
provable from this clone: version drift. `plugin.json` reports version
`2.15.0`, and the repo ships real CI automation for this exact purpose
— `.github/workflows/bump-versions.yml`, `refresh-catalogs.yml`,
`check-asset-sync.yml` — meaning the catalog is actively and
automatically grown, not a fixed snapshot. The clone here is a shallow
`--depth 1` checkout with no tag/release history, so the historical
counts at whatever point the video was recorded can't be reconstructed
from this sandbox — stated as a real limitation rather than guessed
around.

**Claim: install `ui-ux-pro-max` by telling Claude "Install this plugin
using NPM."** This one checks out. The repo's own README documents
`npm install -g ui-ux-pro-max-cli` and `npx ui-ux-pro-max-cli init --ai
claude` as the real, current install path — the video's instruction
matches the actual package's distribution mechanism, not an invented
one.

**Pricing claims** ("$43 for the year" of Hostinger hosting + domain +
email, "~$60 total" with Claude Pro) are time-stamped promotional
prices from the creator's own checkout, explicitly flagged in the video
itself as subject to change ("the exact number you see might be a few
dollars different"). Not independently checkable from this sandbox (no
live network access to Hostinger's pricing page), and the video
doesn't present them as fixed facts either — reported as source-stated,
same treatment as every other unverifiable live-pricing claim in this
project's prior rounds.

One transcription artifact, not a real claim: the transcript repeatedly
renders the tool name as "11ElevenLabs" (e.g. "The one I use is
11ElevenLabs... 11ElevenLabs is a paid service"). This reads as an
auto-captioning merge of a spoken "ElevenLabs" with an adjacent "11" —
not evidence of a different, real product called "11ElevenLabs." Not
repeated as a real name anywhere in this analysis or the build below.

## What's distinctly good about the two linked repos themselves

`frontend-design` is deliberately lean — one file, no database, no
scripts — and is explicit that its job is taste/judgment calibration,
not a lookup table; that's a legitimate, different design choice from
`ui-ux-pro-max`, not a lesser version of it.

`ui-ux-pro-max-skill` is a genuinely large, actively engineered
project, well beyond "a skill": a Next.js style gallery, a published
npm CLI with cross-platform-assistant templates (Claude, Cursor,
Copilot, Windsurf, Gemini, etc.), real CI (catalog refresh, asset-sync
checks, stack-smoke-tests, automated version bumps), and a real test
suite (`scripts/tests/`) covering catalog-quality, data contracts, and
style-taxonomy integrity — not just the design CSVs the video shows on
screen. That's a materially heavier tool than the video's framing of
"the second, community-built skill" suggests.

## What's built from this

Not a WordPress-style situation (last round) where nothing could be
tested — the one piece of this video that's both genuinely novel to
this project *and* fully checkable from static files is the 8-pillar
checklist used as a **self-grading step**, same move as
`/builds/agent-readiness-scorecard/`: take a vendor/creator's checklist
and turn it into a real, locally-checkable grader instead of a thing a
person has to remember to apply by eye, being explicit about which
items a machine can actually check from files on disk and which
genuinely require human judgment (point of view, most of imagery
quality, and whether motion *feels* premium are not checkable from
static analysis, and the grader says so instead of faking a score for
them). Built as `/builds/ten-k-website-grader/` — see that build's
README for what's implemented, what's a heuristic, and what's flagged
not-assessable.
