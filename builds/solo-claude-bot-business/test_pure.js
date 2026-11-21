"use strict";
// Pure-logic tests for assets/app.js -- no DOM, no browser.
// Run with: node test_pure.js
const assert = require("assert");
const {
  SOURCE_UPFRONT_TO_MONTHLY_RATIO,
  DEFAULT_HOURS_PER_MONTH,
  computeOffer,
  CONTACT_STATUSES,
  CALL_GOAL,
  REFERRALS_PER_CASE_STUDY_GOAL,
  makeContact,
  pipelineSummary,
  STACK_CATEGORIES,
  defaultChecklist,
  checklistProgress,
  defaultState,
  loadState,
  saveState,
  STORAGE_KEY,
} = require("./assets/app.js");

let passed = 0, failed = 0;
function test(name, fn) {
  try {
    fn();
    passed++;
    console.log("ok   - " + name);
  } catch (e) {
    failed++;
    console.error("FAIL - " + name + " -- " + e.message);
  }
}

// ---------------- computeOffer ----------------
test("computeOffer: real example from the source's own $200/mo baseline, 10x multiplier", () => {
  const r = computeOffer({ nicheBaseline: 200, multiplier: 10, upfrontRatio: SOURCE_UPFRONT_TO_MONTHLY_RATIO, hoursPerMonth: DEFAULT_HOURS_PER_MONTH });
  assert.strictEqual(r.recommendedMonthly, 2000);
  assert.ok(Math.abs(r.suggestedUpfront - 16666.67) < 1, "upfront ~16,667 for 10x multiplier");
});

test("computeOffer: the real source numbers reproduce exactly ($200 baseline, 20x, real 8.3333 ratio)", () => {
  const r = computeOffer({ nicheBaseline: 200, multiplier: 20, upfrontRatio: SOURCE_UPFRONT_TO_MONTHLY_RATIO, hoursPerMonth: DEFAULT_HOURS_PER_MONTH });
  assert.strictEqual(r.recommendedMonthly, 4000);
  // 4000 * (25000/3000) = 33,333.33
  assert.ok(Math.abs(r.suggestedUpfront - 33333.33) < 1);
});

test("computeOffer: the actual $3,000/mo + $25,000 upfront combination from the source reproduces exactly", () => {
  // monthly=3000 is achieved at baseline=200, multiplier=15
  const r = computeOffer({ nicheBaseline: 200, multiplier: 15, upfrontRatio: SOURCE_UPFRONT_TO_MONTHLY_RATIO, hoursPerMonth: DEFAULT_HOURS_PER_MONTH });
  assert.strictEqual(r.recommendedMonthly, 3000);
  assert.ok(Math.abs(r.suggestedUpfront - 25000) < 1, "upfront should land exactly on the source's real $25,000 figure");
});

test("computeOffer: effective hourly rate uses the VISIBLE hours assumption, not a hidden one", () => {
  const r = computeOffer({ nicheBaseline: 200, multiplier: 15, upfrontRatio: 8, hoursPerMonth: 250 });
  // Same $3,000/mo as the source's own example, same 250hr assumption the
  // audit found hidden in the source -- reproduces the source's own $12/hr
  // figure, but ONLY because hoursPerMonth=250 is explicit here, never
  // defaulted silently.
  assert.ok(Math.abs(r.effectiveHourlyRate - 12) < 0.01);
});

test("computeOffer: the DEFAULT hours-per-month basis is a standard full-time month, not the source's hidden 250hr assumption", () => {
  assert.ok(Math.abs(DEFAULT_HOURS_PER_MONTH - 173.33) < 0.01);
  assert.notStrictEqual(DEFAULT_HOURS_PER_MONTH, 250, "must not silently reuse the audit's found bug");
});

