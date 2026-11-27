---
type: Module
title: policy/approval_store.py
description: ApprovalStore / canonical_hash -- canonical-JSON+SHA-256 payload-bound approval records.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# policy/approval_store.py

Closes the one property `/builds/agent-checkpoint-layer/` didn't have:
approving one request's parameters can never let a different request
execute under that same approval.

## Consumers

- [governed-call.md](./governed-call.md) -- `governed_call`/
  `resume_governed_call` both call `ApprovalStore` directly.
- [policy-write-tiers.md](./policy-write-tiers.md) -- `WriteStager`
  reuses `canonical_hash()` directly.
- [policy-init.md](./policy-init.md) -- re-exports `ApprovalStore`/
  `canonical_hash`.
