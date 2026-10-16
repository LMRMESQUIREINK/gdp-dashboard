"""
A concrete policy set, in this project's own domain, matching the ACP
article's own worked example exactly in shape:

    article's example:  Billing Agent → Telco Billing MCP → createRefund
                         → amount > 1000 → REQUIRES_APPROVAL → Finance

    this project's:      trading-jarvis → prop-firm-mcp-server →
                         prop_firm_size_check → contracts > 5 →
                         REQUIRES_APPROVAL → Risk Desk

Two policies on the SAME operation, same as the article's point that
"the API operation remains the same. The governance decision changes
based on the parameter": a low-priority baseline ALLOW for routine sizes,
and a higher-priority REQUIRES_APPROVAL that only applies once
`contracts > 5` — so small requests sail through and large ones pause for
a human, without needing two different tool names.

The real computation behind ALLOW is `evaluate_size()` from
prop_firm_position_sizing.py (copied in unmodified, same convention as
every other interface in this project) — not a stub.
"""
from __future__ import annotations

from prop_firm_position_sizing import AccountRules, evaluate_size
from prop_firm_sizing import PropFirmAccount

from policy.model import Effect, Policy

POLICIES = [
    Policy(
        id="allow-trading-jarvis-routine-size",
        name="Allow routine position-size checks from trading-jarvis",
        effect=Effect.ALLOW,
        priority=10,
        agent="trading-jarvis",
        tool="prop-firm-mcp-server",
        operation="prop_firm_size_check",
        condition=None,
    ),
    Policy(
        id="require-approval-large-size",
        name="Require Risk Desk approval for size checks over 5 contracts",
        effect=Effect.REQUIRES_APPROVAL,
        priority=50,
        agent="trading-jarvis",
        tool="prop-firm-mcp-server",
        operation="prop_firm_size_check",
        condition={"field": "contracts", "op": ">", "value": 5},
        approval_role="Risk Desk",
    ),
]


def size_check_tool(tier: str, symbol: str, contracts: int) -> dict:
    """The real tool `governed_call`'s ALLOW path (or a resumed
    REQUIRES_APPROVAL path) actually invokes — same evaluate_size() call
    every other interface in this project makes, not a reimplementation."""
    account = PropFirmAccount(tier=tier, symbol=symbol)
    rules = AccountRules(
        account_equity=account.starting_balance, daily_loss_limit=account.daily_loss_limit,
        eod_trailing_drawdown=account.eod_trailing_dd, max_contracts=account.max_contracts,
        point_value=account.point_value,
    )
    return evaluate_size(rules, contracts, average_daily_range_points=None)
