# Interactive Flowchart Generator — Deep Analysis

Source: 4 uploaded master-prompt specs, all describing the same reusable
tool ("generate a locked HTML/CSS/JS application shell that renders an
editable flowchart from JS state; only `nodes`/`edges` change per
request"). All four share an identical visual system — `#f4f4f2`
background, `#242424` 1.7px strokes, Garamond/EB Garamond/Georgia serif,
a fixed 1200×900 SVG canvas, 4× PNG export scale — strong evidence they're
iterations of one spec, not independent inventions.

## The four files, ranked by completeness

1. **`final_interactive_flowchart_master_prompt.md`** ("FINAL") — the
   fullest version. Edge model has `id/from/to/type/direction/label`,
   with 4-way direction cycling (forward/reverse/both/none), a
   `Reconnect` mode, cascading delete, keyboard shortcuts, and a
   27-step required functional test plus a 17-point file-validation
   checklist. Toolbar: Add Node, Add Connection, Toggle Orientation,
   Change Direction, Reconnect, Delete, Download SVG, Download PNG.
2. **`interactive_prompt_v2.md`** — same 3-layer architecture (reference
   image → art direction → JS state) and same visual system, but a
   *condensed* rewrite: the edge model drops `direction` entirely
   (`{id, from, to, type, label}`), and the toolbar drops Add
   Connection / Change Direction / Reconnect / Delete — only Add Node,
   Toggle Orientation, Download SVG, Download PNG remain, even though
   the body text still discusses decision-node rendering as if the
   richer feature set applied.
3. **`interactive_prompt_system.md`** (uploaded twice, identical
   content) — the earliest/shortest draft. Edge model is reduced to
   `{from, to, type}` — no `id`, no `label`, no `direction`. No
   connection-creation workflow is described at all despite `edges`
   being user-editable in principle. Toolbar: Add Node, Toggle
   Orientation, Export SVG only.
4. **`Locked_HTML_Flowchart_Generator_Prompt.md`** — not a variant, a
   **different architecture**. It abandons the other three's "CORE
   PRINCIPLE" (state is the source of truth, SVG is a rendered view) in
   favor of a static, hand-authored SVG with semantic IDs
   (`node-research-question`, `connector-search-to-decision`) baked
   directly into the HTML. No `nodes`/`edges` arrays, no Add Node, no
   drag, no inline editing, no orientation toggle — the locked shell
   only has Download SVG / Download PNG. If someone pastes this prompt
   expecting the same interactive behavior as the other three ("the
   same system, just phrased differently"), they'd get a fundamentally
   non-editable export-only page instead.

## Real contradictions/gaps worth flagging (not just restating the specs)

- **The four aren't drop-in-compatible with each other.** Despite
  identical visual tokens, the feature surface area varies from
  "full editor with direction-cycling + reconnect" (FINAL) down to
  "add a box and export" (`interactive_prompt_system.md`), down to
  "no editing at all" (`Locked_HTML...`). Treating these as
  interchangeable "the same master prompt" would silently drop
  functionality depending on which file happened to get pasted.
- **A genuine, unaddressed browser bug lives in all three interactive
  specs' PNG export path.** Each spec correctly flags that the
  *downloaded SVG* should convert editable `foreignObject`/`contenteditable`
  text into real `<text>`/`<tspan>` for portability (Illustrator/Figma/
  Inkscape). None of them apply that same conversion to the **PNG**
  export path, which also serializes the live SVG and rasterizes it via
  `<canvas>`. Rasterizing an SVG that still contains a mounted
  `foreignObject` with HTML content is unreliable across browsers
  (Firefox in particular does not render `foreignObject` content when
  an SVG is drawn to canvas via `drawImage`) — so, as literally
  specified, PNG export would likely ship with blank or missing node
  text in some browsers. This is a real cross-browser rendering gap,
  not a style nit.
- **No drag-vs-click-vs-double-click disambiguation is specified.**
  All three interactive specs register `pointerdown`/`pointermove` for
  dragging and separately want single-click-to-select and
  double-click-to-edit on the same element, but none mention a minimum
  move threshold before a `pointerdown` counts as a drag. Without one,
  every click (including the first click of a double-click) fires a
  zero-pixel "drag," which is a real source of event-ordering bugs
  between select/edit/drag.
- **`connectionMode` and `reconnectMode` can collide.** Nothing in any
  spec says starting one must cancel the other, or what happens if
  Escape is pressed mid-mode. Left unresolved, a user could end up with
  both modes simultaneously tracking click targets.
- **"Route around the outer perimeter" (feedback loops) is not an
  algorithm.** All three interactive specs state the intent but give no
  actual geometry — a real implementation detail still has to be
  written, not assumed to fall out of the prose.

## Build decision

Built the **FINAL** spec's feature set (it's the most complete and
explicitly named as the authoritative version), with three deliberate
fixes to the gaps above — documented in `/builds/flowchart-generator/README.md`:

1. Added a drag-distance threshold so click/double-click/drag never
   race each other.
2. Made `foreignObject` editing strictly transient — it exists only
   while a node's text is being edited and is removed (committed back
   into `node.text`) before any `render()` or export call. This means
   the live SVG is **always** composed of plain `<text>`/`<tspan>`
   elements outside of the instant a user is actively typing, which
   sidesteps the PNG-rasterization bug entirely rather than needing a
   separate foreignObject→text conversion step for export.
3. `connectionMode` and `reconnectMode` are mutually exclusive —
   activating one cancels the other, and Escape cancels both.

Not built: Stage 1 (AI-generated reference image). This sandbox has no
image-generation tool available, so the build goes straight from
interpreted flowchart content to `nodes`/`edges` state — flagged
plainly rather than faked, same discipline as every other "no live
network access" note already in this project's status log.

`Locked_HTML_Flowchart_Generator_Prompt.md` was **not** merged into the
build — it's a different tool (static export-only diagram page) and
forcing it into the same shell as the other three would misrepresent
both. If that variant is ever wanted, it should be its own build.
