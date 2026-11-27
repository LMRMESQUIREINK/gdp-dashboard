---
type: Module
title: jarvis_orchestrator.py
description: The Claude tool-dispatch loop tying all four tool categories (symbol-trading, prop-firm, memory, OKF impact) together.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# jarvis_orchestrator.py

The top-level consumer of every other module in this bundle — see each
module's own "Consumers" section for what it wires here. No live
Anthropic API access from this sandbox, same standing restriction
documented throughout this project.

## Consumers

None modeled in this bundle — `run_strategy.py` and `live_monitor.py`
are separate entry points onto some of the same underlying modules, not
callers of this orchestrator itself.
