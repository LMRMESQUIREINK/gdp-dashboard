---
type: Module
title: prop_firm_position_sizing.py
description: AccountRules/evaluate_size — the simple point-risk/25%-rule/ADR check.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# prop_firm_position_sizing.py

Deliberately standalone — does not import `prop_firm_sizing.py` itself;
`jarvis_orchestrator.py`'s `prop_firm_size_check` tool is what bridges
the two by building an `AccountRules` from a `PropFirmAccount`'s fields.

## Consumers

- [jarvis_orchestrator.py](./jarvis-orchestrator.md) — the
  `prop_firm_size_check` tool only.
