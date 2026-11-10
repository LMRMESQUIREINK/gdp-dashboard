"use strict";

const fs = require("fs");
const readline = require("readline");

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Reads a plain-text repo-list file the same way the original
 * github-repo-manager scripts do: one name per line, blanks stripped.
 * Returns raw lines — use parseEntries() to resolve them against an
 * owner.
 */
function loadRepoList(filePath) {
  if (!fs.existsSync(filePath)) return null;
  return fs
    .readFileSync(filePath, "utf-8")
    .split("\n")
    .map((name) => name.trim())
    .filter((name) => name.length > 0);
}

/**
 * Resolves raw list-file lines into {owner, repo, display} entries.
 *
 * The original scripts hardcode a single owner (GITHUB_USER or
 * TARGET_ORG) for every line in every list file — the README names
 * this explicitly as unsupported ("owner/repository values are not
 * supported"). With ownerRepoMode on, a line containing a "/" is
 * parsed as an explicit owner/repo pair (for managing repos across
 * more than one account/org from one list file); a bare line still
 * falls back to defaultOwner either way, so existing single-owner list
 * files keep working unchanged.
 */
function parseEntries(rawLines, defaultOwner, ownerRepoMode) {
  return rawLines.map((line) => {
    if (ownerRepoMode && line.includes("/")) {
      const slash = line.indexOf("/");
      const owner = line.slice(0, slash).trim();
      const repo = line.slice(slash + 1).trim();
      if (owner && repo) {
        return { owner, repo, display: `${owner}/${repo}` };
      }
    }
    return {
      owner: defaultOwner,
      repo: line,
      display: ownerRepoMode ? `${defaultOwner}/${line}` : line,
    };
  });
}

/**
 * Guards against the failure mode the real repo's README doesn't name:
 * a target list accidentally containing every name that was ever
 * written to all_repos.txt — the natural result of a copy-paste
 * workflow across two unrelated files. If the target entries exactly
 * match the full inventory, that is far more likely to be a mistake
 * than an intentional "act on everything" request, so it's refused
 * unless the caller explicitly opts in with allowFullMatch.
 *
 * all_repos.txt (written by the original 1-fetch-repos.js) only ever
 * lists one owner's repos, so its entries are always normalized against
 * defaultOwner here — a cross-owner target list can only match it if
 * every entry actually resolves to defaultOwner.
 */
function checkFullWipeGuard(entries, allReposFile, defaultOwner, allowFullMatch) {
  const allRepos = loadRepoList(allReposFile);
  if (!allRepos || allRepos.length === 0) return { blocked: false };

  const allSet = new Set(allRepos.map((r) => `${defaultOwner}/${r}`.toLowerCase()));
  const targetSet = new Set(entries.map((e) => `${e.owner}/${e.repo}`.toLowerCase()));

  const isFullMatch =
    targetSet.size === allSet.size && [...targetSet].every((key) => allSet.has(key));

  if (isFullMatch && !allowFullMatch) {
    return {
      blocked: true,
      reason:
        `The target list exactly matches all ${allRepos.length} repositories ` +
        `owned by ${defaultOwner}. This is refused by default because it is the ` +
        `signature of an accidental full-inventory copy-paste, not an ` +
        `intentional request to act on every repository you own. Re-run ` +
        `with --force-full if that really is what you want.`,
    };
  }
  return { blocked: false };
}

/**
 * Prompts on stdin for an exact confirmation phrase. Injectable for
 * tests via the `prompt` option — production code never has to touch
 * this directly.
 */
function realPrompt(question) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  return new Promise((resolve) => {
    rl.question(question, (answer) => {
      rl.close();
      resolve(answer);
    });
  });
}

const RETRYABLE_PATTERN = /secondary rate limit|rate limit exceeded|ETIMEDOUT|ECONNRESET|socket hang up/i;

function isRetryable(error) {
  const status = error && error.status;
  if (typeof status === "number" && status >= 500) return true;
  const message = (error && error.message) || "";
  return RETRYABLE_PATTERN.test(message);
}

