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

- `run_strategy.py` — the `--ask` CLI flag imports `ask_jarvis` directly
  (lazily, inside the flag's own branch). Named as plain text, not a
  link: not modeled as its own concept in this bundle. Found by
  `/builds/okf-navigator/drift_check.py`'s AST re-grep, which walks
  into function bodies, not just module-level imports — this really is
  a real, if conditional, consumer, not a phantom edge.

`live_monitor.py` is a separate entry point onto some of the same
underlying modules (`data_pipeline.py`/`signal_generator.py`/
`risk_manager.py`/`positions_store.py` — see each of their own
Consumers sections), but confirmed directly via grep: it never imports
`jarvis_orchestrator.py` itself, so it isn't listed here.
