# Deep analysis: a pasted Medium article on using REA for vibe coding

Source: "Forget Claude Code: Reverse Engineer Anything 10x Better (Full
Guide)" (GaoDalie_AI, Medium), pasted directly — `medium.com` is
unreachable from this sandbox (the same DNS-failure restriction class
already documented for dev.to/nocobase.com/arxiv.org/Hugging Face/
Substack throughout this project), so the text came in as a paste rather
than a fetch.

This is the **fourth** engagement this project has had with `morluto/rea`
("REA: Reverse Engineer Anything"), and the first from a third-party
reviewer's hands-on angle rather than a direct repo audit:

1. `/notes/rea-reverse-engineer-anything-analysis.md` + `/builds/go-buildinfo-extractor/` — the original deep dive, reading REA's own Go build-info extraction code.
2. `/builds/go-buildinfo-extractor` extended with a Rust `cargo-auditable` sibling extractor, built the same way.
3. `/notes/rea-gate-analysis.md` + `/builds/rea-gate/` — a `ruthless-gate` four-level verdict round, re-cloning and checking growth/licensing/star claims.
4. `/notes/oss-ai-engineering-stack-week25-analysis.md` — a light recheck (a newsletter survey mentioning REA again), explicitly declining a new build since two already exist.

This round is the fifth: a different author's "how I actually used this"
guide, with real hands-on CLI testing against the author's own small
Electron app, not a repo-code read.

## Measured and verified, not repeated as fact

**`rea-agents` is a real, currently-published npm package.** `npm view
rea-agents` confirms version `6.10.1`, 36 published versions, `bin: rea,
rea-agents` — matching the article's exact CLI binary names — pointing at
`github.com/morluto/rea`. A fresh clone of the real repo today confirms
the exact same version (`6.10.1`) in `package.json`, at commit `14b4d1f`
dated 2026-11-26 — the repo is still being actively, continuously shipped,
consistent with every prior round's finding.

**The article's exact CLI debugging story checks out against the real
docs.** The article reports that `rea setup --client claude-code`
(hyphenated) fails with "Unsupported agent integration," and that the
correct flag is `--client claude_code` (underscore). Grepping the real,
freshly-cloned repo's own documentation
(`docs/desktop-build-computer.md`) confirms `claude_code` (underscore) is
the real, currently-documented flag value used throughout REA's own docs
— the article's own troubleshooting anecdote is accurate, not invented.
`rea doctor` is likewise real and documented.

**The DX-Ball claim checks out exactly, down to the byte.** The article
states: "REA was used to reconstruct the game's sound-positioning
calculation function in C. After compilation, the resulting 63 bytes of
machine code matched the original exactly." The real repo's own
`website/evidence/dx-ball-sound-pan.md` states: "Function: `0x406400`
through `0x40643e`, inclusive, 63 bytes" — `0x40643e - 0x406400 + 1 =
63` exactly, matching the article's number precisely. One precision note
worth recording: this evidence is pinned to an older recorded analysis
(REA 4.1.0, a 7 October 2026 checkpoint) rather than the current 6.10.1
— the article doesn't specify a version, so there's no conflict, but the
example itself is a fixed, dated artifact, not something re-verified on
every release.

**The star-count claim is plausible and consistent with independently
corroborated growth, not inflated.** The article states REA had "fewer
than 10,000 stars" on October 6 and "reportedly surpassed 472,600 stars"
"as of this writing." A web search for the most recent independent
figures (dated November 25, 2026 — the day before this check) converges
on 477,000–479,000 stars across star-history.com, a dated blog post
(478,090 at a stated UTC timestamp), and GitHub's own live page —
consistent with a 472,600 snapshot taken a day or two earlier, and
consistent with the independently-corroborated growth curve this
project's earlier `rea-gate` round already established (~9,700 stars on
October 7, past 290,000 by October 17, 453,918 by November 12, ~462,000
by November 16). The earlier `rea-gate` round also already surfaced
independent commentary questioning how many of REA's stars reflect real
usage — not a new finding this round, restated here only for continuity.

## Not independently reproducible from this sandbox, reported as such

The article's own concrete hands-on test — building a small 7-file,
1.9KB Electron-style note-taking app and running `rea
analyze-javascript-application /path/to/memo-app --json` against it,
reporting a 557,236-byte JSON result in 1.495 seconds that correctly
identified the `notes:search` IPC channel, the handler's location down to
a column range in `main.js`, `contextIsolation: true`, and the
`searchNotes` function name — was **not** independently re-run here. This
sandbox's auto-mode classifier has previously denied executing REA's own
cloned/installed code outright (documented in both the original
go-buildinfo-extractor round and the later html-ai-sanitizer round's
Scrapling work, under the same "Code from External"/"Unauthorized
Access" restriction), so no attempt was made to `npm install -g
rea-agents` and run it here. The claim is internally consistent with
REA's own real, verified evidence format seen directly in the DX-Ball
file above (hash-keyed "dossier" objects, detailed instruction/call
traces, byte-level reads) — a tool that produces that much structured
detail for one 63-byte function plausibly produces hundreds of kilobytes
for a whole (if tiny) application — but this is a plausibility judgment,
not independent reproduction, and is stated as such rather than claimed
confirmed.

**Credit**: the article's own closing ethical framing — that using REA to
copy a competitor's software risks real ToS/IP exposure, while using it
within authorized boundaries (legacy-system investigation, data
migration) is legitimate — matches the real repo's own `DISCLAIMER.md`
lawful-use boundary this project already credited in its very first REA
round, arrived at independently by a different author rather than
repeated from this project's own prior write-up.

## Checked `/builds/` first — no new build this round

`/builds/go-buildinfo-extractor/` and its Rust `cargo-auditable` sibling
already extract REA's static-binary-analysis mechanisms (built directly
from reading REA's own Go/Rust implementation code in two earlier
rounds). `/builds/rea-gate/` is the four-level verdict audit of the repo
itself. This article's two genuinely new technical threads — REA's
Electron/JavaScript IPC-call-tracing capability (main-process handler to
renderer-process call, matched and located to a source line/column) and
the real-world JSON-output-size experience — aren't independently
testable from this sandbox: the first would need REA actually running
against a real sample app (blocked by the classifier restriction above),
and the second is an experiential report about output volume, not a
mechanism with a clear input/output contract to reimplement and verify
against. Consistent with the Week 25 round's own precedent ("REA already
has two [builds]... nothing narrow enough to extract" when a fifth-ish
pass over the same repo surfaces no new generalizable, testable gap),
no new build was made this round — this write-up is the deliverable.
