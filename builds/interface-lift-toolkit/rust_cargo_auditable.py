"""
Standalone cargo-auditable dependency-graph extractor — reads the
compressed JSON package/dependency list that `cargo auditable build`
embeds in a `.dep-v0` ELF/PE section, without needing `cargo` or Rust
source. Sibling to go_buildinfo.py; same project, same discipline
(built from reading morluto/rea's TypeScript implementation as a
correctness reference, reimplemented fresh, verified against real
compiled binaries).

Format: a zlib-compressed UTF-8 JSON document
`{"format": 1, "packages": [{"name", "version", "source", "kind",
"dependencies": [indices...], "root": bool}, ...]}`, stored verbatim
(not relocated, no pointers to resolve) in a section named `.dep-v0`
on ELF and PE, or `__DATA,.dep-v0` on Mach-O. Mach-O is not
implemented here, same reason as go_buildinfo.py: no way to produce
or verify one in this sandbox.
"""

from __future__ import annotations

import json
import struct
import zlib
from dataclasses import dataclass, field

DEP_SECTION_NAME = ".dep-v0"
MAX_SECTION_BYTES = 1024 * 1024
MAX_INFLATE_RATIO = 64
MAX_UNCOMPRESSED_BYTES = 8 * 1024 * 1024
MAX_JSON_DEPTH = 32

SHT_NOBITS = 8


class RustAuditableError(Exception):
    """A `.dep-v0` section was found but is malformed, unsupported, or
    exceeds a resource limit."""


@dataclass
class RustPackage:
    name: str
    version: str
    source: str
    kind: str | None
    dependencies: list[int] = field(default_factory=list)
    root: bool = False


@dataclass
class RustAuditableMetadata:
    section_name: str
    file_offset: int
    section_bytes: int
    uncompressed_bytes: int
    format_version: int | None
    packages: list[RustPackage]
    root_package_index: int | None
    dependency_edges: list[tuple[int, int]]
    cyclic_dependency_indices: list[int]


# ---------------------------------------------------------------------------
# Section lookup
# ---------------------------------------------------------------------------


def _elf_named_section(data: bytes, name: str) -> tuple[int, int] | None:
    if data[:4] != b"\x7fELF":
        raise RustAuditableError("not an ELF file")
    ei_class = data[4]
    ei_data = data[5]
    if ei_class not in (1, 2) or ei_data not in (1, 2):
        raise RustAuditableError("malformed ELF identification bytes")
    is64 = ei_class == 2
    endian = "<" if ei_data == 1 else ">"

    if is64:
        (e_shoff,) = struct.unpack_from(endian + "Q", data, 0x28)
        (e_shentsize,) = struct.unpack_from(endian + "H", data, 0x3A)
        (e_shnum,) = struct.unpack_from(endian + "H", data, 0x3C)
        (e_shstrndx,) = struct.unpack_from(endian + "H", data, 0x3E)
    else:
        (e_shoff,) = struct.unpack_from(endian + "I", data, 0x20)
        (e_shentsize,) = struct.unpack_from(endian + "H", data, 0x2E)
        (e_shnum,) = struct.unpack_from(endian + "H", data, 0x30)
        (e_shstrndx,) = struct.unpack_from(endian + "H", data, 0x32)

    if e_shnum == 0:
        return None

    def section_header(index: int) -> tuple[int, int, int, int]:
        """Returns (sh_name, sh_type, sh_offset, sh_size)."""
        base = e_shoff + index * e_shentsize
        if is64:
            sh_name, sh_type = struct.unpack_from(endian + "II", data, base)
            sh_offset, sh_size = struct.unpack_from(endian + "QQ", data, base + 24)
        else:
            sh_name, sh_type = struct.unpack_from(endian + "II", data, base)
            sh_offset, sh_size = struct.unpack_from(endian + "II", data, base + 16)
        return sh_name, sh_type, sh_offset, sh_size

    _, _, strtab_offset, strtab_size = section_header(e_shstrndx)

    def read_name(sh_name: int) -> str:
        start = strtab_offset + sh_name
        end = data.find(b"\x00", start, strtab_offset + strtab_size)
        if end < 0:
            raise RustAuditableError("section name is not NUL-terminated")
        return data[start:end].decode("ascii", errors="replace")

    for index in range(e_shnum):
        sh_name, sh_type, sh_offset, sh_size = section_header(index)
        if read_name(sh_name) != name:
            continue
        if sh_type == SHT_NOBITS:
            raise RustAuditableError("dependency section is not file-backed (SHT_NOBITS)")
        return sh_offset, sh_size
    return None


