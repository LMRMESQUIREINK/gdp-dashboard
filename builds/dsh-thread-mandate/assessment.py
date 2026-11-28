"""assessment -- the model-ASSESSMENT layer's typed interface, read
directly from the real repo's own two-layer Eval concept
(`deepseek-ai/dsh-superagent-prototype`'s `docs/001-domain.md`): "Eval --
The judgement on a batch of Triggers, in two layers: gate and
assessment... Gate -- The deterministic first layer of Eval: who may
originate work, and with what strength... Assessment -- The model's
judgement during Eval."

`eval_gate.py`'s `run_gate_eval()` only ever implements the GATE layer --
deterministic, no model call. This module defines the typed CONTRACT the
assessment layer would plug into, without implementing an actual model
call: no live model exists in this sandbox, the same standing restriction
as every other build here needing one.

The real gap this closes: before this module, `run_gate_eval()` returned
`Decision.IGNORE` the instant no gate rule matched any Trigger in the
batch -- conflating two genuinely different situations the real Strength
group (explicit/inferred) implies exist. Only the assessment layer can
ever grant INFERRED strength (a gate rule only ever grants EXPLICIT), so
"no deterministic rule exists" was never itself a reason to stop looking
-- it's the reason to ask the assessment layer, if one exists. IGNORE is
the real Eval's own decision only once BOTH layers have had a say: no
gate rule, and either no assessor is configured at all, or a real
assessor was consulted and it also declined. `EvalResult.reason` (added
alongside this module) now distinguishes those two cases in plain text
instead of collapsing them into the same bare IGNORE.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from thread_mandate import Decision, EvalBatch, Policy


class Strength(Enum):
    EXPLICIT = "explicit"
    INFERRED = "inferred"


@dataclass(frozen=True)
class AssessmentRequest:
    """What the assessment layer is handed once the gate layer has
    already found no deterministic rule. Real repo: Eval's real input is
    "the Trigger batch, a Thread snapshot, every Ticket on the Thread
    including ended ones, and the current Policy" -- narrowed here to
    what a model-judgement call actually needs, plus which scopes the
    gate layer already looked at and declined, so an assessor doesn't
    have to re-derive that from the Policy itself."""
    batch: EvalBatch
    policy: Policy
    gate_declined_scopes: tuple[str, ...]


@dataclass(frozen=True)
class AssessmentResult:
    """The model's judgement. Only ever meaningful as a source of
    INFERRED strength -- an assessor that wants to grant EXPLICIT
    strength belongs in the gate layer (a named GateRule), not here.
    `scope` is required for an ACCEPT or STOP decision and ignored
    otherwise; `reason` is always a plain-text explanation, never empty,
    so a declined assessment still says why.
    """
    decision: Decision
    scope: Optional[str] = None
    reason: str = ""


# A real assessor is any callable matching this shape. No implementation
# of one lives in this sandbox -- it would need a live model call, the
# same standing restriction as every other build here needing one. A
# test-only scripted stand-in (same convention as this project's other
# mocked-model tests) is what `test_assessment.py` actually exercises.
Assessor = Callable[[AssessmentRequest], AssessmentResult]
