# Agent Readiness Scorecard

A real, runnable, vendor-neutral scorer inspired by Factory.ai's
**Autonomy Maturity Model (AMM)** white paper. Built from
`/notes/software-factory-autonomy-maturity-model-analysis.md` — read that
first for what the source framework actually says, what's unsourced in
it, and why this tool deliberately doesn't try to reproduce Factory.ai's
own (undisclosed) exact scoring rubric or any of their branded products
(Droid, Squads, Missions, etc.). Same move this project made with Build
Brain method: take the generalizable structure from an uploaded vendor
artifact, leave the vendor's own branded instance unbuilt.

## What it measures

Binary, locally-checkable signals across three levels (Level 4/5 from the
source framework are operational telemetry — sub-minute feedback loops,
auto-picked-up tickets, multi-day mission reliability — and genuinely
can't be seen from files on disk, so this tool doesn't fake them):

| Level | Points/signal | Cumulative threshold | Signals checked |
|---|---|---|---|
| 1 — Functional | 1 | 5 | README, linter config, type-checker config, formatter config, unit tests exist |
| 2 — Documented | 2 | 19 | AGENTS.md/CLAUDE.md, reproducible dev env, pre-commit hooks, documented build command, branch protection *(unknown — not checkable locally)*, structured logging, CODEOWNERS |
| 3 — Standardized | 4 | 36 | Integration/E2E tests (>1 test file), docs updated in the last 30 days, security-scanning config, observability/tracing library, CI workflow config |

Signal checks are plain file-system/regex inspection — no network calls,
no GitHub API, runs in well under the source paper's own "five minutes
per repository" bar.

## Run it

```bash
python3 score_repo.py [REPO_PATH]       # rendered scorecard (default: current dir)
python3 score_repo.py [REPO_PATH] --json
```

## Real output — run against this repo

```
$ python3 score_repo.py .
Agent Readiness Scorecard — gdp-dashboard
============================================================
Score: 14 pts (of 37 assessable from this checkout) -> Level 1 (Functional)

Level 1 signals (1 pt each, threshold 5 pts cumulative):
  [x] README present
  [ ] Linter configured
  [ ] Type checker active
  [ ] Formatter standardized
  [x] Unit tests exist

Level 2 signals (2 pt each, threshold 19 pts cumulative):
  [x] AGENTS.md / CLAUDE.md present
  [x] Reproducible dev environment config
  [ ] Pre-commit hooks configured
  [x] Build/run command documented
  [?] Branch protection enabled  (not checkable from a local clone)
  [ ] Structured logging in use
  [x] CODEOWNERS present

Level 3 signals (4 pt each, threshold 36 pts cumulative):
  [ ] Integration/E2E tests (beyond one test file)
  [x] Docs updated within the last 30 days
  [ ] Security scanning configured
  [ ] Observability/tracing library in use
  [ ] CI workflow configured
```

**Read honestly, not mechanically**: this repo scores Level 1 (14/37
assessable points), and that's an accurate reflection of what's actually
here — not a verdict that the work in it is low quality. This repo is a
business-strategy + multi-build workspace (a dozen independent, often
Windows-targeting or client-side-only `/builds/` subprojects), not a
single deployable service. It has no repo-wide linter/type-checker/CI
because it was never built as one codebase — `requirements.txt` at the
root (`streamlit`, `pandas`, unpinned) only serves the one top-level
`streamlit_app.py`; every other build pins its own dependencies
separately. The AMM's assumptions (one service, one CI pipeline, one test
suite) don't fit a workspace shaped like this one, and the scorer
reports that mismatch plainly rather than letting a low number imply
something false.

`CLAUDE.md` is counted as satisfying the "AGENTS.md" signal — same role,
different filename, and genuinely more detailed than a typical AGENTS.md
in this project's case.

## Also run against a single `/builds/` subproject

The scorer works on any path, so it's just as useful pointed at one
subproject instead of the whole repo:

```
$ python3 score_repo.py ../recovery-desk
Agent Readiness Scorecard — recovery-desk
============================================================
Score: 4 pts (of 37 assessable from this checkout) -> Level 0 (Below Level 1)
...
  [x] Unit tests exist
  [x] Build/run command documented
```

Lower still — expected, since this scorer's L1/L2 signals mostly target
repo-root concerns (CODEOWNERS, a root AGENTS.md/CLAUDE.md, a
`.devcontainer/`) that a build subfolder was never meant to carry on its
own. Worth noting as a real limitation of applying a repo-level framework
one directory at a time, not silently smoothed over.

## Known limitations (stated, not hidden)

- **Branch protection is always `unknown`.** It requires GitHub API
  access with repo admin scope, not a local file. Reported distinctly
  from a `fail`, never silently counted as passing or failing.
- **Structured logging / observability checks are heuristic regex
  scans** (`logging.getLogger(`, `opentelemetry`, etc.) — they can miss
  real usage behind an unusual import style, or false-positive on a
  commented-out import. Treat a `fail` here as "worth a human glance,"
  not gospel.
- **Docs-freshness is a 30-day git-log proxy**, not true
  code-vs-docs-drift detection (the source paper's actual "documentation
  freshness above 90%" signal implies something more precise that isn't
  derivable from a static checkout).
- **This is not Factory.ai's scorer.** Their exact signal set and point
  totals per pillar aren't published in the source white paper (see the
  notes analysis) — this tool's signal choices are original, designed
  for what a static checkout can actually show, and the level thresholds
  (5/19/36/60/100) are the only numbers taken directly from their paper.

## Verification

Run for real against three different scopes in this sandbox, output
captured above and cross-checked by hand against the actual repo state
(confirmed no `.flake8`/`ruff.toml`/CI workflows exist here before
trusting the `fail` results, confirmed `CLAUDE.md` and
`.github/CODEOWNERS` really do exist before trusting the `pass` results):
this repo root, the `recovery-desk` subproject, and `--json` mode (valid
JSON, matches the rendered output). Also verified clean error handling
on a nonexistent path (`exit code 1`, message to stderr, no traceback).
