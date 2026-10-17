"use strict";

const fs = require("fs");
const path = require("path");
const os = require("os");

const { parseEntries, checkFullWipeGuard, withRetry, runSafely } = require("./safety-core");

let passed = 0;
let failed = 0;

function assert(cond, msg) {
  if (cond) {
    passed++;
    console.log(`OK: ${msg}`);
  } else {
    failed++;
    console.error(`FAIL: ${msg}`);
  }
}

async function assertRejects(fn, msg) {
  try {
    await fn();
    failed++;
    console.error(`FAIL: ${msg} (expected rejection, got none)`);
  } catch (e) {
    passed++;
    console.log(`OK: ${msg}`);
  }
}

// --- test fixtures -----------------------------------------------------

const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "repo-manager-safety-test-"));
const allReposFile = path.join(tmpDir, "all_repos.txt");
fs.writeFileSync(allReposFile, ["alpha", "beta", "gamma"].join("\n"));

const noopSleep = () => Promise.resolve();
const fakeLog = (sink) => (msg) => sink.push(msg);

function entries(names, defaultOwner = "me") {
  return parseEntries(names, defaultOwner, false);
}

// --- parseEntries ----------------------------------------------------------

(function testParseEntriesBareMode() {
  const result = parseEntries(["alpha", "beta"], "me", false);
  assert(
    result.every((e) => e.owner === "me" && e.display === e.repo),
    "bare mode: every entry defaults to the given owner, display is the bare repo name"
  );
})();

(function testParseEntriesOwnerRepoMode() {
  const result = parseEntries(["me/alpha", "someorg/beta", "gamma"], "me", true);
  assert(result[0].owner === "me" && result[0].repo === "alpha" && result[0].display === "me/alpha", "owner-repo mode parses an explicit owner/repo line");
  assert(result[1].owner === "someorg" && result[1].repo === "beta", "owner-repo mode parses a different, non-default owner");
  assert(result[2].owner === "me" && result[2].repo === "gamma" && result[2].display === "me/gamma", "owner-repo mode still accepts a bare line, defaulting the owner and showing it in display");
})();

// --- checkFullWipeGuard ------------------------------------------------

(function testFullWipeGuard() {
  const fullMatch = checkFullWipeGuard(entries(["gamma", "alpha", "beta"]), allReposFile, "me", false);
  assert(fullMatch.blocked === true, "full-wipe guard blocks when target entries exactly match all_repos.txt (order-independent)");

  const fullMatchAllowed = checkFullWipeGuard(entries(["gamma", "alpha", "beta"]), allReposFile, "me", true);
  assert(fullMatchAllowed.blocked === false, "full-wipe guard allows the same list through with allowFullMatch");

  const partial = checkFullWipeGuard(entries(["alpha"]), allReposFile, "me", false);
  assert(partial.blocked === false, "full-wipe guard does not block a genuine subset");

  const missingInventory = checkFullWipeGuard(entries(["alpha"]), path.join(tmpDir, "does-not-exist.txt"), "me", false);
  assert(missingInventory.blocked === false, "full-wipe guard no-ops gracefully when no inventory file exists");
})();

(function testFullWipeGuardOwnerRepoMode() {
  // All three entries resolve to the default owner's full inventory,
  // just spelled out as owner/repo — the guard must still catch this.
  const sameOwnerSpelledOut = parseEntries(["me/alpha", "me/beta", "me/gamma"], "me", true);
  const blocked = checkFullWipeGuard(sameOwnerSpelledOut, allReposFile, "me", false);
  assert(blocked.blocked === true, "owner-repo mode: explicit 'defaultOwner/name' entries matching the full inventory still trip the guard");

  // A cross-owner list can never equal a single-owner inventory file.
  const crossOwner = parseEntries(["me/alpha", "someorg/beta", "me/gamma"], "me", true);
  const notBlocked = checkFullWipeGuard(crossOwner, allReposFile, "me", false);
  assert(notBlocked.blocked === false, "owner-repo mode: a cross-owner target list is never mistaken for a single-owner full wipe");
})();

// --- withRetry -----------------------------------------------------------

(async function testRetry() {
  let calls = 0;
  const result = await withRetry(
    async () => {
      calls++;
      if (calls < 3) throw new Error("secondary rate limit hit, please retry");
      return "ok";
    },
    { attempts: 5, baseDelayMs: 1, sleepFn: noopSleep }
  );
  assert(result === "ok" && calls === 3, `retryable error retries until success (got ${calls} calls, result=${result})`);

  let non404calls = 0;
  await assertRejects(
    () =>
      withRetry(
        async () => {
          non404calls++;
          const err = new Error("Not Found");
          err.status = 404;
          throw err;
        },
        { attempts: 5, baseDelayMs: 1, sleepFn: noopSleep }
      ),
    "non-retryable error (404) rejects"
  );
  assert(non404calls === 1, `non-retryable error fails fast without burning retries (got ${non404calls} calls)`);

  let exhausted = 0;
  await assertRejects(
    () =>
      withRetry(
        async () => {
          exhausted++;
          throw new Error("ETIMEDOUT");
        },
        { attempts: 3, baseDelayMs: 1, sleepFn: noopSleep }
      ),
    "retryable error still rejects once attempts are exhausted"
  );
  assert(exhausted === 3, `exhausts exactly the configured attempt count (got ${exhausted})`);
})();

