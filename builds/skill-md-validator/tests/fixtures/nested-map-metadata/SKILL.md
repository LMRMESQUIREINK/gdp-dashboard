---
name: nested-map-metadata
description: Do a specific, well-defined thing with a clear scope. Use when the user asks for exactly this kind of task.
version: "0.5.1"
metadata:
  homepage: "https://example.com/docs"
  openclaw:
    emoji: "x"
    homepage: "https://example.com/docs"
---

# Nested Map Metadata

A real shape found in `D4Vinci/Scrapling`'s own official `Scrapling-Skill`
SKILL.md: the leaf key `homepage` legitimately repeats at two different
YAML nesting depths (`metadata.homepage` and `metadata.openclaw.homepage`)
-- valid YAML, not a duplicate top-level key.

## Steps

1. Do the first real step.
2. Do the second real step.
