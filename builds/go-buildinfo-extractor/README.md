# Go Build-Info Extractor (+ Rust cargo-auditable Extractor)

Two standalone, dependency-free Python tools that read the metadata a
compiler embeds in a binary without needing the original toolchain or
source:

- **`go_buildinfo.py`** — the compiler version, main module
  path+version, dependency list (including local `replace`
  directives), and build settings the Go toolchain embeds in every
  compiled binary — the same data `go version -m` prints. Reads ELF
  and PE binaries directly.
- **`rust_cargo_auditable.py`** — the package/dependency graph (name,
  version, source, dependency edges, cyclic-dependency detection)
  embedded by `cargo auditable build` in a `.dep-v0` section. Also ELF
  and PE.

Built from a deep analysis of `morluto/rea`'s MCP reverse-engineering
toolkit, which documents both capabilities as sibling static-parsing
features ("Go binaries — Embedded compiler version, modules,
replacements and build settings"; Rust `.dep-v0` dependency metadata).
Full analysis: `/notes/rea-reverse-engineer-anything-analysis.md`.

## Usage

```bash
python3 go_buildinfo.py /path/to/binary
python3 rust_cargo_auditable.py /path/to/binary
```

```json
{
  "go_binary": true,
  "format": "elf",
  "go_version": "go1.24.7",
  "module_path": "example.com/mainmod",
  "main_module": { "path": "example.com/mainmod", "version": "(devel)", "sum": "", "replacement": null },
  "dependencies": [
    {
      "path": "example.com/depmod",
      "version": "v0.0.0",
      "sum": null,
      "replacement": { "path": "../depmod", "version": "(devel)", "sum": "", "replacement": null }
    }
  ],
  "settings": { "-buildmode": "exe", "CGO_ENABLED": "0", "GOOS": "linux", "GOARCH": "amd64", "...": "..." }
}
```

```json
{
  "cargo_auditable": true,
  "section_name": ".dep-v0",
  "packages": [
    {"name": "itoa", "version": "1.0.18", "source": "crates.io", "kind": null, "dependencies": [], "root": false},
    {"name": "localdep", "version": "0.3.1", "source": "local", "kind": null, "dependencies": [], "root": false},
    {"name": "maincrate", "version": "1.2.3", "source": "local", "kind": null, "dependencies": [0, 1], "root": true}
  ],
  "root_package_index": 2,
  "dependency_edges": [[2, 0], [2, 1]],
  "cyclic_dependency_indices": []
}
```

Or import either as a library — `go_buildinfo.read_go_buildinfo(data: bytes)`
returns a `GoBuildInfo | None`, and `rust_cargo_auditable.read_cargo_auditable(data: bytes)`
returns a `RustAuditableMetadata | None`. In both, `None` means the
binary doesn't carry that metadata (not a Go binary / not built with
`cargo auditable`, or the header/section was stripped) — a normal,
successful outcome, not an error.

## Where this came from, and what was and wasn't copied

REA's own TypeScript implementation (`src/go/GoBinaryImage.ts`,
`src/go/GoModuleText.ts`) was read in full to understand the real
format correctly — the build-info magic bytes, the module-string
framing sentinels, the inline-vs-pointer string encoding, and Go's own
quoted-string syntax for build settings are not things to guess at.
Nothing was copied from it (REA is MIT-licensed, so that would even be
permitted, but the point here was to build an independent, understood
implementation, not transcribe one): this is a fresh Python
implementation, and it diverges from REA's in real, stated ways:

- **No virtual-address-precise header search.** REA walks the actual
  section/segment table and only searches bytes that are really mapped
  at a given virtual address, with an exact 16-byte *virtual-address*
  alignment check. This tool searches the whole file for the magic
  bytes and checks 16-byte *file-offset* alignment instead — a weaker
  but much simpler proxy that happened to work correctly against every
  real binary tested below. A deliberately handcrafted binary with the
  magic bytes planted at a false-positive file offset could fool this
  tool's search in a way REA's wouldn't; REA's own resource-budget
  comments (a 256 MiB cumulative search cap) suggest this is a genuine,
  if narrow, attack surface it was built to resist.
