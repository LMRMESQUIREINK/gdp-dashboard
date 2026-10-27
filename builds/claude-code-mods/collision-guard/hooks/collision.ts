/**
 * Pure collision-detection logic, kept separate from the hooks module so it
 * can be unit-tested with no engine mocking.
 *
 * Scope, stated plainly: this catches the core case the mods article's own
 * worked example shows (session A edits a file, session B edits the same
 * file minutes later with no idea). It does not implement "move to a
 * worktree" or the free-text "type something else" option the article
 * describes, nor the bidirectional "what's the other session doing" banner
 * — each is a materially bigger feature (spawning/relocating work, or a
 * second cross-session broadcast channel) than this mod's one job of
 * warning before a likely-colliding write, and is cut here for that reason,
 * not silently narrowed.
 */

export type CollisionRecord = {
  sessionId: string
  at: number
}

/**
 * Returns the record to warn about, or null when there is nothing to warn
 * about: no record, the same session wrote it, or it is older than the
 * window.
 */
export function collisionToWarnAbout(
  record: CollisionRecord | null,
  currentSessionId: string,
  now: number,
  windowMinutes: number,
): CollisionRecord | null {
  if (record === null) return null
  if (record.sessionId === currentSessionId) return null
  if (now - record.at >= windowMinutes * 60_000) return null
  return record
}

export function storeKeyFor(filePath: string): string {
  return `collision-guard:file:${filePath}`
}

export function formatMinutesAgo(now: number, at: number): string {
  const minutes = Math.max(0, Math.round((now - at) / 60_000))
  return minutes <= 1 ? 'under a minute ago' : `${minutes} minutes ago`
}
