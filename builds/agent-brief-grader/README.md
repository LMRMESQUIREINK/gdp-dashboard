# agent-brief-grader

A real, dependency-free Python checker for the one piece of "how the
top 1% use Claude" that's actually checkable from text alone: whether
the brief you're about to send an agent carries the signals Anthropic's
own research says separate a high-success session from a low-success
one. Built from a pasted listicle ("Anthropic's Latest Study Reveals
How the Top 1% Use AI"), fact-checked against the real primary sources
rather than taken on the listicle's word. Full write-up:
`/notes/anthropic-claude-usage-habits-analysis.md`.

## What the real research actually says, checked directly

The listicle's central claim traces to Anthropic's real, published
report, **"Agentic coding and persistent returns to expertise"**
(2026-06-16, ~400,000 Claude Code sessions from ~235,000 people,
October 2025–April 2026). Its own methodology section states the
expertise classifier exactly:

> "The expertise classifier looks for three signals: how precisely the
> user frames their directions, what they ask Claude to verify, and
> whether the user tends to correct Claude or Claude tends to correct
> the user."

Only the first two are checkable from a single brief's text with no
model judgment and no multi-turn transcript — the third needs to watch
a whole conversation unfold. This tool checks what's actually
checkable: a stated reason (**why**), a stated boundary
(**constraints**), and a stated way to tell the work is finished
(**done criteria**) — plus whether that done-criteria is **concrete**
(a "hard verifiable signal," the report's own phrase: "git activity
like commits and pull requests matching the work, as well as test
suites passing, and explicit affirmation from the user") or just a
subjective call ("looks good").

The listicle's own two headline numbers for novice vs. everyone-else
sessions are exact matches to the real report, confirmed by reading
it directly: **15%** verified-success for novice-rated sessions,
**28–33%** for intermediate-or-above (the report's own combined range,
not two separate figures), and **19%** of *troubled* novice sessions
abandoned outright vs. **5–7%** for everyone else.

## What the listicle gets right, and where it quietly blends four sources

Credited directly: the "4 questions" framing (job / why / constraints
/ done) is a genuinely close paraphrase of the real three-signal
classifier, and the article's framing — "the ability to steer Claude
toward success comes more from command of a domain than from the
ability to write code" (the report's own words, matched closely) — is
accurate. Alex Albert's quoted habit (renaming screenshots by their
contents rather than dismissing the idea as "not worth my time") is a
real, verbatim-matched post (X, 2026-01-09). Boris Cherny's "give
Claude a way to verify its work" quote is real too, matching his own
post closely ("probably the most important thing to get great results
out of Claude Code... it will 2-3x the quality of the final result").

**The one finding worth naming plainly**: the listicle presents this
as "Anthropic's Latest Study" (singular) plus "they turned the lens on
themselves" (one internal report), but the numbers actually trace to
**four distinct sources**, never individually named in the piece:

1. The June 2026 400K-session external-user study (Habits 1 and 6, and
   the intro's framing).
2. A separate, earlier internal survey — "How AI is transforming work
   at Anthropic" (132 engineers/researchers, ~August 2025) — which is
   the real source of the "27% of work wouldn't have happened without
   it" figure (Habit 4; the report's closer wording is "wouldn't have
   been done," not "happened").
3. A third, later internal workforce report (2026-10-16) — the real
   source of the "6x hours" and "~80% waiting for a human" figures
   (Habit 3), and of the junior-hiring-share drop (unrelated to
   anything in this listicle).
4. Individual staff social-media posts (Boris Cherny, Alex Albert, and
   a claimed Amanda Askell habit that **could not be independently
   confirmed anywhere** — flagged here as unverified, not repeated as
   fact) — these back most of Habits 1 (the "done" question
   specifically), 2, 4's framing, 5, and 6.

None of this makes the listicle wrong — every number checked out real
— but a reader following "Anthropic's Latest Study" as one artifact
would not find any single document containing all six habits. That
compression is the real, checkable finding, the same genre this
project has flagged before when several distinct sources get narrated
as one.

Also noted, direction stated rather than left ambiguous: the title's
"200,000+ real Claude users" rounds the real ~235,000 figure down by
roughly 35,000 — an understatement, not an inflation.

## What's built

`brief_grader.py` — `grade_brief(text) -> BriefGrade`, three scored
checks (`why`, `constraints`, `done_criteria`) plus one sub-check
(`done_criteria_concrete`, only produced when `done_criteria` itself is
present) and one **informational-only** flag
(`check_pure_step_list`) that is never folded into the score. Every
`present=True` result carries the exact matched text as evidence — no
check reports a finding without the snippet that produced it.

Stated plainly, not quietly narrowed: the fourth classifier-adjacent
dimension — whether a brief states an *outcome* versus dictating a
rigid, line-by-line recipe — is the one signal this tool can't
reliably tell apart from text alone ("build me X" and a literal
numbered recipe for X both show up in perfectly good real briefs), so
it's surfaced only as that one informational flag on the single
clearest case (every line is a numbered/bulleted step, and no sentence
anywhere states a goal or hands Claude any latitude), never scored as
a pass/fail.

```bash
python3 brief_grader.py path/to/brief.txt
python3 brief_grader.py --json < brief.txt
echo "some text" | python3 brief_grader.py
```

```
Brief grade: 4/4
  [PASS] why -- "…ave to re-enter their email every time, because support tickets about this are our #1 c…"
  [PASS] constraints -- "…ogin page redesigned so returning users don't have to re-enter their email every time…"
  [PASS] done_criteria -- "…any new npm dependency. We'll know it's done when the existing auth test suite still pass…"
  [PASS] done_criteria_concrete -- "…l know it's done when the existing auth test suite still passes and a manual test shows the email field…"
```

## Verification — real tests, including a real bug found and fixed

```bash
python3 test_brief_grader.py
```

20/20 checks pass, including a real discrimination pair (a genuinely
well-formed brief scores 4/4; a bare five-line numbered-step brief
scores 0/3 *and* correctly trips the informational step-list flag),
a vague-done-criteria case scored correctly (`done_criteria=True`,
`done_criteria_concrete=False`), and a real CLI subprocess round trip.

**One real bug found and fixed on the first run, not assumed clean
from writing it**: `CONCRETE_DONE_PATTERNS`'s first draft required
`tests?` to sit directly adjacent to `pass(es|ing)?`
(`r"\btests? pass(es|ing)?\b"`), which fails on completely ordinary
real phrasing — "the existing **test suite still passes**" has two
words between "test" and "passes," so the pattern never matched the
good fixture's own done-criteria sentence, scoring it 3/4 instead of
4/4. Caught immediately by the test asserting the real fixture should
score concrete; fixed by widening the pattern to allow up to 30
non-sentence-ending characters between the two words
(`r"\btests?\b[^.!?\n]{0,30}\bpass(es|ing)?\b"`), bounded by sentence
punctuation so it can't cross into an unrelated later sentence.
