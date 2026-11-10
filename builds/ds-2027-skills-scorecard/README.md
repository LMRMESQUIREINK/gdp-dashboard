# ds-2027-skills-scorecard

A real, dependency-free Python scorer for the 9-skill rubric from "Data
Science Is Changing. These Are the Skills I'd Learn in 2027" (Codebook
Fusion, Medium) — see `/notes/ds-2027-skills-analysis.md`. Same move as
`/builds/agent-readiness-scorecard/` (Factory.ai's Autonomy Maturity Model)
and `/builds/ten-k-website-grader/` (the "$10K Websites" 8-pillar
checklist): turn a source's own checklist into an actual, locally-checkable
self-check rather than trusting a self-report.

## What it checks, and what it honestly can't

The article's 9 skills split into two groups:

- **File-observable (6 skills, real checks)**: Python/SQL and testing (2),
  LLM/RAG/agent usage (3, heuristic), evaluation harnesses (4, heuristic),
  data engineering (5), MLOps/deployment (6), responsible AI/governance (8).
- **Not file-observable (3 skills, always reported `not_assessable`)**:
  problem framing (1), communication/storytelling (7), domain knowledge (9)
  — these are about judgment and audience, not something a directory
  listing can prove or disprove. Same discipline as
  `agent-readiness-scorecard`'s Level 4/5 operational-telemetry signals and
  `ten-k-website-grader`'s "point of view" pillar.

Two of the six real checks (LLM/agent usage, evaluation harness) are
explicitly labelled **heuristic**: keyword or filename-pattern presence,
not a verified capability. A file that imports `anthropic` and calls
`vector_store.search()` proves someone *wrote code that mentions* RAG, not
that the system works or is evaluated well — stated plainly in the tool's
own output, not just in this README.

## A real bug found and fixed during this round, not a synthetic one

Running the first draft against this project's own repo (which genuinely
contains this tool) reported a false `PASS` on the data-engineering skill,
with evidence pointing at `ds_skills_scorecard.py` itself. Traced to two
sources: (1) the module's own `airflow_pattern` regex literally spells
`"from airflow"`/`"import airflow"` in its source line — exactly the
`ruthless-gate` skill's documented pitfall, "a detector that scans its own
file cannot spell its own pattern"; (2) this build's own test fixture
(`test_airflow_dag_satisfies_data_pipeline_skill`) writes that exact string
as deliberate fixture content, which becomes a false positive the moment
the *whole containing repo* — including this tool's own test file — gets
scanned.

Fixed with `exclude_self` (on by default, `--include-self` to override):
any scan excludes the directory this script lives in. This is the general,
correct fix — not a narrower regex, which would only have patched the one
symptom found this round and left the same class of bug waiting for the
next self-matching keyword. `test_exclude_self_fixes_a_real_self_matching_bug_found_during_this_round`
proves the bug was real (reproduces it with `exclude_self=False`) before
proving the fix removes it.

**A second correction, made honestly rather than forced**: this round's
first test draft assumed the data-engineering skill should read `fail`
against this repo, having checked only for literal Airflow/dbt markers
(there are none). Running the actual tool surfaced two real, legitimate
pipeline modules this project already has
(`builds/trading-jarvis/data_pipeline.py`,
`builds/recovery-desk/data_pipeline.py`, both with real fetch/clean/
validate-shaped functions per their own READMEs) via the tool's separate
pipeline-file fallback check — a correct `pass`, not a bug. The test was
corrected to match the verified truth rather than the tool's output
adjusted to force the original wrong assumption, same discipline as
`/builds/paired-bootstrap-ratchet/`'s own mid-build test corrections.

## The evaluation-harness heuristic's real, named narrowness

Spot-checked by hand against this repo rather than assumed: the heuristic
requires a file (not a directory) whose own name contains eval/benchmark/
fixture/golden/ground_truth AND contains an assertion-like pattern. This
repo has several `fixtures`/`evaluation` *directories* (correctly not
file-matched) and one real file, `policy-control-plane/policy/evaluator.py`
— which genuinely contains zero `assert`/`expect(`/`toEqual`/`toBe`
occurrences (it's production policy-evaluation code, not a test harness),
confirmed with a direct `grep -c` before trusting the tool's `fail`
verdict. The heuristic is narrow by design, not broken.

## What was found about the article itself

See `/notes/ds-2027-skills-analysis.md` for the full write-up. The
headline finding: the article's own "9 Skills I Would Learn in 2027" list
never names classical machine learning as one of the 9 skills (Skill 1's
intro even argues the first question has shifted away from "which
algorithm should I train"), yet the 12-month roadmap devotes two full
months to "Core machine learning. Regression, classification, and tree
models," and the FAQ explicitly answers "Learn the basics of classical
machine learning first" — treating it as foundational, prerequisite
material throughout the piece while never naming it in the list that's
supposed to be "roughly... by return on time invested."

## Proven

```
python3 -m pytest test_ds_skills_scorecard.py -v   # 10/10 passing
python3 ds_skills_scorecard.py /path/to/a/repo
```

10/10 tests pass, including a discrimination pair (a synthetic fixture
with real signal for every assessable skill passes all six; a bare script
whose README literally names the three *not-assessable* skills by word
fails all six real checks and stays `not_assessable` on the other three,
proving the tool checks real structure, not keyword-matching against the
rubric's own skill names), the self-matching bug reproduced and then
proven fixed, and a real run against this project's own repo with every
result spot-checked by hand against `find`/`grep` ground truth before the
test was trusted.

## What's deliberately not built

- A check for skill 3 (LLM/agent usage) that verifies the code actually
  *works*, as opposed to merely importing the right libraries — that would
  need to run the code, which this project's standing no-live-API-key
  restriction rules out for most real LLM pipelines anyway.
- A true semantic check for skills 1/7/9 — stated as structurally
  impossible from files alone, not a scope cut to revisit later.
