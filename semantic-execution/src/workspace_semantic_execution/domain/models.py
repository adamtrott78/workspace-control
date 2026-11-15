"""Infrastructure-free domain records for Workspace Semantic Execution."""
from __future__ import annotations

from dataclasses import dataclass, field
from .._compat import StrEnum
from typing import Any


class ProcessState(StrEnum):
    READY = "READY"
    CLAIMED = "CLAIMED"
    RUNNING = "RUNNING"
    WAITING_EXTERNAL = "WAITING_EXTERNAL"
    WAITING_DEPENDENCIES = "WAITING_DEPENDENCIES"
    READY_TO_RESUME = "READY_TO_RESUME"
    TERMINAL_CANDIDATE = "TERMINAL_CANDIDATE"
    VALIDATING = "VALIDATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    AUTHORITY_BLOCKED = "AUTHORITY_BLOCKED"


class WorkDisposition(StrEnum):
    """Durable reasoning classification, distinct from process lifecycle."""

    UNCLASSIFIED = "UNCLASSIFIED"
    EXECUTABLE = "EXECUTABLE"
    TOO_LARGE = "TOO_LARGE"
    INTRINSICALLY_DIFFICULT = "INTRINSICALLY_DIFFICULT"


class ExecutorSessionState(StrEnum):
    READY = "READY"
    BOUND = "BOUND"
    NEEDS_REPLACEMENT = "NEEDS_REPLACEMENT"
    RETIRED = "RETIRED"


class AuthorityOutcome(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    ABSTAIN = "ABSTAIN"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class WorkContract:
    """Non-droppable work obligations carried through decomposition."""

    objective: str
    mandatory_constraints: tuple[str, ...] = ()
    provenance_refs: tuple[str, ...] = ()
    authority_refs: tuple[str, ...] = ()
    validator_contracts: tuple[str, ...] = ()
    output_schema_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class TransitionRecord:
    seq: int
    event: str
    state: ProcessState
    generation: int
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EffectReceipt:
    action_id: str
    idempotency_key: str
    target_ref: str
    effect_hash: str
    executor_id: str
    generation: int
    observed_at: str


@dataclass(frozen=True)
class ValidationResult:
    validator_id: str
    passed: bool
    evidence_ref: str
    observed_at: str


@dataclass(frozen=True)
class CandidateAction:
    action_id: str
    process_id: str
    process_generation: int
    target_ref: str
    executor_type: str
    idempotency_key: str
    preconditions: tuple[str, ...]
    expected_effect: str
    postcondition_validator: str
    authorization_state: str = "UNDECIDED"


@dataclass(frozen=True)
class AuthorityDecision:
    decision_id: str
    outcome: AuthorityOutcome
    action_id: str
    process_id: str
    process_generation: int
    target_ref: str
    authority_scope_ref: str | None


@dataclass(frozen=True)
class ActionSpec:
    action_id: str
    process_id: str
    process_generation: int
    target_ref: str
    executor_type: str
    authority_decision_id: str
    authority_scope_ref: str
    idempotency_key: str
    preconditions: tuple[str, ...]
    expected_effect: str
    postcondition_validator: str


@dataclass
class ExecutorSession:
    """Durable session-slot metadata; never an authority record."""

    slot_id: str
    executor_id: str
    session_generation: int = 0
    session_id: str | None = None
    state: ExecutorSessionState = ExecutorSessionState.READY
    bound_process_id: str | None = None
    bound_process_generation: int | None = None
    bound_packet_sha256: str | None = None
    last_ack_id: str | None = None
    last_ack_process_id: str | None = None
    last_ack_process_generation: int | None = None
    retirement_reason: str | None = None


@dataclass
class ReasoningProcess:
    process_id: str
    state: ProcessState = ProcessState.READY
    generation: int = 0
    worker_id: str | None = None
    lease_id: str | None = None
    dependencies: tuple[str, ...] = ()
    children: tuple[str, ...] = ()
    wait_key: str | None = None
    effect_receipts: dict[str, EffectReceipt] = field(default_factory=dict)
    validations: list[ValidationResult] = field(default_factory=list)
    reasoning_quanta: int = 0
    repair_required: bool = False
    history: list[TransitionRecord] = field(default_factory=list)
    parent_process_id: str | None = None
    work_contract: WorkContract | None = None
    disposition: WorkDisposition = WorkDisposition.UNCLASSIFIED
    disposition_reason: str | None = None


@dataclass
class WorkGraph:
    processes: dict[str, ReasoningProcess]
    executor_sessions: dict[str, ExecutorSession] = field(default_factory=dict)
    event_seq: int = 0
    graph_history: list[dict[str, Any]] = field(default_factory=list)
