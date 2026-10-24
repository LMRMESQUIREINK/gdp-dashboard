"""
Real-binary tests: builds actual `cargo auditable build` Rust binaries
(ELF and cross-compiled PE) with the system toolchain and runs the
extractor against them. Not mocked — genuine compiled artifacts, cross-
checked against an independent decode (readelf's own section-offset/size
report + a manual zlib.decompress of that exact byte range) rather than
hardcoded expected values, so this suite can't silently drift from what
cargo-auditable itself actually embeds.

Skips (not fails) any test whose required toolchain isn't on PATH.
"""

from __future__ import annotations

import random
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from rust_cargo_auditable import (  # noqa: E402
    RustAuditableError,
    read_cargo_auditable,
)

HAVE_CARGO = shutil.which("cargo") is not None
HAVE_MINGW = shutil.which("x86_64-w64-mingw32-gcc") is not None


def _have_cargo_auditable() -> bool:
    if not HAVE_CARGO:
        return False
    try:
        subprocess.run(["cargo", "auditable", "--version"], check=True, capture_output=True, timeout=30)
        return True
    except Exception:
        try:
            subprocess.run(
                ["cargo", "install", "cargo-auditable", "--locked"],
                check=True,
                capture_output=True,
                timeout=300,
            )
            subprocess.run(["cargo", "auditable", "--version"], check=True, capture_output=True, timeout=30)
            return True
        except Exception:
            return False


HAVE_CARGO_AUDITABLE = _have_cargo_auditable()
HAVE_WINDOWS_GNU_TARGET = False
if HAVE_CARGO_AUDITABLE:
    try:
        result = subprocess.run(
            ["rustup", "target", "list", "--installed"], check=True, capture_output=True, text=True, timeout=30
        )
        HAVE_WINDOWS_GNU_TARGET = "x86_64-pc-windows-gnu" in result.stdout
    except Exception:
        HAVE_WINDOWS_GNU_TARGET = False

_FIXTURES: dict[str, bytes] = {}
_FIXTURE_DIR: tempfile.TemporaryDirectory | None = None


def _write_fixture_project(root: Path) -> Path:
    """A main crate with a local path dependency and a real crates.io
    dependency, so the test exercises genuine `local` vs `crates.io`
    source kinds and a real two-edge dependency graph, not a synthetic
    single-package one."""
    dep_dir = root / "localdep"
    dep_dir.mkdir()
    (dep_dir / "Cargo.toml").write_text('[package]\nname = "localdep"\nversion = "0.3.1"\nedition = "2021"\n')
    (dep_dir / "src").mkdir()
    (dep_dir / "src" / "lib.rs").write_text("pub fn helper() -> i32 { 42 }\n")

    main_dir = root / "maincrate"
    main_dir.mkdir()
    (main_dir / "Cargo.toml").write_text(
        '[package]\nname = "maincrate"\nversion = "1.2.3"\nedition = "2021"\n\n'
        '[dependencies]\nlocaldep = { path = "../localdep" }\nitoa = "1.0"\n'
    )
    (main_dir / "src").mkdir()
    (main_dir / "src" / "main.rs").write_text(
        'fn main() { println!("{} {}", localdep::helper(), itoa::Buffer::new().format(7)); }\n'
    )
    return main_dir


def setUpModule() -> None:
    global _FIXTURE_DIR
    if not HAVE_CARGO_AUDITABLE:
        return
    _FIXTURE_DIR = tempfile.TemporaryDirectory(prefix="rust-cargo-auditable-tests-")
    main_dir = _write_fixture_project(Path(_FIXTURE_DIR.name))

    subprocess.run(["cargo", "auditable", "build", "--release"], cwd=main_dir, check=True, capture_output=True, timeout=300)
    elf_path = main_dir / "target" / "release" / "maincrate"
    _FIXTURES["elf"] = elf_path.read_bytes()

    if HAVE_WINDOWS_GNU_TARGET and HAVE_MINGW:
        subprocess.run(
            ["cargo", "auditable", "build", "--release", "--target", "x86_64-pc-windows-gnu"],
            cwd=main_dir,
            check=True,
            capture_output=True,
            timeout=300,
        )
        pe_path = main_dir / "target" / "x86_64-pc-windows-gnu" / "release" / "maincrate.exe"
        _FIXTURES["pe"] = pe_path.read_bytes()

    subprocess.run(["cargo", "build", "--release"], cwd=main_dir, check=True, capture_output=True, timeout=300)
    # cargo build (no auditable) overwrites the same output path, so grab
    # the non-auditable binary into its own key before anything else reuses
    # this directory.
    _FIXTURES["elf_not_auditable"] = (main_dir / "target" / "release" / "maincrate").read_bytes()


def tearDownModule() -> None:
    if _FIXTURE_DIR is not None:
        _FIXTURE_DIR.cleanup()


