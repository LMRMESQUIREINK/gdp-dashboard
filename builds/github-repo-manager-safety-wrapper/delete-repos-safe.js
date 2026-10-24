"use strict";

const { Octokit } = require("@octokit/rest");
require("dotenv").config();

const { loadRepoList, parseEntries, runSafely } = require("./safety-core");

async function main() {
  const args = process.argv.slice(2);
  const dryRun = args.includes("--dry-run");
  const allowFullMatch = args.includes("--force-full");
  const ownerRepoMode = args.includes("--owner-repo");

  const octokit = new Octokit({ auth: process.env.GITHUB_TOKEN });
  const defaultOwner = process.env.GITHUB_USER;

  const rawLines = loadRepoList("delete.txt");
  if (!rawLines) {
    console.log("❌ delete.txt not found. Please create it and add the repo names to DELETE.");
    return;
  }
  if (rawLines.length === 0) {
    console.log("delete.txt is empty — nothing to do.");
    return;
  }

  const entries = parseEntries(rawLines, defaultOwner, ownerRepoMode);

  const result = await runSafely({
    operationName: "DELETE",
    entries,
    allReposFile: "all_repos.txt",
    defaultOwner,
    allowFullMatch,
    dryRun,
    destructive: true,
    confirmPhrase: (count) => `DELETE ${count} REPOS`,
    execute: (entry) => octokit.rest.repos.delete({ owner: entry.owner, repo: entry.repo }),
  });

  if (result.aborted) process.exitCode = 1;
}

if (require.main === module) {
  main().catch((error) => {
    console.error("Unexpected failure:", error);
    process.exitCode = 1;
  });
}

module.exports = { main };
