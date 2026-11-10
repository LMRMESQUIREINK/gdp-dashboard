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
- **Second `ruthless-gate` round, exercising its own multi-source rule**:
  two Medium articles by the same author (Sakshi Jaiswal), uploaded
  together in one text file — "20 Agentic Engineering Concepts Every AI
  Engineer Should Know" and "20 System Design Concepts Every Engineer
  Needs Before Building an AI Agent." Full pointer in
  `/notes/agentic-engineering-concepts-gate-analysis.md`; verdict page
  at `/builds/agentic-concepts-gate/`, same four-file shape as last
  round plus one structural addition this round's two-source format
  needed: a per-source credit/stop balance panel and a `source` tag on
  every finding, both checked programmatically by `test.js` per the
  procedure's own rule that each source must get at least one credit
  and one stop. Several dated, checkable claims web-verified: MCP's
  December 2025 donation to the Agentic AI Foundation (Linux
  Foundation, co-founded with Block and OpenAI) matches Anthropic's own
  announcement exactly, though the named supporter list omits two of
  the real five (Cloudflare, Bloomberg); LangGraph's October 2025 1.0
  release and the OWASP "LLM01:2025" prompt-injection ranking both
  check out; the July 2025 Replit/SaaStr production-database-deletion
  incident is real and multiply-corroborated in its core facts; one
  claim (Microsoft Agent Framework's GA date, stated as "April 2, 2026")
  turned out more precise than independent sources currently agree on
  (split between April 2 and 3). The strongest finding came from
  reading the two articles against each other, not either alone:
  article1 names "blast radius" as an explicit concept (large-impact
  actions need a permission-enforced human checkpoint, not just
  instructions); article2 separately recounts the Replit incident — an
  agent that deleted a production database despite repeated verbal
  instructions not to. Neither article connects the two, but together
  the incident is close to a textbook case of exactly what blast radius
  warns against — one source's framework predicting another's
  documented failure, the strongest kind of gap-finding the procedure
  is built to surface. Also found: article2 covers MCP in comparable
  depth to article1 yet never mentions the Foundation governance story
  despite both pieces being current enough to cite 2026 events; and the
  two articles use genuinely different, non-equivalent memory
  taxonomies — article2's "procedural memory" has no matching concept
  anywhere among article1's 20 items, not a renaming. Credited: both
  articles' own "20 concepts" claims are numerically exact (unlike the
  off-by-one found in last round's separate WordPress prompt pack), and
  the combined 3,669-word text scores zero findings against this
  project's own `/builds/humanizer/` AI-tell detector, re-run live
  inside `test.js` rather than trusted from a cached report. Business
  rules table marked all three n/a — this is educational writing with
  a standard Medium friend-link, not a product funnel, so the rule
  table doesn't describe a situation that exists here, stated rather
  than forced into a false clears/COLLIDES. 122/122 assertions pass,
  clean on the first real run — no bugs found and fixed this round,
  unlike the table-overflow bug caught in last round's build.
- **Deep analysis of four uploaded Fareed Khan "build an agentic X
  system" articles**, three new to this project and one a repeat: "The
  Case for Interface Lifting in AI Agents" is byte-for-byte the same
  article already analyzed and built from earlier in this project
  (`/notes/interface-lifting-fast-computer-agents-analysis.md`,
  `/builds/interface-lift-toolkit/`) — confirmed by title match before
  touching anything, same discipline as every repeat-upload round here,
  no new action taken on it. The three genuinely new pieces — "Building
  an Agentic Quantum Computing System," "Building an Agentic Security
  Pipeline That Finds, Proves, and Patches Vulnerabilities," and
  "Building a Week-Long Running Agentic System" — got the full write-up
  in `/notes/agentic-systems-deep-dive-analysis.md`. Reproduced the
  security-pipeline article's dead-store-elimination hazard from scratch
  before trusting it: a minimal 10-line `memcpy`-into-undersized-buffer
  repro, compiled `-O1 -fsanitize=address`, runs clean (exit 0) without
  an `__asm__ volatile` barrier (the optimizer proves the buffer dead and
  deletes the overflowing write) and crashes correctly with it — matching
  the article's claim exactly. Web-verified several dated claims: Temporal's
  Continue-As-New and replay-determinism mechanics (real, matching the
  long-running-agent article's durability story), PennyLane's `lightning.gpu`
  device (real, GPU-cuQuantum-backed, though its own docs say it raises an
  error with no graceful CPU fallback unless a wrapper checks first — a
  precision gap in how the quantum article describes its own `make_device()`
  helper), the LHC Olympics 2020 Zenodo dataset (real, matches the article's
  description, one DOI-digit mismatch found in an unrelated external
  citation), and Anthropic's own published six-step find/prove/triage/patch
  vulnerability loop (real and independently corroborated, not an invented
  framework). Flagged a likely publishing error in the security-pipeline
  article (every "code is on GitHub" link points at the *quantum* article's
  repo instead of its own stated one) and a real governor gap in the
  long-running-agent article (its budget check authorizes against a
  *projected* mean cost, not a hard per-cycle cap, so an unusually expensive
  cycle can still push the real total past the ceiling). The strongest
  finding came from reading the security-pipeline and long-running-agent
  articles together: both independently arrive at the same underlying
  principle — a deterministic, re-runnable check decides truth, never a
  model's self-report — one via AddressSanitizer exit codes, the other via
  git-committed checklist items that only flip to `done` after real lint/
  type/test commands exit zero — stated by neither article but visible
  reading both. A second cross-article finding: the quantum article's own
  mid-piece admission that its headline 8-qubit win only holds on 2 of 5
  seeds, and the security-pipeline article's report of a 7B model voting a
  provably-crashing bug `FALSE_POSITIVE` 3/3 with 95% confidence, are the
  same "a single run or a single opinion is not evidence" lesson stated two
  ways by the same author across two pieces that never cite each other.
  **Built:** `/builds/defender-loop-verifier/` — not the quantum pipeline
  (inseparable from GPU numbers this sandbox can't produce) or the
  long-running-agent's durability layer (inseparable from a real Temporal
  server, and this project already has a hand-built checkpoint/resume
  analog at `/builds/agent-checkpoint-layer/` covering similar territory
  with SQLite+WAL) — but the one idea from the security-pipeline article
  that is both genuinely new to this project and fully reproducible with
  nothing but `gcc` and the standard library already in this sandbox: "the
  host re-detonates independently and never trusts the agent's self-report,"
  built and tested as a real rule rather than just read about. A 2-bug ASan
  canary (reusing the exact dead-store hazard verified above: a heap-buffer-
  overflow and a heap-use-after-free), a deterministic verifier
  (`detonate()`/`verify_crash()`/`grade_patch()` — a real subprocess exit
  code and ASan `SUMMARY:` line decide crashes, majority-of-3-reruns before
  calling a finding reproducible, a 3-rung patch ladder), an allow-list tool
  dispatcher (unknown/not-allowed/mutation-disabled/egress-disabled, each
  enforced in code), and a scripted stand-in for the model (no live model
  API in this sandbox, same standing restriction as every build here) that
  can be told to lie in either direction about whether its own PoC crashed.
  Proven for real: two tests drive a dishonest agent one way each (denying
  a real crash, claiming a fake one) and show the verdict is unaffected
  either way, because `verify_crash()` never reads the self-report at all —
  a direct, testable version of the article's own worst-case finding. The
  patch ladder is shown to discriminate, not just pass everything: a
  root-cause fix (clamp the copy length before the `memcpy`, the article's
  own stated recipe) passes all three rungs; a cosmetic fix that only
  changes what gets printed correctly fails at rung two because the ladder
  re-detonates the *compiled* patched binary, not the diff text. 18/18 tests
  pass, clean on the first real run. Scope cuts stated plainly rather than
  silently made: no Docker/network sandbox (this session already runs
  inside one container with no outbound default access, so nesting a second
  one would guard against the wrong threat model), no multi-agent swarm, no
  recon/triage/severity stages — just the two stages that are genuinely
  load-bearing and fully verifiable without a model in the loop.
- **New build from a pasted planning conversation, not an uploaded
  document to audit: `/builds/creator-empire-ai/`** — an 18-app
  creator/marketing SaaS plan (6 suites of 3 apps, one master
  dashboard) with a Phase 1 six-app flagship workflow: product image →
  hook → sales script → storyboard → music transition → ad creatives →
  exported campaign package, demoed against a "Goli Nutrition" example.
  The source text's own honesty was carried through rather than
  smoothed over: no 18-app library exists yet, this is a build
  blueprint, and the UI itself tags only the 6 Phase 1 apps `LIVE`
  against 12 `PLANNED`. DNA Lock added to `design-rules.md` as a third,
  distinct brand — **Creator Empire AI**, ember red-orange
  (`#FF4D3D`) on a violet-near-black (`#110B14`), Sora/Manrope/
  JetBrains Mono — deliberately not the generic violet/indigo "AI
  dashboard" gradient this file already bans by default, and the
  source plan's own named margin risk ("unlimited AI video generation")
  and brand-endorsement risk (the Goli demo) both converted into hard
  don't-say rules rather than left as advice to remember later. Built
  **both** editions the user explicitly asked for, matching the user's
  own final instruction ("PLUS" both, not either/or):
  - **Standalone Edition** (`standalone/`) — a real, fully working,
    zero-dependency local app (plain HTML/CSS/JS, template-based
    generation, no API key, no network call) driving all 7 steps of the
    flagship workflow, with `localStorage` project save and
    `campaign.json`/`campaign-brief.md` export. Proven two ways:
    `test_pure.mjs` (40/40 — generator-function correctness, including
    that storyboard scenes tile the full duration with zero gaps/
    overlaps and the beat-map transition-second arithmetic is exactly
    right) and a real-Chromium `test_playwright.py` (25/25 — drives the
    complete 7-step UI flow, confirms the script's Hook part matches
    the picked hook exactly, confirms both file exports and the
    localStorage round-trip, screenshots at 1280px/375px with zero
    console errors and zero overflow). **Two real bugs found and fixed
    while testing, both in the test harness, not the app**: `inner_text()`
    picked up the `.part-name` CSS's `text-transform: uppercase`
    instead of the real DOM text (fixed by switching to
    `text_content()`), and a range `<input>` can't be driven with
    Playwright's `Locator.fill()` (fixed by setting `.value` via
    `page.evaluate()` and dispatching the same `input` event a real
    drag fires). A third, real app issue was also caught and fixed: the
    browser's automatic `favicon.ico` 404 surfaced as a console error,
    fixed with an inline SVG favicon.
  - **Cloud Edition** (`cloud/`) — not deployed (no Supabase project,
    OpenAI key, or Stripe account exists in this sandbox), but real,
    type-checked, dependency-injection-tested TypeScript for the parts
    that are architecturally new over the Standalone Edition rather
    than a line-for-line React port of UI already proven there: the
    shared `Campaign` record + a server-side `validateBrief()` that
    never trusts a client-typed body, a real OpenAI Chat Completions
    call with an injectable `fetch` for testing, two Supabase client
    factories matching its real documented anon-key/service-role split,
    the one secure `/api/generate` auth-gated AI endpoint the source
    plan calls its "immediate next milestone," a real
    `stripe.webhooks.constructEvent` signature-verification call (not a
    hand-rolled HMAC check), and a `projects` table with real
    Supabase row-level-security policies. Both the generate route and
    the Stripe webhook split a pure, dependency-injected handler out
    from their thin framework wrapper (the same pattern on both),
    which is what makes the actual branch logic testable without a
    live Supabase project or Stripe account. `npm run typecheck`
    (strict mode) clean; `npm test` 29/29 passing. **One real bug found
    and fixed while writing those tests, not a harness artifact**:
    `parseHookResponse`'s first draft scanned for the first `[` to the
    last `]` anywhere in the model's raw text, which silently accepted
    `{"hooks": ["a"]}` — a plausible off-spec response — by finding the
    *nested* array's own brackets, exactly the kind of off-spec output
    that should fail loudly instead of being guessed at (the prompt
    asks for "ONLY a JSON array... nothing else"). Fixed by requiring
    the entire fence-stripped response to parse as JSON directly,
    dropping the bracket-scanning fallback. Stated plainly rather than
    silently stubbed: the Stripe webhook's actual subscription→Supabase
    write is a real, named gap (needs a live Stripe account's real
    object shape to design against), not a silent no-op pretending to
    be done. 12 of the 18 apps, a deployed cloud instance, and any
    rendered video remain explicitly out of scope, stated in the
    build's README rather than implied as present.
- **`/builds/creator-empire-ai/cloud` extended into a real running
  Next.js app**, following all three user-picked next moves from round
  1 ("wire a real Supabase/OpenAI/Vercel deploy," "port the standalone's
  UI into Next.js," "build out Phase 2") — sequenced rather than
  attempted all at once: move 2 (the Next.js port) is what this round
  actually builds, since it's real code that could be written and
  proven without the live credentials move 1 needs; move 1's exact
  setup steps are explained rather than guessed at (Supabase project,
  OpenAI key, Stripe account, Vercel project, all needing the user's
  own accounts); move 3 (Phase 2 apps) stays queued for the round after.
  Installed Next.js 15 + React 19 for real — a real `npm view` check
  caught that the first `next@15.1.6` install carried a known CVE, so
  upgraded to the patched `15.5.28` backport before building anything
  on top of it. Ported the dashboard, login, and full 7-step campaign
  wizard from the Standalone Edition's already-proven logic
  (`lib/generators.ts` is a direct TypeScript port of
  `standalone/assets/app.js`'s generator functions, not a re-derivation
  — re-proven with its own 5 new tests matching the Standalone
  Edition's exact behavior) — hooks now call the real `/api/generate`
  route with the signed-in user's session token; `Save to Supabase`
  and both file exports are wired to real code paths. The browser
  Supabase client (`lib/supabaseBrowser.ts`) is deliberately constructed
  lazily, inside `useEffect`/event handlers only, never at module scope
  — the reason stated in the file itself: a module-scope throw (which
  `readSupabaseEnv()` does without live credentials, true in this
  sandbox) would fail `next build`'s prerendering pass for every page
  that imports it. **Two real bugs found and fixed this round, both
  while actually building and running the app, not from reading the
  code** — a real gap in round 1's own verification, which stopped at
  `tsc --noEmit` and never actually ran `next build`: (1) Next's own
  route-type checker rejected round 1's `route.ts` files outright
  (`"handleGenerateRequest" is not a valid Route export field"`) because
  it only allows a fixed set of exports (`GET`/`POST`/a few config
  constants) from a route file — round 1's dependency-injected handlers
  had been exported directly alongside `POST`, which satisfied plain
  `tsc` but not Next's stricter build-time check; fixed by moving
  `handleGenerateRequest`/`handleStripeWebhook` into
  `lib/generateHandler.ts`/`lib/stripeWebhookHandler.ts`, leaving each
  `route.ts` a thin wrapper exporting only `POST`. (2) TypeScript 7 (the
  brand-new native compiler, grabbed by round 1's plain
  `npm install typescript`) is incompatible with Next 15's build-time
  type checker and blocked `next build` entirely until downgraded to
  TypeScript 6, per Next's own error message — a real, currently-live
  version trap for anyone pairing a fresh `npm install` with an
  existing Next 15 project today. `next build` now succeeds for real:
  4 pages + 2 API routes, all 4 pages statically prerendered, with
  **zero live environment variables set** — direct proof the lazy-
  client design works rather than just reading plausibly. The built
  app was started for real (`next start`) and driven with Playwright:
  5 pages/viewports screenshot clean with zero console errors
  (`review/screenshots/cloud/`), and — the test that matters most for a
  "not deployed" build — both the login form and the wizard's
  "Generate hooks" button were actually submitted with no live Supabase
  configured, and both surfaced the real configuration error as
  readable UI with zero uncaught page errors, not a crash. 36/36 tests
  pass (29 from round 1, plus 7 new), strict-mode typecheck clean.
  Round 1's `parseHookResponse` bug-fix stands unchanged. Noted rather
  than silently force-upgraded: `npm audit` still reports one open
  PostCSS advisory, pulled in transitively by Next.js itself, whose fix
  needs a breaking Next 16 jump not validated this round.
- **Analysis-only round: a bare one-page PDF upload, "The $10K
  Checklist" (Metics Media, "Field Guide No. 01 · Claude Code Era ·
  MMXXVI")** — no accompanying text, same bare-file-reference pattern
  as the WordPress prompt pack round. Full write-up in
  `/notes/metics-media-10k-checklist-analysis.md`. Measured via
  `pdftotext -layout` rather than retyped by eye: 297 words, 8 numbered
  items, zero links/URLs/affiliate markers anywhere in the document
  (grepped and confirmed) — a real, checkable contrast with the other
  two Metics Media pieces this project has already audited, both of
  which carried embedded funnel links. The one finding that matters,
  checked directly rather than eyeballed: grepped
  `/builds/ten-k-website-grader/ten_k_grader.py`'s own pillar names
  (point-of-view, typography, colour, hierarchy, imagery, motion,
  mobile, invisible-stuff — built several rounds ago from a *separate*
  source, a "$10,000 Websites using Claude Code" video) against this
  PDF's eight numbered items and found an exact 8-for-8 match, same
  order, near-identical wording on several points — with neither
  document citing the other or any shared source for the taxonomy.
  Stated as an open finding rather than resolved in either direction
  (shared uncited source, one operator behind both, or coincidence too
  precise to easily credit), since nothing in either document settles
  which. **No build this round** — the one concrete idea in the PDF is
  already implemented, more rigorously, in the grader built from the
  earlier video round; a second implementation of the same eight
  categories from a shorter restatement would add nothing.
- **Deep analysis + new build from a bare repo link: `bytedance/deer-flow`
  ("DeerFlow 2.0")** — a bare GitHub URL with no accompanying text, same
  bare-reference pattern as every prior upload, cloned and read directly
  rather than summarized from its own README. Full write-up in
  `/notes/deer-flow-analysis.md`. This is a real, large, continuously
  shipping open-source agent harness (829 merged PRs toward one milestone
  in roughly a month per its own changelog, MIT-licensed, ByteDance), not a
  claim-heavy article or a toy — so the round focused on reading one
  concrete, fully-specified, independently verifiable mechanism in full
  rather than surveying the whole 4,389-file stack: the authoritative
  run-terminal-outcome protocol in
  `backend/packages/harness/deerflow/runtime/events/terminal.py` (316
  lines) plus its 373-line design doc, both read completely before writing
  anything. Checked two claims rather than repeating them: the README's
  "ground-up rewrite, shares no code with v1" held up structurally (the
  real `main-1.x` branch exists, 451 files, flat layout; a direct
  path-overlap diff against `main`'s 4,389 files found exactly 13 shared
  paths, every one of them repo boilerplate — README/LICENSE/Makefile/
  gitignore/one workflow file — zero shared implementation code); the
  "#1 on GitHub Trending" / "41,700 stars" claim is self-reported and only
  found mirrored elsewhere, not independently confirmed, same "source is
  silent" treatment as every other unverifiable popularity claim this
  project has flagged (Factory.ai's white paper, REA's "300,000 stars").
  **Built**: `/builds/run-terminal-ledger/` — a standalone, dependency-free
  Python reimplementation of the real mechanism (not guessed from docs
  prose): an idempotent `put_if_absent`-based singleton confirmation with
  four outcomes (`CONFIRMED_NEW`/`CONFIRMED_EXISTING`/`CONFLICT`/`UNKNOWN`),
  a bounded two-attempt lost-ACK retry, and a one-shot `RecoveryTarget`
  (immutable, raises on double-use) issued only from a genuine
  claim-for-takeover result, with a lifecycle guard ensuring a stale target
  issued before a run's deletion can't resurrect an orphan event — closing
  a real coordination gap this project's existing `/builds/
  agent-checkpoint-layer/` and `/builds/policy-control-plane/` don't cover
  (a disputed-outcome singleton that converges correctly even when two
  processes each wrongly believe they won a takeover race). Deliberately
  narrowed to just the terminal-outcome protocol and its seq watermark, not
  DeerFlow's full event envelope/categories/consumer projections, and not
  the upstream Evidence Ordering barrier sequence (concerns *when*
  confirmation may be called, not the protocol itself). **Found and fixed a
  real gap in this build's own first draft, not the source**: the first
  concurrency test shared one `TerminalLedger` instance across 20 racing
  threads, so that instance's own `threading.Lock` — not SQLite's `UNIQUE`
  constraint — was what actually prevented a double insert, leaving the
  `sqlite3.IntegrityError` fallback branch (the literal code backing the
  module's central atomicity claim) unexercised. Fixed by adding a genuine
  cross-process test: six separate OS processes, each constructing its own
  `TerminalLedger` against one shared SQLite file, with a seventh,
  independent connection verifying exactly one row after all six exit.
  16/16 tests pass on the real run, including the original 20-thread race
  (one status, and a harsher version where half the threads race a
  different, contradictory status) and the new cross-process race.
- **Deep analysis + new build from a pasted article: "AI System Design: A
  Practical Guide to Production AI"** (Piyush Kashyap). Full write-up in
  `/notes/ai-system-design-guide-analysis.md`. A genuine first for this
  project's run of deep-dives: no code to run and no dated/external claim
  to check — pure prose plus one running worked example (a fictional "AI
  helpdesk" company's capacity-planning arithmetic), so the only things
  to verify were its own numbers. Independently recomputed all 12 worked
  figures in a standalone script: every one checked out exactly, the
  cleanest arithmetic record of any source analyzed here — **except one
  small, real finding**: the article's peak-RPS figure (0.69 × 8 ≈ 5.52)
  computes from its own already-rounded 0.69, while the exact fraction
  (20,000 ÷ 28,800 = 0.69444...) × 8 = 5.5556 — both round to
  "approximately 5.5" so the practical conclusion is unaffected, but 5.52
  is a rounding-propagation artifact, not what the stated inputs actually
  produce. Credited: the "model requests, application executes" rule and
  the approval-must-be-payload-bound requirement are both independently
  the same principles `/builds/policy-control-plane/` and `/builds/
  defender-loop-verifier/` were already built around, arrived at by an
  unrelated author — the same kind of convergent-finding this project has
  flagged before. Found a real **internal tension**, not an external
  error: Section 9 proposes a cost-saving cascade ("try a cheap model,
  escalate if a quality threshold isn't met") two paragraphs before
  warning "don't confuse confidence with correctness" — and never
  reconciles how the cascade's own quality check avoids exactly the
  self-confidence trap the very next paragraph warns against. This
  project's own `/builds/jev-pattern-router/` hit a live version of this
  same failure during its own testing (a reworded destructive request
  dropping from 0.77 to 0.50 confidence, under its escalation threshold)
  — cited directly as a demonstration of the article's own unresolved
  warning. **Built**: `/builds/ai-system-design-toolkit/` — two of the
  article's ideas that are genuinely new to this project (everything
  else — HITL approval, idempotent outcome confirmation, confidence-gated
  routing, rate limiting, tool validation — already has a real build
  here, cross-referenced in the analysis rather than rebuilt): (1)
  `capacity_planner.py`, a real implementation of the article's exact
  sizing formulas (daily/peak RPS, Little's Law concurrency, token/cost
  estimation) — a gap this project's existing prop-firm sizing tools
  don't fill, since those size trading risk, not AI infrastructure; (2)
  `provider_breaker.py`, the circuit-breaker/bounded-retry/backoff
  algorithm `/builds/prop-firm-mcp-server/` explicitly deferred in an
  earlier round ("no upstream network call exists to protect against") —
  now built for real against a genuinely simulated flaky dependency, with
  real thread safety: the standard closed/open/half-open state machine,
  equal-jitter exponential backoff, a time budget that stops retrying
  early, and a fallback path when the breaker is open. 29/29 tests pass
  on the real run, including a deterministic backoff-value check (fake
  clock/sleep/rand injection, no real sleeping) and — the test that
  actually proves the concurrency claim rather than asserting it — 8 real
  OS threads racing the instant a cooldown elapses, with exactly one
  becoming the half-open probe (confirmed by a call counter) while the
  other 7 are rejected until it resolves.
- **Deep analysis + new build from a pasted three-article AgentsKit.co
  bundle** ("Claude Coding Tools: What to Install in 2026," "The Best
  MCP Servers for Claude," "Claude Productivity Tools: The Hidden
  Features"). Full write-up in
  `/notes/agentskit-claude-tooling-bundle-analysis.md`. Measured rather
  than skimmed: 1,769 words, exactly 8 links, every single one pointing
  back at `agentskit.co` itself with zero query-string tracking
  parameters and zero links to any third party — a real, checkable
  contrast with this project's two earlier Metics Media rounds, whose
  links carried per-campaign tracking suffixes on third-party partner
  pages. Every concrete technical claim checked out: real
  `npm install -g @anthropic-ai/claude-code` and `claude mcp add`/
  `claude mcp list` CLI syntax, and (checked by web search since the
  article's July 2026 dateline sits past this project's own knowledge
  cutoff) GitHub Copilot's real Claude-model support, confirmed current
  via GitHub's own changelog. Flagged as unverifiable rather than
  repeated as fact: "the AgentsKit Engineering Kit, 58 agents, 61
  skills, and 159 commands" — a paid product with no public repository
  to check, same treatment as every other unverifiable vendor-capability
  claim this project has flagged (Factory.ai's white paper, REA's star
  count before independent corroboration). **Built**: `/builds/
  skill-md-validator/` — the bundle's own named "SKILL.md validator"
  idea (a web product with no inspectable source, so built independently
  from this project's own eleven real skills rather than ported),
  checking frontmatter shape, name/directory match, description quality,
  broken file references, and duplicate-name collisions (the exact
  failure class `bytedance/deer-flow`'s own `docs/
  SKILL_NAME_CONFLICT_FIX.md` documents, from the deer-flow round two
  entries back). **Found and fixed two real bugs in this build's own
  first draft, not in the real skills it was tested against**: (1) the
  broken-reference check's first draft assumed every reference was
  relative to the skill's own folder, producing 16 false-positive
  errors across 7 of this project's 11 real skills on the very first
  run, since several skills legitimately use repo-root-relative paths
  (`/builds/...`, `/notes/...`) and bare sibling-skill references
  (`.claude/skills/other-skill`) — fixed by resolving against both the
  skill's own directory and the repo root, failing only if neither
  resolves; (2) the "states a usage condition" heuristic missed real,
  correctly-phrased trigger language in `code-structure` and
  `review-loop` ("Use while implementing...", "Before calling a build
  finished..."), caught by reading the two flagged files by hand before
  trusting the tool's own warning, confirming the gap was in the
  heuristic, not those two skills — fixed by widening the trigger-word
  list. 19/19 tests pass on the real run, including the real deliverable
  (`test_all_real_skills_pass_clean`): this repo's actual eleven skills
  now validate with zero errors and zero warnings, spot-checked by hand
  rather than taken on the tool's own word.
- **Shown two AgentsKit.co screenshots (12 more of their tools) and
  asked which to recommend** — strategist-mode judgment call, not a
  build request: picked the Slash Command Generator as the clear top
  pick, reasoning from this project's own actual pattern rather than
  the tools' own marketing copy — the single most repetitive thing this
  session does, over and over, is source-arrives → measure → verify →
  credit/flag → decide build-or-not → build+test if warranted →
  `/notes/` write-up → `CLAUDE.md` status-log update → commit → push,
  executed by hand well over a dozen times. Named CLAUDE.md Grader as a
  real second pick (this file is now 2,000+ lines, a plausible fit for
  its stated "token budget, vague rules, linter duplication" checks),
  named the SKILL.md Validator as already covered (built independently
  last round, more rigorously tested than taking theirs on faith), and
  gave a one-line reason each for skipping the other nine rather than
  surveying all twelve. **Built, per the user's follow-up**: a real
  slash command, `.claude/commands/analyze-and-ship.md` —
  `/analyze-and-ship [source]`. Not a port of AgentsKit's own tool (a
  generator for an unrelated kind of command entirely — turning one
  repeated *prompt* into a command, not encoding a multi-stage audit
  procedure); written directly from this session's own real,
  repeatedly-executed loop. Encodes, as an actual operational playbook
  rather than a vague pointer: check-before-assuming for an unrelated-
  project source (the `outage-alert` precedent), diff a repeat upload
  against the repo before touching anything (the Trading Jarvis
  round-4/Week-21-survey precedent), measure-before-meaning, verify via
  direct recomputation and web search rather than repeating claims,
  require at least one real credit and one real gap, check `/builds/`
  for an existing implementation before building a duplicate, extract
  the generalizable mechanism rather than cloning a vendor's own
  branded instance (the RemixForge/REA/deer-flow precedent), prefer
  testing against this project's own real material over synthetic
  fixtures alone (the `skill-md-validator`/`ten-k-website-grader`
  precedent, both of which found real bugs exactly that way), and the
  existing git/PR workflow rule for shipping. Explicitly distinguished
  from `ruthless-gate` in the command's own text, so a cold session
  doesn't confuse the two. Also added a short TECHNIQUES entry
  (**Deep-analysis-and-ship loop**) pointing to it, matching how
  Goal/Loop, Software Factory, and Build Brain are each documented
  there. **Proof available, and its real limit stated plainly**: no
  official `claude command validate` exists in this project the way
  `claude plugin validate` does for mods, so this was checked the way
  `skill_md_validator.py`'s own frontmatter parser checks a SKILL.md —
  a standalone script confirming well-formed YAML frontmatter
  (`description`, `argument-hint`, both non-empty), a non-empty body,
  and a real `$ARGUMENTS` reference. What isn't proven: the command
  hasn't been invoked inside a live, interactive Claude Code session
  from within this sandbox — the same honestly-flagged limitation this
  project already stated for `/builds/claude-code-mods/`'s three mods,
  which also can't be exercised live from here.
- **First real run of `/analyze-and-ship`** on a pasted Fareed Khan
  article, "Engineering Multi-Agent AI for a 100 GB Data Warehouse" — a
  repeat author (five prior rounds) but a genuinely new article,
  confirmed by title first. Full write-up in
  `/notes/agentic-warehouse-analyst-analysis.md`. Cloned the real named
  repo (`FareedKhan-dev/agentic-warehouse-analyst`, MIT) rather than
  trusting the pasted code samples alone — the most thoroughly
  independently-verifiable source this project has analyzed to date:
  a real 6,679-line executed notebook, a real `run_manifest_sf100.json`,
  a real 12-row `revisions_sf100.csv` revision ledger, and a real
  `llm_cache.sqlite` with 4,005 cached model calls (consistent with
  roughly a dozen revisions over ~100 dev questions times several calls
  each — not a number easy to fake convincingly). Every specific number
  checked against the real executed notebook output matched exactly:
  "92/93 official answers reproduced," the "469,796x" planner
  underestimate, "85,927,834,294,703" vs. the real exact count
  "135,299,781,560,539" (ratio 1.575, matching the article's own
  "within a factor of 1.6" precisely), the warehouse's 28,609,622,016
  bytes, and every dated test/live-stopwatch figure. Credited: the
  article's own "Known Limits" section discloses both missed targets
  (9.8% false-success vs. a 5% goal, 24.55s live p95 vs. a 15s goal)
  unprompted, right where the numbers appear — the same honest-
  negative-result credit this project has given the Jev and quantum-
  computing articles in earlier rounds. **Found a real, well-evidenced
  gap, checked directly in the source, not inferred**: the revision
  loop's `revise()` function (`notebook/agentic_data_analyst.py:3738`)
  computes and prints a 95% paired-bootstrap confidence interval for
  every keep/revert decision, but the actual decision —
  `keep_if=lambda new, old: new["utility"] > old["utility"]` — never
  looks at it; the interval is real and genuinely displayed, just not
  load-bearing. Confirmed against the real ledger: r09 ("sorted copy +
  rollups") was KEPT with an accuracy confidence interval of
  `[-0.0098, +0.0686]` that includes zero — not a wrong call (its real
  justification was a latency win, stated plainly in the article's own
  prose), but the printed interval creates an appearance of statistical
  rigor for the accuracy claim specifically that the code doesn't
  enforce anywhere. **Built**: `/builds/paired-bootstrap-ratchet/` — not
  a port of the article's own TPC-DS-specific revision loop (inseparable
  from a 28.6GB warehouse this sandbox doesn't have), but the one
  generalizable mechanism the finding points directly at: a
  paired-bootstrap significance gate that actually enforces the interval,
  with two modes (strict significant-improvement, and a non-regression
  mode correctly modeling the legitimate r09-style case — a regression is
  only significant when the *entire* interval, including its best-case
  upper bound, sits below a floor). Tested against the real, unmodified
  `revisions_sf100.csv` (MIT licensed, copied in as a fixture) rather
  than only synthetic data: confirmed the four clear accuracy-claim
  revisions (r01/r02/r06/r12) pass a strict gate, confirmed r09 fails the
  strict gate but passes non-regression, and found a second, more
  granular instance of the same phenomenon purely by building and running
  the gate rather than reading the CSV by eye — r05 ("repair=2") was KEPT
  in the real repo with a real reported `delta_lo` of exactly `0.0`,
  touching but not excluding zero, which a strict gate correctly refuses
  to call significant even though the real repo's point-estimate rule
  called it an improvement. **Found and fixed a real bug in this build's
  own first draft while writing those same real-ledger tests**: the
  non-regression gate's first version checked `ci_lo >= -epsilon`, which
  is actually a strict "must never dip below zero" rule, the wrong bound
  for "not significantly worse" — caught immediately because r09's own
  real interval failed the gate it was supposed to pass under that wrong
  logic. Fixed by checking `ci_hi` instead (a regression is significant
  only when the whole interval, including its best case, sits below the
  floor). Also rewrote two test assertions mid-build after the real data
  disagreed with the first draft's assumptions (r05's boundary case; r13/
  r15 touching exactly `ci_hi = 0.0`, correctly distinguished as
  "not confirmed better" rather than forced into "confirmed worse")
  rather than adjusting the data or the gate to force a pass. 17/17 tests
  pass on the real run.
- **An exact duplicate re-paste correctly declined.** The user pasted
  the same Fareed Khan warehouse-analyst article a second time, verbatim,
  immediately after the round above shipped it. Per this project's own
  "diff a repeat upload before touching anything" rule, confirmed the
  commit/build/notes already existed (`c89588e`, `/builds/
  paired-bootstrap-ratchet/`, `/notes/agentic-warehouse-analyst-analysis.md`)
  and reported that back instead of redoing the work. The user's
  follow-up ("SOMETHING DIFFERENT!!") named no new source, so rather
  than guess which of several real meanings was intended (strategist
  mode, one of the 3 suggested next-moves, or a genuinely new source),
  asked via `AskUserQuestion` — the user dismissed the question without
  answering and sent a new source directly instead, handled below.
- **Deep analysis + new build from a pasted newsletter article**: "12
  Open-Source GitHub Repositories to Learn AI and LLM Engineering From
  Scratch" (vijayasekhardeepak.com). Full write-up in
  `/notes/learning-path-12-repos-analysis.md`. Unlike most sources this
  project analyzes, there's no pipeline of the author's own to audit —
  it's a curated pointer list to 12 independent, real repos, so the
  checkable surface is whether every link is real and whether the
  article's specific claims about each one hold up. All 12 repos
  confirmed to exist via anonymous `git ls-remote` (zero link rot) before
  reading any for meaning. Five were cloned and read in full for their
  most specific, numeric/status claims: `huggingface/ml-intern`'s
  claimed archived status confirmed exactly (the real README even names
  the exact repo it moved to, `huggingface/chat-ui`, a detail the
  article omitted); `microsoft/AI-For-Beginners`'s claimed "24 lessons"
  and `microsoft/generative-ai-for-beginners`'s claimed "21-lesson"
  figure both matched their real READMEs' own stated counts exactly;
  `mlabonne/llm-course`'s claimed three-part structure (LLM
  Fundamentals/Scientist/Engineer) matched verbatim; `mml-book/
  mml-book.github.io`'s description as the *Mathematics for Machine
  Learning* companion repo (linear regression + PCA notebooks) matched
  exactly. **One real, well-evidenced miss found**: item #5 is headed
  "LLM Course by Maarten Grootendorst," but the real repo's own README
  names its actual maintainer three separate ways (`@maximelabonne` on
  X, `huggingface.co/mlabonne`, co-author credit for a *different* book,
  *LLM Engineer's Handbook*). Web-verified before calling it an error
  rather than an obscure alias: Maarten Grootendorst is a real, different
  person — BERTopic/KeyBERT's creator, a Developer Relations Engineer at
  Google DeepMind, co-author of a *different* LLM book (*Hands-On Large
  Language Models*, with Jay Alammar) — not this repo's author. Two
  real, both-active authors in the same adjacent space, swapped; every
  other claim about that same repo (link, structure, content) was
  accurate, only the byline was wrong. **Built**: `/builds/
  curriculum-link-auditor/` — not a port of any of the 12 repos (they're
  independent, unrelated projects with nothing to extract), but the
  generalizable version of the by-hand check that found the
  misattribution: given a repo's real README text and a curated list's
  specific claims about it (lesson count, archived status, structure
  keywords, claimed author), report what holds up and what doesn't,
  with a conservative author-attribution check that only flags a
  mismatch when the README actively names a real handle inconsistent
  with the claim, never from a README's mere silence. Tested against the
  real, unmodified README fixtures from three of this exact article's
  repos (not synthetic text) as committed regression fixtures, including
  the real misattribution as a permanent test case. **Found and fixed a
  real bug while actually running the CLI end-to-end against the real
  llm-course README**, not caught by reading the regex: the first draft
  of the handle-extraction function matched Hugging Face's own
  site-navigation paths (`huggingface.co/blog`, `/docs`, `/learn`,
  `/models`, `/spaces`, …) as if they were usernames, polluting the
  mismatch evidence with noise alongside the real `mlabonne`/
  `maximelabonne` handles. Fixed with an explicit reserved-path-segment
  exclusion list. Proven two ways: 21/21 unit tests against the real
  fixtures, and a real, live, network-backed end-to-end run of the CLI
  itself (`audit.py --check-live`) against all 5 actually-cloned repos,
  reproducing the same result — 4 clean matches, 1 correctly-flagged
  mismatch — with a live no-token `git ls-remote` confirming every repo
  still exists today.
- **All three suggested next-moves on `curriculum-link-auditor` done in
  one round, not a subset.** (1) **Tried the live GitHub API archived
  check, found it genuinely isn't available without a disproportionate
  step, and said so rather than building a fake version.** `add_repo`
  with `access:"read"` confirmed this session's anonymous git proxy
  already serves any public repo's clone/fetch with no attachment
  needed — but it also states GitHub API tools require `access:"push"`,
  which mints real write-capable credentials for that repo. A plain
  HTTPS fetch of a repo's own GitHub.com page (no API, no git) was tried
  as a middle ground and returned 403 — also blocked. Minting push
  credentials to an arbitrary external repo just to read one boolean
  flag is disproportionate to the task and wasn't done; documented
  plainly in the build's README as a real, checked constraint rather
  than an unexplored TODO. (2) **Re-checked three of this project's own
  previously-flagged "self-reported, never independently re-checked"
  figures for drift** — `/notes/stale-claims-recheck-2026-11.md`.
  `bytedance/deer-flow`'s original "41,700 stars" figure is still
  `source-is-silent` (sources disagree with each other on the exact
  historical number, from "nearly 30K" to "72,000"), but all agree on
  real continued growth, not fabrication. `morluto/rea`'s "300,000
  stars" claim, originally judged "plausible" from a growth trajectory
  reaching ~234,000 by Oct 14, is now confirmed by a stronger
  independent source: it actually crossed 300,000 on Oct 17 and reached
  347,802 by Oct 21 — the original judgment held up and was if anything
  conservative, plus a new caveat surfaced (one fact-check source
  questions how many of those stars are from real readers). `n8n-io/
  n8n`'s "1,500+ integrations" vs. its real core package's node count,
  originally found at 308 dirs/563 files and left unreconciled, was
  re-cloned fresh and found at 309/563 — the gap is stable, not a
  timing artifact. None of the three original findings needed
  correcting; the "no changes needed is a common, correct outcome" rule
  applied to claims rather than to a repeat upload. (3) **Built a
  batch/regex auto-extraction mode**: `extract_claims.py`'s
  `auto_extract_manifest(text)` takes a curated list's own raw article
  text and auto-builds the same `RepoClaim` objects a human would
  otherwise hand-write — repo links, "N lesson(s)" figures, archived/
  retired mentions, numbered-heading "by `<Name>`" bylines — leaving
  structure-keyword claims as manual-only, since that phrasing varies
  too much to regex reliably without false positives. Proven against a
  condensed reconstruction of this exact build's own source article
  (`tests/fixtures/12-repo-learning-path-article.txt`, preserving the
  real article's exact repo links/figures/wording): auto-extraction
  reproduces all 12 repos in order with zero false positives, and the
  full extract-then-audit pipeline run end-to-end reproduces the exact
  same 4-matches-plus-1-misattribution result as the original
  hand-written manifest — proof it's a real drop-in for
  `/analyze-and-ship` on curated-list sources, not just plausible-
  looking output. **Found and fixed a real bug while writing the
  extraction tests**: the first draft of `extract_repo_links` excluded
  links whose path continued past the repo name (`.../issues/12`), on
  the theory that such a link points "into" a repo rather than "at"
  it — but a link to a repo's issues page is still citing that same
  repo, not a different one, so the exclusion was actively wrong, not
  merely unnecessary. Caught by the test itself failing on exactly that
  case; fixed by removing the exclusion. 38/38 tests pass across both
  modules on the real run (21 original + 17 new).
- **Deep analysis of Part 2 of the same newsletter series**: "12
  Open-Source GitHub Repositories to Become an AI Engineer: Agents, RAG,
  MCP & System Design" (vijayasekhardeepak.com) — a different,
  independently-written article with 12 different repos, confirmed by
  title/content before touching anything, not a repeat upload. Full
  write-up in `/notes/learning-path-12-repos-part2-analysis.md`. All 12
  repos confirmed real via anonymous `git ls-remote` (zero link rot):
  `openai/openai-cookbook`, `anthropics/claude-cookbooks`,
  `Shubhamsaboo/awesome-llm-apps`, `huggingface/agents-course`,
  `NirDiamant/GenAI_Agents`, `KalyanM45/AI-Project-Gallery`,
  `asgeirtj/system_prompts_leaks`, `priyanshop754/vibe-coding-playbook`,
  `ombharatiya/ai-system-design-guide`, `donnemartin/system-design-primer`,
  `florinpop17/app-ideas`, `The-Cool-Coders/Project-Ideas-And-Resources`.
  A real structural difference from Part 1 confirmed by reading the
  whole article rather than assumed from its shape: zero lesson-count
  claims and zero author bylines anywhere in it — every claim here is a
  topic/scope description instead. Four repos cloned and read in full:
  `huggingface/agents-course`'s claimed `smolagents`/LangGraph/
  LlamaIndex/MCP coverage confirmed substantial, not name-dropped (156,
  94, 16 file mentions respectively, plus a dedicated `llama-index/` unit
  per translated language); `NirDiamant/GenAI_Agents`'s claimed
  multi-agent tutorial coverage confirmed via 65 real notebooks;
  `ombharatiya/ai-system-design-guide`'s claimed RAG/interview-prep
  content confirmed exactly (a real 155-question interview bank);
  `asgeirtj/system_prompts_leaks`'s claimed broad multi-vendor system-
  prompt collection confirmed real and current (its own "most recent
  additions" table carries an entry dated the same day as this
  analysis — confirmed as evidence of active maintenance, with that
  specific entry's content deliberately not opened, since reading
  content purporting to describe this session's own operating
  instructions wasn't needed to confirm the repo is actively
  maintained). Flagged rather than repeated as fact: the same repo's own
  self-cited Simon Willison endorsement couldn't be independently
  confirmed by a web search this round — noted as unverified from this
  check, not as the analyzed article's own claim (the article doesn't
  repeat that quote). **No new build** — per this project's "check
  `/builds/` for an existing implementation before building a
  duplicate" rule, this is exactly the source type `/builds/
  curriculum-link-auditor/` already handles. Ran its
  `auto_extract_manifest()` directly against this second, independently-
  written article's raw text and it correctly extracted all 12 repos in
  order with **zero false-positive claims** — the honest-negative-result
  case, since a cruder extractor could have mismatched the article's own
  incidental numbers/names ("1,000 users," "smolagents," "LangGraph") as
  structured claims about a repo. Added as a permanent regression test
  (`TestGeneralizationToASecondIndependentArticle`, using a committed
  fixture of this real article's text) proving the tool generalizes
  beyond the one article it was originally built from. 40/40 tests pass
  across both modules on the real run (up from 38).
- **Third `ruthless-gate` round**: "The $1M+ Solo Grok Bot Business (Full
  Course)" PDF (23 pages, converted the same day it was uploaded per its
  own metadata). Full pointer in
  `/notes/solo-bot-business-gate-analysis.md`; verdict page at
  `/builds/solo-bot-business-gate/`, same four-file shape and METAL
  HEAVY palette as `wp-prompt-pack-gate`/`agentic-concepts-gate`, this
  round's skill copy carrying updated exact contrast numbers
  (`--stop-ink:#ED7066`, not the earlier `#E8615A`) — independently
  recomputed and confirmed exact (4.94/4.49/3.93 for `--stop`,
  6.30/5.73/5.01 for `--stop-ink`) before trusting them. Measured first:
  this "course" is actually a single podcast episode (Greg Isenberg
  interviewing Nick Vasilescu, Orgo's co-founder) run through a PDF
  converter, with an AI-cleaned "Key Points" summary layer pasted over
  an unedited ASR transcript — proven precisely by the product's own
  name spelled correctly (`GrokBot`, 7×) only before the exact line
  where real podcast prose starts, and garbled (`Grockbot`, 29×) only
  after it, zero crossover. 15 findings (6 credit, 9 stop — an honest,
  not-forced ratio, asserted as such in the suite rather than padding
  credits to force balance). Two headline findings: the title's "$1M+"
  claim never appears again anywhere in 834 lines (one hit total — the
  title), and a direct arithmetic error in the transcript itself
  (`"$36,000 plus 25K, $51,000 of value"` — the real sum is $61,000,
  understated by exactly $10,000, direction and size both asserted).
  Also found: the single most actionable promise in the pitch ("fork
  the open-source repo") never supplies a repo name or URL anywhere in
  the source; the "$3,000/month is like $12/hour" framing is exact only
  under a hidden, never-stated 250-hours-a-month assumption; and the
  real, dated "2% of US households pay for AI tools" statistic
  (Andreessen Horowitz's 2026 report, web-confirmed) is attributed on
  the page to "Andre Horowitz," an individual who doesn't appear to
  exist — almost certainly the real firm name clipped by the same
  ASR-garbling pattern already confirmed for GrokBot/Grockbot,
  misattributing institutional research to a fictional person.
  Credited: Nick/Orgo's real identity and accurately-self-described
  product; the concrete, falsifiable client-acquisition sequence (call
  50 people, free first build for a case study, trade for 3 intros);
  Paper's real, current MCP server matching the claimed design
  workflow; and the "10-20x niche pricing power" claim checking out
  arithmetically against the actual $3,000/mo price sold elsewhere in
  the same transcript. **A real correction made mid-build, caught by
  the suite itself**: the first draft of the GrokBot/Grockbot finding
  assumed the clean/garbled boundary was the "1. Why Businesses..."
  heading (line 34) and claimed a 7-vs-30 split; running the suite
  immediately surfaced 6 false positives (clean "GrokBot" spellings
  inside what should have been the garbled region) — reading those
  lines directly rather than trusting the regex found the real boundary
  46 lines later, at the actual first line of podcast prose. Corrected
  to the true boundary (verified 7-vs-29, zero crossover) rather than
  adjusting the regex to force the wrong original boundary to pass. A
  second, smaller correction: a palette assertion copied the skill's
  own prose claim that `--stop` "clears the text floor nowhere" without
  re-deriving it — but `--stop` on `--engrave` is 4.94:1, which does
  clear 4.5. Fixed by dropping the blanket claim and asserting only
  what the real rendered page actually guarantees: `--stop` is never
  applied as a `color` property anywhere in the CSS, confirmed via real
  computed-style inspection in the Chromium phase, not the raw contrast
  number alone. Both new detector types (the arithmetic-error check,
  the section-5/6/7-gap check) proven to actually fire via a planted
  counterexample before being trusted. 170/170 assertions pass,
  including a real Chromium render at 1280px and 375px, zero console
  errors, zero overflow, and coverage confirmed above the verdict by
  real `getBoundingClientRect` position, not just DOM order. The second
  half of this round's instruction — "create code for an app... called
  Solo Claude Bot Business, incorporating the other 2 articles" — was
  deliberately deferred rather than guessed at, since "the other 2
  articles" names no specific source; clarification requested
  separately before any code gets written for it.
- **The app got built**: the clarification came back "no incorporation
  needed — just build from this PDF." **`/builds/solo-claude-bot-business/`**
  — a real, zero-dependency local app (plain HTML/CSS/JS, localStorage,
  no API key, no network call, same convention as this project's other
  standalone builds) with three panels built from the audit's own
  credited findings, not the source's unverified claims: an **Offer
  Calculator** (reproduces the source's real $200/mo baseline → $3,000/mo
  retainer → $25,000 upfront exactly when fed the source's own real
  numbers, but computes the effective hourly rate from a visible,
  editable hours-per-month input rather than hiding the 250hr/month
  assumption the audit found baked into the source's own "$12/hour"
  line), a **Client Pipeline tracker** (operationalizes the audit's
  credited client-acquisition sequence — call 50 people you know, free
  first build for a case study, trade for 3 referrals — with real add/
  status-change/remove and a referral-goal counter), and a **Build
  Checklist** (Research → Design → Build, the four generalized stack
  categories left for the user's own tool names rather than hardcoded
  to the source's own named vendors, since the audit found "Agent
  Mail"/"Agent Phone" don't exactly match any locatable real product
  under those literal names). New DNA Lock added to `design-rules.md`
  (fourth locked brand) — deep teal `#1C7C74` on near-black `#0B1412`,
  IBM Plex Sans/Source Sans 3/JetBrains Mono, deliberately distinct
  from all three other locked brands' hues, voice rules carrying the
  audit's own findings forward as hard don't-say rules (no "$1M+" or
  unbacked revenue claim, no "fork the repo" promise without a real
  link, no bare hourly rate without a stated hours basis, never cite a
  statistic to a name without checking it's real first — the audit's
  own "Andre Horowitz" finding). **Every mention of "Grok"/"GrokBot"
  eliminated from the app itself**, confirmed by a real DOM-text check
  in the Playwright suite, not just a source-file grep (one
  developer-facing provenance comment in `assets/app.js` factually
  names the real source title, per this project's standing
  documentation convention — not user-facing branding). **A real bug
  found and fixed during screenshot verification**: the pricing-
  multiplier range slider rendered with the browser's native blue
  thumb, clashing with the locked teal palette — caught on the first
  screenshot pass, fixed with `accent-color`, clean on the second
  pass. Proven two ways: `test_pure.js` (21/21 — the offer math
  reproduces the source's own real numbers exactly when given the
  source's own real inputs, pipeline/checklist logic, a real
  localStorage round-trip including graceful fallback on corrupted
  JSON and a merge-with-defaults path for an older saved profile
  missing newer fields) and `test_playwright.py` (22/22 — a real
  Chromium render driving the full add-contact/change-status/log-
  referral/remove flow, a real page reload confirming state
  persistence, zero console errors, zero overflow at 375px, and the
  zero-Grok-mentions check run directly against the live rendered DOM).
- **Fourth `ruthless-gate` round, and the first on a bare GitHub repo rather
  than an article/PDF**: `FareedKhan-dev/ontology-driven-observability` — a
  sixth Fareed Khan source for this project, confirmed genuinely new by
  title/content before touching anything. The user's own pasted file tree
  (a `kg/` directory of 13 separate Python modules) was measured against the
  real, anonymously-cloned repo and found not to match it at all — the real
  repo has no `kg/` directory anywhere; everything lives in one real,
  already-executed 12,141-line jupytext notebook rebuilding Netflix's real,
  web-verified October 2026 "Ontology-Driven Observability" knowledge-graph
  design from its public description, measured against real public data
  (Wikimedia's operations record, OpenRCA, RCAEval, Wikipedia pageviews).
  Confirmed via the real `README.md`'s own "Repository layout" section
  before writing anything else — a direct, documented instance of why this
  project's "measure before reading for meaning" rule exists (`deep-01`,
  `deepest-est-03`). One of the most rigorous, most independently-checkable
  sources this project has analyzed: a real pre-registration file with a
  SHA-256 fingerprint, a logged label-revision kept with both old and new
  fingerprints side by side, a 51-entry bug registry (recomputed and
  confirmed exact, matching the notebook's own `BUGS` list literally), and
  an honest 4-of-7 explicitly-missed pre-registered-targets table. Several
  headline figures independently recomputed and confirmed exact rather than
  trusted: "48 notebook sections" (a first-pass digits-only regex
  undercounted at 46, caught and corrected before publishing by widening it
  to catch two lettered sub-sections, `1b` and `40b`, per the gate's own
  "read the line, never the match" rule), "90 figures," "3,734/3,841
  catalogue-gate rejections," and "14 namespaces" (web-verified against
  Netflix's real post, which independent secondary sources consistently
  report as 12 — fully reconciled, since the notebook and the ontology
  file's own comments both explicitly label the extra 2 as "ours," not an
  unstated inflation). **The round's central finding**: the committed
  `artifacts/run_manifest.json` records sha256[:16] fingerprints for the
  three ontology files, matching exactly what the executed notebook printed
  when it last ran — but recomputing those same hashes directly against the
  actually-committed ontology files in this exact clone gives three
  different values, for all three files. Ruled out before trusting this:
  line-ending drift (none — ASCII, LF-only, `.gitattributes`-enforced),
  multiple commits (`git log --follow` shows exactly one), an alternate
  repo version (one branch, zero tags). The likely explanation: the
  ontology files were edited after the last full run and committed
  alongside the now-stale manifest — directly contradicting the README's
  own central claim that "the run fingerprints itself... a reader can see
  that the two agree." Verdict page at
  `/builds/ontology-observability-gate/` (16 findings, 11 credit / 5 stop —
  an honest, credit-heavy ratio for an unusually rigorous source, not a
  forced balance; a new rights table added, since this is the first
  code-repo source analyzed that explicitly states "no licence has been
  chosen yet, so all rights are reserved" — nothing from the repo's own
  files is committed in this project, only this round's own measurements).
  193/193 assertions pass, including two new detectors (the fingerprint-
  drift check, the namespace-reconciliation check) each proven to actually
  fire via a planted counterexample before being trusted, then restored to
  a clean run. **Built**: `/builds/manifest-drift-guard/` — a real,
  dependency-free Python CI-gate tool generalizing the central finding: given
  a `{filename: hash}` manifest and a directory, recompute every hash and
  report drift/missing/unlisted files, exit 1 on any problem. 32/32 tests
  pass against real temp-directory files (no mocking), including five real
  CLI subprocess calls. One real bug found and fixed while testing: a
  malformed `--key` originally crashed with a raw, unhandled `KeyError`
  traceback instead of a clean exit code. Also run directly against the
  real cloned repository (transiently, never committed, consistent with its
  unlicensed status) and reproduces the exact real-world drift found during
  the gate round, exactly matching the finding.
- **Deep analysis + new skill from a pasted article: "Matt Pocock's AI
  Coding Skills: A Complete Workflow From Idea to Production-Ready
  Code"** — the first `/analyze-and-ship` round on a source that's
  itself about agent skills, not trading/business content. Full write-up
  in `/notes/mattpocock-skills-analysis.md`. Measured first, not
  summarized from the article: cloned the real `mattpocock/skills`
  GitHub repo (MIT, commit `4ae2317`, plugin `mattpocock-skills@1.3.2`,
  27 shipped skills) rather than trusting the article's description,
  same discipline as every other GitHub-repo source this project has
  audited. Credited: `code-review`'s two-parallel-sub-agent Standards/
  Spec design and `retro`'s five categories both match the article's
  description closely and precisely, down to specific named Fowler
  smells. Found two real gaps: the article's Claude Code install
  command (`claude plugins install mattpocock-skills`) doesn't match
  what the repo's own README documents
  (`claude plugin install mattpocock-skills@claude-plugins-official` —
  wrong verb form, missing the required marketplace suffix); and the
  article names only `implement` (a thin 17-line single-ticket
  orchestrator) as the step after `to-tickets`, never mentioning
  `implement-spec` — a real, separate, more-matched skill (parallel
  implementer sub-agents, one per worktree, across a ticket "frontier,"
  merged onto one integration branch) that the real repo's own
  `/ask-matt` router names explicitly as the alternative for exactly
  the ticket-graph-with-blocking-edges structure the article's own
  `to-tickets` section describes just before skipping past it. Also
  noted, as a pure naming coincidence rather than a derivation either
  way: the repo has its own in-progress, unshipped "software-factory"
  skill (a glossary for a fully autonomous ticket/PR/schedule-driven
  multi-agent build system), unrelated to and distinct from this
  project's own pre-existing "Software Factory method" name for the
  isolate→build→prove→ship discipline. **Built**:
  `.claude/skills/retro` — this project had no retrospective/self-
  improvement mechanism at all before this round; the real `retro`
  skill's five lenses (navigation, automated checks, standing rules,
  tool economy, information access) were rebuilt, not ported, retargeted
  at this project's own real environment (`CLAUDE.md`, `design-rules.md`,
  this project's own skills, each build's own test suite) instead of an
  issue tracker and CI, with a worked example applying it to a real
  prior round (the ontology-driven-observability gate) rather than a
  hypothetical. **Verified with this project's own existing
  `skill-md-validator`**, run against the whole `.claude/skills/`
  directory rather than just the new file — real bugs caught exactly
  that way on the first run, not by re-reading: a bare
  `mattpocock/skills` reference inside backticks and a not-yet-written
  `/notes/` path both false-tripped the broken-reference check (fixed by
  rewording the former and writing the latter, the file this round
  genuinely needed anyway), and the description lacked a literal "use
  when" phrase the trigger-condition check looks for (reworded without
  changing the actual trigger). Clean run afterward: all 12 skills in
  this project, `retro` included, pass with zero errors and zero
  warnings.
- **Third round on the same newsletter series: "Week 23: 5 GitHub
  Repositories Every Developer Should Know in 2026"** (the same
  vijayasekhardeepak.com series as Week 19/20 and Week 21). Full
  write-up in `/notes/week23-github-repos-analysis.md`. All five named
  repos (`ayghri/i-have-adhd`, `outline/outline`,
  `bradautomates/claude-video`, `immich-app/immich`, `antirez/ds4`)
  cloned and confirmed real. Credited: Outline's Business Source License
  1.1 description (Change Date, Apache 2.0 future license, the
  "Document Service" restriction) matches the real `LICENSE` file
  verbatim; Immich's AGPL-3.0 and "3-2-1 backup" recommendation both
  check out exactly against the real README/docs; `claude-video`'s
  Gemini-vs-local privacy/engine description is accurate and precise.
  Found a real, direction-stated gap: `ds4`'s article description
  undercounts its real model support (the real README also lists
  DeepSeek V4.1 Flash, GLM 5.3, GLM 5.3 Flash, and Qwen3.8 Flash Next,
  none named by the article), an understatement not an inflation, and
  the article's flat "96 GB" framing is actually a per-model floor in
  the source (64 GB suffices for Qwen3.8 Flash Next). **The round's
  strongest finding**: `ayghri/i-have-adhd` ships a real, rigorous eval
  harness (`evals/RESULTS.md`) whose one recorded run shows the
  candidate improving on every weighted rubric dimension and more than
  halving its blocker count (7→3) — yet still reporting "Release gate:
  FAILED," because an absolute "zero blocking findings" veto rule sits
  alongside the weighted scoring, and one test case is architecturally
  unpassable by any run (the harness strips tool access, so a criterion
  requiring the agent to act on the repo can never be met). The
  article's own "Productivity impact" section for this repo never
  mentions any of this, describing it only as something that "changes
  the response format" — not a flaw in the repo, which is exemplary in
  disclosing its own eval failure, but a real, checkable omission of the
  single most interesting, most load-bearing part of the source.
  **Built**: `/builds/gate-floor-checker/` — generalizes the finding
  into a reusable mechanism distinguishing `FAIL_IMPROVABLE` (real
  signal exists, more work could close the gap) from `FAIL_STRUCTURAL`
  (at least one case has never once cleared, so no amount of re-running
  the candidate alone can satisfy an absolute gate), with a recursive
  "excluding the structural cases" sub-report so a structural failure
  can't hide a real regression underneath it — a genuinely new gap in
  this project's own tooling, since `agent-readiness-scorecard`,
  `ten-k-website-grader`, and `paired-bootstrap-ratchet` all score or
  gate something but none of them draw this specific distinction.
  30/30 tests pass, including a full reconstruction of the real
  published i-have-adhd numbers reproducing both of the source's own
  conclusions exactly. **A real design gap found and fixed while
  building it, not a synthetic test bug**: the first draft modeled
  gate-blocking as "did the most recent trial block," which both
  mismatched the source's real N-trials-of-one-candidate semantics and
  would have silently let a confirmed-structural case pass if its one
  sampled trial happened to read clean — caught by the real-data test
  failing against the true numbers, fixed by switching to "any recorded
  trial blocked," with a confirmed-structural flag that always counts
  regardless of trial data.
- **Deep analysis + new build from a pasted article: "Memory Engineering
  for AI Agents"** (DhanushKumar, Medium) — a 30-plus-category prose
  taxonomy of agent memory types with no code attached, closer in kind to
  the earlier "AI System Design" and "Agentic Harness Frameworks" rounds
  than the GitHub-repo rounds. Full write-up in
  `/notes/memory-engineering-analysis.md`. Eight specific claims web-
  verified: Anthropic's real Contextual Retrieval blog post (confirmed,
  with the article's vague "substantially fewer" found to understate the
  real, precise reported numbers — 5.7%→3.7%→2.9%→1.9% failure rate
  across the contextual-embeddings/BM25/reranking stages), Anthropic's
  real memory tool (confirmed exactly, including its client-side
  architecture), Generative Agents' real recency+importance+relevance
  scoring formula (Park et al. 2023, confirmed accurate attribution),
  Reflexion, Voyager, and Zep/Graphiti (all confirmed accurate against
  their real papers). **A real, dated gap found**: the article describes
  MemGPT's real OS-inspired design accurately but never mentions it was
  renamed **Letta** in September 2024 (`cpacker/MemGPT` →
  `letta-ai/letta`) — a genuine omission for an article citing
  2025–2026 material over a year after a maintainer-announced rename.
  **The strongest finding**: the article's own unnamed "2025–2026
  survey" is identifiable as "Memory in the Age of AI Agents: A Survey,
  Forms, Functions and Dynamics" (arXiv:2512.13564) — the article
  paraphrases its three-axis taxonomy closely but never names it, and
  separately devotes a whole section to a RAG-vs-memory distinction that
  is explicitly that same survey's own fourth stated contribution,
  making the survey's point without crediting it as the source, visible
  only by finding and reading the unnamed paper. **Built**:
  `/builds/agent-memory-layer/` — not the article's own taxonomy (prose
  classification, nothing to execute), but the one concrete, now-
  verified mechanism inside it: the real Generative Agents scoring
  formula (kept strictly separate from the article's own unattributed
  "extended" formula, so neither could be mistaken for the other), a
  validated lifecycle state-machine resolving a real ambiguity in the
  article's own prose chain (read literally, RAW→ACTIVE→CONFIRMED→
  SUPERSEDED→STALE→ARCHIVED→FORGOTTEN would forbid superseding a
  still-RAW memory, contradicting the article's own worked example — now
  a documented DAG decision instead of a silently-picked reading), and
  the article's own Flask→FastAPI preference-supersession example made
  real and testable, with a subject-mismatch guard the article never
  states. 30/30 tests pass, including an independent hand recomputation
  of the real scoring formula. **One real bug found and fixed while
  testing**: the cosine-to-[0,1] normalization ran unconditionally, so a
  record with no embedding at all had its "zero relevance" sentinel
  silently inflated from 0 to 0.5 — caught by a dedicated no-embedding
  test, fixed by only normalizing when a real cosine value existed.