test("computeOffer: rejects non-positive inputs instead of producing nonsense", () => {
  assert.throws(() => computeOffer({ nicheBaseline: 0, multiplier: 10, upfrontRatio: 8, hoursPerMonth: 170 }));
  assert.throws(() => computeOffer({ nicheBaseline: 200, multiplier: -1, upfrontRatio: 8, hoursPerMonth: 170 }));
  assert.throws(() => computeOffer({ nicheBaseline: 200, multiplier: 10, upfrontRatio: 8, hoursPerMonth: 0 }));
});

test("SOURCE_UPFRONT_TO_MONTHLY_RATIO is exactly the real source's 25000/3000 ratio", () => {
  assert.ok(Math.abs(SOURCE_UPFRONT_TO_MONTHLY_RATIO - 8.3333) < 0.001);
});

// ---------------- Client pipeline ----------------
test("makeContact: creates a contact with a valid default status", () => {
  const c = makeContact({ name: "  Jane Smith  " });
  assert.strictEqual(c.name, "Jane Smith", "name is trimmed");
  assert.strictEqual(c.status, "not-contacted");
  assert.strictEqual(c.referrals, 0);
  assert.ok(c.id && c.id.length > 0);
});

test("makeContact: rejects an empty name", () => {
  assert.throws(() => makeContact({ name: "" }));
  assert.throws(() => makeContact({ name: "   " }));
});

test("makeContact: rejects an invalid status", () => {
  assert.throws(() => makeContact({ name: "X", status: "bogus" }));
});

test("pipelineSummary: counts by status correctly, not just a total", () => {
  const contacts = [
    makeContact({ name: "A", status: "not-contacted" }),
    makeContact({ name: "B", status: "called" }),
    makeContact({ name: "C", status: "called" }),
    makeContact({ name: "D", status: "interested" }),
    makeContact({ name: "E", status: "case-study", referrals: 2 }),
    makeContact({ name: "F", status: "referred-client", referrals: 1 }),
  ];
  const s = pipelineSummary(contacts);
  assert.strictEqual(s.totalContacts, 6);
  assert.strictEqual(s.byStatus["called"], 2);
  assert.strictEqual(s.byStatus["not-contacted"], 1);
  assert.strictEqual(s.calledOrFurther, 5, "everyone except the not-contacted one");
  assert.strictEqual(s.caseStudiesStarted, 2, "case-study + referred-client both count");
  assert.strictEqual(s.totalReferrals, 3);
  assert.strictEqual(s.referralGoal, 2 * REFERRALS_PER_CASE_STUDY_GOAL, "3 referrals per case study, matching the source's real client-acquisition sequence");
});

test("pipelineSummary: call-goal progress is capped at 1.0 even past the 50-call goal", () => {
  const contacts = [];
  for (let i = 0; i < CALL_GOAL + 10; i++) contacts.push(makeContact({ name: "C" + i, status: "called" }));
  const s = pipelineSummary(contacts);
  assert.strictEqual(s.callGoalProgress, 1);
});

test("pipelineSummary: an empty pipeline reports zero everywhere, no NaN/division errors", () => {
  const s = pipelineSummary([]);
  assert.strictEqual(s.totalContacts, 0);
  assert.strictEqual(s.callGoalProgress, 0);
  assert.strictEqual(s.referralGoal, 0);
  assert.ok(!Number.isNaN(s.callGoalProgress));
});

// ---------------- Build checklist ----------------
test("defaultChecklist: starts with all 4 real stack categories from the source, none pre-filled", () => {
  const cl = defaultChecklist();
  assert.deepStrictEqual(Object.keys(cl.stack).sort(), STACK_CATEGORIES.slice().sort());
  STACK_CATEGORIES.forEach((cat) => {
    assert.strictEqual(cl.stack[cat].tool, "", cat + " starts with no vendor name pre-filled -- the audit found the source's own named vendors don't exactly match real products");
    assert.strictEqual(cl.stack[cat].docsRead, false);
  });
});

