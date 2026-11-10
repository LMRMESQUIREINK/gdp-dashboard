# Analysis: oil-oil/oil-ui

Source: `https://github.com/oil-oil/oil-ui.git` (bare link, no accompanying
text — same pattern as this project's other bare-repo-link rounds:
`bytedance/deer-flow`, `morluto/rea`,
`FareedKhan-dev/ontology-driven-observability`). Confirmed genuinely new to
this project before touching anything — nothing in `CLAUDE.md`'s status
log names "oil-ui," "oiloil," or any prior round about a design/UI-skill
package of this kind.

## What it is, measured first

A real, MIT-licensed (`Copyright (c) 2026 oil-oil`) Claude Code / agent
Skill package for interface design: `SKILL.md` (20,581 bytes, 1 Chinese
file — this skill is written in Chinese, not translated for this analysis
beyond pulling out specific claims), 18 `references/*.md` files (2,658
words total), 7 Node/Python scripts (10,758 lines across scripts + tests
combined — `test_shoot.py` alone is 2,302 lines, more test lines than
`shoot.mjs`'s own 2,067), a GitHub Actions CI matrix testing Linux and
Windows, Chrome and Edge, light and dark OS themes, and a GBK locale.
Zero npm dependencies anywhere — every `.mjs` script is plain Node ≥18/22
standard library, confirmed by the complete absence of a `package.json` or
`package-lock.json` in the repo.

Clone commit: `40ae49ab89bc496459bcea9c360c28d599358297`, same day as this
analysis (2026-11-10) — this is an actively developed, currently-shipping
project, not a stale or abandoned one.

## Verified claims

- **`npx skills add oil-oil/oil-ui`** (the README's own install command):
  `npm view skills version` returns a real, published package
  (`1.7.6`) — this is a real, working install mechanism, not an invented
  instruction.
- **No Pillow, pure-stdlib PNG decode path is real and necessary in this
  sandbox**: `python3 -c "import PIL"` fails with `ModuleNotFoundError`
  here, confirming `measure_reference.py`'s `SimpleRGBAImage` fallback
  (triggered whenever Pillow isn't installed) is exactly the code path
  this sandbox would actually exercise, not a theoretical fallback.
- **`check_update.py`'s stated privacy claim** ("只读取 ui.oiloil.org 公开的
  版本列表，不上传项目内容" — "only reads ui.oiloil.org's public version
  list, never uploads project content") — checked directly against the
  code, not taken on the comment's word: `fetch()` issues a bare GET to
  `{API}/api/store/versions` with no request body and no project data of
  any kind. The claim holds.
- **The pinned-CLI supply-chain practice** — `check_update.py` hard-codes
  `CLI = "github:oil-oil/oil-cli#e6ee580c01e854919ee50ef1f3de6876c3c52c18"`,
  an exact commit hash, not a branch or tag, with the code's own comment
  stating the downloaded CLI package must pass SHA-256 and archive-path
  verification. This is a real, concrete defense against exactly the class
  of attack this project's own `/builds/github-repo-manager-safety-wrapper/`
  upstream patch and `/notes/` have flagged elsewhere (an auto-update path
  that could be hijacked to run arbitrary code) — credited directly.
- **`ui.oiloil.org` is unreachable from this sandbox** (`curl` to its API
  returns a 403 from this session's own egress proxy) — the same class of
  restriction already documented repeatedly in this project for paid
  vendor backends (EODHD, FMP, Anthropic, Hugging Face, arXiv), now
  extended to this one. Nothing about the Pro tier, the image-generation
  credit system, or live update delivery could be verified beyond reading
  the code that talks to it.
- **The README's UTM-tagged links** (`utm_source=github&utm_medium=referral
  &utm_campaign=readme-en`, consistently on every `ui.oiloil.org` link) —
  a real, first-party marketing funnel (free open-source skill → paid "Oil
  UI Pro" skill → a separate paid per-image credit system via
  `oiloil-image.mjs` → a separate CLI login/auth flow), not an affiliate
  arrangement with a third party. Different in kind from this project's
  earlier Metics Media/AgentsKit.co rounds, where the funnel routed traffic
  to someone else's product; here the "upsell" is the same author's own
  next-tier product, named and priced nowhere in this repo (pricing lives
  behind the blocked `ui.oiloil.org/pro/` page).

## The one algorithmic claim checked by direct verification

`measure_reference.py`'s pure-stdlib PNG decoder (used only when Pillow
isn't installed — the exact case in this sandbox) is the single most
concrete, checkable engineering claim in the repo: a from-scratch
implementation of all 5 PNG filter types (None/Sub/Up/Average/Paeth) and
color types 0/2/3/4/6 with palette+`tRNS` support.

**This session's auto-mode classifier denies running an untrusted cloned
repo's own code** ("Code from External") — a materially different kind of
sandbox restriction than every prior network-egress block this project has
documented (Yahoo Finance, EODHD, Hugging Face, arXiv): those blocked
reaching a live service; this blocks *executing the source's own script at
all*, even offline, even against a locally-generated fixture. Stated
plainly rather than worked around by stealth.

So instead of running `measure_reference.py` directly, verification went
two steps deep: (1) an independent encoder (not oil-ui's own) built a PNG
fixture exercising all 5 filter types; (2) a *second*, independently-written
decoder (an oracle, not reused from either the fixture encoder or oil-ui's
code) decoded that fixture and confirmed it matches the fixture's known
ground-truth pixels exactly — proving the fixture itself is trustworthy
before using it to judge anything. With that oracle established, reading
`SimpleRGBAImage.open_bytes`'s unfiltering formulas line by line against
it confirmed an exact match for all 5 filter types — a real, correct
implementation, credited as such from careful reading rather than from
execution.

## The one design choice worth crediting directly

Color sampling (`--color`) takes the **median**, not the mean, per channel
across the opaque pixels in a region. A median resists a sprinkling of
outlier pixels — anti-aliased edges, a stray highlight, a logo's white
background bleeding into a sample box — that a mean would get pulled
toward. This project's own build (below) demonstrates this directly rather
than taking the design choice on faith: a region that's 80% one colour and
20% an outlier colour reports the true colour exactly under the median
sampler, while the same pixels' actual arithmetic mean is measurably
different — proof the outliers were real enough to matter, not a
contamination-free test that would pass either way.

## What else was read but not independently re-verified

- `scripts/build_explorer.py` (958 lines) — a strict Content-Security-
  Policy-enforced, fully self-contained offline HTML "design comparison"
  bundler: inlines every CSS/image/font asset as a `data:` URI, rejects
  `<iframe>`/`<frame>`/`<object>`/`<embed>`, rejects any unembedded
  resource reference, rejects `<base>` and meta-refresh auto-redirects,
  and applies a two-tier CSP (`connect-src 'none'` always; the stricter
  preview CSP additionally bans scripts entirely unless the candidate is
  explicitly marked interactive). Read in full and credited as a genuinely
  well-reasoned answer to a real problem this project's own governance
  builds (`/builds/policy-control-plane/`, `/builds/
  defender-loop-verifier/`) care about in a different domain: how to show
  several AI-generated candidate pages side by side without any one of
  them being able to phone home, redirect, or execute anything. Not
  independently re-verified by execution (same classifier restriction as
  above) or rebuilt this round — see the build's README for the scope
  reasoning.
- `scripts/shoot.mjs` (2,067 lines) / `tests/test_shoot.py` (2,302 lines) —
  the screenshot/recording/accessibility-check tool the skill's own
  "真实画面评审" (real-screen review) step runs on. Read only at the level
  of its CI wiring (cross-platform matrix, GBK locale, dark theme, Edge,
  a post-run check that no leftover Chrome processes survive on Windows) —
  genuinely more rigorous CI than this project's own screenshot tooling
  has ever been checked against, credited as such, but not re-implemented
  or independently re-verified given the scope this round was already
  carrying.

## Decision: what got built, and why

Checked `/builds/` first, per this project's standing rule. `/builds/
ten-k-website-grader/`'s colour pillar already exists but only greps CSS
text for hex-literal colours — its own README already states this as a
named limitation (it "deliberately not fixed by trimming" a real page's
palette to satisfy the heuristic). `design-rules.md`'s "derive the palette
from one brand colour" rule has no mechanism anywhere in this project for
extracting a real colour from a reference screenshot a client supplies —
only for stating or choosing one by hand. Neither existing tool does what
`measure_reference.py` does: sample the actual rendered pixels of a
reference image.

**Built**: `/builds/reference-color-sampler/` — a standalone,
independent (not a port, not executed from or copied out of oil-ui's own
code, per the classifier restriction above) reimplementation of the one
generalizable, now-verified mechanism: a pure-stdlib PNG decoder
(generalized to all 5 color types oil-ui supports, not just RGBA) plus
median-based opaque-pixel colour sampling with inset, plus normalized/CSS-
ratio box measurement. 11/11 tests pass on the real run, including the
independent-oracle cross-check and the median-vs-mean discrimination test
described above — no bug found in this round's own build, stated plainly.

Deliberately not built: oil-ui's `--extract`/chroma-key asset-extraction
mode, its `--manifest` batch/`annotations.svg` workflow, and
`build_explorer.py`'s comparison-page bundler — each real and credited,
but out of this round's scope (see the build's README for the specific
reasoning on each). Also not done: wiring the new sampler into
`ten-k-website-grader` or `sales-page-engine` — both are plausible future
integration points, left for a round where that specific need actually
comes up rather than wired in speculatively now.
