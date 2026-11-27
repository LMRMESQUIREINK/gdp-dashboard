---
type: Module
title: toolkit/ledger.py
description: Ledger/LedgerRow/TaskCounters — per-task {model calls, tool calls, UI actions, tokens, seconds, checks} row.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# toolkit/ledger.py

Adapted from the source article's `speed_ledger.py`.

## Consumers

- [toolkit-init.md](./toolkit-init.md) — re-exports `Ledger`/
  `LedgerRow`/`TaskCounters`.
- [toolkit-loop.md](./toolkit-loop.md) — `run_agent` takes an optional
  `counters: TaskCounters` and increments it on every model/tool call.
