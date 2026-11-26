"""Deterministic durable control service for the persistent Instant front door."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Protocol

from ..domain import (
    FrontDoorIntent,
    FrontDoorMessage,
    TaskControlCandidate,
    TaskIntakeCandidate,
    TaskStatusView,
)
from .frontdoor import InstantFrontDoorIntake


class FrontDoorControlError(RuntimeError):
    pass


class TaskStatusReader(Protocol):
    def get_status(self, task_id: str) -> TaskStatusView: ...


class TaskIntakeWriter(Protocol):
    def persist(
        self,
        candidate: TaskIntakeCandidate,
        *,
        submitted_at: str,
    ) -> Path: ...


class TaskControlWriter(Protocol):
    def persist(
        self,
        candidate: TaskControlCandidate,
        *,
        submitted_at: str,
    ) -> Path: ...


@dataclass(frozen=True)
class FrontDoorControlResult:
    intent: FrontDoorIntent
    task_status: TaskStatusView | None = None
    intake_ref: str | None = None
    control_ref: str | None = None
    authorization_state: str = "UNDECIDED"


class InstantFrontDoorControlService:
    """Resolve front-door operations against durable Workspace Control state.

    This service can persist candidate records and read task status. It cannot
    mutate task capsules, execution authority, runtime state, or external
    effects.
    """

    def __init__(
        self,
        *,
        task_catalog: TaskStatusReader,
        intake_store: TaskIntakeWriter,
        control_store: TaskControlWriter,
        intake: InstantFrontDoorIntake | None = None,
    ) -> None:
        self._task_catalog = task_catalog
        self._intake_store = intake_store
        self._control_store = control_store
        self._intake = intake or InstantFrontDoorIntake()

    def handle(
        self,
        message: FrontDoorMessage,
        *,
        target_task_id: str | None = None,
    ) -> FrontDoorControlResult:
        if message.intent == FrontDoorIntent.SUBMIT_TASK:
            if target_task_id is not None:
                raise FrontDoorControlError(
                    "new_task_submission_must_not_target_existing_task"
                )
            intake = self._intake.ingest(message)
            if intake.candidate is None:
                raise FrontDoorControlError("frontdoor_intake_candidate_missing")
            path = self._intake_store.persist(
                intake.candidate,
                submitted_at=message.submitted_at,
            )
            return FrontDoorControlResult(
                intent=message.intent,
                intake_ref=str(path),
            )

        if not target_task_id:
            raise FrontDoorControlError("target_task_id_required")

        status = self._task_catalog.get_status(target_task_id)
        if message.intent == FrontDoorIntent.QUERY_STATUS:
            return FrontDoorControlResult(
                intent=message.intent,
                task_status=status,
            )

        if message.intent not in {
            FrontDoorIntent.RESUME_TASK,
            FrontDoorIntent.PROVIDE_DECISION,
            FrontDoorIntent.CANCEL_REQUEST,
        }:
            raise FrontDoorControlError(
                f"unsupported_frontdoor_intent:{message.intent}"
            )

        digest = hashlib.sha256(
            (
                f"{message.conversation_id}\0{message.message_id}\0"
                f"{message.intent.value}\0{target_task_id}\0{message.text}"
            ).encode("utf-8")
        ).hexdigest()
        candidate = TaskControlCandidate(
            control_id=f"frontdoor-control:{digest[:24]}",
            message_id=message.message_id,
            conversation_id=message.conversation_id,
            intent=message.intent,
            target_task_id=target_task_id,
            text=message.text.strip(),
            source_ref=(
                f"chatgpt-instant://{message.conversation_id}/"
                f"{message.message_id}"
            ),
            requested_by="human",
            authorization_state="UNDECIDED",
        )
        path = self._control_store.persist(
            candidate,
            submitted_at=message.submitted_at,
        )
        return FrontDoorControlResult(
            intent=message.intent,
            task_status=status,
            control_ref=str(path),
        )
