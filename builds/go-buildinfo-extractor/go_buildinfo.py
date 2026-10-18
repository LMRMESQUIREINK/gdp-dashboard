"""
Standalone Go build-info extractor — reads the compiler version, main
module path+version, dependency list, and build settings that the Go
toolchain embeds in every compiled binary (the same data `go version -m`
reports), without needing a Go installation or the original source.

Supports ELF and PE containers. Thin Mach-O is explicitly not
implemented — see README.md for why.

Format reference: Go's own `debug/buildinfo` package and the
`runtime/debug.BuildInfo` text format. No code here was copied from
Go's source or from any other project; the format was learned by
reading morluto/rea's (MIT-licensed) TypeScript implementation for
correctness reference, then reimplemented from scratch in Python and
verified against real compiled Go binaries (see tests/).
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field

MAGIC = bytes.fromhex("ff20476f206275696c64696e663a")  # "\xff Go buildinf:"
MODULE_START = bytes.fromhex("3077af0c9274080241e1c107e6d618e6")
MODULE_END = bytes.fromhex("f932433186182072008242104116d8f2")
MAX_BUILD_INFO_BYTES = 1024 * 1024


class GoBuildInfoError(Exception):
    """A buildinfo structure was found but is malformed or unsupported."""


@dataclass
class GoModule:
    path: str
    version: str
    sum: str | None = None
    replacement: "GoModule | None" = None


@dataclass
class GoModuleMetadata:
    path: str | None
    main: GoModule | None
    dependencies: list[GoModule] = field(default_factory=list)
    settings: dict[str, str] = field(default_factory=dict)
    unparsed_lines: list[str] = field(default_factory=list)


@dataclass
class GoBuildInfo:
    format: str  # "elf" | "pe"
    bits: int  # 32 | 64
    byte_order: str  # "little" | "big"
    encoding: str  # "inline" | "pointer"
    header_offset: int
    go_version: str | None
    module_text: str | None
    module: GoModuleMetadata | None


# ---------------------------------------------------------------------------
# Container parsing: map a virtual address to a file offset for each format.
# ---------------------------------------------------------------------------


class _AddressMapper:
    """Maps a virtual address range to its file offset, or raises if the
    range isn't backed by file bytes (e.g. the zero-filled tail of a
    segment/section)."""

    def __init__(self, regions: list[tuple[int, int, int, int]]):
        # Each region: (vaddr, vaddr_size, file_offset, file_size)
        self._regions = regions

    def to_file_offset(self, address: int, size: int) -> int:
        for vaddr, vsize, foff, fsize in self._regions:
            if vaddr <= address < vaddr + vsize:
                delta = address - vaddr
                if delta + size > fsize:
                    raise GoBuildInfoError(
                        "address range falls in a zero-filled (non-file-backed) span"
                    )
                return foff + delta
        raise GoBuildInfoError(f"address 0x{address:x} is not mapped by any segment")

    def contains_file_offset(self, offset: int) -> bool:
        return any(foff <= offset < foff + fsize for _, _, foff, fsize in self._regions)


def _parse_elf(data: bytes) -> tuple[_AddressMapper, int, str]:
    if data[:4] != b"\x7fELF":
        raise GoBuildInfoError("not an ELF file")
    ei_class = data[4]  # 1 = 32-bit, 2 = 64-bit
    ei_data = data[5]  # 1 = little endian, 2 = big endian
    if ei_class not in (1, 2) or ei_data not in (1, 2):
        raise GoBuildInfoError("malformed ELF identification bytes")
    bits = 32 if ei_class == 1 else 64
    endian = "<" if ei_data == 1 else ">"
    byte_order = "little" if ei_data == 1 else "big"

    if bits == 64:
        # e_phoff(8) at 0x20, e_phentsize(2) at 0x36, e_phnum(2) at 0x38
        (e_phoff,) = struct.unpack_from(endian + "Q", data, 0x20)
        (e_phentsize,) = struct.unpack_from(endian + "H", data, 0x36)
        (e_phnum,) = struct.unpack_from(endian + "H", data, 0x38)
    else:
        (e_phoff,) = struct.unpack_from(endian + "I", data, 0x1C)
        (e_phentsize,) = struct.unpack_from(endian + "H", data, 0x2A)
        (e_phnum,) = struct.unpack_from(endian + "H", data, 0x2C)

    regions: list[tuple[int, int, int, int]] = []
    for i in range(e_phnum):
        base = e_phoff + i * e_phentsize
        if bits == 64:
            p_type, _flags, p_offset, p_vaddr, _paddr, p_filesz, p_memsz, _align = (
                struct.unpack_from(endian + "IIQQQQQQ", data, base)
            )
        else:
            p_type, p_offset, p_vaddr, _paddr, p_filesz, p_memsz, _flags, _align = (
                struct.unpack_from(endian + "IIIIIIII", data, base)
            )
        PT_LOAD = 1
        if p_type == PT_LOAD:
            regions.append((p_vaddr, p_memsz, p_offset, p_filesz))

    return _AddressMapper(regions), bits, byte_order


def _parse_pe(data: bytes) -> tuple[_AddressMapper, int, str]:
    if data[:2] != b"MZ":
        raise GoBuildInfoError("not a PE file")
    (e_lfanew,) = struct.unpack_from("<I", data, 0x3C)
    if data[e_lfanew : e_lfanew + 4] != b"PE\x00\x00":
        raise GoBuildInfoError("missing PE signature")
    coff_base = e_lfanew + 4
    (machine, num_sections) = struct.unpack_from("<HH", data, coff_base)
    (size_of_opt_header,) = struct.unpack_from("<H", data, coff_base + 16)
    opt_base = coff_base + 20
    (magic,) = struct.unpack_from("<H", data, opt_base)
    if magic == 0x10B:
        bits = 32
    elif magic == 0x20B:
        bits = 64
    else:
        raise GoBuildInfoError("unrecognized PE optional-header magic")

    section_base = opt_base + size_of_opt_header
    regions: list[tuple[int, int, int, int]] = []
    for i in range(num_sections):
        base = section_base + i * 40
        virtual_size, virtual_address, size_of_raw_data, pointer_to_raw_data = (
            struct.unpack_from("<IIII", data, base + 8)
        )
        # PE images are loaded with an implicit base; buildinfo pointers in a
        # non-relocated/non-PIE Go PE binary are absolute, but the raw
        # on-disk buildinfo pointer search in this tool only needs the
        # RVA-relative mapping, since Go's PE writer stores pointers as
        # ImageBase + RVA and callers resolving them must subtract the
        # configured image base. Handled in `_resolve_pe_pointer`.
        regions.append((virtual_address, max(virtual_size, size_of_raw_data), pointer_to_raw_data, size_of_raw_data))

    # PE is little-endian only.
    return _AddressMapper(regions), bits, "little"


def _pe_image_base(data: bytes) -> int:
    (e_lfanew,) = struct.unpack_from("<I", data, 0x3C)
    coff_base = e_lfanew + 4
    opt_base = coff_base + 20
    (magic,) = struct.unpack_from("<H", data, opt_base)
    if magic == 0x10B:
        (base,) = struct.unpack_from("<I", data, opt_base + 28)
        return base
    (base,) = struct.unpack_from("<Q", data, opt_base + 24)
    return base


# ---------------------------------------------------------------------------
# Build-info header + string decoding
# ---------------------------------------------------------------------------


def _find_magic(data: bytes) -> int | None:
    offset = 0
    while True:
        index = data.find(MAGIC, offset)
        if index < 0:
            return None
        # Go always places the header at a 16-byte-aligned file position in
        # practice (the linker aligns the data section); this is a weaker
        # check than REA's virtual-address-based alignment test, documented
        # in README.md as a deliberate simplification.
        if index % 16 == 0:
            return index
        offset = index + 1


def _read_uvarint(data: bytes, offset: int) -> tuple[int, int]:
    """Go's binary.Uvarint: little-endian base-128 varint."""
    result = 0
    shift = 0
    for i in range(10):
        if offset + i >= len(data):
            raise GoBuildInfoError("build-info varint is truncated")
        byte = data[offset + i]
        if i == 9 and byte > 1:
            raise GoBuildInfoError("build-info varint overflows 64 bits")
        result |= (byte & 0x7F) << shift
        if byte & 0x80 == 0:
            if result > MAX_BUILD_INFO_BYTES:
                raise GoBuildInfoError("build-info string length exceeds 1 MiB limit")
            return result, offset + i + 1
        shift += 7
    raise GoBuildInfoError("build-info varint is unterminated")


