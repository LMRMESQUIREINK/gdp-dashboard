# Analysis: "Data Science Is Changing. These Are the Skills I'd Learn in 2027"

Source: a pasted Medium article (Codebook Fusion, Oct 10 2026, 12-minute
read). No accompanying instruction — handled per this project's standing
`/analyze-and-ship` loop.

## What kind of source this is

Unlike most sources this project analyzes, this one has almost no
externally-checkable surface: no code to run, no repo to clone, no
specific statistic cited to a named source, no dated external claim. It's
a personal-experience-driven opinion/career-advice piece: a 9-skill
rubric, a 12-month roadmap, a "mistakes I made" list, and an FAQ. The
named tools throughout (Python, SQL, pandas, Polars, DuckDB, Airflow,
Dagster, dbt, "LLM as a judge") are all real, well-known, actively
maintained tools — stating this plainly rather than spending verification
effort confirming facts this widely-known that nobody disputes. The
article's own Medium engagement numbers (288 claps, 7 responses) are not
independently checkable from this sandbox (no live Medium API access,
same class of restriction as every other paid/live-service check this
project has documented) and aren't load-bearing to any of its claims
anyway.

## The real finding: the 9-skill list and the rest of the article disagree with each other

The article's headline "9 Skills I Would Learn in 2027" list does **not**
include classical machine learning as one of the 9 named skills. Skill 1's
own framing explicitly argues the shift has moved *away* from it: "the
first question has changed from 'which algorithm should I train?' to 'do
I need to train anything at all?'" Skill 2 is Python/SQL/reading code;
Skill 3 is LLMs/RAG/agents — classical ML sits in neither.

Yet the rest of the article treats classical ML as essential, foundational,
first-to-learn material:

- The 12-month roadmap's **Months 3 to 4** are devoted entirely to it:
  "Core machine learning. Regression, classification, and tree models
  with proper validation. Learn to build a baseline and beat it honestly."
- The FAQ directly asks "Should I learn LLMs before classical machine
  learning?" and answers: "Learn the basics of classical machine learning
  first. It teaches validation, overfitting, and evaluation, which you
  will need to judge any AI system properly. Then add LLMs and RAG on
  top." — explicitly sequencing it *before* skill 3 in actual practice.
- The article's own closing line ("Notice that I am not saying classical
  machine learning is dead... The skill is knowing when a simple model
  beats a giant one") treats it as a live, ongoing skill, not a
  deprioritized one.

So the piece's own practical advice (learn classical ML first; it's a
genuine, two-month roadmap item; the FAQ states it outright) contradicts
the structure of its own headline list, which the article itself says is
ordered "roughly by return on time invested" — a list that omits
classical ML entirely cannot also be an honest ranking of what to invest
time in first, given the FAQ's own answer. This is a real, checkable
internal inconsistency in the article's structure, not an external fact
to verify — found by reading the piece's own sections against each other,
the same technique this project has applied to prior sources (the ACP/
multi-tenant-LLM round, the two Sakshi Jaiswal articles, the quantum/
security-pipeline pair).

## What's credited

- The article's own cross-references are internally consistent and
  mutually reinforcing in a way worth naming: Skill 1 ("write a one page
  brief... before touching data") and Skill 4 ("write the evaluation set
  *before* writing the system") independently arrive at the same
  discipline — define success before building — and "Mistake 1: Starting
  with the model" directly operationalizes both. A genuinely coherent
  throughline, not three disconnected bullet points.
- "The job I trained for is not disappearing, but it is moving" and the
  closing spreadsheets/accountants analogy are a reasonable, non-alarmist
  framing, consistent with the article's own honest personal anecdotes
  (the three-weeks-tuning-gradient-boosting story, told against the
  article's own point rather than to flatter the author).
- Naming "LLM as a judge" as a real, current evaluation technique is
  accurate — this is a genuinely active area of eval methodology, not an
  invented term.

## What's flagged

- **Skill 4 names "LLM as a judge" biases and limits without naming a
  single one** ("Rubrics and LLM as a judge methods, while understanding
  their biases and limits") — for the single most practically important
  caveat anyone implementing this technique needs (position bias favoring
  whichever option is shown first/last, self-enhancement bias favoring a
  judge's own model family, verbosity bias favoring longer answers
  regardless of quality — all well-documented, specific, nameable
  failure modes), the article only gestures at "biases and limits"
  existing, never says what they are. A real, checkable gap in depth for
  a piece that otherwise gives concrete, operational advice everywhere
  else (write the eval set first, sanity-check row counts, check cost
  math early).
- Several claims are stated as flat assertions with no evidence offered
  ("Generalists are easier to replace than specialists," "cost is now a
  design constraint, not an afterthought") — plausible, consistent with
  the rest of the piece's reasoning, but not independently sourced to
  anything, reported here as the article's own stated opinion rather than
  verified fact.

## Decision: what got built, and why

Checked `/builds/` first: `agent-readiness-scorecard` assesses a
codebase's AI-*agent* maturity (Factory.ai's framework); `ten-k-website-
grader` assesses a rendered web page; `gate-floor-checker` distinguishes
structural from improvable gate failures. None of them score a repo
against *this* rubric — a data-science/ML-engineering skill-signal
checklist.

**Built**: `/builds/ds-2027-skills-scorecard/` — the same move as
`agent-readiness-scorecard`/`ten-k-website-grader`: an honest, file-
observable scorer for the 6 of 9 skills a directory listing can actually
speak to, with the other 3 always reported `not_assessable` rather than
faked. Found and fixed a real bug during this round (a self-matching
detector pattern, the exact `ruthless-gate`-documented pitfall), and
corrected one of the test's own wrong ground-truth assumptions once the
real run surfaced genuine evidence the first draft hadn't checked for —
both detailed in the build's own README.
