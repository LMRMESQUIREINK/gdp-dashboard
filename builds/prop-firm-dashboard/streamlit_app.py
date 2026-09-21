"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              ♛  RUTHLESS TRADING GOLD  ♛                      ║
║                                                               ║
║      Component: streamlit_app.py                              ║
║      Role:      Web dashboard over the four prop-firm         ║
║                  sizing tools (also reachable via              ║
║                  jarvis_orchestrator.py's Claude tools and     ║
║                  run_strategy.py's --prop-* CLI flags)         ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

Four tabs, one per --prop-* flag in trading-jarvis/run_strategy.py:
Size Check, Session Report, Pass Probability, Compare Sizes. Calls
PropFirmAccount / AccountRules / SessionState / PassSimulator directly
— no subprocess, no duplicated math. Every number on this page comes
from the same functions already proven in
/notes/prop-firm-sizing-analysis.md and /builds/prop-firm-sizing/README.md.

Run it:
    pip install -r requirements.txt
    streamlit run streamlit_app.py
"""

import pandas as pd
import streamlit as st

from prop_firm_sizing import PropFirmAccount, SessionState, TPT_TIERS, CONTRACT_SPECS
from prop_firm_position_sizing import AccountRules, evaluate_size
from prop_pass_simulator import PassSimulator

st.set_page_config(page_title="RUTHLESS Prop-Firm Dashboard", page_icon="♛", layout="wide")

# ───────────────────────────────────────────────────────────────
# RUTHLESS TRADING GOLD theme — black/gold, Cinzel Decorative +
# Cormorant Garamond + IBM Plex Mono, matching every analysis
# dashboard and CLI banner elsewhere in this project.
# ───────────────────────────────────────────────────────────────

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Cinzel+Decorative:wght@700;900&family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {
    --bg-primary: #0A0A0A; --bg-card: #141414; --bg-elevated: #1C1C1C;
    --gold-primary: #C9A84C; --gold-bright: #F0C040; --gold-muted: #8B7333;
    --text-primary: #E8E8E8; --text-secondary: #A0A0A0;
    --profit-green: #22c55e; --loss-red: #ef4444; --warn-yellow: #F0C040;
  }
  .stApp { background: var(--bg-primary); color: var(--text-primary);
           font-family: 'Cormorant Garamond', Georgia, serif; font-size: 18px; }
  h1, h2, h3, .ruthless-title {
    font-family: 'Cinzel Decorative', 'Cinzel', Georgia, serif !important;
    color: var(--gold-primary) !important; letter-spacing: 1px;
  }
  .ruthless-header { text-align: center; border-bottom: 2px solid var(--gold-primary);
                      padding-bottom: 20px; margin-bottom: 28px; }
  .ruthless-crown { font-size: 44px; color: var(--gold-bright);
                     text-shadow: 0 0 20px rgba(240, 192, 64, 0.4); }
  .ruthless-subtitle { color: var(--text-secondary); font-style: italic; font-size: 16px; }
  /* Tabs */
  .stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid var(--gold-muted); }
  .stTabs [data-baseweb="tab"] {
    font-family: 'Cinzel Decorative', Georgia, serif; font-size: 13px; letter-spacing: 1px;
    color: var(--text-secondary); background: transparent;
  }
  .stTabs [aria-selected="true"] { color: var(--gold-bright) !important;
                                    border-bottom-color: var(--gold-primary) !important; }
  /* Inputs */
  .stSelectbox div[data-baseweb="select"] > div, .stNumberInput input, .stTextInput input {
    background: var(--bg-card) !important; border: 1px solid var(--gold-muted) !important;
    color: var(--text-primary) !important; font-family: 'IBM Plex Mono', monospace !important;
  }
  .stSelectbox div[data-baseweb="select"] > div:focus-within, .stNumberInput input:focus {
    border-color: var(--gold-bright) !important;
  }
  label, .stMarkdown p { color: var(--text-primary) !important; }
  /* Buttons */
  .stButton button {
    background: var(--gold-primary); color: #0A0A0A; border: none;
    font-family: 'Cinzel Decorative', Georgia, serif; letter-spacing: 1px; font-weight: 700;
  }
  .stButton button:hover { background: var(--gold-bright); color: #0A0A0A; }
  /* Metrics */
  [data-testid="stMetric"] { background: var(--bg-card); border: 1px solid var(--gold-muted);
                              border-radius: 6px; padding: 12px 16px; }
  [data-testid="stMetricLabel"] { color: var(--text-secondary) !important; }
  [data-testid="stMetricValue"] { color: var(--gold-bright) !important;
                                   font-family: 'IBM Plex Mono', monospace !important; }
  /* Status badges */
  .status-badge { display: inline-block; padding: 4px 14px; border-radius: 4px;
                   font-family: 'Cinzel Decorative', Georgia, serif; font-size: 13px;
                   letter-spacing: 1px; margin-bottom: 8px; }
  .status-safe { background: rgba(34,197,94,0.15); color: var(--profit-green); border: 1px solid var(--profit-green); }
  .status-warning { background: rgba(240,192,64,0.15); color: var(--warn-yellow); border: 1px solid var(--warn-yellow); }
  .status-critical, .status-breached { background: rgba(239,68,68,0.15); color: var(--loss-red); border: 1px solid var(--loss-red); }
  /* Meter bar for pass/fail probabilities */
  .meter { display: flex; height: 28px; border-radius: 4px; overflow: hidden;
           border: 1px solid var(--gold-muted); margin: 10px 0; font-family: 'IBM Plex Mono', monospace; font-size: 12px; }
  .meter-seg { display: flex; align-items: center; justify-content: center; color: #0A0A0A; font-weight: 600; }
  .meter-pass { background: var(--profit-green); }
  .meter-fail-dd { background: var(--loss-red); }
  .meter-fail-time { background: var(--text-secondary); }
  code, .stCode, pre { font-family: 'IBM Plex Mono', monospace !important; color: var(--gold-bright) !important; }
  hr { border-color: var(--gold-muted) !important; }
</style>
<div class="ruthless-header">
  <div class="ruthless-crown">♛</div>
  <div class="ruthless-title" style="font-size: 26px; font-weight: 900;">RUTHLESS PROP-FIRM DASHBOARD</div>
  <div class="ruthless-subtitle">TPT funded-account sizing, session tracking &amp; pass-probability — powered by
  PropFirmAccount / SessionState / PassSimulator</div>
</div>
""", unsafe_allow_html=True)

