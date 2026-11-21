// RUTHLESS GATE test suite for the "20 Agentic Engineering Concepts" /
// "20 System Design Concepts" verdict page (two sources, one file).
// Two phases: pure-data assertions (no browser), then a real Chromium
// render via the portable launcher block, serving the page over a real
// local HTTP server (not file://, same discipline this project uses
// everywhere else for anything visual).
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

const VALID_PROVENANCE = new Set(["sourced", "sourced-dated", "source-is-silent", "not-supplied", "not-checked"]);
D.findings.forEach(function (f) {
  assert(typeof f.evidence === "string" && f.evidence.length > 12, "finding " + f.id + " has a real evidence string", "len=" + (f.evidence || "").length);
  assert(VALID_PROVENANCE.has(f.provenance), "finding " + f.id + " declares a valid provenance state", f.provenance);
  assert(f.type === "credit" || f.type === "stop", "finding " + f.id + " is typed credit or stop", f.type);
  assert(["DEEP", "DEEPER", "DEEPEREST", "DEEPEREST-EST"].includes(f.level), "finding " + f.id + " has a valid level", f.level);
});

const stops = D.findings.filter((f) => f.type === "stop");
stops.forEach(function (f) {
  const hasFileLine = /\.(js|md|py|html|txt)[:,]?\s*lines?\s*\d|:\d+/.test(f.evidence);
  const hasCommand = /^(grep|python3|node|wc|sha256sum|pdftotext)/.test(f.evidence.trim()) || / grep | python3 | wc | sha256sum /.test(f.evidence);
  const hasNamedSource = /anthropic\.com|theregister\.com|eweek\.com|techtarget\.com|devblogs\.microsoft\.com|owasp|\/notes\//i.test(f.evidence);
  assert(hasFileLine || hasCommand || hasNamedSource, "stop " + f.id + " names a file:line, a command, or an outside source, not just an opinion", f.evidence.slice(0, 60));
});

const credits = D.findings.filter((f) => f.type === "credit");
assert(credits.length >= stops.length, "verified (credit) column is not smaller than the stop column", `credits=${credits.length} stops=${stops.length}`);
assert(credits.length > 0 && stops.length > 0, "both credit and stop findings exist (not just arguing one side)");

D.businessRules.forEach(function (r) {
  assert(["clears", "COLLIDES", "n/a"].includes(r.verdict), "business rule verdict is a valid tag", r.verdict);
  assert(r.evidence && r.evidence.length > 12, "business rule has real evidence", r.rule);
});

// Per-source requirement (the procedure's own rule for multi-source rounds):
// each article must get at least one credit AND one stop of its own.
const VALID_SOURCE_TAGS = new Set(["article1", "article2", "both"]);
D.findings.forEach(function (f) {
  assert(VALID_SOURCE_TAGS.has(f.source), "finding " + f.id + " is tagged with a valid source", f.source);
});
(D.source.articles || []).forEach(function (a) {
  const relevant = D.findings.filter((f) => f.source === a.id || f.source === "both");
  const c = relevant.filter((f) => f.type === "credit").length;
  const s = relevant.filter((f) => f.type === "stop").length;
  assert(c >= 1, a.id + " receives at least one credit (not only attacked)", "credits=" + c);
  assert(s >= 1, a.id + " receives at least one stop (not waved through)", "stops=" + s);
});

// Arithmetic recompute: the "20 concepts" claims, from the source's own raw
// numbers, not from data.js's own claim about itself.
const extractedText = fs.readFileSync(path.join(HERE, "source", "raw.txt"), "utf8");
const article1Text = extractedText.slice(0, extractedText.indexOf("20 System Design Concepts"));
const article2Text = extractedText.slice(extractedText.indexOf("20 System Design Concepts"));
const article1Count = (article1Text.match(/^\d{1,2}\. /gm) || []).length;
const article2Count = (article2Text.match(/^\d{1,2}\. /gm) || []).length;
assert(article1Count === 20, "recomputed: article1 really numbers exactly 20 concepts, independent of data.js's own claim", "counted=" + article1Count);
assert(article2Count === 20, "recomputed: article2 really numbers exactly 20 concepts, independent of data.js's own claim", "counted=" + article2Count);

