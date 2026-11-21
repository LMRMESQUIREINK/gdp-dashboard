import type { Engine, Register } from 'claude-code'

import { collisionToWarnAbout, formatMinutesAgo, storeKeyFor } from './collision'
import type { CollisionRecord } from './collision'

async function guard(
  $: Engine,
  filePath: string,
  windowMinutes: number,
): Promise<{ deny: string } | null> {
  const sessionId = await $.session.id()
  const now = await $.clock.now()
  const raw = (await $.store.get(storeKeyFor(filePath))) as CollisionRecord | undefined

  const collision = collisionToWarnAbout(raw ?? null, sessionId, now, windowMinutes)
  if (collision === null) return null

  const choice = await $.ui.ask(
    `${$.plugin.name}: another session edited ${filePath} ${formatMinutesAgo(now, collision.at)}. Proceed anyway?`,
    ['Proceed anyway', 'Cancel'],
  )
  if (choice === 'Proceed anyway') return null
  return { deny: `${$.plugin.name}: cancelled — another session touched ${filePath} recently` }
}

async function record($: Engine, filePath: string): Promise<void> {
  const sessionId = await $.session.id()
  const now = await $.clock.now()
  const value: CollisionRecord = { sessionId, at: now }
  await $.store.set(storeKeyFor(filePath), value)
}

export const register: Register = (on, options) => {
  const windowMinutes = Number(options.collisionWindowMinutes ?? 30)

  on('tool.call', { tool: 'Edit' }, async ($, e, next) => {
    const denial = await guard($, e.file_path, windowMinutes)
    if (denial) return denial

    const ran = await next(e)
    if (ran.deny === undefined) await record($, e.file_path)
    return ran
  }).catch(($, e, next) =>
    next.called ? next(e) : { deny: `${$.plugin.name}: the collision check failed; denying to be safe` },
  )

  on('tool.call', { tool: 'Write' }, async ($, e, next) => {
    const denial = await guard($, e.file_path, windowMinutes)
    if (denial) return denial

    const ran = await next(e)
    if (ran.deny === undefined) await record($, e.file_path)
    return ran
  }).catch(($, e, next) =>
    next.called ? next(e) : { deny: `${$.plugin.name}: the collision check failed; denying to be safe` },
  )

  on('tool.call', { tool: 'NotebookEdit' }, async ($, e, next) => {
    const denial = await guard($, e.notebook_path, windowMinutes)
    if (denial) return denial

    const ran = await next(e)
    if (ran.deny === undefined) await record($, e.notebook_path)
    return ran
  }).catch(($, e, next) =>
    next.called ? next(e) : { deny: `${$.plugin.name}: the collision check failed; denying to be safe` },
  )
}
