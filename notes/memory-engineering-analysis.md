# Analysis: "Memory Engineering for AI Agents" (DhanushKumar, Medium)

Source: a pasted long-form Medium article proposing an extensive
(30-plus-category) taxonomy of AI-agent memory types, a proposed memory
lifecycle, a proposed JSON schema, a proposed retrieval scoring formula,
and claims about how Stanford, Microsoft, Anthropic, and NVIDIA each
approach agent memory, plus references to named research systems (MemGPT,
Reflexion, Voyager, Zep/Graphiti, Mem0, Generative Agents). No repo or
code attached — closer in kind to the earlier "AI System Design" and
"Agentic Harness Frameworks" rounds than the GitHub-repo rounds.

## What checked out

Eight specific, checkable claims verified via web search this round:

- **Anthropic's Contextual Retrieval** — confirmed real
  (anthropic.com/news/contextual-retrieval): combines contextual
  embeddings + contextual BM25, exactly as described. The real reported
  numbers are more precise than the article's own vague "substantially
  fewer... when contextual retrieval and reranking are combined":
  baseline top-20 retrieval failure rate 5.7% → 3.7% with contextual
  embeddings alone (35% reduction) → 2.9% adding BM25 (49% reduction) →
  1.9% adding reranking (67% cumulative reduction). Direction is
  accurate; precision is left on the table.
- **Anthropic's memory tool** — confirmed real and current (beta,
  `context-management-2025-06-27` header, tool `memory_20250818`,
  docs.claude.com): files in a `/memories` directory, create/read/
  update/delete plus rename/insert/str_replace, client-side architecture
  where the application does the actual file I/O. Matches the article
  exactly.
- **Generative Agents' scoring formula** (Park et al. 2023,
  arXiv:2304.03442) — confirmed: an equally-weighted sum of recency,
  importance, and relevance. The article's attribution is accurate.
- **Reflexion** (Shinn et al., arXiv:2303.11366) — confirmed: verbal/
  textual reflections stored in an episodic buffer, no weight updates.
- **Voyager** (Wang et al., arXiv:2305.16291) — confirmed: an ever-
  growing executable skill library, GPT-4 as a black box, no fine-tuning.
- **Zep/Graphiti** (arXiv:2501.13956, Jan 2025) — confirmed: a temporal
  knowledge graph with bi-temporal edges and invalidation-not-deletion,
  matching the article's description closely.

## A real, dated gap: MemGPT was renamed Letta over a year before this article

The article describes MemGPT's real OS-inspired virtual-memory analogy
accurately (arXiv:2310.08560) but never mentions that the project was
renamed **Letta** in September 2024 — the repository moved from
`cpacker/MemGPT` to `letta-ai/letta`. "MemGPT" today names the original
design pattern, not the actively maintained project. For an article
with no stated publication date in the pasted text but citing 2025–2026
material throughout, going unmentioned over a year after a maintainer-
announced rename is a real, checkable omission, not a judgment call.

## The strongest finding: the article's own unnamed source already made its central point, uncredited

The article's "2025–2026 survey of agent memory" (described only by its
three-axis framing: forms/functions/dynamics) is identifiable as
**"Memory in the Age of AI Agents: A Survey, Forms, Functions and
Dynamics"** (arXiv:2512.13564, Dec 2025/Jan 2026). The article's
paraphrase of the three-axis taxonomy matches closely — but the article
never names the paper anywhere, and separately devotes a whole section
("RAG Is Not the Same Thing as Memory") to a distinction the survey's
own fourth stated contribution is explicitly about: scoping agent memory
as distinct from LLM memory, RAG, and context engineering. The article
makes the same point the survey already makes, without citing the
survey as the source for it — visible only by actually finding and
reading the unnamed paper, not by reading the article alone.

## Build: `agent-memory-layer`

`/builds/agent-memory-layer/` — not the article's own 30-plus-category
taxonomy (prose classification with nothing to execute or test), but the
one part of the article that is concrete, well-specified, and now
independently verified: the Generative Agents scoring formula
(`score_generative_agents()`, matching the real paper, with the
unconfirmed 0.995/hour decay constant kept as an explicit parameter
rather than a hardcoded fact), the article's own separately-labeled
extended formula (`score_extended()`, never conflated with the real
one), a validated lifecycle state-machine (`transition()`, resolving a
real ambiguity in the article's own prose chain as a documented DAG
rather than silently picking one reading), and the article's own
Flask→FastAPI supersession example made real and testable
(`supersede()`, with a subject-mismatch guard the article never states).

30/30 tests pass, including a hand-independent recomputation of the real
scoring formula and the full supersession example end to end. **A real
bug found and fixed while testing**: the first draft's cosine-to-[0,1]
normalization ran unconditionally, turning the "no embedding" sentinel
value `0.0` into `0.5` instead of leaving it at `0` — silently inflating
every embedding-less memory's score. Caught by a dedicated no-embedding
test, fixed by only normalizing when a real cosine value was computed.
