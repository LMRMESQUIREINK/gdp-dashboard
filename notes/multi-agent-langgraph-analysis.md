# Deep analysis: "Building a Multi-Agent AI System with LangGraph and LangSmith"

Source: a pasted Medium article by Fareed Khan, a tenth source from
this author analyzed in this project, and the direct follow-up round
to the "RAG Ecosystem" analysis one round earlier. No accompanying
instruction, so per this project's convention the article itself is
the instruction to run the deep-analysis-and-ship loop. Builds a
customer-support multi-agent system (music catalog + invoice sub-agents
under a supervisor) on the Chinook sample database, using LangGraph's
checkpointer/store for short/long-term memory, a human-in-the-loop
verification step, and LangSmith for evaluation.

## What was measured first

The prior round's analysis (`/notes/rag-ecosystem-analysis.md`) found
the author's own repo for that article had a `LICENSE` file naming
LangChain as copyright holder, with zero disclosure anywhere in the
article's own prose. This round's article is structurally different in
one important, checkable way: several of its diagram captions read
"(From LangChain — OpenSource)" with a direct link to
`github.com/langchain-ai/langgraph-101`. Worth checking directly rather
than taking either the credit or the absence of one on faith, the same
way the prior round checked the LICENSE line rather than assuming it.

Cloned both real repos: `FareedKhan-dev/Multi-Agent-AI-System` and the
named `langchain-ai/langgraph-101`.

- **`Multi-Agent-AI-System`'s own `LICENSE` reads "Copyright (c) 2025
  Fareed Khan"** — his own copyright this time, not LangChain's, a
  real, checkable contrast with the prior round's repo.
- **9 of 11 shared-filename diagram images between the two real repos
  are byte-for-byte identical**, confirmed via `sha256sum` on each pair
  (`architecture.png`, `human_input.png`, `invoice_subagent.png`,
  `memory.png`, `music_subagent.png`, `supervisor.png`,
  `supervisor_vs_swarm.png`, `swarm.png`, `evals-conceptual.png`,
  `final-response.png` all identical; `single-step.png` and
  `trajectory.png` differ, possibly due to the source repo being
  actively updated since Fareed Khan's own clone). These are exactly
  the images the article's own captions mark "(From LangChain —
  OpenSource)."
- **The core `get_engine_for_chinook_db()` function is functionally
  identical** between the two repos (same URL, same logic, same
  structure) — but not word-for-word copied the way the prior round's
  Step-Back Prompting example was. Fareed Khan's version layers his own
  expanded, line-by-line explanatory comments and docstrings on top of
  the same functional core, confirmed by reading both cells side by
  side.
- **Full-notebook n-gram overlap is only ~9.6%** (1,297 of 13,546 shared
  8-word fingerprints), far lower than the near-universal-term overlap
  found in the rag-ecosystem round — the surrounding code/prose here
  reads as a genuine, independent expansion of the same architecture,
  not a copy.

## The finding: the opposite verdict, and it matters that it's fair

Unlike the rag-ecosystem round, this is a clean, properly-disclosed
case. The images are substantially reused, confirmed byte-for-byte —
but the article's own captions and a direct, named repo link disclose
exactly that. Reporting this plainly rather than searching for a
problem to match the prior round's finding: the same author's practice
clearly varies by article, and this round is the fair, credit-worthy
instance, not a repeat of the same gap.

## Checked `/builds/` first

`/builds/content-provenance-check/`, built from last round's finding,
is the direct, obvious fit — not a new build. Extended rather than
duplicated.

## Extended

`/builds/content-provenance-check/` gained:

1. **A second, independent real-world fixture pair** (the Chinook DB
   function from both real repos, plus the article's own real caption
   text naming `langgraph-101`), proving the existing `check_provenance()`
   mechanism reaches the *correct, opposite* verdict on a second real
   input rather than only ever reproducing the one finding it was built
   from.
2. **`find_binary_reuse()`** — a new, separate sha256-based function for
   detecting byte-identical files by filename, since images carry no
   words for the existing `find_reuse()`'s n-gram fingerprinting to
   work on. This is the same method used by hand to confirm the
   9-of-11 image finding above, now a reusable mechanism. Tested
   against small synthetic fixture directories modeling the exact real
   shape (identical bytes, different bytes, one-sided-only), stated
   plainly as synthetic rather than committing large real PNGs.

30/30 tests pass (22 original + 8 new), including both new real-world
generalization tests and the binary-reuse tests. No bug found this
round — stated plainly rather than manufactured, unlike last round's
real n-gram-window fixture-math bug.

## Deliberately not built

A full image-perceptual-hashing system (detecting a resized/recompressed
near-duplicate, not just a byte-identical one) — this round's real
finding was byte-identical reuse, which sha256 already catches exactly;
perceptual hashing would be solving a problem this investigation didn't
actually have evidence for.
