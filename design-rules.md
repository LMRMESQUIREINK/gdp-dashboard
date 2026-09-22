# Design Rules

The design system for anything visual in this project — a web page, app
screen, or component. Any build that touches a UI MUST follow this file.
**Status: locked for Recovery Desk** (see `business-brain.md`). This
project also holds an unrelated RUTHLESS TRADING GOLD trading-tools
portfolio under `/builds/` — those builds keep their own established
black/gold branding (set before this file was ever filled in) rather
than being retrofitted to this palette; this file governs new visual
work for Recovery Desk specifically, going forward.

---

## Brand

- **Name**: Recovery Desk.
- **Tagline**: "One text. Know what to do."
- **Logo direction**: a plain wordmark, "Recovery Desk" in the display
  font, sentence case (not a stylized icon) — the whole positioning is
  "not another app to open," so the brand shouldn't look like an app
  icon. If a mark is ever needed (favicon, app-store listing), a single
  filled circle in the brand green standing for "the one decision,"
  nothing more literal (no wearable/watch iconography — that's every
  competitor's logo already).

## Colour

- Brand colour: **`#3E7C5C`** (deep recovery green) — chosen
  deliberately distinct from Whoop's neon lime and Oura's teal/white,
  so a screenshot doesn't read as "yet another wearable app." Not
  mint, not neon — desaturated and confident, closer to forest than
  spring green.
- Background: `#101210` (near-black, warm-neutral undertone) — fits a
  product that's read half-asleep before opening anything else; also
  distances the brand from Oura's clinical white-and-teal look.
- Surface/card: `#1B1E1B`.
- Text primary: `#F0F0EC`. Text secondary: `#9A9A94`.
- Secondary/status colour (product UI only, e.g. flagging a "back off"
  day or an anomalous reading — never used as a second brand colour):
  muted amber `#D98B3E`. Anomaly/medical-flag colour: `#C24B3F` (a
  clear but not alarmist red), used only for the "see a doctor, not a
  training call" override — see `business-brain.md`'s Constraints.
- One accent colour (the brand green) for CTAs/highlights — the amber
  and red above are functional status colours inside the product
  itself, not brand accents, and never appear on the marketing/sales
  page.

## Type

- Display font: **Space Grotesk** (headings, wordmark, big numbers).
- Body font: **Inter** (everything else — legible at small sizes,
  which matters since a lot of this product's own voice lives in SMS-
  length text, not just the web page).
- Body text stays at 400+ weight for reading copy.
- No tracked-out ALL-CAPS eyebrow labels.

## Spacing

- Real spacing scale: 4/8/12/16/24/32/48/64px.
- Consistent rhythm between sections.

## Shadows & depth

- Layered, low-opacity shadows (2–3 stacked, low alpha) for elevation.
- Vary corner radius/elevation instead of identical rounded cards
  everywhere.

## Motion

- `transform`/`opacity` only.
- Spring/ease-out, not linear.
- Respect `prefers-reduced-motion`.

## Voice (do-say / don't-say)

Recovery Desk's voice: **a friend who happens to know sports science** —
direct, plain, specific. Not clinical, not hype.

- **Do say**: plain verbs the product actually uses — "train hard,"
  "back off," "eat more," "sleep earlier" — plus a one-line reason
  ("your HRV dropped 18% overnight" beats "your recovery metrics
  indicate suboptimal readiness"). Talk about the text, not the app:
  "before you open anything," "one text, one call."
- **Don't say**: "AI-powered," "biohacking," "optimize your
  performance," "unlock your potential," "holistic," "next-level,"
  "cutting-edge," "game-changer," "leverage," "synergy," "empower." Also
  specific to this product: never say "diagnose," "treat," or anything
  implying medical advice — every claim stays in "here's what the data
  suggests for training," never "here's what's wrong with you."
- **Signature phrases**: "One text. Know what to do." / "The dashboard
  was never the product." / "Before you open anything."

## Generic-AI tells to avoid

- Cream-and-terracotta "AI startup" palettes.
- Identical rounded cards with no visual hierarchy.
- Tracked-out ALL-CAPS eyebrow text above headings.
- Arrow-suffixed buttons ("Get Started →") as a default pattern.
- Default framework blue/indigo as the primary colour.
- Stock-photo hero images with generic gradient overlays.
- **Specific to this product**: fake device mockups showing invented
  metrics, stock photos of generic runners, or any dashboard screenshot
  in marketing material — the entire pitch is "no dashboard," so
  showing one (even a pretty one) undercuts the positioning.

## Verification

Every visual build follows the screenshot-before-done rule in
`CLAUDE.md`: serve it locally, screenshot it, compare against this file
and the ask, fix, re-screenshot, minimum two passes before calling it
done.
