import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

import { formatCountdown, msRemaining, shouldWarn } from './cache-math'
// Imported for its 'claude-code' module augmentation (declares the
// 'cache-keeper' entry in PluginState) — the atoms below are typed from it.
import type { CacheKeeperState } from '../types'

const lastResetAt = atom(
  { plugin: 'cache-keeper', key: 'lastResetAt' } as const,
  0 as CacheKeeperState['lastResetAt'],
)
const warnedThisWindow = atom(
  { plugin: 'cache-keeper', key: 'warnedThisWindow' } as const,
  false as CacheKeeperState['warnedThisWindow'],
)
const tick = atom({ plugin: 'cache-keeper', key: 'tick' } as const, 0 as CacheKeeperState['tick'])

export const register: Register = (on, options) => {
  const windowMinutes = Number(options.cacheWindowMinutes ?? 60)
  const warnBeforeMinutes = Number(options.warnBeforeMinutes ?? 5)
  let cancelTimer: (() => void) | null = null

  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'cache-status',
      description: 'Show the prompt-cache countdown, context size, rate limits and session cost',
    })

    const now = await $.clock.now()
    await update($, lastResetAt, current => current || now)

    cancelTimer = $.clock.every(30_000, async () => {
      const nowTick = await $.clock.now()
      const resetAt = await read($, lastResetAt)
      const remaining = msRemaining(nowTick, resetAt, windowMinutes)
      const warned = await read($, warnedThisWindow)

      if (shouldWarn(remaining, warnBeforeMinutes, warned)) {
        await $.ui.notify(`Prompt cache goes cold in about ${warnBeforeMinutes} minutes.`, {
          title: 'Cache Keeper',
        })
        await update($, warnedThisWindow, () => true)
      }

      await update($, tick, n => n + 1)
    })

    return next(e)
  })

  on('session.end', ($, e, next) => {
    cancelTimer?.()
    return next(e)
  })

  on('prompt.submit', async ($, e, next) => {
    if (!e.isMeta) {
      const now = await $.clock.now()
      await update($, lastResetAt, () => now)
      await update($, warnedThisWindow, () => false)
    }
    return next(e)
  })

  on('command.run', { command: 'cache-status' }, async $ => {
    const usage = await $.session.usage()
    const now = await $.clock.now()
    const resetAt = await read($, lastResetAt)
    const remaining = msRemaining(now, resetAt, windowMinutes)

    const lines = [
      `Cache estimated cold in ~${formatCountdown(remaining)} (resets on your next prompt; see this mod's README for why this is an estimate, not a measurement).`,
      `Context: ${usage.context.tokens ?? '?'} / ${usage.context.window} tokens (${usage.context.percent ?? '?'}%)`,
      ...usage.rateLimits.map(
        r => `${r.kind}: ${r.percentUsed}% used${r.resetsAt ? `, resets ${r.resetsAt}` : ''}`,
      ),
      usage.cost ? `Session cost so far: $${usage.cost.usd.toFixed(2)}` : 'Session cost: not available',
    ]

    return { text: lines.join('\n') }
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const resetAt = await read($, lastResetAt)
    await read($, tick) // subscribes this render to the periodic timer's ticks
    const now = await $.clock.now()
    const remaining = msRemaining(now, resetAt, windowMinutes)
    const usage = await $.session.usage()

    const { Box, Text, Button } = $.ui.resolve(e)

    return (
      <Box>
        <Text dimColor>
          Cache ~{formatCountdown(remaining)} · Context {usage.context.percent ?? '?'}% ·{' '}
          {usage.cost ? `$${usage.cost.usd.toFixed(2)}` : 'cost n/a'}{' '}
        </Text>
        <Button
          key="handoff"
          label="Handoff & Compact"
          onPress={() =>
            $.session.compact({
              instructions:
                'Write a short handoff: the decisions made so far, the current state, and the next steps — then continue the work from there.',
            })
          }
        />
      </Box>
    )
  })
}