// Humanizer zero-finding claim, recomputed by actually re-running the tool
// here rather than trusting data.js's cached report of a prior run.
const { execFileSync } = require("child_process");
const humanizerPath = path.join(HERE, "..", "humanizer", "humanizer.py");
let humanizerFindingCount = null;
try {
  const out = execFileSync("python3", [humanizerPath, path.join(HERE, "source", "raw.txt"), "--json"], { encoding: "utf8" });
  humanizerFindingCount = JSON.parse(out).finding_count;
} catch (e) { /* leave null; asserted below */ }
assert(humanizerFindingCount === 0, "recomputed: re-running this project's own Humanizer live finds 0 AI-writing-tell hits, not cached from data.js", "got=" + humanizerFindingCount);

// Self-check: article2's named memory types really have no equivalent name
// anywhere in article1 (the deepest-01 finding's own claim).
const article1HasProcedural = /procedural memory/i.test(article1Text);
assert(!article1HasProcedural, "recomputed: 'procedural memory' really does not appear anywhere in article1", "found=" + article1HasProcedural);
const article2HasProcedural = /procedural memory/i.test(article2Text);
assert(article2HasProcedural, "recomputed: 'procedural memory' really does appear in article2");

// Contrast and palette checks (WCAG relative luminance, computed here, not eyeballed).
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
const PALETTE = { panel: "#1A1D21", plate: "#24282E", engrave: "#111316", go: "#3BD17E", caution: "#F2A93B", stop: "#E2534C", stopInk: "#E8615A", ink: "#E8EAED", ink2: "#9AA2AC" };
const stopOnPanel = contrastRatio(PALETTE.stop, PALETTE.panel);
assert(stopOnPanel >= 4.4 && stopOnPanel <= 4.6, "--stop on --panel measures ~4.49:1 as the spec states", stopOnPanel.toFixed(2) + ":1");
const inkOnPanel = contrastRatio(PALETTE.ink, PALETTE.panel);
assert(inkOnPanel >= 4.5, "body text (--ink on --panel) clears 4.5:1", inkOnPanel.toFixed(2) + ":1");
const ink2OnPlate = contrastRatio(PALETTE.ink2, PALETTE.plate);
assert(ink2OnPlate >= 3.0, "secondary text (--ink2 on --plate) clears 3:1 for interface-level text", ink2OnPlate.toFixed(2) + ":1");

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

// Static file hygiene: no external scripts, no base64 blobs.
const htmlSrc = fs.readFileSync(path.join(HERE, "index.html"), "utf8");
assert(!/<script[^>]+src=["']https?:/i.test(htmlSrc), "index.html loads no external script");
assert(!/data:[^"']*base64/i.test(htmlSrc) && !/base64,/i.test(dataSrc), "no base64 blobs in index.html or data.js");
assert(/<script src="data\.js">/.test(htmlSrc), "index.html loads data.js locally");

console.log(`\nPhase 1 (data + static checks): ${passed} passed, ${failed} failed so far.\n`);

// ---------------------------------------------------------------
// Phase 2: real Chromium render, via the portable launcher.
// ---------------------------------------------------------------
async function main() {
  let chromium;
  try { chromium = require("playwright").chromium; }
  catch (e) { chromium = require("playwright-core").chromium; }
  const LAUNCH = process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : { executablePath: "/opt/pw-browsers/chromium" };

  const PORT = 8731;
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
    process.exitCode = 1;
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

    assert(consoleErrors.length === 0, "zero console errors on desktop render", JSON.stringify(consoleErrors));

    const reviewDir = path.join(HERE, "review", "screenshots");
    fs.mkdirSync(reviewDir, { recursive: true });
    await page.screenshot({ path: path.join(reviewDir, "desktop-1280.png"), fullPage: true });

    // 375px: no horizontal overflow.
    const page375 = await browser.newPage({ viewport: { width: 375, height: 800 } });
    const consoleErrors375 = [];
    page375.on("console", (msg) => { if (msg.type() === "error") consoleErrors375.push(msg.text()); });
    await page375.goto(`http://127.0.0.1:${PORT}/index.html`);
    await page375.waitForSelector(".finding");
    // documentElement.scrollWidth alone is blind to overflow hidden by
    // overflow-x:clip on html/body — found by actually comparing it
    // against body.scrollWidth (and the real fullPage screenshot width)
    // during this build: a wide <table> pushed body.scrollWidth to 455px
    // while documentElement still reported a clean 375px. Check both.
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
