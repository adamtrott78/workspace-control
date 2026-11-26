"""Deterministic packet-source persistence and OperatorAction planning."""
from __future__ import annotations

from dataclasses import dataclass, replace

from ..domain import (
    OperatorAckMode,
    OperatorAction,
    OperatorActionState,
    OperatorActionType,
    OperatorHumanRequirement,
    OperatorPostLocalSuccess,
    SemanticPacketDecision,
    SemanticPacketFinding,
    SemanticPacketQuestion,
    SemanticPacketSource,
    WorkerResultPublicationContract,
)
from .packet_compiler import (
    CompiledPacket,
    DecisionRecord,
    FindingRecord,
    PacketCompilationInput,
    QuestionRecord,
    SemanticPacketCompiler,
)
from .router import ExecutorRegistry
from .runtime import RuntimeCoordinator
from .token_economy import (
    TokenEconomyDecision,
    TokenEconomyPlanner,
    TokenEconomyRequest,
)


def _operator_token_economy_decision(
    *,
    packet_input: PacketCompilationInput,
    executor,
    planner: TokenEconomyPlanner,
    session=None,
    expected_session_generation: int | None = None,
) -> TokenEconomyDecision:
    """Plan Operator context without trusting conversational continuity.

    DELTA is permitted only when the current durable session generation carries
    an exact ACK for a previous packet SHA. Missing/stale evidence falls back to
    REF_ONLY; a replaced session therefore cannot inherit old chat context.
    """
    ack_packet_sha = None
    if (
        session is not None
        and expected_session_generation is not None
        and session.session_generation == expected_session_generation
        and session.executor_id == executor.executor_id
        and session.last_ack_session_generation == expected_session_generation
        and session.last_ack_packet_sha256 is not None
    ):
        ack_packet_sha = session.last_ack_packet_sha256

    required_refs = tuple(
        dict.fromkeys(
            packet_input.evidence_refs
            + packet_input.authority_refs
        )
    )
    return planner.plan(
        TokenEconomyRequest(
            required_refs=required_refs,
            optional_refs=(),
            delta_refs=required_refs if ack_packet_sha is not None else (),
            base_checkpoint=(
                f"packet:{ack_packet_sha}"
                if ack_packet_sha is not None
                else packet_input.source_checkpoint
            ),
            session_has_base_checkpoint=ack_packet_sha is not None,
            recovery_required=False,
            broad_context_required=False,
            waiting_external=False,
            invocation_mode=executor.invocation_mode,
            session_mode=executor.session_mode,
            user_facing=False,
            deep_reasoning_required=False,
        )
    )


def operator_dispatch_worker_id(
    *,
    executor_id: str,
    worker_slot_id: str,
    session_generation: int,
) -> str:
    if (
        not executor_id
        or not worker_slot_id
        or session_generation < 0
    ):
        raise ValueError("operator_dispatch_worker_identity_invalid")
    return (
        f"operator:{executor_id}:{worker_slot_id}:"
        f"{session_generation}"
    )


def operator_dispatch_lease_id(
    *,
    action_id: str,
    action_generation: int,
) -> str:
    if not action_id or action_generation < 0:
        raise ValueError("operator_dispatch_lease_identity_invalid")
    return f"operator-action:{action_id}:{action_generation}"


class DurablePacketMaterializationError(RuntimeError):
    """Fail-closed durable packet reconstruction error."""


@dataclass(frozen=True)
class PlannedOperatorDispatch:
    action: OperatorAction
    packet: CompiledPacket
    packet_source: SemanticPacketSource


