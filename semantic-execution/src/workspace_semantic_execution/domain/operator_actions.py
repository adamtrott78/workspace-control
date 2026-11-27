"""Pure durable OperatorAction lifecycle over WorkGraph state."""
from __future__ import annotations

from copy import deepcopy

from .models import (
    ExecutorSessionState,
    OperatorAckMode,
    OperatorAction,
    OperatorActionClaim,
    OperatorActionState,
    OperatorHumanRequirement,
    OperatorPostLocalSuccess,
    WorkGraph,
)


class OperatorActionError(RuntimeError):
    """Fail-closed OperatorAction transition error."""


ACTIVE_ACTION_STATES = {
    OperatorActionState.QUEUED,
    OperatorActionState.CLAIMED_LOCAL,
    OperatorActionState.LOCAL_PREPARED,
    OperatorActionState.AWAITING_DURABLE_ACK,
    OperatorActionState.ACKNOWLEDGED,
}
TERMINAL_ACTION_STATES = {
    OperatorActionState.COMPLETED,
    OperatorActionState.FAILED_LOCAL,
    OperatorActionState.CLAIM_EXPIRED,
    OperatorActionState.BLOCKED,
    OperatorActionState.STALE,
    OperatorActionState.SUPERSEDED,
}


class OperatorActionKernel:
    @staticmethod
    def _copy(graph: WorkGraph) -> WorkGraph:
        return deepcopy(graph)

    @staticmethod
    def _event(graph: WorkGraph, event: str, **details: object) -> None:
        graph.event_seq += 1
        graph.graph_history.append(
            {"seq": graph.event_seq, "event": event, "details": deepcopy(details)}
        )

    @staticmethod
    def _action(graph: WorkGraph, action_id: str) -> OperatorAction:
        try:
            return graph.operator_actions[action_id]
        except KeyError as exc:
            raise OperatorActionError(f"unknown_operator_action:{action_id}") from exc

    @staticmethod
    def _valid_sha256(value: str | None) -> bool:
        return (
            value is not None
            and len(value) == 64
            and all(ch in "0123456789abcdef" for ch in value)
        )

    @classmethod
    def validate_action(cls, action: OperatorAction) -> None:
        if not action.action_id or not action.task_id or not action.created_at:
            raise OperatorActionError("operator_action_identity_required")
        if action.generation < 0 or action.priority_rank < 0 or action.queue_sequence < 0:
            raise OperatorActionError("operator_action_nonnegative_fields_required")
        if (action.reasoning_process_id is None) != (action.process_generation is None):
            raise OperatorActionError("operator_action_process_binding_partial")
        if (action.worker_slot_id is None) != (action.session_generation is None):
            raise OperatorActionError("operator_action_session_binding_partial")
        if action.process_generation is not None and action.process_generation < 0:
            raise OperatorActionError("operator_action_process_generation_invalid")
        if action.session_generation is not None and action.session_generation < 0:
            raise OperatorActionError("operator_action_session_generation_invalid")
        if action.payload_ref is None and action.payload_sha256 is not None:
            raise OperatorActionError("operator_action_payload_ref_required")
        if action.payload_ref is not None and not cls._valid_sha256(action.payload_sha256):
            raise OperatorActionError("operator_action_payload_sha256_required")
        if action.human_requirement == OperatorHumanRequirement.PASTE_AND_SUBMIT:
            required = (
                action.reasoning_process_id,
                action.worker_slot_id,
                action.executor_id,
                action.payload_ref,
                action.payload_sha256,
            )
            if not all(required):
                raise OperatorActionError("service_action_binding_required")
        if (
            action.post_local_success == OperatorPostLocalSuccess.AWAIT_DURABLE_ACK
            and action.ack_mode == OperatorAckMode.NONE
        ):
            raise OperatorActionError("await_durable_ack_requires_ack_mode")
        if action.status == OperatorActionState.QUEUED and action.claim is not None:
            raise OperatorActionError("queued_action_cannot_have_claim")
        if action.status == OperatorActionState.AWAITING_DURABLE_ACK and action.local_prepared_at is None:
            raise OperatorActionError("awaiting_action_missing_local_prepared")
        if action.status == OperatorActionState.ACKNOWLEDGED and not action.durable_ack_id:
            raise OperatorActionError("acknowledged_action_missing_ack")
        if action.status == OperatorActionState.COMPLETED and action.completed_at is None:
            raise OperatorActionError("completed_action_missing_timestamp")

    @classmethod
    def validate_graph(cls, graph: WorkGraph) -> None:
        for action_id, action in graph.operator_actions.items():
            if action.action_id != action_id:
                raise OperatorActionError("operator_action_key_mismatch")
            cls.validate_action(action)
            if (
                action.reasoning_process_id is not None
                and action.reasoning_process_id not in graph.processes
            ):
                raise OperatorActionError("operator_action_unknown_process")
            if (
                action.worker_slot_id is not None
                and action.worker_slot_id not in graph.executor_sessions
            ):
                raise OperatorActionError("operator_action_unknown_session_slot")

    @classmethod
    def binding_is_current(
        cls,
        graph: WorkGraph,
        action: OperatorAction,
        *,
        require_bound_session: bool,
    ) -> bool:
        if action.reasoning_process_id is not None:
            process = graph.processes.get(action.reasoning_process_id)
            if process is None or process.generation != action.process_generation:
                return False
        if action.worker_slot_id is not None:
            session = graph.executor_sessions.get(action.worker_slot_id)
            if (
                session is None
                or session.session_generation != action.session_generation
                or (
                    action.executor_id is not None
                    and session.executor_id != action.executor_id
                )
            ):
                return False
            if require_bound_session:
                if session.state != ExecutorSessionState.BOUND:
                    return False
                if (
                    session.bound_process_id != action.reasoning_process_id
                    or session.bound_process_generation != action.process_generation
                    or (
                        action.payload_sha256 is not None
                        and session.bound_packet_sha256 != action.payload_sha256
                    )
                ):
                    return False
        return True

    @classmethod
    def enqueue(cls, graph: WorkGraph, action: OperatorAction) -> WorkGraph:
        cls.validate_action(action)
        if action.status != OperatorActionState.QUEUED:
            raise OperatorActionError("new_operator_action_must_be_queued")
        next_graph = cls._copy(graph)
        existing = next_graph.operator_actions.get(action.action_id)
        if existing is not None:
            if existing == action:
                return next_graph
            raise OperatorActionError(f"operator_action_conflict:{action.action_id}")
        if not cls.binding_is_current(
            next_graph,
            action,
            require_bound_session=(
                action.human_requirement
                == OperatorHumanRequirement.PASTE_AND_SUBMIT
            ),
        ):
            raise OperatorActionError("operator_action_binding_stale")
        next_graph.operator_actions[action.action_id] = deepcopy(action)
        cls._event(
            next_graph,
            "OPERATOR_ACTION_ENQUEUE",
            action_id=action.action_id,
            generation=action.generation,
            priority_rank=action.priority_rank,
            queue_sequence=action.queue_sequence,
        )
        cls.validate_graph(next_graph)
        return next_graph

    @classmethod
    def _mark_stale_queued_actions(cls, graph: WorkGraph) -> None:
        for action in graph.operator_actions.values():
            if action.status != OperatorActionState.QUEUED:
                continue
            if not cls.binding_is_current(
                graph,
                action,
                require_bound_session=(
                    action.human_requirement
                    == OperatorHumanRequirement.PASTE_AND_SUBMIT
                ),
            ):
                action.status = OperatorActionState.STALE
                cls._event(
                    graph,
                    "OPERATOR_ACTION_STALE",
                    action_id=action.action_id,
                    generation=action.generation,
                )

    @classmethod
    def claim_next(
        cls,
        graph: WorkGraph,
        *,
        helper_instance_id: str,
        claim_id: str,
        claimed_at: str,
        expires_at: str,
    ) -> WorkGraph:
        if not all((helper_instance_id, claim_id, claimed_at, expires_at)):
            raise OperatorActionError("operator_claim_identity_required")
        next_graph = cls._copy(graph)
        for action in next_graph.operator_actions.values():
            if (
                action.claim is not None
                and action.claim.claim_id == claim_id
                and action.claim.helper_instance_id == helper_instance_id
            ):
                return next_graph

        cls._mark_stale_queued_actions(next_graph)
        candidates = sorted(
            (
                action
                for action in next_graph.operator_actions.values()
                if action.status == OperatorActionState.QUEUED
            ),
            key=lambda item: (
                item.priority_rank,
                item.queue_sequence,
                item.action_id,
            ),
        )
        if not candidates:
            cls.validate_graph(next_graph)
            return next_graph
        action = candidates[0]
        action.status = OperatorActionState.CLAIMED_LOCAL
        action.claim = OperatorActionClaim(
            claim_id=claim_id,
            helper_instance_id=helper_instance_id,
            claimed_at=claimed_at,
            expires_at=expires_at,
        )
        cls._event(
            next_graph,
            "OPERATOR_ACTION_CLAIM",
            action_id=action.action_id,
            generation=action.generation,
            claim_id=claim_id,
            helper_instance_id=helper_instance_id,
        )
        cls.validate_graph(next_graph)
        return next_graph

    @classmethod
    def revalidate(
        cls,
        graph: WorkGraph,
        *,
        action_id: str,
        generation: int,
        worker_slot_id: str | None,
        session_generation: int | None,
    ) -> bool:
        action = graph.operator_actions.get(action_id)
        if action is None or action.generation != generation:
            return False
        if action.worker_slot_id != worker_slot_id:
            return False
        if action.session_generation != session_generation:
            return False
        if action.status != OperatorActionState.CLAIMED_LOCAL:
            return False
        return cls.binding_is_current(
            graph,
            action,
            require_bound_session=(
                action.human_requirement
                == OperatorHumanRequirement.PASTE_AND_SUBMIT
            ),
        )

    @classmethod
    def record_local_prepared(
        cls,
        graph: WorkGraph,
        *,
        action_id: str,
        generation: int,
        worker_slot_id: str | None,
        session_generation: int | None,
        observed_at: str,
    ) -> WorkGraph:
        next_graph = cls._copy(graph)
        action = cls._action(next_graph, action_id)
        if action.generation != generation:
            raise OperatorActionError("operator_action_generation_mismatch")
        if (
            action.worker_slot_id != worker_slot_id
            or action.session_generation != session_generation
        ):
            raise OperatorActionError("operator_action_identity_mismatch")
        if action.status != OperatorActionState.CLAIMED_LOCAL:
            raise OperatorActionError(f"local_prepared_invalid_state:{action.status}")
        if not cls.binding_is_current(
            next_graph,
            action,
            require_bound_session=(
                action.human_requirement
                == OperatorHumanRequirement.PASTE_AND_SUBMIT
            ),
        ):
            action.status = OperatorActionState.STALE
            cls._event(next_graph, "OPERATOR_ACTION_STALE", action_id=action.action_id)
            cls.validate_graph(next_graph)
            return next_graph
        action.local_prepared_at = observed_at
        if action.post_local_success == OperatorPostLocalSuccess.AWAIT_DURABLE_ACK:
            action.status = OperatorActionState.AWAITING_DURABLE_ACK
        else:
            action.status = OperatorActionState.COMPLETED
            action.completed_at = observed_at
        cls._event(
            next_graph,
            "OPERATOR_ACTION_LOCAL_PREPARED",
            action_id=action.action_id,
            status=action.status.value,
        )
        cls.validate_graph(next_graph)
        return next_graph

    @classmethod
    def record_local_failure(
        cls,
        graph: WorkGraph,
        *,
        action_id: str,
        generation: int,
        failure_code: str,
        failure_message: str,
    ) -> WorkGraph:
        if not failure_code:
            raise OperatorActionError("failure_code_required")
        next_graph = cls._copy(graph)
        action = cls._action(next_graph, action_id)
        if action.generation != generation:
            raise OperatorActionError("operator_action_generation_mismatch")
        if action.status not in {
            OperatorActionState.CLAIMED_LOCAL,
            OperatorActionState.LOCAL_PREPARED,
        }:
            raise OperatorActionError(f"local_failure_invalid_state:{action.status}")
        action.status = OperatorActionState.FAILED_LOCAL
        action.failure_code = failure_code
        action.failure_message = failure_message
        cls._event(
            next_graph,
            "OPERATOR_ACTION_LOCAL_FAILURE",
            action_id=action.action_id,
            failure_code=failure_code,
        )
        cls.validate_graph(next_graph)
        return next_graph

    @classmethod
    def record_blocked(
        cls,
        graph: WorkGraph,
        *,
        action_id: str,
        generation: int,
        failure_code: str,
        failure_message: str,
    ) -> WorkGraph:
        if not failure_code:
            raise OperatorActionError("failure_code_required")
        next_graph = cls._copy(graph)
        action = cls._action(next_graph, action_id)
        if action.generation != generation:
            raise OperatorActionError("operator_action_generation_mismatch")
        if action.status not in {
            OperatorActionState.QUEUED,
            OperatorActionState.CLAIMED_LOCAL,
        }:
            raise OperatorActionError(f"blocked_invalid_state:{action.status}")
        action.status = OperatorActionState.BLOCKED
        action.failure_code = failure_code
        action.failure_message = failure_message
        cls._event(
            next_graph,
            "OPERATOR_ACTION_BLOCKED",
            action_id=action.action_id,
            failure_code=failure_code,
        )
        cls.validate_graph(next_graph)
        return next_graph

    @classmethod
    def record_durable_ack(
        cls,
        graph: WorkGraph,
        *,
        action_id: str,
        generation: int,
        ack_id: str,
    ) -> WorkGraph:
        if not ack_id:
            raise OperatorActionError("durable_ack_id_required")
        next_graph = cls._copy(graph)
        action = cls._action(next_graph, action_id)
        if action.generation != generation:
            raise OperatorActionError("operator_action_generation_mismatch")
        if action.status != OperatorActionState.AWAITING_DURABLE_ACK:
            raise OperatorActionError(f"durable_ack_invalid_state:{action.status}")
        if not cls.binding_is_current(
            next_graph,
            action,
            require_bound_session=False,
        ):
            action.status = OperatorActionState.STALE
            cls._event(next_graph, "OPERATOR_ACTION_STALE", action_id=action.action_id)
            cls.validate_graph(next_graph)
            return next_graph
        action.status = OperatorActionState.ACKNOWLEDGED
        action.durable_ack_id = ack_id
        cls._event(
            next_graph,
            "OPERATOR_ACTION_ACKNOWLEDGED",
            action_id=action.action_id,
            ack_id=ack_id,
        )
        cls.validate_graph(next_graph)
        return next_graph

    @classmethod
    def complete_acknowledged(
        cls,
        graph: WorkGraph,
        *,
        action_id: str,
        generation: int,
        completed_at: str,
    ) -> WorkGraph:
        next_graph = cls._copy(graph)
        action = cls._action(next_graph, action_id)
        if action.generation != generation:
            raise OperatorActionError("operator_action_generation_mismatch")
        if action.status != OperatorActionState.ACKNOWLEDGED:
            raise OperatorActionError(f"complete_invalid_state:{action.status}")
        action.status = OperatorActionState.COMPLETED
        action.completed_at = completed_at
        cls._event(
            next_graph,
            "OPERATOR_ACTION_COMPLETED",
            action_id=action.action_id,
        )
        cls.validate_graph(next_graph)
        return next_graph

    @classmethod
    def expire_claim(
        cls,
        graph: WorkGraph,
        *,
        action_id: str,
        generation: int,
    ) -> WorkGraph:
        next_graph = cls._copy(graph)
        action = cls._action(next_graph, action_id)
        if action.generation != generation:
            raise OperatorActionError("operator_action_generation_mismatch")
        if action.status != OperatorActionState.CLAIMED_LOCAL:
            raise OperatorActionError(f"claim_expire_invalid_state:{action.status}")
        action.status = OperatorActionState.CLAIM_EXPIRED
        cls._event(
            next_graph,
            "OPERATOR_ACTION_CLAIM_EXPIRED",
            action_id=action.action_id,
        )
        cls.validate_graph(next_graph)
        return next_graph

    @classmethod
    def stale_for_process_generation(
        cls,
        graph: WorkGraph,
        *,
        process_id: str,
        process_generation: int,
    ) -> None:
        for action in graph.operator_actions.values():
            if (
                action.status in ACTIVE_ACTION_STATES
                and action.reasoning_process_id == process_id
                and action.process_generation == process_generation
            ):
                action.status = OperatorActionState.STALE
                cls._event(
                    graph,
                    "OPERATOR_ACTION_STALE",
                    action_id=action.action_id,
                    reason="process_generation_advanced",
                )

    @classmethod
    def stale_for_session_generation(
        cls,
        graph: WorkGraph,
        *,
        slot_id: str,
        session_generation: int,
    ) -> None:
        for action in graph.operator_actions.values():
            if (
                action.status in ACTIVE_ACTION_STATES
                and action.worker_slot_id == slot_id
                and action.session_generation == session_generation
            ):
                action.status = OperatorActionState.STALE
                cls._event(
                    graph,
                    "OPERATOR_ACTION_STALE",
                    action_id=action.action_id,
                    reason="session_generation_advanced",
                )
