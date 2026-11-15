"""Generic executor dispatch across deterministic effects and Instant Chat."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from ..domain import (
    CandidateAction,
    ExecutionRequirement,
    ExecutorProfile,
    InvocationMode,
    RoutingDecision,
)
from ..ports import (
    AuthorityEvaluatorPort,
    ExecutorPort,
)
from .operator_packets import (
    OperatorDispatchPlanner,
    PlannedOperatorDispatch,
)
from .packet_compiler import (
    PacketCompilationInput,
    SemanticPacketCompiler,
)
from .router import ExecutorRegistry, route_executor
from .runtime import RuntimeCoordinator
from .vertical_slice import (
    CoordinatedActionService,
    CoordinatedExecutionRequest,
    CoordinatedExecutionResult,
    PostconditionValidator,
)


class ExecutorDispatchError(RuntimeError):
    """Fail-closed dispatch error for an unsupported or incomplete route."""


@dataclass(frozen=True)
class OperatorDispatchParameters:
    task_id: str
    action_id: str
    action_generation: int
    worker_slot_id: str
    session_generation: int
    priority_rank: int
    queue_sequence: int
    created_at: str
    result_publication_target_ref: str
    result_publication_schema_ref: str = (
        "architecture/"
        "workspace-semantic-execution-worker-result.v0.1.json"
    )


@dataclass(frozen=True)
class ExecutorDispatchRequest:
    process_id: str
    expected_generation: int
    requirement_id: str
    requirement: ExecutionRequirement
    packet_input: PacketCompilationInput
    worker_id: str | None = None
    lease_id: str | None = None
    candidate_action: CandidateAction | None = None
    operator: OperatorDispatchParameters | None = None


@dataclass(frozen=True)
class ExecutorDispatchResult:
    routing: RoutingDecision
    executor: ExecutorProfile
    dispatch_mode: str
    coordinated_result: CoordinatedExecutionResult | None = None
    operator_dispatch: PlannedOperatorDispatch | None = None


class ExecutorDispatchCoordinator:
    """Route one durable process without model-name-specific scheduler logic."""

    def __init__(
        self,
        *,
        runtime: RuntimeCoordinator,
        registry: ExecutorRegistry,
        packet_compiler: SemanticPacketCompiler,
        authority_evaluator: AuthorityEvaluatorPort,
        executor_ports: Mapping[str, ExecutorPort],
        validators: Mapping[str, PostconditionValidator],
    ) -> None:
        self._runtime = runtime
        self._registry = registry
        self._packet_compiler = packet_compiler
        self._operator = OperatorDispatchPlanner(
            runtime=runtime,
            registry=registry,
            compiler=packet_compiler,
        )
        self._coordinated = CoordinatedActionService(
            runtime=runtime,
            registry=registry,
            packet_compiler=packet_compiler,
            authority_evaluator=authority_evaluator,
            executor_ports=executor_ports,
            validators=validators,
        )

    def dispatch(
        self,
        request: ExecutorDispatchRequest,
    ) -> ExecutorDispatchResult:
        if (
            not request.process_id
            or request.expected_generation < 0
            or request.packet_input.process_id != request.process_id
        ):
            raise ExecutorDispatchError(
                "dispatch_process_identity_invalid"
            )

        routing = route_executor(
            self._registry,
            requirement_id=request.requirement_id,
            requirement=request.requirement,
        )
        if (
            routing.outcome != "SELECTED"
            or routing.selected_executor_id is None
        ):
            raise ExecutorDispatchError("no_eligible_executor")
        executor = self._registry.get(
            routing.selected_executor_id
        )

        if executor.invocation_mode == InvocationMode.HUMAN_ASSISTED:
            params = request.operator
            if params is None:
                raise ExecutorDispatchError(
                    "operator_dispatch_parameters_required"
                )
            planned = self._operator.plan_service_existing(
                task_id=params.task_id,
                action_id=params.action_id,
                action_generation=params.action_generation,
                process_id=request.process_id,
                process_generation=request.expected_generation,
                worker_slot_id=params.worker_slot_id,
                session_generation=params.session_generation,
                executor_id=executor.executor_id,
                packet_input=request.packet_input,
                priority_rank=params.priority_rank,
                queue_sequence=params.queue_sequence,
                created_at=params.created_at,
                result_publication_target_ref=(
                    params.result_publication_target_ref
                ),
                result_publication_schema_ref=(
                    params.result_publication_schema_ref
                ),
            )
            return ExecutorDispatchResult(
                routing=routing,
                executor=executor,
                dispatch_mode="OPERATOR_ACTION",
                operator_dispatch=planned,
            )

        if executor.invocation_mode == InvocationMode.DETERMINISTIC:
            if (
                request.worker_id is None
                or request.lease_id is None
                or request.candidate_action is None
            ):
                raise ExecutorDispatchError(
                    "deterministic_execution_parameters_required"
                )
            result = self._coordinated.execute(
                CoordinatedExecutionRequest(
                    process_id=request.process_id,
                    worker_id=request.worker_id,
                    lease_id=request.lease_id,
                    expected_generation=request.expected_generation,
                    requirement_id=request.requirement_id,
                    requirement=request.requirement,
                    packet_input=request.packet_input,
                    candidate_action=request.candidate_action,
                )
            )
            if (
                result.routing.selected_executor_id
                != executor.executor_id
            ):
                raise ExecutorDispatchError(
                    "routing_replay_mismatch"
                )
            return ExecutorDispatchResult(
                routing=routing,
                executor=executor,
                dispatch_mode="DETERMINISTIC_EFFECT",
                coordinated_result=result,
            )

        raise ExecutorDispatchError(
            "selected_executor_invocation_mode_not_bound:"
            f"{executor.invocation_mode.value}"
        )
