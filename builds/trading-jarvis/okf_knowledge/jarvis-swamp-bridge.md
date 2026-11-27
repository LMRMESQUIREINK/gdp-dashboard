---
type: Module
title: jarvis_swamp_bridge.py
description: decompose_objective — routes an objective through a governed Task Tree before handing off to real Jarvis modules.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# jarvis_swamp_bridge.py

`approval_required=True` is hard-coded on risk-bearing steps — a
code-level governance gate, not a system-prompt instruction.

## Consumers

- [jarvis_orchestrator.py](./jarvis-orchestrator.md) — the
  `swamp_decompose` tool, which the system prompt instructs Claude to
  call FIRST for any per-symbol question.
- `run_strategy.py` — the `--swamp` CLI flag imports `route_through_bus`
  directly (lazily, inside the flag's own branch). Named as plain text,
  not a link: not modeled as its own concept in this bundle. Found by
  `/builds/okf-navigator/drift_check.py`.
