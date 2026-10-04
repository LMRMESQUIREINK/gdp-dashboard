# Deep analysis: "Software Factory — An Autonomy Maturity Model for the Enterprise"

Source: uploaded PDF, `Factory.ai`, 16 pages. Full text extracted locally
(pypdf — `poppler-utils` wasn't available in this sandbox, so `pdftotext`
couldn't be used; `pip install pypdf` + `cffi` worked cleanly instead, and
is the honest record of how this was actually read, not assumed).

## What the paper actually is

A vendor white paper from **Factory.ai**, maker of an agentic coding
product line (Droid CLI/Desktop, Droid Computers, Squads, Missions,
Triage, Code Review, /incident, AutoWiki, Security Review/DroidShield,
QA, Router, Analytics). It proposes the **Autonomy Maturity Model (AMM)**
— a framework for scoring how "agent-ready" a codebase/organization is —
and ends on page 16 with "GET STARTED… CONTACT SALES." This is marketing
collateral with a genuinely well-structured framework inside it, not a
neutral research paper — worth saying plainly before treating any of its
specific numbers as established fact, same discipline this project
already applies to every uploaded "analysis" HTML/PDF.

## The framework, as stated

- **Two dimensions**: (1) **Eight Pillars** — the technical foundation:
  Style & Validation, Build System, Testing, Documentation &
  Instructions, Dev Environment & Remote Execution, Code Quality,
  Debugging & Observability, Security & Governance. (2) **Autonomous
  Processes** — the workflows that run on top: human-agent orchestration,
  triage, long-running goal agents, code review, incident response,
  documentation, security scanning, deployment, QA, model routing,
  outcome measurement.
- **Five Maturity Levels**, non-linear point thresholds: L1 Functional
  (5 pts), L2 Documented (19 pts), L3 Standardized (36 pts — **stated as
  the minimum production-grade bar**), L4 Optimized (60 pts), L5 Software
  Factory/autonomous (100 pts, "the frontier").
- **Scoring**: signals are strictly binary (present/absent, no partial
  credit), each level's signals carry escalating point values (L1=1pt,
  L2=2pts, L3=4pts, L4=8pts, L5=16pts per signal), and signals are meant
  to be automatable and fast (under 5 minutes per repo).
- **Headline metric**: *Organizational Readiness = (Repos at Level 3+ ÷
  Active Repos) × 100* — explicitly chosen over an averaged score because
  "80% of our repos are agent-ready" is more board-legible than "average
  score 73.2%."
- **DMASI**: Define → Measure → Analyze → Scale → Integrate — a
  continuous-improvement loop, structurally identical to Six Sigma's
  DMAIC with "Scale" and "Integrate" swapped in for "Improve"/"Control."
  Not presented as original; the paper doesn't claim novelty here, and
  neither should this analysis.
- **Capability Map** (pages 14–15): every capability in the model is
  mapped 1:1 to a named, paid Factory.ai product. This is the clearest
  tell that the framework, however well-structured, is built to make the
  vendor's product line look like the only complete answer to it.

## What doesn't check out / can't be verified from the text

