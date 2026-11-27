"""Generic executor dispatch across deterministic effects and Instant Chat."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol

from ..domain import (
    CandidateAction,
    ExecutionRequirement,
    ExecutorProfile,
    InvocationMode,
    RoutingDecision,
    TokenBudget,
    WorkDisposition,
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
    CompiledPacket,
    PacketCompilationInput,
    SemanticPacketCompiler,
)
from .router import ExecutorRegistry, route_executor
from .runtime import RuntimeCoordinator
from .token_economy import (
    TokenEconomyDecision,
    TokenEconomyPlanner,
    TokenEconomyRequest,
)
from .vertical_slice import (
    CoordinatedActionService,
    CoordinatedExecutionRequest,
    CoordinatedExecutionResult,
    PostconditionValidator,
)


@dataclass(frozen=True)
class ExecutorSelectionPolicyDecision:
    selected_executor_id: str | None
    outcome: str
    rationale: str


class ProgrammaticReasoningPort(Protocol):
    def execute(
        self,
        *,
        packet: CompiledPacket,
        executor: ExecutorProfile,
        budget: TokenBudget,
    ) -> object: ...


class ExecutorSelectionPolicy(Protocol):
    def select(
        self,
        *,
        requirement_id: str,
        eligible_profiles: tuple[ExecutorProfile, ...],
        base_routing: RoutingDecision,
        disposition: WorkDisposition,
    ) -> ExecutorSelectionPolicyDecision: ...


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
class ProgrammaticDispatchResult:
    packet: CompiledPacket
    token_economy: TokenEconomyDecision
    executor_result: object


@dataclass(frozen=True)
class ExecutorDispatchResult:
    routing: RoutingDecision
    executor: ExecutorProfile
    dispatch_mode: str
    coordinated_result: CoordinatedExecutionResult | None = None
    operator_dispatch: PlannedOperatorDispatch | None = None
    programmatic_dispatch: ProgrammaticDispatchResult | None = None
    selection_policy: ExecutorSelectionPolicyDecision | None = None


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
        selection_policy: ExecutorSelectionPolicy | None = None,
        programmatic_ports: Mapping[str, ProgrammaticReasoningPort] | None = None,
        token_economy_planner: TokenEconomyPlanner | None = None,
    ) -> None:
        self._runtime = runtime
        self._registry = registry
        self._packet_compiler = packet_compiler
        self._selection_policy = selection_policy
        self._programmatic_ports = dict(programmatic_ports or {})
        self._token_economy_planner = (
            token_economy_planner or TokenEconomyPlanner()
        )
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

        base_routing = route_executor(
            self._registry,
            requirement_id=request.requirement_id,
            requirement=request.requirement,
        )
        if (
            base_routing.outcome != "SELECTED"
            or base_routing.selected_executor_id is None
        ):
            raise ExecutorDispatchError("no_eligible_executor")

        routing = base_routing
        policy_decision = None
        if self._selection_policy is not None:
            graph = self._runtime.snapshot().graph
            process = graph.processes.get(request.process_id)
            if process is None:
                raise ExecutorDispatchError(
                    "selection_policy_process_unknown"
                )
            if process.generation != request.expected_generation:
                raise ExecutorDispatchError(
                    "selection_policy_stale_process_generation"
                )
            eligible_profiles = tuple(
                self._registry.get(executor_id)
                for executor_id
                in base_routing.eligible_executor_ids
            )
            policy_decision = self._selection_policy.select(
                requirement_id=request.requirement_id,
                eligible_profiles=eligible_profiles,
                base_routing=base_routing,
                disposition=process.disposition,
            )
            selected = policy_decision.selected_executor_id
            if selected is None:
                raise ExecutorDispatchError(
                    "selection_policy_denied:"
                    f"{policy_decision.outcome}"
                )
            if selected not in base_routing.eligible_executor_ids:
                raise ExecutorDispatchError(
                    "selection_policy_selected_ineligible_executor"
                )
            routing = RoutingDecision(
                requirement_id=base_routing.requirement_id,
                selected_executor_id=selected,
                eligible_executor_ids=(
                    base_routing.eligible_executor_ids
                ),
                exclusions=base_routing.exclusions,
                outcome="SELECTED",
                rationale=(
                    base_routing.rationale
                    + " Selection policy: "
                    + policy_decision.rationale
                ),
            )

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
                selection_policy=policy_decision,
            )

        if executor.invocation_mode == InvocationMode.PROGRAMMATIC:
            graph = self._runtime.snapshot().graph
            process = graph.processes.get(request.process_id)
            if process is None:
                raise ExecutorDispatchError(
                    "programmatic_process_unknown"
                )
            if process.generation != request.expected_generation:
                raise ExecutorDispatchError(
                    "programmatic_stale_process_generation"
                )

            required_refs = tuple(
                dict.fromkeys(
                    request.packet_input.evidence_refs
                    + request.packet_input.authority_refs
                )
            )
            economy = self._token_economy_planner.plan(
                TokenEconomyRequest(
                    required_refs=required_refs,
                    base_checkpoint=request.packet_input.source_checkpoint,
                    waiting_external=(
                        process.state.value == "WAITING_EXTERNAL"
                    ),
                    invocation_mode=executor.invocation_mode,
                    session_mode=executor.session_mode,
                    user_facing=False,
                    deep_reasoning_required=(
                        process.disposition
                        == WorkDisposition.INTRINSICALLY_DIFFICULT
                    ),
                )
            )
            if not economy.budget.allow_model_call:
                raise ExecutorDispatchError(
                    "programmatic_model_call_forbidden_by_token_budget"
                )
            packet = self._packet_compiler.compile(
                request.packet_input,
                executor=executor,
                token_economy=economy,
            )
            port = self._programmatic_ports.get(executor.executor_id)
            if port is None:
                raise ExecutorDispatchError(
                    "programmatic_executor_port_missing:"
                    f"{executor.executor_id}"
                )
            executor_result = port.execute(
                packet=packet,
                executor=executor,
                budget=economy.budget,
            )
            return ExecutorDispatchResult(
                routing=routing,
                executor=executor,
                dispatch_mode="PROGRAMMATIC_MODEL",
                programmatic_dispatch=ProgrammaticDispatchResult(
                    packet=packet,
                    token_economy=economy,
                    executor_result=executor_result,
                ),
                selection_policy=policy_decision,
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
                selection_policy=policy_decision,
            )

        raise ExecutorDispatchError(
            "selected_executor_invocation_mode_not_bound:"
            f"{executor.invocation_mode.value}"
        )
