---
type: Module
title: tools_demo.py
description: register_demo_tools — three tools (prop_firm_size_check, prop_firm_pass_probability, publish_report) demonstrating local vs. outward effects.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# tools_demo.py

Not toy stand-ins: wraps the same already-proven
`PropFirmAccount`/`AccountRules`/`PassSimulator` classes every other
interface in this project uses. `publish_report` is the one
`effect="outward"` tool in this toolkit, demonstrating the approval
gate end to end.

## Consumers

None found by grep among this build's own shipped modules — it's a
top-level tool-registration entry point, called directly by
`test_toolkit.py`/`test_agent_loop.py` and by a real caller's own
script (see README's "Using it for real"), the same role
`binary-metadata-tools.md` plays for the binary-metadata tools
(deliberately not a markdown link, for the same reason noted in that
file: it isn't a real consumer edge).
