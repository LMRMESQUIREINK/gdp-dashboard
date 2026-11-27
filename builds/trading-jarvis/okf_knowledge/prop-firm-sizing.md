---
type: Module
title: prop_firm_sizing.py
description: PropFirmAccount/SessionState/TPT_TIERS — trailing-drawdown-floor-aware account/session model.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# prop_firm_sizing.py

The trailing EOD drawdown floor follows the high-water mark, not the
starting balance — the key insight the source playbook under-explains
(see `/notes/prop-firm-sizing-analysis.md`).

## Consumers

- [prop-pass-simulator.md](./prop-pass-simulator.md) — imports
  `PropFirmAccount`/`TPT_TIERS` directly.
- [jarvis_orchestrator.py](./jarvis-orchestrator.md) — all three
  `prop_firm_*` tools construct a `PropFirmAccount` directly.