def _pe_named_section(data: bytes, name: str) -> tuple[int, int] | None:
    if data[:2] != b"MZ":
        raise RustAuditableError("not a PE file")
    (e_lfanew,) = struct.unpack_from("<I", data, 0x3C)
    if data[e_lfanew : e_lfanew + 4] != b"PE\x00\x00":
        raise RustAuditableError("missing PE signature")
    coff_base = e_lfanew + 4
    (num_sections,) = struct.unpack_from("<H", data, coff_base + 2)
    (size_of_opt_header,) = struct.unpack_from("<H", data, coff_base + 16)
    section_base = coff_base + 20 + size_of_opt_header

    name_bytes = name.encode("ascii")
    for i in range(num_sections):
        base = section_base + i * 40
        raw_name = data[base : base + 8].split(b"\x00", 1)[0]
        if raw_name != name_bytes:
            continue
        virtual_size = struct.unpack_from("<I", data, base + 8)[0]
        size_of_raw_data, pointer_to_raw_data = struct.unpack_from("<II", data, base + 16)
        # SizeOfRawData is padded up to FileAlignment (512 bytes is typical);
        # VirtualSize is the real, unpadded content length. The real data is
        # never longer than either, so take whichever is smaller (a linker
        # that leaves VirtualSize at 0 gets no benefit from this, so fall
        # back to the raw size in that case).
        size = min(virtual_size, size_of_raw_data) if virtual_size else size_of_raw_data
        return pointer_to_raw_data, size
    return None


# ---------------------------------------------------------------------------
# Section payload decoding
# ---------------------------------------------------------------------------


def _inflate_section(section_bytes: bytes) -> bytes:
    maximum = min(MAX_UNCOMPRESSED_BYTES, len(section_bytes) * MAX_INFLATE_RATIO)
    decompressor = zlib.decompressobj()
    try:
        out = decompressor.decompress(section_bytes, maximum)
    except zlib.error as error:
        raise RustAuditableError(f"dependency section is not a valid zlib stream: {error}") from error
    if not decompressor.eof:
        if len(out) >= maximum:
            raise RustAuditableError("inflated dependency JSON exceeds the size limit")
        raise RustAuditableError("dependency section is not a complete zlib stream")
    if decompressor.unused_data:
        raise RustAuditableError("dependency section has bytes after the zlib stream")
    return out


def _assert_json_depth(text: str) -> None:
    depth = 0
    quoted = False
    escaped = False
    for ch in text:
        if quoted:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                quoted = False
            continue
        if ch == '"':
            quoted = True
            continue
        if ch in "{[":
            depth += 1
            if depth > MAX_JSON_DEPTH:
                raise RustAuditableError(f"dependency JSON nesting exceeds {MAX_JSON_DEPTH} levels")
        elif ch in "}]" and depth > 0:
            depth -= 1


def _parse_packages(document: dict) -> list[RustPackage]:
    if not isinstance(document, dict):
        raise RustAuditableError("dependency JSON root is not an object")
    raw_packages = document.get("packages")
    if not isinstance(raw_packages, list):
        raise RustAuditableError("dependency JSON has no 'packages' array")

    packages: list[RustPackage] = []
    for index, raw in enumerate(raw_packages):
        if not isinstance(raw, dict):
            raise RustAuditableError(f"package {index} is not an object")
        name = raw.get("name")
        version = raw.get("version")
        source = raw.get("source")
        if not (isinstance(name, str) and name) or not (isinstance(version, str) and version) or not (
            isinstance(source, str) and source
        ):
            raise RustAuditableError(f"package {index} is missing a required string field")
        kind = raw.get("kind")
        if kind is not None and kind not in ("runtime", "build"):
            raise RustAuditableError(f"package {index} has an invalid 'kind'")
        deps = raw.get("dependencies", [])
        if not isinstance(deps, list) or not all(isinstance(d, int) and d >= 0 for d in deps):
            raise RustAuditableError(f"package {index} has an invalid 'dependencies' array")
        root = raw.get("root", False)
        if not isinstance(root, bool):
            raise RustAuditableError(f"package {index} has a non-boolean 'root'")
        extra = set(raw.keys()) - {"name", "version", "source", "kind", "dependencies", "root"}
        if extra:
            raise RustAuditableError(f"package {index} has unrecognized field(s): {sorted(extra)}")
        packages.append(RustPackage(name=name, version=version, source=source, kind=kind, dependencies=list(deps), root=root))
    return packages


def _root_index(packages: list[RustPackage]) -> int | None:
    roots = [i for i, pkg in enumerate(packages) if pkg.root]
    if len(roots) > 1:
        raise RustAuditableError("dependency JSON declares more than one root package")
    for index, pkg in enumerate(packages):
        for target in pkg.dependencies:
            if target >= len(packages):
                raise RustAuditableError(
                    f"dependency index {target} from package {index} is outside the package list"
                )
    return roots[0] if roots else None


