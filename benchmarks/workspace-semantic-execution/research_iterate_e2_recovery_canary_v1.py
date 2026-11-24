"""E2 deterministic durable-recovery canary.

This canary deliberately loses:
1. the worker/process ownership generation,
2. the persistent Instant session generation, and
3. the in-memory RuntimeCoordinator instance.

Correctness must come entirely from durable typed state. A late result from the
retired generation must be rejected without mutation, and a replacement
session must finish the same logical leaf from reconstructed packet state.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from workspace_semantic_execution.adapters import (
    FakeClock,
    ImmutableWorkerResultCandidate,
    InMemoryEventLedger,
    InMemoryStateStore,
    RecordingTelemetry,
    StaticAuthorityEvaluator,
    WorkerResultCandidateAdapter,
    dumps_work_graph,
)
from workspace_semantic_execution.application import (
    ExecutorDispatchCoordinator,
    ExecutorDispatchRequest,
    ExecutorRegistry,
    OperatorDispatchParameters,
    PacketCompilationInput,
    PersistentExecutorSessionBroker,
    RuntimeCoordinator,
    SemanticPacketCompiler,
    WorkerResultIntakeService,
    openai_chat_instant_current_profile,
)
from workspace_semantic_execution.domain import (
    DomainKernel,
    ExecutionRequirement,
    ExecutorSessionState,
    InvocationMode,
    OperatorActionState,
    PrivacyClass,
    ProcessState,
    SessionMode,
    ValidationResult,
)


PROCESS_ID = "research-iterate-e2.recoverable-instant-leaf"
SLOT_ID = "research-iterate-e2.instant-slot"
PROFILE = openai_chat_instant_current_profile()
VALIDATOR_ID = "validator:research-iterate-e2-recovery-v1"


class E2RecoveryError(RuntimeError):
    pass


class PassingValidator:
    def validate(self, publication, packet_source):
        return ValidationResult(
            validator_id=VALIDATOR_ID,
            passed=True,
            evidence_ref=f"e2-recovery:{publication.publication_id}",
            observed_at="T-validation",
        )


def _requirement() -> ExecutionRequirement:
    return ExecutionRequirement(
        required_capabilities=frozenset({"reasoning.bounded"}),
        allowed_invocation_modes=frozenset({InvocationMode.HUMAN_ASSISTED}),
        allowed_session_modes=frozenset({SessionMode.PERSISTENT_CHAT}),
        privacy_class=PrivacyClass.INTERNAL,
        require_human_launch=True,
    )


def _packet_input() -> PacketCompilationInput:
    return PacketCompilationInput(
        process_id=PROCESS_ID,
        source_checkpoint="research-iterate-e2@durable-recovery",
        objective=(
            "Complete the bounded recovery leaf from typed durable state. "
            "Conversation memory is optional cache only."
        ),
        constraints=(
            "publish immutable candidate result",
            "do not reconstruct state from human relay",
            "stale generations must not mutate durable state",
        ),
        evidence_refs=("e2:durable-recovery-input",),
        authority_refs=("scope:proposal-only",),
        allowed_actions=("publish-candidate-result",),
        validator_contract=VALIDATOR_ID,
        output_schema="WORKER_RESULT_V1",
        next_safe_boundary="publish immutable candidate JSON",
    )


def _params(*, action_id: str, process_generation: int, session_generation: int, sequence: int) -> OperatorDispatchParameters:
    return OperatorDispatchParameters(
        task_id="workspace-semantic-execution-migration-v1",
        action_id=action_id,
        action_generation=0,
        worker_slot_id=SLOT_ID,
        session_generation=session_generation,
        priority_rank=10,
        queue_sequence=sequence,
        created_at=f"T{sequence}",
        result_publication_target_ref=(
            "github-candidate://adamtrott78/workspace-control/"
            "worker-results/e2/recovery/"
            f"{PROCESS_ID}-g{process_generation}.json"
        ),
    )


def _worker_json(planned, *, result_hash: str) -> bytes:
    contract = planned.packet_source.result_publication
    if contract is None:
        raise E2RecoveryError("missing_result_publication_contract")
    return json.dumps(
        {
            "publication_id": contract.publication_id,
            "action_id": planned.action.action_id,
            "action_generation": planned.action.generation,
            "process_id": PROCESS_ID,
            "process_generation": planned.action.process_generation,
            "executor_id": PROFILE.executor_id,
            "worker_slot_id": SLOT_ID,
            "session_generation": planned.action.session_generation,
            "packet_sha256": planned.packet.packet_sha256,
            "kind": "RESULT",
            "observed_at": "T-worker",
            "result_payload_ref": "e2://durable-recovery/result",
            "result_payload_sha256": result_hash,
            "evidence_refs": ["e2:replacement-worker-output"],
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _dispatcher(runtime: RuntimeCoordinator) -> ExecutorDispatchCoordinator:
    return ExecutorDispatchCoordinator(
        runtime=runtime,
        registry=ExecutorRegistry((PROFILE,)),
        packet_compiler=SemanticPacketCompiler(),
        authority_evaluator=StaticAuthorityEvaluator(),
        executor_ports={},
        validators={},
    )


def run_e2_recovery_canary() -> dict[str, object]:
    state_store = InMemoryStateStore()
    event_ledger = InMemoryEventLedger()
    telemetry = RecordingTelemetry()
    clock = FakeClock()

    runtime1 = RuntimeCoordinator(
        state_store=state_store,
        event_ledger=event_ledger,
        telemetry=telemetry,
        clock=clock,
    )
    runtime1.initialize(
        DomainKernel.create_graph([DomainKernel.create_process(PROCESS_ID)])
    )
    broker1 = PersistentExecutorSessionBroker(runtime1)
    broker1.ensure_session(
        profile=PROFILE,
        slot_id=SLOT_ID,
        session_id="e2-chat-before-loss",
    )

    first_result = _dispatcher(runtime1).dispatch(
        ExecutorDispatchRequest(
            process_id=PROCESS_ID,
            expected_generation=0,
            requirement_id="e2:recovery:first",
            requirement=_requirement(),
            packet_input=_packet_input(),
            operator=_params(
                action_id="action:e2:recovery:g0",
                process_generation=0,
                session_generation=0,
                sequence=1,
            ),
        )
    )
    first = first_result.operator_dispatch
    if first is None:
        raise E2RecoveryError("first_operator_dispatch_missing")

    runtime1.claim_next_operator_action(
        helper_instance_id="windows-helper-e2",
        claim_id="claim:e2:g0",
        claimed_at="T1",
        expires_at="T2",
    )
    runtime1.record_operator_action_local_prepared(
        action_id=first.action.action_id,
        generation=0,
        worker_slot_id=SLOT_ID,
        session_generation=0,
        observed_at="T1.5",
    )

    old_candidate = ImmutableWorkerResultCandidate(
        target_ref=first.packet_source.result_publication.target_ref,
        immutable_revision="a" * 40,
        raw_bytes=_worker_json(first, result_hash="b" * 64),
    )

    recovered = runtime1.recover(
        PROCESS_ID,
        expected_generation=0,
        reason="e2_injected_worker_process_loss",
    )
    recovered_process = recovered.graph.processes[PROCESS_ID]
    recovered_session = recovered.graph.executor_sessions[SLOT_ID]
    recovered_action = recovered.graph.operator_actions[first.action.action_id]
    if recovered_process.generation != 1:
        raise E2RecoveryError("process_generation_not_advanced")
    if recovered_process.state != ProcessState.READY_TO_RESUME:
        raise E2RecoveryError("process_not_ready_to_resume")
    if recovered_session.state != ExecutorSessionState.NEEDS_REPLACEMENT:
        raise E2RecoveryError("session_not_fenced")
    if recovered_session.session_generation != 1:
        raise E2RecoveryError("session_generation_not_advanced")
    if recovered_action.status != OperatorActionState.STALE:
        raise E2RecoveryError("old_action_not_staled")

    version_before_late = runtime1.snapshot().version
    stale_rejected = False
    try:
        WorkerResultCandidateAdapter(
            intake=WorkerResultIntakeService(
                runtime=runtime1,
                validators={VALIDATOR_ID: PassingValidator()},
            )
        ).ingest(old_candidate)
    except RuntimeError:
        stale_rejected = True
    if not stale_rejected:
        raise E2RecoveryError("late_old_candidate_not_rejected")
    if runtime1.snapshot().version != version_before_late:
        raise E2RecoveryError("late_old_candidate_mutated_state")
    if runtime1.snapshot().graph.worker_results:
        raise E2RecoveryError("late_old_candidate_persisted")

    # Deliberately discard runtime/broker/dispatcher objects. Only durable ports survive.
    runtime2 = RuntimeCoordinator(
        state_store=state_store,
        event_ledger=event_ledger,
        telemetry=telemetry,
        clock=clock,
    )
    rehydrated = runtime2.snapshot()
    process_after_restart = rehydrated.graph.processes[PROCESS_ID]
    session_after_restart = rehydrated.graph.executor_sessions[SLOT_ID]
    if process_after_restart.generation != 1:
        raise E2RecoveryError("restart_lost_process_generation")
    if process_after_restart.state != ProcessState.READY_TO_RESUME:
        raise E2RecoveryError("restart_lost_process_state")
    if session_after_restart.session_generation != 1:
        raise E2RecoveryError("restart_lost_session_generation")
    if session_after_restart.state != ExecutorSessionState.NEEDS_REPLACEMENT:
        raise E2RecoveryError("restart_lost_session_state")

    broker2 = PersistentExecutorSessionBroker(runtime2)
    replacement = broker2.replace(
        slot_id=SLOT_ID,
        expected_session_generation=1,
        session_id="e2-chat-after-loss",
    )
    if replacement.state != ExecutorSessionState.READY:
        raise E2RecoveryError("replacement_session_not_ready")

    second_result = _dispatcher(runtime2).dispatch(
        ExecutorDispatchRequest(
            process_id=PROCESS_ID,
            expected_generation=1,
            requirement_id="e2:recovery:replacement",
            requirement=_requirement(),
            packet_input=_packet_input(),
            operator=_params(
                action_id="action:e2:recovery:g1",
                process_generation=1,
                session_generation=1,
                sequence=2,
            ),
        )
    )
    second = second_result.operator_dispatch
    if second is None:
        raise E2RecoveryError("replacement_operator_dispatch_missing")
    if first.packet.packet_sha256 == second.packet.packet_sha256:
        raise E2RecoveryError("replacement_packet_did_not_rebind_generation")
    if '"process_generation": 1' not in second.packet.text:
        raise E2RecoveryError("replacement_packet_missing_process_generation")
    if '"session_generation": 1' not in second.packet.text:
        raise E2RecoveryError("replacement_packet_missing_session_generation")

    runtime2.claim_next_operator_action(
        helper_instance_id="windows-helper-e2",
        claim_id="claim:e2:g1",
        claimed_at="T3",
        expires_at="T4",
    )
    runtime2.record_operator_action_local_prepared(
        action_id=second.action.action_id,
        generation=0,
        worker_slot_id=SLOT_ID,
        session_generation=1,
        observed_at="T3.5",
    )
    contract = second.packet_source.result_publication
    if contract is None:
        raise E2RecoveryError("replacement_result_publication_missing")
    outcome = WorkerResultCandidateAdapter(
        intake=WorkerResultIntakeService(
            runtime=runtime2,
            validators={VALIDATOR_ID: PassingValidator()},
        )
    ).ingest(
        ImmutableWorkerResultCandidate(
            target_ref=contract.target_ref,
            immutable_revision="c" * 40,
            raw_bytes=_worker_json(second, result_hash="d" * 64),
        )
    )
    if outcome.process_state != ProcessState.COMPLETED:
        raise E2RecoveryError("replacement_result_not_completed")

    runtime3 = RuntimeCoordinator(
        state_store=state_store,
        event_ledger=event_ledger,
        telemetry=telemetry,
        clock=clock,
    )
    final = runtime3.snapshot().graph
    if final.processes[PROCESS_ID].state != ProcessState.COMPLETED:
        raise E2RecoveryError("final_rehydration_not_completed")
    if final.operator_actions[first.action.action_id].status != OperatorActionState.STALE:
        raise E2RecoveryError("final_old_action_not_stale")
    if final.operator_actions[second.action.action_id].status != OperatorActionState.COMPLETED:
        raise E2RecoveryError("final_replacement_action_not_completed")
    if final.executor_sessions[SLOT_ID].state != ExecutorSessionState.READY:
        raise E2RecoveryError("final_session_not_ready")
    if final.executor_sessions[SLOT_ID].session_generation != 1:
        raise E2RecoveryError("final_session_generation_mismatch")

    durable = dumps_work_graph(final)
    if first.packet.text in durable or second.packet.text in durable:
        raise E2RecoveryError("chat_packet_leaked_into_durable_graph")

    return {
        "schema": "workspace-semantic-research-iterate-e2-recovery-canary.v1",
        "result": "PASS",
        "worker_process_loss_injected": True,
        "process_generation": {"before": 0, "after": 1},
        "session_loss_injected": True,
        "session_generation": {"before": 0, "after": 1},
        "old_operator_action_staled": True,
        "late_old_candidate_rejected_without_mutation": True,
        "orchestrator_runtime_restarted": True,
        "durable_state_rehydrated_without_chat_memory": True,
        "replacement_session_created": True,
        "replacement_packet_recompiled_from_typed_state": True,
        "replacement_worker_completed": True,
        "final_rehydration_completed": True,
        "manual_state_relay": False,
        "chat_transcript_in_durable_graph": False,
    }


def main() -> int:
    print(json.dumps(run_e2_recovery_canary(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
