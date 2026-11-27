"""Tests for agent_plugin_conformance.py.

Fixtures under tests/fixtures/ are built two ways:
  - hello-plugin/, reports-plugin/, full-manifest-plugin/,
    extension-plugin/: reproduce the real Agent Plugins 1.0.0 spec's own
    worked examples verbatim (spec/1.0.0.md §5.2, §6.1, §8.2, from the
    real spec repo cloned at this round's analysis time), so "does this
    pass" is checked against the spec's own stated-good examples, not
    examples this build invented.
  - cc-unibrow-real/: an exact copy of the real, currently-shipipng
    andriitk/cc-unibrow Claude Code plugin's own plugin.json (its
    .claude-plugin/plugin.json), proving the non-portable-layout and
    missing-$schema findings against real external material, not a
    synthetic stand-in.

This project's own previously-shipped /builds/claude-code-mods/ plugins
are audited directly in place (not copied) as a second real source for
the same findings.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from agent_plugin_conformance import audit_plugin, validate_manifest

FIXTURES = Path(__file__).parent / "tests" / "fixtures"
REPO_ROOT = Path(__file__).resolve().parents[2]


def _codes(report):
    return [f.code for f in report.findings]


# -- Real spec worked examples: all MUST conform cleanly -------------------


def test_hello_plugin_spec_example_conforms():
    report = audit_plugin(FIXTURES / "hello-plugin")
    assert report.ok, report.findings
    assert report.skills == ["greet"]


def test_reports_plugin_spec_example_conforms():
    report = audit_plugin(FIXTURES / "reports-plugin")
    assert report.ok, report.findings
    assert report.skills == ["summarize"]
    assert report.has_mcp_json is True


def test_full_manifest_spec_example_conforms():
    report = audit_plugin(FIXTURES / "full-manifest-plugin")
    assert report.ok, report.findings
    assert report.manifest["version"] == "1.2.0"


def test_extension_plugin_spec_example_conforms():
    report = audit_plugin(FIXTURES / "extension-plugin")
    assert report.ok, report.findings
    # No warning about the extension directory -- it's genuinely there.
    assert "extension-path-not-a-directory" not in _codes(report)


# -- §5.5's own listed invalid/valid names, verbatim -------------------------


def test_spec_valid_names_all_pass():
    for name in ["my-plugin", "acme.tools", "lint3r", "a"]:
        report = validate_manifest({"$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json", "name": name})
        assert report.ok, (name, report.findings)


def test_spec_invalid_names_all_fail():
    cases = {
        "My-Plugin": "uppercase",
        "-start": "leading hyphen",
        "has--double": "consecutive hyphens",
        "too.many..dots": "consecutive periods",
    }
    for name, _why in cases.items():
        report = validate_manifest({"$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json", "name": name})
        assert not report.ok, (name, "should have failed")
        assert any(f.level == "fatal" for f in report.findings)


def test_empty_name_fails():
    report = validate_manifest({"$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json", "name": ""})
    assert not report.ok


# -- §5.2's exact fatal vs. non-fatal distinction ----------------------------


def test_unknown_top_level_field_is_warning_not_fatal():
    data = {
        "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        "name": "my-plugin",
        "displayName": "My Plugin",  # not in the permitted set
    }
    report = validate_manifest(data)
    assert report.ok, report.findings  # still loads
    assert "unknown-top-level-field" in _codes(report)
    assert all(f.level != "fatal" for f in report.findings)


def test_non_object_extensions_field_is_warning_not_fatal():
    data = {"$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json", "name": "my-plugin", "extensions": "nope"}
    report = validate_manifest(data)
    assert report.ok, report.findings
    assert "non-object-extensions-field" in _codes(report)


def test_non_object_extension_value_is_fatal():
    # §8.1's MUST ("whose member values are objects") isn't one of
    # §5.2's two named exceptions (unknown field, non-object `extensions`
    # itself) -- so a non-object VALUE inside an object-shaped extensions
    # field is a schema violation the spec's own text makes fatal.
    data = {
        "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        "name": "my-plugin",
        "extensions": {"com.example.client": "not-an-object"},
    }
    report = validate_manifest(data)
    assert not report.ok
    assert "non-object-extension-value" in _codes(report)


def test_missing_schema_field_is_fatal():
    report = validate_manifest({"name": "my-plugin"})
    assert not report.ok
    assert "missing-schema-field" in _codes(report)


def test_wrong_schema_value_is_fatal():
    report = validate_manifest({"$schema": "not-the-real-one", "name": "my-plugin"})
    assert not report.ok
    assert "unrecognized-schema" in _codes(report)


def test_missing_name_field_is_fatal():
    report = validate_manifest({"$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"})
    assert not report.ok
    assert "missing-name-field" in _codes(report)


def test_wrong_type_for_permitted_field_is_fatal():
    data = {"$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json", "name": "my-plugin", "version": 2}
    report = validate_manifest(data)
    assert not report.ok
    assert "invalid-version-type" in _codes(report)


def test_author_with_extra_field_is_fatal():
    data = {
        "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        "name": "my-plugin",
        "author": {"name": "X", "twitter": "@x"},
    }
    report = validate_manifest(data)
    assert not report.ok
    assert "invalid-author-fields" in _codes(report)


def test_manifest_not_an_object_is_fatal():
    report = validate_manifest(["not", "an", "object"])
    assert not report.ok
    assert "manifest-not-an-object" in _codes(report)


# -- §6 component discovery: missing is fine, wrong kind is per-component --


def test_missing_skills_and_mcp_json_is_not_an_error():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "plugin.json").write_text(
            json.dumps({"$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json", "name": "bare-plugin"})
        )
        report = audit_plugin(root)
        assert report.ok, report.findings
        assert report.skills == []
        assert report.has_mcp_json is False


def test_skills_resolving_to_a_file_invalidates_only_that_component():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "plugin.json").write_text(
            json.dumps({"$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json", "name": "weird-plugin"})
        )
        (root / "skills").write_text("not a directory")
        report = audit_plugin(root)
        assert report.ok, report.findings  # not fatal -- whole plugin still loads
        assert "skills-not-a-directory" in _codes(report)


def test_mcp_json_resolving_to_a_directory_invalidates_only_that_component():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "plugin.json").write_text(
            json.dumps({"$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json", "name": "weird-plugin"})
        )
        (root / "mcp.json").mkdir()
        report = audit_plugin(root)
        assert report.ok, report.findings
        assert "mcp-json-not-a-file" in _codes(report)


def test_malformed_mcp_json_is_warning_not_fatal():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "plugin.json").write_text(
            json.dumps({"$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json", "name": "weird-plugin"})
        )
        (root / "mcp.json").write_text("{not valid json")
        report = audit_plugin(root)
        assert report.ok, report.findings
        assert "mcp-json-invalid-json" in _codes(report)


# -- Real, external, independently-confirmed non-portable-layout findings --


def test_real_cc_unibrow_plugin_is_missing_root_manifest_and_not_portable():
    report = audit_plugin(FIXTURES / "cc-unibrow-real")
    assert not report.ok
    assert "missing-manifest" in _codes(report)
    assert "claude-code-layout-not-portable" in _codes(report)


def test_real_cc_unibrow_manifest_itself_lacks_schema_and_has_unknown_field():
    # Even read directly (bypassing the missing-root-manifest check), the
    # real Claude Code manifest content doesn't attempt Agent Plugins
    # 1.0.0 conformance at all: no $schema field, and a displayName field
    # the spec's closed schema doesn't permit.
    real_manifest = json.loads((FIXTURES / "cc-unibrow-real" / ".claude-plugin" / "plugin.json").read_text())
    report = validate_manifest(real_manifest)
    assert not report.ok
    assert "missing-schema-field" in _codes(report)
    assert "unknown-top-level-field" in _codes(report)


def test_this_projects_own_real_claude_code_mods_are_not_portable():
    # Audited directly in place against this project's own three
    # previously-shipped, previously-tested Claude Code plugins -- not a
    # copied fixture, the real build directories.
    mods_dir = REPO_ROOT / "builds" / "claude-code-mods"
    found_any = False
    for mod in ["blast-radius", "cache-keeper", "collision-guard"]:
        mod_dir = mods_dir / mod
        if not mod_dir.is_dir():
            continue
        found_any = True
        report = audit_plugin(mod_dir)
        assert not report.ok, f"{mod}: expected non-conformant, got {report.findings}"
        assert "missing-manifest" in _codes(report), mod
        assert "claude-code-layout-not-portable" in _codes(report), mod
    assert found_any, "expected to find at least one real claude-code-mods plugin to audit"


TESTS = [
    test_hello_plugin_spec_example_conforms,
    test_reports_plugin_spec_example_conforms,
    test_full_manifest_spec_example_conforms,
    test_extension_plugin_spec_example_conforms,
    test_spec_valid_names_all_pass,
    test_spec_invalid_names_all_fail,
    test_empty_name_fails,
    test_unknown_top_level_field_is_warning_not_fatal,
    test_non_object_extensions_field_is_warning_not_fatal,
    test_non_object_extension_value_is_fatal,
    test_missing_schema_field_is_fatal,
    test_wrong_schema_value_is_fatal,
    test_missing_name_field_is_fatal,
    test_wrong_type_for_permitted_field_is_fatal,
    test_author_with_extra_field_is_fatal,
    test_manifest_not_an_object_is_fatal,
    test_missing_skills_and_mcp_json_is_not_an_error,
    test_skills_resolving_to_a_file_invalidates_only_that_component,
    test_mcp_json_resolving_to_a_directory_invalidates_only_that_component,
    test_malformed_mcp_json_is_warning_not_fatal,
    test_real_cc_unibrow_plugin_is_missing_root_manifest_and_not_portable,
    test_real_cc_unibrow_manifest_itself_lacks_schema_and_has_unknown_field,
    test_this_projects_own_real_claude_code_mods_are_not_portable,
]


def run(name, fn):
    try:
        fn()
        print(f"PASS  {name}")
        return True
    except AssertionError as e:
        print(f"FAIL  {name}: {e}")
        return False


if __name__ == "__main__":
    results = [run(t.__name__, t) for t in TESTS]
    passed = sum(results)
    total = len(results)
    print(f"\n{passed}/{total} passed")
    if passed != total:
        raise SystemExit(1)
