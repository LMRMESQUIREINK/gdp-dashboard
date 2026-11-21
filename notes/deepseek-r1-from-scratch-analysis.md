# Deep analysis: "Building DeepSeek R1 from Scratch Using Python"

Source: a pasted Medium article by Fareed Khan, an eleventh source from
this author analyzed in this project. No accompanying instruction, so
per this project's convention the article itself is the instruction to
run the deep-analysis-and-ship loop. Walks through reproducing
DeepSeek R1's training pipeline on a small `Qwen2.5-0.5B-Instruct`
stand-in: GRPO-based RL with five reward functions (`accuracy_reward`,
`format_reward`, `reasoning_steps_reward`, `get_cosine_scaled_reward`,
`get_repetition_penalty_reward`), SFT with cold-start data, a second
reasoning-oriented RL stage, rejection sampling, SFT stage 2, and
distillation. Real linked repo: `FareedKhan-dev/train-deepseek-r1`.

## What was measured first

The specific reward-function names and implementation style
(`math_verify`/`latex2sympy2_extended`, TRL's `GRPOTrainer`) closely
resemble Hugging Face's own `open-r1` project — worth checking directly,
the same provenance-checking discipline already applied twice this
project (`/notes/rag-ecosystem-analysis.md`,
`/notes/multi-agent-langgraph-analysis.md`), not assumed from the
resemblance alone.

Cloned both real repos: `FareedKhan-dev/train-deepseek-r1` and
`huggingface/open-r1`.

- **`train-deepseek-r1`'s own `LICENSE` reads "Copyright (c) 2025 Fareed
  Khan"** — his own copyright, not a third party's. Same pattern as the
  langgraph-101 case, not the rag-ecosystem one.
- **`reasoning_steps_reward`'s regex pattern is character-for-character
  identical** between the two real `rewards.py`/notebook cells:
  `r"(Step \d+:|^\d+\.|\n-|\n\*|First,|Second,|Next,|Finally,)"`, down
  to the exact bullet markers and transition words, plus the identical
  "magic number 3" scaling (`min(1.0, count / 3)`).
- **`get_repetition_penalty_reward`'s core formula and error string are
  verbatim**: `scaling = 1 - len(ngrams) / total`, `reward = scaling *
  max_penalty`, and `raise ValueError(f"max_penalty {max_penalty} should
  not be positive")` match exactly, character for character. Measured
  with this project's own `content-provenance-check` tool: 22 of 179
  n-gram windows shared (12.3% overlap) between the two real functions.
- Real, independent rewriting elsewhere: `accuracy_reward` swaps
  `open-r1`'s "skip unparseable examples" behavior (`reward = None`,
  letting `GRPOTrainer` drop the example) for a fixed neutral reward
  (`0.5`, keeping it in the batch) — a genuinely different design
  choice, not a copy; `format_reward` uses a looser regex
  (`\s*` instead of explicit `\n` + `re.MULTILINE`); `get_cosine_scaled_
  reward` reuses `accuracy_reward()` internally rather than re-parsing
  the gold/answer pair a second time, and **caps `progress` at 1.0**
  where `open-r1`'s own version doesn't — a real, credit-worthy fix of
  a latent bug in the original (an uncapped `progress` beyond 1.0 can
  push the cosine term past a full period, producing a reward that
  swings the wrong direction for very long completions); the
  `get_repetition_penalty_reward` here is English-only, dropping
  `open-r1`'s Chinese/`jieba` branch and its citation of the reward's
  own source paper (Kimi 1.5-adjacent, `arxiv`/`huggingface.co/papers/
  2502.03373`) and reference implementation.

## The finding: real reuse, and real, specific disclosure

**The repo's own real `README.md`, lines 1661-1673, carries an explicit
"## Citation" section**, right after "Happy reading!":

> This project was completed with the help of the OpenR1 implementation
> from Hugging Face.
>
> ```
> @misc{openr1,
>     title = {Open R1: A fully open reproduction of DeepSeek-R1},
>     url = {https://github.com/huggingface/open-r1},
>     author = {Hugging Face},
>     month = {January},
>     year = {2025}
> }
> ```