def _cyclic_dependency_indices(packages: list[RustPackage]) -> list[int]:
    """Tarjan's strongly-connected-components algorithm, iterative (no
    recursion) so it can't blow the stack on a large real dependency
    graph. A package is "cyclic" if its SCC has more than one member, or
    is a single package with a self-dependency."""
    n = len(packages)
    edges = [pkg.dependencies for pkg in packages]
    index_counter = [0]
    index_of: list[int | None] = [None] * n
    lowlink = [0] * n
    on_stack = [False] * n
    stack: list[int] = []
    sccs: list[list[int]] = []

    for start in range(n):
        if index_of[start] is not None:
            continue
        work: list[tuple[int, int]] = [(start, 0)]
        while work:
            node, edge_pos = work[-1]
            if edge_pos == 0:
                index_of[node] = index_counter[0]
                lowlink[node] = index_counter[0]
                index_counter[0] += 1
                stack.append(node)
                on_stack[node] = True
            if edge_pos < len(edges[node]):
                work[-1] = (node, edge_pos + 1)
                successor = edges[node][edge_pos]
                if index_of[successor] is None:
                    work.append((successor, 0))
                elif on_stack[successor]:
                    lowlink[node] = min(lowlink[node], index_of[successor])
            else:
                work.pop()
                if work:
                    parent = work[-1][0]
                    lowlink[parent] = min(lowlink[parent], lowlink[node])
                if lowlink[node] == index_of[node]:
                    component = []
                    while True:
                        member = stack.pop()
                        on_stack[member] = False
                        component.append(member)
                        if member == node:
                            break
                    sccs.append(component)

    cyclic: set[int] = set()
    for component in sccs:
        if len(component) > 1:
            cyclic.update(component)
        elif component and component[0] in edges[component[0]]:
            cyclic.add(component[0])
    return sorted(cyclic)


def _parse_section(section_name: str, file_offset: int, section_bytes: bytes) -> RustAuditableMetadata:
    if len(section_bytes) == 0:
        raise RustAuditableError("dependency section is empty")
    if len(section_bytes) > MAX_SECTION_BYTES:
        raise RustAuditableError("dependency section exceeds the 1 MiB compressed limit")

    inflated = _inflate_section(section_bytes)
    text = inflated.decode("utf-8", errors="strict") if _is_strict_utf8(inflated) else None
    if text is None:
        raise RustAuditableError("dependency JSON is not valid UTF-8")
    _assert_json_depth(text)
    try:
        document = json.loads(text)
    except json.JSONDecodeError as error:
        raise RustAuditableError(f"dependency section JSON is invalid: {error}") from error

    format_version = document.get("format") if isinstance(document, dict) else None
    if format_version is not None and not (isinstance(format_version, int) and not isinstance(format_version, bool) and format_version >= 0):
        raise RustAuditableError("dependency JSON 'format' is not a non-negative integer")

    packages = _parse_packages(document)
    root = _root_index(packages)
    edges = [(frm, to) for frm, pkg in enumerate(packages) for to in pkg.dependencies]

    return RustAuditableMetadata(
        section_name=section_name,
        file_offset=file_offset,
        section_bytes=len(section_bytes),
        uncompressed_bytes=len(inflated),
        format_version=format_version,
        packages=packages,
        root_package_index=root,
        dependency_edges=edges,
        cyclic_dependency_indices=_cyclic_dependency_indices(packages),
    )


def _is_strict_utf8(data: bytes) -> bool:
    try:
        data.decode("utf-8", errors="strict")
        return True
    except UnicodeDecodeError:
        return False


def read_cargo_auditable(data: bytes) -> RustAuditableMetadata | None:
    """Inspect a compiled binary's bytes and return its cargo-auditable
    dependency metadata, or None if no `.dep-v0` section was found (not
    built with `cargo auditable`, or it's a plain `cargo build`)."""
    if data[:4] == b"\x7fELF":
        section = _elf_named_section(data, DEP_SECTION_NAME)
    elif data[:2] == b"MZ":
        section = _pe_named_section(data, DEP_SECTION_NAME)
    else:
        raise RustAuditableError("only ELF and PE containers are supported")

    if section is None:
        return None
    offset, size = section
    if offset + size > len(data):
        raise RustAuditableError("dependency section range is outside the file")
    return _parse_section(DEP_SECTION_NAME, offset, data[offset : offset + size])


def _main() -> None:
    import sys

    if len(sys.argv) != 2:
        print("usage: rust_cargo_auditable.py <path-to-binary>", file=sys.stderr)
        raise SystemExit(2)
    with open(sys.argv[1], "rb") as handle:
        data = handle.read()
    try:
        info = read_cargo_auditable(data)
    except RustAuditableError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
    if info is None:
        print(json.dumps({"cargo_auditable": False}))
        return

    print(
        json.dumps(
            {
                "cargo_auditable": True,
                "section_name": info.section_name,
                "file_offset": info.file_offset,
                "section_bytes": info.section_bytes,
                "uncompressed_bytes": info.uncompressed_bytes,
                "format_version": info.format_version,
                "root_package_index": info.root_package_index,
                "packages": [
                    {
                        "name": p.name,
                        "version": p.version,
                        "source": p.source,
                        "kind": p.kind,
                        "dependencies": p.dependencies,
                        "root": p.root,
                    }
                    for p in info.packages
                ],
                "dependency_edges": info.dependency_edges,
                "cyclic_dependency_indices": info.cyclic_dependency_indices,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    _main()