- **The paper's own headline ROI claim is unsourced.** Page 2: "A 10×
  improvement on [code generation alone] yields only roughly a 10%
  improvement overall." No study, dataset, or methodology is cited for
  either the 10× or the 10% — it's asserted as the paper's own framing,
  not derived from shown data. Worth using as a *directionally plausible*
  argument (automating one pipeline stage bounds total throughput gains
  by Amdahl's-law-style reasoning), not as a cited fact.
  - **However, a figure chart on page 11 ("Outcomes from enterprise
    deployments… Spend maps to merged work, not tokens consumed") exists
    but is image-only** — pypdf extracted zero body text from that page
    (just the header/footer), so whatever numbers that chart actually
    shows are **not verified here** and not quoted anywhere in this
    analysis. Flagged explicitly rather than guessed at from the caption
    alone.
- **The full signal-to-point mapping isn't disclosed.** The "Five
  Maturity Levels" page lists a handful of *example* signals per level
  (e.g., L1: "README present, linter configured, type checker active,
  formatter standardized, unit tests exist" — exactly 5 signals × 1pt =
  the stated 5-point L1 threshold, which checks out). But the separate
  Eight Pillars table lists many more granular signals per pillar
  ("validation under 30 seconds," "pinned dependencies," "succeeds on
  fresh checkout," etc.) than the Level page enumerates — the complete
  signal set across all 8 pillars × 5 levels is Factory.ai's proprietary
  scoring rubric, not published in this paper. **Any reproduction of
  their exact scoring is therefore impossible from this document alone**
  — stated here so the tool built from this analysis is never
  mis-described as replicating Factory.ai's actual scorer.
- **L4/L5 signals are operational, not static.** "Sub-minute feedback,"
  "inter-task parallelization with tickets auto-picked from Linear/Jira,"
  "multi-day missions run reliably" — these require live telemetry from
  a running agent system, not anything visible in a git checkout. A tool
  that only inspects files on disk structurally cannot assess L4/L5; the
  paper doesn't claim otherwise, but it's worth stating plainly since
  it's the ceiling on what any static-analysis implementation (including
  the one built from this analysis) can ever measure.

## What's genuinely useful here, independent of the sales pitch

- **Binary, automatable signals over a subjective maturity score.** This
  mirrors this project's own `sales-page-engine` skill's best idea
  (turning a style guideline into a literal grep check) — a maturity
  model that can't be gamed by "felt sense" is more useful than one that
  can.
- **The readiness-percentage reframe** (% of repos at L3+, not an
  averaged score) is a genuinely good communication pattern, independent
  of Factory.ai's product: a portfolio of 20 repos where 3 are excellent
  and 17 untouched should not report as "62% average," since that hides
  the real distribution. Worth adopting as a pattern for this project's
  own `/builds/` portfolio if it ever needs a one-line health summary.
- **"Precision, not prevention"** (page 3): the system executes intent
  faithfully but can't rescue a bad architectural decision — judgment
  stays human, execution becomes automated. This is close to this
  project's own CLAUDE.md framing (Claude as "build agent," the person
  as the one who decides what's worth building) and worth naming as a
  shared value, not imported from this paper.

## Applied honestly to this repo (`LMRMESQUIREINK/gdp-dashboard`)

Running even a locally-checkable subset of this framework against this
actual repo (see `/builds/agent-readiness-scorecard/`) surfaces a real,
useful mismatch worth stating plainly rather than silently computing a
number that would mislead: **this repo isn't shaped like the kind of
single-service codebase the AMM assumes.** It's a business-strategy +
multi-build workspace — a dozen independent, often Windows-targeting or
client-side-only `/builds/` subprojects (Streamlit apps, static HTML
pages, standalone trading scripts), not one deployable service with a
unified test suite, CI pipeline, or branch-protection policy. Scoring it
against AMM's pillars (no CI config, no pinned `requirements.txt`, no
repo-wide linter/type-checker, tests existing in exactly one `/builds/`
subfolder) will show a low score — accurately reflecting "this isn't
engineered as a single production service," not "this project's actual
work is low quality." That distinction matters and is stated explicitly
in the scorecard tool's own output, not left for a reader to misread a
number.

## What was built from this (see `/builds/agent-readiness-scorecard/`)

Per this round's "create" instruction and this project's own precedent
(Build Brain method was generalized from an uploaded vendor wizard
export, explicitly *not* building that wizard's own branded output
["RemixForge" was never built]) — the same move here: the **generalized,
vendor-neutral structure** of the AMM (binary signals, escalating level
weights, a readiness-percentage headline metric) was extracted and built
as an independent, runnable scorer. Factory.ai's own products (Droid,
Squads, Missions, etc.) were **not** built or reproduced — only the
scoring *idea*, with an original, locally-checkable signal set designed
for this analysis (not a reproduction of Factory.ai's undisclosed exact
rubric, per the gap noted above).
