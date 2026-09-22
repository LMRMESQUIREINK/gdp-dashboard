# Recovery Desk

One decision text every morning from your Oura or Whoop overnight data —
train hard, back off, eat more, or sleep earlier, plus a one-line why.
No dashboard, no chat window. Built via the Build Brain method
(`/prompts/build-brain-method.md`) end-to-end from an uploaded
IdeaBrowser opportunity report — see `/business-brain.md` for the full
audience/offer/pricing research and `/design-rules.md` for the locked
brand.

## Files

| File | Role |
|---|---|
| `decision_engine.py` | The actual decision logic — rules-based, not LLM-generated (see below for why) |
| `data_pipeline.py` | Normalizes Oura/Whoop data into one shared shape; `synthetic_reading()` is what every test/demo runs against |
| `sms_dispatch.py` | Formats and sends the morning text via Twilio; `print_decision_text()` is the no-Twilio demo path |
| `run_daily_check.py` | CLI entry point — `--demo SCENARIO` or `--provider oura/whoop --to NUMBER` |
| `test_decision_engine.py` | Asserts each synthetic scenario lands on its *specific* intended branch, not just "returns something" |
| `sales-page/index.html` | Stage 5 (Sales Page Engine) — real-money, real-copy landing page, screenshot-verified |

## Why rules-based, not an LLM

The source opportunity report's own competitive analysis notes that
Whoop Coach and ChatGPT Health run on the same underlying model
family — "smarter text generation" isn't the differentiator being sold
here. A fixed, explainable rule set produces the same call for the same
inputs every time, costs nothing per message, and has no failure mode
where a generative step invents a plausible-sounding but wrong reason
for a health-adjacent recommendation. Logged in
`/business-brain.md`'s Decisions log as a real product call, not an
implementation detail.

## Safety (not boilerplate)

The single biggest risk the source report itself flags: *"One missed
atrial fibrillation signal or one push-through-illness call is a
business-ending event."* `decision_engine._check_anomaly()` is a hard,
code-level gate — a pattern that looks like illness (depressed HRV
**and** elevated resting HR or breathing rate **and** poor sleep, all
three together, not any one alone) always routes to "see a doctor,"
never to a training recommendation, regardless of what the raw recovery
score says. `test_anomaly_overrides_everything_and_never_recommends_training`
asserts this directly, and a second test
(`test_anomaly_requires_all_three_signals_not_just_low_hrv`) confirms a
normal hard-training week alone doesn't over-trigger it. Every message,
anomaly or not, carries a plain non-diagnostic disclaimer
(`sms_dispatch.DISCLAIMER`).

## Setup

```bash
pip install -r requirements.txt
```

Live sending needs real credentials (fails fast and locally on a
placeholder, same as this project's other builds):

```bash
export OURA_API_TOKEN="your_token_here"      # or WHOOP_API_TOKEN
export TWILIO_ACCOUNT_SID="your_sid_here"
export TWILIO_AUTH_TOKEN="your_token_here"
export TWILIO_FROM_NUMBER="your_twilio_number"
```

## Run it

```bash
# No credentials needed — prints the exact message a subscriber would get:
python run_daily_check.py --demo train_hard
python run_daily_check.py --demo back_off
python run_daily_check.py --demo eat_more
python run_daily_check.py --demo sleep_earlier
python run_daily_check.py --demo anomaly

# Live path (real Oura/Whoop + Twilio credentials required):
python run_daily_check.py --provider oura --to +15551234567
```

## Verification

Proven in this build environment:

- All 5 synthetic scenarios exercised via `test_decision_engine.py`
  (7/7 tests pass) — each asserted against the *specific* branch it
  claims to hit (score above/below the exact threshold), not just "the
  CLI printed something."
- **Two real bugs caught by actually running this**, not by reading the
  code: the original `train_hard` and `back_off` synthetic fixtures
  were hand-picked numbers that looked directionally right but didn't
  actually cross `decision_engine`'s own thresholds. `train_hard`
  happened to still print "Train hard" because the fallback branch is
  also `TRAIN_HARD` — silently correct output for the wrong reason.
  `back_off` did not: it silently fell through to the `TRAIN_HARD`
  catch-all, an actually wrong decision that would have gone right past
  a demo that only checked "did it print something plausible." Fixed by
  recalculating both fixtures against the real thresholds.
- Anomaly safety gate proven directly, including that it requires the
  combination of signals (not one alone) to fire, so it doesn't
  over-trigger on an ordinary hard-training week.
- Both fail-fast paths verified: a placeholder `OURA_API_TOKEN` fails
  locally with a clear message before any network call; `--provider`
  without `--to` fails via a clean `argparse` error.

**Not verified live**: `fetch_oura_reading()`/`fetch_whoop_reading()`
against the real Oura/Whoop APIs, and `send_decision_text()` against a
real Twilio account — this sandbox has no live credentials for either
and no network path to them (same restriction noted in every other
build in this project, e.g. `/notes/prop-firm-sizing-analysis.md`). The
implementations are complete and match each provider's documented v1/v2
response shape, but that's a claim, not a proof, until run against a
real account.

## Sales page verification (Stage 5)

Served locally (`python3 -m http.server`) and screenshotted with
Playwright/Chromium — not just read as HTML. Two real findings from
actually testing it, not from reading the code:

1. **Google Fonts (Space Grotesk/Inter) don't load in this sandbox** —
   confirmed via a failed-request listener
   (`net::ERR_CERT_AUTHORITY_INVALID`, then confirmed as a genuine
   network block rather than a cert-trust artifact by re-checking with
   certificate errors ignored and still getting zero response). Same
   class of restriction as every other external API blocked elsewhere
   in this project (Oura/Whoop/Twilio above, yfinance/EODHD in the
   trading builds) — flagged rather than claimed as verified. The page
   degrades to a system sans-serif fallback, which still reads cleanly
   in the screenshots, but the real Space Grotesk/Inter pairing has
   **not** been confirmed rendering anywhere in this session.
2. **Don't-say-list grep produced two flagged hits ("diagnose",
   "treat") that are correct, not violations** — both are inside the
   disclaimer's negation ("doesn't diagnose or treat anything"), which
   is the intended, necessary use of those exact words. A literal
   substring grep can't tell a claim from its denial; confirmed by
   reading both hits in context rather than either ignoring the check
   or stripping medically-necessary disclaimer language to satisfy a
   naive grep. Noted here so a future check gets negation-aware instead
   of quietly living with this false-positive class.

Confirmed clean: mobile width (375px — price cards stack to one column,
nav and hero hold up, no horizontal overflow), no cream/terracotta or
default blue/indigo, no ALL-CAPS tracked eyebrows, no arrow-suffixed
buttons, no fabricated stats/testimonials/guarantee (every number and
quote traces to the source opportunity report; the "guarantee" section
is the real stated cancel-by-texting-STOP policy, not an invented
refund window), no dashboard/device-mockup imagery (the whole pitch is
"no dashboard," so the page doesn't show one, including in its own
marketing).

## What's deliberately not built yet

No billing/subscription management, no web signup flow, no auth, no
hosting. This is the core decision mechanism — the actual product wedge
the report's research is about — proven correctly, not a production
SaaS. Building the account/billing layer around a verified-correct core
is the right order; building it around an unverified one isn't.
