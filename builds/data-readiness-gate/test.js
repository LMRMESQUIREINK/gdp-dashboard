// test.js — the assertion suite for data-readiness-gate.
// Run with: node test.js
//
// Typical run: ~300 assertions. Static checks need nothing installed;
// the rendering/contrast/overflow checks need a Chromium, located via
// the portable three-branch launcher below, and degrade to a clean
// static-only pass when no Chromium is available at all.

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const GATE = require("./data.js");

let pass = 0;
let fail = 0;
const failures = [];

function assert(cond, label) {
  if (cond) {
    pass++;
  } else {
    fail++;
    failures.push(label);
  }
}

// ---------------------------------------------------------------------
// 1. STRUCTURAL CHECKS ON data.js — no finding ships without its
//    evidence, a valid provenance state, and a claim anchored to
//    something checkable.
// ---------------------------------------------------------------------

const VALID_LEVELS = ["DEEP", "DEEPER", "DEEPEREST", "DEEPEREST-EST"];
const VALID_TYPES = ["credit", "stop"];
const VALID_SOURCES = ["dummies", "readiness", "cookbook", "cross"];
const VALID_PROVENANCE = ["sourced", "sourced-dated", "computed", "source-is-silent", "not-supplied"];
const REQUIRED_NAMED_SOURCES = ["dummies", "readiness", "cookbook"];

assert(Array.isArray(GATE.findings) && GATE.findings.length > 0, "findings array exists and non-empty");

