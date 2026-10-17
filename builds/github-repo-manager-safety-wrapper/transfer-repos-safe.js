"use strict";

const { Octokit } = require("@octokit/rest");
require("dotenv").config();

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const { loadRepoList, runSafely } = require("./safety-core");

async function transferOne(octokit, owner, targetOrg, repo) {
  const { data: repoInfo } = await octokit.rest.repos.get({ owner, repo });

  if (repoInfo.archived) {
    await octokit.rest.repos.update({ owner, repo, archived: false });
    await sleep(3000);
  }
  if (!repoInfo.private) {
    await octokit.rest.repos.update({ owner, repo, private: true });
    await sleep(3000);
  }
  await octokit.rest.repos.transfer({ owner, repo, new_owner: targetOrg });
}

async function main() {
  const args = process.argv.slice(2);
  const dryRun = args.includes("--dry-run");
  const allowFullMatch = args.includes("--force-full");

  const octokit = new Octokit({ auth: process.env.GITHUB_TOKEN });
  const owner = process.env.GITHUB_USER;
  const targetOrg = process.env.TARGET_ORG;

  const repos = loadRepoList("move.txt");
  if (!repos) {
    console.log("❌ move.txt not found. Please create it and add the repo names to transfer.");
    return;
  }
  if (repos.length === 0) {
    console.log("move.txt is empty — nothing to do.");
    return;
  }

  const result = await runSafely({
    operationName: "TRANSFER",
    repos,
    allReposFile: "all_repos.txt",
    allowFullMatch,
    dryRun,
    destructive: true,
    confirmPhrase: (count) => `TRANSFER ${count} REPOS TO ${targetOrg}`,
    execute: (repo) => transferOne(octokit, owner, targetOrg, repo),
  });

  if (result.aborted) process.exitCode = 1;
}

if (require.main === module) {
  main().catch((error) => {
    console.error("Unexpected failure:", error);
    process.exitCode = 1;
  });
}

module.exports = { main, transferOne };
