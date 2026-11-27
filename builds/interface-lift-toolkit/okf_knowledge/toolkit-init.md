---
type: Module
title: toolkit/__init__.py
description: Re-exports every toolkit submodule's public names at the package level.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# toolkit/__init__.py

A real, checked finding, not an assumption: grepping this entire repo
for `import toolkit` or `from toolkit import` (a bare package-level
import) finds zero hits — every real consumer, including this README's
own "Using it for real" usage example, imports a specific submodule
directly (`from toolkit.registry import ToolRegistry`,
`from toolkit.approval import ApprovalGate`, etc.), never the package
aggregator this file provides. The re-exports here are real and
correct, just currently unused by anything in this repo.

## Consumers

None found by grep — this file re-exports every other `toolkit/`
module but nothing in this repo actually imports `toolkit` (the bare
package) itself.
