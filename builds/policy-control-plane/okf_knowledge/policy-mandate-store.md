---
type: Module
title: policy/mandate_store.py
description: MandateStore -- a durable grant that outlives one execution, revalidated against the current PolicyEvaluator only at resume.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# policy/mandate_store.py

Closes the gap `/builds/dsh-thread-mandate/`'s README named for this
build: `ApprovalStore` is single-use (pending → approved → consumed),
but nothing in this package modeled a grant that survives a unit of
work ending and resuming many times. `MandateStore` does, read directly
from `deepseek-ai/dsh-superagent-prototype`'s own domain model via that
earlier build: ending a unit of work never revokes its Mandate; only an
explicit `withdraw()` or a failed revalidation **at resume** does, and
revalidation reuses this package's own real `PolicyEvaluator` against
the Mandate's original selector — never a second, disconnected rule.

## Consumers

None found by grep -- no other file in this repo imports
`mandate_store.py` yet (`test_mandate_store.py` exercises it directly,
same convention as every other module's own test file in this bundle,
not modeled as a consumer).