def _read_inline_string(data: bytes, offset: int) -> tuple[bytes, int]:
    length, start = _read_uvarint(data, offset)
    if start + length > len(data):
        raise GoBuildInfoError("build-info inline string range is truncated")
    return data[start : start + length], start + length


def _resolve_pointer_string(
    data: bytes, mapper: _AddressMapper, header_bits: int, pointer_value: int
) -> bytes:
    width = header_bits // 8
    try:
        offset = mapper.to_file_offset(pointer_value, width * 2)
    except GoBuildInfoError:
        # A zero-length Go string may carry a zero/dangling data pointer;
        # treat an unmapped header as length 0 rather than fail outright.
        return b""
    endian = "<"
    fmt = "Q" if header_bits == 64 else "I"
    (data_ptr,) = struct.unpack_from(endian + fmt, data, offset)
    (length,) = struct.unpack_from(endian + fmt, data, offset + width)
    if length == 0:
        return b""
    if length > MAX_BUILD_INFO_BYTES:
        raise GoBuildInfoError("build-info pointer string length exceeds 1 MiB limit")
    str_offset = mapper.to_file_offset(data_ptr, length)
    return data[str_offset : str_offset + length]


def _decode_utf8_strict(raw: bytes, what: str) -> str:
    try:
        return raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise GoBuildInfoError(f"build-info {what} is not valid UTF-8: {error}") from error


