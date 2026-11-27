# Deep analysis: `HeyPuter/everything`

Source: a bare GitHub repo link, no accompanying text (the user's paste,
`https://github/HeyPuter/everything`, was missing `.com` — corrected as
the obvious intent rather than asking, per this project's own rule for
trivial ambiguity). Per this project's established convention, the bare
link is itself the instruction to run the deep-analysis-and-ship loop.
Measured via `git clone --depth 1`/`find`/`wc` before reading anything
for meaning.

## What it is

"The Everything Project," by the makers of Puter (`HeyPuter/puter` — a
real, independently confirmed project: 44.2k GitHub stars, AGPL-3.0,
7,588 commits, "The Internet Computer! Free, Open-Source, and
Self-Hostable"). This sibling mono-repo collects 51 independent app
directories, each rebuilding a category of proprietary software as a
free, MIT-licensed, open-source alternative: Office (Spreadsheet,
Documents, Presentation, Whiteboard, PDF, Notes, Records), Collaboration
(Meetings, Teamchat, Email, Contacts, Calendar, Signatures), Creative
Tools (Photo/Video/Vector/Audio/Music Studio, 3D Studio), Engineering
(CAD, Parametric, Circuits, Building Design), Productivity, Finance,
Business (CRM, Help Desk, Contracts, POS, Inventory, Hiring, Fleet,
Legal, Childcare, Field Service, Property Management), Developer Tools
(API Client), and Games (Chess, Backgammon, Checkers, Solitaire, Sudoku).

Checked whether this is real engineering or a thin wrapper before
anything else: `documents/` alone is 266,752 lines of real JS/TS,
`presentation/` 350,548, `spreadsheet/` 98,512 — not stub scaffolding.
`documents/` ships a genuine ECMA-376 OOXML conformance checker
(`tools/check-docx-schema.py`): downloads the official, hash-pinned
ECMA-376 Part 4 XSD archive to the OS temp directory (never ships schema
files in the app itself), validates document/style/settings/numbering/
theme XML against it with `lxml`, and the app carries 2,258 real `.docx`
test fixtures (`rotated-images.docx`, `chart-text-inherited.docx`,
`geometry-guide-rebinding.docx`, etc.) plus 10,603 files under `tests/`.
A real dependency list (`@zip.js/zip.js`, `yjs` for collaborative
editing, `opentype.js`, `rtf.js`) consistent with building a real word
processor from primitives, not wrapping an existing one.

Checked one specific, project-wide pattern this project has repeatedly
found elsewhere ("a script references a tool file that was never
supplied"): 12 of the 51 apps' `package.json` run `check:licenses` as a
`prebuild` step, pointing at `tools/check-licenses.mjs`. All 12 actually
have the real file. This specific gap, seen in nearly every prior round
of this project (Trading Jarvis, Kryptera, the prop-firm builds), does
**not** recur here — a genuine clean result, not an unchecked assumption.

## The real finding: two bugs in the README, identical across all three languages

The repo ships `README.md`, `README.es.md`, and `README.zh-CN.md` — three
language variants of the same ~45-row table of apps, each row carrying an
icon `<img src>`, a title `<a href>`, a "Try it" demo link, and a
"Source" link.

**Bug 1 — a promised note that doesn't exist.** The README's own
top-of-file HTML comment states: *"missing destinations point to the
link-status note."* Three rows (Expenses, Assets, Property Management)
link their "Try it" button to `#link-status` — but no heading, anchor,
or section named `link-status` exists anywhere in the document. Clicking
through on any of the three goes nowhere.

**Bug 2 — a row whose own links disagree.** The "Assets" row's icon
(`src/assets/icon-128.png`) and its "Source" link (`src/assets/`) both
correctly point at the real `src/assets/` directory. But the row's own
**title** link points to `../equipment/` — a path that doesn't exist in
the repo at all, and which (read literally, as a relative link from the
README's own location) climbs *outside* the repository root entirely.
Every other row in all three tables is internally consistent (icon,
title, and Source link all name the same app); this is the one
exception, and it's the same exception in English, Spanish, and Chinese —
strong evidence the bug lives in whatever generated/copied these rows
originally, not in any one translator's pass.

## Built

Checked `/builds/` first: `curriculum-link-auditor` checks claims an
*external* list makes about a repo against that repo's real README —
different shape of problem. `skill_md_validator.py` checks SKILL.md
frontmatter and body references — a different document type, with no
anchor-fragment resolution or relative-link-escape detection at all.
Neither checks what this source's bugs actually are.

**`/builds/readme-link-auditor/`** — a new, standalone, dependency-free
Python tool: resolves every `#anchor` link against a Unicode-aware
reproduction of GitHub's own heading-slug algorithm, resolves every
relative link against the real repo tree (flagging both "doesn't exist"
and "climbs outside the repo root" as distinct, named failure modes), and
cross-checks that several links inside one HTML table row agree on which
entity they name. Proven against the real, unmodified README files from
all three languages (committed as fixtures, with a lightweight skeleton
of the real 51-directory tree so relative-link resolution runs for real
without committing all 37,642 actual files) — found exactly the two real
bugs above and nothing else, confirmed identically against the complete,
uncommitted 37,642-file clone directly as a second check.

**A real bug found and fixed in this build's own first draft, not the
source — caught by testing against the real Spanish/Chinese files, not
assumed safe from the English case alone.** The first version of the
anchor-slug function filtered on a literal ASCII character class,
`[^a-z0-9 _-]`, which silently stripped every accented Latin letter
(`Ofimática` → `ofimtica`) and every CJK ideograph (`办公` → `''`) —
manufacturing a dozen false "dangling anchor" findings against headings
that resolve perfectly well on GitHub itself. Isolated before reporting
anything: GitHub's real slugger preserves Unicode letters, confirmed
directly (`'í'.isalnum()` and `'办'.isalnum()` are both `True` in
Python, and `.lower()` is a safe no-op on CJK). Fixed by switching the
filter to Unicode-aware `str.isalnum()`, a general fix rather than a
per-language patch. After the fix, all three language files converge on
exactly the same two real findings.

A second, smaller real bug surfaced the same way: the Tasks and Time
Tracking rows use `./src/tasks/icon-128.png` (a leading `./`) for their
icon, while every other row (and these same rows' own title/Source
links) use the bare `src/tasks/` form — functionally identical paths
that the first draft's manual prefix-stripping treated as naming
different entities. Fixed by normalizing a leading `./` before comparing.

17/17 tests pass, including the real multi-language fixtures, a planted
discrimination case proving the row-consistency check still fires on a
genuinely broken row, and regression tests locking in both fixes.

## Deliberately not built

A fix or PR against the real repo — read-only clone access only, no
push/fork capability, same limit as every other external-repo build in
this project. Live reachability checks of the `*.puter.com` demo
URLs — confirmed directly that this sandbox's egress proxy returns a DNS
failure for every `puter.com` subdomain, the same restriction class
already documented for EODHD/FMP/Hugging Face/arXiv/agentskills.io/
dev.to, now extended to `puter.com`. The `#link-status` finding is
therefore about the README's own internal consistency, not about
whether the destination it was meant to point to would have worked.
