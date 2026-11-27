# WP-Connect

A complete WordPress plugin (v1.1.0, PHP 7.4+, WP 6.2+, GPL-2.0-or-later)
built literally from a user-supplied, fully-specified build prompt — every
ability name/label/description, the Auto-Optimize skill's instructions, the
AI Agent system prompt, and the admin dashboard's wording/layout were given
verbatim and implemented as given, not reinterpreted.

It connects Claude to a WordPress site over MCP (streamable HTTP, OAuth
2.1 + PKCE, dynamic client registration), with three modes (Full Access /
Abilities / AI Agent), a real abilities engine (1-100 ratings from actual
use, owner-written and Claude-written custom abilities with a lint/approve/
tamper-check lifecycle), backup-and-undo on every write, a skills system
(one built-in Auto-Optimize skill), and an AI Agent mode that runs jobs on
its own against the Anthropic API with risky steps pausing for the owner's
approval.

## How this was proven

No live network access exists in this sandbox to Hostinger/a real WP
install/the Anthropic API — the same standing restriction as every other
build in this project. Instead, a real WordPress 6.7.1 install was stood up
from the official `WordPress/sqlite-database-integration` plugin (no MySQL
needed), served locally with PHP's built-in server, and the plugin was
actually installed, activated, and driven end to end against it:

- All 6 database tables created correctly on activation.
- All 8 admin dashboard tabs render with zero PHP warnings/notices/fatals
  (`WP_DEBUG_LOG` on throughout).
- OAuth: discovery (`/.well-known/oauth-protected-resource` and
  `/oauth-authorization-server`), dynamic client registration, the login
  redirect, the real consent screen, the authorize→code→token exchange,
  wrong-PKCE rejection, reused-code rejection, and the refresh grant all
  exercised for real against the live site.
- MCP: unauthenticated calls correctly 401 with the `WWW-Authenticate`
  header; `initialize`/`ping`/`tools/list` all work; a bare notification
  correctly returns a plain 202; a non-admin authenticated caller correctly
  gets 403.
- A real 1.1MB JPEG was compressed by `image_compress` (1128KB → 133KB,
  resized to 800×600) and then restored byte-for-byte by Undo.
- `db_cleanup` with `keep_revisions: 3` against 8 real revisions correctly
  kept exactly the 3 newest.
- `link_fix` correctly replaced a real broken link and correctly stripped
  a link via an empty `new_url`.
- A Claude-written custom ability was proposed, approved, and run for
  real, then a tampered stored-code row was correctly blocked before
  execution.
- Lessons saved from negative feedback appear in the live tool description
  sent to Claude; ratings move correctly after thumbs feedback.
- Abilities mode correctly hides `run_php`; Full Access mode correctly
  exposes and runs it.
- The AI Agent tick→approval→resolve loop was driven end to end against a
  mocked Anthropic API: an immediate read-only tool call, a risky tool
  call pausing for approval, approval, and a final answer — with the
  approved tool's real effect (a plugin actually activating) confirmed.

## Real bugs found and fixed during that testing

1. **OAuth login redirect dropped the original request.** Redirecting an
   unauthenticated `authorize` call to `wp-login.php` built the return URL
   from `admin_url('admin-post.php')` with no query string, so after
   logging in the owner would land back on a bare `action=wpc_authorize`
   with none of `client_id`/`redirect_uri`/the PKCE challenge/`state` —
   the whole flow would fail post-login. Fixed by building the return URL
   from the real current request URI, so every original parameter
   survives the login round trip.
2. **MCP crashed on `ping`.** The code extracting an `initialize` response's
   `_session_id` into the `Mcp-Session-Id` header used
   `isset($responses[0]['result']['_session_id'])`, which throws
   "Cannot use object of type stdClass as array" on PHP 8+ whenever a
   dispatch result is a plain object rather than an array — exactly what
   a bare `ping` call returns (`new stdClass()`). A single `ping` as the
   first message (a common MCP client liveness check) returned a raw
   HTTP 500. Fixed by checking `is_array(...)` before the nested `isset()`.
3. **A regex delimiter collision silently defeated a link filter.**
   `wpc_extract_links()`'s exclusion pattern used `#` as both the regex
   delimiter and a literal alternative inside it
   (`'#^(mailto:|tel:|#|javascript:|sms:)#i'`), which PHP parses as an
   invalid pattern — `preg_match()` returned `false` with a
   "Unknown modifier" warning on every single link checked, meaning the
   intended `#`/`javascript:`/`sms:` exclusions never actually fired.
   Fixed by switching the delimiter to `~`.
4. **The agent's approval log could claim success for a call that actually
   failed.** `resolve()` hard-coded `"name ✓ (approved)"` whenever the
   owner approved a risky call, without checking whether the tool
   actually succeeded — so a risky action that errored (reproduced with a
   deliberately malformed input) was reported to the owner as having
   worked. Fixed by deriving the log line from the real result.
5. **Every immediately-run tool call in the agent loop executed the
   underlying ability twice.** `tick_locked()` built the log line via
   `run_and_log()` (which calls `WPC_Abilities::run()`) and separately
   built the tool result via `tool_result_block()` (which calls
   `WPC_Abilities::run()` again) — so any non-risky write ability the
   model called ran its real side effect twice per logical call. Confirmed
   via the real run-row count (2 rows for one tool call before the fix,
   1 after). Fixed by running the ability exactly once and deriving both
   the log line and the result block from that single run; the now-dead
   `run_and_log()` was removed.
6. **The in-memory ability registry could go stale after approving,
   restoring, or deleting a custom ability within the same PHP process.**
   Not reachable from any wired request in the shipped plugin (every real
   WordPress request is its own process), but cheap to close: `approve()`,
   `restore_version()`, and `delete_custom()` now refresh the static
   registry entry they just changed.

## Not verified from this sandbox

- Live Hostinger/a real public WordPress install, Claude Desktop/claude.ai
  actually connecting over the internet, and a real Anthropic API key —
  no outbound network access to any of these from here. The OAuth/MCP/
  agent mechanics above were proven against the real code paths with
  mocked network boundaries, not against the real services.
- The Mach-O-equivalent "every host environment" sweep: tested on PHP 8.3
  with SQLite; not tested against MySQL/MariaDB or older PHP 7.4.
