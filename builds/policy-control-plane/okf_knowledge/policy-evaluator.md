---
type: Module
title: policy/evaluator.py
description: Decision / PolicyEvaluator -- deterministic priority+effect-precedence policy resolution.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# policy/evaluator.py

Reproduces the ACP article's exact deterministic resolution rules --
ALLOW/DENY/REQUIRES_APPROVAL with priority+effect precedence.

## Consumers

- [governed-call.md](./governed-call.md) -- `governed_call` calls
  `PolicyEvaluator` directly.
- [policy-init.md](./policy-init.md) -- re-exports `Decision`/
  `PolicyEvaluator`.
