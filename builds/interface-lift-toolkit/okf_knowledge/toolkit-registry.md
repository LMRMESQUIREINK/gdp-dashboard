---
type: Module
title: toolkit/registry.py
description: ToolRegistry/@tool — derives an Anthropic-shaped JSON schema from a function's type hints + docstring.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# toolkit/registry.py

One `ToolRegistry` instance per agent (not a module-level global dict),
so a test and the real app never collide on the same tools. Schemas
come out in Anthropic's native tool-use shape, matching
`/builds/trading-jarvis/jarvis_orchestrator.py`'s `TOOLS` convention.

## Consumers (what to re-check if this module's contract changes)

- [toolkit-init.md](./toolkit-init.md) — re-exports `ToolRegistry`/`ToolSpec`.
- [toolkit-chain.md](./toolkit-chain.md) — `run_chain` calls
  `registry.call()`/`registry.effect_of()`.
- [toolkit-loop.md](./toolkit-loop.md) — `run_agent` calls
  `registry.schemas()`/`registry.call()`/`registry.effect_of()`.
- [toolkit-skill-compiler.md](./toolkit-skill-compiler.md) — `compile_skill`
  calls `registry.register_raw()`.
- [binary-metadata-tools.md](./binary-metadata-tools.md) — imports
  `ToolRegistry` to register `go_buildinfo_check`/`rust_cargo_auditable_check`.
- [tools-demo.md](./tools-demo.md) — imports `ToolRegistry` to register
  the three demo tools.
- `okf_impact_tool.py` — imports `ToolRegistry` to register
  `check_module_impact`. A real omission from the round that added this
  file, caught by `/builds/okf-navigator/drift_check.py`'s AST re-grep
  rather than left in place: this file itself isn't modeled as its own
  concept in this bundle, so it's named here as plain text, not a link.
- `thread_gate_tool.py` — imports `ToolRegistry` to register
  `thread_gate_request`/`thread_gate_execute`, wiring
  `/builds/dsh-thread-mandate/`'s gate-only Eval onto this toolkit's real
  dispatch. Same convention as `okf_impact_tool.py` immediately above:
  not modeled as its own concept here, named as plain text.
