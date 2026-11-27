---
type: Module
title: policy/conditions.py
description: evaluate() -- a safe, non-eval() nested-dict condition evaluator.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# policy/conditions.py

A deliberate security choice the ACP article itself never addresses:
conditions are evaluated against a safe structural interpreter, never
Python's own `eval()`.

## Consumers

- [policy-evaluator.md](./policy-evaluator.md) -- imports
  `evaluate as evaluate_condition` directly.
- [policy-write-tiers.md](./policy-write-tiers.md) -- `classify_tier()`
  reuses the same safe evaluator.
- [policy-init.md](./policy-init.md) -- re-exports `evaluate as
  evaluate_condition`.
