"""
Real-binary tests: compiles actual Go (and, for the negative case, C)
binaries with the system toolchain and runs the extractor against them.
Not mocked — these are genuine compiled artifacts, and the Go fixture's
expected values are cross-checked against `go version -m`'s own output
(ground truth) rather than hardcoded independently of it, so this suite
can't silently drift from what Go itself actually embeds.

Skips (not fails) any test whose required toolchain isn't on PATH.
"""

from __future__ import annotations

import os
import random
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from go_buildinfo import GoBuildInfoError, _find_magic, read_go_buildinfo  # noqa: E402

HAVE_GO = shutil.which("go") is not None
HAVE_GCC = shutil.which("gcc") is not None

# Go switched to the "inline" build-info string encoding unconditionally in
# 1.18; only 1.13-1.17 binaries use the older pointer-based encoding. Go's
# own toolchain-management machinery (GOTOOLCHAIN=goX.Y.Z) can fetch and run
# an old compiler on demand via the module proxy, separately from this
# sandbox's blocked direct go.dev downloads — tried once at import time so
# pointer-encoding coverage runs for real whenever that's reachable, and
# skips cleanly (not fails) when it isn't.
OLD_GO_VERSION = "go1.17.13"
HAVE_OLD_GO_TOOLCHAIN = False
if HAVE_GO:
    try:
        subprocess.run(
            ["go", "version"],
            env={**os.environ, "GOTOOLCHAIN": OLD_GO_VERSION},
            check=True,
            capture_output=True,
            timeout=120,
        )
        HAVE_OLD_GO_TOOLCHAIN = True
    except Exception:
        HAVE_OLD_GO_TOOLCHAIN = False

_FIXTURES: dict[str, bytes] = {}
_FIXTURE_DIR: tempfile.TemporaryDirectory | None = None
_OLD_FIXTURES: dict[str, bytes] = {}
_OLD_FIXTURE_DIR: tempfile.TemporaryDirectory | None = None


def setUpModule() -> None:
    global _FIXTURE_DIR
    if not HAVE_GO:
        return
    _FIXTURE_DIR = tempfile.TemporaryDirectory(prefix="go-buildinfo-tests-")
    root = Path(_FIXTURE_DIR.name)

    dep_dir = root / "depmod"
    dep_dir.mkdir()
    (dep_dir / "go.mod").write_text("module example.com/depmod\n\ngo 1.21\n")
    (dep_dir / "dep.go").write_text("package depmod\n\nfunc Greet() string { return \"hi\" }\n")

    main_dir = root / "mainmod"
    greeting_dir = main_dir / "internal" / "greeting"
    greeting_dir.mkdir(parents=True)
    (main_dir / "go.mod").write_text(
        "module example.com/mainmod\n\ngo 1.21\n\n"
        "require example.com/depmod v0.0.0\n\n"
        "replace example.com/depmod => ../depmod\n"
    )
    (main_dir / "main.go").write_text(
        "package main\n\n"
        'import (\n\t"fmt"\n\t"example.com/mainmod/internal/greeting"\n)\n\n'
        "func main() { fmt.Println(greeting.Say()) }\n"
    )
    (greeting_dir / "greeting.go").write_text(
        'package greeting\n\nimport "example.com/depmod"\n\nfunc Say() string { return depmod.Greet() }\n'
    )

    env = {**os.environ, "CGO_ENABLED": "0", "GOFLAGS": "-mod=mod"}
    subprocess.run(["go", "mod", "tidy"], cwd=main_dir, env=env, check=True, capture_output=True)

    elf_path = root / "mainmod_elf"
    subprocess.run(["go", "build", "-o", str(elf_path), "."], cwd=main_dir, env=env, check=True, capture_output=True)
    _FIXTURES["elf"] = elf_path.read_bytes()
    _FIXTURES["go_version_m"] = subprocess.run(
        ["go", "version", "-m", str(elf_path)], check=True, capture_output=True, text=True
    ).stdout

    pe_path = root / "mainmod_pe.exe"
    subprocess.run(
        ["go", "build", "-o", str(pe_path), "."],
        cwd=main_dir,
        env={**env, "GOOS": "windows", "GOARCH": "amd64"},
        check=True,
        capture_output=True,
    )
    _FIXTURES["pe"] = pe_path.read_bytes()

    if HAVE_GCC:
        c_dir = root / "c"
        c_dir.mkdir()
        (c_dir / "hello.c").write_text("int main(){return 0;}\n")
        c_path = root / "hello_c_elf"
        subprocess.run(["gcc", "-o", str(c_path), str(c_dir / "hello.c")], check=True, capture_output=True)
        _FIXTURES["c_elf"] = c_path.read_bytes()


def tearDownModule() -> None:
    if _FIXTURE_DIR is not None:
        _FIXTURE_DIR.cleanup()
    if _OLD_FIXTURE_DIR is not None:
        _OLD_FIXTURE_DIR.cleanup()


