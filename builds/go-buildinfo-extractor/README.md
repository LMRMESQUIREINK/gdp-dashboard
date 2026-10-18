# Go Build-Info Extractor

A standalone, dependency-free Python tool that reads the compiler
version, main module path+version, dependency list (including local
`replace` directives), and build settings that the Go toolchain embeds
in every compiled binary — the same data `go version -m` prints —
without needing a Go installation or the original source. Reads ELF
and PE binaries directly.

Built from a deep analysis of `morluto/rea`'s MCP reverse-engineering
toolkit, which documents exactly this capability ("Go binaries —
Embedded compiler version, modules, replacements and build settings").
Full analysis: `/notes/rea-reverse-engineer-anything-analysis.md`.

## Usage

```bash
python3 go_buildinfo.py /path/to/binary
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

Or import it as a library — `go_buildinfo.read_go_buildinfo(data: bytes)`
returns a `GoBuildInfo | None` (`None` means no Go build-info header was
found; it does not by itself mean the binary isn't Go — e.g. the header
could have been stripped).

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
- **The pointer-encoding path is implemented but unverified.** Modern
  Go (tested here: 1.24.7) always uses the newer "inline" string
  encoding for both ELF and PE output. The older pointer-based encoding
  path exists in this tool (same virtual-address-resolution logic, just
  reading a `{pointer, length}` pair instead of an inline varint-length
  string) but there's no Go toolchain old enough in this sandbox to
  produce a binary that actually exercises it. Flagged here rather than
  silently left untested.

## Verified against real compiled binaries, not synthesized bytes

`tests/test_go_buildinfo.py` builds its own fixtures at test time (a
real two-module project — a main module with a local dependency pulled
in via a `replace` directive, so the test exercises a genuine `dep` +
`=>` replacement pair, not a synthetic one) using the system `go`
toolchain, and checks results against `go version -m`'s own output as
ground truth rather than hand-typed expected values. 11/11 passing:

- ELF binary: compiler version, module path, main module, the real
  local-replaced dependency, and all 6 build settings match
  `go version -m` exactly.
- Cross-compiled PE binary (`GOOS=windows GOARCH=amd64`): same checks,
  confirming the PE section-table/RVA mapping and the `ImageBase`
  normalization for pointer-encoded fields are both correct for a real
  Windows binary — built and parsed without ever needing Windows.
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

Run it:

```bash
python3 -m unittest tests.test_go_buildinfo -v
```

Tests requiring `go` or `gcc` skip cleanly (rather than fail) if those
tools aren't on `PATH`.
