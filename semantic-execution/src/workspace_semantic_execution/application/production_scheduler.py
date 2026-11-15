"""Production scheduler over durable typed dispatch specifications."""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

from ..domain import (
    ProcessState,
    SchedulerDispatchSpec,
    SchedulerOperatorSpec,
)
from .executor_dispatch import (
    ExecutorDispatchCoordinator,
    ExecutorDispatchRequest,
    ExecutorDispatchResult,
    OperatorDispatchParameters,
)
from .packet_compiler import (
    DecisionRecord,
    FindingRecord,
    PacketCompilationInput,
    QuestionRecord,
)
from .runtime import RuntimeCoordinator


_READY_STATES = {
    ProcessState.READY,
    ProcessState.READY_TO_RESUME,
}


class ProductionSchedulerError(RuntimeError):
    """Fail-closed production scheduler error."""


@dataclass(frozen=True)
class SchedulerTickResult:
    outcome: str
    dispatch_id: str | None = None
    process_id: str | None = None
    executor_id: str | None = None
    dispatch_mode: str | None = None
    unplanned_ready_processes: tuple[str, ...] = ()


def candidate_target_ref(operator: SchedulerOperatorSpec) -> str:
    """Canonical opaque candidate target included in the worker packet."""
    encoded_ref = quote(operator.candidate_ref, safe="")
    encoded_path = quote(operator.candidate_path, safe="/")
    return (
        f"github-candidate://{operator.candidate_repository}/"
        f"ref/{encoded_ref}/path/{encoded_path}"
    )


def _packet_input(spec: SchedulerDispatchSpec) -> PacketCompilationInput:
    packet = spec.packet
    return PacketCompilationInput(
        process_id=spec.process_id,
        source_checkpoint=packet.source_checkpoint,
        objective=packet.objective,
        findings=tuple(
            FindingRecord(
                finding_id=item.finding_id,
                text=item.text,
                evidence_refs=item.evidence_refs,
            )
            for item in packet.findings
        ),
        decisions=tuple(
            DecisionRecord(
                decision_id=item.decision_id,
                decision=item.decision,
                rationale=item.rationale,
                evidence_refs=item.evidence_refs,
                alternatives=item.alternatives,
            )
            for item in packet.decisions
        ),
        unresolved_questions=tuple(
            QuestionRecord(
                question_id=item.question_id,
                text=item.text,
            )
            for item in packet.unresolved_questions
        ),
        constraints=packet.constraints,
        evidence_refs=packet.evidence_refs,
        authority_refs=packet.authority_refs,
        allowed_actions=packet.allowed_actions,
        validator_contract=packet.validator_contract,
        output_schema=packet.output_schema,
        next_safe_boundary=packet.next_safe_boundary,
    )


def _dispatch_request(
    spec: SchedulerDispatchSpec,
) -> ExecutorDispatchRequest:
    operator = None
    if spec.operator is not None:
        operator = OperatorDispatchParameters(
            task_id=spec.operator.task_id,
            action_id=spec.operator.action_id,
            action_generation=spec.operator.action_generation,
            worker_slot_id=spec.operator.worker_slot_id,
            session_generation=spec.operator.session_generation,
            priority_rank=spec.operator.priority_rank,
            queue_sequence=spec.operator.queue_sequence,
            created_at=spec.operator.created_at,
            result_publication_target_ref=candidate_target_ref(
                spec.operator
            ),
            result_publication_schema_ref=(
                spec.operator.candidate_schema_ref
            ),
        )

    deterministic = spec.deterministic
    return ExecutorDispatchRequest(
        process_id=spec.process_id,
        expected_generation=spec.process_generation,
        requirement_id=spec.requirement_id,
        requirement=spec.requirement,
        packet_input=_packet_input(spec),
        worker_id=(
            None
            if deterministic is None
            else deterministic.worker_id
        ),
        lease_id=(
            None
            if deterministic is None
            else deterministic.lease_id
        ),
        candidate_action=(
            None
            if deterministic is None
            else deterministic.candidate_action
        ),
        operator=operator,
    )


class ProductionSchedulerService:
    """Advance at most one durable READY process per scheduler cycle."""

    def __init__(
        self,
        *,
        runtime: RuntimeCoordinator,
        dispatcher: ExecutorDispatchCoordinator,
    ) -> None:
        self._runtime = runtime
        self._dispatcher = dispatcher

    def register(
        self,
        spec: SchedulerDispatchSpec,
    ) -> None:
        self._runtime.register_scheduler_dispatch(spec)

    def run_once(self) -> SchedulerTickResult:
        graph = self._runtime.snapshot().graph
        exact_specs = {
            (spec.process_id, spec.process_generation): spec
            for spec in graph.scheduler_dispatches.values()
        }
        ready_without_plan: list[str] = []
        dispatchable: list[SchedulerDispatchSpec] = []

        for process in sorted(
            graph.processes.values(),
            key=lambda item: item.process_id,
        ):
            if process.state not in _READY_STATES:
                continue
            spec = exact_specs.get(
                (process.process_id, process.generation)
            )
            if spec is None:
                ready_without_plan.append(process.process_id)
                continue
            dispatchable.append(spec)

        if not dispatchable:
            return SchedulerTickResult(
                outcome=(
                    "UNPLANNED_READY"
                    if ready_without_plan
                    else "NO_WORK"
                ),
                unplanned_ready_processes=tuple(
                    ready_without_plan
                ),
            )

        spec = sorted(
            dispatchable,
            key=lambda item: item.dispatch_id,
        )[0]
        result: ExecutorDispatchResult = self._dispatcher.dispatch(
            _dispatch_request(spec)
        )

        if (
            result.dispatch_mode == "DETERMINISTIC_EFFECT"
            and result.coordinated_result is not None
            and result.coordinated_result.completed
        ):
            self._runtime.refresh_dependency_waits(
                event_id=(
                    "scheduler-deterministic-complete:"
                    f"{spec.dispatch_id}:"
                    f"{spec.process_generation}"
                )
            )

        return SchedulerTickResult(
            outcome="DISPATCHED",
            dispatch_id=spec.dispatch_id,
            process_id=spec.process_id,
            executor_id=result.executor.executor_id,
            dispatch_mode=result.dispatch_mode,
            unplanned_ready_processes=tuple(
                ready_without_plan
            ),
        )
