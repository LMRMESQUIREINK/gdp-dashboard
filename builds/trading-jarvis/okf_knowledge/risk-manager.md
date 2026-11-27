---
type: Module
title: risk_manager.py
description: evaluate_trade — position sizing, stop/2R target, portfolio heat.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# risk_manager.py

`evaluate_trade()` accepts `existing_positions` for real multi-position
portfolio heat (added in an earlier round once the real file arrived —
see `/notes/trading-jarvis-analysis.md` addenda).

## Consumers

- [jarvis_orchestrator.py](./jarvis-orchestrator.md) — the `check_risk`
  tool; it refuses to call `evaluate_trade` at all unless `check_signal`
  itself just returned a live BUY. A real correction, found by
  `/builds/okf-navigator/drift_check.py`'s AST re-grep: this file's own
  prior text called `check_risk` "the only caller," which was wrong even
  at the time it was written — see the other three real callers below.
- [jarvis_swamp_bridge.py](./jarvis-swamp-bridge.md) — `route_through_bus()`
  imports `evaluate_trade` directly, behind a try/except `ImportError`
  guard.
- `live_monitor.py` / `run_strategy.py` — both import `evaluate_trade` at
  module load. Named as plain text, not a link: neither is modeled as its
  own concept in this bundle.
