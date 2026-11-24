"""Persistent Instant session-loss recovery fault injection."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.adapters import (  # noqa: E402
    FakeClock,
    ImmutableWorkerResultCandidate,
    InMemoryEventLedger,
    InMemoryStateStore,
    RecordingTelemetry,
    StaticAuthorityEvaluator,
    WorkerResultCandidateAdapter,
    dumps_work_graph,
)
from workspace_semantic_execution.application import (  # noqa: E402
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
from workspace_semantic_execution.domain import (  # noqa: E402
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


PROCESS_ID = "recoverable-instant-leaf"
SLOT_ID = "instant-recovery-slot"
PROFILE = openai_chat_instant_current_profile()
VALIDATOR_ID = "validator:instant-recovery"


class PassingValidator:
    def validate(self, publication, packet_source):
        return ValidationResult(
            validator_id=VALIDATOR_ID,
            passed=True,
            evidence_ref=(
                "recovery-validation:"
                f"{publication.publication_id}"
            ),
            observed_at="T-validation",
        )


def requirement() -> ExecutionRequirement:
    return ExecutionRequirement(
        required_capabilities=frozenset({"reasoning.bounded"}),
        allowed_invocation_modes=frozenset(
            {InvocationMode.HUMAN_ASSISTED}
        ),
        allowed_session_modes=frozenset(
            {SessionMode.PERSISTENT_CHAT}
        ),
        privacy_class=PrivacyClass.INTERNAL,
        require_human_launch=True,
    )


def packet_input() -> PacketCompilationInput:
    return PacketCompilationInput(
        process_id=PROCESS_ID,
        source_checkpoint="task@recovery-checkpoint",
        objective=(
            "Complete the bounded leaf from durable state after any "
            "session replacement."
        ),
        constraints=(
            "conversation memory is optional cache only",
            "publish immutable candidate result",
        ),
        evidence_refs=("evidence:durable-recovery-input",),
        authority_refs=("scope:proposal-only",),
        allowed_actions=("publish-candidate-result",),
        validator_contract=VALIDATOR_ID,
        output_schema="WORKER_RESULT_V1",
        next_safe_boundary="publish immutable candidate JSON",
    )


def params(
    *,
    action_id: str,
    process_generation: int,
    session_generation: int,
    sequence: int,
) -> OperatorDispatchParameters:
    return OperatorDispatchParameters(
        task_id="instant-recovery",
        action_id=action_id,
        action_generation=0,
        worker_slot_id=SLOT_ID,
        session_generation=session_generation,
        priority_rank=10,
        queue_sequence=sequence,
        created_at=f"T{sequence}",
        result_publication_target_ref=(
            "github-candidate://adamtrott78/workspace-control/"
            "worker-results/candidates/"
            f"{PROCESS_ID}-g{process_generation}.json"
        ),
    )


def worker_json(planned, *, result_hash: str) -> bytes:
    contract = planned.packet_source.result_publication
    assert contract is not None
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
            "result_payload_ref": (
                "github://instant-recovery-result@immutable"
            ),
            "result_payload_sha256": result_hash,
            "evidence_refs": ["evidence:instant-recovery-output"],
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


class InstantRecoveryFaultTests(unittest.TestCase):
    def test_session_loss_stales_old_action_and_replacement_resumes_from_durable_state(self):
        runtime = RuntimeCoordinator(
            state_store=InMemoryStateStore(),
            event_ledger=InMemoryEventLedger(),
            telemetry=RecordingTelemetry(),
            clock=FakeClock(),
        )
        runtime.initialize(
            DomainKernel.create_graph(
                [DomainKernel.create_process(PROCESS_ID)]
            )
        )
        broker = PersistentExecutorSessionBroker(runtime)
        broker.ensure_session(
            profile=PROFILE,
            slot_id=SLOT_ID,
            session_id="chat-session-before-loss",
        )
        dispatcher = ExecutorDispatchCoordinator(
            runtime=runtime,
            registry=ExecutorRegistry((PROFILE,)),
            packet_compiler=SemanticPacketCompiler(),
            authority_evaluator=StaticAuthorityEvaluator(),
            executor_ports={},
            validators={},
        )

        first_result = dispatcher.dispatch(
            ExecutorDispatchRequest(
                process_id=PROCESS_ID,
                expected_generation=0,
                requirement_id="instant-recovery:first",
                requirement=requirement(),
                packet_input=packet_input(),
                operator=params(
                    action_id="action:instant-recovery:g0",
                    process_generation=0,
                    session_generation=0,
                    sequence=1,
                ),
            )
        )
        first = first_result.operator_dispatch
        self.assertIsNotNone(first)
        assert first is not None
        runtime.claim_next_operator_action(
            helper_instance_id="windows-helper",
            claim_id="claim:g0",
            claimed_at="T1",
            expires_at="T2",
        )
        runtime.record_operator_action_local_prepared(
            action_id=first.action.action_id,
            generation=0,
            worker_slot_id=SLOT_ID,
            session_generation=0,
            observed_at="T1.5",
        )

        old_candidate = ImmutableWorkerResultCandidate(
            target_ref=(
                first.packet_source.result_publication.target_ref
            ),
            immutable_revision="a" * 40,
            raw_bytes=worker_json(first, result_hash="b" * 64),
        )

        runtime.recover(
            PROCESS_ID,
            expected_generation=0,
            reason="persistent_chat_continuity_lost",
        )
        after_recovery = runtime.snapshot()
        process = after_recovery.graph.processes[PROCESS_ID]
        session = after_recovery.graph.executor_sessions[SLOT_ID]
        old_action = after_recovery.graph.operator_actions[
            first.action.action_id
        ]
        self.assertEqual(process.generation, 1)
        self.assertEqual(process.state, ProcessState.READY_TO_RESUME)
        self.assertEqual(
            session.state,
            ExecutorSessionState.NEEDS_REPLACEMENT,
        )
        self.assertEqual(session.session_generation, 1)
        self.assertEqual(old_action.status, OperatorActionState.STALE)

        version_before_late = runtime.snapshot().version
        with self.assertRaisesRegex(
            RuntimeError,
            "worker_result_action_not_awaiting_ack",
        ):
            WorkerResultCandidateAdapter(
                intake=WorkerResultIntakeService(
                    runtime=runtime,
                    validators={
                        VALIDATOR_ID: PassingValidator()
                    },
                )
            ).ingest(old_candidate)
        self.assertEqual(
            runtime.snapshot().version,
            version_before_late,
        )
        self.assertEqual(runtime.snapshot().graph.worker_results, {})

        replacement = broker.replace(
            slot_id=SLOT_ID,
            expected_session_generation=1,
            session_id="chat-session-after-loss",
        )
        self.assertEqual(
            replacement.state,
            ExecutorSessionState.READY,
        )
        self.assertEqual(replacement.session_generation, 1)

        second_result = dispatcher.dispatch(
            ExecutorDispatchRequest(
                process_id=PROCESS_ID,
                expected_generation=1,
                requirement_id="instant-recovery:replacement",
                requirement=requirement(),
                packet_input=packet_input(),
                operator=params(
                    action_id="action:instant-recovery:g1",
                    process_generation=1,
                    session_generation=1,
                    sequence=2,
                ),
            )
        )
        second = second_result.operator_dispatch
        self.assertIsNotNone(second)
        assert second is not None
        self.assertNotEqual(
            first.packet.packet_sha256,
            second.packet.packet_sha256,
            "generation/session/action binding must change the packet",
        )
        self.assertIn(
            '"process_generation": 1',
            second.packet.text,
        )
        self.assertIn(
            '"session_generation": 1',
            second.packet.text,
        )

        runtime.claim_next_operator_action(
            helper_instance_id="windows-helper",
            claim_id="claim:g1",
            claimed_at="T3",
            expires_at="T4",
        )
        runtime.record_operator_action_local_prepared(
            action_id=second.action.action_id,
            generation=0,
            worker_slot_id=SLOT_ID,
            session_generation=1,
            observed_at="T3.5",
        )
        contract = second.packet_source.result_publication
        assert contract is not None
        outcome = WorkerResultCandidateAdapter(
            intake=WorkerResultIntakeService(
                runtime=runtime,
                validators={VALIDATOR_ID: PassingValidator()},
            )
        ).ingest(
            ImmutableWorkerResultCandidate(
                target_ref=contract.target_ref,
                immutable_revision="c" * 40,
                raw_bytes=worker_json(
                    second,
                    result_hash="d" * 64,
                ),
            )
        )

        self.assertEqual(
            outcome.process_state,
            ProcessState.COMPLETED,
        )
        final = runtime.snapshot().graph
        self.assertEqual(
            final.processes[PROCESS_ID].state,
            ProcessState.COMPLETED,
        )
        self.assertEqual(
            final.operator_actions[first.action.action_id].status,
            OperatorActionState.STALE,
        )
        self.assertEqual(
            final.operator_actions[second.action.action_id].status,
            OperatorActionState.COMPLETED,
        )
        self.assertEqual(
            final.executor_sessions[SLOT_ID].state,
            ExecutorSessionState.READY,
        )
        self.assertEqual(
            final.executor_sessions[SLOT_ID].session_generation,
            1,
        )
        durable = dumps_work_graph(final)
        self.assertNotIn(first.packet.text, durable)
        self.assertNotIn(second.packet.text, durable)


if __name__ == "__main__":
    unittest.main()
