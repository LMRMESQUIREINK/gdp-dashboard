---
type: Module
title: positions_store.py
description: Persisted open-position records feeding existing_positions into risk_manager.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# positions_store.py

A single-trader, no-auth-layer convention (same as `jarvis_memory.py`'s
own fixed `subject_id`).

## Consumers

- [jarvis-swamp-bridge.md](./jarvis-swamp-bridge.md) — imported as
  `positions` for the Task Tree's own position awareness.
- [jarvis_orchestrator.py](./jarvis-orchestrator.md) — `check_risk`
  reads real recorded positions before computing portfolio heat.
- `live_monitor.py` / `run_strategy.py` — both import `positions_store`
  (as `positions`) at module load. Named as plain text, not a link:
  neither is modeled as its own concept in this bundle. Found by
  `/builds/okf-navigator/drift_check.py`.