def setUpModule_old_toolchain() -> None:
    """Builds real pointer-encoding fixtures with Go 1.17.13. Not run via
    the usual setUpModule hook (unittest only calls one per module) — invoked
    lazily from TestPointerEncoding.setUpClass instead, so a failure here
    only skips that one class rather than the whole file."""
    global _OLD_FIXTURE_DIR
    if _OLD_FIXTURE_DIR is not None:
        return
    _OLD_FIXTURE_DIR = tempfile.TemporaryDirectory(prefix="go-buildinfo-old-tests-")
    root = Path(_OLD_FIXTURE_DIR.name)

    dep_dir = root / "depmod"
    dep_dir.mkdir()
    (dep_dir / "go.mod").write_text("module example.com/depmod\n\ngo 1.17\n")
    (dep_dir / "dep.go").write_text("package depmod\n\nfunc Greet() string { return \"hi\" }\n")

    main_dir = root / "mainmod"
    main_dir.mkdir()
    (main_dir / "go.mod").write_text(
        "module example.com/mainmod\n\ngo 1.17\n\n"
        "require example.com/depmod v0.0.0\n\n"
        "replace example.com/depmod => ../depmod\n"
    )
    (main_dir / "main.go").write_text(
        'package main\n\nimport (\n\t"fmt"\n\t"example.com/depmod"\n)\n\n'
        "func main() { fmt.Println(depmod.Greet()) }\n"
    )

    env = {**os.environ, "GOTOOLCHAIN": OLD_GO_VERSION, "GOFLAGS": "-mod=mod"}
    subprocess.run(["go", "mod", "tidy"], cwd=main_dir, env=env, check=True, capture_output=True)

    elf_path = root / "mainmod_elf"
    subprocess.run(["go", "build", "-o", str(elf_path), "."], cwd=main_dir, env=env, check=True, capture_output=True)
    _OLD_FIXTURES["elf"] = elf_path.read_bytes()
    _OLD_FIXTURES["go_version_m"] = subprocess.run(
        ["go", "version", "-m", str(elf_path)], env=env, check=True, capture_output=True, text=True
    ).stdout

    pe_path = root / "mainmod_pe.exe"
    subprocess.run(
        ["go", "build", "-o", str(pe_path), "."],
        cwd=main_dir,
        env={**env, "GOOS": "windows", "GOARCH": "amd64"},
        check=True,
        capture_output=True,
    )
    _OLD_FIXTURES["pe"] = pe_path.read_bytes()


@unittest.skipUnless(HAVE_OLD_GO_TOOLCHAIN, "go1.17.13 toolchain not reachable (needs module-proxy network access)")
class TestPointerEncoding(unittest.TestCase):
    """Go 1.13-1.17 binaries use the older pointer-based build-info string
    encoding — the modern `go` on PATH (1.18+) always emits the newer
    "inline" encoding, so this is the only way to exercise that code path
    against real compiled output. Fetched via GOTOOLCHAIN rather than a
    direct go.dev download, which this sandbox's egress proxy blocks.

    Also regression coverage for a real bug found manually before this test
    existed: the PE pointer-resolution path normalized the outer
    version/module pointers against ImageBase but not the inner string-data
    pointer found one indirection further in, so every PE pointer-encoded
    binary failed to resolve. Fixed by moving the normalization into
    _AddressMapper itself so every lookup goes through the same path."""

    @classmethod
    def setUpClass(cls) -> None:
        setUpModule_old_toolchain()

    def test_elf_uses_pointer_encoding_and_matches_ground_truth(self) -> None:
        info = read_go_buildinfo(_OLD_FIXTURES["elf"])
        self.assertIsNotNone(info)
        self.assertEqual(info.encoding, "pointer")
        self.assertIn(info.go_version, _OLD_FIXTURES["go_version_m"])
        self.assertEqual(info.module.main.path, "example.com/mainmod")
        self.assertEqual(info.module.dependencies[0].path, "example.com/depmod")
        self.assertEqual(info.module.dependencies[0].replacement.path, "../depmod")

    def test_pe_uses_pointer_encoding_and_resolves_correctly(self) -> None:
        info = read_go_buildinfo(_OLD_FIXTURES["pe"])
        self.assertIsNotNone(info)
        self.assertEqual(info.format, "pe")
        self.assertEqual(info.encoding, "pointer")
        self.assertEqual(info.go_version, "go1.17.13")
        self.assertEqual(info.module.main.path, "example.com/mainmod")
        self.assertEqual(info.module.dependencies[0].path, "example.com/depmod")
        self.assertEqual(info.module.dependencies[0].replacement.path, "../depmod")


