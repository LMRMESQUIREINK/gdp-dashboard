# 10K Website Grader

A real, dependency-free Python implementation of the 8-pillar checklist
from "Build $10,000 Websites using Claude Code (Ultimate Guide)" — point
of view, typography, colour, hierarchy, imagery, motion, mobile, and
"the invisible stuff" (felt-quality/performance). Same move this project
already made for the Factory.ai Autonomy Maturity Model paper
(`/builds/agent-readiness-scorecard/`): turn a creator's checklist into
an actual, locally-checkable grader instead of a thing someone has to
remember to apply by eye. Full analysis of the source video and the two
design-skill repos it links (`anthropics/skills/skills/frontend-design`
and `nextlevelbuilder/ui-ux-pro-max-skill`), including two concrete,
checked-not-assumed claims that don't hold up:
`/notes/10k-website-claude-code-analysis.md`.

## What it actually checks, and what it honestly can't

```bash
python3 ten_k_grader.py path/to/built-site/
python3 ten_k_grader.py path/to/built-site/ --json
python3 ten_k_grader.py path/to/built-site/ --min-score 0.75   # exit 1 if below
```

| Pillar | Assessable from static files? | What's actually checked |
|---|---|---|
| Point of view | **No** | Always reported not-assessable — this is about intent behind the brief, which no file on disk records. |
| Typography | Yes | 1–4 distinct non-generic `font-family` values + at least 3 distinct `font-size` values (a real type scale, not one size everywhere). Flags (doesn't fail) `Inter` usage by name, since the source video specifically calls it out. |
| Colour | Yes | 3–10 distinct colour literals in CSS — few enough to read as a deliberate palette, not so few there's no real palette and not a rainbow. Flags known default-framework blues (Tailwind/Bootstrap/indigo hexes), reusing `design-rules.md`'s own existing "never default blue" rule. |
| Hierarchy | Partially — heuristic only | Proxy only: ≥4 distinct font sizes with a ≥2× spread between largest and smallest. This is **not** a real layout-hierarchy check (it can't see whether the biggest text is actually the most important content) — stated plainly in the output itself, not just here. |
| Imagery | Partially | Checks presence of real `<img>`/`<video>`/`<source>` references with non-empty `src`, alt-text coverage ≥90% on non-decorative images, and `loading="lazy"` usage. Does **not** and cannot check whether the imagery itself looks custom/premium vs. generic stock — that's flagged explicitly as needing a human to look at the actual pictures. |
| Motion | Partially | Checks for any `transition`/`animation`/`@keyframes`/`transform` AND a `@media (prefers-reduced-motion: reduce)` guard. Does not and cannot check whether the motion *feels* restrained vs. gimmicky — flagged the same way as imagery. |
| Mobile | Partially | Viewport meta tag present + at least one `max-width`/`min-width` media query breakpoint. A separate heuristic flags (doesn't fail) broad selectors with a large hardcoded pixel width, which tends to break small screens. |
| Invisible stuff | Yes | Broken local file references (img/video/css/script `src`/`href` that don't resolve to a real file), duplicate `id` attributes within a page, and raster images over 1.5MB. This is a real, narrow slice of "felt quality" — it says nothing about actual load time, CLS, or runtime JS errors, which would need a real browser. |

Of the 8 pillars, **1 is always not-assessable** (point of view) and
**3 of the remaining 7 are explicit heuristics or partial proxies**
(hierarchy, imagery, motion) rather than full checks — the tool says so
in its own output every time, not just in this README. The overall score
is the pass rate across only the assessable pillars; the denominator is
reported alongside it so it's never silently averaged against a pillar
that was never actually checked.

## Verification

`test_grader.py`, 15/15 passing, including the discrimination test that
matters: a deliberately well-built fixture site
(`fixtures/good-site/`) scores 100%, and a deliberately generic,
AI-default-shaped fixture (`fixtures/generic-site/` — Inter-only, one
flat font size, a default Tailwind blue, a missing-alt image with a
broken file reference, a duplicate id, no viewport meta, no motion)
scores 14%, with the specific failing pillars and flags matching exactly
what was deliberately built wrong into that fixture. A CLI test runs the
real subprocess with `--json` and `--min-score`, plus a clean-error check
on a nonexistent path.

```bash
python3 -m unittest test_grader -v
```

**Also run for real against this project's own already-shipped, already
screenshot-verified pages** (`/builds/recovery-desk/sales-page/` and
`/builds/prop-firm-dashboard/sales-page/`), not just the synthetic
fixtures — both scored 71% on first run. That real run **found a real,
previously-undocumented accessibility gap** in Recovery Desk's sales
page: its `.btn` hover has a `transition` with no
`prefers-reduced-motion` guard anywhere in the file, a real violation of
`design-rules.md`'s own already-stated rule ("motion limited to
transform/opacity with spring easing and reduced-motion support").
Confirmed by reading the actual CSS (one `transition` declaration, zero
`prefers-reduced-motion` in the whole file) before fixing it — not just
trusting the grader's own output. Fixed with a 3-line `@media
(prefers-reduced-motion: reduce)` block; re-run afterward moved that
page from 71% to 86%, motion pillar now passing. Both pages still fail
`imagery` for a real, known, already-documented reason — neither has any
actual `<img>`/`<video>` tag at all (both are CSS-only hero treatments,
consistent with this project's own prior notes that no image-generation
tool exists in this sandbox) — reported honestly rather than special-
cased to pass. `prop-firm-dashboard`'s sales page separately fails
`colour` at 11 distinct colour literals against the grader's 3–10
threshold; deliberately **not** "fixed" by trimming that page's real
RUTHLESS TRADING GOLD palette just to satisfy this tool's own heuristic
— stated here instead as a known, honest limitation: a palette built
from several tints/shades of a few base hues can look disciplined to
the eye while still counting as more than 10 distinct literal colour
values, and this heuristic can't tell the difference between that and
an actual undisciplined rainbow.

## What this deliberately doesn't do

No headless-browser rendering, no Lighthouse/CLS/real-performance
measurement, no visual screenshot comparison — this is a static-file
checker, not a replacement for this project's own screenshot-before-done
rule, which still applies for anything the grader marks not-assessable
or heuristic-only. Pair the two: run this first for the objective,
boring stuff (broken links, missing alt text, no viewport meta, flat
typography), then look at the actual rendered page for everything this
tool is honest that it cannot see.
