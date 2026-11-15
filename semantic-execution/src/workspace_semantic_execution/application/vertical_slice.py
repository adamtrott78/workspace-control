"""Coordinated application slice for one bounded semantic action.

This module composes already-validated domain/runtime/router/packet/authority/
executor/validator components. It intentionally owns no infrastructure-specific
state machine and introduces no execution authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol

from ..domain import (
    ActionSpec,
    AuthorityDecision,
    AuthorityOutcome,
    CandidateAction,
    EffectReceipt,
    ExecutionRequirement,
    ExecutorProfile,
    ProcessState,
    RoutingDecision,
    ValidationResult,
)
from ..ports import AuthorityEvaluatorPort, ExecutorPort, StateSnapshot
from .packet_compiler import (
    CompiledPacket,
    PacketCompilationInput,
    SemanticPacketCompiler,
)
from .router import ExecutorRegistry, route_executor
from .runtime import RuntimeCoordinator


class CoordinatedExecutionError(RuntimeError):
    """Fail-closed composition error before or during bounded execution."""


class PostconditionValidator(Protocol):
    def validate(
        self,
        action: ActionSpec,
        receipt: EffectReceipt,
    ) -> ValidationResult: ...


@dataclass(frozen=True)
class CoordinatedExecutionRequest:
    process_id: str
    worker_id: str
    lease_id: str
    expected_generation: int
    requirement_id: str
    requirement: ExecutionRequirement
    packet_input: PacketCompilationInput
    candidate_action: CandidateAction


@dataclass(frozen=True)
class CoordinatedExecutionResult:
    routing: RoutingDecision
    executor: ExecutorProfile
    packet: CompiledPacket
    authority: AuthorityDecision
    action: ActionSpec
    receipt: EffectReceipt
    validation: ValidationResult
    final_snapshot: StateSnapshot

    @property
    def completed(self) -> bool:
        return (
            self.validation.passed
            and self.final_snapshot.graph.processes[
                self.action.process_id
            ].state
            == ProcessState.COMPLETED
        )


class CoordinatedActionService:
    """Compose one routed, authority-bound, postcondition-validated action.

    Ordering is deliberate:
    1. bind request identity to current durable generation;
    2. make a deterministic routing decision;
    3. compile the worker packet from durable typed state;
    4. obtain authority from the authority-owned evaluator;
    5. compile an exact ActionSpec;
    6. claim/start through RuntimeCoordinator (the generation race fence);
    7. execute only through the selected executor's registered adapter;
    8. persist the EffectReceipt before terminal proposal;
    9. independently validate the observed postcondition;
    10. let the production kernel decide COMPLETED vs repair-ready.

    Routing and packet compilation are non-authoritative and effect-free.
    """

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
        self._authority_evaluator = authority_evaluator
        self._executor_ports = dict(executor_ports)
        self._validators = dict(validators)

    def _validate_request_identity(
        self,
        request: CoordinatedExecutionRequest,
    ) -> None:
        if not all(
            (
                request.process_id,
                request.worker_id,
                request.lease_id,
                request.requirement_id,
            )
        ):
            raise CoordinatedExecutionError("request_identity_required")
        if request.expected_generation < 0:
            raise CoordinatedExecutionError("generation_invalid")

        snapshot = self._runtime.snapshot()
        try:
            process = snapshot.graph.processes[request.process_id]
        except KeyError as exc:
            raise CoordinatedExecutionError("unknown_process") from exc

        if process.generation != request.expected_generation:
            raise CoordinatedExecutionError(
                "stale_generation:"
                f"expected={request.expected_generation}:"
                f"current={process.generation}"
            )
        if process.state not in {
            ProcessState.READY,
            ProcessState.READY_TO_RESUME,
        }:
            raise CoordinatedExecutionError(
                f"process_not_claimable:{process.state.value}"
            )

        candidate = request.candidate_action
        if candidate.process_id != request.process_id:
            raise CoordinatedExecutionError("candidate_process_mismatch")
        if candidate.process_generation != request.expected_generation:
            raise CoordinatedExecutionError("candidate_generation_mismatch")
        if request.packet_input.process_id != request.process_id:
            raise CoordinatedExecutionError("packet_process_mismatch")
        if (
            request.packet_input.source_checkpoint == ""
            or request.packet_input.objective == ""
        ):
            raise CoordinatedExecutionError("packet_identity_required")

    def execute(
        self,
        request: CoordinatedExecutionRequest,
    ) -> CoordinatedExecutionResult:
        self._validate_request_identity(request)

        routing = route_executor(
            self._registry,
            requirement_id=request.requirement_id,
            requirement=request.requirement,
        )
        if (
            routing.outcome != "SELECTED"
            or routing.selected_executor_id is None
        ):
            raise CoordinatedExecutionError("no_eligible_executor")

        executor = self._registry.get(routing.selected_executor_id)
        packet = self._packet_compiler.compile(
            request.packet_input,
            executor=executor,
        )

        decision = self._authority_evaluator.evaluate(
            request.candidate_action
        )
        if decision.outcome != AuthorityOutcome.ALLOW:
            raise CoordinatedExecutionError(
                f"authority_not_allow:{decision.outcome.value}"
            )

        # This exact compilation is the trust boundary. It independently
        # verifies process/generation/action/target bindings.
        action = self._compile_action(request, decision)

        executor_port = self._executor_ports.get(executor.executor_id)
        if executor_port is None:
            raise CoordinatedExecutionError(
                f"executor_port_missing:{executor.executor_id}"
            )
        validator = self._validators.get(action.postcondition_validator)
        if validator is None:
            raise CoordinatedExecutionError(
                f"validator_missing:{action.postcondition_validator}"
            )

        # Claim/start are deliberately after all effect-free planning. If the
        # durable generation changed meanwhile, RuntimeCoordinator/DomainKernel
        # fails closed before the executor can be invoked.
        try:
            self._runtime.claim(
                request.process_id,
                worker_id=request.worker_id,
                lease_id=request.lease_id,
                expected_generation=request.expected_generation,
            )
            self._runtime.start(
                request.process_id,
                lease_id=request.lease_id,
                expected_generation=request.expected_generation,
            )
        except RuntimeError as exc:
            raise CoordinatedExecutionError(
                f"runtime_claim_start_failed:{exc}"
            ) from exc

        receipt = executor_port.execute(
            action,
            executor=executor,
        )
        self._runtime.record_effect(
            request.process_id,
            receipt=receipt,
            lease_id=request.lease_id,
            expected_generation=request.expected_generation,
        )
        self._runtime.propose_terminal(
            request.process_id,
            lease_id=request.lease_id,
            expected_generation=request.expected_generation,
        )
        self._runtime.begin_validation(request.process_id)

        validation = validator.validate(action, receipt)
        final_snapshot = self._runtime.record_validation(
            request.process_id,
            result=validation,
        )

        return CoordinatedExecutionResult(
            routing=routing,
            executor=executor,
            packet=packet,
            authority=decision,
            action=action,
            receipt=receipt,
            validation=validation,
            final_snapshot=final_snapshot,
        )

    @staticmethod
    def _compile_action(
        request: CoordinatedExecutionRequest,
        decision: AuthorityDecision,
    ) -> ActionSpec:
        from ..domain import DomainKernel

        try:
            return DomainKernel.compile_action_spec(
                request.candidate_action,
                decision,
            )
        except RuntimeError as exc:
            raise CoordinatedExecutionError(
                f"action_compile_failed:{exc}"
            ) from exc
