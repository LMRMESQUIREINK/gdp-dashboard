// Pure-logic tests for the generator functions in standalone/assets/app.js --
// no browser needed. We stub just enough of `document`/`crypto` for the
// module's top-level DOMContentLoaded wiring to load without throwing, then
// pull the real functions off the exposed window.__CreatorEmpire object.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const appJsPath = path.join(here, "..", "standalone", "assets", "app.js");
const src = readFileSync(appJsPath, "utf8");

let failures = 0, passed = 0;
function assert(cond, msg) {
  if (cond) { passed++; }
  else { failures++; console.error("FAIL: " + msg); }
}

// Minimal DOM stub: addEventListener captures the DOMContentLoaded callback
// instead of running it (there is no document.getElementById("stepper")
// etc. in this harness, and we don't need the wiring -- only the exported
// generator functions).
let domReadyCallback = null;
global.document = {
  addEventListener(name, cb) { if (name === "DOMContentLoaded") domReadyCallback = cb; },
  getElementById() { return null; },
  createElement() { return { appendChild() {}, click() {}, remove() {} }; },
  body: { appendChild() {}, removeChild() {} },
};
global.window = {};
// Node's own global `crypto` already has randomUUID() (Node 19+) -- app.js
// checks `crypto && crypto.randomUUID` before using it, so no stub needed.
global.alert = () => {};

// eslint-disable-next-line no-eval
const fn = new Function(src);
fn();

assert(domReadyCallback !== null, "the module registered a DOMContentLoaded handler");
const api = global.window.__CreatorEmpire;
assert(!!api, "window.__CreatorEmpire was exposed for testing");

const brief = {
  brand: "Goli Nutrition",
  product: "ACV gummies",
  audience: "busy parents",
  benefit: "a gut-health habit that actually tastes good",
  duration: "40",
  ratio: "9:16",
};

// --- SUITES: the library honestly marks only 6 of 18 apps as live ---
const liveCount = api.SUITES.reduce(
  (n, suite) => n + suite.apps.filter((a) => a.live).length, 0
);
assert(liveCount === 6, `exactly 6 of 18 apps are marked live (got ${liveCount})`);
assert(api.SUITES.length === 6, "there are 6 suites");
assert(api.SUITES.every((s) => s.apps.length === 3), "every suite has exactly 3 apps");

// --- generateHooks ---
const hooks = api.generateHooks(brief);
assert(hooks.length === 5, `generateHooks returns 5 options (got ${hooks.length})`);
assert(new Set(hooks).size === hooks.length, "the 5 hooks are not duplicates of each other");
assert(hooks.every((h) => typeof h === "string" && h.length > 10), "every hook is a real non-trivial string");

// --- generateScript ---
const script = api.generateScript(brief, hooks[0]);
const expectedParts = ["Hook", "Problem", "Agitate", "Solution / Demo", "Proof", "Offer", "CTA"];
assert(script.length === 7, `generateScript returns all 7 parts (got ${script.length})`);
assert(
  script.map((p) => p.part).join("|") === expectedParts.join("|"),
  "the 7 parts are in the documented order: " + expectedParts.join(", ")
);
assert(script[0].text === hooks[0], "the script's Hook part is exactly the selected hook, not regenerated");

// --- generateStoryboard: scenes must tile the full duration with no gaps ---
[15, 40, 60].forEach((duration) => {
  const scenes = api.generateStoryboard(duration, brief);
  assert(scenes.length >= 3, `storyboard for ${duration}s has at least 3 scenes (got ${scenes.length})`);
  assert(scenes[0].start === 0, `storyboard for ${duration}s starts at 0s (got ${scenes[0].start})`);
  assert(
    scenes[scenes.length - 1].end === duration,
    `storyboard for ${duration}s ends exactly at ${duration}s (got ${scenes[scenes.length - 1].end})`
  );
  for (let i = 1; i < scenes.length; i++) {
    assert(
      scenes[i].start === scenes[i - 1].end,
      `storyboard for ${duration}s: scene ${i} starts exactly where scene ${i - 1} ends (no gap/overlap)`
    );
  }
});

// --- generateBeatMap: transition_second is a correct, deterministic computation ---
const bm1 = api.generateBeatMap("R&B", "Hip-Hop", 30, "40");
assert(bm1.transition_second === 12, `30% of 40s transitions at 12s (got ${bm1.transition_second})`);
const bm2 = api.generateBeatMap("Lo-fi", "EDM", 50, "60");
assert(bm2.transition_second === 30, `50% of 60s transitions at 30s (got ${bm2.transition_second})`);
assert(bm1.intro_genre === "R&B" && bm1.drop_genre === "Hip-Hop", "beat map records the chosen genres exactly");

// --- generateAds ---
const ads = api.generateAds(brief);
assert(ads.length === 3, `generateAds returns 3 distinct ad angles (got ${ads.length})`);
assert(new Set(ads.map((a) => a.hook)).size === 3, "the 3 ad hooks are genuinely distinct, not copies");

// --- timeLabel formatting ---
assert(api.timeLabel({ start: 0, end: 5 }) === "00–05s", "timeLabel zero-pads single digits");
assert(api.timeLabel({ start: 12, end: 25 }) === "12–25s", "timeLabel formats double digits plainly");

// --- campaignToMarkdown: the export actually contains the real data, not placeholders ---
const campaign = {
  brand: brief.brand, product: brief.product, audience: brief.audience, benefit: brief.benefit,
  duration_seconds: 40, aspect_ratio: "9:16",
  music: { intro: "R&B", drop: "Hip-Hop", transition_second: 12 },
  modules: { selected_hook: hooks[0], sales_script: script, storyboard: api.generateStoryboard(40, brief), ad_creatives: ads },
};
const md = api.campaignToMarkdown(campaign);
assert(md.includes(brief.brand), "markdown export contains the real brand name");
assert(md.includes(hooks[0]), "markdown export contains the actual selected hook text");
assert(md.includes("Hip-Hop"), "markdown export contains the real beat-map genre");

console.log(`\n${passed} passed, ${failures} failed`);
process.exit(failures > 0 ? 1 : 0);
