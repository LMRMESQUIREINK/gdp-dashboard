# Deep analysis: "How to build your second brain with NotebookLM"

Source: a pasted Substack article, a guest post by Hamza Khalid (AI in
public) for Frank Andrade's Artificial Corner — the same publication
`/notes/winston-talk-checker-analysis.md` analyzed last round, a
different guest author this time. No accompanying instruction, so per
this project's convention the article itself is the instruction to run
the deep-analysis-and-ship loop. A paywalled piece — the free portion
covers a step-by-step NotebookLM setup, one real custom-instructions
block, and two free prompts; the paid portion (a "Second Brain Starter
Kit": four notebook blueprints, 12 prompts, an AI-mentor technique) is
behind the paywall and was never seen by this round.

## What was measured and verified first

- **NotebookLM really was renamed "Gemini Notebook."** Confirmed via
  Google's own Workspace Updates blog: the rename happened July 16,
  2026, is explicitly stated as not a discontinuation, and
  `notebooklm.google.com` now redirects to the real new address,
  `notebook.google.com`. The article's own framing ("Google renamed it
  Gemini Notebook recently... I'll use the old name here because most
  people still search for it") matches exactly, both the fact and the
  stated reason for still using the old name.
- **"Configure Chat" is a real, current feature**, checked against
  Google's own help documentation rather than the article's paraphrase:
  three conversational styles (Default, Learning Guide, Custom) and
  three response lengths (Default, Longer, Shorter). The article's
  described click path (three dots → "Configure Chat" → "Custom" → save
  instructions) matches the real current UI as documented.
- **Hamza Khalid / "AI in public" is a real, active Substack**
  (`humzakhalid.substack.com`, mirrored at `aiinpublic.com`), with
  recent 2026 posts and a stated move to three issues a week.
- **The Ebbinghaus claim checks out.** "More than half of new material
  was gone within an hour" matches the real, independently-replicated
  figures: commonly cited as ~50%, with Ebbinghaus's own more precise
  1885 figure at ~56% (measured as "savings" lost in relearning time,
  not direct recall) and Murre and Dros's 2015 replication landing
  within a few percentage points of the original. Not an invented or
  exaggerated statistic.
- **No live NotebookLM/Gemini Notebook access from this sandbox** — it
  requires a real Google account login, which isn't available here.
  The UI claims were checked against Google's own written help docs,
  never exercised live, and this is stated plainly rather than guessed
  past.

## The real finding: the article's own evidence undercuts its own prescription

The article cites Ebbinghaus specifically to motivate urgency — forgetting
is front-loaded, fastest in the first hours and days. Then its actual
operating cadence (Step 6) is: "every Sunday, add what you saved that
week. Ask what changed compared to your older sources." That's a flat,
once-a-week batch review with **no per-item spacing** at all — the
opposite structural idea from what spaced repetition (a technique
Ebbinghaus's own research directly motivated — SM-2, the Leitner system,
and every modern flashcard app) actually does.

Quantified directly rather than asserted: under the article's own weekly-
Sunday cadence, the delay between saving an item and its first review
depends entirely on which day of the week it happened to get saved —
recomputed with real date arithmetic (`date.weekday()`), not estimated:

| Saved on | Days until the next Sunday review |
|---|---|
| Monday | 6 |
| Tuesday | 5 |
| Wednesday | 4 |
| Thursday | 3 |
| Friday | 2 |
| Saturday | 1 |
| Sunday | 0 |

Against a simple day-1 spaced-repetition checkpoint, that means an item
saved on a Monday gets its first review **5 days later** than the decay
curve the article itself cites would suggest is useful — and the
average extra delay across the week is a real, computed 2.0 days. The
article's own justification argues for exactly the mechanism it doesn't
implement.

A real caveat found while checking the alternative, stated honestly
rather than oversold: there is no single proven-optimal spacing. Karpicke
& Roediger (2007) found equally-spaced retrieval actually beat expanding-
interval retrieval on recall after two days in at least one controlled
study. So the finding here is a real, well-evidenced *tension* in the
article's own reasoning, not proof that its weekly cadence is simply
wrong — stated with that nuance in both the build and this note.

## Credited

The custom-instructions block given in Step 4 is a genuinely well-
constructed anti-hallucination contract for a RAG-style tool: grounding
restricted to the notebook's own sources, an explicit fallback phrase for
missing information ("Not in my sources"), a request to name what kind of
source would fill the gap, a citation requirement, and an instruction to
surface disagreement between sources rather than silently blending them.
This is the same discipline this project has built around repeatedly
(`checkGrounding.ts`, the Required/Forbidden framework in
`qualityBoundary.ts`), arrived at independently here from a completely
different domain (personal knowledge management rather than agent
testing) — a real, convergent finding, not a derivation either way.

## Checked `/builds/` first

Nothing in this project does spaced-review scheduling or audits a system-
prompt/custom-instructions block's text against a stated rule set.
`agent-memory-layer` has a lifecycle (RAW→ACTIVE→CONFIRMED→SUPERSEDED→
STALE→ARCHIVED→FORGOTTEN) for *agent* memory records, a different concept
from human review scheduling. `skill_md_validator.py` and
`winston_checker.py` both check structured text against a stated rule set
in other domains, confirming the pattern fits this project but doesn't
already exist for this source.

## Built

**`/builds/second-brain-toolkit/`** — two small, dependency-free Python
modules:

- `review_scheduler.py` — the computed weekly-cadence-lag finding above,
  plus a real, usable expanding-interval scheduler (`DEFAULT_INTERVALS =
  (1, 3, 7, 14, 30)`, a commonly-cited schedule, explicitly caveated with
  the Karpicke & Roediger finding rather than claimed optimal).
- `prompt_auditor.py` — six checks derived directly from specific clauses
  in the article's own real Step 4 text (grounding-only, fallback phrase,
  suggests-missing-source-type, citation-required, disagreement-
  surfacing, plain-English), three load-bearing (FAIL) and three softer
  (WARN) — not a generic prompt-quality rubric invented independently of
  the source.

31/31 tests pass, including the article's own real, verbatim
custom-instructions text passing every check cleanly, and a naive "be a
helpful assistant" block failing or warning on every single one — a real
discrimination pair, not a one-sided demonstration.

**A real bug caught in this build's own first-draft hand math, not
manufactured**: before writing any test, a manual pass computed Monday's
lag to the next Sunday as 5 days. Running the actual
`date.weekday()`-based arithmetic gave 6. Caught by recomputing directly
rather than trusting the hand count, and every affected test and the
README's own table were corrected to the real, re-derived numbers.

## Deliberately not built

- Anything resembling the paywalled Starter Kit's four notebook
  blueprints, 12 prompts, or AI-mentor technique — never seen, nothing
  here is derived from it.
- A live NotebookLM/Gemini Notebook integration — no account, no login,
  no API access from this sandbox.
- A claim that the expanding-interval schedule is proven optimal for all
  material — see the Karpicke & Roediger caveat above.
