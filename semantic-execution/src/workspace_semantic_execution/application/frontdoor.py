"""Deterministic Instant front-door intake."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib

from ..domain import (
    FrontDoorIntent,
    FrontDoorMessage,
    TaskIntakeCandidate,
)


class FrontDoorIntakeError(RuntimeError):
    pass


@dataclass(frozen=True)
class FrontDoorIntakeResult:
    message: FrontDoorMessage
    candidate: TaskIntakeCandidate | None
    requires_existing_task_lookup: bool


class InstantFrontDoorIntake:
    """Translate human chat input into typed non-authoritative control input.

    The front door is an interface, not an authority source. Task submissions
    become candidates for the existing Workspace Control intake/policy path.
    """

    def ingest(self, message: FrontDoorMessage) -> FrontDoorIntakeResult:
        if message.intent == FrontDoorIntent.SUBMIT_TASK:
            digest = hashlib.sha256(
                f"{message.conversation_id}\0{message.message_id}\0{message.text}".encode(
                    "utf-8"
                )
            ).hexdigest()
            candidate = TaskIntakeCandidate(
                intake_id=f"frontdoor:{digest[:24]}",
                message_id=message.message_id,
                conversation_id=message.conversation_id,
                objective=message.text.strip(),
                source_ref=f"chatgpt-instant://{message.conversation_id}/{message.message_id}",
                requested_by="human",
                authorization_state="UNDECIDED",
            )
            return FrontDoorIntakeResult(
                message=message,
                candidate=candidate,
                requires_existing_task_lookup=False,
            )

        if message.intent in {
            FrontDoorIntent.RESUME_TASK,
            FrontDoorIntent.QUERY_STATUS,
            FrontDoorIntent.PROVIDE_DECISION,
            FrontDoorIntent.CANCEL_REQUEST,
        }:
            return FrontDoorIntakeResult(
                message=message,
                candidate=None,
                requires_existing_task_lookup=True,
            )

        raise FrontDoorIntakeError(f"unsupported_frontdoor_intent:{message.intent}")
