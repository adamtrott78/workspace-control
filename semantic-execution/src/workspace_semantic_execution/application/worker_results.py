"""Durable worker-result intake and transition validation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol

from ..domain import (
    ProcessState,
    SemanticPacketSource,
    ValidationResult,
    WorkerResultKind,
    WorkerResultPublication,
)
from .operator_packets import (
    operator_dispatch_lease_id,
    operator_dispatch_worker_id,
)
from .runtime import RuntimeCoordinator


class WorkerResultIntakeError(RuntimeError):
    """Fail-closed worker-result intake error."""


class WorkerResultValidator(Protocol):
    def validate(
        self,
        publication: WorkerResultPublication,
        packet_source: SemanticPacketSource,
    ) -> ValidationResult: ...


@dataclass(frozen=True)
class WorkerResultIntakeOutcome:
    publication: WorkerResultPublication
    process_state: ProcessState
    validation: ValidationResult | None


class WorkerResultIntakeService:
    """Ingest durable worker-authored state without reading consumer UI."""

    def __init__(
        self,
        *,
        runtime: RuntimeCoordinator,
        validators: Mapping[str, WorkerResultValidator] | None = None,
    ) -> None:
        self._runtime = runtime
        self._validators = dict(validators or {})

    def ingest(
        self,
        publication: WorkerResultPublication,
    ) -> WorkerResultIntakeOutcome:
        before = self._runtime.snapshot().graph
        action = before.operator_actions.get(publication.action_id)
        if action is None:
            raise WorkerResultIntakeError(
                "worker_result_action_unknown"
            )
        if action.payload_ref is None:
            raise WorkerResultIntakeError(
                "worker_result_action_payload_missing"
            )
        source = before.packet_sources.get(action.payload_ref)
        if source is None:
            raise WorkerResultIntakeError(
                "worker_result_packet_source_missing"
            )

        contract = source.result_publication
        if contract is not None:
            if (
                publication.publication_id
                != contract.publication_id
                or publication.action_id != contract.action_id
                or publication.action_generation
                != contract.action_generation
                or publication.process_generation
                != contract.process_generation
                or publication.worker_slot_id
                != contract.worker_slot_id
                or publication.session_generation
                != contract.session_generation
                or not publication.source_ref.startswith(
                    contract.target_ref + "@"
                )
            ):
                raise WorkerResultIntakeError(
                    "worker_result_publication_contract_mismatch"
                )

        validator: WorkerResultValidator | None = None
        if publication.kind == WorkerResultKind.RESULT:
            validator = self._validators.get(
                source.validator_contract
            )
            if validator is None:
                raise WorkerResultIntakeError(
                    "worker_result_validator_unavailable:"
                    f"{source.validator_contract}"
                )

        worker_id = operator_dispatch_worker_id(
            executor_id=publication.executor_id,
            worker_slot_id=publication.worker_slot_id,
            session_generation=publication.session_generation,
        )
        lease_id = operator_dispatch_lease_id(
            action_id=publication.action_id,
            action_generation=publication.action_generation,
        )

        existing = before.worker_results.get(
            publication.publication_id
        )
        if existing is None:
            snapshot = self._runtime.accept_worker_result(
                publication=publication,
                worker_id=worker_id,
                lease_id=lease_id,
            )
        elif existing == publication:
            snapshot = self._runtime.snapshot()
        else:
            raise WorkerResultIntakeError(
                "worker_result_publication_conflict"
            )

        process = snapshot.graph.processes[
            publication.process_id
        ]
        if publication.kind != WorkerResultKind.RESULT:
            return WorkerResultIntakeOutcome(
                publication=publication,
                process_state=process.state,
                validation=None,
            )

        assert validator is not None
        if process.state == ProcessState.COMPLETED:
            latest = (
                process.validations[-1]
                if process.validations
                else None
            )
            return WorkerResultIntakeOutcome(
                publication=publication,
                process_state=process.state,
                validation=latest,
            )
        if (
            process.state == ProcessState.READY_TO_RESUME
            and process.validations
        ):
            return WorkerResultIntakeOutcome(
                publication=publication,
                process_state=process.state,
                validation=process.validations[-1],
            )
        if process.state == ProcessState.TERMINAL_CANDIDATE:
            snapshot = self._runtime.begin_validation(
                publication.process_id
            )
            process = snapshot.graph.processes[
                publication.process_id
            ]
        if process.state != ProcessState.VALIDATING:
            raise WorkerResultIntakeError(
                "worker_result_validation_state_invalid:"
                f"{process.state.value}"
            )

        result = validator.validate(publication, source)
        final = self._runtime.record_validation(
            publication.process_id,
            result=result,
        )
        return WorkerResultIntakeOutcome(
            publication=publication,
            process_state=final.graph.processes[
                publication.process_id
            ].state,
            validation=result,
        )