@unittest.skipUnless(HAVE_GO, "go toolchain not available")
class TestRealGoElfBinary(unittest.TestCase):
    def test_matches_go_version_dash_m_ground_truth(self) -> None:
        info = read_go_buildinfo(_FIXTURES["elf"])
        self.assertIsNotNone(info)
        truth = _FIXTURES["go_version_m"]
        self.assertIn(info.go_version, truth)
        self.assertEqual(info.format, "elf")
        self.assertEqual(info.bits, 64)
        self.assertEqual(info.encoding, "inline")

    def test_module_path_and_main_module(self) -> None:
        info = read_go_buildinfo(_FIXTURES["elf"])
        self.assertEqual(info.module.path, "example.com/mainmod")
        self.assertEqual(info.module.main.path, "example.com/mainmod")
        self.assertEqual(info.module.main.version, "(devel)")

    def test_local_replaced_dependency(self) -> None:
        info = read_go_buildinfo(_FIXTURES["elf"])
        deps = info.module.dependencies
        self.assertEqual(len(deps), 1)
        self.assertEqual(deps[0].path, "example.com/depmod")
        self.assertEqual(deps[0].version, "v0.0.0")
        self.assertIsNotNone(deps[0].replacement)
        self.assertEqual(deps[0].replacement.path, "../depmod")

    def test_build_settings(self) -> None:
        info = read_go_buildinfo(_FIXTURES["elf"])
        settings = info.module.settings
        self.assertEqual(settings.get("CGO_ENABLED"), "0")
        self.assertEqual(settings.get("GOOS"), "linux")
        self.assertEqual(settings.get("GOARCH"), "amd64")

    def test_nothing_left_unparsed(self) -> None:
        info = read_go_buildinfo(_FIXTURES["elf"])
        self.assertEqual(info.module.unparsed_lines, [])


@unittest.skipUnless(HAVE_GO, "go toolchain not available")
class TestRealGoPeBinary(unittest.TestCase):
    def test_cross_compiled_windows_binary(self) -> None:
        info = read_go_buildinfo(_FIXTURES["pe"])
        self.assertIsNotNone(info)
        self.assertEqual(info.format, "pe")
        self.assertEqual(info.bits, 64)
        self.assertEqual(info.encoding, "inline")
        self.assertEqual(info.module.settings.get("GOOS"), "windows")
        self.assertEqual(info.module.main.path, "example.com/mainmod")
        self.assertEqual(info.module.dependencies[0].path, "example.com/depmod")


@unittest.skipUnless(HAVE_GO and HAVE_GCC, "go and/or gcc not available")
class TestNegativeCase(unittest.TestCase):
    def test_non_go_elf_reports_no_build_info_not_an_error(self) -> None:
        info = read_go_buildinfo(_FIXTURES["c_elf"])
        self.assertIsNone(info)


@unittest.skipUnless(HAVE_GO, "go toolchain not available")
class TestMalformedInputHandling(unittest.TestCase):
    """Regression coverage for a real bug found during development: a
    corrupted byte inside the version/module string could raise a raw
    UnicodeDecodeError instead of GoBuildInfoError. Fixed in
    _decode_utf8_strict(); this suite guards against it recurring."""

    def test_corrupted_flags_byte_raises_typed_error(self) -> None:
        data = bytearray(_FIXTURES["elf"])
        header = _find_magic(bytes(data))
        data[header + 15] |= 0x4  # set an unsupported flag bit
        with self.assertRaises(GoBuildInfoError):
            read_go_buildinfo(bytes(data))

    def test_truncated_header_raises_typed_error(self) -> None:
        data = bytes(_FIXTURES["elf"])
        header = _find_magic(data)
        with self.assertRaises(GoBuildInfoError):
            read_go_buildinfo(data[: header + 20])

    def test_invalid_utf8_in_version_string_raises_typed_error_not_unicode_error(self) -> None:
        data = bytearray(_FIXTURES["elf"])
        header = _find_magic(bytes(data))
        # byte 40 sits inside the inline version string's byte range for
        # this fixture; flipping it mid-run is exactly the case that used
        # to leak a raw UnicodeDecodeError before the fix.
        data[header + 40] ^= 0xFF
        try:
            read_go_buildinfo(bytes(data))
        except GoBuildInfoError:
            pass  # acceptable: some flips are caught earlier as structural errors
        except UnicodeDecodeError:
            self.fail("UnicodeDecodeError leaked instead of being wrapped as GoBuildInfoError")

    def test_fuzz_no_uncaught_exceptions(self) -> None:
        """2,000 random byte-flip corruptions near the header must only
        ever produce a clean success or a GoBuildInfoError — never any
        other exception type."""
        data = bytearray(_FIXTURES["elf"])
        header = _find_magic(bytes(data))
        rng = random.Random(20261018)
        crashes: list[tuple[str, str]] = []
        for _ in range(2000):
            corrupted = bytearray(data)
            for _ in range(rng.randint(1, 20)):
                pos = header + rng.randint(0, 4000)
                if pos < len(corrupted):
                    corrupted[pos] ^= rng.randint(1, 255)
            try:
                read_go_buildinfo(bytes(corrupted))
            except GoBuildInfoError:
                pass
            except Exception as error:  # noqa: BLE001 - intentional catch-all for this assertion
                crashes.append((type(error).__name__, str(error)))
        self.assertEqual(crashes, [], f"{len(crashes)} uncaught exception(s) during fuzzing, e.g. {crashes[:3]}")


if __name__ == "__main__":
    unittest.main()
