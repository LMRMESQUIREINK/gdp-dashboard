---
type: Module
title: prop_firm_sizing.py
description: PropFirmAccount/TPT_TIERS/CONTRACT_SPECS — the trailing-drawdown-floor-aware account/session model.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# prop_firm_sizing.py

Copied in unmodified from `/builds/prop-firm-sizing/` — same convention
`/builds/trading-jarvis/` and `/builds/prop-firm-mcp-server/` already
follow. The trailing EOD drawdown floor follows the high-water mark,
not the starting balance (see `/notes/prop-firm-sizing-analysis.md`).

## Consumers

- [prop-pass-simulator.md](./prop-pass-simulator.md) — imports
  `PropFirmAccount`/`TPT_TIERS` directly.
- [tools-demo.md](./tools-demo.md) — both demo prop-firm tools
  construct a `PropFirmAccount` directly, and read `CONTRACT_SPECS`/
  `TPT_TIERS` for their own known-tier/known-symbol checks.
