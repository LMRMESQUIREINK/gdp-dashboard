---
name: agent-brief-grader
description: Grade a brief/prompt against the three real signals Anthropic's own usage-expertise report ties to high-success sessions — a stated reason, a stated boundary, a checkable done-condition. Use before starting any build with several moving parts, or when asked "is this a good brief." Triggers on "grade this brief", "is this prompt clear enough", or a thin-reading brief before a multi-step build.
---

# Agent Brief Grader

A real, dependency-free Python checker, not a vibe check — see
`/builds/agent-brief-grader/README.md` for the full source
verification (Anthropic's real June 2026 400K-session report, read
directly) and the real bug found and fixed while building it.

## When to run this

- **Before starting a Goal/Loop or Software Factory build** whose
  initial brief reads thin — missing a stated reason, no named
  constraints, or no way to tell when it's done. This is the
  pre-flight half of what the Goal/Loop method
  (`/prompts/goal-loop-method.md`) already asks for (a checkable Goal
  document) — this tool checks whether the brief handed to you already
  has the raw material for one, before you write it.
- When a human directly asks whether their own prompt/brief is clear
  enough, or asks you to "grade this brief."
- Not needed for a genuinely small, one-line change — this is for
  anything with several moving parts or real ambiguity risk, the same
  bar `new-feature` and the Goal/Loop method already use.

## How to run it

```bash
python3 /home/user/gdp-dashboard/builds/agent-brief-grader/brief_grader.py path/to/brief.txt
python3 /home/user/gdp-dashboard/builds/agent-brief-grader/brief_grader.py --json < brief.txt
```

Or call it directly on the brief text you were just given, by writing
it to a temp file first (or piping it via stdin) — it doesn't need to
be a saved file, just the raw text of the request.

## What it checks, and what it deliberately doesn't

Three real, evidenced signals, each reported with the exact matched
text, never a bare pass/fail with no evidence:

- **`why`** — is a reason given, so small judgment calls during the
  work can be made the way the person actually wants?
- **`constraints`** — is there a stated boundary (what's off-limits)?
- **`done_criteria`** — is there a stated way to tell the work is
  finished, and (`done_criteria_concrete`) is that way checkable
  (tests passing, a specific condition, a number) rather than a
  subjective call ("looks good")?

**What it can't check, stated plainly**: whether the brief states an
*outcome* versus dictating a rigid step-by-step recipe is the one
signal from the real report's classifier this tool can't reliably tell
apart from text alone — surfaced only as a non-scored informational
flag on the single clearest case, never a hard pass/fail. `brief_grader.py` itself only ever sees one message, so it can't check
the real classifier's third signal (who corrects whom over a
conversation) — for a short transcript (a JSON list of `{role, text}`
turns), use `conversation_grader.py` instead, which adds that check on
top of the same three.

A companion module, `reply_format_checker.py`, checks the OTHER side of
a conversation — an agent's own reply, against the fixed order
`CLAUDE.md`'s "Reply format for multi-step or long-running work"
section now states (needs-from-you → done? → summary → what-went-wrong).

## What to do with a low score

Don't silently proceed on a brief missing `why`/`constraints`/
`done_criteria` if it's about to drive a multi-step build — ask the one
or two missing questions back (per `how-i-work.md`'s "ask ONE question
at a time" rule), using the tool's own category names as a guide for
what's actually missing, rather than a vague "can you clarify?" A score
this tool reports is informational, not a hard gate: a human who
answers "skip" to a clarifying question still gets to skip, same as
every other rule in this project about not over-interrogating.
