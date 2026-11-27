"""A concrete tier-classification rule set, in this project's own domain
— same convention as demo_policies.py: the real operation this exercises
is `size_check_tool()`, reused unmodified from demo_policies.py, not a
reimplementation.

Risk classification mirrors the ACP policy's own existing threshold
(contracts > 5 already requires Risk Desk approval there) but adds the
tier granularity the Blueprint article's write-tier pattern is actually
about: not just "does this need a human," but "how much friction does
committing it need":

  contracts <= 1   -> immediate  (trivial, commits on request)
  1 < contracts <= 5 -> confirm    (must be staged, then confirmed against
                                     the exact pinned payload)
  contracts > 5     -> step_up     (confirm, PLUS a freshly re-verified
                                     identity at commit time — the same
                                     threshold where demo_policies.py's
                                     own REQUIRES_APPROVAL policy already
                                     kicks in, so a large request is both
                                     routed to a human AND requires
                                     step-up re-authentication to commit)
"""
from __future__ import annotations

from demo_policies import size_check_tool
from policy.write_tiers import RiskTier, TierRule

WRITE_TIER_RULES = [
    TierRule(tier=RiskTier.IMMEDIATE, condition={"field": "contracts", "op": "<=", "value": 1}),
    TierRule(tier=RiskTier.CONFIRM, condition={"field": "contracts", "op": "<=", "value": 5}),
    TierRule(tier=RiskTier.STEP_UP, condition=None),  # anything larger
]


def set_position_size(tier: str, symbol: str, contracts: int) -> dict:
    """The real tool a committed write actually invokes — reuses
    size_check_tool() directly."""
    return size_check_tool(tier=tier, symbol=symbol, contracts=contracts)