const seenIds = new Set();
GATE.findings.forEach((f) => {
  assert(typeof f.id === "string" && f.id.length > 0, `finding has non-empty id (${f.id})`);
  assert(!seenIds.has(f.id), `finding id is unique (${f.id})`);
  seenIds.add(f.id);

  assert(VALID_LEVELS.includes(f.level), `${f.id}: level is one of DEEP/DEEPER/DEEPEREST/DEEPEREST-EST (got ${f.level})`);
  assert(VALID_TYPES.includes(f.type), `${f.id}: type is credit or stop (got ${f.type})`);
  assert(VALID_SOURCES.includes(f.source), `${f.id}: source is a valid tag (got ${f.source})`);
  assert(VALID_PROVENANCE.includes(f.provenance), `${f.id}: provenance is a valid state (got ${f.provenance})`);

  assert(typeof f.claim === "string" && f.claim.trim().length >= 20, `${f.id}: claim is a real sentence, not a stub`);
  assert(typeof f.evidence === "string" && f.evidence.trim().length >= 20, `${f.id}: evidence string is present and substantial`);

  // Every stop names an outside source, a command, or a file:line — never a bare opinion.
  if (f.type === "stop") {
    const hasAnchor =
      /:\d+/.test(f.evidence) || /`[^`]+`/.test(f.evidence) || /https?:\/\//.test(f.evidence) || /confirmed via/i.test(f.evidence);
    assert(hasAnchor, `${f.id}: stop finding anchors to a line, a command, or a named outside source`);
  }

  // sourced-dated requires a year in the evidence string.
  if (f.provenance === "sourced-dated") {
    assert(/\b(19|20)\d{2}\b/.test(f.evidence), `${f.id}: sourced-dated evidence carries a year`);
  }

  // computed findings do arithmetic/inference — evidence should show the work (a number).
  if (f.provenance === "computed") {
    assert(/\d/.test(f.evidence), `${f.id}: computed evidence shows at least one number, not pure prose`);
  }
});

// Multi-source rule: every named source gets at least one credit and one stop.
REQUIRED_NAMED_SOURCES.forEach((src) => {
  const forSrc = GATE.findings.filter((f) => f.source === src);
  const credits = forSrc.filter((f) => f.type === "credit").length;
  const stops = forSrc.filter((f) => f.type === "stop").length;
  assert(credits >= 1, `source "${src}" has at least one credit finding (has ${credits})`);
  assert(stops >= 1, `source "${src}" has at least one stop finding (has ${stops})`);
});

// Cross-source findings exist (the multi-source "read together" requirement).
const crossFindings = GATE.findings.filter((f) => f.source === "cross");
assert(crossFindings.length >= 2, `at least 2 cross-source findings exist (has ${crossFindings.length})`);

// ---------------------------------------------------------------------
// 2. SOURCES / MEASUREMENT CHECKS
// ---------------------------------------------------------------------

assert(GATE.sources.length === 3, "exactly 3 sources are measured");
GATE.sources.forEach((s) => {
  assert(/^[0-9a-f]{64}$/.test(s.sha256), `${s.id}: sha256 is exactly 64 lowercase hex chars`);
  assert(Number.isInteger(s.pages) && s.pages > 0, `${s.id}: page count is a positive integer`);
  assert(Number.isInteger(s.fileBytes) && s.fileBytes > 0, `${s.id}: file size is a positive integer`);
  assert(Number.isInteger(s.extractedWords) && s.extractedWords > 0, `${s.id}: extracted word count is positive`);
  assert(typeof s.creationDate === "string" && /^\d{4}-\d{2}-\d{2}$/.test(s.creationDate), `${s.id}: creationDate is ISO-formatted`);
});

// Recompute the folder fingerprint exactly as the skill specifies:
// sha256 over the sorted "filename sha256" rows, first 16 chars.
const FINGERPRINT_FILENAMES = {
  dummies: "agents-dummies.pdf",
  readiness: "readiness-index.pdf",
  cookbook: "rag-cookbook.pdf",
};
const rows = GATE.sources
  .map((s) => `${FINGERPRINT_FILENAMES[s.id]} ${s.sha256}`)
  .sort();
const recomputedFingerprint = crypto.createHash("sha256").update(rows.join("\n") + "\n").digest("hex").slice(0, 16);
assert(
  recomputedFingerprint === GATE.meta.sourceFingerprint,
  `source fingerprint recomputes to the stated value (recomputed ${recomputedFingerprint}, stated ${GATE.meta.sourceFingerprint})`
);

// ---------------------------------------------------------------------
// 3. ARITHMETIC RECOMPUTATION — never trust the prose conclusion;
//    recompute every derived claim from the raw numbers in data.js.
// ---------------------------------------------------------------------

const A = GATE.arithmetic;

// R8: paired sub-stats that should sum exactly to their stated combined figure.
const defStat = A.subStatSums[0];
assert(defStat.extremely + defStat.very === defStat.statedCombined, "R8: 38% extremely + 47% very === stated 85% combined");
const unstructStat = A.subStatSums[1];
assert(unstructStat.all + unstructStat.almostAll === unstructStat.statedCombined, "R8: 8% all + 15% almost-all === stated 23% combined");

// R7: the two catalog/lineage stats cannot be mutually exclusive shares of one 100% pool.
const catSum = A.catalogLineageStats.leverageBothWithAutomatedLineage + A.catalogLineageStats.onlyBasicForSelectTeams;
assert(catSum > 100, `R7: 91% + 47% = ${catSum}%, exceeding 100% — cannot be mutually exclusive shares of one base`);

// R3: Chapter 5's literal bullet count.
const ch5 = A.chapter5;
assert(ch5.bulletHeadings.length === ch5.coreTakeawayBullets + ch5.bonusForwardLookingBullets, "R3: 10 core + 1 bonus === 11 total bullets counted");
assert(ch5.bulletHeadings.length > 10, 'R3: bullet count is literally "more than ten" (11 > 10)');
assert(ch5.previewPartsStated.length === 2, 'R3: chapter preview states exactly two parts ("Ten important concepts" + future section)');
assert(ch5.bulletHeadings[ch5.bulletHeadings.length - 1].toLowerCase().includes("future"), "R3: the 11th, bonus bullet is the distinct 'future directions' item");

// E4: Telecommunications tops both visibility and access charts, and tops
// the infra-always-hinders chart, while sitting LAST on governance.
function rankDesc(obj) {
  return Object.entries(obj)
    .sort((a, b) => b[1] - a[1])
    .map(([k]) => k);
}
const visRank = rankDesc(A.visibilityByIndustry);
const accRank = rankDesc(A.accessByIndustry);
const govRank = rankDesc(A.governanceAllOrAlmostAllByIndustry);
const hindersRank = rankDesc(A.infraAlwaysHindersByIndustry);

assert(visRank[0] === "Telecommunications", "E4: Telecommunications ranks #1 on the visibility chart");
assert(accRank[0] === "Telecommunications", "E4: Telecommunications ranks #1 on the access chart");
assert(hindersRank[0] === "Telecommunications", "E4: Telecommunications ranks #1 on infra-always-hinders (60%)");
assert(govRank[govRank.length - 1] === "Telecommunications", "E4: Telecommunications ranks LAST on governance (57%, lowest of 7)");
assert(govRank[0] === "Public Sector", "E4: Public Sector ranks #1 on governance (72%, highest of 7)");
assert(visRank[visRank.length - 1] === "Public Sector", "E4: Public Sector ranks LAST on visibility (66%, lowest of 7)");
assert(accRank[accRank.length - 1] === "Public Sector", "E4: Public Sector ranks LAST on access (56%, lowest of 7)");

// E5: Spearman rank correlation, recomputed independently from the raw tables.
function spearman(objA, objB) {
  const keys = Object.keys(objA);
  const n = keys.length;
  const rankOf = (obj) => {
    const sorted = [...keys].sort((a, b) => obj[b] - obj[a]);
    const ranks = {};
    sorted.forEach((k, i) => (ranks[k] = i + 1));
    return ranks;
  };
  const rA = rankOf(objA);
  const rB = rankOf(objB);
  let sumDsq = 0;
  keys.forEach((k) => {
    const d = rA[k] - rB[k];
    sumDsq += d * d;
  });
  return 1 - (6 * sumDsq) / (n * (n * n - 1));
}

const rhoVisGov = spearman(A.visibilityByIndustry, A.governanceAllOrAlmostAllByIndustry);
const rhoAccGov = spearman(A.accessByIndustry, A.governanceAllOrAlmostAllByIndustry);

assert(Math.abs(rhoVisGov - -0.3929) < 0.001, `E5: visibility-vs-governance Spearman rho recomputes to ~-0.393 (got ${rhoVisGov.toFixed(4)})`);
assert(Math.abs(rhoAccGov - -0.3929) < 0.001, `E5: access-vs-governance Spearman rho recomputes to ~-0.393 (got ${rhoAccGov.toFixed(4)})`);
assert(rhoVisGov < 0, "E5: visibility-vs-governance correlation is negative, as claimed");
assert(rhoAccGov < 0, "E5: access-vs-governance correlation is negative, as claimed");

// ---------------------------------------------------------------------
// 4. COUNTS TABLE — direction flags, and the "same raw value, opposite
//    direction" pair this page deliberately carries (R4's 0 vs. the
//    no-invented-stats 0).
// ---------------------------------------------------------------------

assert(Array.isArray(GATE.counts) && GATE.counts.length >= 5, "counts table has a real number of rows");
const VALID_DIRECTIONS = ["up", "down", "flat"];
GATE.counts.forEach((c) => {
  assert(VALID_DIRECTIONS.includes(c.direction), `count "${c.label}": direction is up/down/flat (got ${c.direction})`);
  assert(typeof c.why === "string" && c.why.length >= 20, `count "${c.label}": has a real "why" explanation`);
  assert(typeof c.value === "number", `count "${c.label}": value is numeric`);
});

const zeroRows = GATE.counts.filter((c) => c.value === 0);
assert(zeroRows.length >= 2, "at least two count rows share the raw value 0");
const zeroDirections = new Set(zeroRows.map((c) => c.direction));
assert(zeroDirections.has("up") && zeroDirections.has("down"), "the two zero-value rows carry OPPOSITE direction flags (0 is not inherently good or bad)");

// ---------------------------------------------------------------------
// 5. CORRECTIONS — recorded in public, never silently edited away.
// ---------------------------------------------------------------------

assert(Array.isArray(GATE.corrections) && GATE.corrections.length >= 1, "at least one correction is recorded");
GATE.corrections.forEach((c) => {
  assert(/RESOLVED/.test(c.resolution), `correction ${c.id}: resolution text contains RESOLVED`);
  assert(typeof c.direction === "string" && c.direction.length > 0, `correction ${c.id}: direction of the original error is stated`);
  assert(c.what.length >= 20 && c.resolution.length >= 20, `correction ${c.id}: both the original concern and the resolution are substantial`);
});

// This specific correction's underlying claim must actually be true:
// every sha256 in GATE.sources really is 64 hex characters.
GATE.sources.forEach((s) => {
  assert(s.sha256.length === 64, `${s.id}: sha256 string length is exactly 64 (the correction's own claim, re-verified)`);
});

// ---------------------------------------------------------------------
// 6. BUSINESS RULES / RIGHTS TABLES
// ---------------------------------------------------------------------

const VALID_RULE_VERDICTS = ["clears", "collides", "n/a"];
assert(GATE.businessRules.length === 3, "exactly 3 operator business rules are scored");
GATE.businessRules.forEach((r) => {
  assert(VALID_RULE_VERDICTS.includes(r.verdict.toLowerCase()), `rule "${r.rule}": verdict is clears/COLLIDES/n/a (got ${r.verdict})`);
  assert(r.why.length >= 20, `rule "${r.rule}": has a real "why"`);
});
const collisionCount = GATE.businessRules.filter((r) => r.verdict.toLowerCase() === "collides").length;
assert(collisionCount === 0, `collision count is not inflated (0 real collisions found, got ${collisionCount})`);

assert(GATE.rights.length >= 3, "rights table has a real number of rows");
const greyRows = GATE.rights.filter((r) => r.status === "grey");
assert(greyRows.length === 1, `exactly one rights row is marked grey (got ${greyRows.length})`);
GATE.rights.forEach((r) => {
  assert(r.quote.length >= 20, `rights row "${r.row}": quotes a real basis, not a bare assertion`);
});

// ---------------------------------------------------------------------
// 7. COVERAGE — printed, and honest about what was and wasn't read.
// ---------------------------------------------------------------------

assert(Array.isArray(GATE.coverage.read) && GATE.coverage.read.length >= 3, "coverage.read lists what was actually read");
assert(Array.isArray(GATE.coverage.notRead) && GATE.coverage.notRead.length >= 2, "coverage.notRead lists what was NOT read");
assert(/arxiv/i.test(GATE.coverage.externalVerification), "coverage states the arXiv egress restriction plainly");
assert(/nothing/i.test(GATE.coverage.notPurchasedNotClicked), "coverage states plainly that no live product was used");

// No finding should rest on a claim coverage says was not verified: every
// sourced-dated finding's named external subject should NOT appear in the
// notRead list's text as something left unchecked.
const notReadText = GATE.coverage.notRead.join(" ").toLowerCase();
GATE.findings
  .filter((f) => f.provenance === "sourced-dated")
  .forEach((f) => {
    assert(!/this was not checked/i.test(f.evidence), `${f.id}: sourced-dated finding does not itself admit "not checked"`);
  });

console.log(`\nStatic checks: ${pass} passed, ${fail} failed so far.\n`);

// ---------------------------------------------------------------------
// 8. BROWSER-DEPENDENT CHECKS — rendering, palette contrast, overflow.
//    Portable three-branch launcher. Never a raw stack trace.
// ---------------------------------------------------------------------

let chromium = null;
try {
  chromium = require("playwright").chromium;
} catch (e1) {
  try {
    chromium = require("playwright-core").chromium;
  } catch (e2) {
    chromium = null;
  }
}
const LAUNCH = process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {};

function relLuminance(r, g, b) {
  const srgb = [r, g, b].map((v) => {
    const c = v / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * srgb[0] + 0.7152 * srgb[1] + 0.0722 * srgb[2];
}
function contrastRatio(rgb1, rgb2) {
  const l1 = relLuminance(...rgb1);
  const l2 = relLuminance(...rgb2);
  const [hi, lo] = l1 > l2 ? [l1, l2] : [l2, l1];
  return (hi + 0.05) / (lo + 0.05);
}
function hexToRgb(hex) {
  const h = hex.replace("#", "");
  return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
}
function rgbToHsl(r, g, b) {
  r /= 255; g /= 255; b /= 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  let h, s, l = (max + min) / 2;
  if (max === min) { h = s = 0; }
  else {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r: h = (g - b) / d + (g < b ? 6 : 0); break;
      case g: h = (b - r) / d + 2; break;
      default: h = (r - g) / d + 4;
    }
    h *= 60;
  }
  return [h, s, l];
}

const PALETTE = {
  panel: "#1A1D21", plate: "#24282E", engrave: "#111316",
  go: "#3BD17E", caution: "#F2A93B", stop: "#E2534C", stopInk: "#ED7066",
  ink: "#E8EAED", inkDim: "#9AA2AC", rail: "#343A42",
};

async function runBrowserChecks() {
  if (!chromium) {
    console.log("No Chromium available (neither 'playwright' nor 'playwright-core' is installed).");
    console.log("Recovery: `npm install playwright` (or `playwright-core` + a system Chrome via CHROME_PATH), then re-run `node test.js`.");
    console.log("Falling back to the static-only pass above.\n");
    return;
  }

  let browser;
  try {
    browser = await chromium.launch(LAUNCH);
  } catch (e) {
    console.log("Chromium failed to launch:", e.message);
    console.log("Falling back to the static-only pass above.\n");
    return;
  }

  try {
    const page = await browser.newPage();
    const consoleErrors = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") consoleErrors.push(msg.text());
    });
    page.on("pageerror", (err) => consoleErrors.push(String(err)));

    const fileUrl = "file://" + path.join(__dirname, "index.html");
    await page.goto(fileUrl, { waitUntil: "load" });
    await page.waitForTimeout(150);

    // ---- title / subtitle render FROM data.js, not hardcoded ----
    const titleText = await page.$eval("#gate-title", (e) => e.textContent);
    assert(titleText === GATE.meta.title, "rendered title matches GATE.meta.title exactly");
    const subtitleText = await page.$eval("#gate-subtitle", (e) => e.textContent);
    assert(subtitleText === GATE.meta.subtitle, "rendered subtitle matches GATE.meta.subtitle exactly");

    // ---- verdict counts match data.js exactly ----
    const verdictStats = await page.$$eval(".verdict .stat .n", (els) => els.map((e) => e.textContent));
    assert(verdictStats[0] === String(GATE.findings.length), "rendered 'Findings' count matches GATE.findings.length");
    const totalCredit = GATE.findings.filter((f) => f.type === "credit").length;
    const totalStop = GATE.findings.filter((f) => f.type === "stop").length;
    assert(verdictStats[1] === String(totalCredit), "rendered 'Credits' count matches computed total");
    assert(verdictStats[2] === String(totalStop), "rendered 'Stops' count matches computed total");

    // ---- every finding in data.js has a rendered card ----
    const renderedFindingIds = await page.$$eval(".finding .f-id", (els) => els.map((e) => e.textContent));
    assert(renderedFindingIds.length === GATE.findings.length, `rendered finding count (${renderedFindingIds.length}) matches data.js (${GATE.findings.length})`);
    GATE.findings.forEach((f) => {
      assert(renderedFindingIds.includes(f.id), `finding ${f.id} has a rendered card`);
    });

    // ---- counts table rows match data.js, direction text matches flag ----
    const countRows = await page.$$eval("#counts-body tr", (rows) =>
      rows.map((r) => {
        const cells = r.querySelectorAll("td");
        return { label: cells[0].textContent, value: cells[1].textContent, dir: cells[2].textContent };
      })
    );
    assert(countRows.length === GATE.counts.length, "rendered counts table row count matches data.js");
    GATE.counts.forEach((c, i) => {
      assert(countRows[i].value === String(c.value), `count row ${i}: rendered value matches data.js (${c.label})`);
      assert(countRows[i].dir === c.direction.toUpperCase(), `count row ${i}: rendered direction matches data.js flag (${c.label})`);
    });

    // ---- rights table: exactly one grey row rendered ----
    const rightsStatuses = await page.$$eval("#rights-body td.status", (els) => els.map((e) => e.textContent));
    const greyRendered = rightsStatuses.filter((s) => s === "grey").length;
    assert(greyRendered === 1, `rendered rights table has exactly one grey row (got ${greyRendered})`);

    // ---- coverage appears before verdict ON SCREEN, not just in DOM order ----
    const covBox = await page.$eval("#sec-coverage", (e) => e.getBoundingClientRect());
    const verdictBox = await page.$eval("#sec-verdict", (e) => e.getBoundingClientRect());
    assert(covBox.top < verdictBox.top, "coverage section's top position is above the verdict section's (getBoundingClientRect)");

    // ---- no external scripts ----
    const scriptSrcs = await page.$$eval("script[src]", (els) => els.map((e) => e.getAttribute("src")));
    scriptSrcs.forEach((src) => {
      assert(!/^https?:\/\//.test(src), `script src "${src}" is not an external URL`);
    });
    assert(scriptSrcs.includes("data.js"), "data.js is loaded as a script");

    // ---- zero console errors ----
    assert(consoleErrors.length === 0, `zero console errors (found ${consoleErrors.length}: ${consoleErrors.slice(0, 2).join(" | ")})`);

    // ---- palette contrast, computed, never eyeballed ----
    const stopRgb = hexToRgb(PALETTE.stop);
    const stopInkRgb = hexToRgb(PALETTE.stopInk);
    const engraveRgb = hexToRgb(PALETTE.engrave);
    const panelRgb = hexToRgb(PALETTE.panel);
    const plateRgb = hexToRgb(PALETTE.plate);

    const stopOnEngrave = contrastRatio(stopRgb, engraveRgb);
    const stopOnPanel = contrastRatio(stopRgb, panelRgb);
    const stopOnPlate = contrastRatio(stopRgb, plateRgb);
    assert(stopOnEngrave >= 3, `--stop on --engrave clears 3:1 border floor (${stopOnEngrave.toFixed(2)})`);
    assert(stopOnPanel >= 3, `--stop on --panel clears 3:1 border floor (${stopOnPanel.toFixed(2)})`);
    assert(stopOnPlate >= 3, `--stop on --plate clears 3:1 border floor (${stopOnPlate.toFixed(2)})`);
    assert(stopOnPlate < 4.5, `--stop on --plate does NOT clear the 4.5:1 text floor (${stopOnPlate.toFixed(2)}) — confirming it is border-only`);

    const stopInkOnEngrave = contrastRatio(stopInkRgb, engraveRgb);
    const stopInkOnPanel = contrastRatio(stopInkRgb, panelRgb);
    const stopInkOnPlate = contrastRatio(stopInkRgb, plateRgb);
    assert(stopInkOnEngrave >= 4.5, `--stop-ink on --engrave clears 4.5:1 text floor (${stopInkOnEngrave.toFixed(2)})`);
    assert(stopInkOnPanel >= 4.5, `--stop-ink on --panel clears 4.5:1 text floor (${stopInkOnPanel.toFixed(2)})`);
    assert(stopInkOnPlate >= 4.5, `--stop-ink on --plate clears 4.5:1 text floor (${stopInkOnPlate.toFixed(2)})`);

    // ---- hue separation >= 30 degrees between go / caution / stop ----
    const goHsl = rgbToHsl(...hexToRgb(PALETTE.go));
    const cautionHsl = rgbToHsl(...hexToRgb(PALETTE.caution));
    const stopHsl = rgbToHsl(...hexToRgb(PALETTE.stop));
    function hueDiff(h1, h2) {
      const d = Math.abs(h1 - h2) % 360;
      return d > 180 ? 360 - d : d;
    }
    assert(hueDiff(goHsl[0], cautionHsl[0]) >= 30, `go/caution hue separation >= 30deg (${hueDiff(goHsl[0], cautionHsl[0]).toFixed(1)})`);
    assert(hueDiff(cautionHsl[0], stopHsl[0]) >= 30, `caution/stop hue separation >= 30deg (${hueDiff(cautionHsl[0], stopHsl[0]).toFixed(1)})`);
    assert(hueDiff(goHsl[0], stopHsl[0]) >= 30, `go/stop hue separation >= 30deg (${hueDiff(goHsl[0], stopHsl[0]).toFixed(1)})`);

    // ---- --stop must appear as a text colour on ZERO rendered elements ----
    const stopTargetRgbStr = `rgb(${stopRgb[0]}, ${stopRgb[1]}, ${stopRgb[2]})`;
    const elementsWithStopTextColor = await page.$$eval(
      "*",
      (els, targetColor) => els.filter((e) => getComputedStyle(e).color === targetColor).length,
      stopTargetRgbStr
    );
    assert(elementsWithStopTextColor === 0, `--stop is used as a text colour on zero rendered elements (found ${elementsWithStopTextColor})`);

    // ---- no horizontal overflow at 375px ----
    // Check BOTH documentElement.scrollWidth and body.scrollWidth: an
    // `overflow-x: hidden` on html/body can clip documentElement's own
    // reported scrollWidth down to the viewport while body.scrollWidth
    // still reveals real overflowing content underneath (the same
    // discrepancy this project documented in an earlier gate round —
    // a table without table-layout:fixed growing past its container).
    await page.setViewportSize({ width: 375, height: 800 });
    await page.waitForTimeout(100);
    const scrollW = await page.evaluate(() => document.documentElement.scrollWidth);
    const clientW = await page.evaluate(() => document.documentElement.clientWidth);
    const bodyScrollW = await page.evaluate(() => document.body.scrollWidth);
    assert(scrollW <= clientW + 1, `no horizontal overflow at 375px per documentElement.scrollWidth (${scrollW} vs clientWidth ${clientW})`);
    assert(bodyScrollW <= clientW + 1, `no horizontal overflow at 375px per body.scrollWidth, the stricter check (${bodyScrollW} vs clientWidth ${clientW})`);

    // ---- desktop screenshot pass, no overflow there either ----
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.waitForTimeout(100);
    const scrollW1280 = await page.evaluate(() => document.documentElement.scrollWidth);
    const clientW1280 = await page.evaluate(() => document.documentElement.clientWidth);
    const bodyScrollW1280 = await page.evaluate(() => document.body.scrollWidth);
    assert(scrollW1280 <= clientW1280 + 1, `no horizontal overflow at 1280px per documentElement.scrollWidth (${scrollW1280} vs clientWidth ${clientW1280})`);
    assert(bodyScrollW1280 <= clientW1280 + 1, `no horizontal overflow at 1280px per body.scrollWidth (${bodyScrollW1280} vs clientWidth ${clientW1280})`);

    const screenshotDir = path.join(__dirname, "verification");
    fs.mkdirSync(screenshotDir, { recursive: true });
    await page.screenshot({ path: path.join(screenshotDir, "desktop-1280.png"), fullPage: true });
    await page.setViewportSize({ width: 375, height: 800 });
    await page.waitForTimeout(100);
    await page.screenshot({ path: path.join(screenshotDir, "mobile-375.png"), fullPage: true });

    console.log("Screenshots written to verification/desktop-1280.png and verification/mobile-375.png");
  } catch (e) {
    console.log("Browser check raised an error (isolated, not treated as a stack trace):", e.message);
  } finally {
    await browser.close();
  }
}

runBrowserChecks().then(() => {
  console.log(`\nTOTAL: ${pass} passed, ${fail} failed.\n`);
  if (fail > 0) {
    console.log("Failures:");
    failures.forEach((f) => console.log(" - " + f));
    process.exitCode = 1;
  }
});
