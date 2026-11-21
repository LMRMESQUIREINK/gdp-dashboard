# wiki-health-check

A dependency-free Python tool implementing a real, checkable structure
behind one specific prompt in a pasted Substack article ("Build a second
brain that Claude can read, write and keep tidy for you," Frank Andrade/
Artificial Corner — his own article this round, not a guest post like the
NotebookLM round). Full analysis: `/notes/obsidian-llm-wiki-analysis.md`.

## Why this exists

The article describes setting up an Obsidian vault as an Andrej Karpathy-
style "LLM wiki": a `raw/` folder of immutable sources (meeting notes,
articles, chats) plus an LLM-maintained `wiki/` folder of cross-linked
topic notes, governed by a `CLAUDE.md` rules file. It then gives a real
"health check" prompt:

> "Do a health check of the wiki. Find notes that contradict each other,
> claims a newer source has replaced, and topics mentioned often that
> have no note yet. ... Only report what would mislead me if I followed
> it today. Don't change anything."

That's a live instruction re-interpreted fresh by an LLM on every run —
not a mechanism. This build turns its three named targets, plus its own
stated filtering rule (the article calls it "the line that matters
most"), into real, structural checks that produce the same verdict every
time on the same input.

## What was verified before building anything

- **Karpathy's LLM wiki gist is real** — `gist.github.com/karpathy/
  442a6bf555914893e9891c11519de94f`, published April 2026, and the
  described `raw/wiki` separation (sources stay immutable; the LLM owns
  the wiki layer) matches multiple independent write-ups of the same
  gist. The article's own framing is an accurate, concrete walkthrough of
  what the gist itself states abstractly.
- **Anthropic really did merge Claude's chat and Cowork modes** —
  announced mid-September 2026, rollout beginning then and continuing
  through November 2026 for different plan tiers; Claude Code is
  confirmed to stay a separate product, matching the article's own
  "regular Claude vs. Claude Code" framing.
- **Obsidian Sync's $5/month** and the **official Web Clipper extension**
  (`obsidian.md/clipper`, free, open source, maintained by Obsidian's own
  team) both check out exactly.
- **Not independently confirmed**: the specific claim that the Claude
  desktop app shows a literal icon toggle in the top-left between
  "regular Claude" and Claude Code in one window. The chat/Cowork merge
  and Claude Code's separateness are both confirmed; this one UI detail
  wasn't found described anywhere in the available sources, so it's
  reported as unconfirmed, not disputed.

## Checked `/builds/` first

Nothing in this project checks a personal Obsidian-style wiki for
contradictions, staleness, or coverage gaps. `agent-memory-layer` has a
`STALE` lifecycle state, but for *agent* memory records, not a
cross-linked topic wiki built from raw source files — a different
domain. `manifest-drift-guard` checks file-hash drift, not semantic
claim staleness. A genuinely new gap.

## What this checks

Given a structured representation of raw sources and wiki notes — each
claim explicitly tagged `actionable` or `cosmetic` at creation, the same
"only report what would mislead you" rule applied structurally instead of
left as a live LLM judgment call:

- **`check_contradictions`** — two different notes asserting different
  values for the same claim subject, with no newer source to resolve
  which is right.
- **`check_staleness`** — a note's claim where a newer raw source on the
  same subject asserts a different value the note hasn't caught up to.
- **`check_coverage_gaps`** — a topic mentioned across at least N
  (default 3) distinct raw sources with no dedicated wiki note yet.

A cosmetic claim (a renamed folder, a relabeled vault) never produces a
finding from any of the three checks — the article's own example of what
shouldn't get flagged, enforced structurally rather than hoped for.

## Usage

```
python3 cli.py wiki.json
```

See `cli.py`'s docstring for the JSON shape, or `tests/test_cli.py`'s
fixtures for complete worked examples.

## Proof

`python3 -m unittest tests.test_wiki_health tests.test_cli -v` —
**14/14 tests pass**, including:

- A clean, healthy wiki producing zero findings.
- A deliberately broken wiki modeled on the article's own worked
  scenarios — a budget cap reversed between a March and a June meeting
  (staleness), two notes citing different client deadlines with no
  newer/older resolution (contradiction), "pricing" and "budget" each
  mentioned in 3+ raw sources with no dedicated note (coverage gap), and
  a cosmetic vault rename that correctly triggers nothing at all — a
  true discrimination test across all three check types plus the
  cosmetic-filter rule together.
- Real subprocess CLI runs with clean, non-traceback error handling for
  a missing file, malformed JSON, and an invalid date string.

**One real bug caught in this build's own first-draft test fixture, not
manufactured**: the cosmetic-rename test fixture's date field was
accidentally written as a Python string-slice expression
(`"2027, 02-01"[:10]`) instead of a plain ISO date, which would have
produced `"2027, 02-0"` — not a valid date. Caught immediately on the
first real test run (`ValueError` from `date.fromisoformat`), fixed to a
plain `"2027-02-01"` before anything else was checked.

A second thing worth naming, not a bug: `check_contradictions`'s first
draft skipped an *entire* subject group the moment any one claim in it
was cosmetic, rather than filtering just the cosmetic claims out and
checking what remained — caught by re-reading the logic before writing
the cosmetic-rename test, not by a failing run, and fixed before the
suite was ever executed.

## Deliberately not built

- Any claim-extraction step that would turn freeform prose (an actual
  meeting note, an actual Obsidian vault) into the structured `Claim`
  objects this tool checks — that's exactly the job the article hands to
  a live LLM, and faking it with a keyword heuristic would misrepresent
  what the real health check prompt actually does. This tool is the
  mechanical verifier *underneath* that step, not a replacement for it.
- A live Obsidian/Claude desktop integration — no account, no vault, no
  desktop app access from this sandbox.
- Karpathy's own gist content reproduced here — nothing in this build
  copies the gist's text; the `raw/wiki` separation it describes is
  reimplemented from understanding, not transcribed.
