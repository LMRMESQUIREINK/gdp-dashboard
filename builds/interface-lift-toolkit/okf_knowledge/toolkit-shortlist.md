---
type: Module
title: toolkit/shortlist.py
description: shortlist_groups/score_groups — regex-scored tool-group selection (clear winner vs. top-N fallback).
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# toolkit/shortlist.py

Not wired into any tool-registration module yet — only consumed via
`toolkit/__init__.py`'s re-export, and exercised directly by
`test_toolkit.py`'s own shortlist checks.

## Consumers

- [toolkit-init.md](./toolkit-init.md) — re-exports `score_groups`/
  `shortlist_groups`.
