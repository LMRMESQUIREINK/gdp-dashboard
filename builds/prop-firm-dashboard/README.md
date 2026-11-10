# ♛ RUTHLESS Prop-Firm Dashboard

A Streamlit web dashboard over the four `--prop-*` tools already wired
into `/builds/trading-jarvis/run_strategy.py` and, for the first three,
`jarvis_orchestrator.py`'s Claude tools. Same math, same classes
(`PropFirmAccount`, `AccountRules`, `SessionState`, `PassSimulator`) —
this is a fourth interface on top of the same underlying code, not a
reimplementation.

## Tabs

| Tab | Mirrors | Underlying call |
|---|---|---|
| Size Check | `--prop-size-check` / `prop_firm_size_check` | `evaluate_size()` |
| Session Report | `--prop-session` / `prop_firm_session_report` | `SessionState` |
| Pass Probability | `--prop-pass-prob` / `prop_firm_pass_probability` | `PassSimulator` |
| Compare Sizes | `--prop-compare` | `PassSimulator`, once per row (same class the Pass Probability tab uses — not `compare_sizing_strategies()` directly, since that function `print()`s rather than returning structured data; looping `PassSimulator` per row here gives a proper Streamlit table + chart instead of parsed console output) |

## Files

| File | Role |
|---|---|
| `streamlit_app.py` | The dashboard — four `st.tabs`, RUTHLESS black/gold theme injected via CSS |
| `prop_firm_sizing.py`, `prop_firm_position_sizing.py`, `prop_pass_simulator.py` | Copied in from `/builds/prop-firm-sizing/` (same files, unmodified) |
| `.streamlit/config.toml` | Dark base theme + primary gold color, belt-and-suspenders alongside the custom CSS |

## Setup

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Design

Follows the RUTHLESS TRADING GOLD convention used throughout this
project's other trading-tool dashboards and CLI banners: black
background (`#0A0A0A`), gold accent (`#C9A84C`/`#F0C040`), Cinzel
Decorative for headings, Cormorant Garamond for body text, IBM Plex
Mono for numbers — one brand colour, not the default framework
blue/indigo, per `design-rules.md`'s "derive the whole palette from one
brand colour" rule. The user explicitly asked for this specific,
already-established brand rather than `design-rules.md`'s own
placeholder green, which is the intended use of that file's "MUST
follow this file" rule when no scheme is named — here one was.

## A real bug found and fixed while building this

`st.markdown("<div class='ruthless-card'>", unsafe_allow_html=True)`
followed later by a separate `st.markdown("</div>", ...)` call, with
`st.success`/`st.warning` calls in between, does **not** work in
Streamlit the way it would in a single HTML document — each `st.*` call
renders its own isolated fragment, so the opening `<div>` rendered as
an empty gold-bordered box with nothing inside it, and the closing
`</div>` had no effect. Caught in the first screenshot pass (see
Verification below) and fixed by dropping the wrapper entirely and
letting `st.success`/`st.warning` render directly — Streamlit's own
components already carry enough visual weight without an extra card
wrapper. Also found and fixed a second, unrelated bug the same way:
several lines of the injected CSS were rendering as literal visible
text above the page header instead of being applied as a stylesheet —
caused by blank lines inside the `<style>` block breaking CommonMark's
raw-HTML-block passthrough (a blank line terminates that parsing mode
early, so everything after it gets treated as markdown text instead of
raw HTML). Fixed by removing every blank line inside the injected
`<style>` block.

## Verification (screenshot-before-done)

Served locally (`streamlit run ... --server.headless true`) and
screenshotted with Playwright/Chromium — not just read as code. Two
full passes plus two targeted edge-case checks, per `CLAUDE.md`'s
screenshot-before-done rule:

1. **First pass** caught both bugs above (CSS leaking as text, the
   empty orphan-div box on the Size Check tab) — both fixed, server
   restarted, re-screenshotted.
2. **Second pass**, after the fixes: all four tabs, both idle (empty
   inputs) and after clicking each tab's action button, confirmed
   clean — no leaked text, no orphan boxes, gold/black theme applied
   throughout (tabs, inputs, buttons, metric cards, status badges).
   Every displayed number cross-checked against this project's own
   previously-verified figures from `/notes/prop-firm-sizing-analysis.md`
   and `/builds/trading-jarvis/README.md`'s CLI verification — exact
   matches: Size Check (21.91 pts / 16.7% / Yes), Session Report
   ($49,500 trailing floor, WARNING badge), Pass Probability (36.7%
   / 6.1% / 57.1%, $49,284.22 / $53,717.11), Compare Sizes (1.7% /
   27.1% / 49.7% / 70.8% pass rates, "← 25%" marker on the correct row).
