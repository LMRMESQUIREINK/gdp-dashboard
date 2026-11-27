# Deep analysis: "12 Open-Source GitHub Repositories to Learn AI and LLM Engineering From Scratch"

Source: a pasted newsletter article (read.vijayasekhardeepak.com), no
accompanying instruction — a genuinely new source, not a repeat (the
immediately prior turn had been an exact re-paste of an already-shipped
Fareed Khan article, confirmed and declined; the user then clarified
they meant a different source and pasted this one).

## What this is

A curated 12-repo learning path for AI/LLM engineering, ordered from
mathematics fundamentals through nanochat-scale end-to-end systems, with
a stated Learn→Build→Experiment→Read→Repeat cycle and a per-repo
mini-project. Unlike most sources this project analyzes, there's no
pipeline or mechanism of the author's own to audit — it's a curated
pointer list to *other* real, independent projects. The checkable
surface is therefore different: does every linked repo exist, and do
this article's specific claims about each one (lesson counts, structure,
status, authorship) hold up against the real thing.

## Measured, not assumed

All 12 named repos were checked for existence via anonymous
`git ls-remote` (no GitHub API token needed, no `add_repo` required for
read access) before reading any of them for meaning — zero link rot,
all 12 real:

`mml-book/mml-book.github.io`, `microsoft/AI-For-Beginners`,
`microsoft/generative-ai-for-beginners`, `dair-ai/Prompt-Engineering-Guide`,
`mlabonne/llm-course`, `rasbt/LLMs-from-scratch`,
`FareedKhan-dev/train-llm-from-scratch`, `karpathy/nanochat`,
`huggingface/ml-intern`, `harvard-edge/cs249r_book`,
`labmlai/annotated_deep_learning_paper_implementations`,
`rohitg00/ai-engineering-from-scratch`.

(Item #7 is a different Fareed Khan repo than any analyzed in this
project's five prior Fareed Khan rounds — confirmed by name before
treating it as new.)

Five of the twelve were cloned and read in full for their most specific,
checkable claims — the numeric and status claims most likely to be
wrong if the article were stale or careless, rather than the harder-to-
check descriptive ones:

- **`huggingface/ml-intern`** — claimed "archived, hosted app/CLI
  retired." The real README's own first line: "**This repo is
  archived.** ML Intern has now moved to the
  [HuggingChat repo](https://github.com/huggingface/chat-ui)." Confirmed
  exactly, with a specific migration target the article didn't even
  mention.
- **`microsoft/AI-For-Beginners`** — claimed "24 lessons." The real
  README states "24-lesson" verbatim. Confirmed.
- **`microsoft/generative-ai-for-beginners`** — claimed "21-lesson
  curriculum." The real README states "21 Lesson"/"21-lesson"
  repeatedly. Confirmed (22 numbered folders on disk includes a `00-`
  setup module not counted toward the 21, consistent rather than
  contradictory).
- **`mlabonne/llm-course`** — claimed structure "organized around LLM
  Fundamentals, The LLM Scientist, and The LLM Engineer." The real
  README's own section headers match verbatim. Confirmed.
- **`mml-book/mml-book.github.io`** — claimed to be the companion repo
  to the book *Mathematics for Machine Learning*, covering linear
  algebra/PCA/gradient descent connected to ML algorithms. The real repo
  is exactly that — its own `tutorials/` folder is linear regression and
  PCA notebooks, matching the article's own suggested mini-project
  almost exactly. Confirmed.

## The one claim that doesn't hold up: a real author misattribution

Item #5 is headed **"LLM Course by Maarten Grootendorst"**, linking
`mlabonne/llm-course`. Checked rather than passed through: the real
repo's own README names its maintainer three separate ways —
`@maximelabonne` on X, `huggingface.co/mlabonne`, and credit as
co-author of a *different* book, *LLM Engineer's Handbook*. Web search
confirms Maarten Grootendorst is a real, different person: creator of
BERTopic and KeyBERT, currently a Developer Relations Engineer at Google
DeepMind, and co-author of a *different* LLM book, *Hands-On Large
Language Models* (with Jay Alammar) — not this repo's author.

This isn't a fabricated name or a dead link; it's two real, both-active
authors in the same adjacent space (LLM courses, LLM books) who got
swapped — the specific, well-evidenced kind of error this project's
discipline exists to catch rather than silently repeat. Everything else
about item #5 (the repo link itself, the three-part structure, the
course content) is accurate; only the byline is wrong.

## What's credited

- Precise, checkable, non-rounded numeric claims (24 lessons, 21
  lessons) that both turned out exactly right — the kind of specific
  claim that's easy to get subtly wrong (off-by-one, stale after a
  curriculum update) and wasn't here.
- The archived-repo disclosure for `huggingface/ml-intern`, including an
  explicit "treat it as a historical case study, not a maintained tool"
  caveat right where the claim appears — not buried, matching this
  project's standing credit for honest self-disclosure (though here it's
  the newsletter author's disclosure about someone else's retired tool,
  not a source's own limits).
- The two-track (practical vs. theory) framing and the
  Learn→Build→Experiment→Read→Repeat cycle are both genuinely actionable,
  checkable-in-principle advice, not vague encouragement — "keep one
  small project alive throughout" is concrete and correct for anyone
  actually following the path.

## What's unverifiable, stated as such

- The remaining 7 of 12 repos' difficulty/content descriptions
  (`dair-ai/Prompt-Engineering-Guide`, `rasbt/LLMs-from-scratch`,
  `FareedKhan-dev/train-llm-from-scratch`, `karpathy/nanochat`,
  `harvard-edge/cs249r_book`,
  `labmlai/annotated_deep_learning_paper_implementations`,
  `rohitg00/ai-engineering-from-scratch`) were confirmed to exist but not
  read in full this round — all plausible and consistent with their own
  public descriptions, not independently verified claim-by-claim the way
  the five above were.
- No performance/outcome claims appear anywhere in this article (unlike
  most sources this project has audited) — it's a learning-sequence
  recommendation, not a product or benchmark, so there's no arithmetic
  or outcome figure to recompute.

## What's built from this

`/builds/curriculum-link-auditor/` — not a port of any one of the 12
repos (there's no pipeline here to extract; they're independent,
unrelated projects), but the generalizable version of the by-hand check
that found the misattribution above: given a repo's README text and a
curated list's specific claims about it (lesson count, archived status,
structure keywords, claimed author), report what holds up and what
doesn't. Tested against the real README fixtures from this exact
article's repos, including the real misattribution as a committed
regression test. See the build's own README for what it found when run
for real, including a real false-positive bug found and fixed in its
first draft (Hugging Face site-navigation links mismatched as
"usernames") while actually running the CLI against the real llm-course
README rather than trusting the regex by inspection.
