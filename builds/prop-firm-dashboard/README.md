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
