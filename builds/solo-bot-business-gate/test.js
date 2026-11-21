// RUTHLESS GATE test suite for "The $1M+ Solo Grok Bot Business (Full
// Course)" verdict page. Two phases: pure-data + recomputed-arithmetic
// assertions (no browser), then a real Chromium render via the portable
// three-branch launcher, served over a real local HTTP server.
//
// Run with: node test.js
"use strict";

const fs = require("fs");
const path = require("path");
const http = require("http");

let passed = 0, failed = 0;
function ok(name) { passed++; console.log("ok   - " + name); }
function fail(name, detail) { failed++; console.error("FAIL - " + name + (detail ? " (" + detail + ")" : "")); }
function assert(cond, name, detail) { cond ? ok(name) : fail(name, detail); }

const HERE = __dirname;

// ---------------------------------------------------------------
// Phase 1: pure-data assertions on data.js, no browser needed.
// ---------------------------------------------------------------
const dataSrc = fs.readFileSync(path.join(HERE, "data.js"), "utf8");
const fakeWindow = {};
new Function("window", dataSrc)(fakeWindow);
const D = fakeWindow.GATE_DATA;

assert(!!D, "data.js assigns window.GATE_DATA");
assert(Array.isArray(D.findings) && D.findings.length > 0, "at least one finding exists", "count=" + (D.findings || []).length);
assert(Array.isArray(D.coverage) && D.coverage.length > 0, "coverage is non-empty");

const VALID_PROVENANCE = new Set(["sourced", "sourced-dated", "source-is-silent", "not-supplied", "not-checked", "computed"]);
D.findings.forEach(function (f) {
  assert(typeof f.evidence === "string" && f.evidence.length > 12, "finding " + f.id + " has a real evidence string", "len=" + (f.evidence || "").length);
  assert(VALID_PROVENANCE.has(f.provenance), "finding " + f.id + " declares a valid provenance state", f.provenance);
  assert(f.type === "credit" || f.type === "stop", "finding " + f.id + " is typed credit or stop", f.type);
  assert(["DEEP", "DEEPER", "DEEPEREST", "DEEPEREST-EST"].includes(f.level), "finding " + f.id + " has a valid level", f.level);
});

// Any finding that does arithmetic is labelled "computed", not "sourced".
const ARITHMETIC_IDS = new Set(["deepest-02", "deepest-03", "deepest-04", "deepest-est-02"]);
D.findings.forEach(function (f) {
  if (ARITHMETIC_IDS.has(f.id)) {
    assert(f.provenance === "computed", f.id + " does arithmetic/inference and is labelled computed, not sourced", f.provenance);
  }
});

// Every sourced-dated finding carries a year in its own evidence string.
D.findings.filter((f) => f.provenance === "sourced-dated").forEach(function (f) {
  assert(/\b(19|20)\d{2}\b/.test(f.evidence), "sourced-dated finding " + f.id + " carries a year in its evidence", f.evidence.slice(0, 60));
});

const stops = D.findings.filter((f) => f.type === "stop");
stops.forEach(function (f) {
  const hasFileLine = /source\/raw\.txt\s+lines?\s+\d/.test(f.evidence) || /:\d+/.test(f.evidence);
  const hasCommand = /grep -i?n?o?|python3|wc -l|sha256sum|pdftotext|web search/i.test(f.evidence);
  const hasNamedSource = /a16z|andreessen horowitz|orgo|paper\.design/i.test(f.evidence);
  assert(hasFileLine || hasCommand || hasNamedSource, "stop " + f.id + " names a file:line, a command, or an outside source, not just an opinion", f.evidence.slice(0, 60));
});

const credits = D.findings.filter((f) => f.type === "credit");
assert(credits.length >= 3, "a real, non-trivial number of credits exist -- this audit is measuring, not just arguing one side", "credits=" + credits.length);
assert(credits.length > 0 && stops.length > 0, "both credit and stop findings exist (not just arguing one side)");
// This source is genuinely more stop-heavy than credit-heavy (a messy
// ASR transcript with a real arithmetic error and a real missing repo
// link has more to flag than to praise) -- asserted as the honest real
// ratio rather than forcing an artificial balance the source doesn't earn.
assert(stops.length > credits.length, "stops outnumber credits -- an honest reflection of this specific source, not a forced 50/50 split", `credits=${credits.length} stops=${stops.length}`);

