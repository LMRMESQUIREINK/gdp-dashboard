---
type: Module
title: toolkit/skill_compiler.py
description: compile_skill — turns one successful run_chain-shaped run into a new, directly-callable, parametrized tool.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# toolkit/skill_compiler.py

Works one layer down from the source article's own compiler: it
compiles a recorded `run_chain`-shaped `steps` list (named literal
arguments become parameters), not a screen-agent run — there's no
screen loop in this toolkit to compile from.

## Consumers

- [toolkit-init.md](./toolkit-init.md) — re-exports `compile_skill`.