test("checklistProgress: 0/4 steps on a fresh checklist", () => {
  const p = checklistProgress(defaultChecklist());
  assert.strictEqual(p.completedSteps, 0);
  assert.strictEqual(p.totalSteps, 4);
  assert.strictEqual(p.isComplete, false);
});

test("checklistProgress: the stack step only counts complete once ALL 4 categories have both a tool name AND docs-read checked", () => {
  const cl = defaultChecklist();
  cl.stack.compute.tool = "a cloud desktop provider";
  cl.stack.compute.docsRead = true;
  cl.stack.email.tool = "an agent email provider";
  // email.docsRead still false -- stack step must NOT count as done yet
  let p = checklistProgress(cl);
  assert.strictEqual(p.stackDone, 1);
  assert.strictEqual(p.completedSteps, 0, "stack step requires all 4 categories, not just some");

  STACK_CATEGORIES.forEach((cat) => {
    cl.stack[cat].tool = "tool-" + cat;
    cl.stack[cat].docsRead = true;
  });
  p = checklistProgress(cl);
  assert.strictEqual(p.stackDone, 4);
});

test("checklistProgress: all 4 steps true gives isComplete=true", () => {
  const cl = defaultChecklist();
  cl.researchDone = true;
  cl.designDone = true;
  STACK_CATEGORIES.forEach((cat) => {
    cl.stack[cat].tool = "x";
    cl.stack[cat].docsRead = true;
  });
  cl.buildDone = true;
  const p = checklistProgress(cl);
  assert.strictEqual(p.isComplete, true);
  assert.strictEqual(p.completedSteps, 4);
});

// ---------------- Persistence (fake localStorage) ----------------
function fakeStorage() {
  const data = {};
  return {
    getItem: (k) => (k in data ? data[k] : null),
    setItem: (k, v) => { data[k] = v; },
    _data: data,
  };
}

test("loadState: returns real defaults when storage is empty", () => {
  const storage = fakeStorage();
  const s = loadState(storage);
  assert.deepStrictEqual(s, defaultState());
});

test("saveState + loadState: a real round trip preserves offer, contacts, and checklist", () => {
  const storage = fakeStorage();
  const state = defaultState();
  state.offer.nicheBaseline = 350;
  state.offer.multiplier = 12;
  state.contacts.push(makeContact({ name: "Round Trip Test", status: "interested", referrals: 1 }));
  state.checklist.researchDone = true;
  state.checklist.stack.compute.tool = "test-compute-tool";
  state.checklist.stack.compute.docsRead = true;

  saveState(storage, state);
  const loaded = loadState(storage);

  assert.strictEqual(loaded.offer.nicheBaseline, 350);
  assert.strictEqual(loaded.offer.multiplier, 12);
  assert.strictEqual(loaded.contacts.length, 1);
  assert.strictEqual(loaded.contacts[0].name, "Round Trip Test");
  assert.strictEqual(loaded.checklist.researchDone, true);
  assert.strictEqual(loaded.checklist.stack.compute.tool, "test-compute-tool");
});

test("loadState: a corrupted localStorage value falls back to defaults instead of throwing", () => {
  const storage = fakeStorage();
  storage.setItem(STORAGE_KEY, "{not valid json");
  const s = loadState(storage);
  assert.deepStrictEqual(s, defaultState());
});

test("loadState: an older saved profile missing newer fields merges with defaults rather than breaking", () => {
  const storage = fakeStorage();
  storage.setItem(STORAGE_KEY, JSON.stringify({ offer: { nicheBaseline: 500 } }));
  const s = loadState(storage);
  assert.strictEqual(s.offer.nicheBaseline, 500, "the one field that was saved is preserved");
  assert.strictEqual(s.offer.multiplier, defaultState().offer.multiplier, "a missing field falls back to default rather than being undefined");
  assert.deepStrictEqual(s.contacts, []);
  assert.strictEqual(s.checklist.researchDone, false);
});

console.log(`\n${passed} passed, ${failed} failed.`);
if (failed > 0) process.exitCode = 1;
