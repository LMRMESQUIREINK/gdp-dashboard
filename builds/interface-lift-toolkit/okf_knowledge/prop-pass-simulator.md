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

Copied in unmodified from `/builds/prop-firm-sizing/`. Imports
`PropFirmAccount`/`TPT_TIERS` from
[prop-firm-sizing.md](./prop-firm-sizing.md) directly.

## Consumers

- [tools-demo.md](./tools-demo.md) — the `prop_firm_pass_probability`
  tool only. Never invent `avg_daily_pnl`/`daily_pnl_std` — the tool
  takes them as required arguments and refuses to estimate them.
