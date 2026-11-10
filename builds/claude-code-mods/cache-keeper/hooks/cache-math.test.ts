import { expect, test } from 'claude-code/testing'

import { formatCountdown, msRemaining, shouldWarn } from './cache-math'

test('msRemaining counts down from the window', () => {
  const now = 1_000_000
  const lastResetAt = now - 10 * 60_000 // 10 minutes ago
  expect(msRemaining(now, lastResetAt, 60)).toBe(50 * 60_000)
})

test('msRemaining never goes negative once the window has passed', () => {
  const now = 1_000_000
  const lastResetAt = now - 90 * 60_000 // 90 minutes ago, window is 60
  expect(msRemaining(now, lastResetAt, 60)).toBe(0)
})

test('shouldWarn is false well before the warning threshold', () => {
  expect(shouldWarn(30 * 60_000, 5, false)).toBe(false)
})

test('shouldWarn is true once inside the warning window and not yet warned', () => {
  expect(shouldWarn(4 * 60_000, 5, false)).toBe(true)
})

test('shouldWarn is false once already warned this window', () => {
  expect(shouldWarn(4 * 60_000, 5, true)).toBe(false)
})

test('shouldWarn is false once the cache is already cold (0 remaining)', () => {
  expect(shouldWarn(0, 5, false)).toBe(false)
})

test('formatCountdown renders minutes and zero-padded seconds', () => {
  expect(formatCountdown(65_000)).toBe('1m 05s')
})

test('formatCountdown renders 0m 00s at or below zero', () => {
  expect(formatCountdown(0)).toBe('0m 00s')
  expect(formatCountdown(-500)).toBe('0m 00s')
})
