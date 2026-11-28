---
type: Module
title: toolkit/result.py
description: result() — the {ok, summary, files, checks} contract; ok is always derived from checks, never set by hand.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# toolkit/result.py

A tool can't accidentally report success while one of its own checks
failed, because `ok` is computed from `checks`, not passed in.

## Consumers

- [toolkit-init.md](./toolkit-init.md) — re-exports `result`.
- [binary-metadata-tools.md](./binary-metadata-tools.md) — every tool
  function builds its return value with `result()`.
- [tools-demo.md](./tools-demo.md) — same, for all three demo tools.
- `okf_impact_tool.py` — same, for `check_module_impact`. A real
  omission from the round that added this file, caught by
  `/builds/okf-navigator/drift_check.py`; named as plain text, not a
  link, since this file isn't modeled as its own concept in this bundle.
- `thread_gate_tool.py` — same, for `thread_gate_request`/
  `thread_gate_execute`. Same convention immediately above: named as
  plain text, not modeled as its own concept.
