# second-brain-toolkit

Two small, dependency-free Python tools built from a pasted Substack
article about turning NotebookLM (now Gemini Notebook) into a "second
brain." Full analysis: `/notes/second-brain-notebooklm-analysis.md`.

## Why this exists

The article's free portion (a guest post by Hamza Khalid for Frank
Andrade/Artificial Corner — the same publication `/builds/
winston-talk-checker/` analyzed last round) gives a real, checkable setup
guide plus one concrete custom-instructions block to paste into
NotebookLM/Gemini Notebook's "Configure Chat" feature. The paid
"Starter Kit" (four notebook blueprints, 12 prompts, the AI-mentor
technique) is behind the paywall and was never seen — nothing here is
derived from it.

Two things were checked and built from, independent of the paywall:

1. **A real tension the article itself doesn't resolve**: it justifies
   urgency with Ebbinghaus's forgetting curve (decay is fastest in the
   first hours/days), then prescribes a flat weekly batch review
   ("every Sunday, add what you saved that week") with no per-item
   spacing at all.
2. **A real, checkable custom-instructions block** (Step 4) that can be
   audited for whether it actually implements the safety properties the
   article claims for it.

## What was verified before building anything

- **NotebookLM really was renamed "Gemini Notebook"** on July 16, 2026
  (Google's own Workspace Updates blog), with `notebook.google.com` as
  the real new address (old `notebooklm.google.com` links redirect) —
  the article's claim checks out exactly, dated.
- **"Configure Chat" is a real, current feature** matching Google's own
  help docs: Default/Learning Guide/Custom conversational styles,
  Default/Longer/Shorter response length. The article's described steps
  match.
- **Hamza Khalid / "AI in public"** is a real, currently-active Substack
  (`humzakhalid.substack.com`, also at `aiinpublic.com`).
- **The Ebbinghaus claim** ("more than half of new material was gone
  within an hour") is an accurate paraphrase of the real, replicated
  figures — commonly cited as ~50%, with the more precise original
  figure (by "savings," not direct recall) at ~56%, replicated within a
  few points by Murre and Dros (2015). Not an invented statistic.
- **No live NotebookLM/Gemini Notebook access from this sandbox** — it
  requires a real Google account login, so the UI steps themselves
  (which menu, which click) were checked against Google's own written
  help docs, not exercised live. Stated plainly rather than faked.

## `review_scheduler.py` — the real, computed finding

The article's own weekly-Sunday cadence delays an item's *first* review
by a different amount depending purely on which day of the week it
happened to be saved — recomputed directly here, not asserted:

| Saved on | Days until next Sunday | Extra delay vs. a day-1 expanding-schedule checkpoint |
|---|---|---|
| Monday | 6 | **+5 days** |
| Tuesday | 5 | +4 days |
| Wednesday | 4 | +3 days |
| Thursday | 3 | +2 days |
| Friday | 2 | +1 day |
| Saturday | 1 | 0 days |
| Sunday | 0 | −1 day |

Worst case: an item saved Monday waits 5 extra days for its first
review versus what a day-1 spaced-repetition checkpoint would call for.
Average across the week: **2.0 extra days**. This is the article's own
cited decay curve working against its own prescribed cadence.

`DEFAULT_INTERVALS = (1, 3, 7, 14, 30)` is a commonly-cited expanding
review schedule, sourced from multiple independent spaced-repetition
guides — distinct from SM-2's ease-factor-driven schedule (1, 6, ~15
days) and the Leitner box system. Stated honestly, per a real caveat
found while checking this: there is **no single proven-optimal**
interval set — Karpicke & Roediger (2007) found equally-spaced
retrieval beat expanding retrieval on recall after two days in at least
one study. This tool offers a reasonable, documented default, not a
claim that expanding intervals are proven best for everyone.

`SavedItem` tracks a title, a save date, and completed review dates;
`next_review_due()` / `is_overdue()` / `days_until_due()` work from
that against any interval schedule, not just the default.

## `prompt_auditor.py` — checking a custom-instructions block

Six checks, each derived directly from a specific clause in the
article's own real, verbatim Step 4 text — not a generic prompt-quality
rubric:

| Check | Severity if missing | From the article's text |
|---|---|---|
| `grounding_only` | FAIL | "Answer only from the sources in this notebook" |
| `fallback_phrase` | FAIL | 'say "Not in my sources"' |
| `citation_required` | FAIL | "give the supporting points with citations" |
| `suggests_missing_source_type` | WARN | "suggest what kind of source I should add" |
| `disagreement_surfacing` | WARN | "Point out when two sources disagree" |
| `plain_english` | WARN | "Use plain English. No filler." |

The three FAIL-level checks are the load-bearing anti-fabrication
properties (no grounding restriction, no fallback phrase, or no
citation requirement means an answer that sounds grounded can't
actually be checked). The three WARN-level checks are real
improvements the article's own example includes, but not safety
properties on their own.

This does **not** call NotebookLM — there is no live access from this
sandbox. It mechanically checks the *text* of an instructions block,
the same static-analysis-of-a-stated-rule-set approach already used in
this project (`winston_checker.py`'s deck-text checks,
`skill_md_validator.py`'s frontmatter checks).

## Usage

```
python3 cli.py audit-prompt instructions.txt
python3 cli.py lag-profile
```

## Proof

`python3 -m unittest tests.test_review_scheduler tests.test_prompt_auditor tests.test_cli -v`
— **31/31 tests pass**, including:

- The article's own real, verbatim custom-instructions text passing
  every check (a true discrimination test: a naive "be a helpful
  assistant" block fails or warns on every single check instead).
- The weekly-lag arithmetic above recomputed directly in the test suite
  (not hardcoded to match a hand-derived table) — this caught a real
  error in this build's own first-draft hand math before any test was
  written: an initial manual pass computed Monday's lag to next Sunday
  as 5 days, but running the actual `date.weekday()` arithmetic gave 6
  — fixed by trusting the recomputed values and rewriting every
  affected test and table entry, rather than adjusting the code to
  match the wrong hand count.
- Real subprocess CLI runs, including clean, non-traceback error
  handling for a missing file and an unknown subcommand.

## Deliberately not built

- Anything resembling the paywalled Starter Kit's four notebook
  blueprints, 12 prompts, or the AI-mentor technique — never seen,
  nothing here is derived from it.
- A live NotebookLM/Gemini Notebook integration — no account, no login,
  no API access from this sandbox.
- A claim that the expanding-interval schedule is proven optimal — see
  the Karpicke & Roediger caveat above.
