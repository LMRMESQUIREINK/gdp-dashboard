"use strict";

const fs = require("fs");
const readline = require("readline");

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Reads a plain-text repo-list file the same way the original
 * github-repo-manager scripts do: one name per line, blanks stripped.
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
 * Guards against the failure mode the real repo's README doesn't name:
 * delete.txt (or any target list) accidentally containing every name
 * that was ever written to all_repos.txt — the natural result of a
 * copy-paste workflow across two unrelated files. If the target list
 * exactly matches the full inventory, that is far more likely to be a
 * mistake than an intentional "wipe everything" request, so it's
 * refused unless the caller explicitly opts in with allowFullMatch.
 */
function checkFullWipeGuard(targetRepos, allReposFile, allowFullMatch) {
  const allRepos = loadRepoList(allReposFile);
  if (!allRepos || allRepos.length === 0) return { blocked: false };

  const targetSet = new Set(targetRepos.map((r) => r.toLowerCase()));
  const allSet = new Set(allRepos.map((r) => r.toLowerCase()));

  const isFullMatch =
    targetSet.size === allSet.size &&
    [...targetSet].every((name) => allSet.has(name));

  if (isFullMatch && !allowFullMatch) {
    return {
      blocked: true,
      reason:
        `The target list exactly matches all ${allRepos.length} repositories ` +
        `in ${allReposFile}. This is refused by default because it is the ` +
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
 * @param {string[]} opts.repos - target repo names
 * @param {string} [opts.allReposFile] - inventory file for the full-wipe guard
 * @param {boolean} [opts.allowFullMatch] - bypass the full-wipe guard
 * @param {boolean} [opts.dryRun] - list intended actions without calling execute
 * @param {boolean} [opts.destructive] - require typed confirmation before proceeding
 * @param {function(number): string} [opts.confirmPhrase] - given repos.length, the exact phrase to require
 * @param {function(string): Promise<any>} opts.execute - performs the real operation for one repo
 * @param {function(string): Promise<string>} [opts.prompt] - injectable for tests
 * @param {function} [opts.sleepFn] - injectable for tests
 */
async function runSafely(opts) {
  const {
    operationName,
    repos,
    allReposFile,
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
    const guard = checkFullWipeGuard(repos, allReposFile, allowFullMatch);
    if (guard.blocked) {
      log(`❌ ${guard.reason}`);
      return { aborted: "full-wipe-guard", succeeded: [], failed: [], skipped: [] };
    }
  }

  if (dryRun) {
    repos.forEach((repo) => log(`[DRY RUN] Would ${operationName} ${repo}`));
    return { aborted: null, dryRun: true, succeeded: [], failed: [], skipped: [...repos] };
  }

  if (destructive) {
    const phrase = confirmPhrase ? confirmPhrase(repos.length) : `${operationName} ${repos.length}`;
    const answer = await prompt(
      `⚠️  Type "${phrase}" to confirm ${operationName} on ${repos.length} repositories: `
    );
    if (answer.trim() !== phrase) {
      log("❌ Confirmation did not match. Aborting without making any changes.");
      return { aborted: "confirmation-mismatch", succeeded: [], failed: [], skipped: [] };
    }
  }

  const succeeded = [];
  const failed = [];

  for (const repo of repos) {
    try {
      log(`Processing: ${repo}...`);
      await withRetry(() => execute(repo), { sleepFn });
      log(`  ✅ ${operationName} succeeded for ${repo}`);
      succeeded.push(repo);
    } catch (error) {
      log(`  ❌ ${operationName} failed for ${repo}: ${error.message}`);
      failed.push({ repo, error: error.message });
    }
  }

  log(
    `\n${operationName} complete: ${succeeded.length} succeeded, ${failed.length} failed, ` +
      `out of ${repos.length} total.`
  );

  return { aborted: null, succeeded, failed, skipped: [] };
}

module.exports = {
  loadRepoList,
  checkFullWipeGuard,
  withRetry,
  isRetryable,
  runSafely,
  realPrompt,
};
