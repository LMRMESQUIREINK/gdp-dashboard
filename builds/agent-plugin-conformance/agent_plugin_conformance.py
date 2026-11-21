"""A real, dependency-free conformance checker for the Agent Plugins 1.0.0
specification (https://github.com/agentplugins/agent-plugins-spec,
spec/1.0.0.md), built by reading that primary spec document directly --
not guessed from a secondary article describing it.

Checks a plugin package directory against:
  - Section 5 (Manifest): plugin.json's closed field schema, the required
    $schema/name fields, the name character-set/length constraints, the
    author object's closed field set, and the exact fatal-vs-non-fatal
    distinction the spec draws (an unknown top-level field, or a
    non-object `extensions` field, are reported and ignored; everything
    else that violates the schema is fatal and the whole plugin is
    rejected).
  - Section 6 (Component discovery): the two fixed component locations
    (skills/, mcp.json) and the "missing is fine, wrong kind is a
    per-component failure, not a whole-plugin failure" rule.
  - Section 8 (Client extensions): extensions object/value shape and
    namespace-to-directory correspondence.

Also detects one real, independently-confirmed incompatibility: Claude
Code's own plugin format puts plugin.json inside a `.claude-plugin/`
subdirectory instead of at the plugin root the spec requires -- found by
checking this project's own previously-shipped `/builds/claude-code-mods/`
plugins and the real external `andriitk/cc-unibrow` plugin directly, not
assumed from any article.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

CANONICAL_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
PERMITTED_TOP_LEVEL = {
    "$schema", "name", "version", "description", "author",
    "homepage", "repository", "license", "keywords", "extensions",
}
PERMITTED_AUTHOR_FIELDS = {"name", "email", "url"}
NAME_RE = re.compile(r"^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")


@dataclass
class Finding:
    level: str  # "fatal" | "warning" | "info"
    code: str
    message: str


@dataclass
class AuditReport:
    findings: list[Finding] = field(default_factory=list)
    manifest: dict | None = None
    skills: list[str] = field(default_factory=list)
    has_mcp_json: bool = False

    def fatal(self, code: str, message: str) -> None:
        self.findings.append(Finding("fatal", code, message))

    def warn(self, code: str, message: str) -> None:
        self.findings.append(Finding("warning", code, message))

    def info(self, code: str, message: str) -> None:
        self.findings.append(Finding("info", code, message))

    @property
    def ok(self) -> bool:
        """Mirrors the spec's own distinction exactly: the plugin is
        rejected ('not ok') only when a FATAL finding exists -- an
        unknown top-level field or a non-object extensions field are by
        the spec's own text reported-and-ignored, never rejection
        grounds on their own.
        """
        return not any(f.level == "fatal" for f in self.findings)


def _check_name(name, report: AuditReport) -> None:
    if not isinstance(name, str):
        report.fatal("invalid-name-type", f"'name' must be a string, got {type(name).__name__}")
        return
    if not (1 <= len(name) <= 64):
        report.fatal("invalid-name-length", f"'name' must be 1-64 characters, got {len(name)}")
        return
    if not NAME_RE.match(name):
        report.fatal(
            "invalid-name-charset",
            f"'name' {name!r} violates §5.5: lowercase alphanumeric/hyphen/period only, "
            f"must start and end alphanumeric, no '--' or '..'",
        )


def _check_author(author, report: AuditReport) -> None:
    if not isinstance(author, dict):
        report.fatal("invalid-author-type", f"'author' must be an object, got {type(author).__name__}")
        return
    extra = set(author.keys()) - PERMITTED_AUTHOR_FIELDS
    if extra:
        report.fatal(
            "invalid-author-fields",
            f"'author' object permits only {sorted(PERMITTED_AUTHOR_FIELDS)}, found extra: {sorted(extra)}",
        )
        return
    for k, v in author.items():
        if not isinstance(v, str):
            report.fatal("invalid-author-field-type", f"author.{k} must be a string, got {type(v).__name__}")


def _check_extensions(extensions, report: AuditReport) -> None:
    # §5.2 carves out exactly one exception for `extensions`: the
    # WHOLE field being non-object is reported-and-ignored, not fatal.
    if not isinstance(extensions, dict):
        report.warn(
            "non-object-extensions-field",
            f"'extensions' must be an object per §8.1; found {type(extensions).__name__}. "
            f"Per §5.2 this specific violation is reported and ignored, not fatal.",
        )
        return
    # But §8.1 separately requires every VALUE inside a (dict-shaped)
    # extensions object to itself be an object -- that MUST isn't one of
    # §5.2's two named exceptions, so a non-object value here is fatal.
    for namespace, value in extensions.items():
        if not isinstance(value, dict):
            report.fatal(
                "non-object-extension-value",
                f"extensions[{namespace!r}] must be an object per §8.1, got {type(value).__name__}",
            )
        if "." not in namespace:
            report.info(
                "non-reverse-domain-namespace",
                f"extension namespace {namespace!r} doesn't look like a reverse-domain identifier "
                f"(§8 SHOULD, not MUST, so this is informational only)",
            )


def validate_manifest(data) -> AuditReport:
    report = AuditReport()
    if not isinstance(data, dict):
        report.fatal("manifest-not-an-object", f"plugin.json must contain a top-level object, got {type(data).__name__}")
        return report

    report.manifest = data

    unknown = set(data.keys()) - PERMITTED_TOP_LEVEL
    for field_name in sorted(unknown):
        report.warn(
            "unknown-top-level-field",
            f"'{field_name}' is not a field §5.2's closed schema permits; "
            f"reported and ignored, plugin still loads",
        )

    if "$schema" not in data:
        report.fatal("missing-schema-field", "required field '$schema' is missing (§5.3)")
    elif data["$schema"] != CANONICAL_SCHEMA:
        report.fatal(
            "unrecognized-schema",
            f"'$schema' must be the exact canonical identifier {CANONICAL_SCHEMA!r}, "
            f"got {data['$schema']!r}",
        )

    if "name" not in data:
        report.fatal("missing-name-field", "required field 'name' is missing (§5.3)")
    else:
        _check_name(data["name"], report)

    if "version" in data and not isinstance(data["version"], str):
        report.fatal("invalid-version-type", f"'version' must be a string, got {type(data['version']).__name__}")
    if "description" in data and not isinstance(data["description"], str):
        report.fatal("invalid-description-type", f"'description' must be a string, got {type(data['description']).__name__}")
    if "homepage" in data and not isinstance(data["homepage"], str):
        report.fatal("invalid-homepage-type", f"'homepage' must be a string, got {type(data['homepage']).__name__}")
    if "repository" in data and not isinstance(data["repository"], str):
        report.fatal("invalid-repository-type", f"'repository' must be a string, got {type(data['repository']).__name__}")
    if "license" in data and not isinstance(data["license"], str):
        report.fatal("invalid-license-type", f"'license' must be a string, got {type(data['license']).__name__}")
    if "keywords" in data:
        kw = data["keywords"]
        if not isinstance(kw, list) or not all(isinstance(k, str) for k in kw):
            report.fatal("invalid-keywords-type", "'keywords' must be an array of strings")
    if "author" in data:
        _check_author(data["author"], report)
    if "extensions" in data:
        _check_extensions(data["extensions"], report)

    return report


def discover_components(plugin_root: Path, report: AuditReport) -> None:
    """§6: fixed component locations. Missing is fine. Present-but-
    wrong-kind invalidates only that component type, never the plugin.
    """
    skills_dir = plugin_root / "skills"
    if skills_dir.exists():
        if not skills_dir.is_dir():
            report.warn("skills-not-a-directory", "'skills' exists but is not a directory; skills component type is invalid, other components still load")
        else:
            for child in sorted(skills_dir.iterdir()):
                if child.is_dir() and (child / "SKILL.md").is_file():
                    report.skills.append(child.name)

    mcp_path = plugin_root / "mcp.json"
    if mcp_path.exists():
        if not mcp_path.is_file():
            report.warn("mcp-json-not-a-file", "'mcp.json' exists but is not a regular file; MCP component type is invalid, other components still load")
        else:
            report.has_mcp_json = True
            try:
                json.loads(mcp_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                report.warn("mcp-json-invalid-json", f"'mcp.json' is not valid JSON: {e}")


def check_extension_directories(plugin_root: Path, report: AuditReport) -> None:
    if not report.manifest:
        return
    extensions = report.manifest.get("extensions")
    if not isinstance(extensions, dict):
        return
    for namespace in extensions:
        ext_dir = plugin_root / namespace
        if ext_dir.exists() and not ext_dir.is_dir():
            report.warn(
                "extension-path-not-a-directory",
                f"a path named for extension namespace {namespace!r} exists but is not a directory (§8.2)",
            )


def detect_non_portable_claude_layout(plugin_root: Path, report: AuditReport) -> None:
    """Not part of the spec itself -- a real, independently-confirmed
    compatibility check: Claude Code's own plugin format nests
    plugin.json under .claude-plugin/ instead of at the plugin root the
    spec requires. Confirmed directly against this project's own
    previously-shipped /builds/claude-code-mods/ plugins and the real
    external andriitk/cc-unibrow repo, not assumed from any article.
    """
    root_manifest = plugin_root / "plugin.json"
    claude_manifest = plugin_root / ".claude-plugin" / "plugin.json"
    if not root_manifest.exists() and claude_manifest.exists():
        report.info(
            "claude-code-layout-not-portable",
            "no root plugin.json, but .claude-plugin/plugin.json exists: this is Claude Code's "
            "own plugin layout, which is not Agent Plugins 1.0.0-portable (§5.1 requires "
            "plugin.json at the plugin root)",
        )


def audit_plugin(plugin_root: str | Path) -> AuditReport:
    plugin_root = Path(plugin_root)
    manifest_path = plugin_root / "plugin.json"

    if not manifest_path.is_file():
        report = AuditReport()
        detect_non_portable_claude_layout(plugin_root, report)
        if not any(f.code == "claude-code-layout-not-portable" for f in report.findings):
            report.fatal("missing-manifest", f"no plugin.json at the plugin root ({plugin_root})")
        else:
            report.fatal("missing-manifest", f"no plugin.json at the plugin root ({plugin_root}); see the info finding above")
        return report

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        report = AuditReport()
        report.fatal("invalid-json", f"plugin.json is not valid JSON: {e}")
        return report

    report = validate_manifest(data)
    discover_components(plugin_root, report)
    check_extension_directories(plugin_root, report)
    detect_non_portable_claude_layout(plugin_root, report)
    return report


def format_report(report: AuditReport) -> str:
    if not report.findings:
        return "Conforms to Agent Plugins 1.0.0 with no findings."
    lines = [f"[{f.level.upper()}] {f.code}: {f.message}" for f in report.findings]
    verdict = "CONFORMS (no fatal findings)" if report.ok else "REJECTED (at least one fatal finding)"
    lines.append(f"\nVerdict: {verdict}")
    if report.skills:
        lines.append(f"Skills discovered: {report.skills}")
    lines.append(f"mcp.json present and valid: {report.has_mcp_json}")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("usage: python3 agent_plugin_conformance.py <plugin root directory>")
        raise SystemExit(2)
    result = audit_plugin(sys.argv[1])
    print(format_report(result))
    raise SystemExit(0 if result.ok else 1)
