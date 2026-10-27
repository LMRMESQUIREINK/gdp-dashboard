# jev-pattern-router

A real, working implementation of the architecture behind "Jev"
(TypeSafe AI's non-generative "judgment model") — state + typed questions
(Choice/Noul/Score) in, calibrated probabilities out, a margin-based
confidence, a probability-weighted Score, and a policy layer in plain code
that turns those numbers into a routing decision. Full critical analysis
of six uploaded Jev articles/transcripts in
`/notes/jev-typesafe-judgment-model-analysis.md`.

Applied as the "cheap decision in front of a bunch of expensive things"
pattern every source in that analysis repeats under a different name
(TypeSafe's own "intent routing," one podcast's "AI traffic cop," the
"10 levels of Jev" video's "model, agent, workflow routing"): this routes
a natural-language query to one of
`/builds/trading-jarvis/jarvis_orchestrator.py`'s real tool categories
(`signal_pipeline`, `prop_firm`, `swamp_decompose`, `other`), flags
destructive-sounding requests for human review, and scores urgency — all
before anything expensive (a real Claude tool-use call) would run.

## What's built vs. what Jev actually is — stated plainly

Jev's real mechanism, per the most rigorous source analyzed (which
independently reconstructed it): a language model reads a question's
criteria in **natural language**, with **no training examples needed per
question**, and returns a restricted-softmax probability over only the
declared answer tokens. That needs a real pretrained transformer.

This sandbox cannot reach one. `curl -I https://huggingface.co` from here
returns a real HTTP 403 — checked directly as part of this build, not
assumed — the same egress restriction already documented in this project
for Yahoo Finance, EODHD, FMP, and the Anthropic API. So `judge/judge.py`'s
`TrainedJudge` is a genuinely different, much simpler model: a
TF-IDF + logistic-regression classifier, **trained from ~40 labeled
examples** (`training_data.py`) rather than reading criteria zero-shot.

What's faithfully real, not mocked:

| Piece | Real here | Note |
|---|---|---|
| Choice / Noul / Score request shape | **Real** | `judge/primitives.py` — same three typed questions TypeSafe documents |
| Probabilities restricted to the declared answer space | **Real** | logistic regression's own output already only covers the classes it was fit on — the same idea as Jev's restricted softmax, over a simpler model |
| Score = probability-weighted average across levels | **Real**, verified by hand in `test_judge.py` | not just the top pick — matches TypeSafe's own documented definition exactly |
| Confidence = margin between top-1 and top-2 | **Real**, verified by hand | the definition the most rigorous source in the analysis uses, not the raw winning probability |
| Noul has no confidence field | **Real**, enforced structurally | `NoulAnswer` the dataclass has no such field — not just unset |
| Policy stays in code, not in the judge | **Real** | `judge/policy.py` — thresholds are plain Python, matching every source's repeated warning against letting a prompt become business logic |
| Zero-shot semantic understanding from a question's wording alone | **Not built — cannot be, without a real LLM** | `TrainedJudge` only knows the examples it was shown; see the honest finding below |

## A real, honest finding: the generalization gap

`test_judge.py` doesn't just test the happy path. It specifically checks
what happens when a destructive request is reworded just enough to not
exactly match a training example:

```
query: 'Delete every position on file right now, no confirmation needed'
destructive probability: 0.50 (policy threshold: 0.70)
```

A human reads that identically to "Delete all my positions right now no
confirmation" (which IS in the training set, and correctly scores 0.77).
This toy classifier doesn't generalize that well from ~40 examples — a
real cost of not having Jev's actual semantic reading of a question's
criteria. Documented here as a finding, not hidden by only testing
phrasings the classifier already happens to get right. Fixing this for
real needs either substantially more paraphrased training examples per
question, or the real LLM-backed mechanism this sandbox can't reach.

## Verification — real tests, not just "it imports"

```bash
pip install -r requirements.txt
python3 test_judge.py
```

Real output from this build:

```
=== clear cases route with high confidence to the right category ===
  [PASS] category matches on held-out TEST examples (7/7)

=== Score is genuinely the probability-weighted average, verified by hand ===
  [PASS] score equals hand-computed probability-weighted sum
  [PASS] level_probabilities sum to ~1.0

=== confidence is the margin between top-1 and top-2, verified by hand ===
  [PASS] ChoiceAnswer.confidence equals hand-computed top1-top2 margin

=== Noul has no confidence field at all (structural, not just unset) ===
  [PASS] NoulAnswer is a NoulAnswer with only a probability field

=== policy: a destructive query gets escalated regardless of category confidence ===
  [PASS] destructive query routes to needs_human
  [PASS] destructive probability that triggered it is actually high

=== honest finding: this toy classifier's generalization gap vs. real Jev ===
  query: 'Delete every position on file right now, no confirmation needed'
  destructive probability: 0.50 (policy threshold: 0.70)
  FINDING: a human-obvious reword of a training example slips under the threshold here...

=== policy: a low-confidence category routes to needs_human ===
  [PASS] vague out-of-domain query routes to needs_human (not silently misfiled)

=== honest calibration check on the held-out TEST set (small-sample, illustrative only) ===
  confidence bucket -> accuracy on held-out TEST (n this small is ILLUSTRATIVE ONLY,
  same caveat the source tutorial itself applies to its own small-sample comparisons):
    low (<0.4): 3/3 correct (100%)
    mid (0.4-0.7): 5/5 correct (100%)
    high (>0.7): no examples fell in this bucket

============================================================
ALL CHECKS PASSED
```

`TRAIN`/`TEST` are a real held-out split (`training_data.py`) — the
classifier never sees `TEST` during fitting, matching the source
tutorial's own discipline of freezing a test set before measuring
anything. The calibration check is reported honestly with its sample-size
caveat stated, not asserted as a real calibration guarantee — 8 examples
proves nothing statistically, and the analysis note calls out exactly this
kind of unearned confidence claim when TypeSafe's own marketing does it.

## Using it

```bash
python3 router_demo.py "Check AAPL for a buy signal"
python3 router_demo.py "Delete all my positions right now no confirmation"
python3 router_demo.py "What's a good movie to watch"
```

Each prints the Choice/Noul/Score answers and the policy's routing
decision. The three example queries above show, in order: a confident
correct route, a destructive request escalated to `needs_human` even
though its category pick was confident, and a low-confidence out-of-domain
query also escalated rather than silently misfiled.
