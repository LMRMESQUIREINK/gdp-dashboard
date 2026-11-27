---
type: Module
title: toolkit/loop.py
description: run_agent — the real tool-use loop, in Anthropic's real message shape.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# toolkit/loop.py

An outward tool call is never executed inline: it's held, and a
`{"pending": ...}` preview comes back as the tool result.

## Consumers

- [toolkit-init.md](./toolkit-init.md) — re-exports `run_agent`.

None of this build's own tool-registration modules
(`binary-metadata-tools.md`, `tools-demo.md`) import `run_agent`
directly — it's driven only from `test_agent_loop.py` and from a real
caller's own script (see README's "Using it for real"). Named here as
plain code text, not a markdown link: a link would be a false
"consumer" edge for a relationship this sentence is explicitly denying.
