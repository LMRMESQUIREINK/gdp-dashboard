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
  tool is the only caller; it refuses to call `evaluate_trade` at all
  unless `check_signal` itself just returned a live BUY.