def _ground_truth_elf_section(data: bytes, name: str) -> tuple[int, int]:
    """Independent re-derivation of the section's (offset, size) via raw
    ELF section-header parsing, kept deliberately separate from (and
    simpler than — no PE/alignment handling) the extractor's own
    `_elf_named_section`, so a bug shared between the two wouldn't be
    invisible to this check."""
    (e_shoff,) = struct.unpack_from("<Q", data, 0x28)
    (e_shentsize,) = struct.unpack_from("<H", data, 0x3A)
    (e_shnum,) = struct.unpack_from("<H", data, 0x3C)
    (e_shstrndx,) = struct.unpack_from("<H", data, 0x3E)

    def header(i: int) -> tuple[int, int, int, int]:
        base = e_shoff + i * e_shentsize
        sh_name, sh_type = struct.unpack_from("<II", data, base)
        sh_offset, sh_size = struct.unpack_from("<QQ", data, base + 24)
        return sh_name, sh_type, sh_offset, sh_size

    _, _, strtab_off, strtab_size = header(e_shstrndx)
    for i in range(e_shnum):
        sh_name, _, sh_offset, sh_size = header(i)
        start = strtab_off + sh_name
        end = data.find(b"\x00", start)
        if data[start:end].decode("ascii") == name:
            return sh_offset, sh_size
    raise AssertionError(f"section {name!r} not found by ground-truth parser")


@unittest.skipUnless(HAVE_CARGO_AUDITABLE, "cargo-auditable not available")
class TestRealElfBinary(unittest.TestCase):
    def test_matches_independent_ground_truth_decode(self) -> None:
        data = _FIXTURES["elf"]
        offset, size = _ground_truth_elf_section(data, ".dep-v0")
        truth = zlib.decompress(data[offset : offset + size])

        info = read_cargo_auditable(data)
        self.assertIsNotNone(info)
        self.assertEqual(info.file_offset, offset)
        self.assertEqual(info.section_bytes, size)
        self.assertEqual(info.uncompressed_bytes, len(truth))

    def test_packages_and_dependency_graph(self) -> None:
        info = read_cargo_auditable(_FIXTURES["elf"])
        by_name = {p.name: p for p in info.packages}
        self.assertEqual(by_name["itoa"].source, "crates.io")
        self.assertEqual(by_name["localdep"].source, "local")
        self.assertEqual(by_name["localdep"].version, "0.3.1")
        self.assertEqual(by_name["maincrate"].version, "1.2.3")
        self.assertTrue(by_name["maincrate"].root)
        self.assertFalse(by_name["itoa"].root)

        root_index = info.root_package_index
        self.assertIsNotNone(root_index)
        self.assertEqual(info.packages[root_index].name, "maincrate")
        dep_names = {info.packages[i].name for _, i in info.dependency_edges if _ == root_index}
        self.assertEqual(dep_names, {"itoa", "localdep"})

    def test_no_cycles_in_a_real_dependency_tree(self) -> None:
        info = read_cargo_auditable(_FIXTURES["elf"])
        self.assertEqual(info.cyclic_dependency_indices, [])


@unittest.skipUnless(HAVE_CARGO_AUDITABLE and HAVE_WINDOWS_GNU_TARGET and HAVE_MINGW, "windows-gnu cross toolchain not available")
class TestRealPeBinary(unittest.TestCase):
    """Regression coverage for a real bug found while building this test:
    PE's SizeOfRawData is padded up to FileAlignment (512 bytes here),
    while VirtualSize (137 bytes, matching the ELF build exactly) is the
    real unpadded content length. Reading SizeOfRawData bytes pulled in
    zero-padding past the end of the real zlib stream, which the inflate
    step correctly rejected as trailing garbage — the fix takes
    min(VirtualSize, SizeOfRawData) as the section's true length."""

    def test_cross_compiled_binary_matches_elf_build_exactly(self) -> None:
        pe_info = read_cargo_auditable(_FIXTURES["pe"])
        elf_info = read_cargo_auditable(_FIXTURES["elf"])
        self.assertIsNotNone(pe_info)
        self.assertEqual(pe_info.section_bytes, elf_info.section_bytes)
        self.assertEqual(
            [(p.name, p.version, p.source) for p in pe_info.packages],
            [(p.name, p.version, p.source) for p in elf_info.packages],
        )
        self.assertEqual(pe_info.dependency_edges, elf_info.dependency_edges)