3. **Edge cases**: Size Check at 6 contracts + ADR 78 correctly fires
   both warning flags (exceeds 25% rule, thin ADR stop room) with the
   exact same numbers (3.577 pts, 100.0%, 4.6%) verified earlier via
   CLI. Session Report at -$1,900 intraday P&L correctly shows a red
   CRITICAL badge and a negative binding loss limit (-$800, meaning the
   daily limit is already exceeded) — the math, not just the color,
   was checked.

Also fixed two `use_container_width` deprecation warnings (Streamlit
1.64 wants `width="stretch"`) surfaced in the server log during
testing — a real, if minor, forward-compatibility issue caught by
actually running the app rather than only reading the code.

Not yet deployed anywhere — this has only been run locally in this
sandbox. See "Deployment" in `CLAUDE.md` for hosting options once
that's wanted (Streamlit Community Cloud is the natural first choice
for a Streamlit app specifically, ahead of the Netlify/Vercel/Supabase
options listed there, which don't run Python servers).

## Build Brain, Stages 3–6: The Pass Line

This tool has a locked brand, a sales page, and launch copy — run via
`/prompts/build-brain-method.md` Stages 3–6 directly on this existing
build, skipping Interview/Idea since the product/audience context was
given inline.

- **DNA Lock** — `/design-rules.md`, "Brand: The Pass Line" section.
  Name: **The Pass Line**. Tagline: **"Feed it your real numbers, or it
  doesn't run."** Confirms the palette/type already in `streamlit_app.py`
  as this product's locked DNA rather than re-deciding it; adds the
  name/tagline/voice that didn't exist before.
- **Sales page** — `sales-page/index.html`. Rebuilt in a second round on
  a trading-course-lead-magnet structure (cold-open hook naming the real
  frustration → honest reframe, no invented failure-rate stat → mechanism
  → one honest teaching beat on expectancy/variance vs. win rate → the
  labeled example run → offer stack → who-for/not-for → a free email
  signup as the front door to the rest of RUTHLESS TRADING GOLD), while
  keeping every hard rule from round one: no invented results, no
  guarantees, tagline unchanged. Don't-say-list grep: zero matches (one
  false-positive on a negated meta-statement, read in context). Google
  Fonts confirmed network-blocked in this sandbox again (same finding as
  `/builds/recovery-desk`'s sales page) — flagged, not claimed as
  rendering. The email signup form is a real-looking UI with no backend
  wired to it (this build has no server) — submitting it shows an
  inline note saying so rather than silently pretending to capture the
  address; the `pip install` path below it is the actual, working way to
  get the tool today.
  - **A real bug found and fixed while re-screenshotting**: the page's
    literal `<table>` element (the Example Run stat table) triggered a
    genuine Chromium full-page-screenshot rendering bug — content from
    the bottom of the page bled into the top of every `fullPage: true`
    capture, reproducibly. Confirmed as a real, page-specific issue (not
    sandbox-wide flakiness) by cross-checking against
    `/builds/recovery-desk`'s sales page, which renders clean under the
    identical capture method. Isolated by bisecting through five other
    hypotheses (sticky nav, `backdrop-filter`, `scroll-behavior: smooth`,
    `<pre>`, `box-shadow`) before finding it; fixed by rebuilding the
    table as a CSS Grid with proper `role="table"`/`role="cell"`
    attributes instead of a literal `<table>`. A second, smaller real bug
    surfaced during the same investigation — the sticky nav's
    `backdrop-filter: blur(6px)` could show a stale, ghosted blur of
    content from a moment earlier during a fast scroll — fixed by
    dropping the blur for a solid nav background. Final verification used
    scroll-segmented, real-position screenshots (not a single stitched
    full-page capture) across the entire page, desktop and mobile, since
    the stitched capture mode itself is what the first bug lived in.
- **Launch copy + plan** — `launch/ad-copy.md`. Short/medium/long ad
  variants (medium is a reply-inside-an-existing-thread format, same
  community-norms reasoning as Recovery Desk's), plus a launch plan:
  channel #1 is prop-firm eval Discords (highest-intent audience, not a
  pre-existing owned asset — this build has none), a dated sequence, and
  a stated-assumption first-customer-equivalent target (25 people
  requesting/running the tool within 30 days, since there's no billing
  or analytics to count real subscribers against). Still $0/free — this
  build has no billing/auth code, so that hasn't changed in the rebuild.

Written to a build-local file rather than `business-brain.md` — this
build is part of the unrelated RUTHLESS portfolio, which `CLAUDE.md`
and `business-brain.md` both already note isn't the business that file
tracks.
