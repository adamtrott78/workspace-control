"""Human-facing Instant front-door task intake contracts."""
from __future__ import annotations

from dataclasses import dataclass
from .._compat import StrEnum


class FrontDoorIntent(StrEnum):
    SUBMIT_TASK = "SUBMIT_TASK"
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
