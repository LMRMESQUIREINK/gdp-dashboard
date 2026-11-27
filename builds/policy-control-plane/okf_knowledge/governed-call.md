---
type: Module
title: governed_call.py
description: governed_call / resume_governed_call -- the enforcement boundary where the real tool is provably unreachable on DENY or pending REQUIRES_APPROVAL.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# governed_call.py

This is the one function every real caller is meant to go through --
it wires `policy/approval_store.py`, `policy/evaluator.py`, and
`policy/model.py` together, but is itself never imported by another
shipped module.

## Consumers

None found by grep among this build's own shipped modules -- it's a
top-level entry point, called directly by `test_policy.py`/
`test_clarification.py` and by a real caller's own script.
