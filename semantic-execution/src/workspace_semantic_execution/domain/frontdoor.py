"""Human-facing Instant front-door task intake contracts."""
from __future__ import annotations

from dataclasses import dataclass
from .._compat import StrEnum


class FrontDoorIntent(StrEnum):
    SUBMIT_TASK = "SUBMIT_TASK"
    RESUME_TASK = "RESUME_TASK"
    QUERY_STATUS = "QUERY_STATUS"
    PROVIDE_DECISION = "PROVIDE_DECISION"
    CANCEL_REQUEST = "CANCEL_REQUEST"


@dataclass(frozen=True)
class FrontDoorMessage:
    message_id: str
    conversation_id: str
    text: str
    submitted_at: str
    intent: FrontDoorIntent = FrontDoorIntent.SUBMIT_TASK

    def __post_init__(self) -> None:
        if not self.message_id or not self.conversation_id or not self.text.strip():
            raise ValueError("frontdoor_message_required_fields_missing")


@dataclass(frozen=True)
class TaskIntakeCandidate:
    """Non-authoritative proposal emitted from the user-facing chat."""

    intake_id: str
    message_id: str
    conversation_id: str
    objective: str
    source_ref: str
    requested_by: str
    authorization_state: str = "UNDECIDED"

    def __post_init__(self) -> None:
        required = (
            self.intake_id,
            self.message_id,
            self.conversation_id,
            self.objective,
            self.source_ref,
            self.requested_by,
        )
        if not all(required):
            raise ValueError("task_intake_candidate_required_fields_missing")
        if self.authorization_state != "UNDECIDED":
            raise ValueError("frontdoor_cannot_mint_execution_authority")


@dataclass(frozen=True)
class TaskControlCandidate:
    """Non-authoritative request against an existing durable task."""

    control_id: str
    message_id: str
    conversation_id: str
    intent: FrontDoorIntent
    target_task_id: str
    text: str
    source_ref: str
    requested_by: str
    authorization_state: str = "UNDECIDED"

    def __post_init__(self) -> None:
        required = (
            self.control_id,
            self.message_id,
            self.conversation_id,
            self.target_task_id,
            self.text.strip(),
            self.source_ref,
            self.requested_by,
        )
        if not all(required):
            raise ValueError("task_control_candidate_required_fields_missing")
        if self.intent not in {
            FrontDoorIntent.RESUME_TASK,
            FrontDoorIntent.PROVIDE_DECISION,
            FrontDoorIntent.CANCEL_REQUEST,
        }:
            raise ValueError("task_control_candidate_intent_invalid")
        if self.authorization_state != "UNDECIDED":
            raise ValueError("frontdoor_cannot_mint_execution_authority")


@dataclass(frozen=True)
class TaskStatusView:
    """Compact deterministic user-facing projection of a task capsule."""

    task_id: str
    title: str
    status: str
    current_stage: str | None
    next_safe_action: str
    blockers: tuple[str, ...]
    remaining_work_count: int
    latest_checkpoint_id: str | None = None

    def __post_init__(self) -> None:
        if (
            not self.task_id
            or not self.title
            or not self.status
            or not self.next_safe_action
            or self.remaining_work_count < 0
        ):
            raise ValueError("task_status_view_invalid")
