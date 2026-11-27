---
type: Module
title: jarvis_memory.py
description: remember/recall/supersede_preference wiring over the real MemoryStore/SQLiteMemoryStore.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# jarvis_memory.py

Applies `positions_store.py`'s own fixed-`subject_id`, no-auth-layer
convention exactly. Deliberately does NOT auto-supersede a preference
on topic match — no embedding/keyword layer exists here to judge "same
topic" honestly.

## Consumers

- [jarvis_orchestrator.py](./jarvis-orchestrator.md) — the
  `remember_preference`/`recall_preferences`/`supersede_preference`
  tools.