// --- runSafely: dry-run ---------------------------------------------------

(async function testDryRun() {
  const log = [];
  let executeCalls = 0;
  const result = await runSafely({
    operationName: "DELETE",
    entries: entries(["alpha"]),
    allReposFile,
    defaultOwner: "me",
    dryRun: true,
    destructive: true,
    execute: async () => {
      executeCalls++;
    },
    log: fakeLog(log),
  });
  assert(executeCalls === 0, "dry-run never calls execute");
  assert(result.dryRun === true && result.skipped.length === 1, "dry-run reports the entry as skipped");
  assert(log.some((l) => l.includes("[DRY RUN]")), "dry-run logs its intended action");
})();

// --- runSafely: confirmation ----------------------------------------------

(async function testConfirmationMismatch() {
  const log = [];
  let executeCalls = 0;
  const result = await runSafely({
    operationName: "DELETE",
    entries: entries(["alpha"]),
    allReposFile,
    defaultOwner: "me",
    destructive: true,
    confirmPhrase: () => "DELETE 1 REPOS",
    prompt: async () => "nope",
    execute: async () => {
      executeCalls++;
    },
    log: fakeLog(log),
  });
  assert(executeCalls === 0, "a wrong confirmation phrase never calls execute");
  assert(result.aborted === "confirmation-mismatch", "a wrong confirmation phrase reports the correct abort reason");
})();

(async function testConfirmationMatch() {
  const log = [];
  let executeCalls = 0;
  const result = await runSafely({
    operationName: "DELETE",
    entries: entries(["alpha"]),
    allReposFile,
    defaultOwner: "me",
    destructive: true,
    confirmPhrase: () => "DELETE 1 REPOS",
    prompt: async () => "DELETE 1 REPOS",
    execute: async () => {
      executeCalls++;
    },
    log: fakeLog(log),
  });
  assert(executeCalls === 1, "the exact confirmation phrase lets execute run");
  assert(result.succeeded.length === 1, "a matched confirmation reports success");
})();

// --- runSafely: full-wipe guard wired end-to-end ---------------------------

(async function testFullWipeGuardEndToEnd() {
  const log = [];
  let executeCalls = 0;
  const result = await runSafely({
    operationName: "DELETE",
    entries: entries(["alpha", "beta", "gamma"]),
    allReposFile,
    defaultOwner: "me",
    destructive: true,
    prompt: async () => "whatever", // must never even be reached
    execute: async () => {
      executeCalls++;
    },
    log: fakeLog(log),
  });
  assert(executeCalls === 0, "full-wipe guard blocks before confirmation is ever prompted");
  assert(result.aborted === "full-wipe-guard", "full-wipe guard reports the correct abort reason");
})();

// --- runSafely: continue-on-error + summary ---------------------------------

(async function testContinueOnErrorAndSummary() {
  const log = [];
  const result = await runSafely({
    operationName: "ARCHIVE",
    entries: entries(["alpha", "beta", "gamma"]),
    destructive: false,
    execute: async (entry) => {
      if (entry.repo === "beta") throw new Error("boom");
      return "ok";
    },
    log: fakeLog(log),
  });
  assert(result.succeeded.length === 2 && result.failed.length === 1, `one failure doesn't stop the rest (succeeded=${result.succeeded.length}, failed=${result.failed.length})`);
  assert(result.failed[0].repo === "beta", "the failed entry names the right repo");
  assert(log.some((l) => l.includes("2 succeeded, 1 failed")), "a real summary line is printed at the end");
})();

// --- runSafely: owner-repo mode wired end-to-end ----------------------------

(async function testOwnerRepoModeEndToEnd() {
  const log = [];
  const calledWith = [];
  const mixedEntries = parseEntries(["alpha", "someorg/shared-tool"], "me", true);
  const result = await runSafely({
    operationName: "ARCHIVE",
    entries: mixedEntries,
    allReposFile,
    defaultOwner: "me",
    destructive: false,
    execute: async (entry) => {
      calledWith.push(`${entry.owner}/${entry.repo}`);
    },
    log: fakeLog(log),
  });
  assert(result.succeeded.length === 2, "owner-repo mode: both a default-owner and an explicit-owner entry succeed");
  assert(
    calledWith.includes("me/alpha") && calledWith.includes("someorg/shared-tool"),
    `execute receives the resolved owner for each entry (got ${JSON.stringify(calledWith)})`
  );
  assert(log.some((l) => l.includes("someorg/shared-tool")), "log lines use the owner/repo display form for a cross-owner entry");
})();

setTimeout(() => {
  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}, 100);
