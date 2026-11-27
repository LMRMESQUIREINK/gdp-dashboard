# Analysis: "Anthropic's Latest Study Reveals How the Top 1% Use AI"

Source: a pasted listicle, no accompanying instruction (per this
project's standing rule, that's itself the instruction to run the
deep-analysis-and-ship loop). Six "habits" claimed to come from
"studying 200,000+ real Claude users," framed as a single study plus
one internal report.

## What was actually checked

This is a rare source for this project: no code, no repo, but a real,
checkable primary source behind most of its numbers — Anthropic's own
published research and internal reports, plus named staff quotes. So
the verification surface was tracing every specific number and quote
back to where it actually comes from, via web search and a direct
fetch of Anthropic's own report page, rather than code execution.

### The core study, read directly

**"Agentic coding and persistent returns to expertise"** (Anthropic
Economics team: Zoe Hitzig, Maxim Massenkoff, Eva Lyubich, Shaoyi
Zhang, Ryan Heller, Peter McCrory; published 2026-06-16). Sample:
~400,000 interactive Claude Code sessions from ~235,000 people,
October 2025–April 2026 (CLI, claude.ai, and the desktop app only —
explicitly excludes Cursor/VS Code integrations, headless `claude -p`
sessions, and programmatic Agent SDK use).

Checked directly against the real report text (fetched via the
`web-fetch` agent):

- **15%** novice verified-success, **77%** novice partial-success —
  exact match to the listicle's "15%" claim.
- **28–33%** verified-success for "intermediate or up" — the
  listicle's "somewhere between 28% and 33%" for "intermediate and
  expert users" is this same combined range, correctly represented as
  one range rather than invented as two separate figures.
- **19%** of *troubled* novice sessions abandoned vs. **5–7%** for
  everyone else — exact match to the listicle's Habit 6 numbers. (The
  report's own sentence doesn't restate the denominator explicitly; it
  is troubled sessions, not all sessions — the listicle's "sessions
  that hit real problems" framing gets this right.)
- Expertise is **not** self-reported and **not** based on job title or
  occupation (that's a separate variable, inferred into one of 23 SOC
  groups for ~70% of sessions). It's rated per-transcript by Claude
  itself, 1–5, from exactly three signals: "how precisely the user
  frames their directions, what they ask Claude to verify, and whether
  the user tends to correct Claude or Claude tends to correct the
  user." The listicle's three framing questions ("Did the person
  explain clearly what they wanted? Did they ask Claude to check
  specific things? Were they the one steering, or was Claude steering
  them?") are a close, accurate paraphrase of exactly these three
  signals — one of the stronger matches found in this round.
- Occupation comparison: software-related occupations reach ~30%
  overall verified-success vs. ~26% for other professions; in
  code-producing sessions specifically, 34% vs. 29%, with "every one of
  the ten largest occupations... within seven points of software
  engineers." The listicle's "their success rates landed close to
  those of actual software engineers" is directionally accurate,
  though it doesn't quote the actual 5–7-point gap.
- The report's own framing — "the ability to steer Claude toward
  success comes more from command of a domain than from the ability to
  write code" — is very closely echoed by the listicle's "Knowing your
  subject and explaining it well beat knowing how to code."
- **Not found in the report**: any stated correlation between
  verification/"done criteria" and session success as a *quantitative
  finding*. "What they ask Claude to verify" is one of the three
  expertise signals (so it correlates with the expertise *rating*,
  which does correlate with success) — but the report itself never
  states a direct done-criteria → success correlation as its own
  result. The listicle's framing of this as something "Anthropic
  found" is one step more confident than the primary source states;
  the actual source for the "give it a way to verify" claim is Boris
  Cherny's personal commentary (see below), not the study.

### Three other real sources, previously uncredited in the piece

- **"How AI is transforming work at Anthropic"** (~August 2025, a
  survey of 132 engineers/researchers + 53 interviews + internal usage
  data). Real source of the "27% of Claude-assisted work wouldn't have
  happened without it" figure (Habit 4) — the report's own closer
  wording is "wouldn't have been done," a small but real difference in
  framing (done vs. happened), not a fabricated number.
