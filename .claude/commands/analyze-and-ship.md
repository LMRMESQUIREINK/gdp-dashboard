---
description: Run a source (upload, URL, repo link, or pasted text) through this project's full deep-analysis-and-ship loop -- measure, verify, decide build-or-no-build, build and test for real if warranted, write it up, and push.
argument-hint: "[source: file path, URL, or leave empty to use the most recently pasted/uploaded content]"
---

# Analyze and Ship

Run `$ARGUMENTS` (or, if empty, the most recently pasted or uploaded
content in this conversation) through this project's established loop.
This is the lighter-weight default path -- a `/notes/*.md` write-up plus
a build when one is warranted. It is **not** the `ruthless-gate` skill:
that one only runs on its own explicit trigger phrase and produces a
four-file HTML verdict page. Don't confuse the two, and don't invoke
`ruthless-gate` just because this command ran.

## 0. Identify what this actually is, before anything else

- If `$ARGUMENTS` is a local filesystem path that doesn't exist in this
  repo and looks like it belongs to a different, unrelated local
  project (a Windows path, a project this repo has never mentioned),
  **stop and ask** rather than guess. (Real precedent: `/builds/
  outage-alert`'s first message was meant for a different local
  session entirely.)
- If `$ARGUMENTS` is a bare GitHub URL, clone it with `add_repo` /
  `git clone` and read the real files -- never summarize a repo from
  its README alone.
- If the same source (by filename, URL, or content hash) was already
  analyzed in an earlier round, **diff it against what's already in the
  repo before touching anything.** A re-upload is very often
  byte-identical to the last one (confirmed via direct `diff`) --
  "no changes needed" is a common, correct outcome, not a shortcut
  taken to save effort. Real precedent: the Trading Jarvis round-4
  revert, the Week 21 OSS-survey re-upload.
- If the request is ambiguous about scope (analysis only vs. analysis
  plus a build), and nothing in the conversation already answers it,
  ask once rather than guess on a large open-ended scope.

## 1. Measure before reading for meaning

Get the cheap, checkable facts before forming any opinion:

- File: `sha256sum`, `wc -l -w -c`.
- Repo: clone (shallow is fine), get file counts, `git log -1`, license,
  real directory structure -- not the README's own description of it.
- Pasted text with no file behind it: save it verbatim to the scratchpad
  first, then `wc`/`grep` it for real instead of eyeballing word counts
  or link counts from memory.
- Any worked arithmetic in the source (capacity math, cost estimates,
  claimed percentages): recompute it independently in a throwaway
  script. Report the exact match or the exact discrepancy -- a small,
  honestly-stated rounding artifact is a real, worthwhile finding even
  when the source's practical conclusion still holds.

## 2. Read the real thing in full

Pick the one or two claims or mechanisms that will actually anchor the
write-up, and read their real, complete source -- the actual code file,
the actual doc, the actual script -- not a table's one-line summary of
it. A capability description in a README is a claim about the code, not
the code.

## 3. Verify, don't repeat

- Check any claim against the real file/repo directly wherever that's
  possible.
- Web-search any claim about the outside world (a statistic, a dated
  event, a company's stated position, a popularity/star/download count)
  that can't be checked locally.
- An unverifiable claim about a paid product, a private repo, or an
  "I built X" statement with no shown code gets reported as
  **source-stated, not verified** -- never repeated as settled fact.
- If the source's dateline is more recent than this session's own
  knowledge, say so and verify the claim rather than assuming it's
  still accurate.

## 4. Find at least one real credit and one real gap

Don't only criticize and don't only praise. Name something the source
gets right, specifically and with evidence, and name something that
doesn't hold up, is unverifiable, or is in tension with something else
the same source says (or with something in this repo). The strongest
findings often come from reading two parts of the same source, or two
different sources in the same round, against each other -- neither one
states the connection, which is exactly why it's worth finding.

## 5. Decide: no build, or a real one

Before writing any code, check `/builds/` for whether this idea is
already covered. If it is, say so and point at the existing build
rather than duplicating it. A source surveying several already-mature,
independently-famous projects with no generalizable gap to extract is a
legitimate "no build" outcome -- state why in one or two sentences and
stop there.

When a build is warranted:

- Extract the **generalizable mechanism**, not the vendor's own
  specific branded instance. (Don't build "RemixForge." Don't clone
  REA's 3,235-file disassembler integration. Build the one real,
  well-specified capability underneath it, independently.)
- Scope it to what this sandbox can actually prove. State every
  deliberate cut with a one-line reason, in the README, not silently.
- Prefer testing against **this project's own real material** over
  synthetic fixtures alone wherever real material exists -- this
  project's own skills, its own sales pages, its own prior builds. Real
  bugs in a validator or checker tend to surface exactly there, not in
  hand-picked synthetic cases. (Real precedent: `skill-md-validator`'s
  two real bugs, `ten-k-website-grader`'s finding against Recovery
  Desk's real sales page.)
- Write real tests that assert actual correctness, not just "it ran
  without crashing." Run them for real. If a bug turns up while
  testing -- in the build, or in this round's own first draft -- fix it
  and say so plainly in the README and the commit; that's a normal,
  expected part of the loop, not something to clean up quietly.
- Never trust a tool's own pass/fail output without spot-checking a few
  results by hand against the real underlying files.

## 6. Write it up

- `/notes/<short-slug>-analysis.md` -- what was measured, what checked
  out, what didn't, what's unverifiable and why, what (if anything) got
  built and why that and not something else.
- If something was built: `/builds/<short-slug>/README.md` -- what's
  real, what's cut, what's proven, any bugs found and fixed.
- Update `CLAUDE.md`'s `## Current status` section: one new bullet, in
  the same specific, no-hype, exhaustive style as every existing entry
  in that file -- not a short summary. Read a couple of the existing
  entries first if this is a cold session, to match the register.

## 7. Ship it

Follow this repo's own git/PR workflow rule in `CLAUDE.md` exactly
(attribution footer, check for an existing open PR on this branch
before opening a new one, never force-push, never skip hooks). Commit,
push, and confirm the PR link in the final message to the user.

## 8. Close the loop

End with a short summary: what the source was, the one or two real
findings, what got built (or why nothing did), and that it's pushed.
Don't re-paste the full analysis -- the user can open the note.