class DurableOperatorPacketMaterializer:
    """Rebuild packet text from durable typed source state at claim time."""

    def __init__(
        self,
        *,
        runtime: RuntimeCoordinator,
        registry: ExecutorRegistry,
        compiler: SemanticPacketCompiler | None = None,
        token_economy_planner: TokenEconomyPlanner | None = None,
    ) -> None:
        self._runtime = runtime
        self._registry = registry
        self._compiler = compiler or SemanticPacketCompiler()
        self._token_economy_planner = (
            token_economy_planner or TokenEconomyPlanner()
        )

    def materialize(self, action: OperatorAction) -> CompiledPacket:
        if action.payload_ref is None or action.payload_sha256 is None:
            raise DurablePacketMaterializationError(
                "operator_action_payload_binding_required"
            )

        graph = self._runtime.snapshot().graph
        source = graph.packet_sources.get(action.payload_ref)
        if source is None:
            raise DurablePacketMaterializationError(
                "packet_source_not_found"
            )

        expected = (
            action.reasoning_process_id,
            action.process_generation,
            action.executor_id,
            action.payload_sha256,
        )
        observed = (
            source.process_id,
            source.process_generation,
            source.executor_id,
            source.packet_sha256,
        )
        if expected != observed:
            raise DurablePacketMaterializationError(
                "packet_source_action_binding_mismatch"
            )

        process = graph.processes.get(source.process_id)
        if (
            process is None
            or process.generation != source.process_generation
        ):
            raise DurablePacketMaterializationError(
                "packet_source_stale_process_generation"
            )

        try:
            executor = self._registry.get(source.executor_id)
        except KeyError as exc:
            raise DurablePacketMaterializationError(
                "packet_source_executor_unknown"
            ) from exc

        packet_input = _compilation_input(source)
        session = (
            None
            if action.worker_slot_id is None
            else graph.executor_sessions.get(action.worker_slot_id)
        )
        economy = _operator_token_economy_decision(
            packet_input=packet_input,
            executor=executor,
            planner=self._token_economy_planner,
            session=session,
            expected_session_generation=action.session_generation,
        )
        packet = self._compiler.compile(
            packet_input,
            executor=executor,
            token_economy=economy,
        )
        if packet.packet_sha256 != source.packet_sha256:
            raise DurablePacketMaterializationError(
                "packet_source_hash_mismatch"
            )
        return packet


class OperatorDispatchPlanner:
    """Atomically bind a persistent session, packet source, and queued action."""

    def __init__(
        self,
        *,
        runtime: RuntimeCoordinator,
        registry: ExecutorRegistry,
        compiler: SemanticPacketCompiler | None = None,
        token_economy_planner: TokenEconomyPlanner | None = None,
    ) -> None:
        self._runtime = runtime
        self._registry = registry
        self._compiler = compiler or SemanticPacketCompiler()
        self._token_economy_planner = (
            token_economy_planner or TokenEconomyPlanner()
        )

    def plan_service_existing(
        self,
        *,
        task_id: str,
        action_id: str,
        action_generation: int,
        process_id: str,
        process_generation: int,
        worker_slot_id: str,
        session_generation: int,
        executor_id: str,
        packet_input: PacketCompilationInput,
        priority_rank: int,
        queue_sequence: int,
        created_at: str,
        result_publication_target_ref: str | None = None,
        result_publication_schema_ref: str = (
            "architecture/"
            "workspace-semantic-execution-worker-result.v0.1.json"
        ),
    ) -> PlannedOperatorDispatch:
        if packet_input.process_id != process_id:
            raise ValueError("packet_process_mismatch")
        if action_generation < 0:
            raise ValueError("action_generation_invalid")
        if priority_rank < 0 or queue_sequence < 0:
            raise ValueError("queue_order_invalid")
        if packet_input.result_publication is not None:
            raise ValueError(
                "result_publication_contract_owned_by_dispatch_planner"
            )

        publication_contract = None
        if result_publication_target_ref is not None:
            publication_contract = WorkerResultPublicationContract(
                publication_id=(
                    f"worker-result:{action_id}:"
                    f"{action_generation}"
                ),
                action_id=action_id,
                action_generation=action_generation,
                process_generation=process_generation,
                worker_slot_id=worker_slot_id,
                session_generation=session_generation,
                schema_ref=result_publication_schema_ref,
                target_ref=result_publication_target_ref,
                candidate_only=True,
            )
        effective_packet_input = replace(
            packet_input,
            result_publication=publication_contract,
        )

        executor = self._registry.get(executor_id)
        graph = self._runtime.snapshot().graph
        session = graph.executor_sessions.get(worker_slot_id)
        economy = _operator_token_economy_decision(
            packet_input=effective_packet_input,
            executor=executor,
            planner=self._token_economy_planner,
            session=session,
            expected_session_generation=session_generation,
        )
        packet = self._compiler.compile(
            effective_packet_input,
            executor=executor,
            token_economy=economy,
        )
        payload_ref = (
            f"semantic-packet://{process_id}/"
            f"{process_generation}/{packet.packet_sha256}"
        )
        source = _packet_source(
            payload_ref=payload_ref,
            process_generation=process_generation,
            packet=packet,
            packet_input=effective_packet_input,
        )
        action = OperatorAction(
            action_id=action_id,
            generation=action_generation,
            action_type=OperatorActionType.SERVICE_EXISTING,
            status=OperatorActionState.QUEUED,
            priority_rank=priority_rank,
            queue_sequence=queue_sequence,
            created_at=created_at,
            task_id=task_id,
            reasoning_process_id=process_id,
            process_generation=process_generation,
            worker_slot_id=worker_slot_id,
            session_generation=session_generation,
            executor_id=executor_id,
            payload_ref=payload_ref,
            payload_sha256=packet.packet_sha256,
            human_requirement=OperatorHumanRequirement.PASTE_AND_SUBMIT,
            ack_mode=OperatorAckMode.DURABLE_EVENT,
            post_local_success=OperatorPostLocalSuccess.AWAIT_DURABLE_ACK,
        )

        snapshot = self._runtime.plan_operator_dispatch(
            packet_source=source,
            action=action,
            slot_id=worker_slot_id,
            expected_session_generation=session_generation,
            process_id=process_id,
            process_generation=process_generation,
            packet_sha256=packet.packet_sha256,
            worker_id=operator_dispatch_worker_id(
                executor_id=executor_id,
                worker_slot_id=worker_slot_id,
                session_generation=session_generation,
            ),
            lease_id=operator_dispatch_lease_id(
                action_id=action_id,
                action_generation=action_generation,
            ),
        )
        persisted = snapshot.graph.operator_actions[action_id]
        if persisted != action:
            raise RuntimeError("persisted_operator_action_mismatch")

        return PlannedOperatorDispatch(
            action=persisted,
            packet=packet,
            packet_source=snapshot.graph.packet_sources[payload_ref],
        )


