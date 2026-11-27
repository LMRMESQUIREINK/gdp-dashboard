import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from skill_md_validator import (
    validate_skill_dir,
    validate_skills_root,
    validate_pack,
    check_pack_description_budget,
    check_description_overlap,
    _collect_descriptions,
)

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "tests" / "fixtures"
DUP_ROOT = HERE / "tests" / "fixtures-dup-root"
REPO_ROOT = HERE.parent.parent  # builds/skill-md-validator -> builds -> repo root


def codes(report):
    return {f.code for f in report.findings}


class TestGoodSkillPasses(unittest.TestCase):
    def test_well_formed_skill_has_no_findings(self):
        report = validate_skill_dir(FIXTURES / "good-skill")
        self.assertTrue(report.ok)
        self.assertEqual(report.findings, [])


class TestNameChecks(unittest.TestCase):
    def test_name_directory_mismatch_is_an_error(self):
        report = validate_skill_dir(FIXTURES / "bad-name-mismatch")
        self.assertFalse(report.ok)
        self.assertIn("name-directory-mismatch", codes(report))

    def test_bad_name_format_is_an_error(self):
        report = validate_skill_dir(FIXTURES / "bad-name-format")
        self.assertFalse(report.ok)
        self.assertIn("bad-name-format", codes(report))


class TestDescriptionChecks(unittest.TestCase):
    def test_missing_description_is_an_error(self):
        report = validate_skill_dir(FIXTURES / "missing-description")
        self.assertFalse(report.ok)
        self.assertIn("missing-description", codes(report))

    def test_too_short_description_is_an_error(self):
        report = validate_skill_dir(FIXTURES / "short-description")
        self.assertFalse(report.ok)
        self.assertIn("description-too-short", codes(report))

    def test_missing_trigger_phrase_is_a_warning_not_an_error(self):
        report = validate_skill_dir(FIXTURES / "no-trigger-phrase")
        self.assertTrue(report.ok, "a missing trigger phrase must be advisory, not blocking")
        self.assertIn("no-trigger-condition", codes(report))

    def test_use_while_phrasing_is_recognized_as_a_trigger_condition(self):
        # Regression test for a real false positive this build's own
        # first draft produced against this repo's real
        # .claude/skills/code-structure and review-loop: both state a
        # clear usage condition ("Use while implementing...", "Before
        # calling a build finished, run it through...") that the
        # original TRIGGER_WORDS list didn't recognize. Confirmed by
        # reading the real files before fixing the heuristic.
        report = validate_skill_dir(REPO_ROOT / ".claude" / "skills" / "code-structure")
        self.assertNotIn("no-trigger-condition", codes(report))
        report2 = validate_skill_dir(REPO_ROOT / ".claude" / "skills" / "review-loop")
        self.assertNotIn("no-trigger-condition", codes(report2))

    def test_use_to_phrasing_is_recognized_as_a_trigger_condition(self):
        # A second real false positive, found the same way: vendoring
        # pbakaus/impeccable's real Claude-Code-targeted SKILL.md
        # (.claude/skills/impeccable, not the repo's own .agent/
        # variant -- the two have genuinely different description text,
        # confirmed by diffing both rather than assumed identical from a
        # same-filename listing) flagged no-trigger-condition against its
        # real description, "Use to design, redesign, critique, audit,
        # polish or animate a frontend..." -- a real, clearly-stated
        # usage condition the original list didn't recognize because it
        # only had "use for", not "use to".
        report3 = validate_skill_dir(REPO_ROOT / ".claude" / "skills" / "impeccable")
        self.assertNotIn("no-trigger-condition", codes(report3))


class TestBodyChecks(unittest.TestCase):
    def test_empty_body_is_an_error(self):
        report = validate_skill_dir(FIXTURES / "empty-body")
        self.assertFalse(report.ok)
        self.assertIn("empty-body", codes(report))

    def test_thin_body_is_a_warning_not_an_error(self):
        report = validate_skill_dir(FIXTURES / "thin-body")
        self.assertTrue(report.ok)
        self.assertIn("thin-body", codes(report))


