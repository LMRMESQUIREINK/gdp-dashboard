---
type: Module
title: rust_cargo_auditable.py
description: read_cargo_auditable — the package/dependency graph embedded by `cargo auditable build`.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# rust_cargo_auditable.py

Copied in unmodified from `/builds/go-buildinfo-extractor/` (that
build's Rust sibling extractor). That build's own suite (built via a
real `cargo auditable` install, cross-checked against an independently
written oracle decoder) is where its correctness is actually proven.

## Consumers

- [binary-metadata-tools.md](./binary-metadata-tools.md) — the
  `rust_cargo_auditable_check` tool is the only caller.
