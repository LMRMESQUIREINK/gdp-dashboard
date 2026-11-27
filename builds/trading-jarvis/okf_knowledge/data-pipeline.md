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
- [jarvis_swamp_bridge.py](./jarvis-swamp-bridge.md) — `route_through_bus()`
  imports `get_recent_ohlcv` directly, behind a try/except `ImportError`
  guard, not only through `jarvis_orchestrator.py`. Found by
  `/builds/okf-navigator/drift_check.py`, a real AST re-grep against this
  bundle's own claims — this consumer was never documented before.
- `live_monitor.py` / `run_strategy.py` — both import `get_recent_ohlcv`/
  `fetch_realtime` at module load, same real finding as above. Named here
  as plain text, not a link: neither is modeled as its own concept in this
  bundle (same convention as every `test_*.py` file), but a real import is
  a real import.
