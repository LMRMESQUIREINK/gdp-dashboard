# Flowchart — Static Export-Only Variant

A separate build from `/builds/flowchart-generator/`, implementing
`Locked_HTML_Flowchart_Generator_Prompt.md` literally rather than
folding it into the interactive editor. That spec is a genuinely
different architecture, not a variant of the other three — no JS
state, no `nodes`/`edges` array, no editing at all. The flowchart is
hand-authored static SVG markup with semantic element IDs
(`node-research-question`, `connector-search-to-decision`,
`connector-feedback-loop`, matching the spec's own example naming),
and the locked HTML shell only offers **Download Editable SVG** /
**Download PNG** — no Add Node, no drag, no orientation toggle.

## What's here

Same research-workflow content as `/builds/flowchart-generator/index.html`
(for direct comparison), reproduced as static markup instead of
rendered from state. Open `index.html` in a browser — no build step.

- `.node-shape`/`.connector`/`.node-label`/`.decision-label`/
  `.branch-label` CSS classes, same visual tokens as every other build
  in this family (`#f4f4f2` background, `#242424` 1.7px strokes,
  Garamond, 1200×900 canvas).
- **Download Editable SVG** clones and serializes the live SVG
  directly — there's no `foreignObject` anywhere in this build (nothing
  is editable in the browser, so there's nothing transient to clean up
  before export), so the exported file is portable by construction.
- **Download PNG** rasterizes the same clone via canvas at 4×
  resolution on a white background.

## Why this is a separate build, not a mode of the other one

Trying to make one HTML shell serve both "fully editable JS-state
diagram" and "static hand-authored export-only diagram" would mean
either faking state management nothing actually uses, or faking a
locked shell that secretly has an editor hiding behind it — both
misrepresent what the user would get. The two tools solve different
problems (iterate on a diagram vs. ship one fixed diagram as a clean
vector file) and the specs themselves describe genuinely different
HTML structures for them.

## Verified

Served locally and screenshotted (desktop + mobile width) — clean on
first pass, no changes needed. Both export buttons tested for real:
the downloaded SVG retains every semantic ID and contains the actual
node text (not a screenshot), and the downloaded PNG is a real,
correctly-sized file.
