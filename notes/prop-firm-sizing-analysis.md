# TPT "Secrets of Trading Funded Accounts" — Deep Analysis

Source: `tpt_analysis.html`, a DEEP/DEEPER/DEEPEST/DEEPEST-EST/MONETIZATION/
STACK MAPPING analysis of James Sixsmith's (CEO, Take Profit Trader)
playbook, "the full PDF read, no content estimated or invented" per its own
footer. This is the analysis document that `/builds/prop-firm-sizing/`'s
files (`prop_firm_position_sizing.py`, `prop_firm_sizing.py`,
`prop_pass_simulator.py`) were built against — those files' own docstrings
reference it by a slightly different name
(`tpt_funded_accounts_analysis.html`) and it arrived several rounds after
the code did. This note is the retroactive write-up: what the analysis
claims, checked against what actually got built.

---

## DEEP — what the playbook claims

A prop-firm survival guide (not a trading-strategy guide) built around two
identified faults — trading too large relative to account parameters, and
scalping on short timeframes — and three "secrets": trade the biggest
account you can afford, never exceed 25% of max allowed contracts, and
take your time (the eval requires a minimum 3 trading days anyway). Core
math example: a $50K ES account, 6 max contracts, $1,100 daily loss limit
(22 points), $2,000 EOD trailing drawdown (40 points). At the 25% rule
(1 contract), that's 22 points of risk against a 78-point average daily
range — 28% of daily range, versus 4.7% at max size.

## DEEPER — the critical gap the playbook itself underweights

Two findings drove the actual code:

1. **The EOD trailing drawdown floor follows the high-water mark, not the
   starting balance.** A trader who peaks at $51,500 on a $50K account has
   a floor of $51,500 − $2,000 = $49,500 — closer to breach than the
   playbook's "22 points of daily risk" framing suggests, and the
   playbook barely explains this despite calling it (alongside the daily
   loss limit) one of "the first numbers to look at."
2. **The 25% rule is static and doesn't account for intraday loss already
   incurred.** Down $700 on a $1,100 daily limit means the effective
   remaining budget is $400, not $1,100 — the playbook's math always
   resets to start-of-day.

Both are exactly what `SessionState` in `prop_firm_sizing.py` fixes:
`trailing_dd_floor = high_water_mark - eod_trailing_dd` (not
`starting_balance - eod_trailing_dd`), and `remaining_daily_loss =
daily_loss_limit + intraday_pnl` (shrinks correctly as `intraday_pnl` goes
negative). Confirmed matching — no code change needed, this analysis
arrived after the code and validates it rather than changing it.

## DEEPEST / DEEPEST-EST — what the analysis adds beyond the code

- **Literature grounding**: ties the 25% rule to fractional-Kelly sizing
  (quarter-Kelly or less) and risk-of-ruin mathematics — the playbook's
  intuition is sound even without a rigorous derivation in the source.
- **Regime dependency**: the 78-point ES range example is roughly a
  2022–2023-vintage number; in a low-vol regime it can compress to
  30–40 points, making the "22-point buffer" look tight rather than
  spacious. The code doesn't hardcode any specific range — `average_daily_range_points`
  is always a caller-supplied parameter in `prop_firm_position_sizing.py`,
  consistent with this warning.
- **The 25% rule reframed as a psychological circuit-breaker, not a quant
  rule** — interrupts the revenge-trading/escalation loop rather than
  being independently optimized as a number. Doesn't change any math;
  exposed as a configurable `percent_rule` parameter either way, so this
  is a framing note rather than something the code needed to encode.
- **Incentive-alignment flag**: TPT's "biggest account you can afford"
  advice also maximizes its own subscription revenue (up to 2.4x). Not
  something the sizing math needs to account for, but worth carrying into
  any content/affiliate framing of this toolkit — this project doesn't
  ship gold-dashboard/affiliate output by design (see CLAUDE.md), so this
  finding is noted and not acted on.

## STACK MAPPING — what it proposed vs. what actually shipped

The analysis's proposed architecture names three files: `prop_firm_sizing.py`,
`prop_session_monitor.py`, `prop_pass_simulator.py` — a three-way split
with the trailing-DD tracking logic in its own module. The actual
uploaded `prop_firm_sizing.py` (a later round, real code, not this
analysis's aspirational description) merges the sizing calculator and the
session/trailing-DD tracker into one file via `PropFirmAccount` +
`SessionState` — there is no separate `prop_session_monitor.py`, and none
was ever uploaded. This is a real, harmless divergence between an
early-stage analysis's proposed shape and the actual shipped code's
shape, not a missing file — the functionality described for the
"session monitor" (trailing-DD floor, gap tracking, warning thresholds)
is fully present, just inside `prop_firm_sizing.py` rather than a
separate module. Documented here rather than "fixed," since the real
code is the source of truth, not the earlier analysis's proposed
file layout.

**One genuine, minor gap, not yet built**: the analysis's "Prop Firm
Sizing Calculator" spec asks for "recommended lot sizes for
ES/NQ/MNQ/MES" — i.e., sizing recommendations across multiple contract
types at once, for a single account. The shipped `PropFirmAccount` is
single-symbol (`symbol: str = "ES"`); `print_full_tier_table()` compares
across account *tiers* for one symbol, not across *contract types* for
one account. Not built here — no such function was in the actual
uploaded code, and adding one wasn't asked for — but noted as a
legitimate small next-step rather than silently ignored.

## Verification

No code in `/builds/prop-firm-sizing/` changed as a result of this
analysis arriving — it was cross-checked line-by-line against
`prop_firm_sizing.py`'s `SessionState` and `prop_pass_simulator.py`'s
`PassSimulator` (see `warning_level()`'s 50%/25%/0% thresholds vs. the
analysis's "alerts when gap compresses below 50% consumed", and
`PassSimulator.fail_dd_probability` vs. "probability of hitting the
trailing DD floor before profit target") and matches on every concrete,
checkable claim. Full build + test evidence: see `/builds/prop-firm-sizing/README.md`.