- **A separate internal workforce report** (2026-10-16). Real source
  of Habit 3's "~6x as many hours" (agents directed by employees vs.
  the employees themselves, as of August 2026) and "~80% of the time...
  just waiting for a person to respond." Also the source of an
  unrelated junior-hiring-share drop the listicle doesn't mention.
- **Individual staff social posts**, not any formal report: Boris
  Cherny's real, verbatim-matched "give Claude a way to verify its
  work... probably the most important thing" quote (X, dated post);
  Alex Albert's real, verbatim-matched "not worth my time" /
  screenshot-renaming example (X, 2026-01-09) — checked and found to
  be the *exact* example the listicle uses, a genuine, confirmed match.

**One claim flagged as unverified, not repeated as fact**: the
Amanda Askell habit ("when Claude surprises her, she asks it to
explain its reasoning, then fixes that gap in her own instructions")
could not be found anywhere in the sources checked — her public
material (the Claude constitution, interview coverage) discusses
explaining Claude's own reasoning *to users*, not this specific
surprise-triggered habit. Not disputed as false, simply not locatable
from this sandbox's search access — stated here as `source-is-silent`,
the same treatment given to every other previously-flagged uncited
claim in this project (Factory.ai's unreadable chart, REA's star
count before independent corroboration, "Andre Horowitz").

### The strongest finding

The listicle frames all six habits as coming from "Anthropic's Latest
Study" plus "they turned the lens on themselves" — implying two
sources. Tracing every number individually surfaces **four**: the
June 2026 400K-session study, the August 2025 employee survey, the
October 2026 workforce report, and uncredited personal staff posts.
Every individual number checked out real; what's compressed is the
narrative that they all come from one or two unified artifacts. This
is the same genre of finding this project has made before — several
independently-written sources narrated as a single study (the
WordPress-prompt-pack/Higgsfield-skill shared-operator finding, the
Week 19/20 newsletter's mixed real/aggregated figures) — visible only
by tracing each specific claim back to its own primary source rather
than trusting the piece's own framing.

A smaller, direction-stated finding: the title's "200,000+ real Claude
users" undercounts the real ~235,000-person sample by about 35,000 —
an understatement, the less common direction for this kind of rounding
in a marketing-adjacent headline.

## Built: `/builds/agent-brief-grader/`

Checked `/builds/` first: nothing in this project checks a single
agent-directed brief/prompt's text for the structural signals a
real usage study says actually predict success — `winston-talk-checker`
checks a presentation deck, `wiki-health-check` checks a knowledge
wiki's internal consistency, `orchestration-decision-engine` is a
runtime decision loop, not a text checker. A genuinely new, narrowly
scoped gap.

Built directly from the one part of this source that's both fully
verified and mechanically checkable: the real classifier's first two
signals (precision of framing, what's asked to be verified) map onto
three checkable components of a single brief — a stated reason
(`why`), a stated boundary (`constraints`), and a stated, evidenced way
to tell the work is done (`done_criteria`, further scored for whether
it's `concrete` — a hard, checkable signal — or just a subjective call,
directly reusing the report's own "hard verifiable signal" definition:
git activity, tests passing, explicit affirmation). The third real
classifier signal (who corrects whom) needs a multi-turn transcript and
isn't attempted here, stated plainly rather than faked with a weaker
proxy.

Every check carries its matched evidence text, never a bare pass/fail.
One signal the real classifier gestures at — outcome-framing versus a
micromanaged step recipe — is deliberately left as an
**informational-only** flag on the single clearest case (every line is
a numbered step, no sentence states a goal), never folded into the
score, since a reliable general version of that distinction needs
semantic judgment this tool doesn't have.

20/20 tests pass, including a real discrimination pair (a well-formed
brief scores 4/4 and triggers no informational flag; a bare five-step
recipe scores 0/3 and does trigger it) and a real CLI subprocess round
trip. **One real bug found and fixed on the first run**:
`CONCRETE_DONE_PATTERNS`'s first draft required "test(s)" directly
adjacent to "pass(es/ing)," which fails on completely ordinary real
phrasing ("the existing test suite still passes") — caught immediately
by the test fixture itself scoring 3/4 instead of the expected 4/4;
fixed by widening the pattern to tolerate up to 30 characters between
the two words, bounded by sentence-ending punctuation so it can't leak
across an unrelated later sentence.