This names the specific project and URL directly — not a bare "Hugging
Face" brand mention, which (checked directly) appears a dozen other
times in this same README purely as a dataset/library-usage reference
("Import ... Hugging Face Transformers," `push_to_hub`, the
`HuggingFaceH4` dataset mirror) — the exact false-disclosure trap the
rag-ecosystem round's "LangChain" mentions were. This is the *opposite*
verdict from that round, and matches the langgraph-101 round: real
verbatim-level reuse, properly and specifically credited.

**One honest limit on this finding**: the "## Citation" section sits at
the very end of the README, immediately after the Distillation section
— and the pasted article content available for this round ended at
that same Distillation discussion, before reaching it. Since the
README otherwise mirrors the article's own prose and image captions
line for line, it's likely this citation is also part of the Medium
article's own closing section, but that wasn't independently confirmed
this round — stated plainly as unconfirmed rather than assumed either
way, the same discipline applied to the langgraph-101 case's own
disclosure text.

## A real gap found in the existing tool, caught while checking this

`/builds/content-provenance-check/find_reuse()`'s n-gram overlap on
`reasoning_steps_reward` measured under 3% despite the regex pattern
being 100% identical between the two real functions. Cause, confirmed
directly: the pattern string (`r"(Step \d+:|^\d+\.|\n-|\n\*|First,|
Second,|Next,|Finally,)"`) contains no internal whitespace, so it forms
exactly one "word" under the fingerprinter's word-splitting — and the
docstrings/comments on either side of it were independently rewritten,
so no 8-word sliding window ever lines up around it, even though the
one token that matters is byte-identical. This is the same class of gap
`find_binary_reuse()` was built to close for images one round ago
("this content carries no words to fingerprint") — just a different
reason (one unbroken word, not zero words).

## Checked `/builds/` first

`/builds/content-provenance-check/` (from the rag-ecosystem and
multi-agent-langgraph rounds) is the direct, obvious fit — not a new
build. Extended, not duplicated.

## Extended

`/builds/content-provenance-check/` gained:

1. **A third, independent real-world fixture pair**
   (`candidate_deepseekr1_repetition_cell.py` /
   `reference_openr1_repetition_cell.py`,
   `candidate_deepseekr1_reasoning_steps_cell.py` /
   `reference_openr1_reasoning_steps_cell.py`,
   `article_prose_openr1_citation.txt` — all real, committed excerpts
   from the real repos), proving `check_provenance()` reaches the
   correct "disclosed" verdict on a third real input, and that a bare
   "Hugging Face" mention still correctly fails `is_disclosed()` the
   same way a bare "LangChain" mention did two rounds ago.
2. **`extract_literal_tokens()` / `find_literal_token_reuse()`** — a
   new function closing the real gap above: exact-match detection for
   whitespace-free literal tokens at least 20 characters long (long
   enough that a coincidental match is implausible), proven directly
   against the real identical regex pattern.

39/39 tests pass (30 prior + 9 new), including a real bug caught by the
test suite's own first run this round: a first-draft assertion checked
for a specific phrase only inside `find_reuse()`'s default 3-sample
preview, which didn't happen to include it — fixed by requesting more
samples in the test, not by lowering what the assertion checks for.

## Deliberately not built

- Wiring `find_literal_token_reuse()` into `check_provenance()`/the CLI
  by default — a 20-character shared token is a weaker signal alone
  than an 8-word shared phrase, so it stays its own explicitly-called
  mechanism (same convention as `find_binary_reuse()`) rather than
  silently merged into the main report.
- A reuse verdict on `accuracy_reward`, `format_reward`, or
  `get_cosine_scaled_reward` — each shows real independent rewriting
  (different defaults, a different unparseable-example design, a
  different cosine implementation strategy), so no claim is made about
  them beyond what's described above.