- **No Mach-O support.** This sandbox is Linux-only with no way to
  produce *or verify* a Mach-O binary's build info, and this project's
  standing discipline is to not ship a code path that was never
  actually run against real output. Confirmed working as a clean
  rejection rather than a crash: cross-compiling a real Mach-O binary
  (`GOOS=darwin GOARCH=arm64 go build`) and running it through this
  tool gives `error: only ELF and PE containers are supported`, exit
  code 1 — not a traceback.
- **The pointer-encoding path is now verified, not just implemented.**
  Modern Go (tested here: 1.24.7) always uses the newer "inline" string
  encoding for both ELF and PE output, and this sandbox has no
  toolchain old enough on `PATH` by default to exercise the older
  pointer-based encoding (Go 1.13–1.17). Direct downloads from
  `go.dev` are blocked by this sandbox's egress proxy (403), but Go's
  own `GOTOOLCHAIN=go1.17.13` mechanism fetches a pinned old version
  through the Go module proxy instead, which this sandbox does allow —
  so a real Go 1.17.13 binary (both ELF and cross-compiled PE) was
  built and run through this tool for real. **This caught a real bug**:
  the PE path normalized the *outer* version/module pointers against
  `ImageBase` but not the *inner* string-data pointer resolved one
  indirection further in, so every PE pointer-encoded binary failed
  with `address ... is not mapped by any segment`. Fixed by moving the
  `ImageBase` subtraction into `_AddressMapper` itself, so every
  address lookup — at any indirection depth — goes through the same
  normalization rather than relying on each call site to remember it.
  Now 2/2 real pointer-encoding tests pass (ELF and PE), with no
  regression to the 11 inline-encoding tests.

REA's Rust implementation (`src/rust/RustAuditableReader.ts`,
`src/rust/RustBinaryImage.ts`, `src/domain/rust/rustBinary.ts`) was
read the same way — in full, as a correctness reference, nothing
copied — to understand the cargo-auditable JSON schema, the zlib
framing, and the SCC-based cyclic-dependency check before writing
`rust_cargo_auditable.py` fresh. Divergences:

- **No Mach-O support**, same reason and same discipline as the Go
  extractor above — no way to produce or verify a Mach-O `.dep-v0`
  section in this Linux sandbox.
- **The bonus `rustc_commit` inference feature in REA's
  `RustBinaryImage.ts`** (scanning read-only sections for a
  `/rustc/<40-hex-hash>/` pattern) was **not** carried over — it's a
  nice-to-have unrelated to the dependency-graph extraction this build
  actually set out to do, and adding it untested would be exactly the
  kind of scope creep this project's discipline avoids.
- **Cycle detection uses the standard Tarjan's SCC algorithm**
  (iterative, not recursive) rather than REA's own
  `cyclicDependencyIndices()` (an iterative DFS-postorder +
  reversed-graph-components approach) — different algorithm, same
  correctness property (a package is cyclic iff its strongly-connected
  component has more than one member, or is a self-loop), verified
  against hand-built graphs covering both cases since crates.io itself
  can't produce a real one to test against.

## Also wired into `/builds/interface-lift-toolkit/`

Both extractors are copied (unmodified) into
`/builds/interface-lift-toolkit/` and registered there as two new
`effect="local"` typed tools (`go_buildinfo_check`,
`rust_cargo_auditable_check`) in `binary_metadata_tools.py` — the
toolkit's `{ok, summary, files, checks}` result contract maps onto
these readers directly. See that build's own README for the tool
schemas and its test coverage (schema derivation, a missing-file usage
error, and real-binary checks against both a real Go binary and a real
cargo-auditable Rust binary, cross-checked against a direct call to
these same reader functions).

## Verified against real compiled binaries, not synthesized bytes

### Go: `tests/test_go_buildinfo.py` — 13/13 passing

Builds its own fixtures at test time (a real two-module project — a
main module with a local dependency pulled in via a `replace`
directive, so the test exercises a genuine `dep` + `=>` replacement
pair, not a synthetic one) using the system `go` toolchain, and checks
results against `go version -m`'s own output as ground truth rather
than hand-typed expected values:

- ELF binary (modern Go 1.24, "inline" encoding): compiler version,
  module path, main module, the real local-replaced dependency, and
  all 6 build settings match `go version -m` exactly.
