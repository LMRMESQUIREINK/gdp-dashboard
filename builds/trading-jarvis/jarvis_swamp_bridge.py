# ═══════════════════════════════════════════════════════════════
#  ♛  RUTHLESS TRADING GOLD  ♛  ×  SWAMP INTELLIGENCE
#  ───────────────────────────────────────────────────────────
#  Bridge: routes a Jarvis objective through the Swamp Intelligence
#  reasoning layer (decompose -> assign -> sequence -> event-structure)
#  before handing off to Jarvis's existing, already-uploaded components.
#  Adds NO new execution capability. No execute_order exists here either.
#  Data Layer: EODHD+FMP (via the existing data_pipeline.py)
#  Generated: 2026-07-28 | Pro fixes applied: see README.md
# ═══════════════════════════════════════════════════════════════
"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              ♛  RUTHLESS TRADING GOLD  ♛                      ║
║                                                               ║
║      Strategy: Trading Jarvis + Swamp Intelligence layer       ║
║      Symbol(s): configurable via CLI arg                       ║
║      Timeframe: daily                                          ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

Drop this file next to run_strategy.py, data_pipeline.py,
signal_generator.py, risk_manager.py, and live_monitor.py in the
existing Trading Jarvis repo. It imports the real Jarvis modules —
it does not reimplement or fake them.

What Swamp Intelligence adds here:
    - Decomposes "check <symbol> for a signal at <risk_pct>% risk"
      into an explicit Task Tree (Fetch -> Signal -> Risk -> Approval)
    - Assigns each step to a named agent matching Jarvis's real modules
    - Emits Event Packets before any function actually runs
    - Hard-locks approval_required=True on every step that would ever
      touch position sizing — this is enforced in code, not just labeled