TIERS = list(TPT_TIERS.keys())
SYMBOLS = list(CONTRACT_SPECS.keys())


def _status_badge(level: str) -> str:
    icon = {"SAFE": "🟢", "WARNING": "🟡", "CRITICAL": "🔴", "BREACHED": "🔴"}.get(level, "⚪")
    css_class = f"status-{level.lower()}"
    return f'<span class="status-badge {css_class}">{icon} {level}</span>'


tab_size, tab_session, tab_pass, tab_compare = st.tabs(
    ["♛ Size Check", "♛ Session Report", "♛ Pass Probability", "♛ Compare Sizes"]
)

# ───────────────────────────────────────────────────────────────
# Tab 1 — Size Check (static, start-of-day)
# ───────────────────────────────────────────────────────────────

with tab_size:
    st.markdown("Static point-risk + 25%-of-max-contracts rule + optional stop-room-vs-ADR check. "
                 "No session state involved — for a live, trailing-DD-aware check, use **Session Report**.")
    c1, c2, c3, c4 = st.columns(4)
    tier = c1.selectbox("Account tier", TIERS, index=TIERS.index("50K"), key="size_tier")
    symbol = c2.selectbox("Contract", SYMBOLS, key="size_symbol")
    contracts = c3.number_input("Contracts", min_value=1, value=1, step=1, key="size_contracts")
    adr = c4.number_input("Avg daily range (pts, optional)", min_value=0.0, value=0.0, step=1.0, key="size_adr")

    if st.button("♛ Run Size Check", key="btn_size"):
        account = PropFirmAccount(tier=tier, symbol=symbol)
        rules = AccountRules(
            account_equity=account.starting_balance,
            daily_loss_limit=account.daily_loss_limit,
            eod_trailing_drawdown=account.eod_trailing_dd,
            max_contracts=account.max_contracts,
            point_value=account.point_value,
        )
        result = evaluate_size(rules, int(contracts), average_daily_range_points=(adr or None))
        point_risk = result["point_risk"]

        if "error" in point_risk:
            st.error(f"♛ {point_risk['error']}")
        else:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Points of risk", point_risk["points_of_risk"])
            m2.metric("% of max contracts used", f"{result['size_rule']['pct_of_max_used']}%")
            m3.metric("Within 25% rule", "Yes" if result["size_rule"]["within_rule"] else "No")
            if "adr_check" in result:
                m4.metric("Stop room as % of ADR", f"{result['adr_check']['pct_of_adr_as_stop_room']}%")

            for flag in result["summary_flags"]:
                if "No flags" in flag:
                    st.success(f"✓ {flag}")
                else:
                    st.warning(f"⚠ {flag}")

# ───────────────────────────────────────────────────────────────
# Tab 2 — Session Report (trailing-DD-floor-aware, live)
# ───────────────────────────────────────────────────────────────