- Cross-compiled PE binary (`GOOS=windows GOARCH=amd64`, "inline"
  encoding): same checks, confirming the PE section-table/RVA mapping
  is correct for a real Windows binary — built and parsed without ever
  needing Windows.
- **Pointer-encoding path, both ELF and PE** (real Go 1.17.13 binaries,
  fetched via `GOTOOLCHAIN=go1.17.13` through the Go module proxy —
  direct `go.dev` downloads are blocked by this sandbox's egress
  proxy): both match `go version -m` ground truth exactly. This is the
  path that caught the real PE `ImageBase`-normalization bug described
  above; skips cleanly (not fails) if the module proxy isn't reachable.
- A plain C binary (compiled with `gcc`) correctly reports
  `go_binary: false` rather than crashing or false-positively matching.
- Malformed-input handling: a corrupted flags byte and a truncated
  header both raise the typed `GoBuildInfoError`, not a raw exception.

**A real bug found and fixed during this testing, not assumed away**:
an early version let a corrupted byte inside the version/module string
raise a bare `UnicodeDecodeError` straight out of the function instead
of the tool's own typed error — caught by a deliberate byte-flip test,
not by inspection. Fixed by routing every UTF-8 decode through
`_decode_utf8_strict()`, which wraps `UnicodeDecodeError` into
`GoBuildInfoError`. A 2,000-iteration fuzz test (1–20 random byte flips
within the header+4000-byte window, run against both the ELF and PE
fixtures, deterministic seed) now asserts zero uncaught exceptions of
any kind — only a clean result or a typed `GoBuildInfoError` — and is
part of the permanent regression suite so this class of bug can't
silently come back.

```bash
python3 -m unittest tests.test_go_buildinfo -v
```

### Rust: `tests/test_rust_cargo_auditable.py` — 15/15 passing

Installs `cargo-auditable` and builds its own fixtures at test time (a
main crate with both a real `crates.io` dependency, `itoa`, and a
local `path` dependency, so the test exercises genuine `local` vs.
`crates.io` source kinds and a real two-edge dependency graph) using
the system `cargo`/`rustc` toolchain:

- ELF binary: the section's file offset and size, and the full
  package/dependency-graph output, are cross-checked against an
  **independent** ground-truth decode — a from-scratch ELF
  section-header walk plus a direct `zlib.decompress()` of that exact
  byte range, written separately from the extractor's own
  `_elf_named_section` so a shared bug between the two wouldn't be
  invisible to the check.
- Cross-compiled PE binary (`--target x86_64-pc-windows-gnu`, via
  `gcc-mingw-w64-x86-64`): matches the ELF build's output exactly.
  **Found and fixed a real bug while building this test**: PE's
  `SizeOfRawData` is padded up to `FileAlignment` (512 bytes observed
  here), while `VirtualSize` (137 bytes, matching the ELF build's
  section size exactly) is the real, unpadded content length. Reading
  `SizeOfRawData` bytes pulled in 375 bytes of trailing zero padding
  past the real zlib stream, which the inflate step correctly rejected
  as "bytes after the zlib stream" — not a crash, but a wrong rejection
  of valid data. Fixed by taking `min(VirtualSize, SizeOfRawData)` as
  the section's true length.
- A plain `cargo build` (no `auditable`) and a plain `gcc`-compiled C
  binary both correctly report `cargo_auditable: false` rather than
  crashing or false-positively matching.
- Malformed-input handling: a truncated section and a corrupted zlib
  stream both raise the typed `RustAuditableError`; a 2,000-iteration
  fuzz test (same discipline as the Go suite) asserts zero uncaught
  exceptions of any kind.
- Cycle detection (Tarjan's SCC, iterative — no recursion, so it can't
  blow the stack on a large real dependency graph) is checked against
  hand-built graphs rather than a real binary, since crates.io itself
  forbids real dependency cycles — a linear chain, a 3-node cycle, a
  self-loop, and a cycle-plus-isolated-node case, plus rejection of a
  duplicate root package and an out-of-range dependency index.

```bash
python3 -m unittest tests.test_rust_cargo_auditable -v
```

Tests requiring `go`, `gcc`, `cargo`, or `cargo-auditable` skip cleanly
(rather than fail) if those tools aren't on `PATH`.
