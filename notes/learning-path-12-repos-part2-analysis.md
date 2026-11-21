# Deep analysis: "12 Open-Source GitHub Repositories to Become an AI Engineer: Agents, RAG, MCP & System Design"

Source: a pasted newsletter article, Part 2 of the same
vijayasekhardeepak.com series as `/notes/learning-path-12-repos-analysis.md`
(Part 1) — a different, independently-written article with 12 different
repos, confirmed by title and content before treating it as new rather
than a repeat upload.

## Measured, not assumed

All 12 linked repos checked for existence via anonymous `git ls-remote`
before reading any for meaning — zero link rot, all 12 real:
`openai/openai-cookbook`, `anthropics/claude-cookbooks`,
`Shubhamsaboo/awesome-llm-apps`, `huggingface/agents-course`,
`NirDiamant/GenAI_Agents`, `KalyanM45/AI-Project-Gallery`,
`asgeirtj/system_prompts_leaks`, `priyanshop754/vibe-coding-playbook`,
`ombharatiya/ai-system-design-guide`, `donnemartin/system-design-primer`,
`florinpop17/app-ideas`, `The-Cool-Coders/Project-Ideas-And-Resources`.

A real structural difference from Part 1, confirmed by reading the whole
article rather than assumed from its shape: Part 1 made several precise
numeric claims (lesson counts) and one author byline — Part 2 makes
neither. Every entry here is a scope/topic description instead
("this collection contains... RAG, agents, multi-agent, MCP"), which
changes what's checkable: structure/content-category claims rather than
numbers or names.

Four repos cloned and read in full for their most specific claims:

- **`huggingface/agents-course`** — claimed coverage of "tools and
  frameworks including `smolagents`, LangGraph, and LlamaIndex, with
  relevant material on integrating MCP tools." All four confirmed real
  and substantial, not name-dropped: 156 files mention `smolagents`, 94
  mention LangGraph, 16 mention MCP, and there's a whole dedicated
  `units/en/unit2/llama-index/` directory per translated language.
- **`NirDiamant/GenAI_Agents`** — claimed "tutorials and implementations
  covering generative AI agent techniques, from conversational bots to
  more complex multi-agent systems." Confirmed: 65 real notebooks under
  `all_agents_tutorials/`, README explicitly covers multi-agent systems.
- **`ombharatiya/ai-system-design-guide`** — claimed coverage of "RAG
  architectures, agents, model selection, evaluation, and production
  engineering" plus "material for AI engineering system-design
  interviews." Confirmed exactly: the real README's own "Quick
  Navigation" points at a 155-question interview bank, a RAG
  fundamentals chapter, and a model-taxonomy/selection chapter.
- **`asgeirtj/system_prompts_leaks`** — claimed to collect "documented
  system prompts attributed to various AI assistants and coding tools."
  Confirmed: real top-level structure spanning Anthropic, OpenAI,
  Google, Meta, Microsoft, Mistral, DeepSeek, xAI, Cursor, Notion, Pi,
  Qwen, Kimi, GLM, MiniMax, and a `Misc` catch-all — a genuinely broad,
  multi-vendor collection matching the description, not a narrow one
  overstated as broad. Confirmed as currently and actively maintained,
  not stale: its own "most recent additions" table lists an entry dated
  the same day as this analysis. That specific entry's content (a
  claimed leaked system prompt related to this very tool/model) was
  deliberately not opened or read as part of this check — its existence
  and date were enough to confirm active maintenance, and reading
  content purporting to describe this session's own operating
  instructions isn't something this check needed to do.

## What's credited

- Every specific, checkable framework/content claim in this round held
  up exactly, across four independently-verified repos — a cleaner
  record than Part 1 (which had a real misattribution) or most other
  sources this project has analyzed.
- The article's own "don't assume multiple agents will automatically
  improve quality... they can introduce extra model calls, latency,
  coordination failures" is a real, correctly-stated caution, consistent
  with this project's own standing finding from the Jev/AI-System-Design
  rounds that confidence and complexity aren't free.
- The RAG-pipeline five-step description (ingest/chunk → embed/index →
  retrieve → generate → cite sources) and the "evaluate retrieval
  quality separately from answer quality" advice are both accurate,
  standard, and correctly sequenced — no embellishment or invented
  terminology.

## What's flagged, not repeated as fact

- `system_prompts_leaks`'s own README carries three self-cited
  endorsements (Washington Post, CEPS' AI World, and a Simon Willison
  quote) with specific dated links. These are the repo's own citations
  about itself, not claims the analyzed article repeats — so they're
  outside this round's actual verification scope, but a web search for
  the Simon Willison quote specifically didn't turn up independent
  confirmation of that exact phrase this round (it surfaced unrelated
  Willison commentary on a different topic). Noted as unverified from
  this check rather than treated as confirmed, consistent with this
  project's standing rule for self-reported citations without
  independent corroboration found.
- No author-misattribution risk exists in this article the way Part 1
  had one, simply because Part 2 names no individual bylines at all —
  a genuine structural difference, not a gap in this round's checking.

## What's built from this: nothing new — the existing tool generalized

Per this project's "check `/builds/` for an existing implementation
before building a duplicate" rule, no new build was warranted — this is
exactly the kind of source `/builds/curriculum-link-auditor/` was built
to handle. Ran its `extract_claims.auto_extract_manifest()` directly
against this article's raw text rather than hand-writing a manifest: it
correctly extracted all 12 repos in order, and — the more important
result — correctly extracted **zero** false-positive lesson-count,
archived, or author claims, where a cruder extractor might have
mismatched the article's own numbers ("1,000 users," "smolagents,"
"LangGraph") as if they were structured claims about a repo. This is
now a permanent regression test
(`TestGeneralizationToASecondIndependentArticle` in
`test_extract_claims.py`, using a committed fixture of this real
article's text) proving the tool generalizes to a second,
independently-written source it wasn't built from — not just the one
article it was originally built to match. 40/40 tests pass across both
modules.