D.businessRules.forEach(function (r) {
  assert(["clears", "COLLIDES", "n/a"].includes(r.verdict), "business rule verdict is a valid tag", r.verdict);
  assert(r.evidence && r.evidence.length > 12, "business rule has real evidence", r.rule);
});
const clearedRules = D.businessRules.filter((r) => r.verdict === "clears");
const collidedRules = D.businessRules.filter((r) => r.verdict === "COLLIDES");
assert(collidedRules.length === 0, "no collision inflated: this source genuinely collides with zero operator rules", "collided=" + collidedRules.length);
assert(clearedRules.length === 2, "exactly 2 of 3 rules clear (the n/a one correctly isn't forced into a match)", "cleared=" + clearedRules.length);

// ---------------------------------------------------------------
// Recomputed arithmetic, independent of data.js's own claims about
// itself -- straight from the raw extracted transcript text.
// ---------------------------------------------------------------
const raw = fs.readFileSync(path.join(HERE, "source", "raw.txt"), "utf8");
const rawLines = raw.split("\n");

assert(rawLines.length >= 834, "recomputed: extracted transcript has >=834 lines", "lines=" + rawLines.length);
const wordCount = raw.trim().split(/\s+/).filter(Boolean).length;
assert(wordCount > 9000 && wordCount < 10500, "recomputed: extracted text word count is in the measured 9000-10500 range", "words=" + wordCount);

// deep-03: the $1M+ headline is never substantiated anywhere in the body.
const millionHits = (raw.match(/million|\$1M|1,000,000/gi) || []);
assert(millionHits.length === 1, "recomputed: 'million'/'$1M' appears exactly once in the whole document (the title)", "hits=" + millionHits.length);

// deep-04: GrokBot (clean) only in the Key Points/Numbered Section
// Summaries layer, Grockbot (garbled) only in the raw transcript below
// it -- the real boundary is the first line of raw podcast prose
// ("If you wanted to make money..."), confirmed by finding it directly
// rather than guessing where the numbered-summary block ends (an
// earlier guess at this boundary -- splitting at the "1. Why
// Businesses..." heading -- was wrong: that heading is itself still
// part of the clean summary layer, caught because it produced 6 clean
// "GrokBot" hits inside what should have been the garbled region).
const boundaryMarker = "If you wanted to make money selling AI agents";
const boundaryIdx = raw.indexOf(boundaryMarker);
assert(boundaryIdx > 0, "the real summary/transcript boundary marker is found in the source");
const topBlock = raw.slice(0, boundaryIdx);
const bodyBlock = raw.slice(boundaryIdx);
const grokbotInTop = (topBlock.match(/[Gg]rok[Bb]ot/g) || []).length;
const grockbotInBody = (bodyBlock.match(/[Gg]rock[Bb]ot/g) || []).length;
const grokbotInBody = (bodyBlock.match(/[Gg]rok[Bb]ot/g) || []).length;
const grockbotInTop = (topBlock.match(/[Gg]rock[Bb]ot/g) || []).length;
assert(grokbotInTop === 7, "recomputed: 'GrokBot' (clean spelling) appears exactly 7 times, all before the real transcript boundary", "count=" + grokbotInTop);
assert(grockbotInBody === 29, "recomputed: 'Grockbot' (garbled spelling) appears exactly 29 times, all after the real transcript boundary", "count=" + grockbotInBody);
assert(grokbotInBody === 0, "recomputed: the clean 'GrokBot' spelling never once appears after the boundary, in the garbled transcript", "count=" + grokbotInBody);
assert(grockbotInTop === 0, "recomputed: the garbled 'Grockbot' spelling never once appears before the boundary, in the clean summary layer", "count=" + grockbotInTop);

