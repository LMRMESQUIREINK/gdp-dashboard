---
type: Module
title: policy/identity_bridge.py
description: IdentityBridge / SimulatedIdP (VIAB) and DelegatedBoundaryToken (DBO).
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# policy/identity_bridge.py

VIAB's `assert_downstream()` returns a plain context dict with no
token inside it, ever; DBO's `DelegatedBoundaryToken` is the opposite
shape on purpose -- the two are structurally distinct, not two names
for the same mechanism.

## Consumers

- [policy-write-tiers.md](./policy-write-tiers.md) -- `step_up`
  commits require a fresh `VerifiedIdentity` from this module.
