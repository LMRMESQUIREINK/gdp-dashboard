---
type: Module
title: policy/__init__.py
description: Re-exports ApprovalStore/canonical_hash, evaluate_condition, Decision/PolicyEvaluator, Effect/Policy.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# policy/__init__.py

A real, checked finding, not an assumption: grepping this whole repo
for a bare `import policy` or `from policy import` finds zero hits --
every real caller imports a specific submodule directly
(`from policy.model import Effect, Policy`, etc.). A second, separate
finding: this file's own re-export list predates three later modules
in this package -- `policy/clarification.py`, `policy/identity_bridge.py`,
and `policy/write_tiers.py` are all real, shipped, imported-elsewhere
modules that `policy/__init__.py` itself never imports or re-exports at
all. Neither finding is a bug (nothing in this repo relies on the
package-level surface either way); both are stated here because the
import graph makes them directly checkable rather than assumed.

## Consumers

None found by grep -- no file in this repo does a bare package import
of `policy`, so this file's re-exports are real and correct, just
currently unused by anything here.