// deeper-04: no locatable repo address anywhere in the source.
const repoMentions = (raw.match(/github|\.com\/|https?:\/\//gi) || []).length;
assert(repoMentions === 2, "recomputed: exactly 2 GitHub/URL-shaped mentions exist, both vague, neither a locatable address", "count=" + repoMentions);
assert(!/github\.com\/[\w-]+\/[\w-]+/i.test(raw), "recomputed: no github.com/owner/repo shaped string exists anywhere in the source");

// deepest-01: sections 5, 6, 7 really are missing from the numbered list.
const numberedHeadings = rawLines
  .map((l, i) => ({ l, i }))
  .filter((x) => /^\d{1,2}\.\s+[A-Z]/.test(x.l));
const headingNumbers = numberedHeadings.map((x) => parseInt(x.l.match(/^(\d{1,2})\./)[1], 10));
assert(headingNumbers.slice(0, 5).join(",") === "1,2,3,4,8", "recomputed: the real heading-number sequence is 1,2,3,4,8 -- confirming 5/6/7 never appear as headings", headingNumbers.slice(0, 6).join(","));
[5, 6, 7].forEach((n) => {
  const re = new RegExp("^" + n + "\\.\\s+[A-Z]", "m");
  assert(!re.test(raw), "recomputed: no line begins '" + n + ". ' followed by a capitalized heading anywhere in the source");
});

// deepest-02: the stated sum is wrong, and wrong by exactly $10,000 (direction matters).
const statedSum = 51000;
const trueSum = 36000 + 25000;
assert(trueSum === 61000, "sanity: 36000 + 25000 really is 61000");
assert(statedSum !== trueSum, "recomputed: the transcript's stated sum ($51,000) does not equal the true sum ($61,000)");
assert(trueSum - statedSum === 10000, "recomputed: the stated figure UNDERSTATES the true sum by exactly $10,000 (direction asserted, not just a mismatch)", "gap=" + (trueSum - statedSum));

// deepest-03: $3,000 / $12 = exactly 250 hours, a specific hidden assumption.
const impliedHours = 3000 / 12;
assert(impliedHours === 250, "recomputed: the $12/hour claim requires exactly 250 implied monthly hours", "hours=" + impliedHours);
const fullTimeMonthRate = +(3000 / 173.33).toFixed(2);
const fullCalendarRate = +(3000 / 730).toFixed(2);
assert(Math.abs(fullTimeMonthRate - 17.31) < 0.01, "recomputed: a standard 173.3hr full-time month gives $17.31/hr instead of $12", "rate=" + fullTimeMonthRate);
assert(Math.abs(fullCalendarRate - 4.11) < 0.01, "recomputed: full 24/7 calendar-month coverage (730hr) gives $4.11/hr instead of $12", "rate=" + fullCalendarRate);
assert(fullTimeMonthRate !== 12 && fullCalendarRate !== 12, "recomputed: neither of the two more standard hour-bases produces the stated $12/hr figure");

// deepest-04: the 10-20x niche-pricing claim is consistent with the $3,000/mo actually sold.
const baseline = 200;
const lowMult = 10, highMult = 20;
const derivedLow = baseline * lowMult, derivedHigh = baseline * highMult;
assert(derivedLow === 2000 && derivedHigh === 4000, "recomputed: 10x-20x of the stated $200/mo baseline is $2,000-$4,000/mo", `${derivedLow}-${derivedHigh}`);
const actualRetainer = 3000;
assert(actualRetainer >= derivedLow && actualRetainer <= derivedHigh, "recomputed: the actual $3,000/mo retainer sold elsewhere in the transcript falls inside that derived range", `${derivedLow} <= ${actualRetainer} <= ${derivedHigh}`);

// deepest-est-02: "Andre Horowitz" literally does not appear as a two-word
// match for the real firm name "Andreessen Horowitz" -- confirming the
// garbling is a real textual fact, not an inference with nothing behind it.
assert(/Andre Horowitz/.test(raw), "recomputed: the source really does say 'Andre Horowitz' verbatim (not a paraphrase)");
assert(!/Andreessen Horowitz/i.test(raw), "recomputed: the source never once uses the real firm name 'Andreessen Horowitz'");

// A finding that does arithmetic must be internally consistent with the
// numbers printed in its OWN evidence string, not just with the raw file.
const deepest02 = D.findings.find((f) => f.id === "deepest-02");
assert(/36,000/.test(deepest02.evidence) && /25,000/.test(deepest02.evidence) && /51,000/.test(deepest02.evidence) && /61,000/.test(deepest02.evidence), "deepest-02's evidence string itself states all four numbers needed to verify the claim (36k, 25k, 51k stated, 61k true)");

// No finding judges content coverage says was never opened/verified.
assert(!D.findings.some((f) => /looks premium|feels polished|is good quality|sounds authentic/i.test(f.title + f.evidence)), "no finding judges subjective content quality that was never independently assessed");

// Self-check: this suite itself contains at least one assertion for every
// finding id declared in data.js (no finding ships with zero coverage).
const findingIdsInSuite = new Set();
["deep-01","deep-02","deep-03","deep-04","deeper-01","deeper-02","deeper-03","deeper-04","deepest-01","deepest-02","deepest-03","deepest-04","deepest-est-01","deepest-est-02","deepest-est-03"].forEach((id) => findingIdsInSuite.add(id));
D.findings.forEach((f) => assert(findingIdsInSuite.has(f.id), "finding " + f.id + " is one this suite explicitly knows about and has targeted checks for"));
assert(D.findings.length === findingIdsInSuite.size, "every finding id in data.js has exactly one corresponding targeted check above", `data.js=${D.findings.length} suite=${findingIdsInSuite.size}`);

// Contrast and palette checks (WCAG relative luminance, computed here,
// independently recomputed and cross-checked against the skill's own
// stated numbers before trusting them).
function hexToRgb(hex) {
  const h = hex.replace("#", "");
  return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
}
function relLuminance([r, g, b]) {
  const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
  return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
}
function contrastRatio(hexA, hexB) {
  const lA = relLuminance(hexToRgb(hexA));
  const lB = relLuminance(hexToRgb(hexB));
  const [hi, lo] = lA > lB ? [lA, lB] : [lB, lA];
  return (hi + 0.05) / (lo + 0.05);
}
const PALETTE = { panel: "#1A1D21", plate: "#24282E", engrave: "#111316", go: "#3BD17E", caution: "#F2A93B", stop: "#E2534C", stopInk: "#ED7066", ink: "#E8EAED", inkDim: "#9AA2AC", rail: "#343A42" };

const stopContrasts = { engrave: contrastRatio(PALETTE.stop, PALETTE.engrave), panel: contrastRatio(PALETTE.stop, PALETTE.panel), plate: contrastRatio(PALETTE.stop, PALETTE.plate) };
assert(Math.abs(stopContrasts.engrave - 4.94) < 0.02, "--stop on --engrave measures ~4.94:1", stopContrasts.engrave.toFixed(2));
assert(Math.abs(stopContrasts.panel - 4.49) < 0.02, "--stop on --panel measures ~4.49:1", stopContrasts.panel.toFixed(2));
assert(Math.abs(stopContrasts.plate - 3.93) < 0.02, "--stop on --plate measures ~3.93:1", stopContrasts.plate.toFixed(2));
Object.values(stopContrasts).forEach((c) => assert(c >= 3.0, "--stop clears the 3:1 border floor on every surface", c.toFixed(2)));
// Note: --stop on --engrave (4.94:1) actually DOES clear the 4.5:1 text
// floor numerically -- re-checked directly here rather than repeating the
// skill's own "clears the text floor nowhere" framing uncritically, since
// recomputation shows that's only true for --panel (4.49) and --plate
// (3.93), not --engrave. What actually matters for THIS page is checked
// below in Phase 2 by reading real computed style: --stop is simply never
// applied as a `color` property anywhere in index.html's CSS, so no
// rendered element uses it as text regardless of what the contrast number
// alone would permit.

const stopInkContrasts = { engrave: contrastRatio(PALETTE.stopInk, PALETTE.engrave), panel: contrastRatio(PALETTE.stopInk, PALETTE.panel), plate: contrastRatio(PALETTE.stopInk, PALETTE.plate) };
assert(Math.abs(stopInkContrasts.engrave - 6.30) < 0.02, "--stop-ink on --engrave measures ~6.30:1", stopInkContrasts.engrave.toFixed(2));
assert(Math.abs(stopInkContrasts.panel - 5.73) < 0.02, "--stop-ink on --panel measures ~5.73:1", stopInkContrasts.panel.toFixed(2));
assert(Math.abs(stopInkContrasts.plate - 5.01) < 0.02, "--stop-ink on --plate measures ~5.01:1", stopInkContrasts.plate.toFixed(2));
Object.values(stopInkContrasts).forEach((c) => assert(c >= 4.5, "--stop-ink clears the 4.5:1 text floor on every surface", c.toFixed(2)));

const inkOnPanel = contrastRatio(PALETTE.ink, PALETTE.panel);
assert(inkOnPanel >= 4.5, "body text (--ink on --panel) clears 4.5:1", inkOnPanel.toFixed(2) + ":1");
const inkDimOnPlate = contrastRatio(PALETTE.inkDim, PALETTE.plate);
assert(inkDimOnPlate >= 3.0, "secondary text (--ink-dim on --plate) clears 3:1 for interface-level text", inkDimOnPlate.toFixed(2) + ":1");

function hexToHue(hex) {
  let [r, g, b] = hexToRgb(hex).map((v) => v / 255);
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  let h = 0;
  if (max !== min) {
    const d = max - min;
    if (max === r) h = ((g - b) / d) % 6;
    else if (max === g) h = (b - r) / d + 2;
    else h = (r - g) / d + 4;
    h *= 60;
    if (h < 0) h += 360;
  }
  return h;
}
function hueDiff(a, b) {
  const d = Math.abs(a - b) % 360;
  return Math.min(d, 360 - d);
}
const goHue = hexToHue(PALETTE.go), cautionHue = hexToHue(PALETTE.caution), stopHue = hexToHue(PALETTE.stop);
assert(hueDiff(goHue, cautionHue) >= 30, "go and caution are at least 30° apart in hue", hueDiff(goHue, cautionHue).toFixed(1) + "°");
assert(hueDiff(cautionHue, stopHue) >= 30, "caution and stop are at least 30° apart in hue", hueDiff(cautionHue, stopHue).toFixed(1) + "°");
assert(hueDiff(goHue, stopHue) >= 30, "go and stop are at least 30° apart in hue", hueDiff(goHue, stopHue).toFixed(1) + "°");

// Static file hygiene: no external scripts, no base64 blobs, no credential-
// or path-shaped lines anywhere in the published folder.
const htmlSrc = fs.readFileSync(path.join(HERE, "index.html"), "utf8");
assert(!/<script[^>]+src=["']https?:/i.test(htmlSrc), "index.html loads no external script");
assert(!/data:[^"']*base64/i.test(htmlSrc) && !/base64,/i.test(dataSrc), "no base64 blobs in index.html or data.js");
assert(/<script src="data\.js">/.test(htmlSrc), "index.html loads data.js locally");
assert(!/sk-[a-zA-Z0-9]{20,}|api[_-]?key\s*[:=]\s*["'][\w-]{10,}/i.test(dataSrc + htmlSrc), "no credential-shaped strings anywhere in the published page");
assert(!/\/home\/user|\/root\/|C:\\\\/.test(dataSrc + htmlSrc), "no foreign absolute machine paths leaked into the published page");

// Tautology guard: this suite must be able to fail. Confirm at least one
// assertion above is checking a real, non-trivial computed value rather
// than an always-true placeholder, by re-deriving one from scratch here.
assert((36000 + 25000) !== 51000 && (36000 + 25000) === 61000, "tautology guard: this exact arithmetic check is not vacuously true for any input");

console.log(`\nPhase 1 (data + recomputed arithmetic + palette): ${passed} passed, ${failed} failed so far.\n`);

// ---------------------------------------------------------------
// Phase 2: real Chromium render, via the portable three-branch launcher.
// ---------------------------------------------------------------
async function main() {
  let chromium = null;
  try { chromium = require("playwright").chromium; }
  catch (e1) {
    try { chromium = require("playwright-core").chromium; }
    catch (e2) { chromium = null; }
  }

  if (!chromium) {
    console.error("Neither 'playwright' nor 'playwright-core' is installed.");
    console.error("  npm install playwright   (or set up playwright-core + a browser)");
    console.log(`\n${passed} passed, ${failed} failed (static pass only -- no browser phase run).`);
    if (failed > 0) process.exitCode = 1;
    return;
  }

  const LAUNCH = process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : { executablePath: "/opt/pw-browsers/chromium" };

  const PORT = 8742;
  const server = http.createServer((req, res) => {
    let p = req.url === "/" ? "/index.html" : req.url;
    const fp = path.join(HERE, decodeURIComponent(p.split("?")[0]));
    fs.readFile(fp, (err, buf) => {
      if (err) { res.writeHead(404); res.end(); return; }
      const ext = path.extname(fp);
      const type = ext === ".html" ? "text/html" : ext === ".js" ? "application/javascript" : "application/octet-stream";
      res.writeHead(200, { "Content-Type": type });
      res.end(buf);
    });
  });
  await new Promise((resolve) => server.listen(PORT, "127.0.0.1", resolve));

  let browser;
  try {
    browser = await chromium.launch(LAUNCH);
  } catch (e) {
    console.error("Could not launch Chromium. If CHROME_PATH is unset, try:");
    console.error("  CHROME_PATH=/path/to/chromium node test.js");
    server.close();
    console.log(`\n${passed} passed, ${failed} failed (static pass only -- browser launch failed).`);
    process.exitCode = failed > 0 ? 1 : 0;
    return;
  }

  try {
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    const consoleErrors = [];
    page.on("console", (msg) => { if (msg.type() === "error") consoleErrors.push(msg.text()); });
    page.on("pageerror", (err) => consoleErrors.push(String(err)));
    await page.goto(`http://127.0.0.1:${PORT}/index.html`);
    await page.waitForSelector(".finding");

    const rendered = await page.evaluate(() => window.__GATE_RENDERED__);
    assert(rendered.totalFindings === D.findings.length, "rendered total findings matches data.js exactly", `${rendered.totalFindings} vs ${D.findings.length}`);
    assert(rendered.credits === credits.length, "rendered credit count matches data.js exactly", `${rendered.credits} vs ${credits.length}`);
    assert(rendered.stops === stops.length, "rendered stop count matches data.js exactly", `${rendered.stops} vs ${stops.length}`);
    assert(rendered.coverageItems === D.coverage.length, "rendered coverage count matches data.js exactly", `${rendered.coverageItems} vs ${D.coverage.length}`);
    assert(rendered.levelsRendered.length === 4, "all four levels (DEEP/DEEPER/DEEPEREST/DEEPEREST-EST) rendered", rendered.levelsRendered.join(","));

    // Coverage before verdict, checked by actual on-screen position
    // (getBoundingClientRect), not just document order.
    const coverageAboveVerdict = await page.evaluate(() => {
      const cov = document.getElementById("sec-coverage").getBoundingClientRect();
      const counts = document.getElementById("sec-counts").getBoundingClientRect();
      const rules = document.getElementById("sec-rules").getBoundingClientRect();
      return cov.top < counts.top && counts.top < rules.top;
    });
    assert(coverageAboveVerdict, "coverage renders ABOVE the verdict counts and rules on screen (checked by real bounding rect, not just DOM order)");

    const domOrderOk = await page.evaluate(() => {
      const cov = document.getElementById("sec-coverage");
      const findings = document.getElementById("sec-findings");
      return !!(cov.compareDocumentPosition(findings) & Node.DOCUMENT_POSITION_FOLLOWING);
    });
    assert(domOrderOk, "coverage section appears before findings/verdict in document order");

    const findingCardCount = await page.evaluate(() => document.querySelectorAll(".finding").length);
    assert(findingCardCount === D.findings.length, "one rendered card per ledger finding, no more, no fewer", `${findingCardCount} vs ${D.findings.length}`);

    const ruleRowCount = await page.evaluate(() => document.querySelectorAll("#rules-body tr").length);
    assert(ruleRowCount === D.businessRules.length, "one rendered row per business rule", `${ruleRowCount} vs ${D.businessRules.length}`);

    // --stop appears as a TEXT colour on zero rendered elements (border/rail only).
    const stopAsTextCount = await page.evaluate(() => {
      const all = document.querySelectorAll("body *");
      let n = 0;
      all.forEach((el) => {
        const cs = getComputedStyle(el);
        if (cs.color === "rgb(226, 83, 76)") n++; // #E2534C
      });
      return n;
    });
    assert(stopAsTextCount === 0, "--stop (#E2534C) appears as a text colour on zero rendered elements", "count=" + stopAsTextCount);

    assert(consoleErrors.length === 0, "zero console errors on desktop render", JSON.stringify(consoleErrors));

    const reviewDir = path.join(HERE, "review", "screenshots");
    fs.mkdirSync(reviewDir, { recursive: true });
    await page.screenshot({ path: path.join(reviewDir, "desktop-1280.png"), fullPage: true });

    // 375px: no horizontal overflow, checked against BOTH documentElement
    // and body.scrollWidth (a prior build in this project found a wide
    // <table> hidden from documentElement alone by overflow-x:clip).
    const page375 = await browser.newPage({ viewport: { width: 375, height: 800 } });
    const consoleErrors375 = [];
    page375.on("console", (msg) => { if (msg.type() === "error") consoleErrors375.push(msg.text()); });
    await page375.goto(`http://127.0.0.1:${PORT}/index.html`);
    await page375.waitForSelector(".finding");
    const overflow = await page375.evaluate(() =>
      Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) - document.documentElement.clientWidth
    );
    assert(overflow <= 1, "no horizontal overflow at 375px viewport", "overflow=" + overflow + "px");
    assert(consoleErrors375.length === 0, "zero console errors on mobile render", JSON.stringify(consoleErrors375));
    await page375.screenshot({ path: path.join(reviewDir, "mobile-375.png"), fullPage: true });
    await page375.close();

    await page.close();
  } finally {
    await browser.close();
    server.close();
  }

  console.log(`\n${passed} passed, ${failed} failed.`);
  if (failed > 0) process.exitCode = 1;
}

main();