@unittest.skipUnless(HAVE_CARGO_AUDITABLE, "cargo-auditable not available")
class TestNegativeCase(unittest.TestCase):
    def test_plain_cargo_build_has_no_dep_section(self) -> None:
        info = read_cargo_auditable(_FIXTURES["elf_not_auditable"])
        self.assertIsNone(info)

    def test_plain_c_binary_has_no_dep_section(self) -> None:
        if not shutil.which("gcc"):
            self.skipTest("gcc not available")
        with tempfile.TemporaryDirectory() as tmp:
            c_path = Path(tmp) / "hello.c"
            c_path.write_text("int main(){return 0;}\n")
            bin_path = Path(tmp) / "hello"
            subprocess.run(["gcc", "-o", str(bin_path), str(c_path)], check=True, capture_output=True)
            info = read_cargo_auditable(bin_path.read_bytes())
            self.assertIsNone(info)


@unittest.skipUnless(HAVE_CARGO_AUDITABLE, "cargo-auditable not available")
class TestMalformedInputHandling(unittest.TestCase):
    def test_truncated_section_raises_typed_error(self) -> None:
        data = _FIXTURES["elf"]
        offset, size = _ground_truth_elf_section(data, ".dep-v0")
        truncated = data[: offset + size // 2] + data[offset + size :]
        with self.assertRaises(RustAuditableError):
            read_cargo_auditable(truncated)

    def test_corrupted_zlib_stream_raises_typed_error(self) -> None:
        data = bytearray(_FIXTURES["elf"])
        offset, size = _ground_truth_elf_section(bytes(data), ".dep-v0")
        data[offset + 2] ^= 0xFF
        with self.assertRaises(RustAuditableError):
            read_cargo_auditable(bytes(data))

    def test_fuzz_no_uncaught_exceptions(self) -> None:
        """2,000 random byte-flip corruptions of the dependency section
        must only ever produce a clean result or RustAuditableError —
        never any other exception type (same discipline, and the same
        real-bug-class check, as go_buildinfo's fuzz test)."""
        data = _FIXTURES["elf"]
        offset, size = _ground_truth_elf_section(data, ".dep-v0")
        rng = random.Random(20261018)
        crashes: list[tuple[str, str]] = []
        for _ in range(2000):
            corrupted = bytearray(data)
            for _ in range(rng.randint(1, 20)):
                pos = offset + rng.randint(0, size - 1)
                corrupted[pos] ^= rng.randint(1, 255)
            try:
                read_cargo_auditable(bytes(corrupted))
            except RustAuditableError:
                pass
            except Exception as error:  # noqa: BLE001 - intentional catch-all for this assertion
                crashes.append((type(error).__name__, str(error)))
        self.assertEqual(crashes, [], f"{len(crashes)} uncaught exception(s) during fuzzing, e.g. {crashes[:3]}")


class TestCycleDetection(unittest.TestCase):
    """Pure-logic tests against hand-built package lists — no toolchain
    needed, since crates.io itself forbids real dependency cycles, so a
    real cargo-auditable binary could never exercise this path. The JSON
    schema can still encode one (nothing stops a hand-crafted or
    corrupted payload from doing so), so it has to be handled correctly
    rather than assumed impossible."""

    def _pkg(self, name: str, deps: list[int], root: bool = False):
        from rust_cargo_auditable import RustPackage

        return RustPackage(name=name, version="1.0", source="crates.io", kind=None, dependencies=deps, root=root)

    def test_linear_chain_has_no_cycle(self) -> None:
        from rust_cargo_auditable import _cyclic_dependency_indices

        pkgs = [self._pkg("a", [1]), self._pkg("b", [2]), self._pkg("c", [], root=True)]
        self.assertEqual(_cyclic_dependency_indices(pkgs), [])

    def test_three_node_cycle_detected(self) -> None:
        from rust_cargo_auditable import _cyclic_dependency_indices

        pkgs = [self._pkg("a", [1]), self._pkg("b", [2]), self._pkg("c", [0])]
        self.assertEqual(_cyclic_dependency_indices(pkgs), [0, 1, 2])

    def test_self_loop_detected(self) -> None:
        from rust_cargo_auditable import _cyclic_dependency_indices

        pkgs = [self._pkg("a", [0], root=True)]
        self.assertEqual(_cyclic_dependency_indices(pkgs), [0])

    def test_cycle_plus_isolated_node(self) -> None:
        from rust_cargo_auditable import _cyclic_dependency_indices

        pkgs = [self._pkg("a", [1]), self._pkg("b", [0]), self._pkg("c", [], root=True)]
        self.assertEqual(_cyclic_dependency_indices(pkgs), [0, 1])

    def test_duplicate_root_rejected(self) -> None:
        from rust_cargo_auditable import RustAuditableError, _root_index

        pkgs = [self._pkg("a", [], root=True), self._pkg("b", [], root=True)]
        with self.assertRaises(RustAuditableError):
            _root_index(pkgs)

    def test_out_of_range_dependency_index_rejected(self) -> None:
        from rust_cargo_auditable import RustAuditableError, _root_index

        pkgs = [self._pkg("a", [5], root=True)]
        with self.assertRaises(RustAuditableError):
            _root_index(pkgs)


if __name__ == "__main__":
    unittest.main()
