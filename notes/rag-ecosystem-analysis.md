# Deep analysis: "Building the Entire RAG Ecosystem and Optimizing Every Component"

Source: a pasted Medium article by Fareed Khan, a ninth source from
this author analyzed in this project. No accompanying instruction, so
per this project's convention the article itself is the instruction to
run the deep-analysis-and-ship loop. A comprehensive survey/tutorial of
RAG techniques: Multi-Query, RAG-Fusion, Decomposition, Step-Back
Prompting, HyDE, Logical/Semantic Routing, Query Structuring,
Multi-Representation Indexing, RAPTOR, ColBERT, dedicated re-ranking,
CRAG/Self-RAG, long context, and evaluation (manual, deepeval, grouse,
RAGAS).

## What was measured first

Cloned the real linked repo, `FareedKhan-dev/rag-ecosystem`, rather
than trusting the article's code samples. Two things stood out before
reading a single cell for meaning:

1. `LICENSE` reads **"Copyright (c) 2025 LangChain"** — not Fareed
   Khan.
2. The repo's single commit is titled **"MIT LangChain."**

That's a legally correct minimum (MIT requires the original copyright
notice be preserved), credited as such. But it directly contradicts
the article's own framing. The Medium text is written entirely in
first person ("My Table of Contents," every diagram image captioned
"Created by Fareed Khan"), and the real README's every mention of
"LangChain" is about *using* the library (`pip install langchain...`,
"LangChain supports a variety of LLM providers") — never about the
walkthrough's own content being substantially someone else's
pre-existing teaching material. Grepped the full README text directly
for any disclosure phrase ("based on," "adapted from," "Lance Martin,"
"rag-from-scratch," "langchain-ai") — zero hits beyond generic tool
mentions.

## The verbatim check

Cloned the real `langchain-ai/rag-from-scratch` — Lance Martin's own
LangChain repo (his LangChain Hub handle is `rlm`, matching the
article's own `hub.pull("rlm/rag-prompt")` call, itself a specific,
checkable clue pointing at this exact source before the clone even
confirmed it). Directly compared distinctive content between the two
repos' notebooks:

- The Step-Back Prompting few-shot examples — "Could the members of
  The Police perform lawful arrests?" / "what can the members of The
  Police do?" and "Jan Sindel's was born in what country?" / "what is
  Jan Sindel's personal history?" — are **character-for-character
  identical** in both repos (`rag_from_scratch_5_to_9.ipynb` cell 32 vs.
  `rag_ecosystem.ipynb` cell 53), confirmed by direct `grep` match, not
  inferred from similarity.
- Broader term checks across the full notebooks (`RAPTOR`, `ColBERT`,
  `cosine_similarity`, `physics_template`, `TutorialSearch`,
  `reciprocal_rank_fusion`, `get_unique_union`) all appear in both,
  confirming the overlap isn't limited to one example — the
  retrieval/indexing/routing core of the article (roughly its first
  two-thirds) tracks LangChain's own public notebook series closely.
- The evaluation chapter's specific worked examples ("capital of France
  and Spain," "what is 3+3?") do **not** appear anywhere in
  `rag-from-scratch`'s five notebooks, checked directly via `grep -c`
  across all five files (zero hits). Whether they trace to a different
  LangChain evaluation cookbook or are more original to this piece
  wasn't chased further — stated as unconfirmed rather than assumed
  either way.

A smaller, worth-naming nuance: `langchain-ai/rag-from-scratch` itself
carries no explicit `LICENSE` file (confirmed by listing the clone's
root), so Fareed Khan's own MIT re-licensing of its content, while
naming LangChain as copyright holder, sits on a source that never
granted an explicit open license in the first place — a minor legal
wrinkle, not this project's call to resolve, stated per this project's
standing "not legal advice" convention.

## Credited

Beyond the attribution question, the described techniques are
accurately explained at the level the article operates at — Multi-Query,
RAG-Fusion's RRF, Decomposition, HyDE, the routing techniques, and the
evaluation metrics (faithfulness, correctness, contextual relevancy)
are all real, standard, correctly-described RAG patterns. The named
external libraries (`deepeval`, `grouse`, `RAGAS`, `RAGatouille`) are
real, actively maintained projects, not invented tooling.

## Checked `/builds/` first

`curriculum-link-auditor/` checks a curated list's factual claims about
a repo (lesson counts, archived status, author bylines) against that
repo's real README — a different mechanism from detecting verbatim
text/code reuse between two corpora and checking whether that reuse is
disclosed. Nothing in this project does that. A genuinely new gap.

## Built

**`/builds/content-provenance-check/`** — `provenance_check.py`
generalizes the by-hand check performed this round: `ngram_fingerprints()`
(8-word sliding-window fingerprints, long enough that coincidental
overlap is implausible), `find_reuse()` (checks a candidate against
named references), `is_disclosed()` (the key piece — a source only
counts as disclosed if the disclosure text names it *specifically*,
never from a bare mention of a generic brand/tool name it also happens
to share — avoiding exactly the false-positive a naive "does it say
LangChain anywhere" check would have produced here), and
`check_provenance()` combining both into one report.

22/22 tests pass, including real short excerpts from both actual
repos (`rag-from-scratch`'s real cell 32, `rag-ecosystem`'s real cell
53) committed as fixtures, and the actual finding reproduced as a
permanent regression test — the real candidate text flagged as
undisclosed reuse against the real reference, using the article's own
real README prose (mentioning "LangChain" only as a tool) as the
disclosure text.

**One real bug caught by the test suite's own first run, not
manufactured**: a first-draft fixture meant to demonstrate "low but
nonzero overlap" shared only 5 words between two 10-word texts — with
the default `n=8`, that's not enough for even one shared fingerprint,
so it produced zero matches instead of "low," and the test failed
immediately. Fixed by rebuilding the fixture so the low-overlap
reference genuinely shares one full 8-word window.

## Deliberately not built

A general plagiarism-detection tool crawling arbitrary web sources —
this module takes reference texts as explicit input, consistent with
how this round's own investigation worked (clone the specific named
repo, compare directly). A verdict on the evaluation chapter's
specific examples, since their source (if any beyond this article)
wasn't confirmed.
