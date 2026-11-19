"""Strict JSON codec for immutable worker-authored result publications."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from ..domain import (
    WorkerChildProposal,
    WorkerResultKind,
    WorkerResultPublication,
    WorkerResultKernel,
)


class WorkerResultJsonError(ValueError):
    """Raised when worker-authored result JSON violates the frozen contract."""


_TOP_LEVEL_KEYS = {
    "publication_id",
    "action_id",
    "action_generation",
    "process_id",
    "process_generation",
    "executor_id",
    "worker_slot_id",
    "session_generation",
    "packet_sha256",
    "kind",
    "observed_at",
    "result_payload_ref",
    "result_payload_sha256",
    "evidence_refs",
    "reason",
    "wait_key",
    "children",
}
_CHILD_KEYS = {
    "process_id",
    "objective",
    "dependencies",
    "mandatory_constraints",
    "provenance_refs",
    "authority_refs",
    "validator_contracts",
    "output_schema_refs",
}


def _string_tuple(
    value: object,
    *,
    field: str,
) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise WorkerResultJsonError(f"{field}_must_be_array")
    if any(not isinstance(item, str) or not item for item in value):
        raise WorkerResultJsonError(f"{field}_must_contain_strings")
    return tuple(value)


def _optional_string(
    payload: dict[str, Any],
    name: str,
) -> str | None:
    value = payload.get(name)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise WorkerResultJsonError(f"{name}_invalid")
    return value


def parse_worker_result_json(
    raw: bytes,
    *,
    source_ref: str,
) -> WorkerResultPublication:
    """Parse exact immutable bytes and bind their SHA-256 into the publication."""

    if not raw:
        raise WorkerResultJsonError("worker_result_json_empty")
    if len(raw) > 1_048_576:
        raise WorkerResultJsonError("worker_result_json_too_large")
    if not source_ref:
        raise WorkerResultJsonError("worker_result_source_ref_required")

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WorkerResultJsonError("worker_result_json_invalid") from exc
    if not isinstance(payload, dict):
        raise WorkerResultJsonError("worker_result_json_object_required")
    unknown = set(payload) - _TOP_LEVEL_KEYS
    if unknown:
        raise WorkerResultJsonError(
            "worker_result_unknown_fields:" + ",".join(sorted(unknown))
        )

    children_raw = payload.get("children", [])
    if not isinstance(children_raw, list):
        raise WorkerResultJsonError("children_must_be_array")
    children: list[WorkerChildProposal] = []
    for raw_child in children_raw:
        if not isinstance(raw_child, dict):
            raise WorkerResultJsonError("child_must_be_object")
        child_unknown = set(raw_child) - _CHILD_KEYS
        if child_unknown:
            raise WorkerResultJsonError(
                "worker_result_child_unknown_fields:"
                + ",".join(sorted(child_unknown))
            )
        process_id = raw_child.get("process_id")
        objective = raw_child.get("objective")
        if (
            not isinstance(process_id, str)
            or not process_id
            or not isinstance(objective, str)
            or not objective
        ):
            raise WorkerResultJsonError(
                "worker_result_child_identity_required"
            )
        children.append(
            WorkerChildProposal(
                process_id=process_id,
                objective=objective,
                dependencies=_string_tuple(
                    raw_child.get("dependencies"),
                    field="child_dependencies",
                ),
                mandatory_constraints=_string_tuple(
                    raw_child.get("mandatory_constraints"),
                    field="child_mandatory_constraints",
                ),
                provenance_refs=_string_tuple(
                    raw_child.get("provenance_refs"),
                    field="child_provenance_refs",
                ),
                authority_refs=_string_tuple(
                    raw_child.get("authority_refs"),
                    field="child_authority_refs",
                ),
                validator_contracts=_string_tuple(
                    raw_child.get("validator_contracts"),
                    field="child_validator_contracts",
                ),
                output_schema_refs=_string_tuple(
                    raw_child.get("output_schema_refs"),
                    field="child_output_schema_refs",
                ),
            )
        )

    try:
        publication = WorkerResultPublication(
            publication_id=str(payload["publication_id"]),
            source_ref=source_ref,
            source_sha256=hashlib.sha256(raw).hexdigest(),
            action_id=str(payload["action_id"]),
            action_generation=int(payload["action_generation"]),
            process_id=str(payload["process_id"]),
            process_generation=int(payload["process_generation"]),
            executor_id=str(payload["executor_id"]),
            worker_slot_id=str(payload["worker_slot_id"]),
            session_generation=int(payload["session_generation"]),
            packet_sha256=str(payload["packet_sha256"]),
            kind=WorkerResultKind(str(payload["kind"])),
            observed_at=str(payload["observed_at"]),
            result_payload_ref=_optional_string(
                payload, "result_payload_ref"
            ),
            result_payload_sha256=_optional_string(
                payload, "result_payload_sha256"
            ),
            evidence_refs=_string_tuple(
                payload.get("evidence_refs"),
                field="evidence_refs",
            ),
            reason=_optional_string(payload, "reason"),
            wait_key=_optional_string(payload, "wait_key"),
            children=tuple(children),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise WorkerResultJsonError(
            "worker_result_required_field_invalid"
        ) from exc

    try:
        WorkerResultKernel.validate_publication(publication)
    except RuntimeError as exc:
        raise WorkerResultJsonError(str(exc)) from exc
    return publication
