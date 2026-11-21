"""Tests for readme_link_auditor.py.

Run against the real, unmodified README.md from HeyPuter/everything
(committed as a fixture, tests/fixtures/everything/README.md), with a
lightweight skeleton of the real repo tree alongside it (empty
directories/files at every path the real repo actually has, so relative-
link resolution can run for real without committing all 37,642 real
files) -- same "real material as a committed fixture" convention this
project has used throughout (real READMEs, real CSVs, real signed skill
bundles).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from readme_link_auditor import (
    audit_readme,
    check_anchor_links,
    check_relative_links,
    check_row_consistency,
    github_slug,
)

FIXTURE_DIR = Path(__file__).parent / "tests" / "fixtures" / "everything"
FIXTURE_README = FIXTURE_DIR / "README.md"


def _codes(report):
    return [f.code for f in report.findings]


def test_real_readme_finds_dangling_link_status_anchor():
    report = audit_readme(FIXTURE_README, FIXTURE_DIR)
    hits = [f for f in report.findings if f.code == "dangling-anchor"]
    assert len(hits) == 1, hits
    assert "link-status" in hits[0].message


def test_real_readme_finds_equipment_escape():
    report = audit_readme(FIXTURE_README, FIXTURE_DIR)
    hits = [f for f in report.findings if f.code == "escapes-repo-root"]
    assert len(hits) == 1, hits
    assert "equipment" in hits[0].message


def test_real_readme_finds_assets_row_mismatch():
    report = audit_readme(FIXTURE_README, FIXTURE_DIR)
    hits = [f for f in report.findings if f.code == "row-target-mismatch"]
    assert len(hits) == 1, hits
    assert "assets" in hits[0].message and "equipment" in hits[0].message


def test_real_readme_has_exactly_these_three_findings_and_no_others():
    # The discriminating claim: everything else in this real, ~45-row,
    # 11-link-section README resolves cleanly. If this count ever grows,
    # something regressed -- either a real new problem, or a false
    # positive that needs isolating before it's reported as one.
    report = audit_readme(FIXTURE_README, FIXTURE_DIR)
    assert len(report.findings) == 3, report.findings
    assert not report.ok


def test_unicode_headings_slug_correctly_not_stripped_to_empty_or_ascii():
    # Regression: the first draft's slug filter was a literal ASCII
    # character class, [a-z0-9 _-], which silently stripped every accented
    # Latin letter and every CJK ideograph -- 'Ofimática' slugged to
    # 'ofimtica' (dropping the accent) and '办公' slugged to '' (dropping
    # everything). Found by running against HeyPuter/everything's own real
    # Spanish and Chinese README translations (committed below), where it
    # manufactured a dozen false "dangling anchor" findings against
    # headings that resolve fine on GitHub. str.isalnum()/.lower() are
    # Unicode-aware, so the fix is general, not special-cased per script.
    assert github_slug("Ofimática") == "ofimática"
    assert github_slug("Ingeniería") == "ingeniería"
    assert github_slug("办公") == "办公"
    assert github_slug("开发者工具") == "开发者工具"


def test_real_spanish_translation_finds_only_the_same_two_real_bugs():
    es_readme = FIXTURE_DIR / "README.es.md.real"
    report = audit_readme(es_readme, FIXTURE_DIR)
    codes = sorted(_codes(report))
    assert codes == ["dangling-anchor", "escapes-repo-root", "row-target-mismatch"], codes
    link_status = next(f for f in report.findings if f.code == "dangling-anchor")
    assert "link-status" in link_status.message
    # None of the Spanish nav's own accented anchors (#colaboración,
    # #ingeniería, #ofimática) are false-flagged after the Unicode fix.
    assert "ofimática" not in link_status.message.split("(")[0]


def test_real_chinese_translation_finds_only_the_same_two_real_bugs():
    zh_readme = FIXTURE_DIR / "README.zh-CN.md.real"
    report = audit_readme(zh_readme, FIXTURE_DIR)
    codes = sorted(_codes(report))
    assert codes == ["dangling-anchor", "escapes-repo-root", "row-target-mismatch"], codes


def test_github_slug_matches_every_real_heading_in_the_fixture():
    # Reproduces, by hand, what every nav link at the top of the real
    # README expects '#office', '#developer-tools', etc. to mean.
    cases = {
        "Getting started": "getting-started",
        "Office": "office",
        "Collaboration": "collaboration",
        "Creative Tools": "creative-tools",
        "Engineering": "engineering",
        "Productivity": "productivity",
        "Finance": "finance",
        "Business": "business",
        "Developer Tools": "developer-tools",
        "Games": "games",
        "License": "license",
    }
    for heading, slug in cases.items():
        assert github_slug(heading) == slug, heading


def test_anchor_matching_a_real_heading_is_not_flagged():
    text = "## Office\n\n[Office](#office)\n"
    findings = check_anchor_links(text)
    assert findings == []


def test_leading_dot_slash_is_normalized_not_treated_as_a_mismatch():
    # Regression: the real README's Tasks/Time Tracking rows use
    # './src/tasks/icon-128.png' (with a leading './') for the icon while
    # the title/Source links use the bare 'src/tasks/' form. The first
    # draft of _entity_name() didn't strip './', so these two
    # functionally-identical paths reduced to different "entities" ('.'
    # vs 'tasks') and the row was wrongly flagged as a mismatch. Caught by
    # running against the real fixture, not invented.
    row = (
        '<tr><td><img src="./src/tasks/icon-128.png"> '
        '<a href="src/tasks/">Tasks</a></td>'
        '<td><a href="src/tasks/">Source</a></td></tr>'
    )
    findings = check_row_consistency(row)
    assert findings == [], findings


def test_clean_row_with_external_demo_link_is_not_flagged():
    row = (
        '<tr><td><img src="src/spreadsheet/icon-128.png"> '
        '<a href="https://spreadsheet.puter.com/">Spreadsheet</a></td>'
        '<td><a href="https://spreadsheet.puter.com/">Try it</a>'
        '<a href="src/spreadsheet/">Source</a></td></tr>'
    )
    findings = check_row_consistency(row)
    assert findings == [], findings


def test_a_genuinely_inconsistent_row_is_caught():
    # Planted counterexample, proving the detector actually discriminates
    # rather than passing everything: icon/source say 'widgets', title
    # says a different app entirely.
    row = (
        '<tr><td><img src="src/widgets/icon-128.png"> '
        '<a href="../gadgets/">Widgets</a></td>'
        '<td><a href="src/widgets/">Source</a></td></tr>'
    )
    findings = check_row_consistency(row)
    codes = [f.code for f in findings]
    assert codes == ["row-target-mismatch"]
    assert "widgets" in findings[0].message and "gadgets" in findings[0].message


def test_relative_link_to_a_real_path_is_not_flagged():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "src" / "spreadsheet").mkdir(parents=True)
        text = '<a href="src/spreadsheet/">Source</a>'
        findings = check_relative_links(text, root)
        assert findings == []


def test_relative_link_to_a_missing_path_is_flagged():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        text = '<a href="src/does-not-exist/">Source</a>'
        findings = check_relative_links(text, root)
        assert len(findings) == 1
        assert findings[0].code == "broken-relative-link"


def test_relative_link_escaping_repo_root_is_flagged():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "repo"
        root.mkdir()
        (Path(tmp) / "sibling").mkdir()
        text = '<a href="../sibling/">Elsewhere</a>'
        findings = check_relative_links(text, root)
        assert len(findings) == 1
        assert findings[0].code == "escapes-repo-root"


def test_external_and_anchor_links_are_never_treated_as_relative_links():
    with tempfile.TemporaryDirectory() as tmp:
        text = (
            '<a href="https://example.com/">External</a>'
            '<a href="#office">Anchor</a>'
            '<a href="mailto:x@example.com">Mail</a>'
        )
        findings = check_relative_links(text, Path(tmp))
        assert findings == []


def test_report_is_ok_when_there_are_no_errors():
    from readme_link_auditor import AuditReport

    report = AuditReport()
    assert report.ok
    report.warn("w", "just a warning")
    assert report.ok
    report.error("e", "a real problem")
    assert not report.ok


TESTS = [
    test_real_readme_finds_dangling_link_status_anchor,
    test_real_readme_finds_equipment_escape,
    test_real_readme_finds_assets_row_mismatch,
    test_real_readme_has_exactly_these_three_findings_and_no_others,
    test_unicode_headings_slug_correctly_not_stripped_to_empty_or_ascii,
    test_real_spanish_translation_finds_only_the_same_two_real_bugs,
    test_real_chinese_translation_finds_only_the_same_two_real_bugs,
    test_github_slug_matches_every_real_heading_in_the_fixture,
    test_anchor_matching_a_real_heading_is_not_flagged,
    test_leading_dot_slash_is_normalized_not_treated_as_a_mismatch,
    test_clean_row_with_external_demo_link_is_not_flagged,
    test_a_genuinely_inconsistent_row_is_caught,
    test_relative_link_to_a_real_path_is_not_flagged,
    test_relative_link_to_a_missing_path_is_flagged,
    test_relative_link_escaping_repo_root_is_flagged,
    test_external_and_anchor_links_are_never_treated_as_relative_links,
    test_report_is_ok_when_there_are_no_errors,
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
