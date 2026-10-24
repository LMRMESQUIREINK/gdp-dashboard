# Claude Code Mods: Blast Radius, Cache Keeper, Collision Guard

Three real Claude Code mods (not skills — a mod hooks the engine's own
events: tool calls, the prompt band, cross-session state), built via the
`plugin-authoring` skill from the "9 Claude Code Mods You NEED to Install
Right Now" article's descriptions. Full source here is the project's
documented record; the **live, loaded copy a session actually runs is in
that session's required mods folder** (`/root/.claude/dev-mods/<session>/`
per the `plugin-authoring` skill's own instructions) — mods aren't loaded
from an arbitrary repo path, so this copy is for version control, review,
and reuse, not direct loading. To run one, copy its folder into a session's
mods folder (or pass it to `claude --plugin-dir`) and answer the hot-reload
prompt that follows.

## What's built, and what's deliberately cut

### `blast-radius/` — confirms before a destructive Bash command runs

The article says this one "comes straight from Anthropic... install it as a
plugin, no building required" — so what's built here is a fresh,
independent implementation of the same behavior it describes, not a copy of
Anthropic's actual shipped mod (which this session has no access to read).

- `hooks/rules.ts` — pure pattern detection, no `$` dependency, deliberately
  separated from the hook so it can be (and is) unit-tested directly:
  `rm -rf`/`-fr` (any flag order, short or long form) and wildcard deletes,
  `git push --force`/`-f`/`--force-with-lease`, `git reset --hard`,
  `git clean -f`, `git branch -D` (and `--delete --force`), `git checkout --
  <path>`/`git checkout .`, `git restore --worktree`.
- `hooks/register.ts` — the thin glue: a `tool.call` hook on `Bash` that
  calls `$.ui.ask(question, ['Proceed', 'Cancel'])` when a pattern matches
  and denies the call unless the answer is exactly `'Proceed'`. `$.ui.ask`
  is the documented primitive for exactly this ("asks the user in the
  engine's own AskUserQuestion dialog... rejects when dismissed") — a call
  through `$` doesn't count against the hook's own execution-time budget,
  so it can genuinely wait on a human without the dispatch timing out, which
  is what makes "nothing runs until you choose" real rather than aspirational.
- **Cut, stated plainly**: the article's "overwriting a bunch of existing
  files at once" case isn't covered — Edit/Write already go one file at a
  time through the person's own permission prompt, so the risk this mod
  targets (Bash bypassing that prompt entirely) doesn't apply to them the
  same way, and a generic "bulk overwrite" heuristic over arbitrary shell
  commands would be too failure-prone to ship. SQL `DROP TABLE`/`DROP
  DATABASE` wasn't in the article's own named list and isn't covered either.

**A real bug found by testing it**, not assumed away: an early version of
the `git branch -D` rule ran case-insensitively, so it flagged the
*safe*, merged-only `git branch -d` as destructive too — caught by a test
asserting `git branch -d` is *not* flagged, not by inspection. Fixed by
making the `-D`-vs-`-d` check case-sensitive while keeping `git branch`
itself matched loosely. 18/18 tests pass:

```bash
cd blast-radius && claude plugin test .
```

### `cache-keeper/` — prompt-cache countdown, context, rate limits, cost

- `hooks/cache-math.ts` — pure countdown math (`msRemaining`, `shouldWarn`,
  `formatCountdown`), unit-tested with no engine mocking.
- `hooks/register.tsx` — an `AbovePrompt` band showing the countdown,
  `$.session.usage()`'s live context percent and cost, and a "Handoff &
  Compact" button; a `/cache-status` command for the same numbers as text;
  a `$.clock.every(30_000, ...)` timer that sends one `$.ui.notify` warning
  before the estimated cold point and ticks the band's redraw.
- **Stated plainly, not overclaimed**: there is no documented API for the
  real server-side prompt-cache TTL, so the "60 minutes" window is this
  mod's own configurable estimate (`cacheWindowMinutes` in its
  `userConfig`, reset on every non-meta prompt), not a measurement — the
  article's own "detect the real cache window if possible, otherwise
  default to 60 minutes and let me change it" is implemented as exactly
  that fallback, with nothing claimed as detected. The "5-hour and weekly
  usage limits" and "cost" figures *are* real and live, from
  `$.session.usage()`'s `rateLimits` and `cost` fields — the same data the
  status line itself reads. The "Handoff & Compact" button calls the real,
  documented `$.session.compact({ instructions })`, which is this build's
  honest equivalent of the article's literal "write a handoff file, clear,
  paste into a fresh session" flow — that exact three-step mechanic isn't
  exposed to a mod the way the article describes it from inside the CLI, so
  compaction (summarize and keep the essentials, in place) is the closest
  real primitive, not a reproduction of the article's literal UX.

