# Design Rules

The design system for anything visual in this project — a web page, app
screen, or component. Any build that touches a UI MUST follow this file.
**Status: three locked brands, scoped by build.** Recovery Desk is
locked below (see `business-brain.md`). This project also holds an
unrelated RUTHLESS TRADING GOLD trading-tools portfolio under `/builds/`
— those builds keep their own established black/gold branding (set
before this file was ever filled in). As of 2026-09-22, one specific
RUTHLESS build — `/builds/prop-firm-dashboard` — has that branding
formally locked here too, under its own product name ("The Pass Line,"
see below), through Build Brain Stage 3. As of 2026-10-24, a third,
unrelated business — Creator Empire AI, an 18-app creator/marketing
SaaS suite (`/builds/creator-empire-ai/`) — has its own DNA Lock below.
Each section below is scoped to the brand it names; don't cross-apply
one brand's palette to a build under a different one.

---

## Brand: The Pass Line (RUTHLESS prop-firm dashboard)

Build Brain DNA Lock (Stage 3) for `/builds/prop-firm-dashboard` — a
prop-firm evaluation pass-probability tool. A trader on a funded-account
challenge (Topstep/TPT/Apex) enters their tier, balance, days left, and
their own journal avg/std daily P&L, and gets a Monte Carlo pass
probability, the drawdown-fail vs. time-fail split, and a sizing
comparison. Audience: retail futures traders paying $150+ entry fees to
attempt these challenges, who get zero real pass-rate math from the
firms themselves.

- **Name**: **The Pass Line** — a real term borrowed from craps (the bet
  that you *pass* rather than fail), which is exactly what a prop-firm
  eval is: a pass/fail challenge with real odds, whether or not the firm
  tells you what they are. The existing dashboard chrome keeps its
  "RUTHLESS PROP-FIRM DASHBOARD" header (established brand, not being
  renamed); "The Pass Line" is this specific tool/product's name for
  marketing and the sales page — same relationship as "Recovery Desk"
  the product vs. this file's design system.
- **Tagline**: **"Feed it your real numbers, or it doesn't run."** — the
  honest hook: no default demo numbers standing in for your edge, no
  optimistic assumed win rate. `avg_daily_pnl`/`daily_pnl_std` come from
  the trader's own journal or the tool refuses to produce a probability.
- **Logo direction**: keep the existing ♛ crown mark and Cinzel
  Decorative wordmark already established across every RUTHLESS build in
  this project (Trading Jarvis, Kryptera, the existing dashboard header)
  — a new logo for one tool inside an existing portfolio would fragment
  the brand, not strengthen it.

### Palette (already established — confirmed, not re-decided)

Pulled directly from `/builds/prop-firm-dashboard/streamlit_app.py`'s
existing CSS, which predates this Stage 3 lock — this section formalizes
it as the product's locked DNA rather than inventing a new palette:

- Background: `#0A0A0A` (near-black). Card/surface: `#141414`. Elevated:
  `#1C1C1C`.
- Gold accent: `#C9A84C` (primary), `#F0C040` (bright/highlight),
  `#8B7333` (muted, for borders/dividers).
- Text: `#E8E8E8` primary, `#A0A0A0` secondary.
- Status colours (functional, product UI — not brand accents): profit
  green `#22c55e`, loss red `#ef4444`, warning `#F0C040` (shared with
  gold-bright by design — a warning reads as "attention," same register
  as a highlight, in this specific domain).

### Type (already established — confirmed)

- Display font: **Cinzel Decorative** (headings, wordmark, crown motif).
- Secondary/body-serif: **Cormorant Garamond** (body copy, italic
  subtitles).
- Numbers/data/code: **IBM Plex Mono** (every dollar figure, percentage,
  and metric — matches every other RUTHLESS dashboard's convention of
  monospacing anything that's a real number the trader should trust at a
  glance).
- Caveat carried forward from `/builds/recovery-desk`'s own sales-page
  verification: Google Fonts do not load from this sandbox (confirmed
  network block, not a cert artifact) — any screenshot taken here will
  show the system-font fallback, not Cinzel/Cormorant/IBM Plex Mono
  rendering live. Flagged rather than claimed as visually verified.

### Voice (do-say / don't-say) — The Pass Line specifically

Direct, a little blunt, numbers-first — a trader talking to another
trader, not a finance-app onboarding flow.

- **Do say**: "your real numbers," "feed it your journal, not a guess,"
  "pass probability," "drawdown-fail vs. time-fail," "where adding
  contracts stops helping," "no invented edge." Name the actual math
  plainly: "Monte Carlo," "trailing drawdown floor," "high-water mark."
- **Don't say**: "AI-powered," "unlock your edge," "guaranteed pass,"
  "proven system," "secret formula," "beat the prop firms," "100% win
  rate," "risk-free," "gamified," "level up," "become a funded trader
  overnight." Never imply a guarantee of passing — this is a probability
  tool, not a promise, and the entire honest-hook positioning collapses
  the moment the copy oversells past what a Monte Carlo estimate
  actually says.
- **Signature phrases**: "Feed it your real numbers, or it doesn't run."
  / "Know your odds before you pay the entry fee again." / "Not another
  optimistic backtest — your own numbers, run straight."

### Generic-AI tells to avoid (on top of the shared list below)

- Fake "X traders passed this week" counters — this tool has no user
  base to cite yet; don't invent one.
- A guarantee badge or "success rate" claim about the tool itself
  (as opposed to the probability it calculates for the trader's own
  numbers) — those are different things and conflating them is the
  exact overselling this brand's honesty hook exists to avoid.