What it deliberately does NOT add:
    - No execute_order / broker call of any kind
    - No path that skips the approval flag and acts anyway
    - No voice input (per the existing README's stated scope)

WHAT CHANGED IN THIS BUILD
    - The self-test that proves swamp.guard("bypass_approval") actually
      raises used to swallow the result either way (try/except/pass —
      no branch existed for "it didn't raise"). If a future edit to
      swamp_intelligence.py ever weakened the guard, this would have
      stayed silent. Now asserts the raise happened, matching this same
      file's own pattern for the step3.approval_required check below.
    - Now passes real existing_positions (via positions_store.py) into
      evaluate_trade(), so the printed portfolio heat reflects other
      recorded open positions, not just this one trade.
"""

from __future__ import annotations

from swamp_intelligence import (
    SwampIntelligence,
    Task,
    Priority,
    GovernanceError,
)
import positions_store as positions

DOMAIN = "trading-jarvis"

# Agent names line up 1:1 with the real Jarvis modules already in this repo.
AGENT_DATA_PIPELINE = "Data Pipeline Agent (data_pipeline.py)"
AGENT_SIGNAL_GENERATOR = "Signal Generator Agent (signal_generator.py)"
AGENT_RISK_MANAGER = "Risk Manager Agent (risk_manager.py)"
AGENT_HUMAN_APPROVAL = "Human Approval Gate (you)"


def decompose_objective(symbol: str, risk_pct: float) -> "TaskTree":  # noqa: F821 (type imported below at use)
    """Build the Task Tree for a single-symbol Jarvis check.

    This is pure reasoning — no data is fetched and nothing runs yet.
    """
    swamp = SwampIntelligence(domain=DOMAIN)
    tree = swamp.build_tree(
        objective=f"Check {symbol} for a tradeable signal at {risk_pct:.1f}% account risk"
    )

    tree.add(Task(
        step=1,
        task=f"Fetch recent OHLCV closes for {symbol}",
        agent=AGENT_DATA_PIPELINE,
        priority=Priority.MEDIUM,
        risk_score=10,
        approval_required=False,
    ))
    tree.add(Task(
        step=2,
        task="Compute RSI + volume-confirmation signal (lookahead-safe, .shift(1)'d)",
        agent=AGENT_SIGNAL_GENERATOR,
        priority=Priority.MEDIUM,
        risk_score=20,
        approval_required=False,
        depends_on=(1,),
    ))
    tree.add(Task(
        step=3,
        task="If BUY signal: compute ATR stop, fixed-fractional size, portfolio heat",
        agent=AGENT_RISK_MANAGER,
        priority=Priority.HIGH,
        risk_score=55,
        approval_required=True,  # non-negotiable — see GovernanceError below
        depends_on=(2,),
    ))
    tree.add(Task(
        step=4,
        task="Present sized suggestion to a human. No order is placed by this system.",
        agent=AGENT_HUMAN_APPROVAL,
        priority=Priority.HIGH,
        risk_score=0,
        approval_required=True,
        depends_on=(3,),
    ))
    return tree


def route_through_bus(symbol: str, equity: float = 50_000, risk_pct: float = 1.0) -> None:
    """Swamp Intelligence structures the workflow, then hands sequenced
    steps to Jarvis's real modules. Swamp Intelligence itself never
    touches data_pipeline / signal_generator / risk_manager directly —
    that call happens here, in the bridge, acting as the Master Event
    Bus's routing surface, exactly as the Brain Spec's system position
    diagram describes (Swamp Intelligence -> Bus -> execution surface).
    """
    swamp = SwampIntelligence(domain=DOMAIN)

    # Governance check, mirrors Section: PROHIBITED ACTIONS.
    # Any caller attempting to skip approval on a risk-bearing step
    # should fail loudly here, not silently downstream. This is a real
    # regression check, not a demonstration: if guard() ever failed to
    # raise for a prohibited action, that's the approval gate itself
    # broken, and this function refuses to proceed rather than continue
    # as if nothing were wrong.
    try:
        swamp.guard("bypass_approval")
    except GovernanceError:
        pass  # expected: bypass_approval is prohibited, guard() correctly raised
    else:
        raise GovernanceError(
            "guard('bypass_approval') should have raised but didn't — "
            "the approval gate may be broken. Refusing to proceed."
        )

    tree = decompose_objective(symbol, risk_pct)
    print(f"♛ SWAMP INTELLIGENCE — routing objective for {symbol}\n")
    print(tree.render())
    print("\n### EVENT PACKETS\n")
    for packet in tree.event_packets():
        print(packet.to_dict())

    print("\n### HANDOFF TO JARVIS EXECUTION SURFACE\n")

    # ---- Step 1 + 2: hand off to the real, already-uploaded modules ----
    # Uses get_recent_ohlcv (real high/low/volume), not the old fabricated
    # frame — the fabricated version made BUY signals structurally
    # impossible because a constant volume series always fails the
    # volume-confirmation check. See data_pipeline.py's fix note.
    try:
        from data_pipeline import get_recent_ohlcv
        from signal_generator import generate_signals, latest_signal
        from risk_manager import evaluate_trade
    except ImportError as exc:
        print(
            "  [halted before execution] Could not import Jarvis's own modules "
            f"(data_pipeline.py / signal_generator.py / risk_manager.py): {exc}\n"
            "  This is expected if you're running the bridge outside the full "
            "Trading Jarvis repo — drop this file in alongside those modules."
        )
        return

    ohlcv = get_recent_ohlcv(symbol, lookback_days=120)
    signaled = generate_signals(ohlcv)
    sig = latest_signal(signaled)
    print(f"  [Step 1-2 complete] Latest close ${ohlcv['adjusted_close'].iloc[-1]:.2f} | "
          f"signal: {sig} | volume confirmed: {bool(signaled['vol_confirm'].iloc[-1])}")

    if sig != "BUY":
        print("  [Step 3 skipped] No BUY signal — risk step not triggered. No approval needed.")
        return

    # ---- Step 3: risk sizing — approval_required is hard-enforced, not decorative ----
    step3 = tree.tasks[2]
    if not step3.approval_required:
        # This branch should be unreachable — decompose_objective always
        # sets this True. It's asserted here so the invariant can't
        # silently rot if this file is edited later.
        raise GovernanceError(
            "Risk-sizing step lost its approval_required flag. Refusing to proceed."
        )

    existing = positions.positions_for_heat_check(exclude_symbol=symbol)
    risk = evaluate_trade(ohlcv, equity=equity, risk_pct=risk_pct, existing_positions=existing)
    print("\n  ♛ Step 3 complete — risk-sized SUGGESTION (approval_required=True):")
    print(f"    Suggested shares : {risk['sizing']['shares']}")
    print(f"    Stop             : ${risk['sizing']['stop']}")
    print(f"    Dollar risk      : ${risk['sizing']['dollar_risk']}")
    print(f"    2R target        : ${risk['sizing']['r_multiple_target']}")
    print(f"    Portfolio heat   : {risk['portfolio_heat']['heat_pct']}%"
          f"{'  WARNING' if risk['portfolio_heat']['warning'] else ''}")

    # ---- Step 4: this system stops here, by design ----
    print("\n  [Step 4] Handed to human approval gate. No execute_order call exists "
          "in this bridge or anywhere in the Trading Jarvis repo. Nothing further "
          "happens until a person acts on this suggestion outside this system.")