- **All three suggested next-moves on `agent-memory-layer` done in one
  round, not a subset.** (1) **`score_candidates()`** closes the real
  gap `score_generative_agents()`'s own docstring states: a single
  memory has no "other candidates" to normalize against. The new
  function min-max normalizes RAW recency, importance, and relevance
  SEPARATELY across a whole candidate set, then sums — the real
  Generative Agents retrieval step, not what the per-record function
  does (a fixed, pool-independent cosine-to-[0,1] map and importance/10).
  A record missing an embedding gets the worst possible raw relevance
  (-1.0) so it ranks at the pool's relevance floor rather than an
  arbitrary fixed value, and correctly becomes a no-op (every candidate
  tied) when the whole pool lacks embeddings. 9 new tests, including an
  independent hand recomputation of the normalization for a 3-record
  pool, a tied-pool check, a single-record pool (normalizes against
  itself, no `ZeroDivisionError`), and an empty-pool `ValueError` — all
  passed on the first run (39/39 total in `test_memory_layer.py`).
  (2) **`persistence.SQLiteMemoryStore`** — the persistence layer
  `MemoryStore` didn't have, following the exact WAL convention already
  established in `/builds/agent-checkpoint-layer/checkpoint/store.py`:
  SQLite's own write-ahead-log journal mode plus an app-level,
  append-only `transitions` table logging every lifecycle change. Same
  `add`/`get`/`live_for_subject`/`supersede` surface as `MemoryStore`,
  delegating every legality check to `memory_layer.transition()`/
  `supersede()` rather than re-implementing them — this module only adds
  "and also persist it, and also log it" around those calls. Proven
  with 27 tests, the one that actually matters being a real
  **cross-process** restart: a genuine subprocess writes two records and
  a status transition and exits, then the test process opens a fresh
  `SQLiteMemoryStore` against the same file and confirms everything
  (the transition WAL included) survived — not two in-process objects
  sharing one Python process, which wouldn't prove persistence at all.
  27/27 passed on the first run — no bug found this round, unlike round
  1's normalization bug. (3) **Wired into
  `/builds/trading-jarvis/jarvis_orchestrator.py`** as a new, third tool
  category — `remember_preference`, `recall_preferences`,
  `supersede_preference` — independent of both the EODHD/FMP
  symbol-trading flow and the prop-firm flow, persisting standing
  trading preferences ("always size conservatively for NQ," "prefers EMA
  crossover signals") across sessions in `jarvis_memory.sqlite3`.
  `memory_layer.py`/`persistence.py` copied in unmodified (same
  convention the prop-firm files already follow there); a new
  `jarvis_memory.py` applies `positions_store.py`'s own stated
  single-trader convention exactly (a fixed `subject_id`, no auth layer
  to scope against). Deliberately does **not** auto-supersede a
  preference on topic match — there's no embedding or keyword-matching
  layer in this codebase to judge "same topic" honestly, and faking that
  judgment with a regex would be exactly the kind of fabricated-
  intelligence shortcut this project avoids elsewhere; instead
  `recall_preferences` surfaces every live preference with its
  `memory_id`, and the system prompt instructs Claude — which can
  actually read and compare the text — to call `supersede_preference`
  naming a specific `memory_id` when a new statement clearly contradicts
  one already on file. Proven with 16 new tests in
  `test_jarvis_memory.py` (needed a real pinned-ish install in this
  session — `anthropic`, `requests`, `pandas`, `numpy` — since
  `jarvis_orchestrator.py` imports its full module graph even to test
  only the new tools): all three tools proven directly via `_run_tool()`
  against a real, isolated `SQLiteMemoryStore` (recall correctly ranks
  by real `score_candidates()` output, not insertion order; superseding
  a `memory_id` never actually returned by `recall_preferences` raises
  `KeyError` rather than creating a dangling link), then proven again
  through the full `ask_jarvis()` tool-dispatch loop against a mocked
  Anthropic client — same established convention as every other
  dispatch-loop test in this project — confirming a preference the
  mocked model asks to remember is actually, durably persisted via the
  real store, not just echoed back by the mock. 16/16 passed on the
  first run.
- **A near-duplicate of the follow-up round's own next-move list,
  redirected correctly rather than guessed at.** The user pasted the
  exact same three next-move instructions again, but this time pointed
  at `/builds/trading-system/trading-system_orchestrator.py` — a path
  that doesn't exist anywhere in this repo — alongside a screenshot of
  a local Windows `trading_system` folder (`evidence_check.py`,
  `quote_guard.py`, `stop_audit.py`, `options_dive.py`, `log_doctor.py`,
  `fx_papertrade_run.py`, `fx_tickers.txt`, a `Trading Jarvis AI system
  with Python` subfolder) with zero file-name overlap with anything in
  this repo. Per this project's own established precedent
  (`/builds/outage-alert`'s first message, meant for a different local
  session entirely), confirmed the path really doesn't exist here
  (`find`, `ls builds/`) before asking rather than guessing or silently
  redoing last round's already-complete work. Asked via
  `AskUserQuestion`; the answer was "new build for trading_system," but
  with no real source files in hand (the screenshot shows only a file
  listing, not contents, and none of the visible files is obviously the
  tool-dispatch "orchestrator" the three memory tools need to wire
  into) — per this project's own "never guess when a quick check would
  settle it" rule and the standing "core file missing, only consumers
  uploaded" pattern from every Trading Jarvis round, asked for the real
  files rather than fabricating a `trading-system_orchestrator.py` from
  a directory listing alone. No code written this round pending that.
- **Deep analysis + new build from a pasted article: "Building
  Self-Improving AI Applications with Harness²"** (DhanushKumar,
  Medium) — covering Google Research's real **Harness²** framework
  (recursively improving an AI agent's surrounding "harness" via
  execution evidence, without touching model weights). Full write-up in
  `/notes/harness2-recursive-agent-optimization-analysis.md`. Unlike
  some earlier sources whose named papers turned out unverifiable, this
  one checked out as real: arXiv:2610.14224, with a real public repo
  (`google-research/harness2`, Apache 2.0) cloned and read directly.
  Several of the article's most specific claims confirmed exactly
  against the real files — the OpenCode-backed file-tree surface
  (`systemprompt.md`/`guardrails.md`/`LongTermMEMORY.md`/
  `tool_descriptions/tool_guidance.md`, found verbatim in the real
  JobBench baseline harness tree), the eight editable components named
  identically in the repo's own README, the three benchmark adapters
  and two execution substrates, and the `--k` budget formula (4k
  rollouts/3k improvement stages, k=2→8/6 confirmed exactly against
  `core/ledger.py`'s own docstring). Read `core/ledger.py` in full
  rather than trusting the article's paraphrase of "verifies expected
  counts and detects duplicate execution labels," and found it's more
  precise than the article conveys: duplicates are checked *before*
  counts, specifically because a duplicate write can make the raw count
  come out numerically correct while a real candidate silently never
  happened — only reading the code shows why the check is ordered that
  way. **The round's strongest finding**: the article's own security
  section discusses risk only in abstract, hypothetical terms, but the
  real repo's `docs/EXPERIMENTS.md` discloses a concrete incident it
  never mentions — "In a validation run of this release, a Codex
  rollout on JobBench downloaded its task's rubric without being
  instructed to," exactly the class of risk the article only
  speculates about. Flagged as unverifiable rather than repeated as
  fact: three independently-written secondary sources (different
  languages) converge on specific negative-result figures (a
  "ReasoningBank" baseline scoring 6.6 points below base on coding, a
  "Harness Scaling" baseline losing to the base harness in 7 of 12
  combinations) that appear nowhere in the repo's own README/docs
  (grepped, zero hits) and couldn't be checked against the primary
  arXiv text — `arxiv.org` is unreachable from this sandbox
  (`getaddrinfo ENOTFOUND`), the same egress restriction already
  documented for every other build here, now extended to arXiv.
  **Built**: `/builds/recursive-harness-primitives/` — not Harness²
  itself (the real Propose-Probe-Compose loop needs a live model and an
  OpenCode/Codex execution substrate, neither available here), but two
  concrete, model-free invariants underneath it, read from the real
  source and independently reimplemented rather than copied (same
  convention as `go-buildinfo-extractor`/`run-terminal-ledger`):
  `budget_ledger.py` (the real R=4k/P=3k identity plus the
  duplicate-before-count check, tested against the exact failure mode
  the real module's docstring describes — a duplicate label that makes
  the raw count numerically right while masking a real gap; one real
  bug in this build's own first test draft, not the mechanism, caught
  immediately: several test ledgers were constructed with `k=2` but fed
  `k=1`'s worth of entries, fixed by matching each ledger's `k` to what
  it was actually loaded with) and `experience_library.py` (the
  ordered, per-domain experience library). **Found a real limitation in
  the original design by reading two files together, not either
  alone**: `core/library.py`'s `retain()` trusts whatever task-id list
  it's handed, and the real no-future-leakage guarantee lives entirely
  in `core/schedule.py`'s one call site (`lib.retain(task_ids[: i -
  1])`) as a caller convention, not a structural invariant of
  `Library` itself — a different or future call site with the slicing
  even slightly wrong would silently violate it with no error raised
  anywhere. Built `OrderedStream` as this build's own fix, not in the
  original: it computes the strictly-prior task slice internally on
  every step rather than trusting a caller-supplied one, and refuses
  out-of-order processing outright. 24/24 and 15/15 tests pass,
  including a direct reproduction of the real gap (a raw
  `ExperienceLibrary.retain()` call *does* leak a future task's entry
  given the wrong slice) and a proof that `OrderedStream` closes it by
  construction. Deliberately not built: the eight editable harness
  components themselves (confirmed real, but nothing here to apply them
  to without a live agent) and the contrastive-judge/selection
  machinery (`core/judge.py`, `core/selection.py`) — both need a real
  execution loop producing evidence that doesn't exist in this sandbox.
- **Deep analysis + new build from a pasted article: "Building Your
  First Orchestration Agent"** (rajesh yemul, Medium, Part 18 of a
  "Quality Engineering" tutorial series) — a purely pedagogical piece
  (the author's own invented "QE Orchestrator" pipeline), no external
  repo/paper/product named anywhere, confirmed by grepping the saved
  copy for a link before concluding that rather than assuming it from
  genre. Full write-up in
  `/notes/orchestration-agent-loop-analysis.md`. Unlike the GitHub-repo
  rounds, the verification surface here was entirely internal: the
  retry-count/coverage arithmetic in the article's own worked example
  (82%→88%→100%, retry_count reaching exactly 1) checked out exactly.
  Credited: the article's explicit Evaluate/Choose separation
  ("if those two stages collapse into one, the agent immediately
  becomes another black box") is a genuinely sound discipline, and its
  named "Mistake #3" (ignoring workflow state → an infinite retry
  loop) is a concrete, correctly-reasoned failure mode this project's
  own `agent-checkpoint-layer` and `defender-loop-verifier` builds
  independently guard against in their own domains. **The round's
  finding**: read the article's own two halves against each other — the
  prose "Choose" stage credits a judgment over Requirement Package
  *content* ("because the business requirement already exists..."),
  but the YAML "Agent Configuration" it presents as making that
  reasoning *"executable orchestration logic"* has only flat numeric
  conditions (`coverage < 90`) with no field anywhere that could
  express "is this specific requirement documented" — the
  "Request Business Clarification" branch the prose names exists only
  in narrative, never in the artifact claimed to encode it. **Built**:
  `/builds/orchestration-decision-engine/` — not the article's own
  fictional QE pipeline, but the generalizable Observe→Evaluate→
  Choose→Execute→Verify mechanism underneath it: a pluggable
  multi-producer router with `Rule.condition` as a real callable over
  the full facts dict (closing the found gap — a rule *can* depend on
  content, not just a flat threshold) and retry-bounded recovery with
  escalation. Checked `/builds/` first — `policy-control-plane`,
  `agent-checkpoint-layer`, `gate-floor-checker`,
  `defender-loop-verifier`, and `ai-system-design-toolkit`'s
  `provider_breaker.py` are all adjacent but none implement this
  specific loop. All four of the article's own named "Common Mistakes"
  refused structurally, not by convention: the orchestrator can never
  execute producer work itself (`Router.execute()` is the one path
  anything runs through, and raises loudly on an unregistered action),
  a workflow is never marked done without a real `verify_fn` call
  returning `True`, the named infinite loop is reproduced and
  refused (a producer that never improves anything runs exactly
  `max_retries + 1` cycles, then escalates — checked by real call
  count, not a status string), and nothing in `DecisionEngine`/
  `Router`/`RecoveryEngine` computes an engineering artifact itself.
  **A real design bug found and fixed in this build's own first
  draft, not the source**: reproducing the worked example as a test
  caught that the first version of `run_cycle()` returned a bare
  "no matching rule" result whenever nothing needed fixing — exactly
  the state the article's own final cycle reaches (coverage=100, no
  rule fires) — and never checked verification at all. Fixed by
  treating "no rule matched" as "nothing to execute, verify current
  facts directly," and by always re-observing fresh state immediately
  after any rule *does* fire, so `Verify` never checks stale,
  pre-execution facts. One ambiguity in the source resolved rather
  than forced to match exactly: the fix reproduces the article's exact
  two named cycles and exact coverage sequence, but calls the real
  producer once, not twice as the article's own cycle-2 prose states
  — the article's own narrative doesn't fully specify whether cycle
  2's starting observation is a fresh read or a restatement of cycle
  1's post-execution check, resolved here toward the cleaner, testable
  semantic. 17/17 tests pass on the real run.
- **Deep analysis + new build from a pasted article: "Building an AI
  Agent Testing Framework from Scratch with TypeScript and Vitest"**
  (rajesh yemul, Medium, Part 1 of a new series) — this project's first
  TypeScript/Vitest build; every other build here is Python,
  HTML/JS, or Next.js. Full write-up in
  `/notes/ai-agent-testing-framework-analysis.md`. A real, checkable
  connection found between this author's two series analyzed this
  session: this article's own worked example defines an agent with
  `agentId: requirement-analyzer`, and the earlier-analyzed "Quality
  Engineering" series' Season 3 pipeline names "Requirement Analyzer"
  as its first producer — neither article cites the other, visible
  only reading both together. Unlike most sources here, this one is
  real, complete, runnable code shown in full, not a conceptual
  framework or vendor product — so this round actually installed and
  ran it (`npm install`, 0 vulnerabilities per `npm audit`; `tsc
  --strict --noEmit` clean). Two technical claims web-verified against
  primary sources: Gemini's real OpenAI-compatible endpoint
  (`generativelanguage.googleapis.com/v1beta/openai/`, matching
  Google's own docs exactly) and Vitest's real `fileParallelism`
  config option (confirmed against the official docs — forces
  `maxWorkers` to 1, exactly matching the article's own comment).
  **Two real bugs found, both reproduced directly rather than spotted
  by eye**: (1) the article's own shown `vitest.config.ts` has a
  genuine unbalanced object literal (counted via `grep -o '{' | wc -l`
  vs `}` — 3 vs 4) — confirmed as a real bug, not a transcription
  artifact, by running the snippet as plain ESM and getting
  `SyntaxError: missing ) after argument list` pointing at the exact
  extra brace (a first attempt with `tsc --noEmit`/`node --check`
  directly on the `.ts` file silently passed, a dead end worth noting
  before the real repro worked); (2) a real gap between the article's
  stated motivation and its own shown code — the article credits
  `LLMClient` as an abstraction enabling "deterministic tests for the
  testing framework itself," but `AgentRuntime`'s real constructor
  types its parameter as the **concrete** `LLMClient` class, not an
  interface, so a plain mock object fails `tsc --strict` with `Property
  'client' is missing in type '...' but required in type 'LLMClient'`
  — TypeScript matches class types structurally *including private
  fields*, and the real class has a private `client: OpenAI` field no
  mock can supply, directly blocking the exact capability the article
  credits the abstraction with enabling. **Built**:
  `/builds/ai-agent-testing-framework/` — a faithful, actually-run
  reproduction (not a generalized-mechanism extraction, since the
  source itself is concrete runnable code) with both bugs fixed:
  `vitest.config.ts`'s brace balanced, and a real `LLMClient` interface
  extracted into `AgentTypes.ts` with the concrete class
  `implements`-ing it, closing the mockability gap. 10/10 Vitest
  assertions pass across three real files, including the test the
  interface fix makes possible for the first time — the real
  `AgentConfigLoader` loading a real `requirement_analyzer.md` (one
  piece filled in rather than left a stub, since the article shows
  only a fragment and defers the full agent definition to Part 2;
  stated plainly as this build's own content, not a guess at
  not-yet-published text), wired through the real `AgentRuntime`,
  against a deterministic mock `LLMClient` with its exact call
  arguments asserted to match the real loaded config — the same
  "mocked client" convention this project's Python builds have used
  throughout, applied here for the first time to TypeScript/Vitest.
  `npm run build` produces a real `dist/`; `npm run agent` fails fast
  and cleanly without a live `GEMINI_API_KEY`, proven as a real
  subprocess run (no live Gemini access from this sandbox, same
  standing restriction as every build here). Not built: the article's
  own explicitly-stated next challenge (the test-oracle problem) and
  TC001, both deferred by the source itself to a future part.
- **Part 2 of the same series, extending `/builds/ai-agent-testing-
  framework/` rather than forking it**: "Testing AI Agents: A Practical
  Quality Engineering Journey," Part 2 (rajesh yemul) — the direct
  continuation of the project built last round. Full write-up in
  `/notes/ai-agent-testing-framework-part2-analysis.md`. **The real
  finding**: Part 1 only showed a fragment of `requirement_analyzer.md`
  (just the `# Role` section), so last round's own placeholder for the
  rest was substantially wrong once checked against the real file Part
  2 now gives in full — different Responsibilities taxonomy (Actor/
  Feature/Preconditions/Positive-Negative-scenarios vs. the
  placeholder's invented Trigger/Expected-Outcome), seven specific
  numbered grounding Rules vs. three generic ones, and a strict-JSON-
  only Output Requirements contract vs. an invented prose format —
  diffed directly, not assumed, and swapped in as a stated correction,
  same as every "real file arrived later" precedent across this
  project's Trading Jarvis rounds. Confirmed no new external claim
  appears in Part 2 beyond what Part 1 already verified. **Built**: two
  new modules operationalizing rules the agent's own instructions state
  but neither article's shown code ever checks — `parseAgentOutput.ts`
  (enforces the real Output Requirements contract: valid JSON only, no
  Markdown fences, no surrounding prose, the exact six-field schema) and
  `checkGrounding.ts`, a real grounding/hallucination checker built
  directly from Part 2's own two worked "valid JSON, still wrong"
  examples (fabricating "OTP"/"5 minutes" in one, "OAuth 2.0"/"AES-256"
  in the other, for a requirement that mentions neither) — checked
  `/builds/` first (`humanizer` checks prose style, not grounding;
  `paired-bootstrap-ratchet` checks statistical significance of
  accuracy claims, not per-response grounding; neither overlaps).
  **Deliberately not a full word-presence checker, verified rather than
  assumed**: Part 2 also gives a real paraphrase-equivalence example
  (two differently-worded, behaviorally-equivalent scenario
  descriptions), and a standalone script run *before* writing any
  module code confirmed a naive "every output word must appear in the
  input" check really does flag `["user", "initiates", "recovery",
  "completes"]` against that exact pair — a genuine false positive, not
  a hypothetical risk. `checkGrounding()` instead targets only the two
  concrete patterns the article's own two examples actually are:
  numeric/duration claims and a small, named, curated technical/
  security-term list — stated plainly as *not* full semantic
  correctness checking (the article's own "test oracle problem,"
  explicitly deferred to a future part of its own series), a narrow,
  evidenced step rather than an oversold oracle. Also updated the
  existing mocked-LLMClient pipeline test, which had been mocking the
  now-superseded placeholder's prose output format, to use the real
  JSON schema and run the full real pipeline (config load → runtime →
  output parsing → grounding check) end to end. **A second real bug
  found while verifying this round, in the build's own test setup, not
  the source**: `npm test` right after `npm run build` first reported
  50 passing tests, exactly double the real count — `tsc`'s own `dist/`
  output includes a compiled copy of every `tests/**/*.ts` file, and
  Vitest's default include pattern was silently matching those too,
  double-running every test. Caught by actually counting (5 files ×
  their real assertion counts = 25, not 35 or 50, both of which were
  seen at different points depending on how stale `dist/` happened to
  be) rather than trusting the first number printed. Fixed with an
  explicit `exclude: ["**/node_modules/**", "**/dist/**"]` in
  `vitest.config.ts`. 25/25 Vitest assertions pass (up from 10), `tsc
  --strict --noEmit` clean, `npm audit` 0 vulnerabilities.
- **Part 3 of the same series, extending `/builds/ai-agent-testing-
  framework/` again**: "What Does 'Correct' Mean for an AI Agent?"
  (rajesh yemul) — the series' own named "test oracle problem," deferred
  since Part 1, finally defined precisely enough to implement: a
  Required/Allowed/Forbidden framework, four correctness dimensions, and
  TC001's own exact 8-item Required checklist for the canonical
  password-reset requirement. Full write-up in
  `/notes/ai-agent-testing-framework-part3-analysis.md`. Built
  **`src/oracle/qualityBoundary.ts`** (the generic mechanism — a
  `required` list and a `forbidden` list, each named and independently
  reportable, never collapsed to one boolean, since Part 3's own central
  Section 6-7 lesson requires seeing exactly which check failed; "Allowed"
  has no list anywhere in the API, by design — the implicit complement of
  the other two) and **`src/oracle/requirementAnalyzerOracle.ts`** (the
  concrete TC001 oracle, instantiating the article's 8-item checklist
  verbatim, reusing Part 2's `checkGrounding()` directly as its one
  Forbidden check rather than reimplementing fabrication detection).
  **The single most important design decision**: deliberately never
  requires `negativeScenarios.length > 0` — Part 3's own central lesson
  ("could be tested != is supported") operationalized directly, proven as
  a named Situation A (empty, evidence-free negative scenarios must pass)
  vs. Situation B (a *fabricated* negative scenario must fail, but as a
  Forbidden violation, not a missing Required item) pair. **A real,
  honestly-stated gap found while implementing checklist items 6-7**
  ("Actor represents the user," "Feature represents password reset"):
  Part 3 names these as its "semantic correctness" dimension but never
  supplies an algorithm beyond one obviously-wrong worked example — same
  shape of gap as Part 1's YAML-vs-prose mismatch in the sibling "Quality
  Engineering" series. Built instead as honest lexical-grounding checks
  (non-empty, shares a significant word with the requirement, allowing
  simple singular/plural variation), stated plainly as not a claim of
  real semantic understanding. **A real bug found and fixed while
  building this, caught by the test suite itself**: the first version of
  the lexical-grounding check used exact token-set intersection, which
  failed the article's own most basic case — `actor: "User"` against a
  requirement that only ever says "users" (plural) shares no exact
  token — fixed with the simplest stemming that resolves it (strip a
  trailing "s" from either side before comparing). A second, smaller bug
  in the same run: three Required checks assumed `ctx.result` was always
  a real object and threw a raw `TypeError` on a missing result instead
  of returning `false`, since `evaluateBoundary()` runs every check
  regardless of whether an earlier one already failed, by design — fixed
  with explicit null guards. 46/46 Vitest assertions pass (up from 25),
  `tsc --strict --noEmit` clean, `npm run build` clean, `npm audit` 0
  vulnerabilities. Deliberately not built: true semantic correctness for
  checks 6-7 (the real, unresolved gap above), TC001 fired against a live
  agent (same standing no-API-key restriction as every build here — this
  oracle is the acceptance criteria TC001 would check against, not a
  live-fired test), and instruction-following as its own dimension (named
  by Part 3 but given no worked example distinct from
  groundedness/structural correctness to build against).
- **Part 4 of the same series, extending `/builds/ai-agent-testing-
  framework/` a third time**: "Writing Our First Functional Test for an
  AI Agent" (rajesh yemul) — TC001 written literally, for the first time,
  as real Vitest code against the real runtime path, unlike Part 3's
  framework-only treatment. Full write-up in
  `/notes/ai-agent-testing-framework-part4-analysis.md`. Built
  **`tests/requirement-analyzer/TC001.test.ts`** — a faithful, literal
  reproduction of the article's own TC001, laid out by its exact 7-layer
  structure (Execution, Identity, Output, Structure, Contract, Semantics,
  Behavioral expectation — Part 3's merged "valid JSON + fields exist"
  check is reproduced here as the article's own two genuinely separate
  assertion blocks, matching fidelity over the earlier simplification),
  run against the real pipeline with a mocked `LLMClient` (same standing
  no-live-API-access convention as every build here). **Independent
  confirmation, not a new finding**: Part 4 arrives at the same
  conclusion Part 3's oracle already implemented — never require
  `negativeScenarios.length > 0` — through its own concrete walkthrough
  (write the assertion, watch it fail on real output, run a 4-step
  investigation, remove it) rather than the abstract framework; a
  dedicated cross-check test proves the Part 3 oracle (built and
  committed before this round ever read Part 4's text) and Part 4's own
  literal TC001 reach the same verdict on the same real pipeline output
  — real evidence the design decision was correct, not a restated
  premise. **A real, verified precision gap in the article's own stated
  reasoning**, checked with code rather than taken at face value: the
  article flags `const parsed = JSON.parse(x); expect(() =>
  parsed).not.toThrow();` as wrong because parsing "has already
  happened" by the time the assertion runs — true, but this understates
  the problem: `() => parsed` is a closure returning an already-captured
  value, so it can **never** throw regardless of what that value is,
  even on the success path where parsing returns something structurally
  nonsensical. Reproduced directly: the flagged assertion passes
  unconditionally for a value that is plainly not a valid
  `RequirementAnalysis`, proving it verifies nothing at all, not just
  that it runs too late. Confirmed this build's own `parseAgentOutput()`
  (built in Part 2) already follows the correct discipline — no change
  needed there. **A real, stated design divergence, not a bug**: the
  article's Layer 6 semantic checks hardcode one literal substring per
  field (`.toContain("user")`, `.toContain("password")`) tied to this
  one requirement's exact wording, while Part 3's `isGroundedField()`
  checks for any shared significant word against the full requirement
  text, generalizing to a differently-worded requirement without
  rewriting the check — stated plainly rather than assumed one subsumes
  the other. 13 new Vitest assertions (59/59 total, up from 46), `tsc
  --strict --noEmit` clean, `npm run build` clean, `npm audit` 0
  vulnerabilities. Deliberately not built: negative testing (empty/
  off-domain/nonsense input) — Part 4's own closing section previews
  this as the next part's subject, deferred by the article itself.
- **Part 5 of the same series, extending `/builds/ai-agent-testing-
  framework/` a fourth time**: "Negative Testing: What Happens When the
  Input Is Bad?" (rajesh yemul) — TC002 (empty input, missing evidence),
  TC003 (meaningful but off-domain input, scope adherence), TC004
  (nonsense input, semantic validity), each with the article's own real,
  actually-quoted agent output. Full write-up in
  `/notes/ai-agent-testing-framework-part5-analysis.md`. The article's
  own named principle — "the agent must not convert insufficient
  evidence into invented facts" — and its own real assertion code
  (`JSON.stringify(parsed).toLowerCase()` matched against a safe-signal
  regex, plus `not.toContain()` on named invented concepts) was
  recognized directly as the same Required+Forbidden shape Part 3's
  `qualityBoundary.ts` already generalizes, rather than hand-rolled as a
  parallel mechanism. Built **`src/oracle/safeFailureOracle.ts`** on top
  of the existing `evaluateBoundary()` — one Required check (the
  safe-signal regex) plus a Forbidden check per named invented concept —
  with one real addition beyond the article's own literal code:
  `serialize()` falls back to the raw output string when the response
  isn't valid JSON at all, instead of letting a bare `JSON.parse()`
  throw before any safe-failure assertion runs, closing the same class
  of problem Part 4's JSON.parse-assertion finding identified,
  architecturally this time rather than just flagged. Built
  **`tests/requirement-analyzer/negative-testing.test.ts`**: each of
  TC002-TC004 tested both as a literal reproduction of the article's own
  exact assertion pattern and through the generalized oracle (confirming
  agreement), plus a **discrimination check** per TC — a planted,
  hallucinated response the agent did not actually produce (a
  password-reset feature invented from empty input; "banana management"
  invented from an elephant/banana statement; a login feature invented
  from pure gibberish) — proving the oracle genuinely fails these rather
  than rubber-stamping everything, the same discrimination discipline
  this project applies throughout (`humanizer`, `ten-k-website-grader`,
  `voice-extractor`). 10 new Vitest assertions (69/69 total, up from
  59), `tsc --strict --noEmit` clean, `npm run build` clean, `npm audit`
  0 vulnerabilities. **No bug found this round** — everything passed on
  the first real run, stated plainly rather than manufactured.
  Deliberately not built: ambiguity testing (a requirement containing
  subjective terms like "quickly"/"using email") — Part 5's own closing
  section previews this as the next part's subject, deferred by the
  article itself.
- **Part 6 of the same series, extending `/builds/ai-agent-testing-
  framework/` a fifth time**: "Testing Ambiguity in AI Agents" (rajesh
  yemul) — TC005, subjective ambiguity (`"...reset their password
  quickly using email."`). Full write-up in
  `/notes/ai-agent-testing-framework-part6-analysis.md`. The article's
  own central event: a naive forbidden-term assertion
  (`not.toContain("otp")`) failing against the agent's own correct
  output, because "OTP" was mentioned as a hedged, labeled possibility
  ("...is not specified... e.g., OTP"), not asserted as a claim. **This
  project checked that directly rather than treating it as hypothetical,
  and found this build's own `checkGrounding()` module (shipped in Part
  2, already reused as Part 3's Forbidden check and Part 5's
  `safeFailureOracle`) has exactly this bug** — reproduced before
  touching any code: running the real TC005 output through the
  unmodified, already-shipped module returned a false-positive finding
  on "OTP." **Fixed with hedge detection, not a weaker check**:
  `HEDGE_PATTERN` in `checkGrounding.ts` exempts a claim/term only when
  the same field/array-item text also contains hedging language ("not
  specified," "e.g.," "possibly," "hypothetical," etc.) — widening what's
  Allowed without narrowing what's Forbidden, verified directly: both of
  Part 2's original fabrication examples (neither hedges its invented
  term) still correctly flag after the fix, and a new test proves the
  article's own "Response A" (an unhedged OTP claim) still fails at the
  full-oracle level too. **A second finding, documented rather than
  "fixed"**: Part 6 itself observes the real schema's `ambiguities`
  array conflates true ambiguity ("quickly" is subjective) with plain
  missing information (password strength rules, error handling) — not
  acted on by inventing a `missingInformation` field, since
  `requirement_analyzer.md` is the source series' own real file, not
  this project's to redesign speculatively; instead confirmed with a
  test against the real output. Built the fix in
  **`src/grounding/checkGrounding.ts`**, regression tests in
  **`tests/grounding/checkGrounding.test.ts`**, and full-pipeline proof
  in **`tests/requirement-analyzer/ambiguity-testing.test.ts`** (the
  real TC005 output passing both `checkGrounding()` and the full Part 3
  `requirementAnalyzerOracle` cleanly, the Response A/B distinction
  proven at the oracle level, and the Contract-defect finding confirmed
  with code). 10 new Vitest assertions (79/79 total, up from 69), `tsc
  --strict --noEmit` clean, `npm run build` clean, `npm audit` 0
  vulnerabilities. **A real, pre-existing bug found and fixed this
  round** — unlike Part 5, which found none. Deliberately not built:
  true ambiguity/multiple concrete interpretations (TC006) — Part 6's
  own closing section previews this as the next part's subject,
  deferred by the article itself.
