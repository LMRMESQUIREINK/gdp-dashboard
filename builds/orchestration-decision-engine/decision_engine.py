"""decision_engine.py -- a real, standalone implementation of the
Observe-Evaluate-Choose-Execute-Verify orchestration loop from "Building
Your First Orchestration Agent" (rajesh yemul, Medium, Part 18 of a
"Quality Engineering" tutorial series) -- not the article's own fictional
QE pipeline (Requirement Analyzer/Scenario Designer/Playwright Test
Generator/etc.), which is just that article's worked-example flavor, but
the generalizable orchestration mechanism underneath it: a pluggable
multi-producer router driven by declarative decision rules, with
retry-bounded recovery and escalation.

See /notes/orchestration-agent-loop-analysis.md for the full read of the
source article, including the real gap this build closes: the article's
own YAML "Agent Configuration" example uses FLAT boolean conditions
(`coverage < 90`), but its own prose "Choose" stage reasoning explicitly
depends on CONTENT the flat schema can't express ("because the business
requirement already exists in the Requirement Package, clarification
isn't necessary" -- a judgment over the requirement package's actual
contents, not a number). This module's `Rule.condition` is a real
callable over the full evaluated-facts dict, not a flat field comparison
string, specifically so a rule CAN express that judgment -- closing the
gap between what the article's prose claims its configuration encodes
and what the configuration shape it actually shows can represent.

THE FOUR NAMED FAILURE MODES THIS MODULE IS BUILT TO REFUSE, STRUCTURALLY,
NOT JUST BY CONVENTION (the article's own "Common Mistakes" section):

1. The orchestrator performing producer work itself, instead of
   delegating. Enforced here: `Router.execute()` is the ONLY way any
   action ever runs, and it only ever calls a REGISTERED producer
   callable -- there is no fallback path, anywhere in this module, that
   does engineering/business work inline. Calling an unregistered action
   raises, loudly, rather than silently no-opping.
2. Assuming success without verification. Enforced here:
   `OrchestrationAgent.run_cycle()` never marks a workflow complete on
   execution alone -- completion is reachable ONLY through a `verify_fn`
   call returning True.
3. Ignoring workflow state, leading to the infinite retry loop the
   article's own worked example describes (Coverage 82% -> Scenario
   Designer -> 88% -> Scenario Designer -> 88% -> Scenario Designer ->
   ...forever). Enforced here: `WorkflowState.retry_count` is tracked
   and checked against `RecoveryEngine.max_retries` on every failed
   verification; once exhausted, the loop ends in ESCALATED, never a
   silent infinite re-route.
4. Embedding business logic inside orchestration. Enforced here: nothing
   in `DecisionEngine`, `Router`, or `RecoveryEngine` computes an
   engineering artifact -- they only read facts, pick an action name,
   and dispatch to caller-registered functions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional


class CycleOutcome(str, Enum):
    VERIFIED = "VERIFIED"        # workflow objective achieved
    RETRYING = "RETRYING"        # verification failed, budget remains -- another cycle will run
    ESCALATED = "ESCALATED"      # verification failed, retry budget exhausted


class UnknownActionError(KeyError):
    """Router.execute() was asked to run an action nothing registered."""


@dataclass
class Rule:
    """One decision rule: `condition` is a real predicate over the FULL
    evaluated-facts dict (not a flat `field < value` string) -- this is
    what lets a rule depend on artifact CONTENT, the real gap found in
    the source article's own flat YAML schema (see module docstring).
    """
    label: str
    condition: Callable[[dict], bool]
    action: str


@dataclass
class DecisionEngine:
    """The Decision Engine: Evaluate (facts in) -> Choose (action out),
    kept as ONE class but two distinct calls so a caller can verify they
    never happen in the same step -- `evaluate()` has no knowledge of
    what action might later be chosen, and `choose()` is a pure function
    of the facts dict it's given (same facts in -> same action out,
    every time, with no side effects -- proven directly in
    test_decision_engine.py).
    """
    rules: list[Rule] = field(default_factory=list)

    def choose(self, facts: dict) -> Optional[Rule]:
        """First-match wins, same ordering discipline as the source
        article's own decision_rules list. Returns None if nothing
        matches (CycleOutcome.NO_MATCHING_RULE)."""
        for rule in self.rules:
            if rule.condition(facts):
                return rule
        return None


@dataclass
class Router:
    """The Routing Engine. `producers` maps an action name to the ONE
    real callable that performs that action -- the sole path any
    engineering/business work can run through this module. There is no
    other way to "do the work" from inside OrchestrationAgent; that's
    what makes Mistake #1 (the agent doing producer work itself)
    structurally impossible here, not just discouraged by convention.
    """
    producers: dict[str, Callable[[dict], dict]] = field(default_factory=dict)

    def execute(self, action: str, context: dict) -> dict:
        if action not in self.producers:
            raise UnknownActionError(
                f"no producer registered for action {action!r} -- "
                f"known actions: {sorted(self.producers)}"
            )
        return self.producers[action](context)


@dataclass
class WorkflowState:
    """Per-workflow execution state -- NOT memory. Deliberately scoped
    to one workflow_id's own run: retry_count here never carries
    information across workflow_ids, matching the source article's own
    explicit "state is not memory" distinction (state = what's
    happening right now in THIS run; memory = learning across runs,
    out of scope here and in the article alike).
    """
    workflow_id: str
    retry_count: int = 0
    last_action: Optional[str] = None
    last_outcome: Optional[CycleOutcome] = None


@dataclass
class RecoveryEngine:
    """Bounded-retry recovery with escalation -- the piece that refuses
    the article's own named Mistake #3 (the infinite "Coverage: 88% ->
    Scenario Designer -> Coverage: 88% -> Scenario Designer -> ...
    forever" loop). `max_retries` caps how many times a failed
    verification may trigger another cycle before this engine reports
    ESCALATED instead of RETRYING.
    """
    max_retries: int
    on_exhausted_action: Optional[str] = None  # e.g. "Human Review" -- informational, caller decides what to do with it

    def handle(self, verified: bool, state: WorkflowState) -> CycleOutcome:
        if verified:
            return CycleOutcome.VERIFIED
        if state.retry_count >= self.max_retries:
            return CycleOutcome.ESCALATED
        state.retry_count += 1
        return CycleOutcome.RETRYING


@dataclass
class CycleResult:
    outcome: CycleOutcome
    action_taken: Optional[str]
    rule_label: Optional[str]
    producer_result: Optional[dict]
    facts: dict
    retry_count: int


class OrchestrationAgent:
    """Ties Observation (a caller-supplied observe_fn), the Decision
    Engine, the Routing Engine, and the Recovery Engine into the real
    Observe->Evaluate->Choose->Execute->Verify loop, run_cycle() per
    cycle and run_until_done() looping it -- matching the article's own
    "this is a loop, not a line" framing (Verify feeds back into the
    next Observe).
    """

    def __init__(self, decision_engine: DecisionEngine, router: Router, recovery_engine: RecoveryEngine):
        self.decision_engine = decision_engine
        self.router = router
        self.recovery_engine = recovery_engine

    def run_cycle(
        self,
        state: WorkflowState,
        observe_fn: Callable[[], dict],
        evaluate_fn: Callable[[dict], dict],
        verify_fn: Callable[[dict], bool],
    ) -> CycleResult:
        """One full Observe->Evaluate->Choose->Execute->Verify pass.
        Never marks the workflow done on its own -- only a True from
        verify_fn can do that (refuses Mistake #2: assuming success
        without verification).

        A REAL DESIGN GAP FOUND AND FIXED WHILE TESTING THIS BUILD'S OWN
        FIRST DRAFT (not the source article): the first version returned
        a bare NO_MATCHING_RULE whenever no decision rule fired and
        never checked verification at all -- but "no rule fired" is
        exactly what happens once the objective is ALREADY met (nothing
        needs fixing), which the source article's own worked example
        reaches on its final step (coverage=100, no rule like
        `coverage < 90` can match). Caught immediately by reproducing
        the article's own 82->88->100 sequence as a test: the final
        cycle reported NO_MATCHING_RULE instead of VERIFIED. Fixed by
        treating "no rule matched" as "nothing to execute" rather than
        an error -- verification still runs, against the CURRENT facts,
        exactly as it would after an execution that fixed everything.
        `verify_fn` therefore always takes the FACTS dict (not a raw
        producer result), and, when a rule DID fire, verification
        re-observes fresh state after execution -- Verify in the source
        article always means "check the state AFTER something ran," so
        a stale, pre-execution observation is never what gets verified.
        """
        observation = observe_fn()
        facts = evaluate_fn(observation)

        rule = self.decision_engine.choose(facts)
        producer_result = None
        if rule is not None:
            producer_result = self.router.execute(rule.action, {"observation": observation, "facts": facts})
            observation = observe_fn()  # re-observe post-execution state -- never verify stale, pre-execution facts
            facts = evaluate_fn(observation)

        verified = verify_fn(facts)
        outcome = self.recovery_engine.handle(verified, state)

        state.last_action = rule.action if rule is not None else None
        state.last_outcome = outcome
        return CycleResult(
            outcome,
            rule.action if rule is not None else None,
            rule.label if rule is not None else None,
            producer_result,
            facts,
            state.retry_count,
        )

    def run_until_done(
        self,
        state: WorkflowState,
        observe_fn: Callable[[], dict],
        evaluate_fn: Callable[[dict], dict],
        verify_fn: Callable[[dict], bool],
        max_cycles: int = 100,
    ) -> list[CycleResult]:
        """Repeats run_cycle() until VERIFIED or ESCALATED (or no rule
        matches). `max_cycles` is a hard safety cap independent of
        RecoveryEngine's own retry budget -- belt-and-braces against a
        misconfigured RecoveryEngine (e.g. max_retries set absurdly
        high), never relied on in the tests below as the real guard
        against Mistake #3; RecoveryEngine.max_retries is."""
        history: list[CycleResult] = []
        for _ in range(max_cycles):
            result = self.run_cycle(state, observe_fn, evaluate_fn, verify_fn)
            history.append(result)
            if result.outcome in (CycleOutcome.VERIFIED, CycleOutcome.ESCALATED):
                return history
        return history
