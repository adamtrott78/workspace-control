"""Provisional DBOS adapter for bounded durable work.

DBOS owns durable execution/recovery of bounded work quanta only. External
semantic waits are persisted in StateStorePort and resumed from EventLedgerPort;
this adapter never uses DBOS.recv for WAITING_EXTERNAL.

The spike is pinned to DBOS Python 3.5.0. Application bootstrap must construct
and launch DBOS and register the queues before this adapter is used.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.metadata
import json
from typing import Any, Callable

from ..ports import (
    DurableWorkConflict,
    DurableWorkRequest,
    DurableWorkState,
    DurableWorkStatus,
)


_REQUIRED_DBOS_VERSION = "3.5.0"


def _load_dbos():
    try:
        installed = importlib.metadata.version("dbos")
    except importlib.metadata.PackageNotFoundError as exc:
        raise RuntimeError(
            "DBOS adapter requires the dedicated dbos==3.5.0 spike dependency."
        ) from exc
    if installed != _REQUIRED_DBOS_VERSION:
        raise RuntimeError(
            "DBOS spike version mismatch:"
            f"required={_REQUIRED_DBOS_VERSION}:installed={installed}"
        )
    try:
        from dbos import DBOS, SetWorkflowID  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("DBOS import failed") from exc
    return DBOS, SetWorkflowID


def _request_envelope(request: DurableWorkRequest) -> dict[str, Any]:
    if not request.work_id or not request.work_kind or not request.queue_name:
        raise ValueError("durable_work_required_fields")
    envelope = {
        "work_kind": request.work_kind,
        "payload": deepcopy(request.payload),
        "queue_name": request.queue_name,
    }
    try:
        json.dumps(
            envelope,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("durable_work_payload_must_be_json_serializable") from exc
    return envelope


def _status_to_port(status: Any) -> DurableWorkStatus:
    raw = str(status.status)
    if raw in {"ENQUEUED", "DELAYED", "SUSPENDED"}:
        state = DurableWorkState.ENQUEUED
    elif raw == "PENDING":
        state = DurableWorkState.RUNNING
    elif raw == "SUCCESS":
        state = DurableWorkState.COMPLETED
    elif raw in {"ERROR", "MAX_RECOVERY_ATTEMPTS_EXCEEDED"}:
        state = DurableWorkState.FAILED
    elif raw == "CANCELLED":
        state = DurableWorkState.CANCELLED
    else:
        state = DurableWorkState.UNKNOWN

    output = getattr(status, "output", None)
    result_ref: str | None = None
    if isinstance(output, str) and output:
        result_ref = output
    elif isinstance(output, dict):
        candidate = output.get("result_ref")
        if isinstance(candidate, str) and candidate:
            result_ref = candidate

    error = getattr(status, "error", None)
    error_text = str(error) if error is not None else None

    return DurableWorkStatus(
        work_id=str(status.workflow_id),
        state=state,
        result_ref=result_ref,
        error=error_text,
    )


def _assert_immutable_request(
    status: Any,
    request: DurableWorkRequest,
    envelope: dict[str, Any],
) -> None:
    if str(status.workflow_id) != request.work_id:
        raise DurableWorkConflict("dbos_workflow_id_mismatch")
    if getattr(status, "queue_name", None) != request.queue_name:
        raise DurableWorkConflict("dbos_queue_name_mismatch")

    inputs = getattr(status, "input", None)
    if not isinstance(inputs, dict):
        raise DurableWorkConflict("dbos_workflow_input_unavailable")
    args = inputs.get("args")
    kwargs = inputs.get("kwargs")
    if args != (envelope,) or kwargs != {}:
        raise DurableWorkConflict("conflicting_durable_work_id")


class DBOSDurableRuntime:
    """DurableRuntimePort adapter over an already-launched DBOS process."""

    def __init__(
        self,
        *,
        workflow_fn: Callable[[dict[str, Any]], Any],
        registered_queues: frozenset[str],
    ) -> None:
        if not callable(workflow_fn):
            raise ValueError("workflow_fn_required")
        if not registered_queues or any(
            not queue for queue in registered_queues
        ):
            raise ValueError("registered_queues_required")
        self._workflow_fn = workflow_fn
        self._registered_queues = registered_queues
        self._dbos, self._set_workflow_id = _load_dbos()

    def submit(self, request: DurableWorkRequest) -> DurableWorkStatus:
        if request.queue_name not in self._registered_queues:
            raise ValueError(f"queue_not_registered:{request.queue_name}")
        envelope = _request_envelope(request)

        existing = self._dbos.get_workflow_status(request.work_id)
        if existing is not None:
            _assert_immutable_request(existing, request, envelope)
            return _status_to_port(existing)

        # Default DBOS workflow-ID reuse is idempotent: if another submit wins
        # this race, this call resolves to the already-existing execution.
        with self._set_workflow_id(request.work_id):
            self._dbos.enqueue_workflow(
                request.queue_name,
                self._workflow_fn,
                envelope,
            )

        status = self._dbos.get_workflow_status(request.work_id)
        if status is None:
            raise RuntimeError("dbos_submit_missing_status")
        _assert_immutable_request(status, request, envelope)
        return _status_to_port(status)

    def get_status(self, *, work_id: str) -> DurableWorkStatus | None:
        if not work_id:
            raise ValueError("work_id_required")
        status = self._dbos.get_workflow_status(work_id)
        if status is None:
            return None
        return _status_to_port(status)
