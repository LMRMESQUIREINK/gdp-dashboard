---
type: Module
title: data_pipeline.py
description: EODHD/FMP OHLCV, quote, and TTM-ratio fetching for the symbol-trading flow.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# data_pipeline.py

Fetches `get_recent_ohlcv`, `fetch_quote`, `fetch_ratios_ttm` from EODHD/FMP.
No live network access from this sandbox — same restriction documented
throughout this project.

## Consumers (what to re-check if this module's contract changes)

- [jarvis_orchestrator.py](./jarvis-orchestrator.md) — `check_signal` and
  `check_fundamentals` call these three functions directly; a signature or
  return-shape change here breaks both tools immediately.
