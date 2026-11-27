---
type: Module
title: binary_metadata_tools.py
description: register_binary_metadata_tools — wraps go_buildinfo.py/rust_cargo_auditable.py as two effect="local" tools.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# binary_metadata_tools.py

A clean `None`/no-section result is a normal, successful outcome here
(the binary just isn't Go, or wasn't built with `cargo auditable`),
never folded into `checks` — only a missing file or the underlying
module's own typed error sets `ok=False`.

## Consumers

None found by grep among this build's own shipped modules — it's a
top-level tool-registration entry point, called directly by
`test_toolkit.py`/`test_agent_loop.py` and by a real caller's own
script (see README's "Using it for real"), the same role
`tools-demo.md` plays for the demo tools (deliberately not a markdown
link: it isn't a real consumer edge, just a sibling comparison, and
this navigator's link extraction can't tell the two apart).