class TestFrontmatterParsing(unittest.TestCase):
    def test_unparseable_frontmatter_is_an_error(self):
        report = validate_skill_dir(FIXTURES / "unparseable-frontmatter")
        self.assertFalse(report.ok)
        self.assertIn("unparseable-frontmatter", codes(report))

    def test_missing_skill_md_is_an_error(self):
        report = validate_skill_dir(FIXTURES / "no-skill-md")
        self.assertFalse(report.ok)
        self.assertIn("missing-skill-md", codes(report))

    def test_yaml_block_scalar_description_parses_correctly(self):
        # Regression test for a real bug: Cedriccmh/claude-code-skill-scrapling's
        # real SKILL.md uses `description: |` with the value on following,
        # more-indented lines. The original parser raised
        # "unparseable frontmatter line (no ':')" on the first continuation
        # line, since it treated every frontmatter line as a standalone
        # key:value pair regardless of indentation.
        report = validate_skill_dir(FIXTURES / "block-scalar-description")
        self.assertNotIn("unparseable-frontmatter", codes(report))
        self.assertTrue(report.ok, report.findings)

    def test_nested_map_with_a_repeated_leaf_key_is_not_a_duplicate(self):
        # Regression test for a real bug: D4Vinci/Scrapling's own official
        # Scrapling-Skill SKILL.md has `metadata.homepage` and
        # `metadata.openclaw.homepage` -- the same leaf key name at two
        # different YAML nesting depths, which is valid YAML, not a
        # duplicate top-level key. The original flat line-by-line parser
        # didn't track indentation at all, so it raised
        # "duplicate frontmatter key: 'homepage'" on real, legal input.
        report = validate_skill_dir(FIXTURES / "nested-map-metadata")
        self.assertNotIn("unparseable-frontmatter", codes(report))
        self.assertTrue(report.ok, report.findings)