**A real bug found while validating it**, not assumed away: `claude plugin
validate` kept reporting `cache-keeper.lastResetAt is not declared` for a
`$.state` contract that structurally matched the skill's own reference
examples (`pane-state.d.ts`/`band-state.d.ts`) exactly. Isolated by
validating the skill's own `pane.tsx`/`pane-state.d.ts` example pair
unmodified as a control (it passed), then diffing byte-for-byte against
that working case: the difference was that this mod's `types/index.d.ts`
declared the `PluginState` entry as a reference to a separately-named type
alias (`'cache-keeper': CacheKeeperState`) instead of an inline object-type
literal (`'cache-keeper': { lastResetAt: number; ... }`) — the validator's
static check reads the entry's own literal shape and doesn't resolve a
reference to another type. Fixed by keeping `CacheKeeperState` as a named
export for reuse elsewhere in the hooks module, while the `PluginState`
interface itself repeats the shape inline, with a comment explaining why.
8/8 tests pass:

```bash
cd cache-keeper && claude plugin test .
```

### `collision-guard/` — warns before editing a file another session just touched

- `hooks/collision.ts` — pure logic (`collisionToWarnAbout`,
  `formatMinutesAgo`, `storeKeyFor`), unit-tested with no engine mocking.
- `hooks/register.ts` — `tool.call` hooks on `Edit`, `Write`, and
  `NotebookEdit`: before running, checks `$.store` (this plugin's own
  key-value store, which persists across sessions and hot reloads — the
  exact cross-session sharing this mod needs) for a `{ sessionId, at }`
  record under a key namespaced by file path; if another session wrote
  that file within the configurable window (`collisionWindowMinutes`,
  default 30), asks via `$.ui.ask(['Proceed anyway', 'Cancel'])` before
  letting the edit through; after a successful edit, records the current
  session's id and timestamp for the next check.
- **Cut, stated plainly**: the article's "Move to a worktree" and free-text
  "type something else" options aren't implemented — each is a materially
  bigger feature (relocating in-progress work, or a second free-form
  decision path) than this mod's one job of warning before a likely
  collision, and building either half-heartedly would be worse than not
  building it. The bidirectional "what's the other session doing" banner
  is also cut: it needs a second, continuously-updated broadcast of each
  session's current task, not just a per-file edit record, and is a
  different (larger) mechanism than the collision warning itself. Both cuts
  mirror this project's standing discipline of naming a scope cut with a
  reason rather than silently narrowing a feature.

8/8 tests pass:

```bash
cd collision-guard && claude plugin test .
```

## Verification, honestly scoped

Every pattern-matching and arithmetic decision each mod makes is a plain
exported function, tested directly against `claude plugin test` with no
engine mocking — real assertions against real inputs, not "it imports."
`claude plugin validate` passes cleanly on all three (one unavoidable
warning on all three: no `author` field set in `plugin.json`, left
unset since this isn't being published).

What is **not** verified end-to-end: none of the three has been exercised
inside a live, hot-reloaded Claude Code session with a real `$.ui.ask`
dialog actually shown and answered by a person, a real `Bash`/`Edit` tool
call actually denied or allowed, or a real second session actually writing
to `collision-guard`'s shared `$.store`. That would need this session's own
hot-reload prompt answered and a second concurrent session to collide
with — outside what this sandbox session can arrange for itself. Flagged
plainly rather than claimed, same discipline as every other sandbox
limitation this project states (no live Yahoo Finance/EODHD/Anthropic/
Hugging Face access, and now no live two-session mod collision either).
