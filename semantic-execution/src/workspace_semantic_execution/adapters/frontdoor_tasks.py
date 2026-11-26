"""Durable task/status and control-candidate adapters for the Instant front door."""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import re

from ..domain import (
    FrontDoorIntent,
    TaskControlCandidate,
    TaskStatusView,
)


_TASK_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_SAFE_CONTROL_ID_RE = re.compile(r"^[A-Za-z0-9._:-]+$")


class FrontDoorTaskCatalogError(RuntimeError):
    pass


class FrontDoorControlStoreError(RuntimeError):
    pass


class FileTaskCapsuleCatalog:
    """Read compact status from authoritative active task capsules."""

    def __init__(self, active_root: Path) -> None:
        self._active_root = active_root

    def get_status(self, task_id: str) -> TaskStatusView:
        if not _TASK_ID_RE.fullmatch(task_id):
            raise FrontDoorTaskCatalogError("task_id_invalid")
        path = self._active_root / f"{task_id}.json"
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise FrontDoorTaskCatalogError("task_not_found") from exc
        except (OSError, json.JSONDecodeError) as exc:
            raise FrontDoorTaskCatalogError("task_capsule_unreadable") from exc

        if not isinstance(raw, dict):
            raise FrontDoorTaskCatalogError("task_capsule_expected_object")
        if raw.get("task_id") != task_id:
            raise FrontDoorTaskCatalogError("task_capsule_identity_mismatch")

        title = raw.get("title")
        status = raw.get("status")
        next_safe_action = raw.get("next_safe_action")
        current_stage = raw.get("current_stage")
        blockers = raw.get("blockers")
        remaining = raw.get("remaining_work")
        checkpoints = raw.get("checkpoints", [])

        if (
            not isinstance(title, str)
            or not title
            or not isinstance(status, str)
            or not status
            or not isinstance(next_safe_action, str)
            or not next_safe_action
            or current_stage is not None
            and not isinstance(current_stage, str)
            or not isinstance(blockers, list)
            or any(not isinstance(item, str) for item in blockers)
            or not isinstance(remaining, list)
            or any(not isinstance(item, str) for item in remaining)
            or not isinstance(checkpoints, list)
        ):
            raise FrontDoorTaskCatalogError("task_capsule_status_fields_invalid")

        latest_checkpoint_id = None
        for item in reversed(checkpoints):
            if isinstance(item, dict):
                checkpoint_id = item.get("id")
                if isinstance(checkpoint_id, str) and checkpoint_id:
                    latest_checkpoint_id = checkpoint_id
                    break

        return TaskStatusView(
            task_id=task_id,
            title=title,
            status=status,
            current_stage=current_stage,
            next_safe_action=next_safe_action,
            blockers=tuple(blockers),
            remaining_work_count=len(remaining),
            latest_checkpoint_id=latest_checkpoint_id,
        )


class FileFrontDoorControlStore:
    """Persist resume/decision/cancel candidates without mutating task state."""

    SCHEMA_VERSION = 1
    KIND = "FRONTDOOR_TASK_CONTROL_CANDIDATE"

    def __init__(self, root: Path) -> None:
        self._root = root

    def persist(
        self,
        candidate: TaskControlCandidate,
        *,
        submitted_at: str,
    ) -> Path:
        if candidate.authorization_state != "UNDECIDED":
            raise FrontDoorControlStoreError(
                "frontdoor_control_must_be_non_authoritative"
            )
        if candidate.intent not in {
            FrontDoorIntent.RESUME_TASK,
            FrontDoorIntent.PROVIDE_DECISION,
            FrontDoorIntent.CANCEL_REQUEST,
        }:
            raise FrontDoorControlStoreError("frontdoor_control_intent_invalid")
        if not submitted_at:
            raise FrontDoorControlStoreError("submitted_at_required")
        if not _SAFE_CONTROL_ID_RE.fullmatch(candidate.control_id):
            raise FrontDoorControlStoreError("unsafe_frontdoor_control_id")

        self._root.mkdir(parents=True, exist_ok=True)
        filename = candidate.control_id.replace(":", "--") + ".json"
        path = self._root / filename
        if path.exists():
            raise FrontDoorControlStoreError(
                "frontdoor_control_already_exists"
            )

        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "kind": self.KIND,
            "submitted_at": submitted_at,
            "candidate": {
                **asdict(candidate),
                "intent": candidate.intent.value,
            },
        }
        path.write_text(
            json.dumps(payload, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        return path

    def load(self, path: Path) -> TaskControlCandidate:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise FrontDoorControlStoreError(
                "frontdoor_control_unreadable"
            ) from exc
        if not isinstance(payload, dict):
            raise FrontDoorControlStoreError(
                "frontdoor_control_expected_object"
            )
        if payload.get("schema_version") != self.SCHEMA_VERSION:
            raise FrontDoorControlStoreError(
                "frontdoor_control_schema_version_unknown"
            )
        if payload.get("kind") != self.KIND:
            raise FrontDoorControlStoreError("frontdoor_control_kind_invalid")

        raw = payload.get("candidate")
        if not isinstance(raw, dict):
            raise FrontDoorControlStoreError(
                "frontdoor_control_candidate_missing"
            )
        try:
            normalized = dict(raw)
            normalized["intent"] = FrontDoorIntent(normalized["intent"])
            candidate = TaskControlCandidate(**normalized)
        except (KeyError, TypeError, ValueError) as exc:
            raise FrontDoorControlStoreError(
                "frontdoor_control_candidate_invalid"
            ) from exc
        if candidate.authorization_state != "UNDECIDED":
            raise FrontDoorControlStoreError(
                "frontdoor_control_authority_violation"
            )
        return candidate
