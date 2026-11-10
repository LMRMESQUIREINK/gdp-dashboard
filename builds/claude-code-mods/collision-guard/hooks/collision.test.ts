import { expect, test } from 'claude-code/testing'

import { collisionToWarnAbout, formatMinutesAgo, storeKeyFor } from './collision'

test('no record means no warning', () => {
  expect(collisionToWarnAbout(null, 'session-a', 1_000_000, 30)).toBeNull()
})

test('the same session editing again is not a collision', () => {
  const record = { sessionId: 'session-a', at: 1_000_000 }
  expect(collisionToWarnAbout(record, 'session-a', 1_000_010, 30)).toBeNull()
})

test('another session editing recently is a collision', () => {
  const record = { sessionId: 'session-a', at: 1_000_000 }
  const now = 1_000_000 + 5 * 60_000 // 5 minutes later
  expect(collisionToWarnAbout(record, 'session-b', now, 30)).toEqual(record)
})

test('another session editing outside the window is not a collision', () => {
  const record = { sessionId: 'session-a', at: 1_000_000 }
  const now = 1_000_000 + 45 * 60_000 // 45 minutes later, window is 30
  expect(collisionToWarnAbout(record, 'session-b', now, 30)).toBeNull()
})

test('right at the window edge is not a collision (exclusive)', () => {
  const record = { sessionId: 'session-a', at: 1_000_000 }
  const now = 1_000_000 + 30 * 60_000 // exactly 30 minutes later
  expect(collisionToWarnAbout(record, 'session-b', now, 30)).toBeNull()
})

test('storeKeyFor is stable and namespaced per file path', () => {
  expect(storeKeyFor('/repo/src/app.ts')).toBe('collision-guard:file:/repo/src/app.ts')
  expect(storeKeyFor('/repo/src/app.ts')).not.toBe(storeKeyFor('/repo/src/other.ts'))
})

test('formatMinutesAgo rounds to whole minutes', () => {
  expect(formatMinutesAgo(1_000_000 + 5 * 60_000 + 20_000, 1_000_000)).toBe('5 minutes ago')
})

test('formatMinutesAgo special-cases under a minute', () => {
  expect(formatMinutesAgo(1_000_000 + 10_000, 1_000_000)).toBe('under a minute ago')
})
