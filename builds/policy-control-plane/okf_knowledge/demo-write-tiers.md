---
type: Module
title: demo_write_tiers.py
description: WRITE_TIER_RULES / set_position_size -- the Blueprint's stage/confirm/commit pattern demonstrated against prop-firm sizing.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# demo_write_tiers.py

Reuses `demo_policies.py`'s real `size_check_tool` unmodified, at the
same 1/5-contract thresholds the existing REQUIRES_APPROVAL policy
already uses.

## Consumers

None found by grep among this build's own shipped modules -- only
`test_write_tiers.py` imports it (test files aren't modeled as
concepts in this bundle, same convention as every other OKF bundle in
this project).
