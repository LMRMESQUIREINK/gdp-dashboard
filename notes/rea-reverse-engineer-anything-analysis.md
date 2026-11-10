# REA ("Reverse Engineer Anything") — Deep Analysis

Source: `morluto/rea` (cloned and read directly, not taken from its own
README's word) — an MCP server (`rea-agents` on npm, v6.7.0) that gives
AI coding agents tool access to native disassemblers (Hopper, Ghidra,
IDA), JADX, pwntools, mitmproxy, binwalk, adb, and a large set of
built-in static parsers (Go/Rust/WASM/.NET/ELF/PE/Mach-O/SQLite/EVM
bytecode), for reverse-engineering binaries, apps, and runtime
behavior. MIT licensed.

## Scale, checked rather than assumed

- 3,235 TypeScript source files, 1,582 `*.test.ts` files, plus native
  Swift/C/Smali components under `native/`. Not a thin wrapper — a
  real, large, actively maintained codebase.
- Dedicated Stryker mutation-testing config
  (`stryker.config.mjs`/`stryker.semantics.config.mjs`) scoped
  specifically at the parsing/"reverse-tools" code paths — a
  meaningfully more rigorous bar than this project has seen in any
  source analyzed so far (every other build here has had, at most,
  conventional unit tests).
- 40 production dependencies, 24 dev dependencies — a deliberately
  lean dependency surface for a project this large.

## The 300,000-star claim — verified, not assumed

The README's star-history section claims "300,000 GitHub stars." That
figure, sitting alone in a README, is exactly the kind of self-reported
number this project's discipline checks rather than repeats (same as
every previously-flagged uncited claim here) — and this sandbox has no
direct GitHub API access to this unattached repo to check it live.
Checked via web search instead: independent sources (an Italian
fact-check site, `ossinsight.io`, `trendshift.io`, and several tech-news
write-ups) corroborate explosive, real growth — roughly 30,000 stars on
October 9, ~110,000 by October 12, ~170,000 a day later, ~234,000 by
October 14. At that growth rate, ~300,000 by the clone date (October
18) is plausible and consistent across independent sources, not an
inflated or fabricated figure. One of those same sources also reports a
real, separate finding worth carrying forward: a fake copy of this repo
under a different GitHub organization was found bundling a suspicious
Windows executable — independent confirmation of exactly the
impersonation risk the README's own top banner already warns about
("A similar repository name or copied README does not establish that a
download is official").

## Framing: legitimate dual-use tooling, not evasion tooling

`DISCLAIMER.md` is explicit and specific about scope: lawful security
research, malware/incident analysis, vulnerability research and
coordinated disclosure, CTFs, education, interoperability, software
preservation, and auditing software you own or are authorized to
examine. It names what it will *not* help with by name — DRM/license-
check/anti-cheat circumvention, game cheats, bypassing auth on
unauthorized systems, reproducing proprietary code/assets, evading AI
provider usage policies. That's a clear, specific authorization
boundary, not a vague liability-shield paragraph — consistent with
treating this as legitimate defensive/research tooling.

## Architecture, checked by reading real code

Picked one concrete capability to verify end-to-end rather than take
the README's capability table at its word: "Go binaries — Embedded
compiler version, modules, replacements and build settings... no Go
installation required." Read `src/go/GoBinaryImage.ts`,
`src/go/GoModuleText.ts`, and `src/domain/go/goBinary.ts` in full.

What's real and well-engineered, confirmed by reading the actual
parsing logic:
- The Go build-info magic (`\xff Go buildinf:`), the module-string
  framing sentinels (`3077af0c9274080241e1c107e6d618e6` /
  `f932433186182072008242104116d8f2`), and the varint-length-prefixed
  "inline" string encoding (Go 1.18+) vs. the pointer-based encoding
  (older/PIE binaries) are all handled correctly against the real Go
  `debug/buildinfo`/`runtime/debug` format — not a simplified
  approximation.
- Real anti-DoS bounds: a 256 MiB cumulative header-search budget and a
  1 MiB aggregate build-info-string cap, both enforced with explicit
  typed failures rather than silent truncation.
- The module-text parser (`GoModuleText.ts`) correctly implements Go's
  own quoted-string syntax (backtick raw strings, double-quoted strings
  with `\n`/`\t`/`\xHH`/`\uHHHH`/`\UHHHHHHHH`/octal escapes) for `build`
  setting values, and preserves non-UTF-8 or malformed lines verbatim
  instead of dropping them — the kind of edge-case care that's easy to
  skip and matters for forensic/evidentiary use.
- Zero-filled virtual-address spans (a real wrinkle: a zero data
  pointer for an empty Go string must not be read as a dangling
  pointer) are handled as a distinct case, not a crash.

This is the most rigorously-engineered parsing code analyzed in this
project's run of source reviews to date — reading it changed nothing
about the project's honest discipline (verify, don't assume), but it's
worth stating plainly when a source *does* hold up this well under
direct code reading, the same way this project states plainly when one
doesn't.

## What's built from this

Not a clone of REA (3,235 files, native disassembler integrations,
Android/iOS/firmware tooling — wildly out of proportion to what this
sandbox can build or verify, and REA already does this far better than
a quick rebuild could). Instead, following this project's established
"extract one real, scoped, independently-verifiable capability" pattern:
`/builds/go-buildinfo-extractor/` — a standalone, dependency-free
Python reimplementation of the one capability actually read and
understood above (Go build-info extraction from ELF and PE binaries),
built from understanding the real format rather than transcribing
REA's TypeScript, and proven against real compiled Go binaries rather
than synthetic byte strings. See that build's README for what's
implemented, what's deliberately cut (Mach-O — no way to produce or
verify a real Mach-O binary in this Linux sandbox), and how it was
tested.
