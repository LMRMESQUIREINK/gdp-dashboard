# Analysis: "Forget PI Agent. DeepSeek Super Agent Harness 10x Better"

Source: a pasted Medium article (no byline visible in the pasted text)
about DeepSeek's "Super Agent" concept, plus a linked GitHub repo,
`deepseek-ai/dsh-superagent-prototype` — no accompanying instruction, so
per this project's standing rule the pasted source is itself the
instruction to run the deep-analysis-and-ship loop.

## Measured first

Cloned the real repo (`git clone --depth 1`, single squashed commit,
`8c32a9d`, dated 2026-10-31, authored "DeepSeek Harness Team",
MIT-licensed, `deepseek.com`'s `team@dsh.dev` as the listed contact) and
read every file in it — 9 numbered docs, 13 prompt files, a Feishu/GitHub
skill pair, ~70 TypeScript source files, and ~50 test spec files. This is
a real, substantial, carefully-written codebase, not a thin marketing
wrapper.

**The repo's own README immediately qualifies the article it names**:

> "Research prototype for reference only, not an official DeepSeek
> product... We have adapted it for publication, so it is not identical
> to our internal version or the implementation described in *Exploring
> Super-agent Design: Towards a More Autonomous Agent System*. Some
> designs discussed in the article are directions for future development
> and are not implemented in this prototype."

That caveat matters directly: it confirms a real, separate DeepSeek
article by that title exists (the article's own quoted title, not this
project's guess), and it states plainly, in DeepSeek's own words, that
the open-source code and the article's described implementation are
**not the same thing** — a distinction the Medium piece collapses when it
cites the open-source prototype's own task-acceptance narrowness
("confined by whitelists and rules... currently only comes from GitHub")
in the same breath as the article's broader chat/email/GitHub framing.

## What checked out

- **The real DeepSeek article exists.** Confirmed via web search:
  secondary coverage (SCMP, Phemex, Interesting Engineering, a Taiwanese
  tech outlet) independently describes "Super-agent Design Exploration:
  Toward a More Autonomous Agent System" — a close match to the pasted
  article's and the repo README's own title (translation variance from
  Chinese, not a discrepancy).
- **Router/Worker terminology is real, at a specific layer.** The real
  repo's `docs/001-domain.md` glossary names the formal domain concepts
  **"Main Session"**/`orchestrator` (code) and **"Executor Session"**/
  `worker` (code) — not literally "Router." But `docs/006-deployment.md`
  and `docs/007-architecture.md` both show the actual DeepSeek Harness
  preset names are `dsh-superagent-router` and `dsh-superagent-worker`,
  and independent secondary sources (Phemex, an Inside.com.tw piece
  titled with "router-worker" in its own URL slug) use "Router"/"Worker"
  too. So the Medium article's naming isn't invented — it's the
  public-facing/preset-level term, while the formal glossary the actual
  domain model uses is one layer more precise.
- **The "3 to 5 active sessions" human-attention claim is real and
  repeated independently** across multiple secondary sources, consistent
  with it being DeepSeek's own stated premise, not the Medium author's
  invention.
- **"Claude Duet" is real**, confirmed via multiple independent outlets:
  opened as a research preview on 2026-10-21, runs on Claude Opus 5.5,
  watches connected email/calendar, sends a morning brief, works via a
  cloud browser, and gates send/spend/sign/delete actions behind
  approval. The pasted article's "still in preview" framing and described
  behavior (morning briefing, proactive reach-out) match closely.
- **The core architectural claim is genuinely reflected in the real
  code**, more precisely than the article states it. `docs/001-domain.md`
  specifies **Subscription** (a many-to-many Ticket↔Thread relation) with
  fan-out that has **no admission check on who sent the triggering
  message** — this is the literal mechanism behind the article's "Workers
  perceive conflicts by subscribing to the same Thread" line, and it's
  more deliberately engineered than that sentence conveys: the real
  "Rejected concepts" table explicitly rejects "Admission checks on
  Subscriptions" with the stated reason *"A Subscription covers the whole
  Thread; the Mandate separates authorization from context"* — i.e., the
  design makes decentralized visibility safe specifically by never
  letting it imply authority.
- **Eval's two-layer structure (gate + model assessment) matches the
  article's "Router only cares about who to push this task to."** The
  real `Eval` concept batches Triggers per-Thread, runs at most once per
  Thread at a time, and merges Triggers arriving mid-Eval into the next
  batch — a concrete mechanism that would plausibly produce the kind of
  throughput-via-batching effect the article describes for rising event
  rates, even though no benchmark numbers back that specific claim
  anywhere in this repo (see below).

## What's wrong, or couldn't be checked

- **The cited Anthropic article's name is wrong.** The pasted Medium
  piece names it "Constructing Agents." The real article — fetched and
  read directly — is titled **"Building agents: When to fold subagents
  into your main agent loop"** (claude.com/resources/articles/…, dated
  2026-10-22, author Diane Sarkis). A companion piece, "Building
  multi-agent systems: when and how to use them" (claude.com/blog/…,
  2026-01-23, author Cara Phillips), is also real. The *thesis* the
  Medium article attributes to Anthropic is a reasonable but
  over-sharpened paraphrase: the real article's speed claim is **one
  customer's own case** — "evaluated their multi-agent harness against a
  single agent loop [and] saw a roughly 2x faster runtime with the
  latter" — not a general law that "a bunch of sub-agents is not as
  efficient as having a single agent." The companion article is more
  careful still: multi-agent systems "excel at... heavy parallelization,
  information that exceeds single context windows, and interfacing with
  numerous complex tools," and underperform mainly when coordination
  costs exceed those benefits — a conditional claim, not an absolute one.