class TestReferenceResolution(unittest.TestCase):
    def test_broken_same_folder_reference_is_an_error(self):
        report = validate_skill_dir(FIXTURES / "broken-reference")
        self.assertFalse(report.ok)
        self.assertIn("broken-reference", codes(report))

    def test_good_skills_same_folder_reference_resolves(self):
        report = validate_skill_dir(FIXTURES / "good-skill")
        self.assertNotIn("broken-reference", codes(report))

    def test_repo_root_relative_references_resolve_with_repo_root_given(self):
        # Regression test for the real bug found running this validator
        # against this repo's own real skills: without repo_root, every
        # skill using a repo-root-relative reference (a leading '/', or
        # a bare '.claude/skills/other-skill') was false-flagged as
        # broken, 16 false positives across 7 real, correct skills on
        # the very first run.
        report_without_root = validate_skill_dir(REPO_ROOT / ".claude" / "skills" / "humanizer")
        self.assertIn("broken-reference", codes(report_without_root), "sanity check: without repo_root this must still reproduce the original false positive")

        report_with_root = validate_skill_dir(REPO_ROOT / ".claude" / "skills" / "humanizer", repo_root=REPO_ROOT)
        self.assertNotIn("broken-reference", codes(report_with_root))

    def test_genuinely_broken_reference_still_caught_even_with_repo_root(self):
        # A reference that resolves under neither the skill's own
        # directory NOR the repo root must still fail -- repo_root
        # should widen what counts as valid, never silence a real gap.
        report = validate_skill_dir(FIXTURES / "broken-reference", repo_root=REPO_ROOT)
        self.assertIn("broken-reference", codes(report))

    def test_a_quoted_runtime_path_fragment_with_no_extension_is_not_flagged(self):
        # Regression test for a real false positive: cyberchitta/scrapling-fetch-mcp's
        # real SKILL.md quotes `bin/python3` in prose -- a fragment of a
        # longer, dynamically-built runtime executable path
        # ("$(uv tool dir)/scrapling-fetch-mcp/bin/python3"), named only so
        # a reader recognizes an error message, never a "see this file"
        # pointer. The original "any path with one slash" fallback in
        # _extract_references flagged it as broken.
        from skill_md_validator import _extract_references
        body = (
            "If the command fails with `No such file or directory` for the "
            "`bin/python3` path, see `references/install.md`."
        )
        refs = [path for path, _preceding in _extract_references(body)]
        self.assertNotIn("bin/python3", refs)
        self.assertIn("references/install.md", refs)

    def test_a_gitignored_local_overlay_reference_is_a_warning_not_an_error(self):
        # Regression test for a real false positive: claude-code-skill-scrapling's
        # SKILL.md references references/cookie-vault.local.md, which its
        # own .gitignore excludes on purpose so real credentials are never
        # committed -- a known-absent-by-design file, not a broken one.
        report = validate_skill_dir(FIXTURES / "gitignored-reference")
        self.assertNotIn("broken-reference", codes(report))
        self.assertIn("gitignored-reference", codes(report))
        self.assertTrue(report.ok, "a gitignored reference must warn, never fail the skill")

    def test_a_negated_existence_statement_is_a_warning_not_an_error(self):
        # Regression test for a real false positive found against NVIDIA's
        # real, unmodified nvidia-ontology-setup SKILL.md: "The app factory
        # is create_app() in auto_ontology/server/__main__.py. There is no
        # auto_ontology/server/main.py." -- a deliberate statement that the
        # path does NOT exist, not a dangling "see this file" pointer.
        # (The fixture is only the skill's own subdirectory, not the full
        # repo, so its two OTHER real-path references genuinely can't
        # resolve here and correctly still error -- this test checks only
        # that 'main.py' specifically is downgraded, not that the whole
        # skill passes clean.)
        report = validate_skill_dir(FIXTURES / "nvidia-skills" / "nvidia-ontology-setup")
        main_py_findings = [f for f in report.findings if "server/main.py" in f.message]
        self.assertTrue(main_py_findings, "expected a finding mentioning auto_ontology/server/main.py")
        self.assertEqual({f.code for f in main_py_findings}, {"negated-reference"})


class TestDuplicateNameDetection(unittest.TestCase):
    def test_sibling_skills_sharing_a_name_are_both_flagged(self):
        reports = validate_skills_root(DUP_ROOT)
        self.assertEqual(len(reports), 2)
        for report in reports:
            self.assertFalse(report.ok)
            self.assertIn("duplicate-skill-name", codes(report))

    def test_distinct_names_across_siblings_are_not_flagged(self):
        reports = validate_skills_root(FIXTURES, repo_root=REPO_ROOT)
        for report in reports:
            self.assertNotIn("duplicate-skill-name", codes(report))


