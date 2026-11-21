/**
 * Pure cache-countdown math, kept separate from the hooks module so it can
 * be unit-tested with no engine mocking.
 *
 * There is no documented API for the real server-side prompt-cache TTL, so
 * `lastResetAt`/`windowMinutes` are this mod's own estimate (reset on every
 * non-meta prompt, defaulting to 60 minutes), not a measurement — stated
 * plainly rather than implied as exact.
 */

export function msRemaining(now: number, lastResetAt: number, windowMinutes: number): number {
  return Math.max(0, windowMinutes * 60_000 - (now - lastResetAt))
}

export function shouldWarn(remainingMs: number, warnBeforeMinutes: number, alreadyWarned: boolean): boolean {
  return !alreadyWarned && remainingMs > 0 && remainingMs <= warnBeforeMinutes * 60_000
}

export function formatCountdown(ms: number): string {
  const totalSeconds = Math.max(0, Math.round(ms / 1000))
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${minutes}m ${seconds.toString().padStart(2, '0')}s`
}
