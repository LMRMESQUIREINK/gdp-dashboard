"use strict";

// ---------------------------------------------------------------
// Solo Claude Bot Business -- pure logic (no DOM), unit-testable.
// Built from the real, audited content of the source transcript
// ("The $1M+ Solo Grok Bot Business (Full Course)," see
// /notes/solo-bot-business-gate-analysis.md), not its unverified
// claims. Deliberately fixes the one real bug the audit found in the
// source's own math: the "$3,000/month is like $12/hour" framing
// hid its own 250-hour-a-month assumption. Here the hours assumption
// is always a visible, editable input -- never hidden behind a round
// number.
// ---------------------------------------------------------------

const STORAGE_KEY = "solo-claude-bot-business-v1";

// The one real ratio recoverable from the source transcript's own
// numbers: $25,000 upfront vs. the $3,000/mo retainer it's paired
// with (source/raw.txt lines 63-70, 488-532 in the audit's own
// fixture). Used as a suggested upfront multiple of the computed
// monthly retainer -- a default, not a rule; always shown as editable.
const SOURCE_UPFRONT_TO_MONTHLY_RATIO = 25000 / 3000; // 8.3333...

// A standard full-time month (40hr/week * 52/12), used as the
// DEFAULT hours-per-month basis for the effective-hourly-rate
// calculation -- NOT the source's own hidden 250hr/month assumption
// (which implies ~8.3hrs of billable work every single day of the
// month, weekends included). The default here is honest and labeled;
// the user can still change it, and the label always states exactly
// what's being assumed.
const DEFAULT_HOURS_PER_MONTH = 173.33;

function computeOffer({ nicheBaseline, multiplier, upfrontRatio, hoursPerMonth }) {
  if (!(nicheBaseline > 0)) throw new Error("nicheBaseline must be a positive number");
  if (!(multiplier > 0)) throw new Error("multiplier must be a positive number");
  if (!(upfrontRatio > 0)) throw new Error("upfrontRatio must be a positive number");
  if (!(hoursPerMonth > 0)) throw new Error("hoursPerMonth must be a positive number");

  const recommendedMonthly = nicheBaseline * multiplier;
  const suggestedUpfront = recommendedMonthly * upfrontRatio;
  const effectiveHourlyRate = recommendedMonthly / hoursPerMonth;
  const firstYearValue = suggestedUpfront + recommendedMonthly * 12;

  return {
    recommendedMonthly,
    suggestedUpfront,
    effectiveHourlyRate,
    firstYearValue,
  };
}

// ---------------------------------------------------------------
// Client pipeline -- operationalizes the source's own real,
// credited client-acquisition sequence (call people you know, free
// first build for a case study, trade for referrals), not the
// unsubstantiated revenue headline.
// ---------------------------------------------------------------

const CONTACT_STATUSES = ["not-contacted", "called", "interested", "case-study", "referred-client"];
const CALL_GOAL = 50;
const REFERRALS_PER_CASE_STUDY_GOAL = 3;

function makeContact({ name, status = "not-contacted", referrals = 0, notes = "" }) {
  if (!name || !name.trim()) throw new Error("contact name is required");
  if (!CONTACT_STATUSES.includes(status)) throw new Error("invalid status: " + status);
  if (referrals < 0) throw new Error("referrals cannot be negative");
  return {
    id: "c_" + Math.random().toString(36).slice(2, 10),
    name: name.trim(),
    status,
    referrals,
    notes: notes || "",
    createdAt: new Date().toISOString(),
  };
}

function pipelineSummary(contacts) {
  const byStatus = {};
  CONTACT_STATUSES.forEach((s) => (byStatus[s] = 0));
  let totalReferrals = 0;
  contacts.forEach((c) => {
    byStatus[c.status] = (byStatus[c.status] || 0) + 1;
    totalReferrals += c.referrals || 0;
  });
  const calledOrFurther = contacts.filter((c) => c.status !== "not-contacted").length;
  const caseStudiesStarted = contacts.filter(
    (c) => c.status === "case-study" || c.status === "referred-client"
  ).length;
  return {
    totalContacts: contacts.length,
    byStatus,
    calledOrFurther,
    callGoalProgress: Math.min(calledOrFurther / CALL_GOAL, 1),
    caseStudiesStarted,
    totalReferrals,
    referralGoal: caseStudiesStarted * REFERRALS_PER_CASE_STUDY_GOAL,
  };
}

// ---------------------------------------------------------------
// Build checklist -- Research -> Design -> Build, with the four
// generalized stack categories from the source (compute, email,
// phone, connectors), deliberately NOT hardcoded to the source's
// own named vendors (Orgo/Agent Mail/Agent Phone/Composio) -- the
// audit found "Agent Mail"/"Agent Phone" don't exactly match any
// locatable real product by that literal name, so this build asks
// the user to name their own chosen tool per category rather than
// repeating an unverified name as if it were settled.
// ---------------------------------------------------------------

const STACK_CATEGORIES = ["compute", "email", "phone", "connectors"];

function defaultChecklist() {
  const stack = {};
  STACK_CATEGORIES.forEach((cat) => {
    stack[cat] = { tool: "", docsRead: false };
  });
  return {
    researchDone: false,
    researchNotes: "",
    designDone: false,
    designTool: "",
    stack,
    buildDone: false,
  };
}

function checklistProgress(checklist) {
  const stackDone = STACK_CATEGORIES.filter(
    (cat) => checklist.stack[cat].tool.trim() !== "" && checklist.stack[cat].docsRead
  ).length;
  const steps = [checklist.researchDone, checklist.designDone, stackDone === STACK_CATEGORIES.length, checklist.buildDone];
  const completedSteps = steps.filter(Boolean).length;
  return {
    stackDone,
    stackTotal: STACK_CATEGORIES.length,
    completedSteps,
    totalSteps: steps.length,
    isComplete: completedSteps === steps.length,
  };
}

// ---------------------------------------------------------------
// Persistence -- localStorage only, no network call (same
// zero-dependency, no-API-key convention as this project's other
// standalone builds: Recovery Desk, Creator Empire AI's Standalone
// Edition).
// ---------------------------------------------------------------

function defaultState() {
  return {
    offer: {
      nicheBaseline: 200,
      multiplier: 10,
      upfrontRatio: Number(SOURCE_UPFRONT_TO_MONTHLY_RATIO.toFixed(4)),
      hoursPerMonth: DEFAULT_HOURS_PER_MONTH,
    },
    contacts: [],
    checklist: defaultChecklist(),
  };
}

function loadState(storage) {
  try {
    const raw = storage.getItem(STORAGE_KEY);
    if (!raw) return defaultState();
    const parsed = JSON.parse(raw);
    // Merge with defaults so a future field addition doesn't break an
    // older saved profile.
    const base = defaultState();
    return {
      offer: Object.assign({}, base.offer, parsed.offer || {}),
      contacts: Array.isArray(parsed.contacts) ? parsed.contacts : [],
      checklist: Object.assign({}, base.checklist, parsed.checklist || {}, {
        stack: Object.assign({}, base.checklist.stack, (parsed.checklist || {}).stack || {}),
      }),
    };
  } catch (e) {
    return defaultState();
  }
}

function saveState(storage, state) {
  storage.setItem(STORAGE_KEY, JSON.stringify(state));
}

const SCBB_EXPORTS = {
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
};

// Node (tests) vs. browser export.
if (typeof module !== "undefined" && module.exports) {
  module.exports = SCBB_EXPORTS;
}
if (typeof window !== "undefined") {
  window.SCBB = SCBB_EXPORTS;
}
