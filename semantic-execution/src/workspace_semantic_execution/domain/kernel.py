"""Pure orchestration state machine for Workspace Semantic Execution.

This module contains domain semantics only. Infrastructure adapters must live
outside the domain package.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Iterable

from .models import (
    ActionSpec,
    AuthorityDecision,
    AuthorityOutcome,
    CandidateAction,
    EffectReceipt,
    ExecutorSession,
    ExecutorSessionState,
    ProcessState,
    ReasoningProcess,
    TransitionRecord,
    ValidationResult,
    WorkContract,
    WorkDisposition,
    WorkGraph,
)
from .operator_actions import OperatorActionKernel
from .packet_sources import PacketSourceKernel
from .worker_results import WorkerResultKernel


class KernelError(RuntimeError):
    """Fail-closed domain transition error."""


TERMINAL_STATES = {
    ProcessState.COMPLETED,
    ProcessState.FAILED,
    ProcessState.AUTHORITY_BLOCKED,
}
WAIT_STATES = {
    ProcessState.WAITING_EXTERNAL,
    ProcessState.WAITING_DEPENDENCIES,
}
CLAIMABLE_STATES = {
    ProcessState.READY,
    ProcessState.READY_TO_RESUME,
}


class DomainKernel:
    """Copy-on-transition domain kernel.

    Every public transition validates a detached graph before returning it.
    Failed transitions leave the caller's graph untouched.
    """

    @classmethod
    def create_process(
        cls,
        process_id: str,
        *,
        dependencies: Iterable[str] = (),
        work_contract: WorkContract | None = None,
    ) -> ReasoningProcess:
        if not process_id:
            raise KernelError("process_id_required")
        deps = tuple(dict.fromkeys(str(x) for x in dependencies))
        if any(not dep for dep in deps):
            raise KernelError("dependency_id_required")
        if process_id in deps:
            raise KernelError("self_dependency")
        if work_contract is not None:
            cls._validate_work_contract(work_contract)
        return ReasoningProcess(
            process_id=process_id,
            dependencies=deps,
            work_contract=deepcopy(work_contract),
        )

    @classmethod
    def create_graph(
        cls,
        processes: Iterable[ReasoningProcess],
    ) -> WorkGraph:
        mapped: dict[str, ReasoningProcess] = {}
        for raw in processes:
            process = deepcopy(raw)
            if process.process_id in mapped:
                raise KernelError(f"duplicate_process:{process.process_id}")
            mapped[process.process_id] = process
        graph = WorkGraph(processes=mapped)
        cls.validate(graph)
        return graph

    @staticmethod
    def _copy(graph: WorkGraph) -> WorkGraph:
        return deepcopy(graph)

    @staticmethod
    def _process(graph: WorkGraph, process_id: str) -> ReasoningProcess:
        try:
            return graph.processes[process_id]
        except KeyError as exc:
            raise KernelError(f"unknown_process:{process_id}") from exc

    @staticmethod
    def _session(graph: WorkGraph, slot_id: str) -> ExecutorSession:
        try:
            return graph.executor_sessions[slot_id]
        except KeyError as exc:
            raise KernelError(f"unknown_session_slot:{slot_id}") from exc

    @staticmethod
    def _guard_generation(
        process: ReasoningProcess,
        expected_generation: int,
    ) -> None:
        if expected_generation != process.generation:
            raise KernelError(
                "stale_generation:"
                f"expected={expected_generation}:current={process.generation}"
            )

    @staticmethod
    def _guard_session_generation(
        session: ExecutorSession,
        expected_session_generation: int,
    ) -> None:
        if expected_session_generation != session.session_generation:
            raise KernelError(
                "stale_session_generation:"
                f"expected={expected_session_generation}:"
                f"current={session.session_generation}"
            )

    @staticmethod
    def _guard_lease(process: ReasoningProcess, lease_id: str) -> None:
        if not lease_id or process.lease_id != lease_id:
            raise KernelError("lease_mismatch")

    @staticmethod
    def _validate_work_contract(contract: WorkContract) -> None:
        if not isinstance(contract, WorkContract):
            raise KernelError("invalid_work_contract")
        if (
            not isinstance(contract.objective, str)
            or not contract.objective.strip()
        ):
            raise KernelError("work_objective_required")
        for field_name in (
            "mandatory_constraints",
            "provenance_refs",
            "authority_refs",
            "validator_contracts",
            "output_schema_refs",
        ):
            values = getattr(contract, field_name)
            if any(not isinstance(value, str) or not value.strip() for value in values):
                raise KernelError(f"work_contract_empty_value:{field_name}")
            if len(set(values)) != len(values):
                raise KernelError(f"work_contract_duplicate_value:{field_name}")

    @staticmethod
    def _merge_contract_values(
        inherited: tuple[str, ...],
        local: tuple[str, ...],
    ) -> tuple[str, ...]:
        return tuple(dict.fromkeys((*inherited, *local)))

    @classmethod
    def _merge_work_contract(
        cls,
        inherited: WorkContract,
        local: WorkContract,
    ) -> WorkContract:
        cls._validate_work_contract(inherited)
        cls._validate_work_contract(local)
        merged = WorkContract(
            objective=local.objective,
            mandatory_constraints=cls._merge_contract_values(
                inherited.mandatory_constraints,
                local.mandatory_constraints,
            ),
            provenance_refs=cls._merge_contract_values(
                inherited.provenance_refs,
                local.provenance_refs,
            ),
            authority_refs=cls._merge_contract_values(
                inherited.authority_refs,
                local.authority_refs,
            ),
            validator_contracts=cls._merge_contract_values(
                inherited.validator_contracts,
                local.validator_contracts,
            ),
            output_schema_refs=cls._merge_contract_values(
                inherited.output_schema_refs,
                local.output_schema_refs,
            ),
        )
        cls._validate_work_contract(merged)
        return merged

    @staticmethod
    def _contract_contains(
        inherited: WorkContract,
        child: WorkContract,
    ) -> bool:
        for field_name in (
            "mandatory_constraints",
            "provenance_refs",
            "authority_refs",
            "validator_contracts",
            "output_schema_refs",
        ):
            if not set(getattr(inherited, field_name)).issubset(
                set(getattr(child, field_name))
            ):
                return False
        return True

    @staticmethod
    def _clear_session_binding(session: ExecutorSession) -> None:
        session.bound_process_id = None
        session.bound_process_generation = None
        session.bound_packet_sha256 = None

    @staticmethod
    def _graph_event(
        graph: WorkGraph,
        event: str,
        **details: object,
    ) -> None:
        graph.event_seq += 1
        graph.graph_history.append(
            {"seq": graph.event_seq, "event": event, "details": deepcopy(details)}
        )

    @classmethod
    def _fence_sessions_for_process(
        cls,
        graph: WorkGraph,
        *,
        process_id: str,
        process_generation: int,
        reason: str,
    ) -> None:
        for session in graph.executor_sessions.values():
            if (
                session.state == ExecutorSessionState.BOUND
                and session.bound_process_id == process_id
                and session.bound_process_generation == process_generation
            ):
                old_generation = session.session_generation
                session.session_generation += 1
                session.session_id = None
                session.state = ExecutorSessionState.NEEDS_REPLACEMENT
                session.retirement_reason = reason
                cls._clear_session_binding(session)
                cls._graph_event(
                    graph,
                    "SESSION_FENCED_BY_PROCESS_RECOVERY",
                    slot_id=session.slot_id,
                    old_session_generation=old_generation,
                    new_session_generation=session.session_generation,
                    process_id=process_id,
                    process_generation=process_generation,
                    reason=reason,
                )

    @classmethod
    def _dependencies_satisfied(
        cls,
        graph: WorkGraph,
        process: ReasoningProcess,
    ) -> bool:
        return all(
            cls._process(graph, dependency_id).state == ProcessState.COMPLETED
            for dependency_id in process.dependencies
        )

    @staticmethod
    def _event(
        graph: WorkGraph,
        process: ReasoningProcess,
        event: str,
        **details: object,
    ) -> None:
        graph.event_seq += 1
        process.history.append(
            TransitionRecord(
                seq=graph.event_seq,
                event=event,
                state=process.state,
                generation=process.generation,
                details=deepcopy(details),
            )
        )

    @classmethod
    def claim(
        cls,
        graph: WorkGraph,
        process_id: str,
        *,
        worker_id: str,
        lease_id: str,
        expected_generation: int,
    ) -> WorkGraph:
        next_graph = cls._copy(graph)
        process = cls._process(next_graph, process_id)
        cls._guard_generation(process, expected_generation)
        if process.state not in CLAIMABLE_STATES:
            raise KernelError(f"claim_invalid_state:{process.state}")
        if process.worker_id is not None or process.lease_id is not None:
            raise KernelError("existing_lease")
        if not worker_id or not lease_id:
            raise KernelError("worker_and_lease_required")
        if not cls._dependencies_satisfied(next_graph, process):
            raise KernelError("dependencies_unsatisfied")

        process.worker_id = worker_id
        process.lease_id = lease_id
        process.state = ProcessState.CLAIMED
        cls._event(
            next_graph,
            process,
            "CLAIM",
            worker_id=worker_id,
            lease_id=lease_id,
        )
        cls.validate(next_graph)
        return next_graph

    @classmethod
    def start(
        cls,
        graph: WorkGraph,
        process_id: str,
        *,
        lease_id: str,
        expected_generation: int,
    ) -> WorkGraph:
        next_graph = cls._copy(graph)
        process = cls._process(next_graph, process_id)
        cls._guard_generation(process, expected_generation)
        cls._guard_lease(process, lease_id)
        if process.state != ProcessState.CLAIMED:
            raise KernelError(f"start_invalid_state:{process.state}")

        process.state = ProcessState.RUNNING
        cls._event(next_graph, process, "START")
        cls.validate(next_graph)
        return next_graph

    @classmethod
    def record_reasoning_quantum(
        cls,
        graph: WorkGraph,
        process_id: str,
        *,
        lease_id: str,
        expected_generation: int,
    ) -> WorkGraph:
        next_graph = cls._copy(graph)
        process = cls._process(next_graph, process_id)
        cls._guard_generation(process, expected_generation)
        cls._guard_lease(process, lease_id)
        if process.state != ProcessState.RUNNING:
            raise KernelError(f"reasoning_invalid_state:{process.state}")

        process.reasoning_quanta += 1
        cls._event(next_graph, process, "REASONING_QUANTUM")
        cls.validate(next_graph)
        return next_graph

    @classmethod
    def wait_external(
        cls,
        graph: WorkGraph,
        process_id: str,
        *,
        wait_key: str,
        lease_id: str,
        expected_generation: int,
    ) -> WorkGraph:
        next_graph = cls._copy(graph)
        process = cls._process(next_graph, process_id)
        cls._guard_generation(process, expected_generation)
        cls._guard_lease(process, lease_id)
        if process.state != ProcessState.RUNNING:
            raise KernelError(f"wait_invalid_state:{process.state}")
        if not wait_key:
            raise KernelError("wait_key_required")

        process.state = ProcessState.WAITING_EXTERNAL
        process.wait_key = wait_key
        process.worker_id = None
        process.lease_id = None
        cls._event(next_graph, process, "WAIT_EXTERNAL", wait_key=wait_key)
        cls.validate(next_graph)
        return next_graph

    @classmethod
    def wake_external(
        cls,
        graph: WorkGraph,
        process_id: str,
        *,
        wait_key: str,
        event_id: str,
    ) -> WorkGraph:
        next_graph = cls._copy(graph)
        process = cls._process(next_graph, process_id)
        if process.state != ProcessState.WAITING_EXTERNAL:
            raise KernelError(f"wake_invalid_state:{process.state}")
        if not event_id:
            raise KernelError("event_id_required")
        if process.wait_key != wait_key:
            raise KernelError("wait_key_mismatch")

        process.state = ProcessState.READY_TO_RESUME
        process.wait_key = None
        cls._event(
            next_graph,
            process,
            "WAKE_EXTERNAL",
            event_id=event_id,
        )
        cls.validate(next_graph)
        return next_graph

    @classmethod
    def classify_work(
        cls,
        graph: WorkGraph,
        process_id: str,
        *,
        disposition: WorkDisposition,
        reason: str,
        lease_id: str,
        expected_generation: int,
    ) -> WorkGraph:
        next_graph = cls._copy(graph)
        process = cls._process(next_graph, process_id)
        cls._guard_generation(process, expected_generation)
        cls._guard_lease(process, lease_id)
        if process.state != ProcessState.RUNNING:
            raise KernelError(f"classify_invalid_state:{process.state}")
        if disposition == WorkDisposition.UNCLASSIFIED:
            raise KernelError("classification_required")
        if not reason:
            raise KernelError("classification_reason_required")

        process.disposition = disposition
        process.disposition_reason = reason
        if disposition == WorkDisposition.INTRINSICALLY_DIFFICULT:
            # Classification itself cannot escalate authority. It only releases
            # the current lease so routing can select a stronger eligible
            # executor under the existing policy/authority boundary.
            process.state = ProcessState.READY_TO_RESUME
            process.worker_id = None
            process.lease_id = None

        cls._event(
            next_graph,
            process,
            "CLASSIFY_WORK",
            disposition=disposition.value,
            reason=reason,
        )
        cls.validate(next_graph)
        return next_graph

    @classmethod
    def decompose(
        cls,
        graph: WorkGraph,
        process_id: str,
        *,
        children: Iterable[ReasoningProcess],
        lease_id: str,
        expected_generation: int,
    ) -> WorkGraph:
        next_graph = cls._copy(graph)
        parent = cls._process(next_graph, process_id)
        cls._guard_generation(parent, expected_generation)
        cls._guard_lease(parent, lease_id)
        if parent.state != ProcessState.RUNNING:
            raise KernelError(f"decompose_invalid_state:{parent.state}")
        if parent.disposition == WorkDisposition.INTRINSICALLY_DIFFICULT:
            raise KernelError("intrinsically_difficult_requires_escalation")
        if (
            parent.work_contract is not None
            and parent.disposition != WorkDisposition.TOO_LARGE
        ):
            raise KernelError("contracted_decomposition_requires_too_large")

        child_values = [deepcopy(child) for child in children]
        if not child_values:
            raise KernelError("children_required")

        child_ids: list[str] = []
        for child in child_values:
            if not child.process_id:
                raise KernelError("child_process_id_required")
            if child.process_id == process_id:
                raise KernelError("self_child")
            if child.process_id in next_graph.processes:
                raise KernelError(f"duplicate_child:{child.process_id}")
            if child.state != ProcessState.READY:
                raise KernelError("new_child_must_be_ready")
            if child.generation != 0:
                raise KernelError("new_child_generation_must_be_zero")
            if child.worker_id is not None or child.lease_id is not None:
                raise KernelError("new_child_cannot_have_lease")
            if parent.work_contract is not None:
                if child.work_contract is None:
                    raise KernelError("contracted_child_requires_work_contract")
                child.work_contract = cls._merge_work_contract(
                    parent.work_contract,
                    child.work_contract,
                )
            elif child.work_contract is not None:
                cls._validate_work_contract(child.work_contract)
            child.parent_process_id = process_id
            next_graph.processes[child.process_id] = child
            child_ids.append(child.process_id)

        parent.children = tuple(
            dict.fromkeys((*parent.children, *child_ids))
        )
        parent.state = ProcessState.WAITING_DEPENDENCIES
        parent.worker_id = None
        parent.lease_id = None
        cls._event(
            next_graph,
            parent,
            "DECOMPOSE",
            children=tuple(child_ids),
        )
        cls.validate(next_graph)
        return next_graph

    @classmethod
    def refresh_dependency_waits(
        cls,
        graph: WorkGraph,
        *,
        event_id: str,
    ) -> WorkGraph:
        if not event_id:
            raise KernelError("event_id_required")
        next_graph = cls._copy(graph)
        changed = False
        for process in next_graph.processes.values():
            if process.state != ProcessState.WAITING_DEPENDENCIES:
                continue
            if not process.children:
                raise KernelError("dependency_wait_without_children")
            if all(
                cls._process(next_graph, child_id).state
                == ProcessState.COMPLETED
                for child_id in process.children
            ):
                process.state = ProcessState.READY_TO_RESUME
                # Fan-in creates a fresh reasoning boundary. The resumed
                # synthesis must be classified again rather than inheriting a
                # stale TOO_LARGE decision from before decomposition.
                process.disposition = WorkDisposition.UNCLASSIFIED
                process.disposition_reason = None
                cls._event(
                    next_graph,
                    process,
                    "DEPENDENCIES_SATISFIED",
                    event_id=event_id,
                    children=process.children,
                )
                changed = True

        if not changed:
            next_graph.event_seq += 1
            next_graph.graph_history.append(
                {
                    "seq": next_graph.event_seq,
                    "event": "DEPENDENCY_REFRESH_NOOP",
                    "details": {"event_id": event_id},
                }
            )
        cls.validate(next_graph)
        return next_graph

    @classmethod
    def register_executor_session(
        cls, graph: WorkGraph, *, slot_id: str, executor_id: str, session_id: str,
    ) -> WorkGraph:
        if not slot_id or not executor_id or not session_id:
            raise KernelError("session_identity_required")
        next_graph = cls._copy(graph)
        if slot_id in next_graph.executor_sessions:
            raise KernelError(f"duplicate_session_slot:{slot_id}")
        next_graph.executor_sessions[slot_id] = ExecutorSession(
            slot_id=slot_id, executor_id=executor_id, session_id=session_id
        )
        cls._graph_event(next_graph, "SESSION_REGISTER", slot_id=slot_id, executor_id=executor_id, session_generation=0)
        cls.validate(next_graph)
        return next_graph

    @classmethod
    def bind_executor_session(
        cls, graph: WorkGraph, *, slot_id: str, expected_session_generation: int,
        process_id: str, process_generation: int, packet_sha256: str,
    ) -> WorkGraph:
        next_graph = cls._copy(graph)
        session = cls._session(next_graph, slot_id)
        cls._guard_session_generation(session, expected_session_generation)
        process = cls._process(next_graph, process_id)
        cls._guard_generation(process, process_generation)
        if len(packet_sha256) != 64 or any(ch not in "0123456789abcdef" for ch in packet_sha256):
            raise KernelError("packet_sha256_required")
        if session.state == ExecutorSessionState.BOUND:
            if (
                session.bound_process_id == process_id
                and session.bound_process_generation == process_generation
                and session.bound_packet_sha256 == packet_sha256
            ):
                cls.validate(next_graph)
                return next_graph
            raise KernelError(f"session_not_ready:{session.state}")
        if session.state != ExecutorSessionState.READY:
            raise KernelError(f"session_not_ready:{session.state}")
        if session.session_id is None:
            raise KernelError("session_id_required")
        session.state = ExecutorSessionState.BOUND
        session.bound_process_id = process_id
        session.bound_process_generation = process_generation
        session.bound_packet_sha256 = packet_sha256
        cls._graph_event(next_graph, "SESSION_BIND", slot_id=slot_id, session_generation=session.session_generation, process_id=process_id, process_generation=process_generation, packet_sha256=packet_sha256)
        cls.validate(next_graph)
        return next_graph

    @classmethod
    def acknowledge_executor_session(
        cls, graph: WorkGraph, *, slot_id: str, expected_session_generation: int,
        process_id: str, process_generation: int, ack_id: str,
    ) -> WorkGraph:
        if not ack_id:
            raise KernelError("session_ack_id_required")
        next_graph = cls._copy(graph)
        session = cls._session(next_graph, slot_id)
        cls._guard_session_generation(session, expected_session_generation)
        if session.state != ExecutorSessionState.BOUND:
            raise KernelError(f"session_not_bound:{session.state}")
        if session.bound_process_id != process_id or session.bound_process_generation != process_generation:
            raise KernelError("session_ack_binding_mismatch")
        process = cls._process(next_graph, process_id)
        cls._guard_generation(process, process_generation)
        session.last_ack_id = ack_id
        session.last_ack_process_id = process_id
        session.last_ack_process_generation = process_generation
        session.state = ExecutorSessionState.READY
        cls._clear_session_binding(session)
        cls._graph_event(next_graph, "SESSION_ACK", slot_id=slot_id, session_generation=session.session_generation, process_id=process_id, process_generation=process_generation, ack_id=ack_id)
        cls.validate(next_graph)
        return next_graph

    @classmethod
    def invalidate_executor_session(
        cls, graph: WorkGraph, *, slot_id: str, expected_session_generation: int, reason: str,
    ) -> WorkGraph:
        if not reason:
            raise KernelError("session_retirement_reason_required")
        next_graph = cls._copy(graph)
        session = cls._session(next_graph, slot_id)
        cls._guard_session_generation(session, expected_session_generation)
        if session.state == ExecutorSessionState.RETIRED:
            raise KernelError("session_already_retired")
        old_generation = session.session_generation
        OperatorActionKernel.stale_for_session_generation(
            next_graph,
            slot_id=slot_id,
            session_generation=old_generation,
        )
        session.session_generation += 1
        session.session_id = None
        session.state = ExecutorSessionState.NEEDS_REPLACEMENT
        session.retirement_reason = reason
        cls._clear_session_binding(session)
        cls._graph_event(next_graph, "SESSION_INVALIDATE", slot_id=slot_id, old_session_generation=old_generation, new_session_generation=session.session_generation, reason=reason)
        cls.validate(next_graph)
        return next_graph

    @classmethod
    def replace_executor_session(
        cls, graph: WorkGraph, *, slot_id: str, expected_session_generation: int, session_id: str,
    ) -> WorkGraph:
        if not session_id:
            raise KernelError("session_id_required")
        next_graph = cls._copy(graph)
        session = cls._session(next_graph, slot_id)
        cls._guard_session_generation(session, expected_session_generation)
        if session.state != ExecutorSessionState.NEEDS_REPLACEMENT:
            raise KernelError(f"session_replace_invalid_state:{session.state}")
        session.session_id = session_id
        session.state = ExecutorSessionState.READY
        session.retirement_reason = None
        cls._graph_event(next_graph, "SESSION_REPLACE", slot_id=slot_id, session_generation=session.session_generation)
        cls.validate(next_graph)
        return next_graph

    @classmethod
    def retire_executor_session(
        cls, graph: WorkGraph, *, slot_id: str, expected_session_generation: int, reason: str,
    ) -> WorkGraph:
        if not reason:
            raise KernelError("session_retirement_reason_required")
        next_graph = cls._copy(graph)
        session = cls._session(next_graph, slot_id)
        cls._guard_session_generation(session, expected_session_generation)
        OperatorActionKernel.stale_for_session_generation(
            next_graph,
            slot_id=slot_id,
            session_generation=session.session_generation,
        )
        session.session_id = None
        session.state = ExecutorSessionState.RETIRED
        session.retirement_reason = reason
        cls._clear_session_binding(session)
        cls._graph_event(next_graph, "SESSION_RETIRE", slot_id=slot_id, session_generation=session.session_generation, reason=reason)
        cls.validate(next_graph)
        return next_graph

    @classmethod
    def record_effect(
        cls,
        graph: WorkGraph,
        process_id: str,
        *,
        receipt: EffectReceipt,
        lease_id: str,
        expected_generation: int,
    ) -> WorkGraph:
        next_graph = cls._copy(graph)
        process = cls._process(next_graph, process_id)
        cls._guard_generation(process, expected_generation)
        cls._guard_lease(process, lease_id)
        if process.state != ProcessState.RUNNING:
            raise KernelError(f"effect_invalid_state:{process.state}")
        if (
            process.work_contract is not None
            and process.disposition != WorkDisposition.EXECUTABLE
        ):
            raise KernelError("contracted_effect_requires_executable")
        if receipt.generation != process.generation:
            raise KernelError("receipt_generation_mismatch")
        if not all(
            (
                receipt.action_id,
                receipt.idempotency_key,
                receipt.target_ref,
                receipt.effect_hash,
                receipt.executor_id,
                receipt.observed_at,
            )
        ):
            raise KernelError("effect_receipt_fields_required")

        existing = process.effect_receipts.get(receipt.idempotency_key)
        if existing is not None:
            if existing != receipt:
                raise KernelError("conflicting_duplicate_effect")
            cls._event(
                next_graph,
                process,
                "RECORD_EFFECT_DUPLICATE_NOOP",
                idempotency_key=receipt.idempotency_key,
            )
            cls.validate(next_graph)
            return next_graph

        process.effect_receipts[receipt.idempotency_key] = receipt
        cls._event(
            next_graph,
            process,
            "RECORD_EFFECT",
            idempotency_key=receipt.idempotency_key,
        )
        cls.validate(next_graph)
        return next_graph

    @classmethod
    def propose_terminal(
        cls,
        graph: WorkGraph,
        process_id: str,
        *,
        lease_id: str,
        expected_generation: int,
    ) -> WorkGraph:
        next_graph = cls._copy(graph)
        process = cls._process(next_graph, process_id)
        cls._guard_generation(process, expected_generation)
        cls._guard_lease(process, lease_id)
        if process.state != ProcessState.RUNNING:
            raise KernelError(f"terminal_invalid_state:{process.state}")
        if not process.effect_receipts:
            raise KernelError("terminal_requires_effect_receipt")

        process.state = ProcessState.TERMINAL_CANDIDATE
        process.worker_id = None
        process.lease_id = None
        cls._event(next_graph, process, "PROPOSE_TERMINAL")
        cls.validate(next_graph)
        return next_graph

    @classmethod
    def begin_validation(
        cls,
        graph: WorkGraph,
        process_id: str,
    ) -> WorkGraph:
        next_graph = cls._copy(graph)
        process = cls._process(next_graph, process_id)
        if process.state != ProcessState.TERMINAL_CANDIDATE:
            raise KernelError(f"validation_invalid_state:{process.state}")
        if not process.effect_receipts:
            raise KernelError("validation_requires_receipt")

        process.state = ProcessState.VALIDATING
        cls._event(next_graph, process, "BEGIN_VALIDATION")
        cls.validate(next_graph)
        return next_graph

    @classmethod
    def record_validation(
        cls,
        graph: WorkGraph,
        process_id: str,
        *,
        result: ValidationResult,
    ) -> WorkGraph:
        next_graph = cls._copy(graph)
        process = cls._process(next_graph, process_id)
        if process.state != ProcessState.VALIDATING:
            raise KernelError(
                f"validation_result_invalid_state:{process.state}"
            )
        if (
            not result.validator_id
            or not result.evidence_ref
            or not result.observed_at
        ):
            raise KernelError("validation_fields_required")

        process.validations.append(result)
        if result.passed:
            if not process.effect_receipts:
                raise KernelError("complete_requires_receipt")
            process.state = ProcessState.COMPLETED
            process.repair_required = False
            cls._event(
                next_graph,
                process,
                "VALIDATION_PASS",
                evidence_ref=result.evidence_ref,
            )
        else:
            process.state = ProcessState.READY_TO_RESUME
            process.repair_required = True
            cls._event(
                next_graph,
                process,
                "VALIDATION_FAIL",
                evidence_ref=result.evidence_ref,
            )
        cls.validate(next_graph)
        return next_graph

    @classmethod
    def recover(
        cls,
        graph: WorkGraph,
        process_id: str,
        *,
        expected_generation: int,
        reason: str,
    ) -> WorkGraph:
        next_graph = cls._copy(graph)
        process = cls._process(next_graph, process_id)
        cls._guard_generation(process, expected_generation)
        if process.state in TERMINAL_STATES:
            raise KernelError(f"recover_terminal_state:{process.state}")
        if not reason:
            raise KernelError("recovery_reason_required")

        previous_state = process.state
        previous_generation = process.generation
        OperatorActionKernel.stale_for_process_generation(
            next_graph,
            process_id=process_id,
            process_generation=previous_generation,
        )
        process.generation += 1
        cls._fence_sessions_for_process(
            next_graph,
            process_id=process_id,
            process_generation=previous_generation,
            reason=f"process_recovered:{reason}",
        )
        process.worker_id = None
        process.lease_id = None

        if previous_state == ProcessState.WAITING_EXTERNAL:
            # Recovery fences ownership only. The external condition still owns
            # readiness, so the exact wait key must survive.
            process.state = ProcessState.WAITING_EXTERNAL
        elif previous_state == ProcessState.WAITING_DEPENDENCIES:
            # A restart cannot complete child work. Preserve the dependency wait.
            process.state = ProcessState.WAITING_DEPENDENCIES
        else:
            process.state = ProcessState.READY_TO_RESUME
            process.wait_key = None

        cls._event(
            next_graph,
            process,
            "RECOVER",
            reason=reason,
            previous_state=previous_state.value,
        )
        cls.validate(next_graph)
        return next_graph

    @classmethod
    def authority_block(
        cls,
        graph: WorkGraph,
        process_id: str,
        *,
        reason: str,
    ) -> WorkGraph:
        next_graph = cls._copy(graph)
        process = cls._process(next_graph, process_id)
        if process.state not in {
            ProcessState.READY,
            ProcessState.CLAIMED,
            ProcessState.RUNNING,
            ProcessState.READY_TO_RESUME,
        }:
            raise KernelError(
                f"authority_block_invalid_state:{process.state}"
            )
        if not reason:
            raise KernelError("authority_reason_required")

        process.state = ProcessState.AUTHORITY_BLOCKED
        process.worker_id = None
        process.lease_id = None
        cls._event(next_graph, process, "AUTHORITY_BLOCK", reason=reason)
        cls.validate(next_graph)
        return next_graph

    @classmethod
    def fail(
        cls,
        graph: WorkGraph,
        process_id: str,
        *,
        reason: str,
    ) -> WorkGraph:
        next_graph = cls._copy(graph)
        process = cls._process(next_graph, process_id)
        if process.state in TERMINAL_STATES:
            raise KernelError(f"fail_terminal_state:{process.state}")
        if not reason:
            raise KernelError("failure_reason_required")

        process.state = ProcessState.FAILED
        process.worker_id = None
        process.lease_id = None
        process.wait_key = None
        cls._event(next_graph, process, "FAIL", reason=reason)
        cls.validate(next_graph)
        return next_graph

    @staticmethod
    def compile_action_spec(
        candidate: CandidateAction,
        decision: AuthorityDecision,
    ) -> ActionSpec:
        if candidate.authorization_state != "UNDECIDED":
            raise KernelError("candidate_claimed_authority")
        if candidate.process_generation < 0:
            raise KernelError("candidate_generation_invalid")
        if decision.outcome != AuthorityOutcome.ALLOW:
            raise KernelError("authority_not_allow")
        if not decision.decision_id or not decision.authority_scope_ref:
            raise KernelError("authority_binding_required")
        if decision.action_id != candidate.action_id:
            raise KernelError("authority_action_mismatch")
        if decision.process_id != candidate.process_id:
            raise KernelError("authority_process_mismatch")
        if decision.process_generation != candidate.process_generation:
            raise KernelError("authority_generation_mismatch")
        if decision.target_ref != candidate.target_ref:
            raise KernelError("authority_target_mismatch")

        return ActionSpec(
            action_id=candidate.action_id,
            process_id=candidate.process_id,
            process_generation=candidate.process_generation,
            target_ref=candidate.target_ref,
            executor_type=candidate.executor_type,
            authority_decision_id=decision.decision_id,
            authority_scope_ref=decision.authority_scope_ref,
            idempotency_key=candidate.idempotency_key,
            preconditions=candidate.preconditions,
            expected_effect=candidate.expected_effect,
            postcondition_validator=candidate.postcondition_validator,
        )

    @classmethod
    def validate(cls, graph: WorkGraph) -> None:
        if graph.event_seq < 0:
            raise KernelError("invalid_event_seq")

        for process_id, process in graph.processes.items():
            if process.process_id != process_id:
                raise KernelError("process_identity_mismatch")
            if process.state not in set(ProcessState):
                raise KernelError(f"unknown_state:{process.state}")
            if process.generation < 0:
                raise KernelError("invalid_generation")
            if process.disposition not in set(WorkDisposition):
                raise KernelError(f"unknown_work_disposition:{process.disposition}")
            if (
                process.disposition == WorkDisposition.UNCLASSIFIED
                and process.disposition_reason is not None
            ):
                raise KernelError("unclassified_work_has_reason")
            if process.work_contract is not None:
                cls._validate_work_contract(process.work_contract)

            if (process.worker_id is None) != (process.lease_id is None):
                raise KernelError("partial_lease_binding")

            if process.state in WAIT_STATES | {
                ProcessState.TERMINAL_CANDIDATE,
                ProcessState.VALIDATING,
            }:
                if process.worker_id is not None or process.lease_id is not None:
                    raise KernelError("lease_present_in_nonleased_state")

            if process.state in {
                ProcessState.CLAIMED,
                ProcessState.RUNNING,
            }:
                if process.worker_id is None or process.lease_id is None:
                    raise KernelError("lease_missing_in_active_state")

            if (
                process.state == ProcessState.WAITING_EXTERNAL
                and not process.wait_key
            ):
                raise KernelError("external_wait_missing_key")
            if (
                process.state != ProcessState.WAITING_EXTERNAL
                and process.wait_key is not None
            ):
                raise KernelError("wait_key_outside_external_wait")

            if (
                process.state == ProcessState.WAITING_DEPENDENCIES
                and not process.children
            ):
                raise KernelError("dependency_wait_missing_children")

            if process.state == ProcessState.COMPLETED:
                if not process.effect_receipts:
                    raise KernelError("completed_without_effect_receipt")
                if not process.validations or not process.validations[-1].passed:
                    raise KernelError("completed_without_passing_validation")
                if not process.validations[-1].evidence_ref:
                    raise KernelError("completed_without_validation_evidence")

            for dependency_id in process.dependencies:
                if dependency_id not in graph.processes:
                    raise KernelError(f"unknown_dependency:{dependency_id}")
                if dependency_id == process_id:
                    raise KernelError("self_dependency")

            for child_id in process.children:
                if child_id not in graph.processes:
                    raise KernelError(f"unknown_child:{child_id}")
                if child_id == process_id:
                    raise KernelError("self_child")

            if process.state in TERMINAL_STATES:
                if process.worker_id is not None or process.lease_id is not None:
                    raise KernelError("terminal_state_has_lease")

        for process_id, process in graph.processes.items():
            if process.parent_process_id is None:
                continue
            parent = graph.processes.get(process.parent_process_id)
            if parent is None:
                raise KernelError("unknown_parent_process")
            if process_id not in parent.children:
                raise KernelError("parent_child_link_mismatch")
            if parent.work_contract is not None:
                if process.work_contract is None:
                    raise KernelError("contracted_child_missing_work_contract")
                if not cls._contract_contains(
                    parent.work_contract,
                    process.work_contract,
                ):
                    raise KernelError("inherited_work_contract_dropped")

        for slot_id, session in graph.executor_sessions.items():
            if session.slot_id != slot_id:
                raise KernelError("session_slot_identity_mismatch")
            if not session.slot_id or not session.executor_id:
                raise KernelError("session_identity_required")
            if session.session_generation < 0:
                raise KernelError("invalid_session_generation")
            if session.state not in set(ExecutorSessionState):
                raise KernelError(f"unknown_session_state:{session.state}")
            bound_values = (session.bound_process_id, session.bound_process_generation, session.bound_packet_sha256)
            if session.state == ExecutorSessionState.BOUND:
                if session.session_id is None:
                    raise KernelError("bound_session_missing_session_id")
                if any(value is None for value in bound_values):
                    raise KernelError("bound_session_incomplete")
                process = graph.processes.get(session.bound_process_id)
                if process is None:
                    raise KernelError("bound_session_unknown_process")
                if process.generation != session.bound_process_generation:
                    raise KernelError("bound_session_stale_process_generation")
                packet_hash = session.bound_packet_sha256 or ""
                if len(packet_hash) != 64 or any(ch not in "0123456789abcdef" for ch in packet_hash):
                    raise KernelError("bound_session_invalid_packet_hash")
                if session.retirement_reason is not None:
                    raise KernelError("bound_session_has_retirement_reason")
            elif session.state == ExecutorSessionState.READY:
                if session.session_id is None:
                    raise KernelError("ready_session_missing_session_id")
                if any(value is not None for value in bound_values):
                    raise KernelError("ready_session_has_binding")
                if session.retirement_reason is not None:
                    raise KernelError("ready_session_has_retirement_reason")
            elif session.state in {ExecutorSessionState.NEEDS_REPLACEMENT, ExecutorSessionState.RETIRED}:
                if session.session_id is not None:
                    raise KernelError("inactive_session_has_session_id")
                if any(value is not None for value in bound_values):
                    raise KernelError("inactive_session_has_binding")
                if not session.retirement_reason:
                    raise KernelError("inactive_session_missing_reason")
            ack_values = (session.last_ack_id, session.last_ack_process_id, session.last_ack_process_generation)
            if any(value is None for value in ack_values) and any(value is not None for value in ack_values):
                raise KernelError("partial_session_ack")

        OperatorActionKernel.validate_graph(graph)
        PacketSourceKernel.validate_graph(graph)
        WorkerResultKernel.validate_graph(graph)