class TestAgainstThisRepositorysRealSkills(unittest.TestCase):
    """The actual deliverable this round: run the validator for real
    against this project's own real skills, the same "test against our
    own real material" discipline as /builds/ten-k-website-grader/ and
    /builds/agent-readiness-scorecard/.

    The count below was corrected from a stale 11 to 12 (this project
    shipped `retro` after this test was first written), then to 15
    (three real external skills vendored in -- `impeccable`,
    `emil-design-eng`, `design-taste-frontend`; see ATTRIBUTION.md in
    each), then to 16 (`reference-builder`, vendored from the Motion
    Sites Method guide), then to the real, current 17
    (`agent-brief-grader`) -- found as a side effect of touching this
    test each of those rounds, not chased down separately."""

    def test_real_skills_directory_exists(self):
        skills_dir = REPO_ROOT / ".claude" / "skills"
        self.assertTrue(skills_dir.is_dir(), f"expected to find real skills at {skills_dir}")

    def test_all_real_skills_pass_except_two_deliberately_partial_vendor_copies(self):
        """Not "should all pass" any more, by design: `design-taste-frontend`
        and `emil-design-eng` are deliberately PARTIAL vendor copies (each
        skill's own ATTRIBUTION.md states exactly what was left out and
        why -- a 40MB asset/script library for the former, 18 sibling
        skills for the latter), and both cross-reference content that
        isn't vendored here, so this validator correctly flags those
        references as broken. Forcing a pass by editing the vendored
        files to hide the references, or by inventing fake local copies
        of what was deliberately excluded, would be worse than the
        honest fail -- same discipline as every other "a real, correct
        fail is not a bug to force-fix" case in this project."""
        skills_dir = REPO_ROOT / ".claude" / "skills"
        reports = validate_skills_root(skills_dir, repo_root=REPO_ROOT)
        self.assertEqual(len(reports), 17, "expected exactly the seventeen real skills this project has shipped")
        failing = {r.skill_dir.name: codes(r) for r in reports if not r.ok}
        self.assertEqual(set(failing), {"design-taste-frontend", "emil-design-eng"})
        # and only for the expected, documented reason -- nothing else
        for name, found_codes in failing.items():
            self.assertTrue(
                all(c in ("broken-reference", "description-over-recommended") for c in found_codes),
                f"{name} failed for an unexpected reason: {found_codes}",
            )
        for r in reports:
            if r.skill_dir.name not in failing:
                self.assertTrue(r.ok, f"{r.skill_dir.name} should pass cleanly: {codes(r)}")

    def test_five_real_skills_now_warn_over_the_real_500char_recommendation(self):
        """A real finding from an earlier round, extended by this one:
        reading coreyhaines31/marketingskills' own dated measurement
        (/notes/marketingskills-analysis.md) and checking it against
        this project's own skills found four whose descriptions
        genuinely exceed the 500-char recommendation --
        launch-kit-writer (721 chars), sales-page-engine (613),
        voice-extractor (576), launch-pad (519). Vendoring
        design-taste-frontend this round adds a fifth, its real,
        unedited description running 922 chars. (A first draft of this
        test only named three, having miscounted launch-pad's 519 as
        under the line when it isn't -- corrected to match a recount,
        not forced to match the original miscount.) Still a warning,
        not an error, for the four skills this project itself wrote --
        design-taste-frontend separately fails for its own, unrelated,
        documented reason (broken-reference), checked in the test above
        rather than conflated with this one."""
        skills_dir = REPO_ROOT / ".claude" / "skills"
        reports = validate_skills_root(skills_dir, repo_root=REPO_ROOT)
        over_recommended = {r.skill_dir.name for r in reports if "description-over-recommended" in codes(r)}
        self.assertEqual(
            over_recommended,
            {"launch-kit-writer", "sales-page-engine", "voice-extractor", "launch-pad", "design-taste-frontend"},
        )
        still_passing = over_recommended - {"design-taste-frontend"}
        for r in reports:
            if r.skill_dir.name in still_passing:
                self.assertTrue(r.ok, f"{r.skill_dir.name} should still pass -- this is a warning, not an error")


class TestPackDescriptionBudget(unittest.TestCase):
    def test_well_under_budget_produces_no_findings(self):
        descriptions = {Path("a"): "x" * 100, Path("b"): "y" * 100}
        self.assertEqual(check_pack_description_budget(descriptions), [])

    def test_crossing_the_warn_threshold_warns_not_errors(self):
        descriptions = {Path(f"skill-{i}"): "x" * 1000 for i in range(20)}  # 20,000 chars
        findings = check_pack_description_budget(descriptions, warn_at=19_000, cap_at=30_000)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].code, "pack-description-budget-warning")
        self.assertEqual(findings[0].severity, "warning")

    def test_crossing_the_hard_cap_still_only_warns_never_errors(self):
        """Deliberate design choice, stated in the function's own
        docstring: a pack over budget still works (some descriptions
        just show name-only), so this is never a hard error."""
        descriptions = {Path(f"skill-{i}"): "x" * 1000 for i in range(35)}  # 35,000 chars
        findings = check_pack_description_budget(descriptions, warn_at=19_000, cap_at=30_000)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].code, "pack-description-budget-exceeded")
        self.assertEqual(findings[0].severity, "warning")

    def test_real_run_against_this_repos_own_skills_is_nowhere_near_the_budget(self):
        """A real, honest 'no problem found' result, not a manufactured
        one: this project's own 17 skills (13 written here, plus 4
        vendored) total around 7.9k characters, far under even the warn
        threshold."""
        skills_dir = REPO_ROOT / ".claude" / "skills"
        descriptions = _collect_descriptions(skills_dir)
        self.assertEqual(len(descriptions), 17)
        total = sum(len(d) for d in descriptions.values())
        self.assertLess(total, 19_000)
        self.assertEqual(check_pack_description_budget(descriptions), [])


