---
type: Module
title: policy/model.py
description: Effect / Policy / _EFFECT_PRECEDENCE -- the ALLOW/DENY/REQUIRES_APPROVAL enum and policy record shape.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# policy/model.py

The three-state policy model the ACP article describes, with no
internal dependency of its own in this repo.

## Consumers

- [demo-policies.md](./demo-policies.md) -- builds real `Policy`
  records against this module's `Effect` enum.
- [governed-call.md](./governed-call.md) -- imports `Effect` directly.
- [policy-evaluator.md](./policy-evaluator.md) -- imports `Effect`/
  `Policy`/`_EFFECT_PRECEDENCE` directly.
- [policy-init.md](./policy-init.md) -- re-exports `Effect`/`Policy`.