/**
 * Calls fn(), retrying with exponential backoff only on errors that
 * look transient (5xx, secondary rate limit, network resets). A 404
 * or other definitive 4xx fails immediately instead of burning retries
 * on something that will never succeed.
 */
async function withRetry(fn, { attempts = 3, baseDelayMs = 500, sleepFn = sleep } = {}) {
  let lastError;
  for (let attempt = 1; attempt <= attempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      if (!isRetryable(error) || attempt === attempts) throw error;
      await sleepFn(baseDelayMs * 2 ** (attempt - 1));
    }
  }
  throw lastError;
}

/**
 * The shared safety envelope every *-safe.js entry point runs its
 * per-repo operation through: full-wipe guard, dry-run, typed
 * confirmation for destructive operations, retry-with-backoff per
 * repo, continue-on-error across the list (same as the original
 * scripts), and a real summary at the end (the originals print nothing
 * comparable).
 *
 * @param {object} opts
 * @param {string} opts.operationName - e.g. "DELETE", "TRANSFER"
 * @param {{owner:string, repo:string, display:string}[]} opts.entries - target entries
 * @param {string} [opts.allReposFile] - inventory file for the full-wipe guard
 * @param {string} [opts.defaultOwner] - owner all_repos.txt's entries belong to
 * @param {boolean} [opts.allowFullMatch] - bypass the full-wipe guard
 * @param {boolean} [opts.dryRun] - list intended actions without calling execute
 * @param {boolean} [opts.destructive] - require typed confirmation before proceeding
 * @param {function(number): string} [opts.confirmPhrase] - given entries.length, the exact phrase to require
 * @param {function({owner,repo,display}): Promise<any>} opts.execute - performs the real operation for one entry
 * @param {function(string): Promise<string>} [opts.prompt] - injectable for tests
 * @param {function} [opts.sleepFn] - injectable for tests
 */
async function runSafely(opts) {
  const {
    operationName,
    entries,
    allReposFile,
    defaultOwner,
    allowFullMatch = false,
    dryRun = false,
    destructive = false,
    confirmPhrase,
    execute,
    prompt = realPrompt,
    sleepFn = sleep,
    log = console.log,
  } = opts;

  if (allReposFile) {
    const guard = checkFullWipeGuard(entries, allReposFile, defaultOwner, allowFullMatch);
    if (guard.blocked) {
      log(`❌ ${guard.reason}`);
      return { aborted: "full-wipe-guard", succeeded: [], failed: [], skipped: [] };
    }
  }

  if (dryRun) {
    entries.forEach((entry) => log(`[DRY RUN] Would ${operationName} ${entry.display}`));
    return { aborted: null, dryRun: true, succeeded: [], failed: [], skipped: [...entries] };
  }

  if (destructive) {
    const phrase = confirmPhrase ? confirmPhrase(entries.length) : `${operationName} ${entries.length}`;
    const answer = await prompt(
      `⚠️  Type "${phrase}" to confirm ${operationName} on ${entries.length} repositories: `
    );
    if (answer.trim() !== phrase) {
      log("❌ Confirmation did not match. Aborting without making any changes.");
      return { aborted: "confirmation-mismatch", succeeded: [], failed: [], skipped: [] };
    }
  }

  const succeeded = [];
  const failed = [];

  for (const entry of entries) {
    try {
      log(`Processing: ${entry.display}...`);
      await withRetry(() => execute(entry), { sleepFn });
      log(`  ✅ ${operationName} succeeded for ${entry.display}`);
      succeeded.push(entry.display);
    } catch (error) {
      log(`  ❌ ${operationName} failed for ${entry.display}: ${error.message}`);
      failed.push({ repo: entry.display, error: error.message });
    }
  }

  log(
    `\n${operationName} complete: ${succeeded.length} succeeded, ${failed.length} failed, ` +
      `out of ${entries.length} total.`
  );

  return { aborted: null, succeeded, failed, skipped: [] };
}

module.exports = {
  loadRepoList,
  parseEntries,
  checkFullWipeGuard,
  withRetry,
  isRetryable,
  runSafely,
  realPrompt,
};
