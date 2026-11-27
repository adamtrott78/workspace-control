"""Durable file-backed storage for Instant front-door intake candidates."""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import re

from ..domain import TaskIntakeCandidate


_SAFE_ID = re.compile(r"^[A-Za-z0-9._:-]+$")


class FrontDoorIntakeStoreError(RuntimeError):
    pass


class FileFrontDoorIntakeStore:
    """Persist candidate-only front-door records without promoting authority."""

    SCHEMA_VERSION = 1
    KIND = "FRONTDOOR_TASK_INTAKE_CANDIDATE"

    def __init__(self, root: Path) -> None:
        self._root = root

    def persist(
        self,
        candidate: TaskIntakeCandidate,
        *,
        submitted_at: str,
    ) -> Path:
        if candidate.authorization_state != "UNDECIDED":
            raise FrontDoorIntakeStoreError(
                "frontdoor_candidate_must_be_non_authoritative"
            )
        if not submitted_at:
            raise FrontDoorIntakeStoreError("submitted_at_required")
        if not _SAFE_ID.fullmatch(candidate.intake_id):
            raise FrontDoorIntakeStoreError("unsafe_frontdoor_intake_id")

        self._root.mkdir(parents=True, exist_ok=True)
        filename = candidate.intake_id.replace(":", "--") + ".json"
        path = self._root / filename
        if path.exists():
            raise FrontDoorIntakeStoreError(
                "frontdoor_intake_already_exists"
            )

        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "kind": self.KIND,
            "submitted_at": submitted_at,
            "candidate": asdict(candidate),
        }
        path.write_text(
            json.dumps(payload, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        return path

    def load(self, path: Path) -> TaskIntakeCandidate:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise FrontDoorIntakeStoreError(
                "frontdoor_intake_unreadable"
            ) from exc

        if not isinstance(payload, dict):
            raise FrontDoorIntakeStoreError("frontdoor_intake_expected_object")
        if payload.get("schema_version") != self.SCHEMA_VERSION:
            raise FrontDoorIntakeStoreError(
                "frontdoor_intake_schema_version_unknown"
            )
        if payload.get("kind") != self.KIND:
            raise FrontDoorIntakeStoreError("frontdoor_intake_kind_invalid")
        raw = payload.get("candidate")
        if not isinstance(raw, dict):
            raise FrontDoorIntakeStoreError(
                "frontdoor_intake_candidate_missing"
            )
        try:
            candidate = TaskIntakeCandidate(**raw)
        except (TypeError, ValueError) as exc:
            raise FrontDoorIntakeStoreError(
                "frontdoor_intake_candidate_invalid"
            ) from exc
        if candidate.authorization_state != "UNDECIDED":
            raise FrontDoorIntakeStoreError(
                "frontdoor_intake_authority_violation"
            )
        return candidate
