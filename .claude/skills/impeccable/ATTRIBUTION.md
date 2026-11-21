# Attribution

Vendored from `pbakaus/impeccable` (Paul Bakaus), Apache License 2.0.
Copied verbatim from the repo's own documented "manual copy, no Node
required" install path (`.claude/skills/impeccable`), unmodified.

This copy includes the skill's prose/reference content and its launcher
scripts, but the launcher's own self-contained detection engine binary
is downloaded on first run (`~/.impeccable/bin/`) or must be installed
separately — it was not fetched or vendored here, and the design hook
and live-mode browser overlay from `npx impeccable install` were not
set up either. The skill's judgment content (critique rubric, craft
floor, audit checklist, etc.) works without any of that; the CLI-backed
commands and the automatic post-edit hook need the real install step,
run by whoever actually works in a checkout of this repo locally.

Upstream: https://github.com/pbakaus/impeccable
