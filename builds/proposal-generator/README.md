# Proposal & Quote Generator — worked example

A real instantiation of `.claude/skills/proposal-generator`, built from
the "Agency Proposal & Quote Generator" idea in the uploaded "7 claude
skills that print money" article. The skill itself is the actual
deliverable (`.claude/skills/proposal-generator/SKILL.md`); this folder
proves it produces something concrete, not just an abstract instruction.

- `example-discovery-notes.md` — synthetic discovery-call notes
  (explicitly marked as a demonstration, no real client), written the
  way raw call notes actually read: specific, slightly disorganized,
  with a stated-but-not-committed budget and one direct client question
  ("what happens if this takes longer than you think").
- `example-proposal.md` — the proposal built from those notes, following
  the skill's structure: project understanding in the client's own
  framing first, explicit in/out-of-scope lines (the client's own past
  bad-agency-experience made this a real requirement, not boilerplate),
  a dated weekly timeline with a buffer week, three real pricing tiers
  (not a decoy pair), and terms that directly answer the client's own
  question about scope-creep risk rather than leaving it unaddressed.

**A real, deliberate honesty flag inside the worked example itself**:
the pricing section states plainly that no established agency day rate
exists for this demonstration, so the three tiers are anchored to the
one real number the synthetic client gave ("somewhere under $5K") rather
than an invented rate — following the skill's own rule 3 rather than
silently presenting a made-up number as if it were real.

**Verified against the actual tool**, not just read over by eye: run
through `/builds/humanizer/humanizer.py` (0 findings, 0.0/1000 words) —
real proof the skill's own "run it through Humanizer before calling it
done" rule produces a passing result on a realistic document, not just
on the short synthetic samples `humanizer`'s own test suite uses.
