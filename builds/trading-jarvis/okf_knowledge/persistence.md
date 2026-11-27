---
type: Module
title: persistence.py
description: SQLiteMemoryStore — WAL-journaled, cross-process-durable memory persistence.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# persistence.py

Copied in unmodified from `/builds/agent-memory-layer/`. Proven by a
genuine cross-process restart test in that build's own suite, not
two in-process objects sharing one Python process.

## Consumers

- [jarvis-memory.md](./jarvis-memory.md) — the one real importer in
  this build.