with tab_session:
    st.markdown("The EOD trailing drawdown floor follows the **high-water mark**, not the starting "
                 "balance — a good morning shrinks your room, it doesn't grow it. Leave high-water mark "
                 "and session start balance blank to derive them from today's P&L.")
    c1, c2, c3 = st.columns(3)
    tier_s = c1.selectbox("Account tier", TIERS, index=TIERS.index("50K"), key="sess_tier")
    symbol_s = c2.selectbox("Contract", SYMBOLS, key="sess_symbol")
    pnl_s = c3.number_input("Today's intraday P&L", value=0.0, step=50.0, key="sess_pnl")

    c4, c5 = st.columns(2)
    hwm_override = c4.number_input("High-water mark (0 = auto)", min_value=0.0, value=0.0, step=50.0, key="sess_hwm")
    start_override = c5.number_input("Session start balance (0 = account default)", min_value=0.0, value=0.0,
                                      step=50.0, key="sess_start")

    if st.button("♛ Run Session Report", key="btn_session"):
        account = PropFirmAccount(tier=tier_s, symbol=symbol_s)
        session_start_balance = start_override or account.starting_balance
        high_water_mark = hwm_override or (session_start_balance + max(0.0, pnl_s))
        state = SessionState(
            account=account,
            session_start_balance=session_start_balance,
            high_water_mark=high_water_mark,
            intraday_pnl=pnl_s,
        )

        st.markdown(_status_badge(state.warning_level()), unsafe_allow_html=True)

        m1, m2, m3 = st.columns(3)
        m1.metric("Current balance", f"${state.current_balance:,.2f}")
        m2.metric("High-water mark", f"${high_water_mark:,.2f}")
        m3.metric("Trailing DD floor", f"${state.trailing_dd_floor:,.2f}")

        m4, m5, m6 = st.columns(3)
        m4.metric("Gap to DD floor", f"${state.gap_to_trailing_floor:,.2f}")
        m5.metric("Remaining daily limit", f"${state.remaining_daily_loss:,.2f}")
        m6.metric("Binding loss limit", f"${state.binding_loss_limit:,.2f}")

        m7, m8 = st.columns(2)
        m7.metric("Safe contracts NOW", state.safe_contracts)
        m8.metric("Points/contract NOW", f"{state.effective_points_per_contract:.1f}")

        level = state.warning_level()
        if level in ("BREACHED", "CRITICAL"):
            st.error("⛔ STOP TRADING — too close to the DD floor to size safely.")
        elif level == "WARNING":
            st.warning("⚠ Consider reducing to 1 contract or flat for the session.")
        else:
            st.success("✓ Safe — within configured thresholds.")

# ───────────────────────────────────────────────────────────────
# Tab 3 — Pass Probability (Monte Carlo)
# ───────────────────────────────────────────────────────────────

with tab_pass:
    st.markdown("Monte Carlo estimate of evaluation pass probability. `avg_daily_pnl` and `daily_pnl_std` "
                 "should come from **your own** trading journal — never estimated here.")
    c1, c2 = st.columns(2)
    tier_p = c1.selectbox("Account tier", TIERS, index=TIERS.index("50K"), key="pass_tier")
    symbol_p = c2.selectbox("Contract", SYMBOLS, key="pass_symbol")

    c3, c4, c5 = st.columns(3)
    balance_p = c3.number_input("Current balance", value=50_800.0, step=100.0, key="pass_balance")
    hwm_p = c4.number_input("High-water mark", value=51_200.0, step=100.0, key="pass_hwm")
    days_p = c5.number_input("Days remaining", min_value=1, value=8, step=1, key="pass_days")

    c6, c7, c8 = st.columns(3)
    avg_pnl_p = c6.number_input("Your avg daily P&L ($)", value=180.0, step=10.0, key="pass_avg")
    std_p = c7.number_input("Your daily P&L std dev ($)", min_value=1.0, value=550.0, step=10.0, key="pass_std")
    sims_p = c8.number_input("Simulations", min_value=1_000, max_value=200_000, value=50_000, step=1_000, key="pass_sims")

    if st.button("♛ Run Pass Probability", key="btn_pass"):
        account = PropFirmAccount(tier=tier_p, symbol=symbol_p)
        sim = PassSimulator(
            account=account, current_balance=balance_p, high_water_mark=hwm_p,
            days_remaining=int(days_p), avg_daily_pnl=avg_pnl_p, daily_pnl_std=std_p,
            simulations=int(sims_p),
        )
        sim.run()

        m1, m2, m3 = st.columns(3)
        m1.metric("♛ Pass probability", f"{sim.pass_probability:.1%}")
        m2.metric("Fail (DD breach)", f"{sim.fail_dd_probability:.1%}")
        m3.metric("Fail (time expired)", f"{sim.fail_time_probability:.1%}")

        pass_pct, fail_dd_pct, fail_time_pct = (
            sim.pass_probability * 100, sim.fail_dd_probability * 100, sim.fail_time_probability * 100
        )
        st.markdown(f"""
        <div class="meter">
          <div class="meter-seg meter-pass" style="width:{pass_pct}%">{pass_pct:.0f}%</div>
          <div class="meter-seg meter-fail-dd" style="width:{fail_dd_pct}%">{fail_dd_pct:.0f}%</div>
          <div class="meter-seg meter-fail-time" style="width:{fail_time_pct}%">{fail_time_pct:.0f}%</div>
        </div>
        <div style="color: var(--text-secondary); font-size: 13px;">
          🟢 Pass &nbsp;&nbsp; 🔴 Fail (DD breach) &nbsp;&nbsp; ⚪ Fail (time expired)
        </div>
        """, unsafe_allow_html=True)

        m4, m5, m6 = st.columns(3)
        median_days = sim.median_days_to_pass
        m4.metric("Median days to pass", f"{median_days:.1f}" if median_days == median_days else "—")
        m5.metric("5th pct final balance", f"${sim.pct5_final_balance:,.2f}")
        m6.metric("95th pct final balance", f"${sim.pct95_final_balance:,.2f}")

        if sim.pass_probability >= 0.70:
            st.success("✔ Strong position — maintain sizing discipline.")
        elif sim.pass_probability >= 0.45:
            st.warning("⚠ Moderate. Consider reducing size to protect the floor.")
        else:
            st.error("⛔ Low pass probability. The trailing DD floor is the primary threat. "
                      "Reduce to 1 contract, focus on not losing, let time work for you.")

