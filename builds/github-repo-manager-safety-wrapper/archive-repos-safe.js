"use strict";

const { Octokit } = require("@octokit/rest");
require("dotenv").config();

const { loadRepoList, parseEntries, runSafely } = require("./safety-core");

async function changeArchiveStatusOne(octokit, entry, archiveRepos) {
  const { owner, repo } = entry;
  const { data: repoInfo } = await octokit.rest.repos.get({ owner, repo });

  if (repoInfo.archived === archiveRepos) {
    return; // already in the requested state — same skip behavior as the original script
  }

  await octokit.rest.repos.update({ owner, repo, archived: archiveRepos });
}

async function main() {
  const args = process.argv.slice(2);
  const dryRun = args.includes("--dry-run");
  const allowFullMatch = args.includes("--force-full");
  const ownerRepoMode = args.includes("--owner-repo");
  const archiveRepos = !args.includes("--unarchive");

  const octokit = new Octokit({ auth: process.env.GITHUB_TOKEN });
  const defaultOwner = process.env.GITHUB_USER;

  const rawLines = loadRepoList("archive.txt");
  if (!rawLines) {
    console.log("❌ archive.txt not found. Please create it and add the repo names.");
    return;
  }
  if (rawLines.length === 0) {
    console.log("archive.txt is empty — nothing to do.");
    return;
  }

  const entries = parseEntries(rawLines, defaultOwner, ownerRepoMode);

  // Archiving/unarchiving is fully reversible (unlike delete, transfer,
  // and visibility changes, which can cascade into forks, Pages,
  // Actions, and access), so this intentionally does NOT set
  // destructive: true — no typed confirmation is required. --dry-run
  // and the full-wipe guard still apply, since "I meant to archive one
  // repo and archived all of them" is still worth catching even when
  // it's reversible, and operator attention is still worth seeing
  // dry-run output for before 50 API calls fire.
  const result = await runSafely({
    operationName: archiveRepos ? "ARCHIVE" : "UNARCHIVE",
    entries,
    allReposFile: "all_repos.txt",
    defaultOwner,
    allowFullMatch,
    dryRun,
    destructive: false,
    execute: (entry) => changeArchiveStatusOne(octokit, entry, archiveRepos),
  });

  if (result.aborted) process.exitCode = 1;
}

if (require.main === module) {
  main().catch((error) => {
    console.error("Unexpected failure:", error);
    process.exitCode = 1;
  });
}

module.exports = { main, changeArchiveStatusOne };
