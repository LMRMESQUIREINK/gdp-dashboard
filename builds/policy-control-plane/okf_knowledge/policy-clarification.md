---
type: Module
title: policy/clarification.py
description: ClarificationStore -- model-initiated clarification, kept architecturally distinct from policy-enforced approval.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# policy/clarification.py

Deliberately its own table and id space, never a second status bolted
onto `ApprovalRecord` -- answering a clarification must leave an
unrelated pending approval's status completely untouched, and vice
versa.

## Consumers

None found by grep among this build's own shipped modules -- only
`test_clarification.py` imports it directly. Note: `policy/__init__.py`
also does NOT re-export this module (see its own concept file) --
a separate, already-stated finding, not repeated as a consumer edge
here.
