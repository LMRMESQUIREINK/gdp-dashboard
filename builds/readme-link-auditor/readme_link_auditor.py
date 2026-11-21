"""Checks a README's internal link integrity -- three things no other tool
in this project's /builds/ checks (curriculum-link-auditor checks claims
ABOUT a repo made by an external list; skill_md_validator checks SKILL.md
frontmatter/references; neither resolves markdown anchor fragments, detects
a relative link escaping the repo root, or cross-checks that several links
in one table row name the same entity):

1. Every '#anchor' link resolves to a real heading in the same document,
   via GitHub's own heading-slug algorithm.
2. Every relative file/directory link resolves to a real path under the
   repo root, and never escapes that root via '../'.
3. Within one table row, several links that should all point at the same
   entity (an icon's src, a title link, a "Source" link) actually agree
   on which directory that is.

Built from a real, confirmed case in HeyPuter/everything's README: three
rows link "Try it" to '#link-status' -- a note the README's own top
comment promises exists, but no heading or anchor by that name exists
anywhere in the file -- and one row's title links to '../equipment/'
(outside the repo entirely) while its own "Source" link and icon both
point at the real 'src/assets/' directory one row over.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
_MD_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")
_HTML_HREF_RE = re.compile(r"""href=["']([^"']+)["']""")
_HTML_SRC_RE = re.compile(r"""src=["']([^"']+)["']""")
_TR_RE = re.compile(r"<tr\b.*?</tr>", re.IGNORECASE | re.DOTALL)


@dataclass
class Finding:
    level: str  # "error" | "warning"
    code: str
    message: str
    line: int | None = None


@dataclass
class AuditReport:
    findings: list[Finding] = field(default_factory=list)

    def error(self, code: str, message: str, line: int | None = None) -> None:
        self.findings.append(Finding("error", code, message, line))

    def warn(self, code: str, message: str, line: int | None = None) -> None:
        self.findings.append(Finding("warning", code, message, line))

    @property
    def ok(self) -> bool:
        return not any(f.level == "error" for f in self.findings)


def github_slug(heading: str) -> str:
    """Reproduces GitHub's heading-to-anchor-id algorithm closely enough for
    auditing purposes: strip inline markup/HTML, lowercase, drop characters
    that are neither alphanumeric nor space/underscore/hyphen, collapse
    whitespace to single hyphens.

    Deliberately Unicode-aware, not ASCII-only: an earlier draft filtered on
    the literal character class [a-z0-9 _-], which silently stripped every
    accented Latin letter ('Ofimática' -> 'ofimtica') and every CJK
    ideograph ('办公' -> '') -- found by running this tool against
    HeyPuter/everything's own real Spanish and Chinese README translations,
    where it manufactured a dozen false "dangling anchor" findings against
    headings that resolve perfectly well on GitHub itself. str.isalnum() is
    Unicode-aware (True for 'í' and '办'), which str.lower() already is too,
    so switching the filter to it fixes this generally, not just for these
    two languages.
    """
    text = re.sub(r"<[^>]+>", "", heading)
    text = re.sub(r"[`*_]", "", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = text.strip().lower()
    text = "".join(ch for ch in text if ch.isalnum() or ch in " _-")
    text = re.sub(r"\s+", "-", text.strip())
    return text


def extract_headings(text: str) -> list[str]:
    return [m.group(2) for m in _HEADING_RE.finditer(text)]


def _line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def _all_links(text: str) -> list[tuple[str, int]]:
    out = []
    for m in _MD_LINK_RE.finditer(text):
        out.append((m.group(2), _line_of(text, m.start())))
    for m in _HTML_HREF_RE.finditer(text):
        out.append((m.group(1), _line_of(text, m.start())))
    return out


def check_anchor_links(text: str) -> list[Finding]:
    headings = extract_headings(text)
    valid_slugs = {github_slug(h) for h in headings}
    findings: list[Finding] = []
    seen: set[str] = set()
    for url, line in _all_links(text):
        if not url.startswith("#"):
            continue
        anchor = url[1:]
        if anchor in valid_slugs:
            continue
        key = f"{anchor}"
        if key in seen:
            continue
        seen.add(key)
        findings.append(
            Finding(
                "error",
                "dangling-anchor",
                f"link targets '#{anchor}', which matches no heading in this document "
                f"(known headings produce: {sorted(valid_slugs)})",
                line,
            )
        )
    return findings


def _is_external_or_special(url: str) -> bool:
    return url.startswith(("http://", "https://", "#", "mailto:", "tel:"))


def check_relative_links(text: str, repo_root: Path, doc_dir: Path | None = None) -> list[Finding]:
    """Resolves every relative link against repo_root (a README lives at the
    repo root unless doc_dir says otherwise) and flags anything that doesn't
    exist on disk, or that climbs above repo_root via '../'.
    """
    doc_dir = doc_dir or repo_root
    repo_root = repo_root.resolve()
    findings: list[Finding] = []
    seen: set[str] = set()
    for url, line in _all_links(text):
        if _is_external_or_special(url):
            continue
        clean = url.split("#")[0].split("?")[0]
        if not clean:
            continue
        key = clean
        if key in seen:
            continue
        seen.add(key)

        candidate = (doc_dir / clean).resolve()
        try:
            candidate.relative_to(repo_root)
            escapes = False
        except ValueError:
            escapes = True

        if escapes:
            findings.append(
                Finding(
                    "error",
                    "escapes-repo-root",
                    f"link '{clean}' resolves outside the repository root ({candidate}) "
                    f"instead of a path inside it",
                    line,
                )
            )
        elif not candidate.exists():
            findings.append(
                Finding(
                    "error",
                    "broken-relative-link",
                    f"link '{clean}' does not resolve to any real file or directory",
                    line,
                )
            )
    return findings


def extract_table_rows(text: str) -> list[tuple[str, int]]:
    return [(m.group(0), _line_of(text, m.start())) for m in _TR_RE.finditer(text)]


def _entity_name(path: str) -> str | None:
    """Reduces a relative link/src to the 'thing it names': strip any
    leading '../' climbs and a leading 'src/' convention prefix, then take
    the first remaining path segment. 'src/assets/icon-128.png',
    'src/assets/' and '../assets/' all reduce to 'assets'; '../equipment/'
    reduces to 'equipment' -- a different entity from either of those.
    """
    p = path
    while p.startswith("./"):
        p = p[2:]
    while p.startswith("../"):
        p = p[3:]
    if p.startswith("src/"):
        p = p[4:]
    p = p.strip("/")
    if not p:
        return None
    return p.split("/")[0].lower()


def _row_entities(row_html: str) -> set[str]:
    entities: set[str] = set()
    for href_or_src in _HTML_HREF_RE.findall(row_html) + _HTML_SRC_RE.findall(row_html):
        clean = href_or_src.split("#")[0].split("?")[0]
        if _is_external_or_special(href_or_src) or not clean:
            continue
        name = _entity_name(clean)
        if name:
            entities.add(name)
    return entities


def check_row_consistency(text: str) -> list[Finding]:
    """Within one <tr>...</tr>, an icon's src=, a title's href=, and a
    "Source" href= each ought to name the SAME entity (the same app
    directory, by whatever relative path gets there). More than one
    distinct entity named by one row's own links is a real inconsistency,
    not three independent facts -- it means the row's title doesn't point
    at the thing its own icon and "Source" link do.
    """
    findings: list[Finding] = []
    for row_html, line in extract_table_rows(text):
        if "<th" in row_html.lower():
            continue  # header row, not a data row
        entities = _row_entities(row_html)
        if len(entities) > 1:
            findings.append(
                Finding(
                    "error",
                    "row-target-mismatch",
                    f"this table row's own links disagree on which entity they point at: "
                    f"{sorted(entities)}",
                    line,
                )
            )
    return findings


def audit_readme(readme_path: str | Path, repo_root: str | Path | None = None) -> AuditReport:
    readme_path = Path(readme_path)
    text = readme_path.read_text(encoding="utf-8")
    root = Path(repo_root) if repo_root is not None else readme_path.parent

    report = AuditReport()
    report.findings.extend(check_anchor_links(text))
    report.findings.extend(check_relative_links(text, root, doc_dir=readme_path.parent))
    report.findings.extend(check_row_consistency(text))
    return report


def format_report(report: AuditReport) -> str:
    if not report.findings:
        return "No findings -- every anchor resolves, every relative link resolves inside the repo, every row is internally consistent."
    lines = []
    for f in sorted(report.findings, key=lambda f: (f.line or 0, f.code)):
        loc = f"line {f.line}" if f.line else "?"
        lines.append(f"[{f.level.upper()}] {f.code} ({loc}): {f.message}")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("usage: python3 readme_link_auditor.py <README path> [repo root]")
        raise SystemExit(2)
    readme = sys.argv[1]
    root = sys.argv[2] if len(sys.argv) > 2 else None
    result = audit_readme(readme, root)
    print(format_report(result))
    raise SystemExit(0 if result.ok else 1)
