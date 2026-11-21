# content-provenance-check

A dependency-free Python tool, originally built from a pasted Medium
article, "Building the Entire RAG Ecosystem and Optimizing Every
Component" (Fareed Khan, a ninth source from this author analyzed in
this project), extended one round later against a second, independent
real-world case from the same author's next article, "Building a
Multi-Agent AI System with LangGraph and LangSmith," and extended again
a round after that against a third, from "Building DeepSeek R1 from
Scratch Using Python." Full analysis: `/notes/rag-ecosystem-analysis.md`,
`/notes/multi-agent-langgraph-analysis.md`, and
`/notes/deepseek-r1-from-scratch-analysis.md`.

## The real finding

Cloned the real linked repo, `FareedKhan-dev/rag-ecosystem`. Two things
jumped out immediately, before reading a single cell for meaning:

1. **The repo's own `LICENSE` file reads "Copyright (c) 2025
   LangChain"** — not Fareed Khan.
2. **The repo's only commit is titled "MIT LangChain."**

That's the author correctly satisfying the MIT license's own
requirement to keep the original copyright notice intact — a legally
proper minimum, credited as such. But the Medium article's own prose
never says this anywhere. It's written entirely in first person ("My
Table of Contents," every diagram captioned "Created by Fareed Khan")
as if this is an original walkthrough, and its real README mentions
"LangChain" only as a library the code happens to use (`pip install
langchain...`, "you may already know LangChain supports a variety of
LLM providers") — never as the source the content itself came from.

Checked directly, not assumed from the license line alone: cloned the
real, public `langchain-ai/rag-from-scratch` (Lance Martin's own
LangChain repo — his LangChain Hub handle is `rlm`, matching the
article's own `hub.pull("rlm/rag-prompt")` call). The Step-Back
Prompting section's few-shot examples are **character-for-character
identical** in both repos:

```
"Could the members of The Police perform lawful arrests?" /
"what can the members of The Police do?"

"Jan Sindel's was born in what country?" /
"what is Jan Sindel's personal history?"
```

Broader term checks (`RAPTOR`, `ColBERT`, `cosine_similarity`,
`physics_template`, `TutorialSearch`, `reciprocal_rank_fusion`,
`get_unique_union`) all appear in both repos too — the retrieval/
indexing/routing core of the article (roughly the first two-thirds)
tracks LangChain's own public "RAG From Scratch" notebook series
closely, not an original synthesis.

## A second real-world case: this time, proper disclosure

"Building a Multi-Agent AI System with LangGraph and LangSmith" (the
same author's next article) names and links `langchain-ai/langgraph-101`
directly, and captions several diagrams "(From LangChain —
OpenSource)". Checked against the real repo: **9 of 11 shared-filename
diagram images between the two real repos are byte-for-byte identical**
(confirmed via `sha256sum`), and the core `get_engine_for_chinook_db()`
function is functionally identical with Fareed Khan's own expanded
explanatory comments layered on top. Unlike the rag-ecosystem case,
this is the *opposite* verdict — real reuse, genuinely disclosed. Added
as a second fixture pair and a dedicated test class
(`TestSecondRealWorldCaseProperDisclosure`) proving this tool correctly
reaches different conclusions on two different real inputs, not just
one hard-coded finding.

This round also added **`find_binary_reuse()`** — images carry no words
to fingerprint, so the 9/11-identical-PNGs finding needed a separate,
sha256-based check (the same method used to verify the finding by
hand), not a variant of the text-based `find_reuse()`. Tested against
small synthetic fixture directories (`tests/fixtures/candidate_images/`,
`reference_images/`) modeling the exact real shape found — same
filename + identical bytes, same filename + different bytes, and a
filename that only exists on one side — stated plainly as synthetic
rather than committing large real PNGs disproportionate to a test.

## A third real-world case: real reuse, real disclosure, and a real
blind spot in the tool itself

"Building DeepSeek R1 from Scratch Using Python" (the same author's
11th source analyzed in this project) walks through reproducing
DeepSeek R1's GRPO training pipeline, including five named reward
functions (`accuracy_reward`, `format_reward`, `reasoning_steps_reward`,
`get_cosine_scaled_reward`, `get_repetition_penalty_reward`) whose names
and implementation style closely resemble Hugging Face's own `open-r1`
project. Checked directly: cloned the real, linked
`FareedKhan-dev/train-deepseek-r1` (LICENSE correctly names Fareed Khan,
not a third party — same pattern as the langgraph-101 case, not the
rag-ecosystem one) and Hugging Face's real `huggingface/open-r1`.

- **`reasoning_steps_reward`'s regex pattern is character-for-character
  identical** between the two: `r"(Step \d+:|^\d+\.|\n-|\n\*|First,|
  Second,|Next,|Finally,)"`, down to the same bullet markers and
  transition words, and both use the identical "magic number 3" scaling
  (`min(1.0, count / 3)`).
- **`get_repetition_penalty_reward`'s core formula and error string are
  verbatim**: `scaling = 1 - len(ngrams) / total`, `reward = scaling *
  max_penalty`, and `raise ValueError(f"max_penalty {max_penalty} should
  not be positive")` match exactly. Measured overlap: 22/179 n-gram
  windows (12.3%) between the two real functions.
- Elsewhere, real independent rewriting: `accuracy_reward` swaps
  `open-r1`'s "skip unparseable examples" (`reward = None`) for a fixed
  neutral reward (`0.5`); `format_reward` uses a looser regex;
  `get_cosine_scaled_reward` reuses `accuracy_reward()` internally
  rather than re-parsing, and caps `progress` at 1.0 where `open-r1`'s
  own version doesn't — a real fix of a latent bug in the original
  (uncapped `progress` can push `cosine` past one full period); the
  `get_repetition_penalty_reward` here is English-only, dropping
  `open-r1`'s Chinese/`jieba` branch and its citation of the reward's own
  source paper (`https://huggingface.co/papers/2502.03373`) and reference
  implementation.
- **The repo's own real `README.md`, lines 1661-1673, carries an
  explicit "## Citation" section**: "This project was completed with the
  help of the OpenR1 implementation from Hugging Face," followed by a
  formal BibTeX-style citation naming the project title and
  `https://github.com/huggingface/open-r1` directly — a specific,
  genuine disclosure, not a bare "Hugging Face" brand mention (every
  other "Hugging Face" reference in this repo's README is a dataset/
  library-usage link, the same false-disclosure trap the
  rag-ecosystem round's "LangChain" mentions were). This is the
  opposite verdict from rag-ecosystem and matches the langgraph-101
  case: real reuse, properly credited. Whether this exact citation also
  appears in the Medium article's own text (vs. only the repo's README)
  wasn't independently confirmed this round, stated plainly rather than
  assumed either way.

**A real gap found in this tool itself while checking the first case**:
`find_reuse()`'s n-gram overlap on `reasoning_steps_reward` measured
under 3% despite the regex pattern being 100% identical — because the
pattern string has no internal whitespace, it's a single unbroken
"word" to the word-splitting fingerprinter, and the surrounding
docstrings/comments were independently rewritten on both sides, so no
8-word window ever lines up. The exact same kind of gap
`find_binary_reuse()` was built to close for images one round ago
("this content carries no words to fingerprint"). Closed the same way:
**`find_literal_token_reuse()`**, a new function checking for exact-match
whitespace-free tokens at least 20 characters long — long enough that
an incidental match is implausible — confirmed to catch the identical
regex pattern directly.

## Checked `/builds/` first

`curriculum-link-auditor/` checks a curated list's *factual claims*
about a repo (lesson counts, archived status, author bylines) against
that repo's real README — a different mechanism from detecting
verbatim text/code reuse between two corpora and checking whether that
reuse is disclosed. A genuinely new gap.

## What this builds

`provenance_check.py`:

- **`ngram_fingerprints(text, n=8)`** — sliding-window 8-word
  fingerprints of normalized text. Long enough that two independent
  authors landing on the same 8-word sequence by coincidence is
  implausible, so a shared fingerprint is real evidence of verbatim
  reuse, not a vague "similar topic" signal.
- **`find_reuse(candidate, references)`** — checks a candidate text
  against one or more named reference texts, returning the overlap
  ratio and sample matched phrases per reference.
- **`is_disclosed(disclosure_text, source_markers)`** — the part that
  closes the real gap this round found: a source only counts as
  disclosed if the disclosure text contains one of its *specific*
  identifying markers (a repo name, an author's name) — never a bare
  mention of a generic brand/tool name the source also happens to
  share. A naive "does it say LangChain anywhere" check would have
  wrongly marked this exact article as disclosing its source, when
  every one of its "LangChain" mentions is about using the library, not
  crediting the content's origin.
- **`check_provenance(...)`** — combines both into one report, with
  `undisclosed_reuse` as the actual finding: reuse with no matching
  disclosure.
- **`find_binary_reuse(candidate_dir, references)`** — sha256-based
  byte-identical file detection by filename, for content (images) that
  carries no words to fingerprint.
- **`extract_literal_tokens(text, min_len=20)`** /
  **`find_literal_token_reuse(candidate, references, min_len=20)`** —
  exact-match detection for whitespace-free literal tokens (a regex
  pattern, a distinctive error-format string) long enough that an
  incidental match is implausible — content that also carries no words
  for `find_reuse()`'s n-gram window to see, for a different reason
  than images do (one unbroken "word," not zero words).

## Proof

`python3 -m unittest tests.test_provenance_check tests.test_cli -v` —
**39/39 tests pass** (30 prior + 9 new: the third real-world case and
`find_literal_token_reuse()`), including:

- Real, short excerpts from both actual repos — `rag-from-scratch`'s
  real cell 32 and `rag-ecosystem`'s real cell 53 — committed as
  fixtures, confirming the verbatim match the analysis found.
- **The actual finding reproduced as a permanent regression test**: the
  real candidate text flagged as undisclosed reuse against the real
  reference, using the article's own real README prose (which mentions
  "LangChain" only as a tool) as the disclosure text — matching exactly
  what a reader of the published article would have seen.
- A real subprocess CLI (`cli.py check <manifest.json>`), including
  clean, non-traceback error handling for a missing manifest, a missing
  referenced file, and malformed JSON.

**One real bug caught by the test suite's own first real run, not
manufactured**: a first-draft test for "multiple references sorted by
overlap" used two 10-word texts sharing only 5 words — with the default
`n=8`, that's not enough consecutive words to produce even one shared
fingerprint, so the intended "low but nonzero overlap" reference
produced *zero* matches instead, and the test failed outright on its
first run. Fixed by rebuilding the fixture so the "low overlap"
reference genuinely shares one full 8-word window (ratio 1/3) while
the "high overlap" one shares all three (ratio 1.0) — recomputed
directly, not guessed at.

## Deliberately not built

- A general plagiarism-detection tool crawling arbitrary web sources —
  this module takes reference texts as explicit input; it doesn't fetch
  or search for sources itself.
- A verdict on the article's other sections (the evaluation chapter's
  specific examples — "capital of France and Spain," "what is 3+3?" —
  don't appear in `langchain-ai/rag-from-scratch`'s five notebooks,
  checked directly; whether they trace to a different LangChain
  evaluation cookbook wasn't chased further, stated as unconfirmed
  rather than assumed either way).
- Wiring `find_literal_token_reuse()` into `check_provenance()`/the CLI
  by default — kept as its own separate, explicitly-called mechanism,
  same convention as `find_binary_reuse()`, rather than silently merged
  into the main report where its different (and much more permissive)
  false-positive profile — a 20-character shared token is a weaker
  signal alone than an 8-word shared phrase — would need its own
  disclosure-matching semantics to combine safely.
- A verdict on whether the DeepSeek R1 article's other reward functions
  (`accuracy_reward`, `format_reward`, `get_cosine_scaled_reward`) trace
  to `open-r1` specifically versus general GRPO-training convention —
  the two functions checked (`reasoning_steps_reward`,
  `get_repetition_penalty_reward`) are the ones with distinctive enough
  verbatim elements (an exact regex, an exact error string) to support a
  real finding; the other three show real independent rewriting
  (different defaults, a different accuracy-reward design, a cosine
  implementation that reuses `accuracy_reward()` rather than
  re-parsing), so no reuse claim is made about them.