def _packet_source(
    *,
    payload_ref: str,
    process_generation: int,
    packet: CompiledPacket,
    packet_input: PacketCompilationInput,
) -> SemanticPacketSource:
    return SemanticPacketSource(
        payload_ref=payload_ref,
        process_id=packet_input.process_id,
        process_generation=process_generation,
        executor_id=packet.executor_id,
        packet_sha256=packet.packet_sha256,
        source_checkpoint=packet_input.source_checkpoint,
        objective=packet_input.objective,
        findings=tuple(
            SemanticPacketFinding(
                finding_id=item.finding_id,
                text=item.text,
                evidence_refs=item.evidence_refs,
            )
            for item in packet_input.findings
        ),
        decisions=tuple(
            SemanticPacketDecision(
                decision_id=item.decision_id,
                decision=item.decision,
                rationale=item.rationale,
                evidence_refs=item.evidence_refs,
                alternatives=item.alternatives,
            )
            for item in packet_input.decisions
        ),
        unresolved_questions=tuple(
            SemanticPacketQuestion(
                question_id=item.question_id,
                text=item.text,
            )
            for item in packet_input.unresolved_questions
        ),
        constraints=packet_input.constraints,
        evidence_refs=packet_input.evidence_refs,
        authority_refs=packet_input.authority_refs,
        allowed_actions=packet_input.allowed_actions,
        validator_contract=packet_input.validator_contract,
        output_schema=packet_input.output_schema,
        next_safe_boundary=packet_input.next_safe_boundary,
        result_publication=packet_input.result_publication,
    )


def _compilation_input(
    source: SemanticPacketSource,
) -> PacketCompilationInput:
    return PacketCompilationInput(
        process_id=source.process_id,
        source_checkpoint=source.source_checkpoint,
        objective=source.objective,
        findings=tuple(
            FindingRecord(
                finding_id=item.finding_id,
                text=item.text,
                evidence_refs=item.evidence_refs,
            )
            for item in source.findings
        ),
        decisions=tuple(
            DecisionRecord(
                decision_id=item.decision_id,
                decision=item.decision,
                rationale=item.rationale,
                evidence_refs=item.evidence_refs,
                alternatives=item.alternatives,
            )
            for item in source.decisions
        ),
        unresolved_questions=tuple(
            QuestionRecord(
                question_id=item.question_id,
                text=item.text,
            )
            for item in source.unresolved_questions
        ),
        constraints=source.constraints,
        evidence_refs=source.evidence_refs,
        authority_refs=source.authority_refs,
        allowed_actions=source.allowed_actions,
        validator_contract=source.validator_contract,
        output_schema=source.output_schema,
        next_safe_boundary=source.next_safe_boundary,
        result_publication=source.result_publication,
    )
