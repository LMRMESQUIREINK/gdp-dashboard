"use strict";

const { Octokit } = require("@octokit/rest");
require("dotenv").config();

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const { loadRepoList, parseEntries, runSafely } = require("./safety-core");

async function changeVisibilityOne(octokit, entry, makePrivate) {
  const { owner, repo } = entry;
  const { data: repoInfo } = await octokit.rest.repos.get({ owner, repo });
  const wasArchived = repoInfo.archived;

  if (wasArchived) {
    await octokit.rest.repos.update({ owner, repo, archived: false });
    await sleep(3000);
  }

  await octokit.rest.repos.update({ owner, repo, private: makePrivate });
  await sleep(3000);

  if (wasArchived) {
    await octokit.rest.repos.update({ owner, repo, archived: true });
    await sleep(3000);
  }
}

async function main() {
  const args = process.argv.slice(2);
  const dryRun = args.includes("--dry-run");
  const allowFullMatch = args.includes("--force-full");
  const ownerRepoMode = args.includes("--owner-repo");
  const makePrivate = !args.includes("--public");

  const octokit = new Octokit({ auth: process.env.GITHUB_TOKEN });
  const defaultOwner = process.env.GITHUB_USER;

  const rawLines = loadRepoList("visibility.txt");
  if (!rawLines) {
    console.log("❌ visibility.txt not found. Please create it and add the repo names.");
    return;
  }
  if (rawLines.length === 0) {
    console.log("visibility.txt is empty — nothing to do.");
    return;
  }

  const entries = parseEntries(rawLines, defaultOwner, ownerRepoMode);

  const result = await runSafely({
    operationName: makePrivate ? "MAKE PRIVATE" : "MAKE PUBLIC",
    entries,
    allReposFile: "all_repos.txt",
    defaultOwner,
    allowFullMatch,
    dryRun,
    destructive: true,
    confirmPhrase: (count) => `${makePrivate ? "PRIVATE" : "PUBLIC"} ${count} REPOS`,
    execute: (entry) => changeVisibilityOne(octokit, entry, makePrivate),
  });

  if (result.aborted) process.exitCode = 1;
}

if (require.main === module) {
  main().catch((error) => {
    console.error("Unexpected failure:", error);
    process.exitCode = 1;
  });
}

module.exports = { main, changeVisibilityOne };
