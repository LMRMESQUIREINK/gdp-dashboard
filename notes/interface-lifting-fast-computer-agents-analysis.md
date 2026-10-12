# Deep analysis: "Building Fast Computer Agents to Solve Complex Tasks" (Fareed Khan)

Source: an uploaded Medium-style article walking through "ai-pc," a Windows
desktop agent that replaces screenshot-driven GUI automation with typed
Python tools ("interface lifting") across ~118 desktop programs
(Photoshop, Excel, AutoCAD, Blender, CapCut, Slack, etc.), with a linked
public GitHub repo. Unlike the Factory.ai Autonomy Maturity Model paper and
the production-grade-MCP-server article analyzed earlier in this project,
this one shows real code for nearly every claim — that's a materially
stronger evidentiary bar, and the critique below reflects that: most
findings are about what's unverifiable or cherry-picked in the *measurement*,
not about invented mechanisms.

## What it actually argues

The core claim: computer-use agents that work from screenshots pay six
real costs — (1) a model call per click, (2) a picture in every call's
input, (3) blind waiting for the UI to settle, (4) the agent needs the
visible screen, (5) nothing learned carries to the next run, (6) errors
surface late because a screenshot can't prove a number is right. Four of
those six are properties of *the interface*, not the model, so a better
model doesn't fix them — only giving the model a different interface does.
"Interface lifting" is that different interface: wrap each program feature
as a typed Python tool that drives the program through whatever native
channel it already has (its own file format, CLI, COM/scripting, API, and
only last its accessibility tree), return a checked, few-hundred-token JSON
result instead of a picture, and compile a task that worked once into a
new, instantly-replayable tool ("skill compiler").

## The architecture, in one line each

- **Tool registry** (`toolkit/registry.py`) — a `@tool()` decorator reads a
  plain function's type hints and docstring into a JSON schema; no tool is
  hand-written twice.
- **Result contract** (`toolkit/result.py`) — every tool returns
  `{ok, summary, files, checks, ...}`; the model only ever sees this, never
  a screenshot.
- **Five native interfaces, in preference order** — a program's own file
  format, its CLI, its COM/scripting interface, its official API, and only
  last its accessibility tree (UI Automation) with raw pixels as the final
  fallback.
- **Agent loop** (`toolkit/loop.py`) — a standard tool-use loop: model
  decides, tool executes, result goes back as text, repeat until the model
  answers or `max_turns` is hit.
- **Shortlisting** (`toolkit/shortlist.py`) — a cheap regex scorer picks
  which tool-schema *groups* go into a given prompt, so a 200+-tool agent
  doesn't pay ~36,000 schema tokens on every call.
- **Chain planning** (`toolkit/chain.py`, `run_chain`) — the model writes a
  whole dependent sequence of tool calls in one call, with `"$id.field"`
  references resolved between steps, instead of paying a round trip per
  tool.
- **Approval gate** — tools are tagged `effect="local"` or `effect="outward"`;
  outward tools (anything another person will see — a Slack post, a sent
  email) always stop for a human "yes" before they run.
- **Skill compiler** — a successful run's concrete steps get its literal
  values turned into named placeholders and the whole thing registered as a
  new tool, so the same task next time is one call instead of a re-explored
  sequence.
- **A ledger + an ablation** — one row per task (model calls, tool calls, UI
  actions, tokens, seconds, checks passed), and a priced breakdown of what
  removing each design choice would cost.

## What's genuinely well-reasoned here

- **The tool contract is the right shape.** Schema / implementation /
  verifier / effect, with the verifier *mandatory* and the effect tag
  deciding whether a human gate applies, is a clean, enforceable discipline
  — and the article shows it being enforced: `compose_layered_image`'s
  verifier reopens the saved PSD with a library that knows nothing about
  the writer and checks layer names, boxes, and the flattened pixels;
  `build_workbook`'s verifier has Excel itself recalculate every formula
  and compares the result to an independent Python computation of the same
  expressions. This is the same discipline this project's own MCP-server
  build landed on independently last round (SERF-lite's checks, the
  `test_client.py` pattern of comparing an MCP call's output against a
  direct call to the same underlying function) — seeing it re-derived from
  a completely different source is a point in its favor, not a coincidence
  worth distrusting.
