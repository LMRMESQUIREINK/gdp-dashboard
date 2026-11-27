---
type: Module
title: go_buildinfo.py
description: read_go_buildinfo — Go compiler version, main module, dependencies, build settings embedded in a compiled Go binary.
generated: { by: process:claude-code-session, at: 2026-11-27T00:00:00Z }
verified:
  - { by: process:grep-import-scan, at: 2026-11-27T00:00:00Z }
status: stable
stale_after: 2027-02-25T00:00:00Z
---
# go_buildinfo.py

Copied in unmodified from `/builds/go-buildinfo-extractor/`. Works on
ELF and PE; that build's own 13-assertion suite (built via the real Go
toolchain, cross-checked against `go version -m`'s own ground-truth
output) is where its correctness is actually proven — this bundle only
tracks what in THIS toolkit depends on it.

## Consumers

- [binary-metadata-tools.md](./binary-metadata-tools.md) — the
  `go_buildinfo_check` tool is the only caller.
