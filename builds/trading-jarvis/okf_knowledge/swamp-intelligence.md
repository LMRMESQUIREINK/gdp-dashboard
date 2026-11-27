---
type: Module
title: swamp_intelligence.py
description: Task Tree / Event Packet / Priority / ActivationGate primitives.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# swamp_intelligence.py

Checked section-by-section against the real Brain Spec in an earlier
round (Addendum 3, `/notes/trading-jarvis-analysis.md`) — `EventPacket`
fields and `Priority` values match exactly; `risk_score` validates its
1-100 floor in code, not just in a comment.

## Consumers

- [jarvis-swamp-bridge.md](./jarvis-swamp-bridge.md) — the one real
  importer of this module's primitives.
