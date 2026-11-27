---
type: Module
title: demo_policies.py
description: POLICIES / size_check_tool -- the ACP worked example's concrete policy set over prop-firm-sizing.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# demo_policies.py

Mirrors the ACP article's own worked example in shape: the real
"contracts > 5 -> REQUIRES_APPROVAL -> Risk Desk" policy row.

## Consumers (what to re-check if this module's contract changes)

- [demo-write-tiers.md](./demo-write-tiers.md) -- imports
  `size_check_tool` directly, reusing it unmodified as the tool the
  write-tier demo guards.
