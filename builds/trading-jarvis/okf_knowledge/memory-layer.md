---
type: Module
title: memory_layer.py
description: MemoryRecord/MemoryStatus/score_candidates — the real Generative Agents scoring formula and lifecycle state machine.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# memory_layer.py

Copied in unmodified from `/builds/agent-memory-layer/` — its own test
suite (57 assertions) proves the lifecycle/scoring mechanics; this
bundle only tracks what in THIS build depends on it.

## Consumers

- [persistence.md](./persistence.md) — every legality check is
  delegated here, never reimplemented.
- [jarvis-memory.md](./jarvis-memory.md) — imports
  `MemoryRecord`/`MemoryStatus`/`score_candidates` directly.
