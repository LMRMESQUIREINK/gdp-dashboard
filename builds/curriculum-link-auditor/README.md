# Curriculum Link Auditor

A real, dependency-free Python tool for checking a curated list's claims
about *other people's repos* against those repos' own README text —
built from a real finding while deep-reading "12 Open-Source GitHub
Repositories to Learn AI and LLM Engineering From Scratch"
(vijayasekhardeepak.com). Full analysis:
`/notes/learning-path-12-repos-analysis.md`.

## What it found when run for real

All 5 claims in `manifest_12_repo_learning_path.json` were checked
against the real, live-cloned repos (not synthetic stand-ins):

- **`huggingface/ml-intern`** — claimed archived: **confirmed**. The
  real README says so verbatim, and even names exactly where it moved
  (`huggingface/chat-ui`), a detail the article didn't include.
- **`microsoft/AI-For-Beginners`** — claimed 24 lessons: **confirmed**,
  matching the real README's own stated count exactly.
- **`microsoft/generative-ai-for-beginners`** — claimed 21 lessons:
  **confirmed**, same way.
- **`mlabonne/llm-course`** — claimed three-part structure (LLM
  Fundamentals / The LLM Scientist / The LLM Engineer): **confirmed**,
  verbatim section headers. Claimed author **"Maarten Grootendorst"**:
  **wrong**. The real README names its actual maintainer, Maxime
  Labonne, in three places (`@maximelabonne` on X, `mlabonne` on
  Hugging Face, co-author credit for a *different* book, "LLM
  Engineer's Handbook"). Maarten Grootendorst is a real, different
  person — creator of BERTopic/KeyBERT, a Developer Relations Engineer
  at Google DeepMind, co-author of a *different* LLM book ("Hands-On
  Large Language Models," with Jay Alammar) — confirmed via web search
  before concluding this was an error rather than an obscure alias.
  Two real people in the same adjacent space, swapped.
- **`mml-book/mml-book.github.io`** — claimed to be the companion repo
  to "Mathematics For Machine Learning": **confirmed**, including the
  exact linear-regression/PCA tutorial pair the article's own
  mini-project points at.

4 of 5 claims checked out exactly, including two precise numeric claims
(24, 21 lessons) that could easily have been stale or rounded. The one
real miss is a specific, checkable, well-evidenced misattribution — not
a vague "seems off."

## Why this, not a clone of the article's own 12 repos

The article is a curated list of *other people's* work, not a tool or
pipeline of its own to port — there's nothing to clone that would be
this project's "generalizable mechanism" in the usual sense. What *is*
generalizable is the check itself: any curated list of repos (a
newsletter roundup, an awesome-list, a "learn X" roadmap) makes
checkable claims — lesson/episode counts, archived status, structure,
authorship — that go stale or get mixed up, and nobody re-verifies them
after publish. This tool is that re-verification, built once and reused
against any such list, not just this one.

## Usage

```python
from curriculum_auditor import RepoClaim, audit_manifest

claims = [RepoClaim(repo="mlabonne/llm-course", claimed_author="Maxime Labonne")]
readmes = {"mlabonne/llm-course": open("llm-course-README.md").read()}
results = audit_manifest(claims, readmes)
print(results[0].clean, results[0].matches, results[0].mismatches)
```

Or via the CLI, against a directory of locally-cloned repos (one
subfolder per repo, each with a `README.md` — the shape a plain
`git clone` produces):

```bash
python3 audit.py manifest_12_repo_learning_path.json --repos-dir /path/to/clones --check-live
```

`--check-live` adds a `git ls-remote` existence check per repo (no
GitHub API token needed) — kept as an opt-in flag since it's the one
network-dependent part.

## Proven

```bash
python3 -m unittest test_curriculum_auditor -v
```

**21/21 tests pass**, including:

- Every deterministic check (`extract_lesson_count`,
  `detect_archived_banner`, `extract_maintainer_handles`,
  `check_author_attribution`, `check_structure_keywords`) run against
  the real, unmodified README fixtures under `tests/fixtures/`
  (`huggingface/ml-intern`, `microsoft/AI-For-Beginners`,
  `mlabonne/llm-course` — not synthetic text), confirming both the real
  matches and the real misattribution.
- `test_llm_course_full_claim_set_surfaces_exactly_the_real_misattribution`
  — the discrimination test that matters: one call, one repo, a correct
  structure claim AND a wrong author claim, and the tool reports exactly
  one match and exactly one mismatch, not both-pass or both-fail.
- A real, live, network-backed run of `audit.py` itself (not just the
  unit tests) against all 5 actually-cloned repos with `--check-live`,
  reproduced in the analysis note — same result as the unit tests, plus
  a live `git ls-remote` confirming each repo really exists today.
- A real false-positive found and fixed while building this, the same
  class of bug this project's own discipline exists to catch before
  shipping: the first draft of `extract_maintainer_handles` matched
  Hugging Face site-navigation paths (`huggingface.co/blog`, `/docs`,
  `/learn`, `/models`, `/spaces`, ...) as if they were usernames,
  polluting the mismatch evidence with noise. Caught by actually running
  the CLI against the real llm-course README, not by reading the regex.
  Fixed with an explicit reserved-segment exclusion list; the real
  username matches (`mlabonne`, `maximelabonne`) and the real
  misattribution finding are unaffected.
- `check_author_attribution` is deliberately conservative: a README with
  no self-named handle at all gives a **soft pass**, not an accusation
  — the tool only flags a mismatch when the README actively names a
  real handle that doesn't fit the claim, never from silence.

## What's not built here

- No live GitHub API calls (archived flags, star counts, etc.) — this
  session's GitHub API access is gated behind `add_repo`/credentials;
  everything here works from a repo's own README text plus one
  no-token `git ls-remote` existence check, which is also what makes
  the core logic fully testable offline.
- No fuzzy-NLP author-name matching — deliberately narrow (X/Twitter and
  Hugging Face profile-link extraction only) so a flagged mismatch is
  strong evidence, not a guess from string similarity.