def _decode_module_text(raw: bytes) -> bytes:
    if len(raw) == 0:
        return b""
    if (
        len(raw) < 33
        or raw[:16] != MODULE_START
        or raw[-16:] != MODULE_END
        or raw[-17] != 10  # trailing '\n' immediately before MODULE_END
    ):
        raise GoBuildInfoError("module string framing is invalid")
    return raw[16:-16]


def _parse_module_metadata(text: str) -> GoModuleMetadata:
    path: str | None = None
    main: GoModule | None = None
    dependencies: list[GoModule] = []
    settings: dict[str, str] = {}
    unparsed: list[str] = []
    last: GoModule | None = None

    for line in text.split("\n"):
        if line == "":
            continue
        if line.startswith("path\t") and path is None:
            path = line[5:]
            continue
        if line.startswith("mod\t") or line.startswith("dep\t"):
            fields = line[4:].split("\t")
            last = None
            if len(fields) in (2, 3):
                module = GoModule(path=fields[0], version=fields[1], sum=fields[2] if len(fields) == 3 else None)
                if line.startswith("mod\t"):
                    if main is None:
                        main = module
                        last = module
                        continue
                else:
                    dependencies.append(module)
                    last = module
                    continue
            unparsed.append(line)
            continue
        if line.startswith("=>\t"):
            fields = line[3:].split("\t")
            if len(fields) == 3 and last is not None:
                last.replacement = GoModule(path=fields[0], version=fields[1], sum=fields[2])
                last = None
                continue
            last = None
            unparsed.append(line)
            continue
        if line.startswith("build\t"):
            rest = line[6:]
            sep = rest.find("=")
            if sep > 0:
                settings[rest[:sep]] = rest[sep + 1 :]
                continue
            unparsed.append(line)
            continue
        unparsed.append(line)

    return GoModuleMetadata(
        path=path, main=main, dependencies=dependencies, settings=settings, unparsed_lines=unparsed
    )


