# Kryptera Strategy Lab / Simple Indicator Strategy Generator — Deep Analysis

Analysis of five uploaded files: `README.pdf` (marketing/spec doc), `README_QuickStart.md`
(Windows user guide for what's actually in the zip), `requirements.txt`, `setup_venv.bat`,
`run_strategy.bat`. **The core script itself
(`simple_indicators_strategy_generator___python_code_bundle_lite_version.py`) was not
uploaded** — everything below about its behavior is inferred from the two READMEs, not
read from the code. That gap matters and is called out explicitly rather than glossed over.

---

## DEEP — what's actually here

Two documents describe *what sounds like the same product* but don't agree with each other:

| | `README.pdf` ("Lite" marketing doc) | `README_QuickStart.md` (Windows guide, what's in this zip) |
|---|---|---|
| Indicator families | 4 (BB, HMA, KAMA, ER) | 6 (BB, HMA, KAMA, **FastKAMA**, ER, **Bar-based**) |
| Total conditions | 93 | 63 |
| Pass criterion | Total Return **> 0** in all 3 phases | Total Return **> Benchmark Return** in all 3 phases |
| Data split | ~60% / 20% / 20% (IS/OOS/NT) | 35% / 35% / 30% (IS/OOS/NT) |
| Execution detail | Open-price, next-bar-after-signal (no look-ahead) | Not stated |
| Cost model | 0.1% fees, 0.2% slippage, `vbt.Portfolio.from_signals()` | Not stated |
| Positioning | "Lite" — upsell to paid "Full" (34 families / 295+ conditions, beat-buy-and-hold) on Gumroad | No mention of a paid tier |

The packaging (`setup_venv.bat`, `run_strategy.bat`, `requirements.txt`) matches the
QuickStart's file list and naming, not the PDF's. So the PDF reads as **older marketing
collateral for an earlier "Lite" build**, and the QuickStart + batch files describe
**what's actually shipped now** — a version that quietly ships the stricter,
paid-tier-grade "beat the benchmark" validation bar the PDF says is a Full-version-only
feature, at a family/condition count in between the two PDF tiers (63, vs. 93 "Lite" / 295+
"Full").

Supporting files:
- **`requirements.txt`**: pins `vectorbt==0.28.5`, floats `pandas>=2.0.0,<3.0.0`, floats
  `numpy>=1.24.0`, and has `numba` **commented out** as "optional."
- **`setup_venv.bat`**: auto-detects Python across PATH/common install dirs, creates
  `.venv`, installs from `requirements.txt`. Ends by telling the user to double-click
  `launch.bat`.
- **`run_strategy.bat`**: checks `.venv` and the main script exist, then runs the script
  inside `.venv`.

## DEEPER — what doesn't add up, and why it matters

1. **`setup_venv.bat` tells the user to run a file that doesn't exist.** Its final message
   says *"Double-click launch.bat to start Kryptera Strategy Lab"* — but the QuickStart's
   own file table, and the actual launcher, is `run_strategy.bat`. For the exact
   non-technical Windows user this product is built for, that's a dead end right at the
   finish line of setup. This is a real, fixable bug, not a nitpick.

2. **`requirements.txt` doesn't actually enforce the constraint the docs warn about.**
   QuickStart's troubleshooting table says *"Do not upgrade pandas manually — it must stay
   on 2.2.3"* and lists `pandas 2.2.3` as a pinned version — but `requirements.txt` only
   says `pandas>=2.0.0,<3.0.0`, which lets pip install any 2.x release, not specifically
   2.2.3. I confirmed this empirically in this session: a plain `pip install pandas numpy`
   with no pin grabbed **pandas 3.0.6** — exactly the version the product's own docs say
   breaks `vectorbt==0.28.5`. An unpinned floor/ceiling doesn't protect against this; only
   an exact pin does.

3. **`numba` is commented out in `requirements.txt` but listed as a required, pinned
   dependency (`0.60.0`) in QuickStart's library table.** One of these is wrong. Given
   QuickStart says numba is what makes `vectorbt` fast enough for a search loop that "runs
   until a passing strategy is found," shipping without it silently is a real
   performance regression for the customer, not just a documentation slip.

4. **The core script is simply not in this bundle.** Every claim about indicator math,
   the search loop, the lookahead-bias handling, and the output format is taken on faith
   from prose descriptions in two documents that already disagree with each other on the
   validation logic. I can't review code that wasn't given to me — the Pro build below is
   written from the spec, not as a line-by-line upgrade of existing code.

5. **No cross-platform packaging.** Setup and launch are Windows-only (`.bat`); the
   Colab route is referenced only as an external "Gumroad download page" link, not
   included in the bundle. Customers on macOS/Linux who don't want Colab have nothing.

## DEEPEST — root causes and what would actually break

- **Version drift between marketing and shipped product** is the underlying cause of
  finding #1 in DEEP: the PDF and the QuickStart almost certainly describe two points in
  time of the same product, and nobody reconciled the numbers when the shipped version
  changed. Left alone, this is a support-ticket generator: a customer who reads the PDF
  before buying and then gets the QuickStart's numbers after buying will reasonably think
  something's missing or wrong.
- **Unpinned dependency floor/ceiling instead of an exact pin** is the kind of bug that
  stays invisible for months and then breaks for every *new* customer simultaneously the
  day a new pandas 2.x (or, as just demonstrated, 3.x) release hits PyPI — while existing
  installs with an already-populated `.venv` keep working. That asymmetry (works for
  existing users, breaks for new ones) is exactly what makes it easy to miss until refund
  requests start.
- **A search loop with no attempt cap** ("loops indefinitely until a passing strategy is
  found") is fine when it usually takes seconds, but has no defined behavior for a ticker,
  date range, or `min_trades`/`size` setting where no combination of the available
  conditions can pass — the honest failure mode is "runs forever with no feedback," which
  looks identical to "frozen" to a non-technical user.
- **Single-file, copy-paste-the-console-output distribution** (rather than writing the
  discovered strategy straight to a `.py` file) is a usability tax on every single
  successful run, and an easy place to lose or corrupt output (partial copy, wrong
  encoding, accidental extra characters) that has nothing to do with the strategy logic
  itself.

## DEEPEST-EST — what "10x Pro" should actually mean here

Not: bigger indicator library for its own sake, and not: bolt-on branding or a switch to
paid market-data APIs this yfinance-based, free-data product was never built around.
Concretely:

1. **Resolve the doc/spec conflict deliberately** — the Pro build adopts the QuickStart's
   6-family/63-condition, 35/35/30-split, beat-benchmark spec (the stricter, more
   recently-documented one) as the single source of truth, and says so explicitly rather
   than silently picking one.
2. **Fix the two packaging bugs** (`launch.bat` reference, `pandas`/`numba` pin mismatch)
   and add exact pins throughout.
3. **Add the metrics a "Lite" tool skips but a "Pro" one shouldn't**: Sharpe ratio, max
   drawdown, win rate, profit factor — not just total return — reported for all three
   phases, plus an explicit benchmark-return figure so "beat the benchmark" is visible,
   not implicit.
4. **Add the safety rails a search loop needs**: a max-attempt cap with a clear,
   actionable message on exhaustion (not an infinite silent loop), and an explicit,
   commented-and-asserted lookahead-bias guard (shift-by-one-bar before signal use),
   matching the PDF's "open-price, next-bar" description but made verifiable in code
   instead of just claimed in prose.
5. **Auto-save the discovered strategy to a timestamped `.py` file** in addition to
   printing it, and add optional CLI flags (ticker/dates/`min_trades`/`size`) so the
   script doesn't require hand-editing for routine reruns — while keeping the top-of-file
   editable constants as the primary, beginner-facing interface.
6. **Ship setup/launch for macOS/Linux too** (`setup_venv.sh` / `run_strategy.sh`),
   mirroring the batch scripts' auto-detection logic.
7. **Carry the legal/educational disclaimer into the script's own docstring**, so it
   travels with the code even if separated from the README.

Full build: `/builds/kryptera-strategy-lab-pro/`.

---

## ADDENDUM 1 — the condition-count contradiction, resolved

A new upload (`strategy_generator_analysis.html`) directly contradicts the
DEEP section's table above. Both can't be right, so here's the honest
reconciliation.

**What I said originally:** the QuickStart's 63-condition/6-family numbers
were "what's actually shipped now" — reasoning from the fact that the
`.bat`/`requirements.txt` packaging matched QuickStart's naming, **not**
from ever having read the core script itself (it was never uploaded to
that session — this was stated explicitly at the time).

**What the new analysis claims:** it was built "from a direct read of...
the full 1,354-line source script (both .py and .ipynb, identical
content)" and reports the `all_columns` list — the actual searchable
condition set the generator draws from — contains exactly **93 conditions
across 4 families** (BB 32, HMA 21, KAMA-incl-FastKAMA 22, ER 18), matching
the PDF, not the QuickStart. It also reports 8 candlestick-pattern
functions that are computed and applied to the dataframe but never added
to `all_columns` — dead code from the generator's own perspective, and a
plausible source of the "6 families" QuickStart figure if whoever wrote
QuickStart counted every indicator family present in the code rather than
only the ones actually wired into the search.

**Which one is more likely correct:** the new analysis, and it isn't
close. A direct read of the shipped script's own `all_columns` list is
strictly stronger evidence than an inference from packaging-file naming
conventions — the packaging match told me which *docs* were shipped
together, not what the *script* actually does. I don't have the script in
this session either, so I can't independently re-verify the 93/4 count
myself — but I have no basis to doubt a claim of direct code inspection
over my own admittedly-weaker inference, and the new analysis's account is
internally consistent (it explains *why* QuickStart's 63/6 numbers exist —
a stale or miscounted doc — rather than just asserting a different number).

**Correction, stated plainly:** the real Kryptera Lite script most likely
ships **93 conditions across 4 wired-in families** (BB, HMA, KAMA, ER),
with 8 unused candlestick functions as dead code, matching the PDF. The
QuickStart's 63/6 breakdown is the stale/inaccurate document, not the
shipped code — the reverse of what this file originally concluded. The
`/builds/kryptera-strategy-lab-pro/strategy_generator_pro.py` build was
written from the QuickStart spec (63/6, beat-benchmark, 35/35/30 split) at
a time when this was the only spec-level information available; its
pass-criterion and split-ratio choices remain reasonable Pro-tier design
decisions on their own merits, but its condition *count* should not be
read as a claim about what the original Lite script contains.

The new analysis's other finding — the unmitigated multiple-comparisons /
data-snooping problem, with no attempt-count disclosure anywhere in the
original — is the single highest-severity finding across both analyses,
and is what the 10X build (`/builds/kryptera-strategy-generator-10x/`)
is built to address directly. See that build's README for the five
concrete fixes (attempt-count disclosure, Sharpe+max-DD gate, multi-symbol
validation, walk-forward folds, cost-stress test).
