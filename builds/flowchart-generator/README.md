# Interactive Flowchart Generator

A single self-contained `index.html` — the locked, reusable HTML/CSS/
vanilla-JS application shell described across the four uploaded
"Interactive Flowchart Generator" master prompts, instantiated with one
example diagram (a literature-review research workflow) to prove the
architecture end-to-end. Full comparison of the four source specs is in
`/notes/flowchart-generator-analysis.md`.

## What's here

Open `index.html` in a browser — no build step, no dependencies. The
diagram is pure JS state (`nodes`/`edges`); the SVG is only a rendered
view of it, per the specs' own core principle.

Supported:
- Drag any node; connected edges follow automatically.
- Double-click a node or edge label to edit its text in place.
- **Add Node** / **Add Connection** (click source, then target).
- Select an edge → **Change Direction** cycles forward → reverse →
  both → none; **Reconnect** lets you re-pick its source/target.
- **Delete** (node deletion cascades to its edges).
- **Toggle Orientation** — recalculates the whole layout vertical ⇄
  horizontal (doesn't rotate the SVG).
- **Download Editable SVG** / **Download PNG** (4× resolution).
- `Delete`/`Backspace` deletes the current selection, `Escape` cancels
  any in-progress mode or selection — guarded so neither fires while
  you're actually typing in an edit box.

## Source spec it's built from, and why

Built the **FINAL** master prompt's feature set (`id`/`direction`-
cycling/`Reconnect` edge model) — it's the most complete of the four
and is explicitly named as the authoritative version. The other two
interactive variants (`interactive_prompt_v2.md`,
`interactive_prompt_system.md`) are progressively stripped-down drafts
of the same idea and weren't separately built. `Locked_HTML_Flowchart_
Generator_Prompt.md` is a different tool entirely (static export-only
SVG, no JS state) and was deliberately **not** merged in — see the
analysis note for why.

Stage 1 (AI-generated reference image as art direction) was **not**
run — this sandbox has no image-generation tool available, so the
build goes straight from the example content to `nodes`/`edges` state.
Flagged here rather than silently skipped.

## Three fixes applied vs. the specs as literally written

The analysis note found three real gaps shared across the interactive
specs. All three are fixed in this build:

1. **Drag vs. click vs. double-click race.** None of the specs
   describe a minimum-move threshold before a `pointerdown` counts as
   a drag. Added one (`DRAG_THRESHOLD = 4px` in `index.html`) — below
   it, a `pointerup` is treated as a click (select) rather than a
   zero-pixel drag.
2. **PNG export of `foreignObject`-based editable text is unreliable
   cross-browser** (Firefox in particular won't rasterize
   `foreignObject` content when an SVG is drawn to `<canvas>`). The
   specs only apply a foreignObject→`<text>` conversion to the
   *downloaded SVG*, not to PNG export, which has the identical
   problem. Fixed architecturally rather than patched: the
   `foreignObject` edit box here is strictly transient — it's mounted
   only while a node is actively being edited and is always committed
   back into `node.text` and removed (`commitEditing()`) before any
   `render()` or export call. The live SVG is therefore *always*
   composed of plain `<text>`/`<tspan>` outside the instant you're
   typing, so both SVG and PNG export are portable with no separate
   conversion step needed.
3. **`connectionMode` and `reconnectMode` could collide.** Starting
   either one now cancels the other, and `Escape` cancels both.

## A real bug found (and fixed) during testing, not in the specs

Playwright-driven testing (`index.html` served locally, screenshotted
before/after per the screenshot-before-done rule) caught two layout
bugs that only showed up once the diagram was actually rendered:

- **Feedback-loop label clipped off the canvas edge.** The routing
  corridor for the "retry" feedback edge was computed without
  reserving room for its own label, so the label overflowed past
  `x=1200`. Fixed by reserving a 140px corridor on the trailing edge
  whenever a feedback edge exists, and clamping the corridor position
  defensively regardless.
- **Horizontal orientation produced heavily overlapping nodes.** The
  original `recalculateLayout()` spaced levels using a row-gap
  computed from canvas *height* regardless of orientation, and never
  adjusted node width for the horizontal flow axis — so columns were
  spaced ~170px apart while nodes stayed ~300–340px wide, guaranteeing
  overlap. Rewrote the flow-axis spacing to size each level from the
  actual max node extent in that direction (`perLevelExtent`), with a
  single `flowScale` applied when the ideal spacing doesn't fit the
  canvas budget — matching the specs' own "Layout Safety" instruction
  to scale/shrink rather than overlap or resize the outer canvas.
  Confirmed with a second screenshot pass after the fix (both vertical
  and horizontal, plus a mobile-width check).

## Not built

- Reference-image generation (Stage 1) — no image tool in this
  sandbox, noted above.
- The `Locked_HTML_Flowchart_Generator_Prompt.md` static/export-only
  variant — a different tool, see analysis note.
