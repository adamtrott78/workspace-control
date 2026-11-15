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


class OperatorActionState(StrEnum):
    QUEUED = "QUEUED"
    CLAIMED_LOCAL = "CLAIMED_LOCAL"
    LOCAL_PREPARED = "LOCAL_PREPARED"
    AWAITING_DURABLE_ACK = "AWAITING_DURABLE_ACK"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    COMPLETED = "COMPLETED"
    FAILED_LOCAL = "FAILED_LOCAL"
    CLAIM_EXPIRED = "CLAIM_EXPIRED"
    BLOCKED = "BLOCKED"
    STALE = "STALE"
    SUPERSEDED = "SUPERSEDED"


class OperatorActionType(StrEnum):
    SERVICE_EXISTING = "SERVICE_EXISTING"
    CREATE_AND_SERVICE = "CREATE_AND_SERVICE"
    RESTORE_AND_SERVICE = "RESTORE_AND_SERVICE"
    DISCARD_SESSION = "DISCARD_SESSION"
    RETIRE_SESSION = "RETIRE_SESSION"
    OPEN_JUDGMENT_GATE = "OPEN_JUDGMENT_GATE"
    OPEN_RECOVERY = "OPEN_RECOVERY"


class OperatorHumanRequirement(StrEnum):
    NONE = "NONE"
    PASTE_AND_SUBMIT = "PASTE_AND_SUBMIT"
    SUBSTANTIVE_DECISION = "SUBSTANTIVE_DECISION"
    RECOVERY_INTERACTION = "RECOVERY_INTERACTION"


class OperatorAckMode(StrEnum):
    NONE = "NONE"
    DURABLE_EVENT = "DURABLE_EVENT"
    DURABLE_STATE_PREDICATE = "DURABLE_STATE_PREDICATE"


class OperatorPostLocalSuccess(StrEnum):
    AWAIT_DURABLE_ACK = "AWAIT_DURABLE_ACK"
    COMPLETE_AND_REQUERY = "COMPLETE_AND_REQUERY"
    STOP = "STOP"


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


@dataclass(frozen=True)
class OperatorActionClaim:
    claim_id: str
    helper_instance_id: str
    claimed_at: str
    expires_at: str


@dataclass
class OperatorAction:
    """Durable control-plane action; packet text is deliberately absent."""

    action_id: str
    generation: int
    action_type: OperatorActionType
    status: OperatorActionState
    priority_rank: int
    queue_sequence: int
    created_at: str
    task_id: str
    reasoning_process_id: str | None
    process_generation: int | None
    worker_slot_id: str | None
    session_generation: int | None
    executor_id: str | None
    payload_ref: str | None
    payload_sha256: str | None
    human_requirement: OperatorHumanRequirement
    ack_mode: OperatorAckMode
    post_local_success: OperatorPostLocalSuccess
    not_before: str | None = None
    stale_after: str | None = None
    supersedes_action_id: str | None = None
    superseded_by_action_id: str | None = None
    claim: OperatorActionClaim | None = None
    local_prepared_at: str | None = None
    durable_ack_id: str | None = None
    failure_code: str | None = None
    failure_message: str | None = None
    completed_at: str | None = None


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
    operator_actions: dict[str, OperatorAction] = field(default_factory=dict)
    event_seq: int = 0
    graph_history: list[dict[str, Any]] = field(default_factory=list)
