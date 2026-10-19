// A named export for convenient reuse in the hooks module. The interface
// below repeats the shape inline rather than referencing this: the plugin
// validator's static check reads the PluginState entry's own literal shape
// and does not follow a reference to a separately-named type alias.
export type CacheKeeperState = { lastResetAt: number; warnedThisWindow: boolean; tick: number }

declare module 'claude-code' {
  interface PluginState {
    'cache-keeper': { lastResetAt: number; warnedThisWindow: boolean; tick: number }
  }
}
