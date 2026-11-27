"""drift_check -- re-greps a directory's real import graph and diffs it
against an okf_knowledge/ bundle's own claimed "## Consumers" sections,
reporting exactly the kind of drift test_staleness_value.py proved this
mechanism is actually worth catching, as a real, reusable tool instead
of a one-off comparison script.

Also catches the exact phantom-edge bug class found and fixed in
/builds/interface-lift-toolkit/'s bundle (a negated-reference sentence
written as a markdown link manufactures a graph edge to a module that
was never really imported) -- the EXTRA_UNDOCUMENTED side of a diff
(real but undocumented) and the STALE_CLAIM side (documented but not
real) are reported separately, since they're different failure classes
with different fixes: the first means the docs need a new line, the
second means either the code changed or the doc's own wording created
a phantom edge.

Usage:
    python3 drift_check.py <source_dir> <okf_bundle_dir>
    python3 drift_check.py <source_dir> <okf_bundle_dir> --json
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

from okf_navigator import load_bundle, resolve_link

_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")
# A BARE filename only -- no "/" allowed. A path-qualified backtick span
# (e.g. `/builds/okf-navigator/drift_check.py`, `policy/__init__.py`) is
# almost always an attribution or a negated-reference note in this
# project's prose, never the plain "`other_module.py`" shape every real
# non-modeled-consumer mention in these bundles actually uses.
_CODE_SPAN_PY_RE = re.compile(r"`([\w-]+)\.py`")
_HEADING_RE = re.compile(r"^#{1,6}\s", re.MULTILINE)
_TEST_FILE_RE = re.compile(r"^test_.*|.*_test$")


_BULLET_LINE_RE = re.compile(r"^\s*[-*]\s+(.*)$", re.MULTILINE)


def _consumers_section(body: str) -> str:
    """Only the BULLET-LIST lines under the '## Consumers' heading, up
    to the next heading -- not every sentence in that section. Two
    real bugs found while building this tool, both the same root cause
    (treating arbitrary prose as if it were a structured consumer
    entry): a concept's description can legitimately mention a module
    it DEPENDS on in running prose outside this section entirely (the
    first bug, fixed by scoping to the section at all); and a trailing
    explanatory paragraph INSIDE this section -- "X is NOT a consumer,
    because it actually touches Y/Z instead" or "a correction: this
    file used to wrongly claim W" -- can mention several other real
    module names without any of them being a consumer claim about THIS
    concept (the second bug). Restricting to bullet lines only is what
    actually fixes the second one: every real consumer entry in every
    bundle in this project is written as one bullet per consumer, by
    convention, and no explanatory paragraph in any of them is."""
    marker = re.search(r"^##\s*Consumers\b.*$", body, re.MULTILINE)
    if marker is None:
        return ""
    section = body[marker.end():]
    next_heading = _HEADING_RE.search(section)
    if next_heading:
        section = section[: next_heading.start()]
    return "\n".join(_BULLET_LINE_RE.findall(section))


def _consumers_section_links(body: str) -> list[str]:
    """Markdown links inside the '## Consumers' section only -- real
    consumer claims about a module that IS modeled as its own concept
    elsewhere in the bundle."""
    return [target for _text, target in _LINK_RE.findall(_consumers_section(body))]


def _consumers_section_code_spans(body: str) -> list[str]:
    """Bare, backtick-quoted `module.py` filenames inside the
    '## Consumers' section -- the documented way every bundle in this
    project names a real consumer that ISN'T modeled as its own
    concept (a top-level entry script like run_strategy.py/
    live_monitor.py), specifically to avoid the markdown-link phantom-
    edge bug: a plain code span is never treated as a navigable graph
    edge by okf_navigator.py, only as documentation text this checker
    can still read. Test-file names are excluded even in this bare
    form -- every bundle's own prose that mentions e.g. "only
    `test_policy.py` imports it" is explaining why something ISN'T a
    real, countable consumer claim, not making one."""
    return [m for m in _CODE_SPAN_PY_RE.findall(_consumers_section(body)) if not _TEST_FILE_RE.match(m)]


def _real_import_targets(py_file: Path) -> set[str]:
    """Every module stem this one real .py file actually imports,
    parsed with ast (not a regex), restricted to plain `import X` /
    `from X import ...` -- the same two forms every OKF bundle in this
    project documents consumer edges from."""
    targets: set[str] = set()
    try:
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
    except (SyntaxError, UnicodeDecodeError):
        return targets
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            targets.add(node.module.split(".")[-1])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                targets.add(alias.name.split(".")[-1])
    return targets


def _module_stem_for_concept(concept, concept_path: str) -> str:
    """The real .py module stem a concept documents: its own `title`
    frontmatter field when present (every bundle in this project sets
    this to the real relative path, e.g. 'policy/evaluator.py', so
    Path(title).stem gives the real 'evaluator' -- never derived from
    the bundle's own flat filename, which can carry a directory-prefix
    slug like 'policy-evaluator.md' that doesn't match the real
    filename at all). Falls back to the bundle filename's own slug only
    for a concept with no title set."""
    title = concept.frontmatter.get("title") if concept else None
    if title:
        return Path(title).stem
    return Path(concept_path).stem.replace("-", "_")


@dataclass
class ModuleDrift:
    concept_path: str
    module_stem: str
    documented_consumers: set[str] = field(default_factory=set)
    real_consumers: set[str] = field(default_factory=set)

    @property
    def undocumented(self) -> set[str]:
        """Real, grepped consumers this concept's '## Consumers' section
        never mentions -- the exact risk test_staleness_value.py proved
        stale_after exists to bound."""
        return self.real_consumers - self.documented_consumers

    @property
    def stale_claims(self) -> set[str]:
        """Documented consumers that no longer import this module at
        all -- either the code changed, or (per interface-lift-toolkit's
        own found bug) the doc's own prose manufactured a phantom edge
        that was never a real import in the first place."""
        return self.documented_consumers - self.real_consumers

    @property
    def has_drift(self) -> bool:
        return bool(self.undocumented or self.stale_claims)


def check_drift(source_dir: Path, bundle_dir: Path) -> list[ModuleDrift]:
    """For every concept in bundle_dir whose title names a real .py
    file actually present under source_dir, compare its documented
    '## Consumers' links against a fresh AST-based re-grep of
    source_dir. Concepts with no matching real file (this build's own
    convention of excluding test files from the bundle, same as every
    OKF bundle in this project) are silently skipped -- not an error,
    since the spec itself says a bundle need not cover every file."""
    bundle = load_bundle(bundle_dir)
    all_py_files = {p.stem: p for p in source_dir.rglob("*.py")}
    # Test files are the ONE real, explicitly-stated exclusion every
    # OKF bundle in this project names in its own concept files ("test
    # files aren't modeled as concepts in this bundle") -- a real
    # import FROM a test file was never meant to be a consumer claim
    # any bundle here makes. Everything else that really imports a
    # documented module counts, whether or not THAT importer is itself
    # modeled as a concept: an earlier draft of this function also
    # excluded any non-modeled importer (e.g. a real top-level entry
    # script that was never turned into its own concept), which looked
    # like it was suppressing noise but was actually hiding genuine
    # findings -- confirmed directly against trading-jarvis's real
    # risk_manager.py/data_pipeline.py/signal_generator.py, each really
    # imported by run_strategy.py and live_monitor.py (neither modeled)
    # in addition to the one caller their own "## Consumers" sections
    # name as exclusive.
    py_files_by_stem = {
        stem: path for stem, path in all_py_files.items()
        if not _TEST_FILE_RE.match(stem)
    }
    concept_stems = {
        concept_path: _module_stem_for_concept(concept, concept_path)
        for concept_path, concept in bundle.items()
    }
    modeled_stems = set(concept_stems.values())

    # Build the real import graph: every non-test .py file's real
    # imports of a MODELED module (there's nothing to compare an import
    # of an unmodeled module against, since no concept speaks for it).
    real_graph: dict[str, set[str]] = {stem: set() for stem in modeled_stems}
    for stem, py_file in py_files_by_stem.items():
        for target in _real_import_targets(py_file):
            if target in real_graph and target != stem:
                real_graph[target].add(stem)

    results: list[ModuleDrift] = []
    for concept_path, concept in sorted(bundle.items()):
        module_stem = concept_stems[concept_path]
        if module_stem not in py_files_by_stem:
            continue  # this concept doesn't name a real file under source_dir

        documented = set(_consumers_section_code_spans(concept.body))
        for raw_target in _consumers_section_links(concept.body):
            resolved = resolve_link(concept_path, raw_target)
            if resolved is None or resolved not in bundle:
                continue
            documented.add(_module_stem_for_concept(bundle[resolved], resolved))

        drift = ModuleDrift(
            concept_path=concept_path,
            module_stem=module_stem,
            documented_consumers=documented,
            real_consumers=real_graph.get(module_stem, set()),
        )
        results.append(drift)
    return results


def render(results: list[ModuleDrift]) -> str:
    lines: list[str] = []
    any_drift = False
    for d in results:
        if not d.has_drift:
            continue
        any_drift = True
        lines.append(f"{d.concept_path} ({d.module_stem}.py):")
        for stem in sorted(d.undocumented):
            lines.append(f"  UNDOCUMENTED: {stem}.py really imports this, but it's not in '## Consumers'")
        for stem in sorted(d.stale_claims):
            lines.append(f"  STALE_CLAIM: '## Consumers' names {stem}.py, but it no longer (or never) really imports this")
    if not any_drift:
        return f"No drift found across {len(results)} checked module(s)."
    return "\n".join(lines)


def main() -> None:
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("bundle_dir", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    results = check_drift(args.source_dir, args.bundle_dir)
    if args.json:
        print(json.dumps([
            {
                "concept": d.concept_path, "module": d.module_stem,
                "undocumented": sorted(d.undocumented), "stale_claims": sorted(d.stale_claims),
            }
            for d in results
        ], indent=2))
    else:
        print(render(results))

    if any(d.has_drift for d in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
