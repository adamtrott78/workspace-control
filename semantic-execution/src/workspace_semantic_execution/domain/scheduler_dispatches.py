"""Durable production-scheduler dispatch specifications."""
from __future__ import annotations

from copy import deepcopy
import re

from .executors import InvocationMode
from .models import SchedulerDispatchSpec, WorkGraph


class SchedulerDispatchError(RuntimeError):
    """Fail-closed durable scheduler-plan contract error."""


_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_CANDIDATE_REF = "refs/heads/worker-result-candidates-v1"
_CANDIDATE_PREFIX = "worker-results/candidates/"


class SchedulerDispatchKernel:
    @classmethod
    def validate_spec(cls, spec: SchedulerDispatchSpec) -> None:
        required = (
            spec.dispatch_id,
            spec.process_id,
            spec.requirement_id,
            spec.packet.source_checkpoint,
            spec.packet.objective,
            spec.packet.validator_contract,
            spec.packet.output_schema,
            spec.packet.next_safe_boundary,
        )
        if not all(isinstance(value, str) and value for value in required):
            raise SchedulerDispatchError(
                "scheduler_dispatch_required_fields"
            )
        if spec.process_generation < 0:
            raise SchedulerDispatchError(
                "scheduler_dispatch_generation_invalid"
            )

        modes = spec.requirement.allowed_invocation_modes
        if not modes:
            raise SchedulerDispatchError(
                "scheduler_dispatch_invocation_modes_required"
            )
        supported = {
            InvocationMode.HUMAN_ASSISTED,
            InvocationMode.DETERMINISTIC,
        }
        if not modes.issubset(supported):
            raise SchedulerDispatchError(
                "scheduler_dispatch_invocation_mode_unsupported"
            )
        if (
            InvocationMode.HUMAN_ASSISTED in modes
            and spec.operator is None
        ):
            raise SchedulerDispatchError(
                "scheduler_dispatch_operator_parameters_required"
            )
        if (
            InvocationMode.DETERMINISTIC in modes
            and spec.deterministic is None
        ):
            raise SchedulerDispatchError(
                "scheduler_dispatch_deterministic_parameters_required"
            )

        for values in (
            spec.packet.constraints,
            spec.packet.evidence_refs,
            spec.packet.authority_refs,
            spec.packet.allowed_actions,
        ):
            if any(not isinstance(value, str) or not value for value in values):
                raise SchedulerDispatchError(
                    "scheduler_dispatch_packet_value_invalid"
                )

        operator = spec.operator
        if operator is not None:
            required_operator = (
                operator.task_id,
                operator.action_id,
                operator.worker_slot_id,
                operator.created_at,
                operator.candidate_repository,
                operator.candidate_ref,
                operator.candidate_path,
                operator.candidate_schema_ref,
            )
            if not all(
                isinstance(value, str) and value
                for value in required_operator
            ):
                raise SchedulerDispatchError(
                    "scheduler_dispatch_operator_fields_invalid"
                )
            if (
                operator.action_generation < 0
                or operator.session_generation < 0
                or operator.priority_rank < 0
                or operator.queue_sequence < 0
            ):
                raise SchedulerDispatchError(
                    "scheduler_dispatch_operator_number_invalid"
                )
            if not _REPOSITORY_RE.fullmatch(
                operator.candidate_repository
            ):
                raise SchedulerDispatchError(
                    "scheduler_dispatch_candidate_repository_invalid"
                )
            if operator.candidate_ref != _CANDIDATE_REF:
                raise SchedulerDispatchError(
                    "scheduler_dispatch_candidate_ref_invalid"
                )
            if (
                not operator.candidate_path.startswith(_CANDIDATE_PREFIX)
                or not operator.candidate_path.endswith(".json")
                or ".." in operator.candidate_path
                or operator.candidate_path.startswith("/")
                or "//" in operator.candidate_path
            ):
                raise SchedulerDispatchError(
                    "scheduler_dispatch_candidate_path_invalid"
                )

        deterministic = spec.deterministic
        if deterministic is not None:
            if not deterministic.worker_id or not deterministic.lease_id:
                raise SchedulerDispatchError(
                    "scheduler_dispatch_deterministic_identity_invalid"
                )
            action = deterministic.candidate_action
            if (
                action.process_id != spec.process_id
                or action.process_generation != spec.process_generation
            ):
                raise SchedulerDispatchError(
                    "scheduler_dispatch_candidate_action_binding_mismatch"
                )

    @classmethod
    def register(
        cls,
        graph: WorkGraph,
        spec: SchedulerDispatchSpec,
    ) -> WorkGraph:
        cls.validate_spec(spec)
        next_graph = deepcopy(graph)
        process = next_graph.processes.get(spec.process_id)
        if process is None:
            raise SchedulerDispatchError(
                "scheduler_dispatch_unknown_process"
            )
        if spec.process_generation > process.generation:
            raise SchedulerDispatchError(
                "scheduler_dispatch_future_generation"
            )

        for other in next_graph.scheduler_dispatches.values():
            if (
                other.dispatch_id != spec.dispatch_id
                and other.process_id == spec.process_id
                and other.process_generation == spec.process_generation
            ):
                raise SchedulerDispatchError(
                    "scheduler_dispatch_process_generation_conflict"
                )

        existing = next_graph.scheduler_dispatches.get(spec.dispatch_id)
        if existing is not None:
            if existing == spec:
                return next_graph
            raise SchedulerDispatchError(
                f"scheduler_dispatch_conflict:{spec.dispatch_id}"
            )

        next_graph.scheduler_dispatches[spec.dispatch_id] = deepcopy(spec)
        next_graph.event_seq += 1
        next_graph.graph_history.append(
            {
                "seq": next_graph.event_seq,
                "event": "SCHEDULER_DISPATCH_REGISTER",
                "details": {
                    "dispatch_id": spec.dispatch_id,
                    "process_id": spec.process_id,
                    "process_generation": spec.process_generation,
                    "requirement_id": spec.requirement_id,
                },
            }
        )
        return next_graph

    @classmethod
    def validate_graph(cls, graph: WorkGraph) -> None:
        for dispatch_id, spec in graph.scheduler_dispatches.items():
            if spec.dispatch_id != dispatch_id:
                raise SchedulerDispatchError(
                    "scheduler_dispatch_key_mismatch"
                )
            cls.validate_spec(spec)
            process = graph.processes.get(spec.process_id)
            if process is None:
                raise SchedulerDispatchError(
                    "scheduler_dispatch_unknown_process"
                )
            if spec.process_generation > process.generation:
                raise SchedulerDispatchError(
                    "scheduler_dispatch_future_generation"
                )

        active_keys: set[tuple[str, int]] = set()
        for spec in graph.scheduler_dispatches.values():
            key = (spec.process_id, spec.process_generation)
            if key in active_keys:
                raise SchedulerDispatchError(
                    "scheduler_dispatch_process_generation_conflict"
                )
            active_keys.add(key)
