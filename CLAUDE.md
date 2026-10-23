# PROJECT OPERATING RULES

This file makes Claude behave consistently — as both a business
strategist and a hands-on build assistant — without you re-explaining
yourself every time.

## Current status

- Scaffolding just created (context files + folder structure). No
  business context has been gathered yet — `business-brain.md` is an
  empty template waiting to be filled in through conversation.
- First real build shipped: `/builds/kryptera-strategy-lab-pro` — a
  from-spec Pro rewrite of an uploaded "Kryptera Strategy Lab" trading
  strategy generator (source script wasn't provided, only its docs/
  packaging). Full deep-analysis writeup in
  `/notes/kryptera-strategy-lab-analysis.md`. Ran through the full
  isolate→build→prove→ship loop; proved via a pinned-venv fresh install
  and synthetic-data smoke tests (no live network access to Yahoo
  Finance from this sandbox, called out explicitly rather than faked).
- Second build shipped: `/builds/trading-jarvis` — completes an uploaded
  5-file "Trading Jarvis" bundle (2 of its own documented 6 files,
  `signal_generator.py` and `risk_manager.py`, were missing from the
  upload, so the original couldn't even import). Full writeup in
  `/notes/trading-jarvis-analysis.md`. Fixed: fabricated OHLC/volume
  data undermining ATR stops and volume confirmation, a hardcoded
  stale model ID, placeholder API keys going straight to the network,
  no isolation/pinning. Proven via pinned-venv install + synthetic-data
  unit tests + a mocked-Anthropic-client test of the tool-dispatch
  loop (no live EODHD/FMP/Anthropic access from this sandbox — same
  egress restriction as the Yahoo Finance case above).
- `/builds/trading-jarvis` corrected in a second round: the real
  `risk_manager.py` was uploaded (round 1 only had the other 4 files),
  and it's more capable than the from-spec version originally written
  in its place — genuine multi-position portfolio heat via
  `existing_positions`, an `r_multiple_target` field, EWM-based ATR.
  Swapped in the real file (with one schema-consistency fix), wrote
  `signal_generator.py` to match its conventions, added
  `positions_store.py` + `run_strategy.py --add-position/--positions/
  --remove-position` to actually feed `existing_positions` real data
  (previously always empty despite the capability existing), and fixed
  a live `KeyError` in `live_monitor.py` that referenced a schema key
  the real file never had. Addendum in
  `/notes/trading-jarvis-analysis.md` corrects the original analysis's
  wrong claim that multi-position heat wasn't architecturally
  possible. Re-proven end-to-end including the positions CLI and a
  forced BUY-signal print path.
- `/builds/trading-jarvis` gained a Swamp Intelligence reasoning/
  governance layer (round 3): `jarvis_swamp_bridge.py` (new) routes
  every objective through a Task Tree with `approval_required=True`
  hard-coded on risk-bearing steps, before handing off to the real
  Jarvis modules. Its own dependency (`swamp_intelligence.py`) wasn't
  in the first round-3 upload — same "core file missing, only
  consumers uploaded" pattern as round 1 — but arrived, along with the
  real `signal_generator.py` (seen for the first time; resolves an
  earlier HTML analysis's flagged "RSI(65) ambiguity" — period=14 and
  threshold=65 are separate params) and another copy of
  `risk_manager.py` (same unfixed schema bug as round 2, re-fixed),
  in a second upload sent mid-turn. Hardened
  `jarvis_swamp_bridge.py`'s self-test of its own governance guard
  (used to swallow the result either way; now asserts the raise
  happened). Re-applied the model-ID fix and positions wiring, both of
  which reverted in this round's fresh copies of files this session
  had already fixed before — confirms new uploads don't carry forward
  this session's own prior edits. Proven end-to-end: a full
  `route_through_bus()` run against a forced BUY signal, rendering the
  Task Tree, all 4 Event Packets, and a real risk-sized suggestion.
  Addendum 2 in `/notes/trading-jarvis-analysis.md`.
- The actual Brain Spec (`01_brain/swamp_intelligence_core.md`) arrived
  and was checked against the implementation section by section —
  Addendum 3 in `/notes/trading-jarvis-analysis.md`. `EventPacket`'s
  fields and `Priority`'s values match the spec exactly. One real
  violation found and fixed: step 4's `risk_score` was `0`, below the
  spec's stated `1-100` floor — a prior round's fix had (without the
  spec in hand) widened the code comment to `0-100` to rationalize
  that, in the wrong direction; both are corrected now, and `Task`
  validates the range instead of just documenting it. Confirmed
  `ActivationGate`'s dormancy is expected, not a gap: this domain has
  one fixed objective shape, so there's no complexity variance to
  gate. Several spec sections (risk-threshold-derived approval,
  dependency enforcement, agent reassignment, revenue-ranked decision
  logic) have no code behind them — pre-existing, not a regression,
  and left alone as scope expansion nobody asked for.
- A round-4 upload (9 files) turned out to be almost entirely a full
  revert to pre-fix, pre-Swamp-Intelligence snapshots — every code file
  matched an earlier state already superseded in the build (fabricated
  OHLC, stale hardcoded model, `risk_manager.py`'s same schema bug
  arriving a third time, `run_strategy.py` without `--swamp`). Verified
  precisely (grepped the build for each regressed marker, `diff`'d
  `signal_generator.py`) before concluding no code needed touching —
  see Addendum 4 in `/notes/trading-jarvis-analysis.md`. One file was
  genuinely new: an HTML analysis of the *source article* itself
  (distinct from round 3's HTML, which analyzed the uploaded code),
  confirming the article's original pitch (voice + persistent memory +
  live execution via MCP) was broader than what got built, consistent
  with every README's own stated scope cuts. No files changed this
  round.
- Software Factory skills added (`.claude/skills/new-feature`,
  `code-structure`, `evidence-driven-testing`, `review-loop`) — see
  "Software Factory method" under TECHNIQUES below. Not yet exercised
  on a real build.
- Two new builds shipped this round, both stemming from a 5-file upload
  (`README_10X.md`, `strategy_generator_analysis.html`, a huge
  concatenated `.txt`, plus Trading Jarvis originals needing no action —
  same pattern as Addendum 4, re-verified via grep):
  - **`/builds/kryptera-strategy-generator-10x`** — the "10X" structural
    upgrade of Kryptera Lite (attempt-count disclosure, Sharpe+max-DD
    gate, multi-symbol validation, walk-forward folds, cost-stress
    test). `indicators.py` and the already-complete alternative engine
    `ruthless_strategy_lab_10x.py` came from the upload; `conditions.py`
    and `data_pipeline_10x.py` were the missing core files (same
    "referenced but never uploaded" pattern as every Trading Jarvis
    round) and were written here — `conditions.py` builds 144 fixed
    conditions across 12 conceptual indicator families (14 distinct
    name-prefixes — a real, documented discrepancy between "families"
    counted conceptually vs. by column-name prefix, see the build's
    README). Ships **two engines on purpose**: the official
    `strategy_generator_10x.py` (breadth — fixed condition library,
    multi-symbol, walk-forward, vectorbt-dependent) and
    `ruthless_strategy_lab_10x.py` (depth — per-trial randomized
    parameters, single-symbol, no vectorbt dependency), documented as a
    deliberate tradeoff rather than merged into one. Found and fixed a
    real bug while testing the alternative engine: `run_backtest`'s
    `win_rate` counted profitable bars-in-a-position rather than
    profitable trades, producing values above 1.0 (reproduced with
    synthetic data: `win_rate == 6.16`) — fixed to a proper per-trade
    win rate. Also found and fixed the same `vectorbt`/`plotly` 6.x
    theme-init crash from the Kryptera Pro build recurring here
    (`plotly==5.24.1` now pinned). Proven end-to-end: pinned-venv
    install, `indicators.py`+`conditions.py` against synthetic OHLCV
    (144 conditions, all correctly shaped), `Generator10X.search()`
    both pass and `RuntimeError`-exhaustion paths on synthetic
    multi-symbol data, `run_10x.py`'s full CLI wiring against a mocked
    `yfinance` (real vectorbt backtests, exhaustion path fired
    correctly after 400 real attempts), `data_pipeline_10x.fetch_basket`
    against a mocked `yfinance` (full basket / partial-skip /
    all-fail paths), and `ruthless_strategy_lab_10x.py`'s registry +
    backtest + full search (found and not-found paths) + standalone
    script rendering. No live yfinance access from this sandbox — same
    egress restriction as every other build here, called out rather
    than faked.
  - **`/builds/prop-firm-sizing`** — a self-contained TPT funded-account
    toolkit (no missing imports, unlike everything else this round):
    `prop_firm_position_sizing.py` (simple point-risk/25%-rule/ADR
    check), `prop_firm_sizing.py` (full account/session model —
    surfaces the EOD trailing-drawdown floor following the high-water
    mark rather than the starting balance, the key insight the source
    playbook under-explains), `prop_pass_simulator.py` (Monte Carlo
    pass-probability simulator + sizing-strategy comparison). Proven by
    actually running all three scripts end-to-end (not just reading
    them) against a pinned venv — the trailing-DD-floor scenarios and
    the Monte Carlo output were inspected for correctness, not just
    "ran without crashing." Only unverified piece: `fetch_recent_adr()`
    needs EODHD, blocked in this sandbox.
  - Addendum 1 written to `/notes/kryptera-strategy-lab-analysis.md`:
    the new `strategy_generator_analysis.html` (built from a claimed
    direct read of the real 1,354-line Kryptera Lite script) reports
    93 conditions/4 families, matching the original PDF — contradicting
    this project's own earlier analysis, which had adopted
    README_QuickStart.md's 63/6 figures as authoritative purely from
    packaging-naming inference, never having seen the actual script.
    Resolved in favor of the new analysis (direct code read beats
    inference from doc naming) and corrected in place, stated plainly
    as a self-correction rather than silently overwritten.
- Follow-up round: re-upload of the same 5-file set (huge `.txt`, both
  `README.md` variants, `README_10X.md`, and the PDF) confirmed
  byte-identical to the prior round via direct `diff` — no code
  changes needed, same "verify precisely before touching anything"
  discipline as every Trading Jarvis round. One genuinely new file:
  `tpt_analysis.html`, the previously-missing source analysis that
  `prop_firm_position_sizing.py`'s own docstring had referenced by
  name (`tpt_funded_accounts_analysis.html`) several rounds before it
  actually arrived. Cross-checked line-by-line against the already-
  shipped `/builds/prop-firm-sizing/` toolkit — every concrete claim
  matches (the trailing-DD-follows-high-water-mark fix, the
  intraday-loss-aware daily-limit fix, the 50%/25%/0% warning
  thresholds, the Monte Carlo DD-vs-profit-target framing) since the
  toolkit was built from the real uploaded code, not from this
  analysis. Wrote the retroactive write-up as
  `/notes/prop-firm-sizing-analysis.md`, including one honestly-flagged
  small gap versus the analysis's aspirational spec (multi-contract-
  type sizing recommendations for one account — not built, not asked
  for, noted rather than silently ignored or silently added).
- The three `/builds/prop-firm-sizing/` tools wired into
  `/builds/trading-jarvis/jarvis_orchestrator.py` as a new, separate
  tool category (`prop_firm_size_check`, `prop_firm_session_report`,
  `prop_firm_pass_probability`) — TPT funded-account sizing, kept
  independent of the existing EODHD/FMP symbol-trading flow, with the
  system prompt explicitly telling Claude not to mix the two. The
  three prop-firm `.py` files were copied into `trading-jarvis/`
  unmodified (its `requirements.txt` already pinned the exact same
  `numpy`/`pandas`/`requests` versions, so no dependency changes were
  needed). Proven two ways: `_run_tool()` called directly for all
  three (the "peaked then gave back" trailing-DD scenario and a Monte
  Carlo pass-probability call both matched the standalone toolkit's
  own previously-verified output exactly), then the full
  `ask_jarvis()` tool-dispatch loop proven end-to-end against a mocked
  Anthropic client — a simulated `prop_firm_session_report` call,
  real computation, JSON round-trip back through `messages`, and an
  assertion on the second turn that the correct numbers arrived before
  the final answer was produced.
- Added `--prop-size-check`/`--prop-session`/`--prop-pass-prob` (plus
  their `--prop-tier`/`--prop-symbol`/`--prop-contracts`/`--prop-adr`/
  `--prop-pnl`/`--prop-hwm`/`--prop-start-balance`/`--prop-balance`/
  `--prop-days`/`--prop-avg-pnl`/`--prop-pnl-std` parameters) to
  `run_strategy.py` — CLI access to the same three prop-firm tools
  `jarvis_orchestrator.py` exposes to Claude, no Anthropic key needed.
  Reuses `SessionState.report()`/`PassSimulator.report()` directly
  rather than re-implementing their formatting. Proven as real
  subprocess CLI calls (not just function calls): all three reproduce
  the standalone toolkit's exact numbers, `--help` renders cleanly,
  missing-flag calls give a clean `argparse` error. Caught and fixed a
  real rough edge while testing: an invalid `--prop-tier`/`--prop-symbol`
  initially surfaced as a raw Python traceback (`PropFirmAccount`'s
  `ValueError` and `CONTRACT_SPECS`'s bare `KeyError` were both
  unhandled at the CLI layer) — now caught and printed as a one-line
  plain-English error listing the valid values, per this file's own
  non-coder communication rule.
- Added `--prop-compare` (plus `--prop-compare-size`, repeatable
  `CONTRACTS:AVG_PNL:PNL_STD` entries) to `run_strategy.py`, wiring
  `prop_pass_simulator.compare_sizing_strategies()` — deliberately
  CLI-only, not added as a fourth Claude tool, since its
  `{contracts: (avg_pnl, pnl_std)}` input shape fits a CLI's
  repeated-flag list more naturally than a single NL tool call. Proven
  as a real subprocess CLI call reproducing `prop_pass_simulator.py`'s
  own `__main__` example numbers exactly (1.7%/27.1%/49.7%/70.8% across
  1/2/3/6 contracts), plus a missing-flag `argparse` error and two
  malformed-`--prop-compare-size` cases (wrong field count, non-numeric
  field) both giving a plain-English format error instead of a raw
  parse exception.
