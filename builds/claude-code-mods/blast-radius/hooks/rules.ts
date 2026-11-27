/**
 * Pure destructive-command detection, kept separate from the hooks module so
 * it can be unit-tested directly with no engine mocking: given a shell
 * command string, return a short reason it is destructive, or null.
 *
 * Deliberately scoped to what the command string itself says, not what it
 * will actually do (a real, narrow gap, same honesty this project states for
 * every pattern-based detector): an alias, a wrapper script, or a command
 * built from a variable Claude only resolves at execution time can dodge
 * these patterns. It only catches Bash-level destructive operations named by
 * the mods article (delete, force-push, hard-reset, force-clean, force-
 * delete a branch, discard working-tree changes) — not every way a tool call
 * could be destructive (Edit/Write overwrite one file at a time and already
 * go through the person's own permission prompt, so they are out of scope
 * here on purpose).
 */

export type DestructiveMatch = {
  reason: string
}

function hasRmRecursiveForce(command: string): string | null {
  // Matches "rm" followed, within the next couple of tokens, by short flags
  // that combine r and f in either order (-rf, -fr, -rvf, ...) or the long
  // forms, in any order.
  const rmWithShortFlags =
    /\brm\s+(?:\S+\s+){0,2}?-\w*r\w*f\w*\b|\brm\s+(?:\S+\s+){0,2}?-\w*f\w*r\w*\b/i
  const rmWithLongFlags =
    /\brm\s+[^|;&\n]*--recursive\b[^|;&\n]*--force\b|\brm\s+[^|;&\n]*--force\b[^|;&\n]*--recursive\b/i
  if (rmWithShortFlags.test(command) || rmWithLongFlags.test(command)) {
    return 'recursively force-deletes files or folders (rm -rf)'
  }
  return null
}

function hasRmWildcard(command: string): string | null {
  // "rm" (any flags) targeting something with a shell glob character.
  if (/\brm\s+(?:-\S+\s+)*\S*[*?[]\S*/i.test(command)) {
    return 'deletes files matching a wildcard'
  }
  return null
}

const RULES: Array<{ pattern: RegExp; reason: string }> = [
  {
    pattern: /\bgit\s+push\b[^\n]*(?:--force(?:-with-lease)?\b|\s-f\b)/i,
    reason: 'force-pushes to git, which can overwrite remote history',
  },
  {
    pattern: /\bgit\s+reset\b[^\n]*--hard\b/i,
    reason: 'resets a branch and discards changes (git reset --hard)',
  },
  {
    pattern: /\bgit\s+clean\b[^\n]*-\w*f\w*/i,
    reason: 'deletes untracked files (git clean -f)',
  },
  {
    // -D (force delete) is genuinely different from -d (safe, merged-only
    // delete) — the flag check below is deliberately case-sensitive even
    // though "git branch" itself is matched loosely.
    pattern: /\bgit\s+branch\b[^\n]*(?:(?:^|\s)-\w*D\w*(?:\s|$)|--delete\b[^\n]*--force\b|--force\b[^\n]*--delete\b)/,
    reason: 'force-deletes a git branch, even if unmerged (git branch -D)',
  },
  {
    pattern: /\bgit\s+checkout\s+(?:--\s+\S|\.\s*$)/i,
    reason: 'discards uncommitted changes in the working tree (git checkout .)',
  },
  {
    pattern: /\bgit\s+restore\b[^\n]*(?:\.\s*$|--worktree\b)/i,
    reason: 'discards uncommitted changes in the working tree (git restore)',
  },
]

export function destructiveReason(command: string): string | null {
  const rmReason = hasRmRecursiveForce(command) ?? hasRmWildcard(command)
  if (rmReason) return rmReason

  for (const rule of RULES) {
    if (rule.pattern.test(command)) return rule.reason
  }
  return null
}