def read_go_buildinfo(data: bytes) -> GoBuildInfo | None:
    """Inspect a compiled binary's bytes and return its embedded Go build
    info, or None if no Go build-info header was found (not a Go binary,
    or built with build info stripped)."""
    if data[:4] == b"\x7fELF":
        fmt = "elf"
        mapper, bits, byte_order = _parse_elf(data)
        image_base = 0
    elif data[:2] == b"MZ":
        fmt = "pe"
        mapper, bits, byte_order = _parse_pe(data)
        image_base = _pe_image_base(data)
    else:
        raise GoBuildInfoError("only ELF and PE containers are supported")

    header = _find_magic(data)
    if header is None:
        return None
    if header + 32 > len(data):
        raise GoBuildInfoError("build-info header is truncated")

    ptr_size = data[header + 14]
    flags = data[header + 15]
    if flags & ~0x3:
        raise GoBuildInfoError("build-info flags contain an unsupported bit")
    encoding = "inline" if flags & 0x2 else "pointer"

    if encoding == "inline":
        version_bytes, next_offset = _read_inline_string(data, header + 32)
        module_bytes, _ = _read_inline_string(data, next_offset)
    else:
        if ptr_size not in (4, 8):
            raise GoBuildInfoError("build-info pointer width must be 4 or 8")
        endian = "<"
        fmt_code = "Q" if ptr_size == 8 else "I"
        (version_ptr,) = struct.unpack_from(endian + fmt_code, data, header + 16)
        (module_ptr,) = struct.unpack_from(endian + fmt_code, data, header + 16 + ptr_size)
        # PE pointers are absolute (ImageBase + RVA); normalize to an RVA
        # before mapping through the section table. ELF pointers are
        # already virtual addresses matching the program headers.
        if fmt == "pe":
            version_ptr -= image_base
            module_ptr -= image_base
        version_bytes = _resolve_pointer_string(data, mapper, ptr_size * 8, version_ptr)
        module_bytes = _resolve_pointer_string(data, mapper, ptr_size * 8, module_ptr)

    if len(version_bytes) == 0:
        raise GoBuildInfoError("build-info compiler version is empty")
    go_version = _decode_utf8_strict(version_bytes, "compiler version")

    module_text: str | None = None
    module_meta: GoModuleMetadata | None = None
    if len(module_bytes) != 0:
        inner = _decode_module_text(module_bytes)
        module_text = _decode_utf8_strict(inner, "module text")
        module_meta = _parse_module_metadata(module_text)

    return GoBuildInfo(
        format=fmt,
        bits=bits,
        byte_order=byte_order,
        encoding=encoding,
        header_offset=header,
        go_version=go_version,
        module_text=module_text,
        module=module_meta,
    )


def _main() -> None:
    import json
    import sys

    if len(sys.argv) != 2:
        print("usage: go_buildinfo.py <path-to-binary>", file=sys.stderr)
        raise SystemExit(2)
    with open(sys.argv[1], "rb") as handle:
        data = handle.read()
    try:
        info = read_go_buildinfo(data)
    except GoBuildInfoError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
    if info is None:
        print(json.dumps({"go_binary": False}))
        return

    def module_to_dict(module: GoModule | None) -> dict | None:
        if module is None:
            return None
        return {
            "path": module.path,
            "version": module.version,
            "sum": module.sum,
            "replacement": module_to_dict(module.replacement),
        }

    print(
        json.dumps(
            {
                "go_binary": True,
                "format": info.format,
                "bits": info.bits,
                "byte_order": info.byte_order,
                "encoding": info.encoding,
                "header_offset": info.header_offset,
                "go_version": info.go_version,
                "module_path": info.module.path if info.module else None,
                "main_module": module_to_dict(info.module.main) if info.module else None,
                "dependencies": (
                    [module_to_dict(d) for d in info.module.dependencies] if info.module else []
                ),
                "settings": info.module.settings if info.module else {},
                "unparsed_lines": info.module.unparsed_lines if info.module else [],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    _main()