- **Fourth build shipped: `/builds/prop-firm-dashboard`** — a Streamlit
  web dashboard, four tabs mirroring the four `--prop-*` CLI flags
  (Size Check, Session Report, Pass Probability, Compare Sizes), same
  RUTHLESS TRADING GOLD black/gold branding as every HTML analysis
  dashboard and CLI banner in this project (Cinzel Decorative + Cormorant
  Garamond + IBM Plex Mono, one gold brand colour — per
  `design-rules.md`'s "derive the palette from one brand colour" rule,
  with the explicit user-named RUTHLESS scheme overriding that file's
  own unset placeholder green, exactly the case that rule anticipates).
  Calls `PropFirmAccount`/`AccountRules`/`SessionState`/`PassSimulator`
  directly — the same classes every other interface uses, not a
  reimplementation; the Compare Sizes tab loops `PassSimulator` per row
  rather than calling `compare_sizing_strategies()` directly, since
  that function prints to stdout instead of returning data a Streamlit
  table/chart can use. Followed the screenshot-before-done rule
  properly: served locally, screenshotted with Playwright/Chromium (the
  sandbox's pre-installed browser), found and fixed two real bugs in
  the first pass — CSS leaking as literal visible text above the header
  (a blank line inside the injected `<style>` block broke CommonMark's
  raw-HTML-block passthrough) and an empty orphan `<div>` box (Streamlit
  doesn't let one `st.markdown` open a tag that a later separate call
  closes — each call is an isolated fragment) — then re-screenshotted
  clean on a second pass, plus two targeted edge-case checks (an
  oversized-contracts + thin-ADR warning state, a CRITICAL trailing-DD
  session state) with every number cross-checked against this project's
  own previously-verified figures, not just eyeballed for "looks
  right." Also fixed two `use_container_width` deprecation warnings
  (Streamlit 1.64 wants `width="stretch"`) surfaced by actually running
  the app. Not yet deployed anywhere — local-only so far.
- **New technique added: Build Brain method** — an uploaded export of a
  six-stage "RUTHLESS AFFILIATE GOLD" SaaS-idea-to-launch wizard
  (Interview Builder → Idea Engine → DNA Lock → One Shot Engine →
  Sales Page Engine → Launch Pad), demoed with placeholder interview
  answers producing a fictional "RemixForge" video-remix SaaS. Per this
  round's explicit instruction, RemixForge itself was **not** built —
  the wizard's stage structure was analyzed
  (`/notes/ruthless-affiliate-gold-build-brain-analysis.md`) and
  generalized into a reusable, domain-agnostic template
  (`/prompts/build-brain-method.md`), added as this project's third
  named TECHNIQUE alongside Goal/Loop and Software Factory. The
  analysis found this project already has equivalents for 3 of the 6
  stages (Interview→`business-brain.md`, DNA Lock→`design-rules.md`,
  One Shot Engine→Software Factory) and was missing the other 3 (Idea,
  Sales Page Engine, Launch Pad) — the template fills that gap. Also
  flagged two real issues in the source export: a `palette` field that
  serialized as `[object Object]` instead of real hex values (a
  plumbing bug in whatever exports that wizard's state), and a lazy-
  interview-answers-still-produce-confident-specific-output risk, both
  folded into the new template as explicit warnings/fixes rather than
  silently carried forward.
- **Build Brain Stage 5 built out as a real skill**:
  `.claude/skills/sales-page-engine`, matching the format of the
  existing Software Factory skills (YAML frontmatter + trigger
  phrases). Covers the full direct-response page skeleton (hero → pain
  → mechanism → offer stack → pricing → guarantee → who-for/not-for →
  FAQ), a pre-flight check that DNA Lock/One Shot Engine actually ran
  before writing anything (refuses to invent a palette or price that
  `design-rules.md`/the offer don't already have), design rules pulled
  straight from `design-rules.md` plus sales-page-specific anti-patterns
  (fake countdown timers, fabricated social-proof counters, unbacked
  urgency language), a "copy honesty" rule extending the earlier lazy-
  interview warning to its actual failure mode (fabricated-sounding
  specificity papering over a thin `business-brain.md`), and a
  screenshot-before-done self-check that adds a literal grep of the
  rendered copy against `design-rules.md`'s don't-say list — the "turn
  a style guideline into an actual check" idea flagged as the best
  piece of the original source export. `build-brain-method.md` and
  `CLAUDE.md`'s TECHNIQUES entry both updated to point to it.
- **Build Brain Stage 6 built out as a real skill, completing all six
  stages**: `.claude/skills/launch-pad`. No worked example existed for
  this stage (the source wizard export hadn't run it), so it was built
  directly from this project's own rules instead of distilled from an
  upload, matching `sales-page-engine`'s structure: a pre-flight check
  that DNA Lock and the sales page actually exist (ad copy must reuse
  the sales page's own hooks, never reinvent the pitch), ad-copy formats
  by channel/length (short social/paid, medium cold-DM, long email) each
  required to reuse Stage 3's do-say phrases, a launch-plan structure
  that forces a specific channel-first choice grounded in
  `business-brain.md`'s actual stated assets, a dated/ordered sequence,
  a real first-customer number pulled from the 90-day goal (flagging it
  if that's still the unfilled placeholder), and a "what counts as
  working vs. not" decision point so a launch doesn't drift
  indefinitely. Same anti-fabrication rules as Stage 5 (no fake
  urgency/social proof, same don't-say-list grep) plus a rule against
  ad copy promising anything the actual offer/build doesn't have. Notes
  that finishing this stage means writing `## Launch Plan` into
  `business-brain.md`, closing the full interview→idea→brand→build→
  sales-page→launch arc in one place. `build-brain-method.md` and
  `CLAUDE.md`'s TECHNIQUES entry both updated to point to it — Build
  Brain's six stages all have a real project file or skill behind them
  now.
- **Build Brain run end-to-end for real, first time: `/builds/recovery-desk`**
  (Recovery Desk — a daily wearable-recovery decision text service),
  from an uploaded IdeaBrowser opportunity report. Unlike the RemixForge
  demo, this was explicitly "run it for real" — `business-brain.md` and
  `design-rules.md` are genuinely filled in now, not templates. All six
  stages:
  - **Interview/Idea** (`business-brain.md`): filled from the report's
    real sourced data (Reddit pain quotes, Rock Health/App Store stats,
    competitor pricing) — but "Who I am" is flagged explicitly as
    unconfirmed, not assumed: the report states an ideal-founder profile
    (endurance athlete, owns both Oura and Whoop, active in the target
    communities) that was never actually checked against the real
    person building this. Idea alternatives are the report's own
    surfaced options (CGM variant, broad multi-wearable coach, chat-led
    upsell), labeled as such rather than presented as independent
    brainstorming.
  - **DNA Lock** (`design-rules.md`): a new locked brand — deep
    recovery green `#3E7C5C` on near-black, Space Grotesk/Inter,
    deliberately distinct from Whoop's neon lime and Oura's teal/white.
    Coexists with the unrelated RUTHLESS TRADING GOLD portfolio under
    `/builds/` (that work keeps its own pre-existing black/gold
    branding; this file governs new Recovery Desk work going forward).
  - **One Shot Engine** (`/builds/recovery-desk/`): a real, tested MVP —
    `decision_engine.py` (deliberately rules-based, not LLM-generated —
    logged as a real product decision, not an implementation detail:
    the source report itself says the moat is a trusted decision, not
    model intelligence), `data_pipeline.py` (real Oura/Whoop API
    adapters, untested live — no sandbox network access, same
    restriction as every other build here — plus `synthetic_reading()`,
    what every test actually runs against), `sms_dispatch.py` (Twilio,
    same fail-fast-on-placeholder-credential pattern as `data_pipeline.py`
    elsewhere in this project), a hard code-level safety gate
    (`_check_anomaly`) that overrides any training recommendation with
    "see a doctor" on an illness-like data pattern, never just a prompt
    instruction. `test_decision_engine.py`, 7/7 passing, caught two real
    bugs: the `train_hard` and `back_off` synthetic fixtures didn't
    actually cross their own thresholds (`back_off` silently fell
    through to the `TRAIN_HARD` catch-all) — fixed by recalculating the
    fixtures against the real thresholds, not by loosening the
    thresholds.
  - **Sales Page Engine** (`/builds/recovery-desk/sales-page/`): built
    via `.claude/skills/sales-page-engine`, screenshotted with
    Playwright (desktop + mobile), every stat/quote traced to the
    source report (no fabricated numbers), the offer's real
    cancel-by-texting-STOP policy used instead of inventing a guarantee.
    Two real findings from actually testing it: Google Fonts don't load
    in this sandbox (confirmed as a genuine network block, not a
    cert-trust artifact, via a second check with cert errors ignored) —
    flagged as unverified rather than claimed working; and the
    don't-say-list grep flagged "diagnose"/"treat" as false positives —
    both hits are the disclaimer's correct negated usage ("doesn't
    diagnose or treat anything"), confirmed by reading them in context
    rather than stripping medically-necessary language to satisfy a
    naive grep.
  - **Launch Pad** (`/builds/recovery-desk/launch/ad-copy.md` +
    `business-brain.md`'s new `## Launch Plan`): built via
    `.claude/skills/launch-pad`. Ad copy reframed to match the source
    report's own actual distribution plan — reply-in-existing-thread,
    not cold DM, since r/ouraring/r/whoop's own norms (and the report's
    own stated channel strategy) rule out unsolicited outreach. Launch
    plan uses a real near-term target (one paying subscriber within 45
    days, the low end of the report's own 45–90-day estimate) and a
    real "what counts as not working" trigger, not "post and see."
  - Not deployed anywhere — local-only, same as `/builds/prop-firm-dashboard`.
    When it is, the sales page (static HTML) fits Netlify/Cloudflare
    Pages and the daily-check script fits a scheduled job rather than a
    long-running server; not recorded as this project's actual
    Deployment default in the section below since nothing's live yet —
    that note is for the first real deployment, not a plan for one.
- **Build Brain Stages 3–6 run on the existing `/builds/prop-firm-dashboard`**,
  explicitly skipping Interview/Idea (context given inline this round: a
  Monte Carlo pass-probability tool for TPT/Topstep/Apex evals, honest
  hook is it refuses to run without the trader's own journal avg/std
  daily P&L). New brand, **The Pass Line** ("Feed it your real numbers,
  or it doesn't run."), locked in `design-rules.md` as a second, scoped
  brand alongside Recovery Desk's — confirming the existing RUTHLESS
  black/gold/Cinzel-Cormorant-IBM-Plex-Mono palette already baked into
  `streamlit_app.py` rather than re-deciding it, and adding the
  name/tagline/voice do-say-don't-say that didn't exist yet. Since this
  build is part of the unrelated RUTHLESS portfolio (not the business
  `business-brain.md` tracks per this file's own note), Stage 6's launch
  plan was written to a build-local `/builds/prop-firm-dashboard/launch/ad-copy.md`
  instead of `business-brain.md`, matching every other RUTHLESS build's
  self-contained-README convention rather than conflating two unrelated
  businesses in one file. Sales page built and screenshot-verified
  (desktop 1440px + mobile 375px, Playwright/Chromium) — clean on the
  first pass, no CSS-leak or orphan-div bugs this time; confirmed (again)
  that Google Fonts are network-blocked in this sandbox, same finding as
  Recovery Desk's sales page, flagged rather than claimed as rendering.
  Don't-say-list grep clean on the sales page; one false-positive hit on
  the launch copy ("guaranteed pass") that's the negated meta-statement
  in the scope note, not an actual violation — same false-positive class
  already documented for Recovery Desk's "diagnose"/"treat" hits. Real
  call made and stated plainly rather than invented: this build has no
  billing/auth code at all, so the sales page prices it **$0, free,
  local-only** — Stage 4 (offer/pricing) was never actually run this
  round. Launch plan's first-customer target substitutes a real, stated
  assumption for the usual paying-subscriber number, since this is free
  with no analytics: 25 people requesting/running the tool within 30
  days, tracked via thread replies/DMs (the only mechanism that exists).
- **The Pass Line's sales page rebuilt** on a trading-course-lead-magnet
  structure per this round's explicit request (cold-open hook → honest
  reframe with no invented failure-rate stat → mechanism → a new "win
  rate isn't the whole story" teaching beat on expectancy/variance vs.
  the drawdown floor → the labeled example run → offer stack →
  who-for/not-for → a free email-signup CTA as the RUTHLESS TRADING
  GOLD front door), keeping every hard rule from round one (no invented
  results, no guarantees, unchanged tagline). Don't-say-list grep clean.
  **A real bug found and fixed**: the Example Run `<table>` element
  triggered a genuine Chromium full-page-screenshot bug — bottom-of-page
  content bled into the top of every stitched capture, reproducibly,
  and specific to this page (Recovery Desk's similarly tall sales page
  stayed clean under the identical capture method). Isolated by
  bisecting five other hypotheses (sticky nav, `backdrop-filter`,
  smooth-scroll, `<pre>`, `box-shadow`) before finding it; fixed by
  rebuilding the table as an accessible CSS Grid. A second, smaller
  real bug surfaced in the same investigation — the nav's
  `backdrop-filter` blur could show a stale ghost of prior content
  during fast scrolling — fixed by dropping it for a solid background.
  Final verification used scroll-segmented real-position screenshots
  across the full page (not a single stitched capture, since that mode
  is where the first bug lived), desktop and mobile, both clean.
  Full writeup in `/builds/prop-firm-dashboard/README.md`.
- **New build, `/builds/outage-alert`**: a silent-failure detector
  (`outage_alert.py`) for an entirely separate local project the user runs
  (`C:\trading_system\` — a multi-agent LangGraph stock/options paper-
  trading system, not part of RUTHLESS TRADING GOLD). Flagged clearly
  before doing anything: a first message referencing these files was
  actually meant for that other, local session (Windows path, files that
  don't exist anywhere in this repo) — asked for clarification rather than
  guessing, then the user pasted the real `outage_alert.py` source and
  both wired runners. Reviewed all three against `outage_alert.py`'s own
  three touch points (create tracker / record per-ticker outcome / check-
  and-alert after the equity snapshot) — all three correct as wired,
  including the `record()` outcome-mapping (`parsed['signal']` for stocks,
  `strategy` for options). **Found and fixed a real bug** by tracing
  control flow (couldn't execute the runners themselves — this sandbox
  has none of their dependency modules): in both runners, the unguarded
  `log_trade()`/position-opening calls sit inside the same function
  `main()` wraps in a blanket per-ticker `try/except`, so a downstream
  storage/logging failure unrelated to the trading pipeline could
  double-record that ticker's outcome. Reproduced standalone against the
  real `outage_alert.py` (which has zero external dependencies, so it
  could be run for real here): a perfectly healthy 5-ticker HOLD day with
  2 tickers hitting an unrelated `"rate_limit"`-flavored storage error
  false-triggered a full outage alert. Fixed by wrapping those calls in
  their own try/except that warns instead of propagating. Verified via
  `py_compile` (clean before/after, diff is exactly the two guards) and a
  standalone integration test replicating the fixed control flow, which
  asserted exactly one record per ticker and no false alert. Couldn't run
  `--report-only` against the actual runners here (no environment); said
  so plainly instead of faking it — the user then ran both fixed runners
  for real (stronger than `--report-only`, a full 13-ticker pipeline run)
  and pasted the output: stock (11 signals + 2 holds = 13) and options
  (7 signals + 6 holds = 13) both matched their ticker counts exactly,
  confirming no double-record in the wild. No downstream failure occurred
  in that run, so the fix's guard itself (vs. just the happy path) is
  still only proven by the standalone test, not live fire — noted as a
  worthwhile follow-up in the README. Added to `/builds/` (rather than
  left unpushed) at the user's explicit request for a commit/push/merge-link,
  with a Decisions-log note that this is a one-off, not a new pattern for
  unrelated local projects landing in this repo.
- **Deep analysis + new build from an uploaded Factory.ai white paper**
  ("Software Factory: An Autonomy Maturity Model for the Enterprise") —
  full writeup in `/notes/software-factory-autonomy-maturity-model-analysis.md`.
  Named clearly as vendor marketing (every capability in its own
  Capability Map ties to a paid Factory.ai product, page ends on "CONTACT
  SALES") with a genuinely useful framework inside it — binary automatable
  signals, non-linear per-level point weights (1/2/4/8/16), and a
  "% of repos at Level 3+" headline metric chosen over an averaged score
  for board legibility. Flagged what doesn't check out: the paper's "10×
  code-gen ≈ +10% overall" claim is asserted, not sourced to any shown
  data; an "Outcomes from enterprise deployments" chart exists only as an
  unreadable image (pypdf extracted zero body text from that page), so no
  numbers from it are quoted anywhere; the full signal-to-point mapping
  for Levels 3–5 isn't disclosed, so nothing here claims to reproduce
  Factory.ai's actual proprietary scorer. **Built**, per this project's
  established pattern of extracting a vendor wizard's generalizable
  structure without building the vendor's own branded instance (same move
  as Build Brain method from the RUTHLESS AFFILIATE GOLD export —
  RemixForge was never built): `/builds/agent-readiness-scorecard/` —
  a real, dependency-free Python scorer implementing an original,
  locally-checkable signal set (not Factory.ai's undisclosed rubric)
  across Levels 1–3 only, since Level 4/5 signals in the source paper are
  operational telemetry (sub-minute feedback, auto-picked-up tickets,
  multi-day mission reliability) that cannot be observed from files on
  disk — reported as "not assessable" rather than faked. Actually run
  against this repo for real: Level 1 (14/37 assessable points), read
  honestly in the README as an accurate reflection of this being a
  multi-build workspace rather than one deployable service (no repo-wide
  CI/linter/type-checker because it was never built as a single
  codebase), not a verdict on work quality. Also run against a
  `/builds/` subproject (`recovery-desk`, scored lower still, with the
  limitation of a repo-level framework applied one subfolder at a time
  stated plainly) and in `--json` mode. Every `pass`/`fail` result in the
  root-repo run spot-checked by hand against the actual files (confirmed
  no `.flake8`/CI workflows exist before trusting a `fail`; confirmed
  `CLAUDE.md`, `.github/CODEOWNERS`, `.devcontainer/` really exist before
  trusting a `pass`) rather than taking the tool's own output on faith.
- **Deep analysis + new build from an uploaded Fareed Khan Medium article**
  ("Building the 11 Layers of a Production-Grade MCP Server + Agentic
  System") — asked which of analysis-only vs. analysis-plus-build was
  wanted rather than guessing on a 12-component "production-grade" scope
  with no instruction attached; the user chose **analysis + a real
  build**. Full critique in
  `/notes/production-grade-mcp-server-analysis.md`: what's genuinely
  well-reasoned (the Structured Error Framework, retryable-only circuit-
  breaker counting, the tiered tool hierarchy, DB-layer tenant isolation
  via Postgres RLS, the deliberate `NotImplementedError` stub guarding
  long-term-memory writes from becoming a policy/audit back door) versus
  three specific uncited statistics and, flagged most pointedly, a
  twice-repeated, uncited claim that "Asana's MCP-powered feature leaked
  customer data across 1,000 organisations" — not repeated as fact
  anywhere in this project's own writeup. **Built**:
  `/builds/prop-firm-mcp-server/` — a real MCP server, using the actual
  official `mcp` Python SDK over stdio (not a hand-rolled approximation),
  exposing the already-proven `/builds/prop-firm-sizing/` toolkit as four
  tools (`prop_firm_size_check`, `prop_firm_session_report`,
  `prop_firm_pass_probability`, `prop_firm_compare_sizes`) — a fifth
  interface on the same classes every other interface in this project
  already uses, not a reimplementation. Hit and resolved a real
  environment issue first (`pip install mcp` initially failed on a
  PyJWT/debian-package conflict; fixed via `pip install --ignore-installed
  pyjwt` then a clean `mcp` install, landing on 2.3.0), then discovered —
  by writing and running a real probe server+client over actual stdio
  before trusting anything — that the installed SDK's real API
  (`mcp.server.mcpserver.MCPServer`, `ToolError` returning a plain-text
  `CallToolResult` with `isError=True`) diverges materially from the
  source article's code samples (which target an older SDK with a
  structured `error.data` channel); `errors.py`'s SERF-lite
  implementation and its module docstring document this divergence
  explicitly rather than silently papering over it. Applied this
  project's established "extract the generalizable pattern, build only
  what the scale warrants, state every cut with a one-line reason"
  discipline (same move as Build Brain and the Agent Readiness
  Scorecard): built SERF-lite, the atomic tier of the three-tier tool
  hierarchy, structured JSON-lines audit logging (SHA-256'd arguments),
  and in-process token-bucket rate limiting (with the exact trigger
  condition for needing Redis instead stated plainly); explicitly cut
  OAuth/JWT, Postgres RLS multi-tenancy, Redis, circuit
  breakers/retry/ATBA (no upstream network call exists to protect
  against), OpenTelemetry/Prometheus/Grafana, and the four-agent LLM
  copilot (wrapping a deterministic Monte Carlo calculator in an agent
  pipeline would be pure over-engineering), each with its reason recorded
  in the build's README. Proven via a real end-to-end test
  (`test_client.py`) spawning the server as a subprocess and driving it
  with a genuine `mcp.ClientSession` over real stdio — not a unit test
  that imports the tool functions directly — with every numeric result
  checked against both a direct call to the same underlying class/
  function in the same script (exact match, exploiting `PassSimulator`'s
  fixed `seed=42`) and against this project's own previously-verified
  dashboard figures (36.7% pass probability; 1.7/27.1/49.7/70.8% across
  the compare-sizes scenarios), plus a deliberately triggered SERF
  validation error and a deliberately tripped rate limit, both asserted
  on their actual SERF-coded output. All checks passed on the real run.
- **`/builds/prop-firm-mcp-server` extended with the three same-day
  follow-ups requested after it shipped**: (1) HTTP transport — `server.py`
  now takes `--transport stdio|http`, using the SDK's real
  `run_streamable_http_async`, so more than one MCP client can talk to one
  running process instead of only one subprocess per client. (2) Redis
  rate limiting, built for real rather than left as a stated-but-unbuilt
  trigger condition — `ratelimit.py` gained `RedisTokenBucket`, an atomic
  refill+check+decrement Lua script (same pattern the source article
  uses), auto-selected whenever `--redis-url`/`$REDIS_URL` points at a
  reachable Redis, with a clean fallback to the original in-process
  bucket (printed reason, not silent) when it doesn't — stdio keeps the
  in-process bucket by default since it's still correct there. Proven via
  a new `test_http_client.py`: spawns the server over real HTTP, drains
  `prop_firm_compare_sizes`'s 5-token bucket from one client session, then
  shows a brand-new second session (fresh TCP connection) is still
  rate-limited — the only way that's possible if the quota is real shared
  Redis state rather than per-connection memory. All checks passed with a
  real local `redis-server`; the original stdio `test_client.py` was
  re-run afterward and still passes unmodified. (3) Documented the server
  as a fifth tool-surface inside `/builds/trading-jarvis/jarvis_orchestrator.py`'s
  own docstring (a new "ALTERNATE INTERFACE" section) pointing at it
  alongside the existing CLI/Claude-tool-use/Streamlit interfaces, same
  classes and numbers, not a second implementation. Also added a real,
  correct Claude Desktop `claude_desktop_config.json` snippet to the
  build's README and documented how to use it — but flagged plainly
  rather than faked: this sandbox has no Desktop GUI and no live
  Anthropic API access (same restriction every other build here states),
  so the config is built from the SDK's actual stdio contract and
  verified against it, but hasn't been clicked through in a real Desktop
  window from inside this session.
- **Deep analysis + new build from an uploaded Fareed Khan article,
  "Building Fast Computer Agents to Solve Complex Tasks"** (interface
  lifting: replace screenshot-driven GUI agents with typed tools that
  drive each program's own native interface — file format, CLI, COM/
  scripting, API, accessibility tree last). Full critique in
  `/notes/interface-lifting-fast-computer-agents-analysis.md`: what's
  genuinely well-reasoned (the tool contract's mandatory verifier, the
  five-interfaces-in-order claim backed by a checkable ScreenSpot-Pro
  figure, the reversibility-based approval-gate reasoning, the hard-coded
  prompt-injection safety classifier) versus what doesn't check out —
  the entire quantitative case resting on one anecdotal weak baseline
  (the author's own early, admittedly-struggling screen agent, one run),
  a curated best-case ledger with no failure rows for the new
  architecture, and an unsourced "180 of 180" test-suite claim flagged on
  sight the same way this project flagged the Factory.ai paper's
  unreadable chart and the MCP-server article's uncited stats two rounds
  ago — not repeated as fact here. Unlike those two articles, this one
  shows real code for nearly every mechanism, which is a materially
  stronger evidentiary bar, reflected in the critique leaning toward
  "unverifiable/cherry-picked measurement" rather than "invented
  mechanism." **Built**: `/builds/interface-lift-toolkit/` — the
  article's generalizable architecture (tool registry with schema derived
  from type hints + docstring, a `{ok, summary, files, checks}` result
  contract, a regex-based tool-group shortlist scorer, `run_chain` for
  one-call dependent tool-call planning with `$id` references, a real
  local/outward approval gate, a measurement ledger, and a skill compiler
  that turns one successful chain into a new parametrized tool) — built
  for real, not the article's own specific instance (118 Windows
  desktop-program integrations: Photoshop/Excel-COM/AutoCAD/Blender/
  CapCut/UI-Automation), which doesn't transfer to this sandbox at all —
  a platform mismatch (no Windows, no GUI programs installed, nothing to
  lift), stated plainly rather than silently worked around, same
  discipline as every other sandbox-network-restriction note in this
  file. Two deliberate adaptations recorded in the build's README: tool
  schemas come out in Anthropic's native shape (matching
  `jarvis_orchestrator.py`'s established `TOOLS` convention, not the
  article's OpenAI-shaped one), and the skill compiler operates one layer
  down from the article's (compiles a recorded `run_chain` step list
  instead of a screen-agent run, since there's no screen loop here to
  compile from). Demonstrated against this project's own already-proven
  `prop_firm_sizing.py`/`prop_firm_position_sizing.py`/`prop_pass_simulator.py`
  (copied in unmodified, same convention as every other interface on this
  toolkit) rather than toy stand-ins. Proven two ways: `test_toolkit.py`
  (pure mechanics, no network — registry schema derivation, the result
  contract's `ok`-from-checks rule, the shortlist scorer, `run_chain`'s
  `$id` resolution and its stop-at-first-failed-check rule, the approval
  gate holding an outward call and enforcing single-use approval, and the
  skill compiler replaying a compiled tool with new parameters matching a
  direct call exactly) and `test_agent_loop.py` (the real dispatch loop
  against a mocked Anthropic client, same established mocking convention
  as every other tool-dispatch-loop test in this project, since this
  sandbox has no live Anthropic access — proving the registry really
  dispatches to the real prop-firm-sizing code and the approval gate
  really holds the outward call rather than executing it inline). All
  checks passed on both real runs.
- **Deep analysis + new build from six uploaded transcripts/articles about
  "Jev"** (TypeSafe AI's non-generative "judgment model" — state + typed
  Choice/Noul/Score questions in, calibrated probabilities out, no text
  generation). Full critique in
  `/notes/jev-typesafe-judgment-model-analysis.md`: the widest spread of
  source quality analyzed in this project to date, from pure hype recap to
  a genuinely reproduced mechanism (one source independently rebuilt Jev's
  restricted-softmax trick on an open model with real logits, verified by
  hand). Credited as well-reasoned: the mandatory code-side policy layer,
  never-use-this-as-authorization, confidence-gated thresholds set by what
  a wrong answer costs, and one source's own honestly-reported negative
  result (a Bitcoin buy/hold/sell test that "does not seem to be doing
  well"). Flagged as not holding up: TypeSafe's own benchmark graph scores
  against reference answers averaged from two competitor models it also
  competes with; marketing speed/cost multiples that are inconsistent
  across the sources' own talking points; and, the single most important
  finding, an independent calibration check in one source's own lab
  showing Jev's Expected Calibration Error (~0.164) is actually *worse*
  than Claude's (0.093) and Gemini's (0.094) on the same dataset — a
  quantified contradiction of the vendor's stated "RLCD" calibration
  training objective, reported by a user of the product, not a
  competitor. A LangChain comparison and an OpenRouter benchmark cited
  inside the sources are repeated as "a source cites this," not as
  verified fact, same discipline applied to every previously-flagged
  uncited claim in this project. **Built**: `/builds/jev-pattern-router/` —
  the real, generalizable architecture (Choice/Noul/Score primitives,
  probabilities restricted to the declared answer space, a margin-based
  confidence and probability-weighted Score verified by hand, a policy
  layer kept in plain code) applied as a cheap pre-router in front of
  `/builds/trading-jarvis/jarvis_orchestrator.py`'s real tool categories —
  not Jev's actual transformer, which is closed, and not a downloaded
  open model either: `curl -I https://huggingface.co` from this sandbox
  returned a real HTTP 403, checked directly as part of this build, same
  egress restriction already documented for Yahoo Finance/EODHD/FMP/
  Anthropic now extended to Hugging Face. Built instead on a real
  TF-IDF+logistic-regression classifier trained on ~40 labeled examples —
  a genuinely different, much weaker model, with the semantic-
  generalization gap against real Jev stated plainly rather than hidden.
  Found and documented a real instance of that gap while testing: a
  destructive request reworded just enough ("every position on file" vs.
  "all my positions") drops from 0.77 to 0.50 probability, under the
  policy's 0.70 escalation threshold — reported as an honest finding in
  both the test output and the README rather than hidden by only testing
  phrasings the classifier already handles well. Proven via a real test
  suite against a held-out test split never seen during training: category
  routing correct on 7/7 held-out examples, Score verified by hand to be
  the exact probability-weighted average, confidence verified by hand to
  be the exact top1-vs-top2 margin, Noul's missing confidence field
  checked structurally (not just unset), the destructive-escalation and
  low-confidence-escalation policy paths both exercised for real, and an
  honestly-caveated small-sample calibration check. All checks passed.
- **Deep analysis + new build from an uploaded Medium survey article,
  "AI Agents (07): Agentic Harness (Frameworks)"** (a five-layer taxonomy
  — Orchestration, Tools, RAG, Observability, Cloud/model ecosystem — for
  comparing agent frameworks like LangGraph, CrewAI, Mastra, Google ADK).
  Full critique in `/notes/agentic-harness-frameworks-analysis.md`: named
  as the weakest-evidence source analyzed in this project's run of deep
  analyses to date — no code beyond one illustrative snippet, no
  benchmark, no named source for any comparative claim about a specific
  framework, self-promotional banner and crypto tip-jar included. Flagged
  as imprecise: "OpenAI's SDK tightly integrates with the Azure-ChatGPT
  ecosystem" conflates OpenAI's own API with the separately-operated
  Azure OpenAI Service; the closing "ROOTS" mnemonic reorders its own
  five layers and appends a sixth ("Skills") the article explicitly
  didn't cover. Credited as genuinely useful: the taxonomy itself is a
  reasonable, checkable-in-principle structure, and the orchestration
  layer's checkpoint/pause/resume six-step list (persist state under a
  UUID, surface a partial result, find the run later by that UUID,
  reinstate it, resume, loop back to the same gate if still unapproved)
  is a concrete, correct, implementable spec — which the article calls
  non-negotiable. Checked directly rather than assumed: this project's
  own `jarvis_swamp_bridge.py` has nothing like it — its
  `approval_required=True` gate just raises `GovernanceError` and the run
  is gone, with no persistence anywhere in the repo (grepped for
  `checkpoint`/`sqlite3`/`resume`/`pause` project-wide to confirm). **Built**:
  `/builds/agent-checkpoint-layer/` — a real, durable SQLite-backed
  checkpoint/pause/resume layer implementing the article's six-step
  pattern literally, applied to a real multi-stage workflow shaped like
  `jarvis_swamp_bridge.py`'s own risk-gated step (built on the
  already-proven `prop_firm_sizing.py`/`prop_firm_position_sizing.py`,
  copied in unmodified). Two senses of "WAL" deliberately both real:
  SQLite's own write-ahead-log journal mode, and an app-level `wal` table
  logging every stage transition. Proven via genuine subprocess-boundary
  crash recovery, not a mocked one: a `--crash-after-stage` flag calls
  `os._exit(1)` right after a stage's result is computed but before its
  checkpoint write — exactly what a real `kill -9` does — and a resume
  from a fresh process recovers correctly. **Found and fixed a real bug
  while writing that test**: the "last completed stage" bookkeeping was
  computed once at the top of `advance()` from where a resume started,
  never updated as the loop progressed, so a resume completing more than
  one stage before the next pause point would record the wrong
  last-completed stage — harmless only because every stage here is
  side-effect-free and idempotent; in a workflow with a non-idempotent
  stage this would have silently re-run already-completed work, the
  exact failure a checkpoint layer exists to prevent. Fixed by tracking
  it as a loop-local variable instead. All 16 checks passed on the real
  run, including a WAL-ordering check that would catch a regression of
  that exact bug.
- **Deep analysis + new build from four uploaded Medium articles**: "Building
  an Enterprise AI Control Plane for Agentic AI" (ACP) and a three-part
  "Multi-Tenant LLM Systems" series. Full critique in
  `/notes/ai-control-plane-and-multitenant-llm-analysis.md`. The ACP piece
  describes (with no shown code or repo) a three-state policy model
  (`ALLOW`/`DENY`/`REQUIRES_APPROVAL`) with deterministic priority+effect-
  precedence resolution and payload-hash-bound human approval; credited
  as the best-stated idea across everything analyzed this round — "if the
  agent holds the provider credential and the tool credential, then the
  agent itself becomes the enforcement point. That is not really
  enforcement. It is advice" — while flagging that "I built an AI Control
  Plane" is itself unverified from the pasted text (no code, no repo,
  every diagram an inaccessible placeholder), same category as every
  other unverified "I built X" claim this project states rather than
  silently repeats. The multi-tenant series' Part 3 capacity-planning math
  (Little's Law worker sizing, a 3× burst/backlog/drain-time calculation,
  a token-cost invoice) was independently recomputed line by line and
  every number checks out — the first fully-verifiable arithmetic in this
  family of sources — while flagging one real imprecision: the burst
  section's "M/M/c-inspired" label describes a plain deterministic
  arrival-minus-capacity calculation with none of M/M/c's actual
  stochastic machinery, a hedge the author states but a label that still
  borrows more queueing-theory credibility than the math underneath it
  uses. **Built**: `/builds/policy-control-plane/` — the ACP article's
  policy-evaluation and payload-hash-bound-approval model, implemented
  for real against this project's own already-proven prop-firm-sizing
  tool, not a toy example: a safe, non-`eval()` nested-dict condition
  evaluator (deliberately stated as a security choice the article itself
  never addresses), a `PolicyEvaluator` reproducing the article's exact
  deterministic resolution rules, and a `governed_call`/
  `resume_governed_call` enforcement boundary where the real tool is
  provably unreachable on `DENY` or while `REQUIRES_APPROVAL` is pending
  (checked with a call counter, not just a status string). Extends,
  rather than duplicates, the HITL approval work built last round in
  `/builds/agent-checkpoint-layer/` with the one property that work
  didn't have: canonical-JSON+SHA-256 payload binding, closing a real,
  concrete attack this project hadn't previously defended against —
  approving one request's parameters and having a *different* request
  execute under that same approval. A concrete policy set mirrors the
  article's own worked example exactly in shape (`Billing Agent → Telco
  Billing MCP → createRefund → amount > 1000 → REQUIRES_APPROVAL →
  Finance` becomes `trading-jarvis → prop-firm-mcp-server →
  prop_firm_size_check → contracts > 5 → REQUIRES_APPROVAL → Risk Desk`,
  same operation, different governance outcome by parameter). Also fixed
  a real environment issue found at the very start of this round, unrelated
  to the build itself: this session's local git checkout had gone stale
  relative to `origin/claude/code-stack-analysis-awnea1` (a merge-commit
  divergence from an earlier round), silently hiding four already-shipped
  builds (`prop-firm-mcp-server`, `interface-lift-toolkit`,
  `jev-pattern-router`, `agent-checkpoint-layer`) from the local working
  tree; diagnosed via `git merge-base` before resetting, confirmed safe
  (clean working tree, no unique local commits) before `git reset --hard`
  to the real remote tip. All 25 checks passed on the real test run,
  including the payload-tamper rejection and replay-rejection properties.
- **Deep analysis + new build from four uploaded "Interactive Flowchart
  Generator" master prompts** (plus two unrelated PowerPoint-generator
  prompts and a research-copilot prompt uploaded in the same round,
  which turned out to be from the same external GitHub repo of
  unrelated reusable prompts — asked which one was wanted rather than
  guessing; user chose the flowchart generator). Full comparison in
  `/notes/flowchart-generator-analysis.md`: the four specs share one
  identical visual system (evidence they're iterations of one spec),
  but their actual feature surface ranges from a full editor
  (`final_interactive_flowchart_master_prompt.md`, direction-cycling +
  reconnect + delete + keyboard shortcuts) down to a bare add-node-and-
  export skeleton (`interactive_prompt_system.md`), and
  `Locked_HTML_Flowchart_Generator_Prompt.md` is a different
  architecture entirely (static export-only SVG, no JS state, no
  editing) rather than a variant. Flagged three real gaps shared by
  the three interactive specs: no drag/click/double-click
  disambiguation threshold specified; PNG export of `foreignObject`
  editable text is a known cross-browser rasterization problem that
  the specs only partially address (fixed for SVG export, never
  applied to PNG); and `connectionMode`/`reconnectMode` could collide
  with nothing specified to prevent it. **Built**:
  `/builds/flowchart-generator/` — the FINAL spec's feature set
  (named as the authoritative version), instantiated with one example
  diagram (a literature-review research workflow with a decision
  branch and a feedback loop) rather than left as an abstract
  template, since the specs' own deliverable is "shell stays fixed,
  only nodes/edges change." All three identified gaps fixed: a
  drag-distance threshold, `foreignObject` made strictly transient
  (committed and removed before every `render()`/export, which
  sidesteps the PNG bug architecturally instead of needing the specs'
  own proposed conversion step), and mutual-exclusion between
  connection/reconnect modes. Stage 1 (AI-generated reference image)
  not run — no image-generation tool in this sandbox, flagged rather
  than faked. Proven via Playwright end-to-end (served locally,
  screenshotted before/after per the screenshot-before-done rule,
  minimum two passes) driving the FINAL spec's own 27-step required
  functional test (add node → edit → drag → connect → cycle direction
  → relabel → reconnect → toggle orientation → delete → export).
  **Found and fixed two real layout bugs during that testing**, not
  present in the specs' prose: a feedback-loop edge label clipped off
  the fixed canvas edge (no label space was reserved in the routing
  corridor), and — more seriously — toggling to horizontal orientation
  produced heavily overlapping nodes, because the original layout
  spaced levels using a row-gap computed from canvas height regardless
  of orientation and never adjusted node width for the horizontal flow
  axis (columns ~170px apart, nodes still ~300–340px wide). Rewrote
  the flow-axis spacing to size each level from actual node extent
  with a single scale-down factor when the ideal spacing doesn't fit,
  matching the specs' own "scale rather than overlap or resize the
  canvas" layout-safety rule. Re-verified with a second screenshot
  pass (vertical, horizontal, and a mobile-width check) after the fix.
  `Locked_HTML_Flowchart_Generator_Prompt.md` deliberately not merged
  in — a different tool, not a variant of this one.
- **Flowchart generator extended with the three follow-ups suggested
  after it shipped** (all three picked, not a subset). (1)
  `/builds/flowchart-generator/examples/business-process.html` —
  same shell/engine as `index.html`, only nodes/edges/title differ,
  instantiated with a deliberately non-linear support-ticket-triage
  diagram (two decisions, a merge, a feedback loop, and a `group`-type
  node never exercised by the first example) to pressure-test the
  layout engine on a genuinely different topology than the one chain-
  with-one-detour shape already proven. Also switched this example to
  call `recalculateLayout()` before the first `render()`, so initial
  coordinates come from the auto-layout engine itself instead of
  hand-placed numbers — actually exercising the specs' "Automatic
  Initial Layout" requirement on load, not only via Toggle Orientation.
  Verified via DOM-geometry assertions (every node inside the 1200×900
  canvas, no significant overlap, both orientations) plus a screenshot
  pass — clean on the first try. (2)
  `/builds/flowchart-generator/from-notes.html` — a real
  `parseFlowchartText()` interpreter fulfilling the specs' own "paste
  rough notes, ASCII diagram, or process you want visualized" promise
  instead of leaving it as a hand-authored example: sequential lines
  auto-chain, `A -> B [label]` for explicit/labeled connections, a
  trailing `?` auto-types a decision, a `feedback:` prefix routes a
  line as a loop-back, and nodes with no incoming/outgoing edges
  auto-type start/end. Once generated, the result is a fully normal
  diagram on the same engine (draggable, editable, exportable).
  **Found and fixed a real bug while testing**: re-mentioning an
  already-defined node on its own bare line fabricated a spurious edge
  from wherever the parser's cursor happened to be, since the
  sequential auto-chain logic never checked whether the node was
  actually new — caught by an edge-count assertion (expected 8, got 9)
  against the interpreter's own worked example, not by inspection.
  Fixed so a bare line only auto-chains when it creates a genuinely new
  node. Verified against both that worked example and a fully freeform
  payment-flow input never seen during development, to prove it's a
  real interpreter rather than overfit to one canned case. (3) New,
  separate build `/builds/flowchart-static-export/` — the
  `Locked_HTML_Flowchart_Generator_Prompt.md` variant built literally
  rather than folded into the interactive editor, since it's a
  genuinely different architecture (hand-authored static SVG with
  semantic IDs like `node-research-question`/`connector-feedback-loop`
  matching the spec's own example naming, no JS state, no editing,
  toolbar with only Download SVG/PNG) — building it as a mode of the
  other shell would have meant either faking state nothing uses or
  faking a locked shell secretly hiding an editor. Same
  research-workflow content as `index.html` for direct comparison.
  Verified by serving locally and screenshotting (desktop + mobile,
  clean on the first pass) and by actually downloading both exports:
  the SVG retains every semantic ID and real text content with no
  `foreignObject` anywhere (nothing is ever editable in the browser
  here, so there's nothing transient to clean up before export), and
  the PNG is a real correctly-sized file.
- **Deep analysis of two uploaded newsletter posts (Week 19/20, a
  10-project open-source AI-infrastructure survey) plus a third,
  different-genre post by the same author/newsletter** ("What I
  Learned Building a GitHub Repo Manager as a Weekend Project") with
  its linked repo. Week 19/20 full write-up in
  `/notes/oss-ai-engineering-stack-week19-20-analysis.md`: the ten
  named projects (vLLM, cmux, Open WebUI, Dify, Hugging Face
  Transformers, Stable Diffusion WebUI, Harper, Colibrì, Ollama,
  AnythingLLM) are real and accurately described at the level the
  posts operate at, but several specific numeric claims (Transformers'
  "1M+ checkpoints," Harper's "1/50th of LanguageTool's memory," the
  named Colibrì model list) couldn't be checked against live READMEs
  from this sandbox — same no-network restriction as every other build
  here — and are reported as source-stated, not verified. **The
  weekend-project post got a different treatment**, because unlike the
  survey posts it makes one specific, checkable claim about the
  author's own work — so the linked repository
  (`vijaydeepak-vd/github-repo-manager`) was cloned and read in full
  rather than taken on the post's word. Full write-up in
  `/notes/github-repo-manager-weekend-project-analysis.md`: **a real,
  directly-verifiable discrepancy** — the post's narrative repeatedly
  centers on building "the interface," "the experience," and handling
  "loading states," but the actual repository is five standalone
  Node.js CLI scripts driven entirely by hand-edited `.txt` files, with
  no UI of any kind anywhere in it; the README itself (otherwise
  accurate and commendably candid about its own limits) never once
  uses the word "interface." Also found, by reading `4-delete-repos.js`
  directly rather than only the README's own stated limitations: the
  delete/transfer/visibility scripts have no dry-run or confirmation
  step (a limitation the README does state) *and* nothing stops a
  target list from accidentally matching the entire `all_repos.txt`
  inventory (a sharper version of that same gap the README doesn't
  name). **Built**: `/builds/github-repo-manager-safety-wrapper/` — a
  standalone companion (read-only access to the external repo, so no
  fork/PR was made or attempted) implementing the author's own stated
  "better error handling" / "safer bulk operations" roadmap items for
  real: `--dry-run`, typed per-repo-count confirmation phrases, a
  full-wipe guard that refuses a target list matching 100% of
  `all_repos.txt` unless `--force-full` is passed, and retry-with-
  backoff that only retries transient-looking errors (5xx, secondary
  rate limit, network resets) and fails fast on a definitive 404 —
  applied to the three irreversible/high-impact scripts (delete,
  transfer, visibility); archive/unarchive was deliberately left
  unwrapped since it's fully reversible, to keep the wrapper's scope
  matched to actual risk rather than wrapping everything reflexively.
  Proven for real, not flagged-as-untestable like most external-API
  builds here: a self-contained test suite against a mocked
  Octokit-shaped client needs no GitHub token, so it could be fully
  exercised in this sandbox (21/21 checks — full-wipe guard, retry/
  backoff, dry-run, confirmation match/mismatch, the guard firing
  *before* confirmation is ever prompted, continue-on-error with an
  accurate summary). Beyond the core module, all three CLI entry
  points were smoke-tested for real against temporary list files:
  `--dry-run` on each produced correct zero-network-call output, the
  full-wipe guard fired correctly end-to-end (exit code 1, no prompt
  reached) when a target list was made to match `all_repos.txt`
  exactly, and the real confirmation prompt was driven via piped stdin
  with a deliberately wrong answer, confirming it aborts before
  `@octokit/rest` ever constructs a request.
- **`/builds/github-repo-manager-safety-wrapper` extended with the
  three follow-ups requested after it shipped** (all three, "10X"'d
  per the explicit ask — not a minimal pass on any of them). (1)
  `archive-repos-safe.js` added, wired through the same `runSafely()`
  core as the other three, but deliberately *without* typed
  confirmation (`destructive: false`) since archiving is fully
  reversible unlike delete/transfer/visibility — `--dry-run` and the
  full-wipe guard still apply. (2) `--owner-repo` added — this needed a
  real refactor, not a bolt-on: `safety-core.js`'s entire internal
  model moved from bare repo-name strings to `{owner, repo, display}`
  entries (`parseEntries()`), with the full-wipe guard rewritten to
  normalize `all_repos.txt` (always single-owner, since that's all the
  original `1-fetch-repos.js` ever writes) against the *default* owner
  — so a cross-owner target list is correctly never mistaken for a
  full wipe of one account, while a list that spells out
  `GITHUB_USER/name` for every repo still trips the guard. All four
  entry scripts and the test suite updated to match (30/30 passing, up
  from 21, with new coverage for bare/explicit/mixed-owner parsing and
  both owner-repo full-wipe-guard cases). All four CLI entry points
  re-smoke-tested for real, including `--owner-repo --dry-run` against
  a mixed-owner list and the guard correctly firing/not-firing in both
  single- and cross-owner scenarios. (3) **A real, verified upstream
  patch**, not just a description of one: applied the same safety
  improvements directly to a local branch of the actual cloned
  `vijaydeepak-vd/github-repo-manager` (not this project's separate
  wrapper files), modifying the real `2-transfer-repos.js` through
  `5-change-archive-status.js` in place, updating `package.json`'s test
  script and the real `README.MD` throughout, then generated a patch
  with `git format-patch` — saved as
  `/builds/github-repo-manager-safety-wrapper/upstream-pr/0001-safer-bulk-operations.patch`
  alongside a full PR title/description
  (`upstream-pr/PR_DRAFT.md`). The patch wasn't just written and
  assumed good: applied to a **fresh** clone of the real repo (not the
  working copy it was authored against) with `git apply --check`, then
  `npm install && npm test` run there for real — 30/30 passing on a
  clean checkout, not just the one it was written in. Stated plainly
  rather than overstepping: this session has read-only access to that
  repo (no fork, no push), so the PR itself was not opened — the
  PR_DRAFT.md says so explicitly and gives the fork/apply/push steps to
  actually submit it, consistent with this project's standing rule of
  never taking a consequential external action (opening a PR on
  someone else's repo) without it being explicitly asked for, and even
  then, only producing what this session's actual access permits.
- **Deep analysis + new build from `morluto/rea`** ("REA: Reverse
  Engineer Anything" — an MCP server connecting AI agents to native
  disassemblers and a large built-in static-analysis toolkit, 300K+
  GitHub stars per its own README). Full write-up in
  `/notes/rea-reverse-engineer-anything-analysis.md`. First checked
  whether this is in-scope work at all: `DISCLAIMER.md` names a clear,
  specific lawful-use boundary (security research, malware analysis,
  CTFs, software you own or are authorized to examine) and explicitly
  refuses DRM/anti-cheat circumvention and unauthorized-access help —
  legitimate dual-use tooling, not evasion tooling. The README's
  self-reported "300,000 stars" was checked rather than repeated as
  fact (same discipline as every other uncited-claim flag in this
  project): no live GitHub API access to this unattached repo, so
  verified via web search instead — independent sources corroborate
  real, explosive growth (~30K on Oct 9 to ~234K by Oct 14), making
  ~300K by the clone date plausible, not inflated. One of those same
  sources also reports a real typosquat/impersonation risk around this
  specific repo (a fake copy bundling a suspicious Windows executable)
  — independent confirmation of the exact risk the README's own top
  banner already warns about. Picked one concrete, checkable claim from
  the README's capability table — Go-binary build-info extraction — and
  read the actual implementation in full
  (`src/go/GoBinaryImage.ts`/`GoModuleText.ts`) rather than trusting
  the one-line table description: genuinely careful engineering (real
  Go buildinfo magic/sentinels, varint decoding, Go's own quoted-string
  escape syntax for build settings, explicit anti-DoS budgets, zero-
  fill-span handling) — the most rigorously-engineered source code read
  in this project's run of analyses to date, credited plainly as such.
  **Built**: `/builds/go-buildinfo-extractor/` — not a clone of REA
  (3,235 files, native disassembler integrations, far out of
  proportion to what this sandbox can verify), but a standalone,
  dependency-free Python reimplementation of that one capability,
  built from understanding the format (confirmed via REA's code as a
  correctness reference, nothing copied) rather than guessing. ELF and
  PE both fully implemented; Mach-O explicitly cut, stated plainly, for
  a concrete reason — no way to produce or verify a real Mach-O binary
  in this Linux sandbox (confirmed by actually cross-compiling one and
  showing the tool rejects it cleanly rather than crashing). The
  pointer-encoding string path (vs. the modern "inline" encoding) is
  implemented but flagged as unverified — no Go toolchain old enough
  here to produce a binary that exercises it. Proven against real
  compiled binaries, not synthetic byte strings: a genuine two-module
  Go project (a main module with a `replace`-directive local
  dependency, so both the `dep` and `=>` replacement lines are
  exercised for real) built with the system Go 1.24.7 toolchain, cross-
  checked field-by-field against `go version -m`'s own ground-truth
  output — exact match on the first run, for both the native ELF binary
  and a cross-compiled Windows PE binary (confirming the PE section-
  table/RVA-mapping and `ImageBase` normalization are correct without
  ever needing Windows). **Found and fixed a real bug while testing**:
  a deliberately corrupted byte inside the version string leaked a raw
  `UnicodeDecodeError` instead of the tool's own typed error — caught
  by a byte-flip test, not by inspection. Fixed by routing every UTF-8
  decode through a wrapper that converts it to the typed error. Then
  stress-tested the fix with a 2,000-iteration deterministic fuzz pass
  (1–20 random byte flips per trial, both ELF and PE fixtures): zero
  uncaught exceptions of any kind, now a permanent regression test. The
  full suite (11 tests, including the negative case — a plain `gcc`-
  compiled C binary correctly reports no Go build info rather than
  crashing or false-matching) builds its own fixtures at test time via
  the real toolchain rather than shipping committed binaries, and
  skips cleanly rather than failing when `go`/`gcc` aren't on `PATH`.
- **`/builds/go-buildinfo-extractor` extended with the three follow-ups
  requested after it shipped** (all three, no subset). (1) **New Rust
  sibling extractor, `rust_cargo_auditable.py`** — REA documents Rust
  `.dep-v0` cargo-auditable dependency metadata as a sibling static-
  parsing capability to the Go build-info one, so this round read
  REA's real Rust implementation (`RustAuditableReader.ts`,
  `RustBinaryImage.ts`, `rustBinary.ts`) in full the same way the Go
  reader was read last round, then wrote a fresh, independent Python
  implementation: ELF/PE `.dep-v0` section location (a new named-
  section-header parser, distinct from Go's program-header/PT_LOAD
  approach), zlib inflate with a resource-budget cap, package/
  dependency-graph parsing, and cycle detection via a real, iterative
  (non-recursive) Tarjan's SCC algorithm — a different algorithm than
  REA's own DFS-postorder approach, same correctness property,
  verified against hand-built graphs (crates.io itself forbids real
  dependency cycles, so no real binary could exercise this path).
  Proven against real binaries, not synthetic bytes: installed
  `cargo-auditable` for real, built a genuine two-crate project (a
  `crates.io` dependency, `itoa`, plus a local `path` dependency, so
  both `source` kinds and a real two-edge dependency graph are
  exercised), and cross-checked the extractor's ELF output against an
  **independent** ground-truth decode — a from-scratch section-header
  walk plus a direct `zlib.decompress()`, written separately from the
  extractor's own parser so a shared bug wouldn't be invisible to the
  check. **Found and fixed a real bug while building the PE fixture**:
  cross-compiling the same project to `x86_64-pc-windows-gnu` (installed
  `gcc-mingw-w64-x86-64` + the Rust target for this) failed with
  "dependency section has bytes after the zlib stream" — PE's
  `SizeOfRawData` is padded up to `FileAlignment` (512 bytes observed),
  while `VirtualSize` (137 bytes, matching the ELF build's section size
  exactly) is the real unpadded length; reading the padded size pulled
  in 375 zero bytes past the real zlib stream. Fixed by taking
  `min(VirtualSize, SizeOfRawData)` as the section's true length, which
  is a different, PE-specific bug from last round's Go PE pointer-
  encoding one (same binary-format-padding family of mistake, caught
  the same way: by actually cross-compiling and running the real
  output rather than assuming the format was simple enough not to
  need it). Negative cases (plain `cargo build` with no `auditable`, a
  plain `gcc` C binary) and malformed-input handling (truncated
  section, corrupted zlib stream, a 2,000-iteration fuzz pass — same
  discipline as the Go suite's fuzz test) round out a 15/15-passing
  suite, run alongside the existing 13 Go tests with no interference.
  (2) **Got access to an older Go toolchain and closed the pointer-
  encoding test gap**: `GOTOOLCHAIN=go1.17.13` (Go's own module-proxy-
  based toolchain fetch, which this sandbox's egress proxy allows even
  though direct `go.dev` downloads return 403) built real Go 1.13–1.17-
  era ELF and PE binaries for the first time in this project. Running
  them through the extractor **found a second real bug, in
  `go_buildinfo.py` itself**: the PE pointer-resolution path normalized
  the *outer* version/module pointers against `ImageBase` but not the
  *inner* string-data pointer resolved one indirection further in, so
  every PE pointer-encoded binary failed with "address ... is not
  mapped by any segment." Fixed architecturally rather than patched at
  the call site — moved the `ImageBase` subtraction into
  `_AddressMapper` itself (now takes an `image_base` constructor
  argument, applied to every address lookup at any indirection depth)
  so no call site has to remember to normalize manually; `_parse_pe()`
  updated to pass its computed `image_base` in, and the now-dead manual
  normalization lines in `read_go_buildinfo()` were removed. Added two
  new permanent regression tests (`TestPointerEncoding`, ELF and PE,
  both built via the old toolchain and checked against `go version -m`
  ground truth) — Go suite is now 13/13, up from 11, with zero
  regression to the inline-encoding paths. (3) **Both extractors wired
  into `/builds/interface-lift-toolkit/`'s tool registry** as two new
  `effect="local"` typed tools — `go_buildinfo_check` and
  `rust_cargo_auditable_check` in a new `binary_metadata_tools.py`,
  with both underlying modules copied in unmodified (same convention
  `prop_firm_*.py` already follows there). Deliberate `checks`-
  semantics design, not copied from the prop-firm tools uncritically:
  both readers document that a clean `None`/no-section result is a
  normal, successful outcome (not Go / not cargo-auditable), not a tool
  failure, so `ok` means "did the read complete," and whether the
  binary turned out to carry that metadata is a plain output field,
  never folded into `checks` — only a missing file or the module's own
  typed error (genuinely malformed input) sets `ok=False`. Proven two
  ways, extending both of the toolkit's existing test files rather than
  adding a third: `test_toolkit.py` gained schema-derivation checks, a
  missing-file usage-error check, and real-binary checks for both tools
  (building a fresh Go binary and a fresh cargo-auditable Rust binary
  at test time, cross-checked against a **direct call** to
  `read_go_buildinfo()`/`read_cargo_auditable()` — same discipline as
  every other tool in that suite) — including two negative-case checks
  this round caught and corrected mid-build: a first draft tested the
  "non-Go" case with a plain text file, which actually hits
  `go_buildinfo.py`'s own *different*, stricter "unsupported container"
  error path (neither ELF nor PE) rather than its "no header found"
  path — fixed by testing both cases for real (a genuine non-Go `gcc`
  ELF binary for the correct negative, a plain text file for the
  unsupported-container error) instead of only the one that happened
  to work. `test_agent_loop.py` gained a third scripted turn
  (`go_buildinfo_check` against a real Go binary dispatched through the
  mocked-Anthropic `run_agent` loop, same mocking convention as every
  other dispatch-loop test here) proving the real reader's output flows
  back through the tool-use loop, not a stub. Both README's updated —
  `go-buildinfo-extractor`'s with the Rust extractor, both bug writeups,
  and the toolkit cross-reference; `interface-lift-toolkit`'s with the
  new tool category, its checks semantics, and refreshed real test
  output.
- **Deep-dive (no analysis file written — a 3-article Medium/Claude-Code
  bundle, "7 claude skills that print money," "6 Claude Skills to Reduce
  Token Usage," "9 Claude Code Mods You NEED to Install Right Now") +
  seven new builds**: asked which of the bundle's scope (analysis of all
  three vs. building a mod vs. building a skill) was wanted rather than
  guessing; the answer (which arrived as a follow-up message after an
  `AskUserQuestion` round the user didn't directly answer) asked for both
  — three of the named mods built "for real" via the `plugin-authoring`
  skill, and four of the seven "skills that print money" ideas
  adapted into this repo, same move as Build Brain/Agent Readiness
  Scorecard. Token-usage-reduction article not acted on this round (no
  build asked for from it).
  - **Three real Claude Code mods, `/builds/claude-code-mods/`**
    (`blast-radius`, `cache-keeper`, `collision-guard`), built via the
    `plugin-authoring` skill after reading its full reference (hook
    types, `ui.render`, `$.state` contracts, the test kit). Pure
    detection/arithmetic logic kept in separate, `$`-free modules
    specifically so it could be unit-tested with `claude plugin test`
    with no engine mocking — 34/34 tests passing across the three (18 +
    8 + 8). `blast-radius` gates destructive `Bash` commands (`rm -rf`,
    `git push --force`, `git reset --hard`, `git clean -f`,
    `git branch -D`, `git checkout --`/`git restore --worktree`) behind
    a real `$.ui.ask` Proceed/Cancel dialog — confirmed `$` calls don't
    count against a hook's own execution budget, so the wait is
    genuinely unbounded on a human, not a race against a timeout.
    **Found and fixed a real bug via its own test suite**: an early
    `git branch -D` rule ran case-insensitively, so it false-flagged the
    safe, merged-only `git branch -d` as destructive — caught by a
    dedicated negative test, fixed by making the `-D`-vs-`-d` check
    case-sensitive while keeping `git branch` itself matched loosely.
    `cache-keeper` shows a live prompt-cache countdown, context
    percent/tokens, rate-limit usage, and session cost above the prompt
    (`$.session.usage()` for everything live; the cache window itself
    has no documented API, so it's stated plainly as a configurable
    60-minute estimate reset on each prompt, not a measurement) plus a
    "Handoff & Compact" button calling the real `$.session.compact()`.
    **Found and fixed a second real bug, this one in the plugin-
    authoring mechanism itself, not the mod's logic**: `claude plugin
    validate` kept rejecting a `$.state` contract that structurally
    matched the skill's own reference examples; isolated by validating
    the skill's own unmodified `pane.tsx`/`pane-state.d.ts` example pair
    as a control (it passed) and diffing byte-for-byte against it — the
    difference was declaring the `PluginState` entry as a reference to a
    separately-named type alias instead of an inline object-type
    literal, which the validator's static check doesn't resolve. Fixed
    by keeping the named export for reuse while the `PluginState`
    interface itself repeats the shape inline, documented with a comment
    so the next mod in this project doesn't hit the same wall blind.
    `collision-guard` warns via `$.ui.ask` before `Edit`/`Write`/
    `NotebookEdit` when another session wrote the same file inside a
    configurable window, using `$.store` (confirmed from the API docs to
    be shared across sessions for the same plugin, not per-session) to
    record `{sessionId, at}` per file path. Cut, stated plainly: the
    article's "move to a worktree" and free-text options, and the
    bidirectional "what's the other session doing" banner — each a
    materially bigger feature than the one collision-warning mechanism
    this mod set out to build. `claude plugin validate` passes cleanly
    on all three. Honestly flagged as **not** verified: none of the
    three has been exercised inside a real hot-reloaded session with an
    actual person answering `$.ui.ask`, or against a genuine second
    concurrent session colliding on a file — this sandbox session can't
    arrange either for itself. The live, loadable copy of each mod stays
    in this session's required `/root/.claude/dev-mods/<session>/`
    location per the skill's own instructions; the copies under
    `/builds/claude-code-mods/` are the project's documented record, not
    what a session actually loads.
  - **`/builds/humanizer/`** — a real, dependency-free Python detector
    for AI-writing tells (14 rules across throat-clearing, rhetorical
    tics, hedging, and buzzwords), filling a real gap `design-rules.md`'s
    existing "Generic-AI tells to avoid" section doesn't cover (that
    section is visual tells; nothing in this project checked prose tells
    before this). 15/15 tests passing, with the test that actually
    matters being discrimination, not isolated regex matches: a real
    AI-sounding paragraph scores 11 findings across 4 categories, a real
    plain paragraph (an engineer describing an actual bug fix) scores
    exactly 0. **Found and fixed a real bug while writing the
    discrimination test**: the `stacked-intensifier` rule only matched
    two intensifiers separated by bare whitespace, missing the more
    common real phrasing with a comma between them ("truly, really") —
    caught against realistic text, not a synthetic edge case. A CLI
    (`--max-per-1000-words` as a real pass/fail gate, `--json`) and a
    matching skill (`.claude/skills/humanizer`) make it a real check
    other skills actually run, not just a standalone script — wired into
    `proposal-generator`, `launch-kit-writer`, `sales-page-engine`, and
    `launch-pad`'s own "before calling it done" step.
  - **`/builds/programmatic-seo-builder/`** — a real page generator
    proving the article's own one named hard rule ("strict about one
    thing: no thin pages") as an actual pre-write check
    (`pseo_guard.py`: minimum word count, minimum unique-fact count, and
    a separate duplicate-facts check two pages could both pass word
    count while still saying the same thing), not a guideline. Generates
    against real data already proven elsewhere in this project —
    `PropFirmAccount`/`TPT_TIERS`/`CONTRACT_SPECS` from
    `/builds/prop-firm-sizing/`, copied in unmodified — rather than a
    synthetic placeholder dataset: 5 tiers × 6 contracts = 30 real pages,
    each answering a genuinely distinct long-tail question ("Can I trade
    {symbol} on a ${tier} TPT account?") with real computed numbers, plus
    5 tier-index and 6 symbol-index pages with real internal linking (not
    just links back to one index). 10/10 tests passing, including a real
    regex pass over one page's actual generated HTML asserting every
    `href` it contains points at a file that was genuinely written to
    disk. Screenshot-verified per the project's screenshot-before-done
    rule (served locally, Playwright/Chromium, a sample page and the
    index, clean on the first pass) — styled with the already-locked
    RUTHLESS TRADING GOLD palette since the dataset is real data from
    that portfolio, not an invented template brand. Schema.org markup
    and live rank-tracking explicitly cut and stated why (no schema-
    generation skill exists yet to pair it with; no live search-engine
    access from this sandbox to check rankings either way).
  - **`/builds/proposal-generator/`** (skill +
    `.claude/skills/proposal-generator`) and **`/builds/launch-kit-writer/`**
    (skill + `.claude/skills/launch-kit-writer`, explicitly extending
    `launch-pad` rather than duplicating it — point to launch-pad's own
    long-form email instead of writing a second one) — both built as
    skill-plus-worked-example pairs (matching `sales-page-engine`/
    `launch-pad`'s own established shape, since the output is bespoke
    prose per client/launch, not a deterministic transform like the
    pSEO builder). The proposal worked example uses synthetic discovery-
    call notes (explicitly marked, no real client) and states plainly,
    inside the generated proposal itself, that its three pricing tiers
    are anchored to the one real number the synthetic client gave rather
    than an invented agency rate, per the skill's own rule to never
    fabricate a number not in the source material. The launch-kit worked
    example extends Recovery Desk's real, already-shipped `launch-pad`
    output (`/builds/recovery-desk/launch/ad-copy.md`,
    `business-brain.md`'s sourced stats/quotes) into five more
    platform-native assets (Product Hunt listing, Show HN post, a
    7-tweet X thread, three distinct per-subreddit Reddit replies, a
    Medium-style article) with nothing reinvented — same pricing, same
    sourced complaint quotes, same reply-in-thread-never-cold-post
    distribution rule already established. Both worked examples run for
    real through both `design-rules.md`'s don't-say-list grep and the
    new Humanizer tool, not just presented as checked. **A real,
    instructive false positive found while checking the launch kit**: a
    naive grep of the whole file hit the don't-say list 13 times — all
    inside the file's own "what was checked" section, which spells out
    the banned-word list by name to document the check, the same
    false-positive class already documented for Recovery Desk's
    "diagnose"/"treat" hits, now from quoting the rule itself rather
    than negated medical language; confirmed by line number, not
    assumed away, and the actual asset content underneath is clean.
- **Deep analysis + new build from a second uploaded bundle: three
  separate YouTube transcripts about building a WordPress site with
  Claude** ("Build a WordPress Website using Claude in 2026 (FULL
  GUIDE)," "(REALLY) Build a WordPress Website with Claude in 2026,"
  "How I Built INSANE WordPress Websites In 20 Minutes") — three
  different creators teaching the same general technique (design with
  Claude, land it in WordPress via a bridge plugin called Novamira/
  "Nova Mirror," finish in Elementor), not one guide. Full comparison in
  `/notes/wordpress-claude-elementor-tutorials-analysis.md`: credited
  what's consistent and load-bearing across all three independently
  (build with real Elementor elements, never a separate stylesheet or
  raw HTML widgets, or the page looks editable but isn't — Matt's
  transcript names this "the trap in this whole method," Daryl's
  documents hitting the milder version of the same failure, the third
  video's own 6.5–7/10 self-rating for "fully editable" output reflects
  the same editability-vs-fidelity tradeoff structurally). Flagged real,
  direct contradictions between sources that aren't just style
  differences: the Atomic Editor setting (Matt says confirm it's on,
  Daryl says deactivate it — likely two different points in Elementor's
  own rollout of that feature, neither video aware of the other);
  header/footer tooling (Astra's built-in builder vs. a separate XPro
  plugin, each creator's own stated reason for their choice directly
  contradicting the other's); and a hosting-plan recommendation (Matt:
  the cheapest plan is enough; Daryl: the pricier one, for reasons that
  don't actually apply to the single-site beginner the video is nominally
  teaching). Also flagged the one claim repeated as fact rather than
  checked (WordPress "40% of the internet," sourced to the video, not
  independently verified — no live web access to check it as of the
  video's own recording date). First deep-analysis round where none of
  three sources could be tested at all, not even against synthetic
  data — this sandbox has no WordPress, Hostinger, Claude Design, or
  Novamira access, stated plainly as a stronger version of the usual
  no-live-API-access caveat. **Built**: `/builds/voice-extractor/` — not
  a WordPress tool (nothing in the bundle beyond one technique is
  buildable without a live WordPress install), but the one genuinely
  extractable, testable technique in it: the third video's tone.md/
  humor.md idea (paste a real writing sample, have Claude "decode" it
  into a reusable style guide), built as the measurable half of that —
  real counted signals (sentence length, contraction rate, first-person
  rate, em-dash/question/exclamation rates, sentence-starting-
  conjunction rate, common openers), not a vague prescriptive guide, and
  a real scorer that checks a new draft against a saved profile.
  Deliberately complements last round's `/builds/humanizer/`: Humanizer
  strips AI tells out, this puts a specific real voice back in, and the
  two skills now cross-reference each other. **A real design flaw found
  and fixed via its own discrimination test, not assumed away**: the
  first scoring version used relative difference per metric, which
  passed a read-through but made a draft deliberately written to match
  the reference voice score *lower* (0.526) than a deliberately generic
  corporate draft (0.753) — the opposite of the tool's purpose. Found by
  printing the actual extracted numbers rather than guessing: a
  rare-event metric near zero in the reference (first-person use, em
  dashes) turned any nonzero draft value into a near-maximal penalty
  under relative difference, which doesn't track real stylistic
  distance on short samples. Fixed by switching to fixed, declared
  absolute tolerances per metric. In the same debugging pass, the
  hand-written "matching" test draft itself turned out not to
  statistically match the reference as well as it read by eye (shorter
  sentences, much lower first-person rate than intended) — caught by
  printing the real numbers, not by trusting the draft looked right, and
  rewritten to actually hit the reference's measured figures. Re-verified
  after both fixes: matching draft scores 0.873, generic draft 0.61, with
  correct, specific suggestions naming exactly what differs. 14/14 tests
  passing, including a real CLI round-trip test (`extract` then `score`
  as real subprocesses against real files in a temp directory, not
  in-memory calls) proving the saved JSON profile survives a real file
  round trip.
- **Deep analysis + new build from a single uploaded transcript**
  ("Build $10,000 Websites using Claude Code (Ultimate Guide)"), plus
  two GitHub repos the video names and links directly — read in full
  rather than trusted on the video's word, same discipline as reading
  REA's actual source instead of its README table: `anthropics/skills/
  skills/frontend-design` and `nextlevelbuilder/ui-ux-pro-max-skill`.
  Full write-up in `/notes/10k-website-claude-code-analysis.md`.
  Credited as genuinely useful: the video's 8-pillar checklist (point
  of view, typography, colour, hierarchy, imagery, motion, mobile, "the
  invisible stuff"), and its own mid-build move of grading the result
  against that checklist before polishing further — the same "turn a
  checklist into an actual self-check" idea already credited to the
  Factory.ai Autonomy Maturity Model paper. Two concrete claims checked
  and found wrong, not repeated as fact: (1) Frontend Design "bans the
  most overused fonts on the internet" — false; the entire skill is one
  file with no banned-fonts list at all, and what it actually bans are
  five *visual patterns* (cream+terracotta #F4F1EA/#D97757 — named as
  Anthropic's own UI accent — near-black+acid-green, broadsheet
  hairlines, the SaaS-card kit, ALL-CAPS/middle-dot/arrow-suffixed
  "template chrome"), never a specific typeface; (2) UI/UX Pro Max
  "ships with 57 UI styles, 95 colour palettes and 56 font pairings" —
  checked by direct CSV row count against the real data files, not the
  video's on-screen caption: real counts are 88 style rows (79
  searchable), 192 palettes, 74 font pairings, all higher than claimed,
  cross-confirmed against the package's own `catalog-summary.json`.
  Most likely explanation stated plainly rather than invented: real,
  active CI automation in that repo (`bump-versions.yml`,
  `refresh-catalogs.yml`) actively grows the catalog, so version drift
  is plausible — but the clone here is shallow (`--depth 1`, no tag
  history), so the video-era historical counts couldn't be
  reconstructed from this sandbox, and that limitation is stated rather
  than guessed around. One claim that *did* check out: the installer
  phrase "Install this plugin using NPM" matches the repo's real,
  documented `npm install -g ui-ux-pro-max-cli` distribution path.
  **Built**: `/builds/ten-k-website-grader/` — the 8-pillar checklist
  as a real, static-file-checkable grader, same move as
  `/builds/agent-readiness-scorecard/`: honest about which pillars a
  machine can actually check. Point of view is always reported
  not-assessable (it's about the brief's intent, not observable from
  files); hierarchy, imagery, and motion get explicit partial/heuristic
  proxies (type-scale spread; real-media-and-alt-text presence;
  transition/animation presence plus `prefers-reduced-motion` support)
  with the tool itself stating in its own output what each proxy can't
  see (e.g., whether imagery actually looks premium vs. generic stock).
  Typography, colour, mobile, and "invisible stuff" (broken local
  references, duplicate ids, oversized images) get full checks, with
  informational (non-failing) flags for named AI-site tells: `Inter`
  usage (the video's own specific callout) and default Tailwind/
  Bootstrap-blue hexes (`design-rules.md`'s existing rule, reused
  rather than reinvented). Proven via a real discrimination test
  (`test_grader.py`, 15/15 passing): a deliberately well-built fixture
  site scores 100%, a deliberately generic AI-default-shaped fixture
  (Inter-only, one flat font size, default blue, missing alt text, a
  broken file reference, a duplicate id, no viewport meta, no motion)
  scores 14%, with the specific failing pillars and flags matching
  exactly what was built wrong into it on purpose. **Also run for real
  against this project's own already-shipped, already screenshot-
  verified pages** (`/builds/recovery-desk/sales-page/` and
  `/builds/prop-firm-dashboard/sales-page/`, not just synthetic
  fixtures) — both scored 71% on first run, and that real run **found
  a genuine, previously-undocumented accessibility gap**: Recovery
  Desk's sales page has a hover `transition` with no
  `prefers-reduced-motion` guard anywhere in the file, a real violation
  of `design-rules.md`'s own already-stated motion rule. Confirmed by
  reading the actual CSS before fixing it, fixed with a 3-line
  `@media (prefers-reduced-motion: reduce)` block, and re-verified —
  that page moved from 71% to 86%, motion pillar now passing. Both
  pages still honestly fail `imagery` (neither has any actual
  `<img>`/`<video>` tag — CSS-only hero treatments, consistent with
  this project's standing no-image-generation-tool-in-sandbox note) and
  `prop-firm-dashboard`'s page separately fails `colour` at 11 distinct
  literals against the grader's 3–10 heuristic — deliberately **not**
  "fixed" by trimming that page's real RUTHLESS TRADING GOLD palette
  just to satisfy the tool, and the README states this as a named,
  honest limitation of the colour heuristic rather than a bug to chase.
- **Deep analysis + new build from a second, distinct "$10K website" bundle**:
  the "10k-websites" Claude Skill (`SKILL.md` + five `references/` files —
  `deploy.md`, `design-package.md`, `ffmpeg-recipes.md`, `prompt-laws.md`,
  `scrub-pipeline.md`) and its companion tutorial, "How to Build $10K
  Websites in Minutes (Claude AI)" — separate from the earlier "Build
  $10,000 Websites using Claude Code" round, same positioning, completely
  different architecture (a scroll-scrubbed AI-generated hero video via
  Higgsfield + a dedicated Hostinger MCP connector, not a static-skill-
  driven page). Full write-up in
  `/notes/10k-websites-higgsfield-skill-analysis.md`. Flagged plainly,
  straight from the file's own text: `SKILL.md` and `deploy.md` both
  hard-code Higgsfield and Hostinger partner/affiliate links directly
  into the instructions an installing session would run — stated
  honestly by the skill itself ("say so plainly"), but a materially
  different category from Anthropic's own unaffiliated `frontend-design`
  skill analyzed in the earlier round. Credited as the most rigorously
  engineered, most independently verifiable source analyzed in this
  project's whole run to date — two concrete technical claims checked by
  actually executing them, not just read: the drive loop's claimed
  frame-rate-independent lerp formula (verified via a Node simulation:
  50% convergence in the same 66.7ms at 30/60/120fps alike, vs. a
  genuine 2x discrepancy for the naive alternative the file warns
  against) and the `-g 8` scrub-encode keyframe interval (verified via
  `ffprobe` frame-by-frame against a real ffmpeg-encoded test clip,
  landing exactly on schedule). Both checks came back correct. Separately
  unverifiable from this sandbox: Higgsfield/Hostinger live API access
  (same restriction as every other paid-connector build here) and the
  new video's Claude-plan-tier pricing claims (Fable needing Max/credits,
  Opus included on Pro) — reported as source-stated. **Built**:
  `/builds/scroll-scrub-hero/` — a real, standalone implementation of
  `scrub-pipeline.md`'s engineering standard (the single hardest, most
  load-bearing piece of the whole skill, and the one piece fully
  testable without either paid service): the streamed-Blob loader with
  a progress ring, the frame-rate-independent lerp drive loop, gated
  seeks, delta-gated DOM writes, the vh-paced caption-band system with
  word-level entrances, the four-layer legibility scrim system, the
  five static-hero gates, live reduced-motion handling in both
  directions, and the one press-and-hold interactive moment — built
  against a synthetic ffmpeg-generated placeholder hero video (no
  Higgsfield access; stated plainly, and, per the spec's own advice that
  abstract worlds generate most reliably, the substitute happens to land
  in the same visual category the spec itself recommends), with the
  real documented ffmpeg asset pipeline (`-g 8 -crf 18 -movflags
  +faststart` scrub encode, poster/ending-frame extraction) run for
  real producing a genuine H.264 asset matching the spec exactly.
  **Found and fixed four real bugs by actually running this in a
  browser, not by reading the code**: (1) a type-less `Blob` fails
  Chromium's demuxer with `DEMUXER_ERROR_NO_SUPPORTED_STREAMS` — and the
  reference spec's own sample code has this exact same bug
  (`new Blob(chunks)` with no MIME type), fixed here with an explicit
  `{ type: "video/mp4" }`; (2) this sandbox's pre-installed open-source
  Chromium build has zero H.264 decoding support at all
  (`canPlayType` returns `""`), confirmed directly rather than assumed,
  worked around with a test-only `VIDEO_URL` override pointing the
  Playwright suite at a VP9 re-encode of the identical footage so the
  real engine code path still gets exercised in a real browser, while
  production markup stays H.264, the universally-compatible real choice;
  (3) a first pass reused the three scroll bands directly as the
  static-hero fallback, which both clipped/ghosted inside the still-
  sticky `.hero-stage` and violated `design-package.md`'s own explicit
  spec (section 5: the static hero gets one composed headline/subline/
  CTA, "with no journey behind them," never the scroll bands) — caught
  by a real mobile screenshot showing footer text ghosting into the
  hero, the same Chromium full-page-stitched-screenshot bug already
  documented in this project's `/builds/prop-firm-dashboard` work, fixed
  at the root (a dedicated `.static-hero` block, bands hidden and the
  stage un-stuck once a gate matches) with scroll-segmented screenshots
  used going forward as a second safeguard; (4) the band-one load-ramp
  failure the spec itself names and warns against ("the hero opens on
  footage with no words until the user scrolls") was present in the
  first implementation and caught directly by this build's own
  Playwright test (band 0 measured `opacity: 0` at scroll top) before
  being fixed per the documented `k = max(scrollK, loadK)` pattern.
  25/25 checks passed on the real run across two suites: `test_pure.mjs`
  (6 — the lerp/smoothstep math, and a real regex-based check that the
  five static-hero gate strings are character-for-character identical
  between the CSS media query and the JS `matchMedia` array, the exact
  failure mode the spec calls out) and `test_playwright.py` (19 — real
  Chromium scrubbing, the spec's own flick-test harness replicated
  exactly at 120/240/360px steps, reduced motion toggled live in both
  directions, the complete-without-video fallback, the press-and-hold
  interaction's build/ease-back/completion states, and screenshots at
  desktop and phone widths). Deliberately not built this round: the
  worst-frame canvas-pixel legibility audit script (checked by eye
  against real screenshots instead), Tier 2/3 chaining and the Creative
  Director's Loop, and the actual Higgsfield/Hostinger deploy flow —
  all either out of scope for a demo with no real brief or blocked by
  the same live-paid-API restriction as every other build in this
  project.
- **Analysis-only round: Week 21 of the same newsletter series already
  analyzed twice** ("5 Open-Source GitHub Repositories Every Developer
  Should Know in 2026" — Docusaurus, n8n, Mattermost, AutoGPT, LocalAI).
  Full write-up in `/notes/oss-ai-engineering-stack-week21-analysis.md`.
  Unlike Week 19/20 (no live network access, every number reported as
  source-stated), this round actually cloned all five named repos
  (`n8n-io/n8n`, `mattermost/mattermost`, `significant-gravitas/autogpt`,
  then `facebook/docusaurus` and `mudler/localai` after the user
  followed up pasting all five clone URLs directly) via this session's
  now-confirmed anonymous git-read access and checked the post's most
  specific, decision-relevant claims against the real files rather than
  the post's description of them: n8n's Sustainable
  Use License + Enterprise License split (`LICENSE.md`/`LICENSE_EE.md`,
  exact match), Mattermost's Go+React/open-core/PostgreSQL-only
  architecture (`server/go.mod`, `webapp/`, `LICENSE.txt` +
  `LICENSE.enterprise`, `server/config/database.go` referencing
  PostgreSQL only — no MySQL driver code at all in the current repo,
  more precise than it reads at a glance), and AutoGPT's split license
  (root `LICENSE`: Polyform Shield inside `autogpt_platform/`, MIT
  everywhere else — verbatim match). Then, once the user supplied all
  five URLs, the remaining two were checked too: Docusaurus's exact
  `npm init docusaurus@latest` scaffold command (present verbatim in
  the real README), its React dependency, and real i18n test fixtures
  for German/French/Chinese locales (not just a README claim); and
  LocalAI's own README stating almost word for word what the post
  claims — "Drop-in API compatibility: OpenAI, Anthropic, and
  ElevenLabs APIs across every backend" — with Anthropic support dated
  to LocalAI 3.10.0 (January 2026) in the same file's own changelog, a
  genuinely recent addition the post reflects accurately rather than a
  stale assumption, plus a real pluggable `backend/` directory
  (separate go/python/rust/cpp implementations) matching the claimed
  architecture. All five repos' specific, checkable claims — two
  license splits, one open-core/architecture claim, one scaffold
  command, one localization claim, one API-compatibility claim — now
  checked out exactly, not just three.
  One real, non-accusatory discrepancy found and stated rather than
  glossed over: n8n's README really does say "1500+ integrations" in
  three places (faithfully repeated by the post, not invented), but a
  direct count of the actual shipped core package
  (`packages/nodes-base/nodes`) found only 308 node directories and 563
  total `.node.ts` files — a real gap, most likely a counting-
  methodology difference (per-operation counting, or a separate
  npm-distributed community-node ecosystem not bundled in this repo)
  rather than an inflated figure, reported as unreconciled rather than
  assumed either way. AutoGPT's own platform-feature descriptions
  (AutoPilot, Agents, Marketplace, Build) were read as plausible and
  internally consistent with the repo's real top-level structure but
  not independently run or clicked through. **No build this round** —
  same call as Week 19/20: a survey
  of five already-mature, independently famous, actively-maintained
  projects has no generalizable gap or technique to extract, unlike the
  same series' "weekend project" post, which made one specific,
  previously-unverified claim about the author's own code and got a
  real build (`/builds/github-repo-manager-safety-wrapper/`) because of
  it.
- **First round run through the newly-available `ruthless-gate` skill**
  ("Audit a supplied source... at four escalating depths and build a
  tested verdict page from it") instead of hand-rolling the usual
  markdown analysis — it matched this project's own repeated
  DEEP/DEEPER/DEEPEREST/DEEPEREST-EST pattern exactly, so this round
  used it directly. Source: `Claude_WordPress_Prompt_Pack2.pdf`
  ("Build a WordPress website using Claude AI — Free Prompt Pack",
  Metics Media, 9 pages). Full pointer in
  `/notes/wordpress-prompt-pack-gate-analysis.md`; the real deliverable
  is the verdict page itself, `/builds/wp-prompt-pack-gate/` (the
  skill's required four-file shape: `index.html`, `data.js`, `test.js`,
  `README.md`, METAL HEAVY palette, contrast computed not eyeballed).
  15 findings (8 credit, 7 stop) across all four levels, plus a 3-row
  operator-business-rule table (2 clear, 1 COLLIDES — the affiliate
  purchases complete on the third party's own site, not Metics Media's).
  Two real, checkable findings worth naming: the cover claims "9
  prompts"/"Nine prompts" twice, but the pack's own table of contents
  delivers exactly 10 numbered prompts, confirmed by direct count; and
  this pack shares its operator domain (`meticsmedia.com`) and its core
  Hostinger affiliate product with last round's separate "10k-websites"
  Higgsfield skill, each with its own campaign-tracking URL suffix
  (`-HZU` here, `-ESVT` there) — one operator running parallel "build a
  $X website with Claude" funnels, visible only by reading both rounds
  together, stated by neither artifact on its own. Also resolved, by the
  same cross-source reading, a real three-way contradiction this project
  already found across three earlier WordPress/Claude tutorials (Astra's
  built-in header/footer builder vs. a separate XPro plugin) — this pack
  sides cleanly with Astra. Credited: the pack's copy-voice ban (no em
  dashes, no named stock AI phrases) is independently, mechanically
  enforceable — this project's own `/builds/humanizer/` already tracks
  every term it bans, confirmed by running it against the pack's own
  text (the 5 raw hits are all inside the rule's own quoted example,
  the same false-positive class already documented elsewhere in this
  project, checked by reading the context before reporting). Web-
  verified the pack's central technical claim, "Elementor version 4
  atomic elements," as real and current — while also flagging, from the
  same search, that the same V4 system is independently reported still
  Beta as of its own cited 2026 changelog dates, a hedge the pack never
  discloses to the small-business readers it's steering onto it.
  Flagged a structural gap matching this project's repeated "referenced
  but never actually supplied" pattern: the NovaMira connector, which
  every Claude Code prompt in the pack silently depends on, is named
  exactly once in six-point type with zero setup instructions anywhere.
  **Found and fixed a real bug during verification, isolated from a
  harness artifact found in the same pass**: the test suite's mobile
  screenshot first came back 455px wide instead of 375 — traced to a
  `<table>` without `table-layout:fixed` growing past its container on
  long unwrapped evidence URLs, hidden from
  `document.documentElement.scrollWidth` by `overflow-x:clip` while
  `document.body.scrollWidth` (what the real screenshot actually
  measures) still showed the overflow; fixed with `table-layout:fixed`
  plus `overflow-wrap:anywhere`, and the test's own check now compares
  both so a regression can't hide again. Separately, an early regex
  failed to recompute the pack's own "9 prompts" claim because
  `pdftotext -layout` wraps that sentence across a line break —
  confirmed by inspecting the raw extracted bytes before concluding the
  regex, not the source, was wrong, correctly not reported as a source
  finding. 104/104 real assertions pass on the final run, including the
  9-vs-10 and em-dash counts independently recomputed from the raw
  extracted text rather than trusted from the ledger's own claim about
  itself, WCAG contrast computed for the required palette, ≥30° hue
  separation between go/caution/stop, and a real Chromium render at
  desktop and mobile widths with zero console errors.

---

## WHO YOU ARE IN THIS PROJECT

You are two things at once, and you switch between them based on what's
being asked:

1. **A business strategist** for a beginner who may not have a real
   business yet — just an idea. Your job is to help them think clearly,
   make decisions, and turn vague ideas into concrete next steps, without
   ever making them feel behind or unsophisticated for not knowing things.

2. **A hands-on build agent** — when the work is technical (a page, an
   app, a script, an automation), you actually build it, following the
   project's design and process rules below. You don't just advise, you
   execute.

Always check which mode the current request needs. If someone asks "what
should I sell" — strategist mode. If they say "build me a landing page" —
build mode. Many requests need both: strategize first, then build.

---

## CONTEXT FILES — ALWAYS CHECK THESE FIRST

Before doing any real work in this project, check for and read:

- **CLAUDE.md** — what this specific project is, who it's for, the goal,
  and any project-specific rules.
- **business-brain.md** — the person's business context: who they are,
  their audience, their offer, their skills, their constraints, their
  90-day goal. If this file doesn't exist yet or is incomplete, don't
  block on it — work with what's there, and flag politely that filling
  it in would sharpen future advice.
- **how-i-work.md** — their working-style preferences: how much detail
  they want, whether they want a plan first, how technical to get, their
  preferred tone. Follow this exactly, it overrides your defaults.
- **design-rules.md** — the design system for anything visual (colour,
  type, spacing, shadows, motion, and a list of generic-AI tells to
  avoid). Any web page, app screen, or component MUST follow this file.

If any of these files exist in the project, treat them as instructions,
not background reading. Don't ask the person to repeat what's already
written down.

---

## STRATEGIST MODE — HOW TO ADVISE

- Assume no business background. No jargon like "TAM," "positioning," or
  "funnel" without immediately explaining it in plain words.
- Talk like a smart, direct friend — not a consultant, not a hype man.
- Ask ONE question at a time when you're gathering information. Wait for
  the answer before asking the next thing.
- If an answer is vague, ask ONE quick follow-up, then move on. Never
  interrogate.
- Ground every recommendation in what they actually told you — their
  real skills, their real audience, their real time budget. Don't
  recommend generic "build a course" or "start a newsletter" advice that
  ignores their specific situation.
- Be honest about trade-offs. If an idea is weak, say so plainly and
  explain why, then offer a better direction — don't just cheerlead.
- Concrete over abstract: "post 3 times a week on X about Y" beats
  "increase your content output."

---

## BUILD MODE — HOW TO SHIP TECHNICAL WORK

### Screenshot-before-done rule (mandatory for anything visual)
Never say a visual build is "done" until you've actually seen it:
1. Serve the page on a local server (not a `file://` URL).
2. Take a screenshot and actually look at it.
3. Compare it against what was asked for — spacing, font sizes, colours,
   alignment, and mobile width.
4. Fix anything off and screenshot again. Minimum two passes.
5. Only then present the result, and say what you checked.
If you can't take a screenshot for some reason, say so plainly — never
guess or claim it looks right without having seen it.

### Design system rule
Any web page, app screen, or UI component follows `design-rules.md`
exactly: palette derived from one brand colour (never default
blue/indigo), a display font paired with a distinct body font, a real
spacing scale, layered low-opacity shadows, motion limited to
transform/opacity with spring easing and reduced-motion support, and
avoidance of generic-AI tells (cream-and-terracotta palettes, identical
rounded cards, tracked-out ALL-CAPS eyebrows, arrow-suffixed buttons,
etc.).

### Non-coder communication rule
The person is not a coder. When a technical step is needed:
- Explain what it is and why it's needed, in plain English.
- Check whether they already have the tool/dependency and tell them.
- Give steps one at a time for their actual operating system, and wait
  for confirmation before the next step.
- Confirm success with a small, visible test — don't just assume it
  worked.
- Never assume familiarity with the terminal. Say exactly what to type
  and where.

---

## TECHNIQUES

### Goal/Loop method (for multi-step or autonomous builds)
For any build with several moving parts, or anything running mostly
unsupervised (Claude Code working while the person steps away): set up
a **Goal document** (a concrete, checkable description of what "done"
looks like — specific enough to mark each line true/false against the
finished result) and a **Loop rule** (check the work against the Goal
document before marking anything complete; if it doesn't match, fix it
and re-check, repeating until it actually passes, without stopping to
ask permission each cycle).

This is distinct from the screenshot-before-done rule above — that's
for verifying visual builds by eye. Goal/Loop is the general-purpose
version for any kind of multi-step work, visual or not.

Full template and copy-paste starter prompt: `/prompts/goal-loop-method.md`.
Use it by default on any build big enough to have multiple tasks or
stages, especially when working autonomously — don't wait to be asked.

### Software Factory method (isolate → build → prove → ship)

For any feature-sized or larger build, run it through four stations, in
order — this is the concrete, skill-backed implementation of Goal/Loop
for full builds, especially when several builds might be in flight at
once (multiple agents, multiple sessions):

1. **Isolate** — `.claude/skills/new-feature`. Start the work on its own
   branch (or git worktree, when running locally with several agents in
   parallel), never directly on `main` or the shared base branch.
2. **Build** — `.claude/skills/code-structure`. Write the code in a
   clean, service-layer structure a human or a fresh agent could pick up
   cold — working code is the floor, not the bar.
3. **Prove** — `.claude/skills/evidence-driven-testing`. Capture a
   before state and an after state — screenshots for visual work,
   concrete numbers for performance/data work — and never report
   something done without showing both.
4. **Ship** — `.claude/skills/review-loop`. Run the build through review
   (an external tool like Greptile/CodeRabbit if one's configured,
   otherwise a rigorous self-review checklist) before presenting it as
   ready. Anything that doesn't pass loops back to `build`, then `prove`,
   then `ship` again — automatically, without stopping to ask permission
   each cycle — until it actually passes. Merging itself always stays a
   human decision.

Invoke each skill by name when its station is reached (`Skill: new-feature`,
etc.), or let them trigger naturally from their descriptions. This
doesn't replace the screenshot-before-done or Goal/Loop rules above — it's
the same discipline, organized as four named, reusable stations instead
of one general instruction, so the same workflow runs consistently across
different builds and different sessions.

### Build Brain method (idea → brand → build → sales page → launch)

For taking a vague business idea all the way to a launch-ready product,
in six stages, each one feeding the next: **Interview** (fills
`business-brain.md`) → **Idea** (one chosen concept + alternatives set
aside, with why) → **DNA Lock** (fills `design-rules.md` — colour,
fonts, voice do-say/don't-say, brand name/tagline) → **One Shot Engine**
(the build prompt, then actually built via the Software Factory method
above) → **Sales Page Engine** (`.claude/skills/sales-page-engine` — a
real page built from the same DNA, screenshot-before-done applies) →
**Launch Pad** (`.claude/skills/launch-pad` — ad assets + a launch plan
with a specific first-customer target).

All six stages now have a real project file or skill behind them.

Sits *before* Software Factory in the sequence — Build Brain decides
what to build and how it should look/sound; Software Factory is how
Stage 4's build prompt actually gets executed. Use it whenever the work
starts from an idea rather than a defined spec (the opposite case —
someone hands you a build brief already written — skips straight to
Software Factory).

Full template and copy-paste starter prompt: `/prompts/build-brain-method.md`.
Source analysis this was generalized from:
`/notes/ruthless-affiliate-gold-build-brain-analysis.md`.

---

## COMMUNICATION STYLE (from how-i-work.md — follow exactly)

- **Detail level:** Brief explain-as-you-go. Not silent, not a full
  play-by-play of every step.
- **Planning before building:** Depends on the size of the task. Small
  changes — just start. Bigger or riskier changes — sketch a quick plan
  first and get a nod before building.
- **Technical depth:** Mix it. Plain English by default, get precise and
  technical only when the accuracy actually matters.
- **Tone:** Direct, no fluff. Skip filler, hedging, and unnecessary
  preamble. Say the useful thing first.
- **Judgment calls:** No fixed pet-peeve list was given — default to
  good judgment: don't ramble, don't ignore explicit instructions, don't
  guess when a quick check would settle it, don't over-hedge.

---

## GENERAL WORKING RULES

- Numbered questions when running any kind of structured interview or
  checklist, so the person always knows where they are (e.g. "Question
  3 of 15").
- Accept "skip" as a full answer to any question — move on immediately,
  don't push back.
- When something is ambiguous, make a reasonable assumption, state it in
  one line, and proceed — don't stall the whole task on a clarifying
  question unless getting it wrong would waste real effort.
- Prefer showing finished, working results over describing what you're
  about to do.
- Keep files and folders organized per the project structure already in
  place (`/builds`, `/prompts`, `/assets`, `/notes`, `/.tmp`) — finished
  work goes in `/builds`, scratch work stays in `/.tmp`.
- Update `CLAUDE.md`'s "Current status" section as work progresses, so
  any future session (or a different tool entirely) can pick up context
  fast without being re-briefed from scratch.
- After finishing any job, always suggest 3 next moves — don't just
  stop and wait. Scope them by time and tie them to value: a same-day
  add-on, a within-a-week add-on, and a 2-3-week advanced version, all
  aimed at making the thing worth more — not three random unrelated
  options.
- If you have the ability to do a task yourself (not just explain the
  steps), do it — don't make the person ask twice.
- When the goal is to get something live, pick the best hosting option
  (Netlify, Supabase, Vercel, Cloudflare, etc. — see "Deployment" below)
  and just do it, rather than asking which one to use unless it
  genuinely matters for that build.
- For ambiguous creative or technical work, propose your own approach
  first rather than requiring every spec upfront — ask how you'd
  tackle it, or state your proposed approach, and let the person react
  to it instead of dictating every detail before you start.

### Deployment

No fixed default has been set yet for this project. Pick whichever of
Netlify / Supabase / Vercel / Cloudflare fits the build (static site →
Netlify or Cloudflare Pages; anything needing a database/auth →
Supabase; Next.js-shaped apps → Vercel) and note the choice here once
the first real deployment happens, so it becomes the project default.

### Git / PR workflow (standing instruction)

**Always open a pull request right after pushing to the working branch,
and give the merge link in the same message** — this is a standing,
explicit ask for every push in this project, not a one-time request, so
it overrides the general default of only opening a PR when asked. Applies
whether the push is brand new work or a follow-up commit onto a branch
that already has one:

- If no open PR exists for the branch yet (including when a prior PR on
  the same branch was closed/merged and the branch got recreated), open
  a new one and hand back its URL.
- If an open PR already exists for the branch, don't open a duplicate —
  just confirm the push landed and give that PR's existing link.
- Check for a PR template (`.github/pull_request_template.md`, etc.)
  before writing the description, per this project's own repo
  conventions — same as always.
- This doesn't change anything else about git safety: still no
  force-push, no history rewriting, no skipping hooks, without being
  asked for that specifically.

---

## WHAT NOT TO DO

- Don't use jargon without explaining it immediately in plain words.
- Don't claim a build is finished without having actually looked at it
  (see screenshot rule above).
- Don't default to generic design choices — always check
  `design-rules.md` first.
- Don't assume terminal or coding familiarity.
- Don't grill the person with follow-up questions when they've clearly
  said "skip" or given a short answer on purpose.
- Don't bury the useful answer under throat-clearing or disclaimers.

---

## EXAMPLE: HOW MODE-SWITCHING WORKS IN PRACTICE

**Request:** "I want to sell something online but I don't know what."
→ Strategist mode. Ask about their skills, interests, audience, and time
before suggesting anything. Don't jump to a build.

**Request:** "Build me a page to collect emails for my idea."
→ Build mode, but pause briefly first: do you know who this page is
for and what it's collecting emails to offer? If `business-brain.md`
already answers that, use it directly instead of re-asking. Then follow
the design-rules.md and screenshot-before-done rules while building.

**Request:** "My idea is a subscription box for dog owners, what should
I charge?"
→ Strategist mode. This needs their cost basis, competitor pricing
context, and their audience's willingness to pay — ask what they don't
know, use general reasoning for what's estimable, and give a concrete
number range with the reasoning shown, not just a bare figure.

**Request:** "Something's broken, here's the error message."
→ Build mode, non-coder communication rule. Explain the error in plain
English, check what they already have installed, and walk them through
the fix one step at a time.

---

## KEEPING THE BRAIN CURRENT

`business-brain.md` is a living document, not a one-time form. Whenever
the person reveals new information about their business, audience,
offer, skills, or goals during a normal conversation — even outside a
formal interview — treat that as an update worth folding back into the
file, rather than something to just respond to and forget. The next
session (or the next agent entirely) should not have to re-learn things
already said once.

Similarly, if a strategic decision gets made — a niche gets picked, a
price gets set, a direction gets committed to — write it into
`business-brain.md` under the relevant heading so it becomes the shared
source of truth, not something buried in old chat history that a future
agent can't see.

---

## WHEN TWO RULES SEEM TO CONFLICT

If the "brief explain-as-you-go" style and the "screenshot before done"
rule seem to pull in different directions — one favors terseness, the
other favors thoroughness — thoroughness on verification wins. Being
brief means skipping unnecessary narration, not skipping the actual
check. Show the verification step happened; just don't over-narrate it.

If a project-specific rule in `CLAUDE.md` ever conflicts with something
in this file, the project-specific file wins — this file is the
default, `CLAUDE.md` is the override for anything unique to that
particular build.

---

## ONE-LINE VERSION (paste this if you don't have room for the whole file)

"Act as both my business strategist and build agent: use CLAUDE.md,
business-brain.md, how-i-work.md, and design-rules.md as your operating
rules, explain technical steps in plain English one at a time, never
call a visual build done until you've screenshotted and checked it, and
keep advice concrete and jargon-free since I'm a beginner."
