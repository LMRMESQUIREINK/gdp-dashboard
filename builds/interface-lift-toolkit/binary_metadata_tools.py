"""
Binary static-analysis tools — wraps go_buildinfo.py and
rust_cargo_auditable.py (from /builds/go-buildinfo-extractor/, copied
here unmodified, same convention prop_firm_*.py already follows) as two
new "local" tools. Reading a binary's own embedded build metadata is
pure local computation — no network, no write — exactly like
prop_firm_size_check, so effect="local" is correct for both.

Checks semantics, deliberately not "did we find what we were looking
for": both underlying readers document that a clean `None`/no-section
result is a normal, successful outcome (a binary just not being Go, or
not built with `cargo auditable`), not a tool failure — see each
module's own docstring/README. So `checks` here means "did the read
complete, either with a real result or a correct negative one," and
only a missing file or the module's own typed error (malformed input)
sets it False. Whether the binary *turned out to be* Go/cargo-auditable
is reported as a plain output field, not folded into `ok`.
"""
from __future__ import annotations

from pathlib import Path

from go_buildinfo import GoBuildInfoError, read_go_buildinfo
from rust_cargo_auditable import RustAuditableError, read_cargo_auditable

from toolkit.registry import ToolRegistry
from toolkit.result import result


def register_binary_metadata_tools(registry: ToolRegistry) -> None:
    @registry.tool(effect="local")
    def go_buildinfo_check(binary_path: str) -> dict:
        """Read the Go compiler version, main module path+version,
        dependency list (including local replace directives), and build
        settings embedded in a compiled Go binary. Works on ELF and PE;
        returns go_binary=false (not an error) if no Go build-info
        header is found. binary_path: path to the binary on disk."""
        path = Path(binary_path)
        if not path.is_file():
            return result(f"{binary_path} is not a file", checks=[("file exists", False)])

        try:
            info = read_go_buildinfo(path.read_bytes())
        except GoBuildInfoError as error:
            return result(
                f"malformed Go build-info in {path.name}: {error}",
                checks=[("binary read and parsed", False)],
            )

        if info is None:
            return result(
                f"{path.name} has no Go build-info header (not a Go binary, or it was stripped)",
                checks=[("binary read and parsed", True)],
                go_binary=False,
            )

        return result(
            f"{path.name}: {info.go_version}, module {info.module.path}, "
            f"{len(info.module.dependencies)} dependency(ies)",
            checks=[("binary read and parsed", True)],
            go_binary=True,
            format=info.format,
            go_version=info.go_version,
            encoding=info.encoding,
            module_path=info.module.path,
            main_module={"path": info.module.main.path, "version": info.module.main.version},
            dependencies=[
                {
                    "path": dep.path,
                    "version": dep.version,
                    "replacement": (
                        {"path": dep.replacement.path, "version": dep.replacement.version}
                        if dep.replacement
                        else None
                    ),
                }
                for dep in info.module.dependencies
            ],
            settings=info.module.settings,
        )

    @registry.tool(effect="local")
    def rust_cargo_auditable_check(binary_path: str) -> dict:
        """Read the cargo-auditable dependency graph (package name,
        version, source, dependency edges, and any cyclic dependency
        indices) embedded in a Rust binary built with `cargo auditable
        build`. Works on ELF and PE; returns cargo_auditable=false (not
        an error) if no .dep-v0 section is found. binary_path: path to
        the binary on disk."""
        path = Path(binary_path)
        if not path.is_file():
            return result(f"{binary_path} is not a file", checks=[("file exists", False)])

        try:
            info = read_cargo_auditable(path.read_bytes())
        except RustAuditableError as error:
            return result(
                f"malformed cargo-auditable data in {path.name}: {error}",
                checks=[("binary read and parsed", False)],
            )

        if info is None:
            return result(
                f"{path.name} has no .dep-v0 section (not built with `cargo auditable`)",
                checks=[("binary read and parsed", True)],
                cargo_auditable=False,
            )

        root = info.packages[info.root_package_index] if info.root_package_index is not None else None
        summary = f"{path.name}: {len(info.packages)} package(s)"
        if root is not None:
            summary += f", root {root.name} {root.version}"
        if info.cyclic_dependency_indices:
            summary += f", {len(info.cyclic_dependency_indices)} package(s) in a dependency cycle"

        return result(
            summary,
            checks=[("binary read and parsed", True)],
            cargo_auditable=True,
            packages=[
                {
                    "name": pkg.name,
                    "version": pkg.version,
                    "source": pkg.source,
                    "kind": pkg.kind,
                    "dependencies": pkg.dependencies,
                    "root": pkg.root,
                }
                for pkg in info.packages
            ],
            root_package_index=info.root_package_index,
            cyclic_dependency_indices=info.cyclic_dependency_indices,
        )