- **None of the article's specific benchmark numbers appear anywhere in
  the open-source repo.** Grepped the entire repository (docs, source,
  tests) for every numeric claim in the pasted article — 12.4, 15.7,
  29.5 minutes; 23.23M/31.77M cache-read tokens; the ~30% Router-decision
  increase; the 1/min→40/min throughput and 2.5s→3.9s latency figures —
  zero hits. The repo's own `cache.ts` is an unrelated in-memory LRU
  cache for resource snapshots, not a model-cache-read-token tracker.
  This is consistent with the README's own disclaimer that the prototype
  isn't the implementation the article describes — the benchmark almost
  certainly lives in DeepSeek's own separate article/blog post, not in
  the code the Medium piece links to.
- **The 12.4/15.7/29.5-minute figures are only partially corroborated,
  and one independently-surfaced number doesn't reconcile.** A web
  search summarizing third-party coverage (not the Medium article
  itself) reports "just under 16 minutes" vs. "more than 29 minutes" —
  consistent with the pasted article's 15.7 min (p95) vs. 29.5 min (p95).
  But a *separate* search snippet, apparently drawn from the Medium
  article itself via a search engine's own indexing, states "12.4
  minutes versus 20.4 minutes for a single-session agent" with no
  percentile label. The pasted article text I have never states a 20.4-
  minute figure anywhere — it gives the traditional approach's p95 only
  (29.5 min), never its own p50/median. Three attempted direct fetches
  (levelup.gitconnected.com, hackernoon.com, chaincatcher.com — all
  mirrors/coverage of the same DeepSeek material) all failed with DNS
  resolution errors from this sandbox, extending the project's existing
  list of blocked domains (medium.com, arxiv.org, Hugging Face,
  agentskills.io, dev.to, nocobase.com, puter.com, youtube.com,
  ocw.mit.edu, …). **Flagged, not resolved**: either the pasted article
  text is an incomplete excerpt that omits the traditional approach's own
  median (plausible — Medium's own paywall structure), or the "20.4
  minutes" figure is a separate report's loose paraphrase conflating
  percentiles. Neither could be confirmed from this sandbox.
- **The cache-read-token and throughput/latency figures (23.23M→31.77M
  tokens, 1/min→40/min, 2.5s→3.9s) could not be independently verified
  at all** — not present in the repo, and no accessible secondary source
  reproduced them in the searches run this round. Reported as
  `source-is-silent` from this sandbox, not disputed as false.

## Credited

- The real repo is a careful, substantive piece of engineering — the
  domain model document alone (`docs/001-domain.md`) states not just
  what the design does but, in a dedicated "Rejected concepts" table,
  *why* several more-obvious alternative designs were deliberately not
  built (admission checks on Subscriptions, Eval scheduling its own
  delayed Triggers, locking a failed Executor's Session entirely,
  inferring "waiting on a person" from free text instead of a structured
  field). That table is unusually disciplined self-documentation for a
  "research prototype... adapted it for publication" disclaimer.
- The README's own caveat — that the open-source code differs from both
  DeepSeek's internal version and the article's own described
  implementation, and that several discussed designs are future-only —
  is exactly the kind of upfront, unprompted disclosure this project has
  credited before in other sources (the `agentic-warehouse-analyst`
  round's own "Known Limits" section, the `i-have-adhd` repo's honestly-
  reported eval failure). DeepSeek states this plainly, in public, rather
  than letting the Medium article's more sweeping framing stand
  unqualified.
- Claude Duet and the real Anthropic subagents article both check out as
  real, current, and reasonably characterized — the Medium article isn't
  fabricating comparison products, only mis-titling one citation.

## Built: `/builds/dsh-thread-mandate/`

Checked `/builds/` first: `/builds/fingerprinted-ledger-prereg/` (a
different source, `FareedKhan-dev/dynamic-workflow-agents`) covers
request-fingerprinting/caching/pre-registered-hypothesis mechanisms for a
Lead/Worker runtime — a different concern. `/builds/policy-control-plane/`
covers single-call governance (ALLOW/DENY/REQUIRES_APPROVAL with
payload-hash-bound approval) — a different shape of problem.
`/builds/agent-checkpoint-layer/` covers linear-workflow stage checkpoint/
resume. `/builds/orchestration-decision-engine/` covers a single-agent
retry/escalation loop. None of them implement many-to-many Thread/Ticket
Subscription fan-out, or a Mandate that survives a Ticket's end and is
only ever revalidated on resume — a genuinely new gap.

Built the one mechanism in the real repo that is both genuinely new here
and fully specified enough to reimplement for real without a live model
or a live GitHub App: **Subscription fan-out with no admission check**,
and the **Policy/Mandate separation of authorization from context**,
read directly from `docs/001-domain.md`'s concept table and its
"Rejected concepts" table (quoted verbatim in the module's own
docstrings), not copied from the real TypeScript source.

16/16 tests pass on the real run, each one a direct, named reproduction
of a specific real-repo rule: fan-out with zero admission check; two
independently-subscribed Tickets perceiving the same Trigger with no
central coordinator (the actual "perceive conflicts by subscribing to the
same Thread" mechanism); fan-out never triggering a fresh Eval; a stopped
Ticket receiving nothing further; an ended Ticket resuming under its
*original* Mandate on a person's message while a bot/CI message on the
same subscription does not resume it at all; a Ticket ending normally
leaving its Mandate intact; a Policy no longer granting a Mandate's scope
revoking it on revalidation (kept structurally distinct from a person's
explicit stop); a Policy change never retroactively touching a
still-running Ticket; at-most-one-Eval-per-Thread; and a Trigger arriving
mid-Eval landing in the *next* batch. No bug found in the module's own
logic on the first real run — one straightforward docstring-quoting typo
(four closing quote characters instead of three, in several places) was
caught immediately by `ast.parse()` before any test ran, and fixed before
the suite was ever executed.
