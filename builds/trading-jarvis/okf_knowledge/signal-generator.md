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

- [risk_manager.py](./risk-manager.md) — `check_risk`'s code-level gate
  independently re-verifies the live signal itself before sizing
  anything, rather than trusting the caller already checked.
- [jarvis_orchestrator.py](./jarvis-orchestrator.md) — `check_signal`
  tool calls `generate_signals`/`latest_signal` directly.