class TestDescriptionOverlap(unittest.TestCase):
    def test_discrimination_near_identical_descriptions_are_flagged(self):
        descriptions = {
            Path("skill-a"): "Use when the user wants to plan and run conversion rate experiments on pricing pages and landing pages for SaaS products.",
            Path("skill-b"): "Use when the user wants to plan and run conversion rate experiments on signup pages and landing pages for SaaS products.",
        }
        findings = check_description_overlap(descriptions, threshold=0.4)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].code, "description-overlap")

    def test_discrimination_genuinely_distinct_descriptions_are_not_flagged(self):
        descriptions = {
            Path("skill-a"): "Use when the user wants to plan and run conversion rate experiments on pricing pages.",
            Path("skill-b"): "Use when the user wants to write cold outbound emails for B2B sales prospecting campaigns.",
        }
        self.assertEqual(check_description_overlap(descriptions, threshold=0.4), [])

    def test_shared_boilerplate_trigger_phrasing_alone_does_not_count_as_overlap(self):
        """The stopword list exists specifically so two skills that both
        say 'use when the user wants to' don't get flagged just for
        sharing that boilerplate -- only real shared content words
        should count."""
        descriptions = {
            Path("skill-a"): "Use when the user wants to optimize App Store listings and keyword rankings.",
            Path("skill-b"): "Use when the user wants to write cold outbound sales emails for prospecting.",
        }
        self.assertEqual(check_description_overlap(descriptions, threshold=0.3), [])

    def test_each_pair_reported_at_most_once(self):
        descriptions = {
            Path("skill-a"): "pricing page conversion rate experiment landing page",
            Path("skill-b"): "pricing page conversion rate experiment landing page",
            Path("skill-c"): "cold email prospecting outbound sales",
        }
        findings = check_description_overlap(descriptions, threshold=0.4)
        self.assertEqual(len(findings), 1)

    def test_real_run_against_this_repos_own_skills_finds_no_overlap(self):
        """This project's 17 skills cover genuinely distinct domains
        (copy, SEO-adjacent pSEO, voice, launch, review process, agent-
        brief grading, plus four vendored design/animation/taste/
        reference skills) -- confirmed by actually running the check,
        not assumed."""
        skills_dir = REPO_ROOT / ".claude" / "skills"
        descriptions = _collect_descriptions(skills_dir)
        findings = check_description_overlap(descriptions, threshold=0.4)
        self.assertEqual(findings, [], f"unexpected overlap found: {findings}")


class TestValidatePack(unittest.TestCase):
    def test_returns_per_skill_reports_and_pack_findings_separately(self):
        skills_dir = REPO_ROOT / ".claude" / "skills"
        reports, pack_findings = validate_pack(skills_dir, repo_root=REPO_ROOT)
        self.assertEqual(len(reports), 17)
        self.assertEqual(pack_findings, [])  # real repo is well under budget, no overlap

    def test_cli_prints_a_pack_level_section_when_findings_exist(self):
        result = subprocess.run(
            [sys.executable, str(HERE / "skill_md_validator.py"), str(HERE / "tests" / "fixtures"), "--json"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 1)  # the fixtures dir has real per-skill errors
        payload = json.loads(result.stdout)
        self.assertIn("skills", payload)
        self.assertIn("pack_level", payload)


if __name__ == "__main__":
    unittest.main(verbosity=2)
