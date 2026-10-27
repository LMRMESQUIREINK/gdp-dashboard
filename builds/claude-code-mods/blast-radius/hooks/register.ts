import type { Register } from 'claude-code'

import { destructiveReason } from './rules'

export const register: Register = on => {
  on('tool.call', { tool: 'Bash' }, async ($, e, next) => {
    const reason = destructiveReason(e.command)
    if (!reason) return next(e)

    const choice = await $.ui.ask(
      `${$.plugin.name}: this command ${reason}.\n\n${e.command}\n\nProceed?`,
      ['Proceed', 'Cancel'],
    )

    return choice === 'Proceed'
      ? next(e)
      : { deny: `${$.plugin.name}: cancelled — ${reason}` }
  }).catch(($, e, next) =>
    next.called
      ? next(e)
      : { deny: `${$.plugin.name}: the destructive-command check failed; denying to be safe` },
  )
}