# ───────────────────────────────────────────────────────────────
# Tab 4 — Compare Sizes (pass probability across contract counts)
# ───────────────────────────────────────────────────────────────

with tab_compare:
    st.markdown("Compare pass probability across contract sizes, using the **same `PassSimulator`** as the "
                 "Pass Probability tab — one Monte Carlo run per row below. Edit the table to try your own "
                 "sizes and P&L assumptions.")
    c1, c2 = st.columns(2)
    tier_c = c1.selectbox("Account tier", TIERS, index=TIERS.index("50K"), key="cmp_tier")
    symbol_c = c2.selectbox("Contract", SYMBOLS, key="cmp_symbol")

    c3, c4, c5 = st.columns(3)
    balance_c = c3.number_input("Current balance", value=50_000.0, step=100.0, key="cmp_balance")
    hwm_c = c4.number_input("High-water mark", value=50_000.0, step=100.0, key="cmp_hwm")
    days_c = c5.number_input("Days remaining", min_value=1, value=11, step=1, key="cmp_days")

    default_rows = pd.DataFrame([
        {"contracts": 1, "avg_daily_pnl": 90, "daily_pnl_std": 275},
        {"contracts": 2, "avg_daily_pnl": 165, "daily_pnl_std": 490},
        {"contracts": 3, "avg_daily_pnl": 230, "daily_pnl_std": 700},
        {"contracts": 6, "avg_daily_pnl": 400, "daily_pnl_std": 1400},
    ])
    edited = st.data_editor(default_rows, num_rows="dynamic", key="cmp_rows", width="stretch")

    if st.button("♛ Compare Sizes", key="btn_compare"):
        account = PropFirmAccount(tier=tier_c, symbol=symbol_c)
        rows = []
        for _, row in edited.iterrows():
            if pd.isna(row["contracts"]) or pd.isna(row["avg_daily_pnl"]) or pd.isna(row["daily_pnl_std"]):
                continue
            sim = PassSimulator(
                account=account, current_balance=balance_c, high_water_mark=hwm_c,
                days_remaining=int(days_c), avg_daily_pnl=float(row["avg_daily_pnl"]),
                daily_pnl_std=float(row["daily_pnl_std"]), simulations=20_000,
            )
            sim.run()
            rows.append({
                "Contracts": int(row["contracts"]),
                "Avg P&L": f"${row['avg_daily_pnl']:.0f}",
                "Std Dev": f"${row['daily_pnl_std']:.0f}",
                "Pass %": round(sim.pass_probability * 100, 1),
                "DD Fail %": round(sim.fail_dd_probability * 100, 1),
                "At 25% rule": "← 25%" if int(row["contracts"]) == account.safe_contracts else "",
            })

        if not rows:
            st.error("♛ No valid rows to compare — fill in contracts/avg P&L/std dev.")
        else:
            result_df = pd.DataFrame(rows)
            st.dataframe(result_df, width="stretch", hide_index=True)
            st.bar_chart(result_df.set_index("Contracts")["Pass %"], color="#C9A84C")
