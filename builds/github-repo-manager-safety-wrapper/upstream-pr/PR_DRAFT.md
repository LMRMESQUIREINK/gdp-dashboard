# Draft PR for `vijaydeepak-vd/github-repo-manager`

**This was not opened as a real PR.** This session has read-only access
to `vijaydeepak-vd/github-repo-manager` — there's no fork, no push
access, and no standing instruction in this project to open PRs against
other people's repos unasked. What follows is a ready-to-submit patch
and description, generated from and verified against the real repo, for
you (or the repo owner) to actually open.

## How to submit it

1. Fork `vijaydeepak-vd/github-repo-manager` on GitHub.
2. Clone your fork and apply the patch:
   ```bash
   git clone https://github.com/<your-username>/github-repo-manager
   cd github-repo-manager
   git checkout -b safer-bulk-operations
   git apply /path/to/0001-safer-bulk-operations.patch
   git add -A
   git commit -m "Add dry-run, confirmation, full-wipe guard, retry, and owner/repo support"
   git push -u origin safer-bulk-operations
   ```
3. Open the PR from your fork's `safer-bulk-operations` branch against
   `vijaydeepak-vd/github-repo-manager:main`, using the title and body
   below.

The patch was verified by applying it to a fresh clone of the real repo
(not just the local working copy it was written against) and running
`npm install && npm test` there — 30/30 passing — plus `--dry-run`
smoke tests of all four modified scripts under their real filenames.

---

## Suggested PR title

Add dry-run, confirmation, full-wipe guard, retry, and owner/repo support

## Suggested PR body

### What this adds

Reading through the scripts to understand the bulk-delete flow, I
noticed `4-delete-repos.js`'s only safety net is a 5-second timer — the
README already names "no confirmation prompt or dry-run mode" as a
known limitation, but there's a sharper version of that same gap it
doesn't call out: nothing stops `delete.txt` from accidentally
containing the *entire* contents of `all_repos.txt`, which would delete
every repository the token can reach, irreversibly, on that same
5-second timer. That's the natural failure mode of the documented
copy-paste workflow (generate `all_repos.txt`, copy names you want into
a target file) if a line gets trimmed wrong or the wrong file gets
copied.

This PR adds a small `safety-core.js` module and wires all four
mutating scripts (`2-transfer-repos.js`, `3-change-visibility.js`,
`4-delete-repos.js`, `5-change-archive-status.js`) through it:

- **`--dry-run`** on every mutating script — prints exactly what would
  happen, per repository, with zero API calls.
- **Typed confirmation** before delete/transfer/visibility changes
  (archive is left without it, since it's fully reversible) — e.g.
  `Type "DELETE 7 REPOS" to confirm...`, with the live repository count
  baked into the phrase.
- **A full-wipe guard** — refuses to run when the target list exactly
  matches `all_repos.txt`'s full contents, unless `--force-full` is
  passed. This is the specific scenario above.
- **Retry with exponential backoff**, but only for errors that look
  transient (5xx, secondary rate limit, `ETIMEDOUT`/`ECONNRESET`) — a
  definitive 404 still fails immediately rather than burning three
  attempts on a name that will never resolve.
- **`--owner-repo`** — closes the README's other named limitation
  ("`owner/repository` values are not supported"). A list-file line
  containing `/` is parsed as an explicit `owner/repo` pair; a bare
  line still defaults to the configured owner, so every existing list
  file keeps working unchanged. Useful for transferring or managing
  repositories from more than one source account/org in a single run.
- **`--public`** / **`--unarchive`** flags replace the previous
  "edit the source file to flip a `const`" pattern for one-off runs,
  while leaving the same defaults.
- **A real summary line** at the end of each run (`N succeeded, M
  failed, out of T total`) — the scripts currently print per-repo
  status but nothing at the end.

### Testing

`package.json`'s `test` script currently just echoes "no test
specified." This PR adds a real, self-contained test suite
(`test-safety-core.js`) against a mocked Octokit-shaped client — no
GitHub token needed, so it's runnable in CI as-is. 30 checks, covering
the full-wipe guard (including the two owner/repo-specific cases: an
explicit `owner/name` list that still matches the full inventory, and a
genuinely cross-owner list that correctly does *not* trip the guard),
retry/backoff behavior, dry-run, confirmation match/mismatch, the guard
firing before confirmation is ever prompted, and continue-on-error with
an accurate summary.

Beyond the test suite, I ran all four modified scripts for real
(`--dry-run` against temporary list files, plus driving the real
confirmation prompt with a deliberately wrong answer via piped stdin)
to confirm the actual CLI wiring works, not just the underlying module.

### Compatibility

- Every flag is opt-in via `process.argv` — running a script with no
  flags preserves close-to-the-original behavior (it now requires
  typed confirmation for delete/transfer/visibility instead of a bare
  timer, and reads `--public`/`--unarchive` instead of a source-edited
  `const`; archive is otherwise unchanged).
- Existing list files (bare repository names) work unchanged; `/`
  syntax only activates with `--owner-repo`.
- No new dependencies — same `@octokit/rest` and `dotenv` as before.

Happy to adjust anything here — in particular, I kept the CLI-flag
style (`--public`, `--unarchive`) rather than the original
edit-the-source-`const` pattern for one-off visibility/archive
direction, since it means `3-change-visibility.js`/
`5-change-archive-status.js` never need local edits to flip direction,
but that's a judgment call and easy to revert if you'd rather keep the
`const` toggle.