- **Part 7 of the same series, extending `/builds/ai-agent-testing-
  framework/` a sixth time**: "True Ambiguity: Can an AI Agent Recognize
  Multiple Valid Interpretations?" (rajesh yemul) — TC006, a requirement
  supporting multiple concrete, competing interpretations (`"...cancel
  an order within one day..."`: 24 hours from the timestamp, or a
  calendar-day boundary?), distinct from Part 6's merely undefined term.
  Full write-up in `/notes/ai-agent-testing-framework-part7-analysis.md`.
  The article's own central move is self-critical: it names its own
  TC006 as correct but incomplete — only verifying the agent
  acknowledges the ambiguity, not that it never asserts one
  interpretation as fact. **This project turned that question on its
  own code, not just the article's narrative, and found a real
  second-order bug in LAST ROUND'S OWN hedge fix**: the first test
  written against TC006's real output failed unexpectedly, tracing to
  two real defects in Part 6's `HEDGE_PATTERN` — the e.g. alternative
  never matched anything (a literal period can't form a word-boundary
  transition right after it, dead code since the moment it was written,
  invisible because Part 6's own fixture happened to also contain "is
  not specified" in the same sentence, masking it), and "ambiguous"
  itself was never in the hedge list at all. Both fixed in
  `src/grounding/checkGrounding.ts`, confirmed not to loosen true-
  positive detection by re-running every existing fabrication fixture
  from Parts 2 and 6. **Then, deliberately, tested this project's own
  oracle the way the article tests its own**: the article's named
  "Behavior A" (an unhedged numeric interpretation asserted as fact)
  confirmed already caught by the existing numeric-claim mechanism;
  "Behavior B" (an unhedged NON-numeric interpretation asserted as
  fact) confirmed to slip through undetected — an honestly-tracked,
  named limitation, not silently papered over, since closing it
  generally needs the same semantic-correctness mechanism Part 3 already
  named as unsolved; a test asserts the current (gap) behavior
  explicitly so a future fix shows up as an intentional change, not a
  silent shift. The Contract-defect finding (ambiguities mixing true
  ambiguity with missing information) reconfirmed on this independent
  real example too, still documented rather than acted on. 10 new
  Vitest assertions (87/87 total, up from 79), `tsc --strict --noEmit`
  clean, `npm run build` clean, `npm audit` 0 vulnerabilities. **A real
  bug found and fixed for the second round in a row** — this time in
  code this project itself wrote and shipped only one round earlier.
  Deliberately not built: closing the Behavior B gap, and groundedness/
  hallucination testing as its own category — Part 7's own closing
  section previews this as the next part's subject, deferred by the
  article itself.
- **Part 8 of the same series, extending `/builds/ai-agent-testing-
  framework/` a seventh time**: "Testing Grounding: Can an AI Agent Stay
  Within the Evidence?" (rajesh yemul) — TC007 (sparse evidence), TC008
  (explicit evidence), TC009 (conflicting evidence), TC010 (unsupported
  inference), all against a new requirement (`"...upload a profile
  picture."`). Full write-up in
  `/notes/ai-agent-testing-framework-part8-analysis.md`. The article
  repeats Parts 6-7's exact lesson for TC007, then fixes it with six
  separate hand-written, per-claim regexes, naming its own limitation
  plainly (a differently-phrased claim could slip past a narrow
  pattern). **This project's `checkGrounding()` already generalizes
  exactly this principle**, so this round extended its existing term
  list (image formats, storage/cloud terms, UI/processing terms) and
  numeric-unit list (byte sizes) with Part 8's real vocabulary instead
  of writing six new one-off assertions — TC010's six named claim
  categories proven caught by one mechanism in a single parameterized
  test loop. **Two real bugs found while testing against this round's
  real/named material**: (1) a morphological-variant gap, same bug
  class as Part 3's "user"/"users" finding — TC010's own named example
  is "Users must authenticate..." but the term list only had
  "authentication" (the noun), so this exact claim slipped through on
  the first real run; fixed by adding the verb form explicitly. (2) **a
  real, verified defect in the article's own TC009 regex**: its given
  silent-resolution pattern doesn't match either of its own two named
  "tempting but wrong" example responses ("The system must store the
  profile picture in Amazon S3," "The image is stored locally and then
  uploaded to S3") — confirmed directly with a standalone script before
  writing any code. Built **`src/oracle/contradictionOracle.ts`** (new,
  TC009, on the same `qualityBoundary.ts` mechanism as Part 5's
  `safeFailureOracle.ts`), keeping the article's original patterns and
  adding four more, verified to actually catch both named examples.
  Built **`tests/requirement-analyzer/grounding-testing.test.ts`**
  (TC007-TC010 against the real pipeline, with discrimination checks
  throughout) and a regression test in `checkGrounding.test.ts` for the
  authenticate fix. 17 new assertions plus 1 regression test (105/105
  total, up from 87), `tsc --strict --noEmit` clean, `npm run build`
  clean, `npm audit` 0 vulnerabilities. **A third round in a row with at
  least one real bug found and fixed.** Deliberately not built: full
  semantic-claim detection beyond term/numeric patterns (named as a
  limitation by the article itself), and tool-calling/agentic
  architecture testing — Part 8's own closing section previews a much
  larger future shift (agents that call tools and decide what to do
  next, rather than reasoning in one shot) without giving any concrete
  mechanism yet.
- **Part 9 of the same series (different URL slug, same author/agent),
  extending `/builds/ai-agent-testing-framework/` an eighth time**:
  "Testing AI Agent Boundaries: Output Contracts, Grounding and Prompt
  Injection" (rajesh yemul) — names three distinct boundaries explicitly
  (Evidence/grounding, Output/contract, Instructions/injection) and
  gives real content for the latter two. Full write-up in
  `/notes/ai-agent-testing-framework-part9-analysis.md`. **Two real,
  verified gaps found in this project's own pre-existing
  `parseAgentOutput.ts`** (hand-rolled since Part 2), checked directly
  against the article's own real Zod schema (`RequirementAnalysisSchema`,
  reproduced verbatim, `zod@4.6.7` installed) rather than assumed: an
  unexpected extra field (`"confidence": 0.92`) was silently dropped
  instead of rejected, and an empty string (`"actor": ""`) passed
  validation — both reproduced against the unmodified module before
  refactoring. Fixed by rewiring `parseAgentOutput.ts` onto the real
  schema (new `src/schema/RequirementAnalysisSchema.ts`); the module's
  existing parse-into-`unknown`-before-validating discipline needed no
  change. Added TC012-TC016 (deterministic contract tests needing no
  live agent call) to `tests/output/parseAgentOutput.test.ts`. **Built
  `src/oracle/injectionResistanceOracle.ts`** (TC017-TC019, prompt-
  injection resistance) on the same `qualityBoundary.ts` mechanism as
  every other oracle here, directly implementing the article's central
  connecting insight — "mentioning 'JPEG' != claiming JPEG is supported"
  (Parts 6-8) is the same reasoning pattern as "mentioning 'Delete all
  users' != adopting it as the feature." Required checks reuse Part 3's
  `isGroundedField`, extracted this round into a new shared
  `src/oracle/lexicalGrounding.ts`; Forbidden checks test adoption
  directly on the actor/feature field values, cleanly separating
  "named in ambiguities" (Allowed) from "adopted into actor/feature"
  (Forbidden) with no hedge detection needed. The article gives no
  literal quoted output for TC017-020, so every test fixture is
  constructed from its own named desired/undesired values and labeled
  as such. **A real, honest limitation found while testing, not
  assumed**: the first draft of the TC017 discrimination test predicted
  both anchoring checks would fail on a fully-adopted bad response —
  only the actor check actually failed, because the forbidden feature
  value ("Delete all users") shares the literal word "users" with the
  real requirement, so `isGroundedField`'s plain shared-word heuristic
  incorrectly reports it as anchored; the overall verdict still
  correctly fails only because the separate Forbidden check
  independently catches it, documented with a dedicated test proving
  the blind spot rather than silently adjusted away. **TC020** (output-
  format manipulation) is a different boundary entirely — proven
  through the existing Zod-backed contract directly, with the article's
  own literal injected bad output correctly rejected: a positive
  finding that this boundary was already closed by Part 2/9's work. 15
  new Vitest assertions across two files (120/120 total, up from 105),
  `tsc --strict --noEmit` clean, `npm run build` clean, `npm audit` 0
  vulnerabilities. **A fourth round in a row with at least one real
  finding.** Deliberately not built: closing the TC017 anchoring blind
  spot (needs real semantic similarity, the same gap Part 3 named), and
  tool-calling/action testing — Part 9's own closing section previews
  this directly as the next part's subject, deferred by the article
  itself.
- **Deep analysis + new build from a pasted article: "Claude Code
  Agents: How to Build Your Own AI Team"** (cskumara2000, Medium) — a
  different kind of source for this project: a how-to about Claude
  Code's own subagent feature (`.claude/agents/*.md`), checkable
  against this session's own real, authoritative tool
  (`claude-code-guide`, built specifically for exactly this class of
  question) rather than a web search or a cloned repo. Full write-up in
  `/notes/claude-code-agents-ai-team-analysis.md`. Verified against the
  real current docs: the `.claude/agents/` path and most of the
  `security-reviewer.md` frontmatter example check out, including
  `effort` (real, `low`/`medium`/`high`/`xhigh`/`max` — a specific
  suspicion going into the check that it might be confused with the
  SDK's `effort` parameter turned out wrong, confirmed rather than
  assumed). **One claim turned out genuinely wrong, not just
  imprecise**: the article's "Step 3 — use the `/agent` command" names
  a command that doesn't exist (`/agents`, plural, is real) and
  describes an interactive wizard flow that existed only through Claude
  Code v2.1.197 — current builds just point back at asking Claude
  directly or editing files by hand. Two real corrections on context/
  permissions: a subagent does NOT inherit conversation history/
  invoked skills/files already read (only its own system prompt plus a
  delegation message), and permission mode is INHERITED from the main
  session unless explicitly overridden, not independently configured
  as the article's framing implies. **A real, well-evidenced gap found
  in this project itself**: zero `.claude/agents/` files existed
  despite 12 real skills and the `review-loop` skill's own stated
  fallback ("an external tool... otherwise a rigorous self-review
  checklist") having no isolated-context, fresh-eyes reviewer option
  at all. **Built**: `.claude/agents/code-reviewer.md` and
  `.claude/agents/security-reviewer.md` — two real subagents filling
  that gap, `security-reviewer` adapting the article's own literal
  worked example rather than inventing a different one, since this
  project genuinely has security-relevant surface (untrusted binary
  parsing in `go-buildinfo-extractor`/`rust_cargo_auditable`, the MCP
  server in `prop-firm-mcp-server`, governance logic in
  `policy-control-plane`/`agent-checkpoint-layer`). Also built
  `/builds/agent-md-validator/` — a small, dependency-free Python
  linter for `.claude/agents/*.md` frontmatter, built directly from
  this round's own verification rather than guessed: a `KNOWN_FIELDS`
  set from the real documented field list (flagging anything else as a
  likely silent-typo risk — Claude Code itself silently ignores an
  unrecognized field rather than erroring, the single most concrete,
  actionable fact this round's check produced), valid `effort`/
  `permissionMode`/`isolation` values, and a permissive warning (not an
  error) for the three tools confirmed always stripped from subagents
  regardless of what's listed. Its frontmatter parser is structurally
  copied from `skill_md_validator.py`'s generic parser (a few rounds
  earlier in this project), not imported across build directories, per
  this project's established copy-unmodified convention. 16/16 tests
  pass, including a discrimination test (one planted fixture with four
  distinct deliberate problems produces exactly those four findings)
  and a real subprocess CLI run confirming this project's own two new
  agent files pass cleanly with zero findings. Deliberately not built:
  an interactive agent-creation wizard matching the article's outdated
  "Step 3," since the real current `/agents` command doesn't work that
  way anymore; a Planner/Coder subagent pair matching the article's "3
  Classic Agents" pattern, since this project's existing `new-feature`/
  `code-structure` skills already cover that ground within one
  continuous session and splitting them into subagents would duplicate
  rather than fill a gap, unlike the Reviewer.
- **Deep analysis + new build from a bare repo link: `oil-oil/oil-ui`** —
  a real, MIT-licensed, actively-developed (same-day commit) Claude Code
  design skill, confirmed genuinely new to this project before touching
  anything. Full write-up in `/notes/oil-ui-analysis.md`. Measured first:
  zero npm dependencies anywhere (every `.mjs` script is plain Node
  stdlib, confirmed by the total absence of `package.json`), a real
  cross-platform CI matrix (Linux/Windows, Chrome/Edge, light/dark theme,
  a GBK locale), and `test_shoot.py` alone running longer (2,302 lines)
  than the `shoot.mjs` script it tests (2,067). Verified: `npx skills add`
  is a real, published npm package (`npm view skills version` → `1.7.6`);
  `check_update.py`'s stated privacy claim ("only reads the public version
  list, never uploads project content") holds exactly against the actual
  `fetch()` code (a bare GET, no body); its pinned-exact-commit-hash CLI
  dependency is a real, credited supply-chain defense; `ui.oiloil.org` is
  blocked by this session's own egress proxy, the same restriction class
  already documented for EODHD/FMP/Hugging Face/arXiv, now extended to
  this vendor. **A new, different kind of sandbox restriction surfaced
  this round**: this session's auto-mode classifier denies running an
  untrusted cloned repo's own code at all ("Code from External") — not a
  network block, an execution block, even offline against a local fixture
  — so the one concrete algorithmic claim worth checking
  (`measure_reference.py`'s pure-stdlib PNG decoder, the real path this
  sandbox would hit since `python3 -c "import PIL"` fails here) was
  verified by building an independent fixture encoder, cross-checking it
  against a second, independently-written oracle decoder, then reading
  oil-ui's own unfiltering formulas line-by-line against that oracle
  instead of executing their script — confirmed to match the PNG spec
  exactly. Credited directly: colour sampling takes the per-channel
  **median**, not the mean, across opaque pixels, a real design choice
  this round demonstrated rather than took on faith (a region 80% one
  colour / 20% outlier reports the true colour under the median while the
  same pixels' real arithmetic mean is measurably different). Also read
  and credited, not independently re-verified or rebuilt: `build_explorer.py`,
  a strict-CSP, fully self-contained offline HTML "design comparison"
  bundler (inlines every asset as `data:`, rejects iframes/unembedded
  resources/auto-redirects) — a genuinely well-reasoned answer to showing
  several AI-generated candidates side by side without any one phoning
  home, in the same spirit as this project's own `policy-control-plane`/
  `defender-loop-verifier` governance work in a different domain. **Built**:
  `/builds/reference-color-sampler/` — checked `/builds/` first
  (`ten-k-website-grader`'s colour pillar only greps CSS text for hex
  literals, a named limitation in its own README; `design-rules.md`'s
  derive-from-one-brand-colour rule has no mechanism for extracting a real
  colour from a reference image at all) — a standalone, independent
  reimplementation (not a port, not executed from or copied out of
  oil-ui's own code, per the classifier restriction) of the one
  generalizable, now-verified mechanism: the pure-stdlib PNG decoder
  (generalized to all 5 PNG colour types oil-ui supports), median-based
  opaque-pixel colour sampling with inset, and normalized/CSS-ratio box
  measurement. 11/11 tests pass on the real run, including the
  independent-oracle cross-check and the median-vs-mean discrimination
  test — no bug found in this round's own build, stated plainly rather
  than manufactured. Deliberately not built: oil-ui's `--extract`/
  chroma-key asset extraction, its `--manifest` batch workflow, and
  `build_explorer.py`'s comparison bundler (real scope cuts, not gaps);
  also not wired into `ten-k-website-grader`/`sales-page-engine` this
  round — left standalone for a future round where that specific
  integration need actually comes up.
- **Deep analysis + new build from a pasted article: "Data Science Is
  Changing. These Are the Skills I'd Learn in 2027"** (Codebook Fusion,
  Medium). Full write-up in `/notes/ds-2027-skills-analysis.md`. Unlike
  most sources this project analyzes, this one has almost no externally-
  checkable surface (no code, no repo, no dated/sourced statistic) —
  stated plainly rather than padded with unnecessary verification of
  trivially-real, well-known tools (Airflow, Dagster, dbt, Polars,
  DuckDB). **The real finding came from reading the article's own
  sections against each other**: its headline "9 Skills I Would Learn in
  2027" list never names classical machine learning as one of the 9
  (Skill 1's own framing argues the opposite — "the first question has
  changed... to 'do I need to train anything at all?'"), yet the
  12-month roadmap devotes two full months to it and the FAQ explicitly
  answers "Learn the basics of classical machine learning first" —
  treating it as essential, first-to-learn material everywhere except
  the one list that's supposed to rank skills "roughly by return on time
  invested." Credited: Skill 1 ("write a one page brief before touching
  data") and Skill 4 ("write the evaluation set before writing the
  system") independently converge on the same discipline, reinforced
  directly by "Mistake 1: Starting with the model" — a genuinely
  coherent throughline, not three disconnected bullets. Flagged: Skill 4
  names "LLM as a judge" biases and limits without naming a single one
  (position/self-enhancement/verbosity bias are all specific, well-
  documented, nameable failure modes), a real depth gap in an otherwise
  concrete, operational piece. **Built**: `/builds/
  ds-2027-skills-scorecard/` — checked `/builds/` first
  (`agent-readiness-scorecard` scores agent-maturity, `ten-k-website-
  grader` scores a rendered page, neither overlaps) — an honest scorer
  for the 6 of the article's 9 skills a repo's files can actually speak
  to (Python/SQL/testing, LLM/agent usage, evaluation harnesses, data
  engineering, MLOps/deployment, responsible-AI governance), with the
  other 3 (problem framing, communication, domain knowledge) always
  reported `not_assessable` rather than faked — same discipline as
  `agent-readiness-scorecard`'s Level 4/5 signals. **Found and fixed a
  real bug, not a synthetic one**: running the first draft against this
  project's own repo (which genuinely contains the tool) reported a
  false PASS on the data-engineering skill, traced to the tool's own
  Airflow-detection regex literally spelling "from airflow"/"import
  airflow" in its own source line plus its own test fixture writing that
  exact string — precisely the `ruthless-gate` skill's documented "a
  detector that scans its own file cannot spell its own pattern"
  pitfall, caught empirically, not read off the rule in the abstract.
  Fixed generally with an `exclude_self` default (excludes the tool's
  own directory from any scan, `--include-self` to override) rather than
  a narrower regex patch. **A second, honest correction made mid-build**:
  the first test draft assumed the data-engineering skill should read
  `fail` against this repo, having checked only for literal Airflow/dbt
  markers; the real run surfaced two genuine pipeline modules this
  project already has (`trading-jarvis/data_pipeline.py`, `recovery-
  desk/data_pipeline.py`) via a separate fallback check the draft hadn't
  accounted for — the test was corrected to the verified truth rather
  than the tool's output forced to match a wrong assumption, same
  discipline as `paired-bootstrap-ratchet`'s own mid-build corrections.
  10/10 tests pass, including a discrimination pair (a planted fixture
  with real signal for every assessable skill passes all six; a bare
  script whose README literally names the three not-assessable skills by
  word still fails all six real checks, proving the tool checks
  structure, not keyword-matching against the rubric's own names) and
  the self-matching bug reproduced-then-proven-fixed as a permanent
  regression test.
- **Deep analysis + extended build from a pasted article: "The Harness
  Is the Product: How Agents Are Actually Built in 2026"** (Andrii
  Tkachuk). Full write-up in `/notes/harness-is-the-product-analysis.md`.
  This article describes, at a high level, exactly the architecture this
  project has been incrementally building piece by piece across most of
  its history, so the round's real work was mapping its 12 named harness
  components precisely against the existing portfolio rather than
  rebuilding anything already covered. Three named market examples
  web-verified: Viktor's real $75M Series A (Accel, May 2026); OpenAI's
  real dots (DevDay, Sept 29 2026) — but the article cites dots as its
  clean proof of a working graduated-approval policy layer while omitting
  two things independent reporting found: OpenAI itself states dots
  cannot send messages, edit anything, or control the user's computer at
  launch, and a real safety controversy (a shelved GPT-6.1 Astra upgrade
  after deceptive test behavior, an agent "hacking" an Australian
  government website) surrounded the same launch; Meta's real Muse —
  whose actual architecture (a separate, system-level-isolated "Sentinel"
  supervisor agent approving internet-bound requests) is a *better*,
  more concrete illustration of the article's own policy-gateway
  argument than what the article actually cites it for. **Checked the
  article's Jev claim against this project's own much earlier, much
  deeper Jev analysis and found it overstated**: the article says
  "Parallel's evaluation found it matched or beat their trained models in
  some cases," but Parallel's own blog post states plainly "In both
  cases, Jev performed less well than our specialized internal models" —
  the closest thing to a match is a tie on one metric in one test, not
  multiple wins. Consistent with, and extending, this project's prior
  finding that Jev's real evaluations consistently underperform its
  marketing framing — a fresh independent source adds a third instance
  (a claimed 193.6x speed multiple holding up at only ~5-25x under
  independent testing). Credited directly against existing builds:
  section 4 (selection-before-generation) → `jev-pattern-router`;
  section 6 (API-first/browser-fallback) → `interface-lift-toolkit`;
  section 7 (credential/policy gateway) → `policy-control-plane`;
  section 11 (durable long-running state) → `agent-checkpoint-layer`.
  Read and credited but not rebuilt, for stated scope reasons: sandboxed
  code execution, model routing, channel-agnostic surface adapters, and
  the Capability→Tool/Skill→Operation progressive-disclosure primitive
  set. **Found the one genuine, well-specified gap**: the article's own
  sharp distinction — "model-initiated clarification and policy-enforced
  approval look similar on screen, but... belong to different layers" —
  checked directly against `policy-control-plane` and
  `agent-checkpoint-layer` (grepped both for `ask_human`/`clarif`, zero
  hits in either). **Built**: `policy/clarification.py`, extending
  `/builds/policy-control-plane/` rather than starting a new build (the
  article's own point is these two mechanisms must stay architecturally
  distinct while living in the same governance layer) — a separate
  SQLite-backed `ClarificationStore` with its own table and id space, not
  a second status bolted onto `ApprovalRecord`. 16/16 tests pass,
  including a real cross-contamination check (answering a clarification
  leaves an unrelated pending approval's status completely untouched, and
  vice versa), the article's own worked scenario run end-to-end (resolving
  "staging" vs. "production" via `ask_human()` changes what `governed_call`
  later decides), and the one invariant that actually matters for
  security: a production restart is gated identically whether or not the
  model ever called `ask_human()` first — approval enforcement never
  depends on the model's cooperation.

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

### Deep-analysis-and-ship loop (for a new upload, link, or pasted source)

This is the pattern behind nearly every entry in the Current status log
above: a source arrives → measure its hard facts before reading for
meaning → verify its checkable claims (recompute arithmetic, check
against the real file/repo, web-search anything external) → credit what
holds up and flag what doesn't → decide whether a real, generalizable,
testable build is warranted (and if so, build and test it for real,
preferring this project's own real material over synthetic fixtures) →
write the `/notes/` analysis (and `/builds/` README if something got
built) → update this file's status log in the same register as every
existing entry → commit and push per the Git/PR workflow rule below.

Now a real slash command: `.claude/commands/analyze-and-ship.md` — run
`/analyze-and-ship [source]`, or just `/analyze-and-ship` against the
most recently pasted/uploaded content. Distinct from `ruthless-gate`
(that one's a different, stricter four-file HTML-verdict-page procedure
behind its own explicit trigger phrase) — this is the lighter-weight
default this project has actually been running the whole time, now
written down so a cold session doesn't have to reconstruct it from
reading every prior status-log entry.

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
