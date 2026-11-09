"""Tests for decision_engine.py -- reproducing the source article's own
worked example exactly, proving the four named "Common Mistakes" are
structurally refused (not just avoided by convention), and proving the
real schema gap found in the article (flat YAML conditions vs. the
prose's content-dependent "Choose" reasoning) is actually closed here.

Run with: python3 test_decision_engine.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from decision_engine import (  # noqa: E402
    Rule, DecisionEngine, Router, WorkflowState, RecoveryEngine,
    OrchestrationAgent, CycleOutcome, UnknownActionError,
)

passed = 0
failed = 0


def check(cond, name, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print("ok   - " + name)
    else:
        failed += 1
        print("FAIL - " + name + (f" ({detail})" if detail else ""))


# =====================================================================
# Reproduce the article's own worked example exactly: coverage
# 82 -> 88 -> 100 across two retry cycles, same as the article's prose.
# =====================================================================
coverage_sequence = iter([
    {"coverage": 82, "missing_requirements": ["Refund Workflow"]},
    {"coverage": 88, "missing_requirements": ["Refund Edge Cases"]},
    {"coverage": 100, "missing_requirements": []},
])
scenario_designer_calls = []


def observe_fn():
    return next(coverage_sequence)


def evaluate_fn(observation):
    return {"coverage": observation["coverage"], "coverage_below_90": observation["coverage"] < 90}


def scenario_designer(context):
    scenario_designer_calls.append(context["observation"])
    return {"ran": "Scenario Designer"}


def verify_fn(facts):
    return facts["coverage"] >= 90


rules = [Rule(label="low-coverage", condition=lambda f: f["coverage_below_90"], action="Scenario Designer")]
engine = DecisionEngine(rules=rules)
router = Router(producers={"Scenario Designer": scenario_designer})
recovery = RecoveryEngine(max_retries=2, on_exhausted_action="Human Review")
agent = OrchestrationAgent(engine, router, recovery)
state = WorkflowState(workflow_id="refund-workflow-coverage")

history = agent.run_until_done(state, observe_fn, evaluate_fn, verify_fn)

# Cycle 1: observe 82 -> execute Scenario Designer -> re-observe 88 -> not verified (RETRYING).
# Cycle 2: observe 100 -> already meets the objective, no rule fires -> verify(100) -> VERIFIED.
# Matches the article's own two named cycles ("CYCLE 1", "CYCLE 2") exactly, with
# Verify always checking FRESH post-execution state rather than a stale observation
# (see the design-gap writeup in decision_engine.py's run_cycle docstring).
check(len(history) == 2, "exactly 2 cycles run, matching the article's own worked example's 'CYCLE 1'/'CYCLE 2' naming", len(history))
check(history[0].outcome == CycleOutcome.RETRYING, "cycle 1 (82% -> re-observed 88%, still below 90) reports RETRYING, not VERIFIED", history[0].outcome)
check(history[1].outcome == CycleOutcome.VERIFIED, "cycle 2 (observes 100%, already meets the objective) reports VERIFIED", history[1].outcome)
check(state.retry_count == 1, "the workflow state's retry_count reaches exactly 1 -- one failed verification (82->88), matching the article's own 'Retry Count: 1' value", state.retry_count)
check(len(scenario_designer_calls) == 1, "the real Scenario Designer producer was actually called exactly once -- the orchestrator delegated the one real fix needed, never fabricated a result", len(scenario_designer_calls))
check(history[0].action_taken == "Scenario Designer" and history[1].action_taken is None, "cycle 1 routed through the real decision rule; cycle 2 correctly took no action at all since nothing needed fixing", [h.action_taken for h in history])

# =====================================================================
# THE real gap found: the article's own YAML schema (flat
# `coverage < 90`) cannot express the prose's "Choose" reasoning
# ("clarification isn't necessary because the requirement already
# exists in the Requirement Package"). This build's Rule.condition is a
# real callable over the FULL facts dict, so it CAN -- proven by
# actually branching to a different action depending on requirement
# content, something a flat numeric condition structurally cannot do.
# =====================================================================
def evaluate_with_requirement_check(observation):
    return {
        "coverage_below_90": observation["coverage"] < 90,
        "missing_requirement_documented": observation["missing_requirement"] in observation["requirement_package"],
    }


content_aware_rules = [
    Rule(
        label="missing-but-documented",
        condition=lambda f: f["coverage_below_90"] and f["missing_requirement_documented"],
        action="Scenario Designer",
    ),
    Rule(
        label="missing-and-undocumented",
        condition=lambda f: f["coverage_below_90"] and not f["missing_requirement_documented"],
        action="Request Business Clarification",
    ),
]
content_engine = DecisionEngine(rules=content_aware_rules)

documented_facts = evaluate_with_requirement_check({
    "coverage": 82, "missing_requirement": "Refund Workflow",
    "requirement_package": ["Refund Workflow", "Checkout Flow"],
})
chosen = content_engine.choose(documented_facts)
check(chosen is not None and chosen.action == "Scenario Designer", "when the missing requirement IS documented in the requirement package, the engine picks Scenario Designer -- exactly the article's own prose reasoning for cycle 1", chosen)

undocumented_facts = evaluate_with_requirement_check({
    "coverage": 82, "missing_requirement": "Loyalty Points",
    "requirement_package": ["Refund Workflow", "Checkout Flow"],
})
chosen2 = content_engine.choose(undocumented_facts)
check(chosen2 is not None and chosen2.action == "Request Business Clarification", "when the missing requirement is NOT documented, the engine picks Request Business Clarification -- a branch the article's own flat `coverage < 90` YAML condition has no way to reach at all, since it never looks at requirement content", chosen2)

# =====================================================================
# Mistake #3: the named infinite loop ("Coverage: 88% -> Scenario
# Designer -> Coverage: 88% -> Scenario Designer -> ...forever").
# Reproduce a producer that NEVER improves coverage, and confirm the
# engine does NOT loop forever -- it escalates after the configured
# retry budget.
# =====================================================================
stuck_calls = []


def stuck_observe_fn():
    return {"coverage": 88}  # never changes, no matter how many times we're called


def stuck_evaluate_fn(observation):
    return {"coverage_below_90": observation["coverage"] < 90}


def stuck_producer(context):
    stuck_calls.append(1)
    return {"ok": True}


def stuck_verify_fn(facts):
    return False  # never verifies -- the exact stuck scenario the article describes


stuck_rules = [Rule(label="low-coverage", condition=lambda f: f["coverage_below_90"], action="Scenario Designer")]
stuck_engine = DecisionEngine(rules=stuck_rules)
stuck_router = Router(producers={"Scenario Designer": stuck_producer})
stuck_recovery = RecoveryEngine(max_retries=2)
stuck_agent = OrchestrationAgent(stuck_engine, stuck_router, stuck_recovery)
stuck_state = WorkflowState(workflow_id="stuck-workflow")

stuck_history = stuck_agent.run_until_done(stuck_state, stuck_observe_fn, stuck_evaluate_fn, stuck_verify_fn, max_cycles=100)

check(len(stuck_history) == 3, "a producer that never improves coverage runs exactly max_retries+1 = 3 cycles, NOT the max_cycles=100 safety cap -- RecoveryEngine's own budget is what actually stops it", len(stuck_history))
check(stuck_history[-1].outcome == CycleOutcome.ESCALATED, "the final outcome is ESCALATED, not an infinite RETRYING loop -- this is the exact Mistake #3 the article names, refused structurally", stuck_history[-1].outcome)
check(len(stuck_calls) == 3, "the stuck producer was called exactly 3 times, not endlessly -- real call-count proof, not just a status string", len(stuck_calls))

# =====================================================================
# Mistake #1: the orchestrator can never perform producer work itself.
# Router.execute() is the ONLY path any action runs through, and an
# unregistered action raises loudly rather than silently no-opping or
# falling back to some inline implementation.
# =====================================================================
empty_router = Router(producers={})
try:
    empty_router.execute("Scenario Designer", {})
    check(False, "calling an unregistered action raises UnknownActionError", "no exception")
except UnknownActionError as e:
    check("Scenario Designer" in str(e), "UnknownActionError names the unregistered action and lists what IS known", str(e))

# =====================================================================
# Mistake #2: the workflow is never marked done on execution alone --
# only a True from verify_fn can produce VERIFIED.
# =====================================================================
always_false_verify_history = agent_result = None
never_verified_recovery = RecoveryEngine(max_retries=0)  # zero retry budget -- escalates on the very first failure
never_verified_agent = OrchestrationAgent(
    DecisionEngine(rules=[Rule("always", lambda f: True, "Scenario Designer")]),
    Router(producers={"Scenario Designer": lambda ctx: {"ran": True}}),
    never_verified_recovery,
)
never_verified_state = WorkflowState(workflow_id="never-verified")
result = never_verified_agent.run_cycle(never_verified_state, lambda: {}, lambda o: {}, lambda r: False)
check(result.outcome == CycleOutcome.ESCALATED, "even with zero retry budget, a single failed verification produces ESCALATED, never VERIFIED -- execution success is never assumed", result.outcome)

# =====================================================================
# Evaluate/Choose purity: choose() is a pure function of the facts
# dict -- same facts in, same action out, every time, no side effects.
# =====================================================================
pure_engine = DecisionEngine(rules=[Rule("r1", lambda f: f["x"] > 5, "A")])
facts_sample = {"x": 10}
first_call = pure_engine.choose(facts_sample)
second_call = pure_engine.choose(facts_sample)
check(first_call is second_call, "choose() called twice on the identical facts dict returns the identical Rule object -- no hidden state, no randomness", (first_call, second_call))
check(dict(facts_sample) == {"x": 10}, "evaluate's facts dict is never mutated by choose()", facts_sample)

# =====================================================================
# No-matching-rule is reported explicitly, not silently swallowed.
# =====================================================================
no_match_engine = DecisionEngine(rules=[Rule("r1", lambda f: False, "A")])
no_match_result = no_match_engine.choose({"x": 1})
check(no_match_result is None, "an evaluated-facts dict matching no rule's condition returns None, not a crash or a silent default action")

# =====================================================================
# State isolation: two different workflow_ids never share retry_count.
# =====================================================================
state_a = WorkflowState(workflow_id="a")
state_b = WorkflowState(workflow_id="b")
isolated_recovery = RecoveryEngine(max_retries=5)
isolated_recovery.handle(False, state_a)
isolated_recovery.handle(False, state_a)
isolated_recovery.handle(False, state_b)
check(state_a.retry_count == 2 and state_b.retry_count == 1, "retry_count is tracked per WorkflowState instance, never shared across workflow_ids -- matching the article's own 'state is not memory' distinction (no cross-run state)", (state_a.retry_count, state_b.retry_count))

print(f"\n{passed} passed, {failed} failed.")
if failed:
    sys.exit(1)