- **The five-interfaces-in-order list is a real, checkable claim, not a
  slogan.** "A program's own file format beats its CLI beats its COM
  interface beats its API beats its accessibility tree" is falsifiable
  per-program, and the article backs it with a citation that's itself
  checkable in principle: "for 15 of ScreenSpot-Pro's 23 programs, one of
  [the first four] interfaces exists." I can't re-run ScreenSpot-Pro from
  inside this sandbox to confirm 15/23, but the claim is specific enough
  that it's a real, falsifiable number rather than a vibe — different in
  kind from the Factory.ai paper's unsourced "+10% overall" claim analyzed
  two rounds ago in this project.
- **The approval gate's reversibility reasoning is sound and specific.**
  Slack uploads get `undo` because a wrong upload can be deleted; email only
  ever produces a Gmail *draft*, with sending gated behind a second "yes,"
  because "a wrong email cannot be unsent." That's reasoning about the
  actual cost of being wrong, not a blanket "ask permission for everything"
  rule — the same category of judgment this project's own git-safety rules
  apply (force-push and history rewrites need explicit asks; routine
  commits inside an already-granted scope don't).
- **The safety classifier example is a real, well-chosen illustration of a
  genuine attack surface** (prompt injection via on-screen text instructing
  the agent to "press Delete all files") — correctly treated as a
  code-level check, not something the model is trusted to catch on its own,
  which matches the general principle this project's own `jarvis_swamp_bridge.py`
  Swamp Intelligence layer already encodes: hard-code the gate in code,
  never just in a system-prompt instruction.
- **The shortlist scorer's actual numbers are shown, not just claimed**: a
  concrete two-run contrast (`'a 10 marla house ... send it to slack #team'`
  → 3 groups, 19 tools, 3,240 schema tokens vs. all groups → 36,000 tokens)
  is reproducible from the regex table given in the article. That's a
  verifiable mechanism, unlike the article's closing claim of "180 of 180"
  on "over 40 programs," which is asserted with no test list, no repo path,
  and no way to check it from the pasted text (see below).

## What doesn't check out, or can't be checked from here

- **The entire quantitative case rests on one anecdotal baseline.** Every
  "faster than the screen agent" comparison in the ledger is measured
  against a *single* run of the author's *own, admittedly early* screen
  agent on *one* task (the 1 October CapCut run: 32 steps, 13 model calls,
  155 seconds, failed). That's not a controlled baseline — it's one
  attempt by a weak, self-built comparison system, and the article's own
  second CapCut retry ("worse than the first, 20 model calls and 253
  seconds") shows how much this single-run number can vary. A "screen
  agent" that's deliberately early and admittedly struggling is an easy bar
  to clear; the article doesn't cite or build a stronger GUI-automation
  baseline (e.g., a maintained framework like UFO2, which it does cite
  elsewhere, is never actually run side-by-side here) to compare against.
  The six-costs framing *is* independently supported by cited external
  research (OSWorld-Human, ScreenSpot-Pro, the OSWorld window-resize
  finding), so the *qualitative* argument stands on more than the one
  anecdote — but the specific speedup numbers in the ledger (2.9s vs.
  implied ~tens of seconds, 4.4s for a house plan, etc.) are each a
  single run against a single weak baseline, not a distribution.
- **The headline ledger is a curated set of best-case rows, with no
  variance or failure rate shown for the *new* system.** All thirteen
  "tool loop" rows in the final ledger pass every check listed next to
  them. There's no row (for the new architecture) showing a failed run, a
  wrong tool pick, or a check that caught a real mistake *during* normal
  operation — the only failure shown anywhere is the old screen agent's.
  "Known Limits" admits real gaps exist (wrong tool/argument choices,
  checks that "prove numbers, not meaning" — the marks-sheet example
  explicitly flags two uncaught slips), which is honest, but none of those
  admitted failure modes get a ledger row with a real number attached, so
  there's no way to tell from the article how often they actually occur.
- **"My test suite runs over 40 of these programs for real and passes 180
  of 180" is exactly the shape of claim this project has learned to flag
  on sight** (same pattern as the Factory.ai paper's unreadable "Outcomes
  from enterprise deployments" chart, and the MCP-server article's uncited
  "~40% reduction in erroneous tool calls"): a specific, confident number
  with zero supporting detail — no list of the 40 programs, no test file,
  no repo path, nothing checkable from the pasted text. The linked GitHub
  repo may well contain this suite; nothing here claims it doesn't. But
  *from what was pasted*, 180/180 is asserted, not shown, and this writeup
  doesn't repeat it as a verified fact for the same reason it didn't repeat
  the MCP article's uncited Asana-leak claim as fact last round.
- **The "OSExpert... closes about 80% of that gap" claim is a citation
  stacked on a citation this document can't trace.** It's presented to
  support the skill compiler's value, but neither the "5 to 50 times
  longer than human experts" figure nor the "80%" closure number has a
  reachable source in the pasted text. Treated here as an unverified
  external citation, not evidence this writeup can independently confirm.
- **The video-edit row's "57 asks met, 21 partly met, none missed" has no
  stated rubric.** "Partly met" is doing real work in that sentence (21 out
  of 78 total asks, over a quarter) and the article never defines what
  separates "met" from "partly met," unlike every other row's checks,
  which are at least named ("Premiere XML: every clip, ending at the
  sequence's length").
- **Ground-truth comparisons are against the system's own expectations,
  which is weaker than it first appears.** The workbook verifier compares
  Excel's recalculation against a *Python* computation of the same
  formula — a real, valuable check that catches a formula Excel can't
  evaluate, but it cannot catch the case where the *plan itself* encodes
  the wrong formula (exactly the marks-sheet "Students Passed counts grade
  F" slip the article itself names as an uncaught bug). The architecture's
  real strength is "catches whether the file matches the plan," not
  "catches whether the plan is right" — worth keeping separate, and the
  article does keep them separate in "Known Limits," which is to its
  credit, but the ledger's "checks: 19/19," "17/17," etc. columns read at
  a glance like a correctness score rather than a plan-fidelity score.

## What this project already has that overlaps with this article

- `/builds/prop-firm-mcp-server/` (built two rounds ago) is already a
  working instance of "interface lifting," independently arrived at: every
  MCP tool there drives a native Python interface (no GUI, no screenshot),
  returns a checked result, and the project's own `test_client.py`/
  `test_http_client.py` compare tool output against a direct call to the
  same underlying function — the same "verifier reopens the output and
  checks it against ground truth" move `compose_layered_image`'s PSD
  verifier makes in this article. The gap, relative to this article, is
  that the MCP server's `ToolError`/SERF-lite framework has no equivalent
  to `effect="outward"` + a held-for-approval preview — every MCP tool
  there is "local" by nature (it only computes a number), so there was
  never a reason to build the gate. This round's build (below) adds that
  piece as a standalone, reusable primitive rather than retrofitting it
  onto a server that doesn't need it yet.
- `jarvis_orchestrator.py`'s `ask_jarvis()` loop already *is* a tool-use
  loop in the shape `toolkit/loop.py` describes, built for this project
  independently and earlier.

## What was built from this (see `/builds/interface-lift-toolkit/README.md`)

Per this project's established pattern (same move as Build Brain method
from the RUTHLESS AFFILIATE GOLD export, and the Agent Readiness
Scorecard from the Factory.ai paper): the article's *generalizable
architecture* was built for real; its *specific instance* (118 Windows
desktop-program integrations — Photoshop, AutoCAD, Blender, Excel COM,
CapCut/JianYing, UI Automation) was not, because none of those programs
exist, nor can exist, in a headless Linux cloud sandbox. What's missing
here is a platform mismatch, not a scope cut made out of laziness — stated
plainly rather than silently worked around. Built instead: the registry +
schema-derivation decorator, the result/checks contract, the shortlist
scorer, chain planning with `$id` references, the local/outward approval
gate, the ledger, and — the piece with the most standalone value — a real
skill compiler that turns a successful tool-call chain into a new,
directly-callable tool. All demonstrated against real, already-proven,
native (non-GUI) functions already living in this repo
(`prop_firm_sizing.py` / `prop_firm_position_sizing.py` /
`prop_pass_simulator.py`), not toy stand-ins.
