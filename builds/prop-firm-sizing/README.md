# ♛ RUTHLESS TRADING GOLD — Prop-Firm Sizing Toolkit

Three tools operationalizing "The Secrets of Trading Funded Accounts"
(Take Profit Trader) into math you can actually run, rather than a table
of one firm's numbers to copy by hand.

## Files

| File | Role |
|---|---|
| `prop_firm_position_sizing.py` | Simple pre-trade check: point-risk from your daily loss limit, the 25%-of-max-contracts rule, and an optional ADR-consumption check. Superseded for day-to-day use by `prop_firm_sizing.py` below (which adds the trailing-DD floor), kept as a standalone quick-check. |
| `prop_firm_sizing.py` | The full account/session model — TPT tier table, contract specs, and the **EOD trailing drawdown floor** calculation the source playbook under-explains. |
| `prop_pass_simulator.py` | Monte Carlo pass-probability simulator for a live evaluation, plus a sizing-strategy comparison across contract counts. |

## The key fix: the trailing drawdown floor follows your high-water mark, not your starting balance

The single most important number this toolkit surfaces that the source
playbook doesn't spell out: your EOD trailing drawdown floor rises with
your peak balance, not your starting balance. A good morning that pushes
your balance up **shrinks** your remaining room, it doesn't grow it.
`SessionState.trailing_dd_floor` in `prop_firm_sizing.py` makes this
explicit and testable instead of an easy-to-miss implication buried in
prose — see the "peaked at +$1,500, now back to +$200" scenario in that
file's own `__main__` block for a worked example (the floor sits *above*
your original starting balance in that scenario, not below it).

## What's kept vs. left out from the source

**Kept** (generalizable, math-checkable): the point-risk-from-daily-loss
calculation, the 25%-of-max-contracts sizing convention (exposed as a
configurable parameter, `percent_rule` / `max_size_fraction` — flagged
explicitly as the source's own stated personal preference, not a
universal rule), and the ADR-consumption idea the source only gestures at
informally.

**Left out**: any claim of a "probability of success" derived from the
source's own numbers — `PassSimulator` computes a pass probability from
**your own** recent daily P&L mean/stdev, supplied by you, not estimated
here. The specific $25K–$150K tier numbers are one firm's product
parameters (`TPT_TIERS`), not a market constant — every calculation takes
your account's actual rules as input.

## Setup

```bash
pip install -r requirements.txt --break-system-packages
```

`fetch_recent_adr()` in `prop_firm_position_sizing.py` is the only piece
that touches the network (EODHD) — everything else is pure math/Monte
Carlo and needs no API key or connectivity.

## Run it

```bash
python prop_firm_position_sizing.py    # quick point-risk check
python prop_firm_sizing.py             # full tier table + trailing-DD session report
python prop_pass_simulator.py          # Monte Carlo pass probability + sizing comparison
```

## Verified

All three files run end-to-end against a pinned venv (`numpy==2.4.6`,
`pandas==3.0.6`, `requests==2.34.2`) in this sandbox. `prop_pass_simulator.py`'s
`PassSimulator` was smoke-tested at 50,000+80,000 total simulated paths in
~1.2s. The one network-dependent function, `fetch_recent_adr()`, could not
be exercised live — this sandbox's proxy blocks EODHD (and every other
non-allowlisted domain), the same restriction noted throughout this
project's other builds — so it's implemented and reviewed but not
live-tested; every other function in the toolkit is pure math and was run
directly, not just read.

## Disclaimer

This is a sizing/risk calculator, not a signal generator or a guarantee
of passing any evaluation. `PassSimulator`'s output is only as good as
the `avg_daily_pnl`/`daily_pnl_std` inputs you give it — pull those from
your own trading journal, not a guess.
