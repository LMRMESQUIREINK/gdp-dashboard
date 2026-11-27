---
type: Module
title: toolkit/approval.py
description: ApprovalGate/PendingApproval — the local/outward gate; an outward call is held until explicitly, single-use approved.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# toolkit/approval.py

Adapted from the source article's `effect="outward"` + `post_file`
pattern. Every caller that touches an outward-effect tool goes through
one shared `ApprovalGate` instance.

## Consumers

- [toolkit-init.md](./toolkit-init.md) — re-exports `ApprovalGate`/
  `PendingApproval`.
- [toolkit-chain.md](./toolkit-chain.md) — `run_chain` takes a `gate`
  argument and holds an outward step for approval.
- [toolkit-loop.md](./toolkit-loop.md) — `run_agent` takes a `gate`
  argument and holds an outward tool call the same way.
- [toolkit-skill-compiler.md](./toolkit-skill-compiler.md) —
  `compile_skill` takes a `gate` argument too, since a compiled skill
  can replay a chain that includes an outward step.
