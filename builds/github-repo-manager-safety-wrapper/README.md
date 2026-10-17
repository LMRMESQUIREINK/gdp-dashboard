# github-repo-manager — Safety Wrapper

A companion to `vijaydeepak-vd/github-repo-manager`'s three mutating
scripts (`2-transfer-repos.js`, `3-change-visibility.js`,
`4-delete-repos.js`), implementing the author's own "What I'd Improve
Next" items (dry-run, better error handling, safer bulk operations) for
real. Full comparison of the blog post's narrative against the actual
repository is in
`/notes/github-repo-manager-weekend-project-analysis.md`.

This is **not** a fork or a PR against the original repo — this session
only has read access to it, and there's no standing instruction in this
project to open PRs against other people's repos unasked. It's a
standalone wrapper in this project's own `/builds/`, following the
original scripts' real patterns exactly (same `.env` vars, same `.txt`
list-file convention, same `@octokit/rest`).

## What it adds

The original repo's README is honest about three limitations: no
dry-run/confirmation step, no retry logic, and (not stated, but found
by reading the delete script directly) nothing stops a target list from
accidentally matching the *entire* repository inventory. This wrapper
addresses all three, for the three irreversible-or-high-impact
operations (delete, transfer, visibility — not archive/unarchive, which
is fully reversible and was left using the original script, to keep
scope matched to actual risk rather than wrapping everything
reflexively):

- **`--dry-run`** — prints exactly what each script would do, per repo,
  without calling any mutating GitHub API.
- **Typed confirmation** — e.g. `Type "DELETE 7 REPOS" to confirm...`;
  anything else aborts with zero API calls made. The exact repo count
  is baked into the phrase so a stale/miscounted list can't be
  confirmed by muscle memory.
- **Full-wipe guard** — if the target list (`delete.txt`, `move.txt`,
  `visibility.txt`) exactly matches `all_repos.txt`'s full contents,
  the run is refused by default with `--force-full` required to
  proceed. This is the specific failure mode the original README
  doesn't name: copy-pasting the wrong file, or forgetting to trim
  `all_repos.txt` down before using it as a target list, would
  otherwise delete/transfer/re-visibility *every* repository the token
  can reach.
- **Retry with backoff** — only on errors that look transient (5xx,
  "secondary rate limit", `ETIMEDOUT`/`ECONNRESET`); a definitive 404
  fails immediately instead of burning three attempts on a name that
  will never resolve.
- **A real summary line** — `N succeeded, M failed, out of T total` —
  the originals print per-repo status but nothing at the end.

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
```

## Verified

`npm test` (`test-safety-core.js`) is a real, self-contained test suite
against a mocked Octokit-shaped client — no GitHub token needed, so
unlike most builds in this project this one could be fully exercised
here rather than flagged as untestable-without-live-access. 21/21
checks pass: the full-wipe guard (blocks an exact match, allows a
genuine subset, allows `--force-full`, no-ops when no inventory file
exists), retry/backoff (retries a transient error to success, fails
fast on a 404, exhausts attempts correctly on a persistent transient
error), dry-run (never calls `execute`), confirmation (wrong phrase
aborts with zero calls, exact phrase proceeds), the full-wipe guard
firing *before* confirmation is ever prompted, and continue-on-error
with an accurate summary.

Beyond the core module, all three CLI entry points
(`delete-repos-safe.js`, `transfer-repos-safe.js`,
`visibility-repos-safe.js`) were run for real against temporary list
files: `--dry-run` on each produced the correct `[DRY RUN] Would ...`
output with zero network calls; the full-wipe guard fired correctly
when a target list was made to exactly match `all_repos.txt` (exit code
1, no prompt reached); and the real (non-dry-run) confirmation prompt
was driven with a deliberately wrong answer via piped stdin, confirming
it aborts before `@octokit/rest` ever constructs a request — the one
path that can't be exercised without a real GitHub token is a
confirmed, successful live API call, same "no live network access"
limitation as every other build in this project that touches an
external API.
