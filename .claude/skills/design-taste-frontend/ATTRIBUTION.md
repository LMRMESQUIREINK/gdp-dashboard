# Attribution

Vendored from `Leonxlnx/taste-skill` ("Taste Skill" / `tasteskill`),
MIT License. `SKILL.md` and all 22 files under `references/` copied
verbatim (468K total).

**Deliberately not vendored**: the real skill folder is 40MB across
1,631 files — almost all of it `assets/` (a photo/scene/3D-object
library, ~38MB) and `scripts/` (asset-production and browser-check
tooling, ~1.6MB: `gate.mjs`, `shoot.mjs`, `photos.mjs`, etc.). Copying
that wholesale would be exactly the kind of disproportionate vendor-
clone this project avoids by rule (same call made for `morluto/rea`,
`bytedance/deer-flow`, and the RUTHLESS AFFILIATE GOLD wizard before
it) — the 468K of prose (house rules, layout/copy/motion/effects
rubrics, the gate checklist) is the generalizable, portable judgment
content; the asset library and render scripts are not.

One real consequence, stated plainly: `SKILL.md`'s own frontmatter
declares a `Stop` hook that tries to run `scripts/gate.mjs` at several
candidate paths. Since that script isn't vendored here, the hook's own
shell logic degrades the way it's designed to when none of its
candidate paths exist — it writes a note to `.taste-skill/
gate-hook-missing.txt` (only if a `.taste-skill/build.json` is present)
and exits 0, never blocking or erroring. No real build gate runs from
this copy; the skill's prose rubrics are the review mechanism until the
real install (`taste-skill`'s own installer) is run separately.

Upstream: https://github.com/Leonxlnx/taste-skill
