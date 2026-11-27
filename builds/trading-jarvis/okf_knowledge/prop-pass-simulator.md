---
type: Module
title: prop_pass_simulator.py
description: PassSimulator — Monte Carlo eval pass-probability simulator.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# prop_pass_simulator.py

Imports `PropFirmAccount`/`TPT_TIERS` from
[prop-firm-sizing.md](./prop-firm-sizing.md) directly.

## Consumers

- [jarvis_orchestrator.py](./jarvis-orchestrator.md) — the
  `prop_firm_pass_probability` tool. Never invent `avg_daily_pnl`/
  `daily_pnl_std` — the tool refuses to estimate them.
- `run_strategy.py` — the `--prop-pass-prob`/`--prop-compare` CLI flags
  import `PassSimulator`/`compare_sizing_strategies` directly. Named as
  plain text, not a link: not modeled as its own concept in this bundle.
  Found by `/builds/okf-navigator/drift_check.py`.
