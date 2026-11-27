"""Application service for durable OperatorAction transport semantics."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..domain import (
    OperatorAction,
    OperatorActionKernel,
    OperatorActionState,
    OperatorHumanRequirement,
)
from .packet_compiler import CompiledPacket
from .runtime import RuntimeCoordinator


class OperatorActionServiceError(RuntimeError):
    """Fail-closed OperatorAction service error."""


class OperatorPacketMaterializer(Protocol):
    def materialize(self, action: OperatorAction) -> CompiledPacket: ...


@dataclass(frozen=True)
class ClaimedOperatorAction:
    action: OperatorAction
    packet_text: str | None


@dataclass(frozen=True)
class OperatorWorkloadStatus:
    ready_manual_cycles: int
    sent_unconfirmed: int


class OperatorActionService:
    """Transport-neutral backend contract for the Windows Operator Bridge."""

    def __init__(
        self,
        *,
        runtime: RuntimeCoordinator,
        packet_materializer: OperatorPacketMaterializer | None = None,
    ) -> None:
        self._runtime = runtime
        self._packet_materializer = packet_materializer

    def enqueue(self, action: OperatorAction) -> OperatorAction:
        snapshot = self._runtime.enqueue_operator_action(action)
        return snapshot.graph.operator_actions[action.action_id]

    def claim_next(
        self,
        *,
        helper_instance_id: str,
        claim_id: str,
        claimed_at: str,
        expires_at: str,
    ) -> ClaimedOperatorAction | None:
        snapshot = self._runtime.claim_next_operator_action(
            helper_instance_id=helper_instance_id,
            claim_id=claim_id,
            claimed_at=claimed_at,
            expires_at=expires_at,
        )
        claimed = next(
            (
                action
                for action in snapshot.graph.operator_actions.values()
                if action.claim is not None
                and action.claim.claim_id == claim_id
                and action.claim.helper_instance_id == helper_instance_id
            ),
            None,
        )
        if claimed is None:
            return None

        packet_text: str | None = None
        if claimed.payload_ref is not None:
            if self._packet_materializer is None:
                raise OperatorActionServiceError(
                    "packet_materializer_required"
                )
            packet = self._packet_materializer.materialize(claimed)
            if packet.packet_sha256 != claimed.payload_sha256:
                raise OperatorActionServiceError(
                    "materialized_packet_hash_mismatch"
                )
            if (
                claimed.executor_id is not None
                and packet.executor_id != claimed.executor_id
            ):
                raise OperatorActionServiceError(
                    "materialized_packet_executor_mismatch"
                )
            packet_text = packet.text
        return ClaimedOperatorAction(
            action=claimed,
            packet_text=packet_text,
        )

    def revalidate(
        self,
        *,
        action_id: str,
        generation: int,
        worker_slot_id: str | None,
        session_generation: int | None,
    ) -> bool:
        return OperatorActionKernel.revalidate(
            self._runtime.snapshot().graph,
            action_id=action_id,
            generation=generation,
            worker_slot_id=worker_slot_id,
            session_generation=session_generation,
        )

    def record_local_prepared(
        self,
        *,
        action_id: str,
        generation: int,
        worker_slot_id: str | None,
        session_generation: int | None,
        observed_at: str,
    ) -> OperatorAction:
        snapshot = self._runtime.record_operator_action_local_prepared(
            action_id=action_id,
            generation=generation,
            worker_slot_id=worker_slot_id,
            session_generation=session_generation,
            observed_at=observed_at,
        )
        return snapshot.graph.operator_actions[action_id]

    def record_local_completed(
        self,
        *,
        action_id: str,
        generation: int,
        worker_slot_id: str | None,
        session_generation: int | None,
        observed_at: str,
    ) -> OperatorAction:
        # Local-only actions declare COMPLETE_AND_REQUERY/STOP, so the same
        # exact local-prepared transition durably completes them.
        return self.record_local_prepared(
            action_id=action_id,
            generation=generation,
            worker_slot_id=worker_slot_id,
            session_generation=session_generation,
            observed_at=observed_at,
        )

    def record_local_failure(
        self,
        *,
        action_id: str,
        generation: int,
        failure_code: str,
        failure_message: str,
    ) -> OperatorAction:
        snapshot = self._runtime.record_operator_action_local_failure(
            action_id=action_id,
            generation=generation,
            failure_code=failure_code,
            failure_message=failure_message,
        )
        return snapshot.graph.operator_actions[action_id]

    def record_blocked(
        self,
        *,
        action_id: str,
        generation: int,
        failure_code: str,
        failure_message: str,
    ) -> OperatorAction:
        snapshot = self._runtime.record_operator_action_blocked(
            action_id=action_id,
            generation=generation,
            failure_code=failure_code,
            failure_message=failure_message,
        )
        return snapshot.graph.operator_actions[action_id]

    def record_durable_ack(
        self,
        *,
        action_id: str,
        generation: int,
        ack_id: str,
        completed_at: str,
    ) -> OperatorAction:
        acknowledged = self._runtime.record_operator_action_durable_ack(
            action_id=action_id,
            generation=generation,
            ack_id=ack_id,
        )
        if (
            acknowledged.graph.operator_actions[action_id].status
            != OperatorActionState.ACKNOWLEDGED
        ):
            return acknowledged.graph.operator_actions[action_id]
        completed = self._runtime.complete_acknowledged_operator_action(
            action_id=action_id,
            generation=generation,
            completed_at=completed_at,
        )
        return completed.graph.operator_actions[action_id]

    def workload_status(self) -> OperatorWorkloadStatus:
        graph = self._runtime.snapshot().graph
        ready = 0
        sent_unconfirmed = 0
        for action in graph.operator_actions.values():
            if action.status == OperatorActionState.QUEUED:
                if (
                    action.human_requirement
                    != OperatorHumanRequirement.NONE
                    and OperatorActionKernel.binding_is_current(
                        graph,
                        action,
                        require_bound_session=(
                            action.human_requirement
                            == OperatorHumanRequirement.PASTE_AND_SUBMIT
                        ),
                    )
                ):
                    ready += 1
            elif action.status == OperatorActionState.AWAITING_DURABLE_ACK:
                if OperatorActionKernel.binding_is_current(
                    graph,
                    action,
                    require_bound_session=False,
                ):
                    sent_unconfirmed += 1
        return OperatorWorkloadStatus(
            ready_manual_cycles=ready,
            sent_unconfirmed=sent_unconfirmed,
        )
