---
type: Module
title: toolkit/chain.py
description: run_chain — one model call plans several dependent tool calls; "$id.field" references resolve between steps.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# toolkit/chain.py

Stops at the first failed check in a chain — a later step that
referenced the failed step's output never runs.

## Consumers

- [toolkit-init.md](./toolkit-init.md) — re-exports `run_chain`.
- [toolkit-skill-compiler.md](./toolkit-skill-compiler.md) —
  `compile_skill` replays a recorded chain via `run_chain` with
  substituted parameters.
