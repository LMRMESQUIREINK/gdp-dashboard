# Deep analysis: "AI Agents (07): Agentic Harness (Frameworks)"

Source: a Medium survey article (part of a self-described 100+-article series)
surveying agentic-framework vendors (Microsoft Semantic Kernel/AutoGen/Agent
Framework, Google ADK, OpenAI Agents SDK, LangChain/LangGraph, CrewAI,
Mastra) and proposing a five-layer mental model for comparing them:
Orchestration, Tools, RAG, Observability, Cloud/model ecosystem — packaged
at the end as the mnemonic "ROOTS" (RAG, Observability, Orchestration,
Tools, Skills).

## What kind of source this is — stated plainly, since it changes how to read it

This is the weakest-evidence source analyzed in this project's run of
"deep analysis" rounds. Every prior article (the MCP-server piece, the
interface-lifting piece, even the hypiest of the six Jev sources) showed
real code, a real benchmark, or a real reproduced number. This one shows
**zero** — no code beyond one illustrative CrewAI snippet, no benchmark, no
named source for any of its comparative claims about frameworks. It is a
structured opinion piece, self-published, with its own promotional banner
("50% OFF Premium Courses") and a crypto tip-jar line at the top. None of
that makes the mental model wrong, but it means this analysis treats the
*taxonomy* as a reasonable, checkable-in-principle framework for comparing
tools, while treating every specific claim about a specific framework as
the author's own unsourced characterization, not a verified fact.

## The taxonomy itself is a genuinely useful, checkable structure

"Orchestration / Tools / RAG / Observability / Cloud ecosystem" as the
five axes to evaluate any agent framework against is a reasonable,
falsifiable claim: you can take any named framework and actually check
whether it has a story for each axis. The orchestration layer's own
sub-breakdown — workflow architecture (linear/branched, sequential/
parallel, router, centralized/decentralized), ahead-of-time vs. dynamic
planning, multi-agent handoffs, HITL approval, **checkpoint/pause/resume**,
and failure recovery — is a coherent checklist, and the article is explicit
that checkpointing is the one piece it considers non-negotiable:
"this logic of managing workflow pausing, resuming and checkpointing is
very complex and MUST be there in a framework that you want to choose."

## What doesn't check out, or is asserted without support

- **"Agentic AI = Generative AI (LLMs) + Tools + Auth"** is presented as a
  hard-won personal insight ("over the course of past several months, I
  have been able to simplify agentic AI to this one equation") but it's
  also just... missing memory/state and orchestration, both of which the
  same article spends three sections arguing are essential. The equation
  and the rest of the article are in some tension with each other — worth
  noting rather than repeating the equation as a settled definition.
- **"OpenAI's SDK tightly integrates with the Azure-ChatGPT ecosystem"**
  is a specific, checkable technical claim, and it conflates two separate
  things: OpenAI's own API/Agents SDK and the separately-operated Azure
  OpenAI Service are different products with different billing and access
  paths — "tightly integrates with Azure" overstates a real but narrower
  fact (Azure OpenAI exists as *one* deployment option, not the SDK's
  home ecosystem the way Semantic Kernel is Microsoft's). Flagged here as
  an imprecise claim, not a verified one.
- **No comparative data backs any "framework X is better at Y" claim.**
  Every framework in the list (Semantic Kernel, AutoGen, Google ADK,
  CrewAI, Mastra, LangGraph) gets asserted properties with no link, no
  version, no date — a materially weaker bar than even the loosest source
  analyzed so far in this project (the Jev marketing videos at least gave
  specific numbers, even if some were inconsistent across sources).
- **The ROOTS mnemonic reorders its own five-layer list to make the
  acronym work** (RAG, Observability, Orchestration, Tools, then adds a
  sixth concept, Skills, that the article explicitly didn't cover
  — "I skipped the discussion on skills in this article"). A mnemonic
  built by reordering and then appending an uncovered concept is a
  rhetorical device, not additional evidence for the taxonomy.

## What's genuinely well-reasoned, worth keeping

- **The checkpoint/pause/resume six-step list is concrete and correct as
  a design**, independent of whether this particular article invented it:
  save state+context to durable storage, mint a UUID per run, surface a
  partial response to the caller, look the run up later by that UUID,
  reinstate state+context, resume execution from that point — and loop
  back to the same HITL gate if approval still isn't granted. That's a
  real, implementable spec, and this project's own agent loops don't have
  it (checked directly, not assumed — see "what was built," below).
- **Failure recovery via a write-ahead-log-style durable record**, so a
  crashed process can restart and pick up from the last checkpoint instead
  of re-running a whole multi-step workflow, is standard, sound practice
  borrowed correctly from database systems.
- **The closing practical advice — pick the framework your team's stack
  already fits, since all the major frameworks cover the same five layers
  at a basic level — is honest and non-hype**, a rare moment in this kind
  of survey content that declines to crown a "best" framework.

## A real, confirmed gap in this project, not a hypothetical one

Checked directly rather than assumed: `/builds/trading-jarvis/jarvis_orchestrator.py`'s
`ask_jarvis()` tool-dispatch loop and `jarvis_swamp_bridge.py`'s governance
gate both run entirely in-process, in memory. `route_through_bus()`'s
`approval_required=True` check (`jarvis_swamp_bridge.py:190`) raises a
`GovernanceError` and **halts** — it does not persist any state, mint a
run ID, or offer a way to come back later and resume from that exact
point. A crash, a process restart, or genuinely waiting for a human's
"yes" on a slower timeline all lose the entire run. Grepped the whole
project for `checkpoint`/`sqlite3`/`resume`/`pause` — nothing exists
anywhere in this repo that does this. This is the one piece of the
article's taxonomy this project is missing for real, and it's the piece
the article itself calls non-negotiable.

## What was built from this (see `/builds/agent-checkpoint-layer/README.md`)

Per this project's established pattern, the generalizable, valuable piece
— durable checkpoint/pause/resume with real crash recovery — was built
for real, against this project's own existing orchestration code, rather
than building (or worse, re-deriving from an un-sourced survey) a whole
new agentic framework from scratch. Not built: RAG and cloud/ecosystem
layers, since this project is a single local codebase with no vector
store, no multi-cloud deployment question, and nothing the article's RAG
or Cloud sections would apply to — stated as out of scope rather than
silently padded in.
