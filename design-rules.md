# Design Rules

The design system for anything visual in this project — a web page, app
screen, or component. Any build that touches a UI MUST follow this file.
**Status: starter defaults.** No brand colour has been chosen yet —
replace the placeholder below the first time a real build needs one, and
this file becomes the project's actual design system from then on.

---

## Colour

- Derive the whole palette from **one brand colour** — never the
  default AI blue/indigo. Placeholder until a real one is picked:
  `#2D5C3E` (deep green), with tints/shades generated from it rather
  than picked separately.
- Neutrals: a genuine grey scale (not tinted cream/beige) for
  backgrounds, borders, and body text.
- One accent colour max, used sparingly (a single CTA, a highlight) —
  not scattered across the page.

## Type

- A **display font** for headings, distinct from the **body font** —
  never the same font at different weights pretending to be a pairing.
- Body text stays legible: no ultra-thin weights below 400 for reading
  copy.
- Avoid tracked-out ALL-CAPS eyebrow labels — a common generic-AI tell.

## Spacing

- Use a real spacing scale (e.g. 4/8/12/16/24/32/48/64px), not
  arbitrary pixel values chosen per element.
- Consistent rhythm between sections — don't let spacing drift block to
  block.

## Shadows & depth

- Layered, low-opacity shadows (2–3 stacked shadows at low alpha) for
  elevation — not a single hard drop-shadow.
- Avoid identical rounded cards everywhere; vary corner radius and
  elevation to create real hierarchy.

## Motion

- Limit animation to `transform` and `opacity` only (performance +
  consistency).
- Use spring/ease-out easing, not linear.
- Always respect `prefers-reduced-motion` — provide a reduced/no-motion
  path.

## Generic-AI tells to avoid

- Cream-and-terracotta "AI startup" palettes.
- Identical rounded cards with no visual hierarchy.
- Tracked-out ALL-CAPS eyebrow text above headings.
- Arrow-suffixed buttons ("Get Started →") as a default pattern.
- Default framework blue/indigo as the primary colour.
- Stock-photo hero images with generic gradient overlays.

## Verification

Every visual build follows the screenshot-before-done rule in
`CLAUDE.md`: serve it locally, screenshot it, compare against this file
and the ask, fix, re-screenshot, minimum two passes before calling it
done.
