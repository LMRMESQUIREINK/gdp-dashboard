// Pure-logic tests, no browser needed: the lerp frame-rate-independence
// claim from scrub-pipeline.md, the smoothstep band-opacity math, and the
// "five gate strings must be character-for-character identical in CSS
// and JS" rule the spec calls out explicitly as a real, shipped failure
// mode if violated.
//
// Run with: node test_pure.mjs
import { readFileSync } from "node:fs";
import assert from "node:assert/strict";

let passed = 0;
function test(name, fn) {
  try { fn(); passed++; console.log("ok   -", name); }
  catch (e) { console.error("FAIL -", name, "\n     ", e.message); process.exitCode = 1; }
}

// ---------- The lerp formula's claimed frame-rate independence ----------
function simulateTimeToHalf(dtMs, k, normalized) {
  let shown = 0;
  let t = 0;
  while (shown < 0.5) {
    const factor = normalized ? (1 - Math.pow(1 - k, dtMs / 16.667)) : k;
    shown += (1 - shown) * factor;
    t += dtMs;
  }
  return t;
}

test("normalized lerp converges at the same real-time speed at 60fps and 120fps", () => {
  const t60 = simulateTimeToHalf(16.667, 0.16, true);
  const t120 = simulateTimeToHalf(8.333, 0.16, true);
  assert.ok(Math.abs(t60 - t120) < 1, `expected near-identical convergence time, got ${t60}ms vs ${t120}ms`);
});

test("naive constant-per-frame lerp (the documented anti-pattern) converges ~2x faster at 120fps", () => {
  const t60 = simulateTimeToHalf(16.667, 0.18, false);
  const t120 = simulateTimeToHalf(8.333, 0.18, false);
  const ratio = t60 / t120;
  assert.ok(ratio > 1.8 && ratio < 2.2, `expected ~2x discrepancy, got ratio ${ratio.toFixed(2)}`);
});

// ---------- Smoothstep (copied from index.html's own implementation) ----------
function smoothstep(p, e0, e1) {
  const t = Math.min(1, Math.max(0, (p - e0) / (e1 - e0)));
  return t * t * (3 - 2 * t);
}

test("smoothstep is 0 at the start edge and 1 at the end edge", () => {
  assert.equal(smoothstep(0.1, 0.1, 0.3), 0);
  assert.equal(smoothstep(0.3, 0.1, 0.3), 1);
});

test("smoothstep is monotonic across its range", () => {
  let prev = -1;
  for (let p = 0; p <= 1; p += 0.05) {
    const v = smoothstep(p, 0.2, 0.8);
    assert.ok(v >= prev - 1e-9, `smoothstep went backwards at p=${p}`);
    prev = v;
  }
});

// ---------- The five static-hero gates: CSS and JS must be identical ----------
const html = readFileSync(new URL("./index.html", import.meta.url), "utf8");

const jsGatesMatch = html.match(/var GATES = \[([\s\S]*?)\];/);
assert.ok(jsGatesMatch, "could not find the JS GATES array in index.html");
const jsGates = [...jsGatesMatch[1].matchAll(/'([^']+)'/g)].map((m) => m[1]);

const cssBlockMatch = html.match(/\/\* --+ Static-hero gates[^*]*\*\/\s*@media ([\s\S]*?)\{/);
assert.ok(cssBlockMatch, "could not find the static-hero gates @media block in index.html");
const cssGates = cssBlockMatch[1]
  .split(",")
  .map((s) => s.trim().replace(/\s+/g, " "))
  .filter(Boolean);

test("exactly 5 gates declared in both CSS and JS", () => {
  assert.equal(jsGates.length, 5, `JS had ${jsGates.length}`);
  assert.equal(cssGates.length, 5, `CSS had ${cssGates.length}`);
});

test("every JS gate string is character-for-character identical to its CSS counterpart", () => {
  for (let i = 0; i < 5; i++) {
    assert.equal(cssGates[i], jsGates[i], `gate ${i} differs:\n  CSS: ${JSON.stringify(cssGates[i])}\n  JS:  ${JSON.stringify(jsGates[i])}`);
  }
});

console.log(`\n${passed} test(s) passed.`);
