---
name: code-structure
description: Write code in a clean, readable, service-layer structure that a human developer (or a fresh agent with no context) can pick up and understand — not just code that works. Use while implementing any feature or fix, especially before calling it done. The "build" station of the software factory (isolate → build → prove → ship).
---

# Code Structure (Build)

Step 2 of the software factory: **isolate → build → prove → ship**.
Working code isn't the bar — code a stranger (a hired developer, this
project's owner, or another agent with zero context) can open and
immediately understand is the bar.

## Rules

- **Separate concerns.** Don't mix data loading, business logic, and
  presentation in one function or one file. In this project:
  - `streamlit_app.py` stays thin — page layout and calls into other
    modules, not raw data wrangling or business logic inline.
  - Data loading/transformation logic belongs in its own module (e.g. a
    `lib/` or `services/`-style file), not copy-pasted inline wherever
    it's needed.
- **No duplication.** If the same logic appears twice, extract it. Don't
  let two code paths silently drift apart.
- **No dead code.** Don't leave commented-out blocks, unused functions,
  or "just in case" branches that can't be reached.
- **Name things for what they do.** A function/variable name should make
  its purpose obvious without needing to read the body.
- **Match the existing patterns already in the codebase** before
  introducing a new one. Don't invent a second way to do something this
  project already does one way.
- **Follow `design-rules.md` exactly** for anything visual — this is a
  hard requirement, not a suggestion, per `CLAUDE.md`.
- **Keep functions and files a reasonable size.** If a file is doing
  five unrelated things, it's doing too much — split it.

## Self-check before moving to `prove`

Read back what was just written as if you were a second engineer who's
never seen this code before, with no memory of writing it. Would you
understand it in one pass? If not, restructure before moving on —
`prove` and `review-loop` catch behavior bugs, not readability problems,
so don't rely on them to catch messy code.
