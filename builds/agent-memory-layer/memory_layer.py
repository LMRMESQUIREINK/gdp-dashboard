"""agent-memory-layer: a real, dependency-free implementation of the one
part of a pasted "Memory Engineering for AI Agents" article (DhanushKumar,
Medium) that turned out to be concrete, well-specified, and independently
verifiable -- not the article's own 30-plus-category taxonomy, which is
prose classification, nothing to execute or test.

Built from, and tested against, two things web-verified this round
(/notes/memory-engineering-analysis.md):

1. The retrieval scoring formula the article attributes to "Generative
   Agents-style memory scoring" -- Park et al. 2023, "Generative Agents:
   Interactive Simulacra of Human Behavior" (arXiv:2304.03442). Confirmed:
   the real paper scores a memory as an equally-weighted sum of recency,
   importance, and relevance. `score_generative_agents()` below is that
   real formula. The exact recency decay constant (commonly cited
   elsewhere as 0.995/hour) was NOT independently confirmed from the
   primary paper this round -- so it is a caller-supplied parameter here,
   never a hardcoded "fact."

2. The article's own proposed lifecycle state machine (RAW -> ACTIVE ->
   CONFIRMED -> SUPERSEDED -> STALE -> ARCHIVED -> FORGOTTEN) and its
   supersession-based conflict handling for preference memories (its own
   worked example: a user's Flask preference is superseded by a later
   FastAPI preference, not merged or silently overwritten). The article
   states this lifecycle in prose only, with no validation that a
   transition is actually legal -- `transition()` below is that missing
   validation, the generalizable gap this build closes.

The article's own extended scoring formula (relevance + recency +
importance + confidence + authority + task_alignment - contradiction_penalty
- staleness_penalty) is kept as a clearly separate function,
`score_extended()`, since it is the article's own proposal, not something
sourced to Generative Agents or any other cited work -- conflating the two
would misattribute an invented formula to a real paper.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class MemoryStatus(str, Enum):
    RAW = "RAW"
    ACTIVE = "ACTIVE"
    CONFIRMED = "CONFIRMED"
    SUPERSEDED = "SUPERSEDED"
    STALE = "STALE"
    ARCHIVED = "ARCHIVED"
    FORGOTTEN = "FORGOTTEN"


# The article states this sequence in prose ("RAW -> ACTIVE -> CONFIRMED ->
# SUPERSEDED -> STALE -> ARCHIVED -> FORGOTTEN") without saying whether it
# is a strict chain or a DAG. Read literally as a chain, a record could
# only ever be superseded after first being confirmed, which doesn't match
# its own real-world example (a freshly-extracted, still-RAW preference
# can absolutely be contradicted by a newer one before anyone confirms it).
# This table is therefore a considered DAG, not the article's literal
# chain: every non-terminal status can move directly to SUPERSEDED,
# STALE, ARCHIVED, or FORGOTTEN (a record can be invalidated, decay, be
# archived, or be forgotten from any live state), while ACTIVE/CONFIRMED
# are the only two states promotion can land on, and the four end states
# cannot be left once entered. This choice is stated here, not silently
# baked in -- see deeper-02 in the analysis note.
_ALLOWED_TRANSITIONS: dict[MemoryStatus, frozenset[MemoryStatus]] = {
    MemoryStatus.RAW: frozenset({
        MemoryStatus.ACTIVE, MemoryStatus.SUPERSEDED, MemoryStatus.STALE,
        MemoryStatus.ARCHIVED, MemoryStatus.FORGOTTEN,
    }),
    MemoryStatus.ACTIVE: frozenset({
        MemoryStatus.CONFIRMED, MemoryStatus.SUPERSEDED, MemoryStatus.STALE,
        MemoryStatus.ARCHIVED, MemoryStatus.FORGOTTEN,
    }),
    MemoryStatus.CONFIRMED: frozenset({
        MemoryStatus.SUPERSEDED, MemoryStatus.STALE,
        MemoryStatus.ARCHIVED, MemoryStatus.FORGOTTEN,
    }),
    MemoryStatus.SUPERSEDED: frozenset({MemoryStatus.ARCHIVED, MemoryStatus.FORGOTTEN}),
    MemoryStatus.STALE: frozenset({MemoryStatus.ARCHIVED, MemoryStatus.FORGOTTEN}),
    MemoryStatus.ARCHIVED: frozenset(),
    MemoryStatus.FORGOTTEN: frozenset(),
}

LIVE_STATUSES = frozenset({MemoryStatus.RAW, MemoryStatus.ACTIVE, MemoryStatus.CONFIRMED})


class IllegalTransitionError(ValueError):
    pass


@dataclass
class MemoryRecord:
    """Matches the article's own proposed JSON schema field-for-field
    (memory_id, type, subject_id, content, valid_from, valid_until,
    confidence, importance, authority, status, supersedes, scope), kept
    as a typed record instead of a bare dict so a caller can't construct
    one with an out-of-range confidence/importance or an invalid status
    string without an explicit error.
    """
    memory_id: str
    type: str  # e.g. "semantic.preference", matching the article's dotted convention
    subject_id: str
    content: str
    created_at: float  # unix seconds
    valid_from: float
    valid_until: Optional[float] = None
    confidence: float = 1.0
    importance: float = 5.0  # article's own worked example uses a 0-10 scale
    authority: str = "system_inferred"
    status: MemoryStatus = MemoryStatus.RAW
    supersedes: Optional[str] = None
    scope: str = "user"
    last_accessed_at: Optional[float] = None
    embedding: Optional[tuple[float, ...]] = None

    def __post_init__(self) -> None:
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"confidence must be in [0, 1], got {self.confidence}")
        if not (0.0 <= self.importance <= 10.0):
            raise ValueError(f"importance must be in [0, 10] (the article's own scale), got {self.importance}")
        if isinstance(self.status, str):
            self.status = MemoryStatus(self.status)


def transition(record: MemoryRecord, new_status: MemoryStatus) -> MemoryRecord:
    """Move `record` to `new_status`, raising IllegalTransitionError if the
    move isn't in the allowed table above. Returns the same record,
    mutated, for chaining -- this is deliberately in-place, not a copy,
    since callers typically hold the record in a store they want updated.
    """
    if isinstance(new_status, str):
        new_status = MemoryStatus(new_status)
    allowed = _ALLOWED_TRANSITIONS[record.status]
    if new_status not in allowed:
        raise IllegalTransitionError(
            f"{record.memory_id}: cannot move {record.status.value} -> {new_status.value} "
            f"(allowed from {record.status.value}: {sorted(s.value for s in allowed) or 'none, terminal state'})"
        )
    record.status = new_status
    return record


def supersede(old: MemoryRecord, new: MemoryRecord, *, now: float) -> MemoryRecord:
    """The article's own worked conflict-handling example, made real: a
    new memory about the same subject supersedes an old one rather than
    merging or silently overwriting it. Marks `old` SUPERSEDED, closes its
    validity window at `now`, and links `new.supersedes = old.memory_id`.

    Refuses to supersede a memory about a DIFFERENT subject -- the article
    never states this guard, but without it `supersede()` could silently
    overwrite the wrong person's preference, which is a materially worse
    failure than merely missing the feature.
    """
    if old.subject_id != new.subject_id:
        raise ValueError(
            f"refusing to supersede {old.memory_id} (subject={old.subject_id!r}) "
            f"with {new.memory_id} (subject={new.subject_id!r}): different subjects"
        )
    transition(old, MemoryStatus.SUPERSEDED)
    old.valid_until = now
    new.supersedes = old.memory_id
    return new


def _recency_score(record: MemoryRecord, now: float, decay_per_hour: float) -> float:
    if record.last_accessed_at is None:
        hours_elapsed = (now - record.created_at) / 3600.0
    else:
        hours_elapsed = (now - record.last_accessed_at) / 3600.0
    hours_elapsed = max(hours_elapsed, 0.0)
    return decay_per_hour ** hours_elapsed


def _cosine_similarity(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    if len(a) != len(b):
        raise ValueError(f"embedding dimension mismatch: {len(a)} vs {len(b)}")
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def score_generative_agents(
    record: MemoryRecord,
    query_embedding: tuple[float, ...],
    *,
    now: float,
    decay_per_hour: float = 0.995,
) -> float:
    """The real Generative Agents (Park et al. 2023) retrieval score:
    an EQUALLY-WEIGHTED sum of recency, importance, and relevance, each
    normalized to [0, 1] before summing (the paper's own min-max
    normalization step, applied here per-call since a single memory has
    no "other candidates" to normalize against in isolation -- a caller
    scoring a whole candidate set should min-max normalize the three raw
    components across that set, not rely on this function's own [0,1]-ish
    ranges holding up as a fair comparison on their own).

    `decay_per_hour` defaults to 0.995, the value commonly cited in
    secondary sources -- NOT independently confirmed against the primary
    paper in this round (see the build's README) -- so it is always an
    explicit, overridable parameter here, never silently assumed.
    """
    recency = _recency_score(record, now, decay_per_hour)
    importance = record.importance / 10.0
    if record.embedding:
        cosine = _cosine_similarity(record.embedding, query_embedding)
        relevance = (cosine + 1.0) / 2.0  # cosine in [-1,1] -> [0,1], only for a real cosine value
    else:
        relevance = 0.0  # no embedding at all: zero relevance, never renormalized
    return recency + importance + relevance


def score_extended(
    record: MemoryRecord,
    query_embedding: tuple[float, ...],
    *,
    now: float,
    decay_per_hour: float = 0.995,
    task_alignment: float = 0.0,
    contradiction_penalty: float = 0.0,
    staleness_penalty: float = 0.0,
) -> float:
    """The ARTICLE's OWN proposed extension (relevance + recency +
    importance + confidence + authority + task_alignment -
    contradiction_penalty - staleness_penalty) -- not Generative Agents',
    kept as a separate function specifically so a caller (or a future
    maintainer of this module) can never accidentally cite this output as
    "the real Park et al. formula." `authority` is mapped to a fixed
    0-1 scale since the article never specifies one; this build's choice
    (user_explicit=1.0, system_inferred=0.5, unknown=0.25) is stated here
    as this build's own convention, not the article's.
    """
    base = score_generative_agents(record, query_embedding, now=now, decay_per_hour=decay_per_hour)
    authority_score = {"user_explicit": 1.0, "system_inferred": 0.5}.get(record.authority, 0.25)
    return (
        base
        + record.confidence
        + authority_score
        + task_alignment
        - contradiction_penalty
        - staleness_penalty
    )


@dataclass
class MemoryStore:
    """A minimal in-memory store demonstrating the pieces above wired
    together: add, supersede, and query-live (only RAW/ACTIVE/CONFIRMED
    records, matching the article's own retrieval pipeline's implicit
    "filter_invalid_temporal_facts" step -- a SUPERSEDED, STALE, ARCHIVED
    or FORGOTTEN memory should never be the thing a live query surfaces).
    """
    records: dict[str, MemoryRecord] = field(default_factory=dict)

    def add(self, record: MemoryRecord) -> None:
        if record.memory_id in self.records:
            raise ValueError(f"memory_id {record.memory_id!r} already exists")
        self.records[record.memory_id] = record

    def get(self, memory_id: str) -> MemoryRecord:
        return self.records[memory_id]

    def live_for_subject(self, subject_id: str) -> list[MemoryRecord]:
        return [
            r for r in self.records.values()
            if r.subject_id == subject_id and r.status in LIVE_STATUSES
        ]

    def supersede(self, old_id: str, new: MemoryRecord, *, now: float) -> None:
        old = self.records[old_id]
        supersede(old, new, now=now)
        self.add(new)
