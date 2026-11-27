---
type: Module
title: policy/write_tiers.py
description: RiskTier / classify_tier / WriteStager / guard_write -- the Blueprint's immediate/confirm/step_up write-tier pattern.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# policy/write_tiers.py

`classify_tier()` defaults an unmatched write to STEP_UP, never
IMMEDIATE -- failing toward more friction, not less.

## Consumers

- [demo-write-tiers.md](./demo-write-tiers.md) -- imports `RiskTier`/
  `TierRule` directly.
