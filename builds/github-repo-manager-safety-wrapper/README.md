# github-repo-manager — Safety Wrapper

A companion to `vijaydeepak-vd/github-repo-manager`'s four mutating
scripts (`2-transfer-repos.js`, `3-change-visibility.js`,
`4-delete-repos.js`, `5-change-archive-status.js`), implementing the
author's own "What I'd Improve Next" items (dry-run, better error
handling, safer bulk operations) plus the README's own named
limitation (no `owner/repository` support) for real. Full comparison of
the blog post's narrative against the actual repository is in
`/notes/github-repo-manager-weekend-project-analysis.md`.

This is **not** a fork or a PR against the original repo — this session
only has read access to it, and there's no standing instruction in this
project to open PRs against other people's repos unasked. It's a
standalone wrapper in this project's own `/builds/`, following the
original scripts' real patterns exactly (same `.env` vars, same `.txt`
list-file convention, same `@octokit/rest`).

## What it adds

The original repo's README is honest about three limitations: no
dry-run/confirmation step, no retry logic, and no `owner/repository`
support in list files ("not supported"). Reading the delete script
directly found a fourth, unstated one: nothing stops a target list from
accidentally matching the *entire* repository inventory. This wrapper
addresses all four, across all five original operations
(fetch needs no wrapping — it's read-only):

- **`--dry-run`** — prints exactly what each script would do, per repo,
  without calling any mutating GitHub API.
- **Typed confirmation** (delete/transfer/visibility only — see below) —
  e.g. `Type "DELETE 7 REPOS" to confirm...`; anything else aborts with
  zero API calls made. The exact repo count is baked into the phrase so
  a stale/miscounted list can't be confirmed by muscle memory.
- **Full-wipe guard** — if the target list (`delete.txt`, `move.txt`,
  `visibility.txt`, `archive.txt`) exactly matches `all_repos.txt`'s
  full contents, the run is refused by default with `--force-full`
  required to proceed. This is the specific failure mode the original
  README doesn't name: copy-pasting the wrong file, or forgetting to
  trim `all_repos.txt` down before using it as a target list, would
  otherwise act on *every* repository the token can reach.
- **Retry with backoff** — only on errors that look transient (5xx,
  "secondary rate limit", `ETIMEDOUT`/`ECONNRESET`); a definitive 404
  fails immediately instead of burning three attempts on a name that
  will never resolve.
- **`--owner-repo`** — list-file lines can be `owner/repo` instead of
  assuming one fixed owner for every line (the original README's own
  "not supported" limitation). A bare line still works and defaults to
  `GITHUB_USER`, so existing list files need no changes. Useful for
  anyone managing repositories across more than one account or org from
  a single run — e.g. collecting repos from several source accounts
  into one `TARGET_ORG` via `transfer-repos-safe.js --owner-repo`. The
  full-wipe guard understands this too: it normalizes `all_repos.txt`
  (always single-owner, since that's all `1-fetch-repos.js` ever
  writes) against the *default* owner, so a cross-owner target list is
  never mistaken for a full wipe of one account, while a list that
  spells out `GITHUB_USER/name` for every repo still trips the guard
  correctly.
- **A real summary line** — `N succeeded, M failed, out of T total` —
  the originals print per-repo status but nothing at the end.
- **Archive/unarchive is now wrapped too** (`archive-repos-safe.js`),
  for consistency with the other four — but deliberately *without*
  typed confirmation, since archiving is fully reversible in a way
  delete/transfer/visibility changes aren't (those can cascade into
  forks, Pages, Actions, and access). `--dry-run` and the full-wipe
  guard still apply: "I meant to archive one repo and archived fifty"
  is worth catching even when it's undoable.

## Usage

Same `.env` as the original (`GITHUB_TOKEN`, `GITHUB_USER`, and
`TARGET_ORG` for the transfer script) and the same list-file convention
(`delete.txt`, `move.txt`, `visibility.txt`, generated the same way via
the original `1-fetch-repos.js` into `all_repos.txt`).

```bash
npm install

node delete-repos-safe.js --dry-run       # see what would happen
node delete-repos-safe.js                 # real run, requires typed confirmation
node delete-repos-safe.js --force-full    # only if you really mean "every repo"

node transfer-repos-safe.js --dry-run
node visibility-repos-safe.js --dry-run --public   # same --public flag the original script toggles via source edit

node archive-repos-safe.js --dry-run
node archive-repos-safe.js --unarchive --dry-run

# list files can mix owners when --owner-repo is passed:
#   alpha                 -> defaults to GITHUB_USER/alpha
#   someorg/shared-tool    -> explicit owner
node transfer-repos-safe.js --owner-repo --dry-run
```

## Verified

`npm test` (`test-safety-core.js`) is a real, self-contained test suite
against a mocked Octokit-shaped client — no GitHub token needed, so
unlike most builds in this project this one could be fully exercised
here rather than flagged as untestable-without-live-access. 30/30
checks pass: `parseEntries` (bare mode, explicit `owner/repo` lines, a
mixed list defaulting only the bare lines), the full-wipe guard (blocks
an exact match, allows a genuine subset, allows `--force-full`, no-ops
when no inventory file exists, and — the two owner-repo-specific cases
— still blocks when every line spells out `defaultOwner/name` for the
full inventory, and correctly does *not* block a cross-owner list),
retry/backoff (retries a transient error to success, fails fast on a
404, exhausts attempts correctly on a persistent transient error),
dry-run (never calls `execute`), confirmation (wrong phrase aborts with
zero calls, exact phrase proceeds), the full-wipe guard firing *before*
confirmation is ever prompted, continue-on-error with an accurate
summary, and `runSafely` end-to-end with a mixed default-owner/explicit-
owner entry list (confirms `execute` receives the correctly resolved
owner for each, and log lines show the right display form).

Beyond the core module, all four CLI entry points
(`delete-repos-safe.js`, `transfer-repos-safe.js`,
`visibility-repos-safe.js`, `archive-repos-safe.js`) were run for real
against temporary list files: `--dry-run` on each produced the correct
`[DRY RUN] Would ...` output with zero network calls, including
`--owner-repo` mode showing the right `owner/repo` display strings for
a mixed-owner list; the full-wipe guard fired correctly both in bare
mode and when a target list spelled out `GITHUB_USER/name` for the
full inventory (exit code 1, no prompt reached), and correctly did
*not* fire for a cross-owner list even though it had the same length as
the inventory; and the real (non-dry-run) confirmation prompt was
driven with a deliberately wrong answer via piped stdin, confirming it
aborts before `@octokit/rest` ever constructs a request. The one path
that can't be exercised without a real GitHub token is a confirmed,
successful live API call, same "no live network access" limitation as
every other build in this project that touches an external API.