- Stock photos of trading floors, candlestick charts as decoration, or
  a generic "guy pointing at up-and-to-the-right chart" hero image.

---

## Brand: Creator Empire AI (18-app creator/marketing SaaS)

Build Brain DNA Lock for `/builds/creator-empire-ai/`. The idea arrived
pre-planned, not through this project's own Interview stage: a pasted
planning conversation proposing an 18-app product library (6 suites of
3 apps each — Video, Music, Content, Sales, Automation, Agency labs)
behind one dashboard, with a Phase 1 six-app flagship workflow (product
image → hook → storyboard → music transition → video prompts → export)
demoed against a "Goli Nutrition" sales-video concept. That source text
is explicit, and this file repeats the same honesty rather than
smoothing over it: no 18 apps exist yet, nothing here claims an
existing library or verified customer base — this is a build blueprint,
Interview/Idea skipped in favor of a ready-made plan, same shortcut this
project already took once for `/builds/prop-firm-dashboard` (Stages
3–6 run, Interview/Idea explicitly skipped, context given inline).

- **Name**: **Creator Empire AI**, per the source plan's own stated
  decision — kept rather than re-named, since it's a clear, accurate
  description of the product (a dashboard "empire" of creator tools),
  not a name this file invented.
- **Tagline**: **"One product image. One finished campaign."** — a
  tighter version of the source plan's own positioning ("turn one
  product idea into a complete sales-video campaign... from one
  workspace"), shortened to fit a hero line without losing the point:
  the promise is the finished campaign, not the 18-button dashboard.
- **Logo direction**: a bold, condensed wordmark, no crown/shield/badge
  iconography (that register belongs to the unrelated RUTHLESS
  portfolio) — if a mark is ever needed, a single stacked-layers glyph
  (three bars suggesting "suite → app → output"), nothing literal like
  a film clapper or music note, which would narrow the brand to one
  lab instead of six.

### Palette

Deliberately distinct from both other locked brands in this file
(RUTHLESS/The Pass Line's gold-on-black, Recovery Desk's green-on-black)
and from the generic violet/indigo gradient every AI-SaaS dashboard
already uses by default — this file's own "Generic-AI tells to avoid"
list bans exactly that default, so a third brand repeating it would be
the mistake this file exists to prevent:

- Brand colour: **`#FF4D3D`** (ember red-orange) — cinematic and warm,
  evoking studio lights and a music "drop" rather than a tech-dashboard
  gradient. Bright variant for highlights/active states: `#FF8A5B`.
  Muted variant for borders/dividers: `#A8392D`.
- Background: **`#110B14`** (near-black with a faint violet undertone —
  distinct from RUTHLESS's pure `#0A0A0A` and Recovery Desk's warm-green
  `#101210`). Surface/card: `#1B1420`. Elevated: `#241A2B`.
- Text: `#F2EDEE` primary, `#A79AA0` secondary.
- One functional accent only (never a second brand colour): a cool cyan
  `#3FE0D0` used strictly for the "music transition / beat drop" UI
  moments (the R&B→Hip-Hop selector, beat-map markers) — the one place
  in the product where a second colour genuinely means something
  (the drop), not decoration.

### Type

- Display font: **Sora** (headings, suite/app names, big numbers) —
  geometric and confident, distinct from both other brands' display
  fonts (Cinzel Decorative, Space Grotesk).
- Body font: **Manrope**.
- Monospace (campaign JSON, IDs, exports): **JetBrains Mono**.
- Same caveat already recorded for every other brand in this file:
  Google Fonts do not load from this sandbox (confirmed network block),
  so any screenshot taken here shows the system-font fallback, not
  Sora/Manrope/JetBrains Mono rendering live — flagged, not claimed.

### Voice (do-say / don't-say)

Direct and outcome-first, matching the source plan's own best instinct
("people don't buy a dashboard because it has 18 buttons — they buy the
time saved, the campaigns produced") while correcting its own stated
risk areas into hard rules rather than leaving them as advice to
remember later:

- **Do say**: "one workspace," "the finished campaign," "hook to
  export," "six apps, one workflow," "upload one product image." Name
  the real six-app flagship path plainly rather than gesturing at "AI
  magic."
- **Don't say**: "revolutionary," "game-changing," "unlimited AI video
  generation" (the source plan's own flagged margin risk — video-
  generation credits are metered and separate from planning/drafting
  usage, and copy must never imply otherwise), "guaranteed sales,"
  "double your money" or any guarantee stronger than a stated refund
  window, "endorsed by" or any brand-endorsement implication for a demo
  built against a real product name (the source plan's own Goli example
  is a reference/demo, never a claimed partnership), "AI-powered"
  (generic filler — name what the AI actually does instead).
- **Signature phrase**: "One product image. One finished campaign."

### Generic-AI tells to avoid (on top of the shared list below)

- The violet/indigo "AI dashboard" gradient this file already bans by
  default — doubly relevant here since this brand's whole category
  (AI SaaS tool suites) defaults to it hardest.
- Fake "18 apps, all live" framing — the UI must always make clear
  which of the six Phase 1 apps are real and working versus which of
  the remaining twelve are planned, never implying a finished 18-app
  library that doesn't exist.
- A rendered "finished video" anywhere in marketing material for a
  product that only plans storyboards/prompts/scripts — the source
  plan itself draws this line ("neither should pretend to render
  finished video without a connected video-generation service").

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
