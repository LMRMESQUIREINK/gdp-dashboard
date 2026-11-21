# README Link Auditor

A standalone, dependency-free Python tool that checks a README's
**internal** link integrity — three things nothing else in this
project's `/builds/` checks:

1. Every `#anchor` link resolves to a real heading in the same document,
   via a Unicode-aware reproduction of GitHub's own heading-slug
   algorithm.
2. Every relative file/directory link resolves to a real path under the
   repo root, and never escapes that root via `../`.
3. Within one HTML table row, several links naming the same entity (an
   icon's `src`, a title's `href`, a "Source" link's `href`) actually
   agree on which directory that is.

`/builds/curriculum-link-auditor/` checks claims an external list makes
*about* a repo against that repo's real README. `/builds/
skill-md-validator/` checks SKILL.md frontmatter and body references.
Neither resolves a markdown/HTML anchor fragment, detects a relative link
climbing out of the repo, or cross-checks that several links in one row
name the same thing. This is a different, generalizable gap, checked
against `/builds/` before building it.

## Source

A bare GitHub repo link, no accompanying text —
`https://github.com/HeyPuter/everything` (the user's own paste had a typo,
`https://github/HeyPuter/everything`, missing `.com`; corrected as the
obvious intent and proceeded, per this project's own "make a reasonable
assumption, state it in one line" rule for trivial ambiguity). Per this
project's established convention, a bare link with no instruction is
itself the instruction to run the deep-analysis-and-ship loop.

## What HeyPuter/everything is

"The Everything Project": a mono-repo of real, substantial, independently
app directories (51 at the time of this clone) rebuilding office/creative/
engineering/business software as free MIT-licensed alternatives —
Spreadsheet, Documents, Presentation, CAD, Accounting, CRM, Chess, and
dozens more — built on top of Puter (`HeyPuter/puter`, a real, established
project: confirmed via GitHub, 44.2k stars, AGPL-3.0, 7,588 commits, "The
Internet Computer"). Not vaporware: `documents/` alone is 266,752 lines of
real JS/TS source, ships a real ECMA-376 OOXML schema validator
(hash-pinned XSD download, `lxml`-based conformance checking against the
official standard, not a hand-rolled approximation) and 2,258 real `.docx`
test fixtures. `check:licenses` package.json scripts across 12 apps were
checked against the actual presence of `tools/check-licenses.mjs` in each
— all 12 have the real file; this specific "referenced but never
supplied" pattern, seen repeatedly elsewhere in this project, does **not**
recur here.

## The real finding: two bugs in the README itself, reproduced identically across all three language translations

Measured, not assumed: the repo's top-level `README.md` (and its
`README.es.md`/`README.zh-CN.md` siblings) is a ~45-row set of HTML
tables, one row per app, each with an icon `<img src>`, a title `<a
href>`, a "Try it" demo link, and a "Source" link. Running this tool
against the real file found two genuine problems, both present
identically in English, Spanish, and Chinese:

1. **A dangling anchor.** The README's own top-of-file comment states:
   *"missing destinations point to the link-status note."* Three rows
   (Expenses, Assets, Property Management) link their "Try it" button to
   `#link-status` — but no heading or anchor named `link-status` exists
   anywhere in the document. The promised note was never written.
2. **A broken row.** The "Assets" row's icon (`src/assets/icon-128.png`)
   and its "Source" link (`src/assets/`) both correctly point at the real
   `src/assets/` directory — but the row's own **title** link points to
   `../equipment/`, a path that doesn't exist anywhere in the repo and,
   worse, resolves *outside* the repository root entirely. Every other
   row in the table is internally consistent (icon/title/Source all name
   the same app); this is the one exception.

Confirmed both bugs are structural, not an artifact of one translation:
running the tool against all three language files independently (English,
Spanish, Chinese) produces the exact same three findings in each — the
template these rows were generated/copied from carries both bugs into
every language copy.

## A real bug found and fixed in this build's own first draft, not in the source

The first version of `github_slug()` filtered headings through a literal
ASCII character class, `[^a-z0-9 _-]`. Running it against the real Spanish
and Chinese READMEs — not assumed to work from the English case alone —
produced a dozen false "dangling anchor" findings: `Ofimática` slugged to
`ofimtica` (silently dropping the accent), and `办公` slugged to `''`
(dropping every CJK character). Before reporting any of that as a problem
with the source, isolated it: GitHub's real slugger keeps Unicode letters
and only strips punctuation, so an accented or CJK heading resolves fine
on the actual live page. Confirmed directly with Python (`'í'.isalnum()`
and `'办'.isalnum()` are both `True`, and `str.lower()` is a correct no-op
on CJK). **Fixed** by switching the filter to `ch.isalnum() or ch in "
_-"`, which is Unicode-aware generally, not special-cased per language.
After the fix, all three language files converge on exactly the same two
real findings — zero false positives, where before there were a dozen.

## Tests

17/17 pass, including:

- The real, unmodified English/Spanish/Chinese `README.md` files from
  `HeyPuter/everything`, committed as fixtures
  (`tests/fixtures/everything/`) alongside a lightweight skeleton of the
  real repo tree (empty directories/files at every real path — all 51 app
  directories, each real `icon-128.png`, the hero assets — so relative-
  link resolution runs for real without committing all 37,642 real
  files).
- `test_real_readme_has_exactly_these_three_findings_and_no_others` — the
  discriminating claim: everything else in the real, ~45-row README
  resolves cleanly after both fixes. Confirmed identically against the
  full, unmodified 37,642-file clone directly (not just the lightweight
  fixture) before committing to this result.
- `test_leading_dot_slash_is_normalized_not_treated_as_a_mismatch` — a
  second, smaller real bug this project's own first pass caught: the
  Tasks/Time Tracking rows use `./src/tasks/icon-128.png` (a leading
  `./`) for the icon while the title/Source links use the bare
  `src/tasks/` form — functionally identical, but the first draft's
  manual path-prefix stripping didn't normalize `./`, so these two
  rows were wrongly flagged as inconsistent until fixed.
- `test_unicode_headings_slug_correctly_not_stripped_to_empty_or_ascii` +
  the two real-translation tests — lock in the Unicode slug fix as a
  permanent regression, not just a one-off patch.
- A planted discrimination case (`test_a_genuinely_inconsistent_row_is_
  caught`) proving the row-consistency check still fires on a genuinely
  broken row, and several clean-input tests (external demo links, a
  real matching anchor, a path that really exists) proving it doesn't
  rubber-stamp everything.

## Deliberately not built

A fix or PR against the real `HeyPuter/everything` repo — this session
has read-only access (anonymous clone), no push/fork capability, the same
limit as every other external-repo build in this project
(`github-repo-manager-safety-wrapper`, `scrapemaster4`). A full HTML
parser (this tool uses regex over the table/link markup, which is
sufficient for this README's actual structure and consistent with
`skill_md_validator.py`'s own approach elsewhere in this project) rather
than a general-purpose markdown+HTML AST — the regex approach is
sufficient for auditing a README's own internal links and was verified
against the real multi-language files rather than assumed sufficient.
Live reachability checks of the `*.puter.com` demo URLs — this sandbox's
egress proxy returns a DNS failure for every `puter.com` subdomain
(confirmed directly), the same restriction class documented repeatedly
elsewhere in this project, now extended to `puter.com`.
