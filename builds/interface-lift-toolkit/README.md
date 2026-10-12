# interface-lift-toolkit

A real, standalone implementation of "interface lifting" — adapted from
an uploaded article, "Building Fast Computer Agents to Solve Complex
Tasks" (Fareed Khan). Full critical analysis in
`/notes/interface-lifting-fast-computer-agents-analysis.md`. The article's
core argument: screenshot-driven computer-use agents pay six real costs
(a model call per click, a picture in every call, blind waiting for the
UI, losing the screen, learning nothing between runs, errors surfacing
late); four of those six are properties of the *interface*, not the
model, so the fix is giving the model typed tools that drive each
program's own native interface instead of its screen.

This build is the generalizable architecture *for real*, demonstrated
against real, already-proven functions already in this project
(`prop_firm_sizing.py` / `prop_firm_position_sizing.py` /
`prop_pass_simulator.py`, copied here unmodified — same convention
`/builds/trading-jarvis/` and `/builds/prop-firm-mcp-server/` already
follow) — not toy stand-ins, and not the article's own specific 118-
Windows-program instance (see "What's cut, and why" below for exactly
why that part doesn't transfer to this sandbox).

## What's built

| Module | What it does | Adapted from |
|---|---|---|
| `toolkit/registry.py` | `@tool(effect=...)` decorator; derives a JSON schema from a function's type hints + docstring | `toolkit/registry.py` |
| `toolkit/result.py` | `{ok, summary, files, checks}` — `ok` is always derived from `checks`, never set by hand | `toolkit/result.py` |
| `toolkit/shortlist.py` | regex-scored tool-group selection (clear winner vs. top-N fallback) | `toolkit/shortlist.py` |
| `toolkit/chain.py` | `run_chain` — one model call plans several dependent tool calls, `"$id.field"` references resolve between steps | `toolkit/chain.py` |
| `toolkit/approval.py` | the local/outward gate — an outward call is held until explicitly, single-use approved | the article's `effect="outward"` + `post_file` pattern |
| `toolkit/skill_compiler.py` | turns one successful `run_chain`-shaped run into a new, directly-callable, parametrized tool | the article's skill compiler |
| `toolkit/ledger.py` | per-task `{model calls, tool calls, UI actions, tokens, seconds, checks}` row | `speed_ledger.py` |
| `toolkit/loop.py` | `run_agent` — the actual tool-use loop, in Anthropic's real message shape | `toolkit/loop.py` |

Deliberate adaptations, not blind copies:

- **Schemas are Anthropic's native tool-use shape**
  (`{"name", "description", "input_schema": {...}}`), matching
  `/builds/trading-jarvis/jarvis_orchestrator.py`'s already-established
  `TOOLS` convention — not the article's OpenAI-shaped `{"parameters": {...}}`
  — so a tool registered here drops straight into a real
  `client.messages.create(tools=...)` call with no translation step.
- **One `ToolRegistry` instance per agent**, not a module-level global
  dict, so a test and a real app never collide on the same tools.
- **The skill compiler works one layer down from the article's.** The
  article compiles a *screen-agent run* — concrete UI-tree locators and
  literal values become typed placeholders. There's no screen loop here
  to compile from (see below), so this version compiles from a recorded
  `run_chain`-shaped `steps` list instead: name which literal argument
  values should become parameters, and get back a new tool that replays
  the same chain with them substituted in. Same mechanism (one successful
  concrete run becomes a reusable, parametrized tool); different layer,
  because that's the layer this toolkit actually operates at.

## What's cut, and why — stated plainly, not silently narrowed

The article's specific instance is 118 Windows desktop-program
integrations: Photoshop PSD writing, Excel via COM, AutoCAD via DXF,
Blender in background mode, CapCut/JianYing automation, UI Automation
accessibility-tree driving. **None of that was built here.** Not because
it was out of scope to try, but because every one of those programs is a
Windows GUI application — Photoshop, Excel's COM interface, AutoCAD,
Blender's Windows build, CapCut — and this sandbox is a headless Linux
cloud container with none of them installed and no way to install them
(Windows-only COM/UI-Automation APIs don't exist on Linux at all). That's
a platform mismatch, not a scope cut made out of laziness, and it's the
same honest limitation this project has stated for live Yahoo
Finance/EODHD/FMP/Anthropic network access in every other build here —
said plainly rather than faked or silently worked around.

What *is* directly transferable, and was built: the registry, the result
contract, shortlisting, chain planning, the approval gate, the ledger, and
the skill compiler — none of that is Windows-specific or GUI-specific; all
of it operates one layer above "which interface the tool happens to
drive." Demonstrated against this project's own already-proven,
native-interface (pure Python, no GUI, no screenshot) prop-firm-sizing
functions, which already are the kind of thing the article argues for —
a program's actual computation, called directly, with a checked result
instead of a picture.

## Verification — real tests, not just "it imports"

### `test_toolkit.py` — the mechanics, no network needed

```bash
python3 test_toolkit.py
```

Real output from this build:

```
=== registry: schema derivation ===
  [PASS] schema name matches function name
  [PASS] tier/symbol typed as string, contracts as integer
  [PASS] all three params required (no defaults)
  [PASS] docstring became the description

=== result(): ok is derived from checks ===
  [PASS] all-true checks -> ok=True
  [PASS] one false check -> ok=False

=== prop_firm_size_check matches evaluate_size() directly ===
  [PASS] tool output matches direct evaluate_size() call

=== shortlist_groups ===
  [PASS] a clear winner returns exactly one group
  [PASS] no signal hits returns an empty list

=== run_chain: $id references resolve between steps ===
  [PASS] chain of two independent steps both ran and succeeded

=== run_chain: stops at the first failed check ===
  [PASS] chain reports ok=False and names the failed step
  [PASS] the second step never ran

=== run_chain: outward tool holds for approval, then runs once approved ===
  [PASS] unapproved outward call is held, not executed
  [PASS] approved outward call actually runs
  [PASS] approval is single-use (re-running without re-approving holds again)

=== skill compiler: compile a chain, then replay it with new params ===
  [PASS] compiled skill registered as a new tool
  [PASS] compiled skill replayed with contracts=3 matches a direct call with the same args
  [PASS] missing required param raises TypeError naming it

=== ledger ===
  [PASS] ledger renders the recorded row

============================================================
ALL CHECKS PASSED
```

Every numeric assertion against the demo tools checks the toolkit's
output against a **direct call to the same underlying prop-firm-sizing
function** — same discipline as
`/builds/prop-firm-mcp-server/test_client.py` — so a pass proves the
toolkit is a faithful, non-lossy wrapper, not just that it runs.

### `test_agent_loop.py` — the real dispatch loop, mocked Anthropic client

This sandbox has no live Anthropic API access (same restriction stated
for `/builds/trading-jarvis/` and `/builds/prop-firm-mcp-server/`), so
`run_agent` is proven against a mocked `client.messages.create` that
returns a scripted tool-use turn, exactly matching this project's
established mocking pattern for tool-dispatch loops. What's real: the
registry really dispatches to the real `prop_firm_sizing` code, the
approval gate really holds the outward call, and the messages list is
really built up the way the real loop builds it.

```bash
python3 test_agent_loop.py
```

```
=== run_agent: a local tool call, then a final answer ===
  [PASS] final answer is the scripted text
  [PASS] exactly 2 model calls were made (matches the 2 scripted responses)
  [PASS] exactly 1 real tool call was made
  [PASS] the real tool result (not a stub) was fed back to the model

=== run_agent: an outward tool call is held, never executed inline ===
  [PASS] an outward call makes zero real tool calls (held, not executed)
  [PASS] the held call's own pending preview came back, not a stub error
  [PASS] the file was NOT actually written (approval was never granted)

============================================================
ALL CHECKS PASSED
```

## Using it for real

```python
from toolkit.approval import ApprovalGate
from toolkit.ledger import TaskCounters
from toolkit.loop import run_agent
from toolkit.registry import ToolRegistry
from tools_demo import register_demo_tools
import anthropic

registry = ToolRegistry()
gate = ApprovalGate()
register_demo_tools(registry)

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
counters = TaskCounters()
answer = run_agent(
    "check sizing for 2 ES contracts on a 100K TPT account",
    client, "claude-opus-5", registry, gate, counters=counters,
)
print(answer)
```

An outward tool (like the demo's `publish_report`) comes back as a
`{"pending": {...}}` preview on the first ask; call
`gate.approve(tool_name, args)` with the exact args from that preview,
then run the same request again to actually execute it.
