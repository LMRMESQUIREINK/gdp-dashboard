---
type: Module
title: signal_generator.py
description: RSI/volume-confirmation signal generation (generate_signals, latest_signal).
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# signal_generator.py

Pure pandas/numpy signal logic — RSI period/threshold are separate
params (the "RSI(65) ambiguity" this project's own earlier analysis
resolved).

## Consumers

- [jarvis_orchestrator.py](./jarvis-orchestrator.md) — `check_signal`
  tool calls `generate_signals`/`latest_signal` directly.
- [jarvis_swamp_bridge.py](./jarvis-swamp-bridge.md) — `route_through_bus()`
  imports `generate_signals`/`latest_signal` directly, behind a try/except
  `ImportError` guard.
- `live_monitor.py` / `run_strategy.py` — both import `generate_signals`/
  `latest_signal` at module load. Named as plain text, not a link: neither
  is modeled as its own concept in this bundle.

**A real correction, found by `/builds/okf-navigator/drift_check.py`'s AST
re-grep**: this file previously listed `risk_manager.py` itself as a
consumer, with a description about `check_risk`'s code-level gate
"independently re-verif[ying] the live signal." That's a true statement
about call ORDER inside `jarvis_orchestrator.py` (`check_risk` refuses to
run unless `check_signal` just returned a live BUY), but `risk_manager.py`
never actually imports anything from `signal_generator.py` at the code
level — confirmed directly: `risk_manager.py`'s only top-level import is
`pandas`. The call-order relationship is real; the import-consumer claim
wasn't. Removed rather than left in place now that the distinction is
checkable.
