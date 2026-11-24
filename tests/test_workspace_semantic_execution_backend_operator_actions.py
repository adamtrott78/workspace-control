"""Durable OperatorAction lifecycle and backend transport-contract tests."""
from __future__ import annotations

from dataclasses import fields, replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.adapters import (  # noqa: E402
    FakeClock,
    InMemoryEventLedger,
    InMemoryStateStore,
    RecordingTelemetry,
    dumps_work_graph,
    loads_work_graph,
)
from workspace_semantic_execution.application import (  # noqa: E402
    OperatorActionService,
    PacketCompilationInput,
    PersistentExecutorSessionBroker,
    RuntimeCoordinator,
    SemanticPacketCompiler,
    openai_chat_instant_current_profile,
)
from workspace_semantic_execution.domain import (  # noqa: E402
    DomainKernel,
    OperatorAckMode,
    OperatorAction,
    OperatorActionState,
    OperatorActionType,
    OperatorHumanRequirement,
    OperatorPostLocalSuccess,
)
from workspace_semantic_execution.domain.operator_actions import (  # noqa: E402
    OperatorActionError,
)


PROCESS_ID = "instant-leaf"
SLOT_ID = "instant-slot-1"
EXECUTOR = openai_chat_instant_current_profile()


def packet():
    return SemanticPacketCompiler().compile(
        PacketCompilationInput(
            process_id=PROCESS_ID,
            source_checkpoint="task@sha",
            objective="Perform one bounded semantic worker leaf.",
            constraints=("manual paste and submit only",),
            evidence_refs=("evidence:durable",),
            authority_refs=("scope:proposal-only",),
            allowed_actions=("report-result",),
            validator_contract="validator:typed-result-v1",
            next_safe_boundary="return typed result and durable evidence",
        ),
        executor=EXECUTOR,
    )


def runtime():
    coordinator = RuntimeCoordinator(
        state_store=InMemoryStateStore(),
        event_ledger=InMemoryEventLedger(),
        telemetry=RecordingTelemetry(),
        clock=FakeClock(),
    )
    coordinator.initialize(
        DomainKernel.create_graph(
            [DomainKernel.create_process(PROCESS_ID)]
        )
    )
    broker = PersistentExecutorSessionBroker(coordinator)
    compiled = packet()
    broker.ensure_session(
        profile=EXECUTOR,
        slot_id=SLOT_ID,
        session_id="chat-session-a",
    )
    broker.bind(
        profile=EXECUTOR,
        slot_id=SLOT_ID,
        expected_session_generation=0,
        process_id=PROCESS_ID,
        process_generation=0,
        packet_sha256=compiled.packet_sha256,
    )
    return coordinator, broker, compiled


def service_action(
    *,
    action_id: str = "action:instant-leaf",
    priority_rank: int = 10,
    queue_sequence: int = 1,
    compiled=None,
):
    compiled = compiled or packet()
    return OperatorAction(
        action_id=action_id,
        generation=0,
        action_type=OperatorActionType.SERVICE_EXISTING,
        status=OperatorActionState.QUEUED,
        priority_rank=priority_rank,
        queue_sequence=queue_sequence,
        created_at="2026-11-15T16:00:00Z",
        task_id="workspace-semantic-execution-november-integration-plan-v1",
        reasoning_process_id=PROCESS_ID,
        process_generation=0,
        worker_slot_id=SLOT_ID,
        session_generation=0,
        executor_id=EXECUTOR.executor_id,
        payload_ref=f"semantic-packet://{PROCESS_ID}/0",
        payload_sha256=compiled.packet_sha256,
        human_requirement=OperatorHumanRequirement.PASTE_AND_SUBMIT,
        ack_mode=OperatorAckMode.DURABLE_EVENT,
        post_local_success=OperatorPostLocalSuccess.AWAIT_DURABLE_ACK,
    )


class StaticMaterializer:
    def __init__(self, compiled):
        self.compiled = compiled
        self.calls = 0

    def materialize(self, action):
        self.calls += 1
        return self.compiled


class OperatorActionLifecycleTests(unittest.TestCase):
    def test_service_action_claim_revalidate_prepare_ack_complete(self):
        coordinator, broker, compiled = runtime()
        materializer = StaticMaterializer(compiled)
        service = OperatorActionService(
            runtime=coordinator,
            packet_materializer=materializer,
        )
        action = service.enqueue(service_action(compiled=compiled))

        status = service.workload_status()
        self.assertEqual(status.ready_manual_cycles, 1)
        self.assertEqual(status.sent_unconfirmed, 0)
        self.assertEqual(action.status, OperatorActionState.QUEUED)

        claimed = service.claim_next(
            helper_instance_id="windows-helper-1",
            claim_id="claim-1",
            claimed_at="2026-11-15T16:00:01Z",
            expires_at="2026-11-15T16:00:31Z",
        )
        self.assertIsNotNone(claimed)
        assert claimed is not None
        self.assertEqual(claimed.action.action_id, action.action_id)
        self.assertEqual(claimed.packet_text, compiled.text)
        self.assertEqual(materializer.calls, 1)
        self.assertTrue(
            service.revalidate(
                action_id=action.action_id,
                generation=0,
                worker_slot_id=SLOT_ID,
                session_generation=0,
            )
        )

        prepared = service.record_local_prepared(
            action_id=action.action_id,
            generation=0,
            worker_slot_id=SLOT_ID,
            session_generation=0,
            observed_at="2026-11-15T16:00:03Z",
        )
        self.assertEqual(
            prepared.status,
            OperatorActionState.AWAITING_DURABLE_ACK,
        )
        status = service.workload_status()
        self.assertEqual(status.ready_manual_cycles, 0)
        self.assertEqual(status.sent_unconfirmed, 1)

        # Durable worker/session acknowledgment is authoritative and can clear
        # the session binding before the OperatorAction observer completes it.
        broker.acknowledge(
            slot_id=SLOT_ID,
            expected_session_generation=0,
            process_id=PROCESS_ID,
            process_generation=0,
            ack_id="worker-ack-1",
        )
        completed = service.record_durable_ack(
            action_id=action.action_id,
            generation=0,
            ack_id="worker-ack-1",
            completed_at="2026-11-15T16:00:05Z",
        )
        self.assertEqual(completed.status, OperatorActionState.COMPLETED)
        self.assertEqual(completed.durable_ack_id, "worker-ack-1")
        self.assertEqual(service.workload_status().sent_unconfirmed, 0)

    def test_claim_order_is_priority_then_sequence_then_action_id(self):
        coordinator = RuntimeCoordinator(
            state_store=InMemoryStateStore(),
            event_ledger=InMemoryEventLedger(),
            telemetry=RecordingTelemetry(),
            clock=FakeClock(),
        )
        coordinator.initialize(
            DomainKernel.create_graph(
                [DomainKernel.create_process("local")]
            )
        )
        service = OperatorActionService(runtime=coordinator)

        def local(action_id, priority, sequence):
            return OperatorAction(
                action_id=action_id,
                generation=0,
                action_type=OperatorActionType.OPEN_RECOVERY,
                status=OperatorActionState.QUEUED,
                priority_rank=priority,
                queue_sequence=sequence,
                created_at="T0",
                task_id="task",
                reasoning_process_id="local",
                process_generation=0,
                worker_slot_id=None,
                session_generation=None,
                executor_id=None,
                payload_ref=None,
                payload_sha256=None,
                human_requirement=OperatorHumanRequirement.RECOVERY_INTERACTION,
                ack_mode=OperatorAckMode.NONE,
                post_local_success=OperatorPostLocalSuccess.COMPLETE_AND_REQUERY,
            )

        service.enqueue(local("later-priority", 20, 1))
        service.enqueue(local("same-b", 10, 2))
        service.enqueue(local("same-a", 10, 2))
        service.enqueue(local("first", 10, 1))

        claimed = service.claim_next(
            helper_instance_id="helper",
            claim_id="claim",
            claimed_at="T1",
            expires_at="T2",
        )
        assert claimed is not None
        self.assertEqual(claimed.action.action_id, "first")

    def test_process_recovery_stales_queued_action(self):
        coordinator, _broker, compiled = runtime()
        service = OperatorActionService(runtime=coordinator)
        action = service.enqueue(service_action(compiled=compiled))

        coordinator.recover(
            PROCESS_ID,
            expected_generation=0,
            reason="worker/session recovery",
        )

        stale = coordinator.snapshot().graph.operator_actions[action.action_id]
        self.assertEqual(stale.status, OperatorActionState.STALE)
        self.assertEqual(service.workload_status().ready_manual_cycles, 0)

    def test_session_invalidation_stales_claimed_action(self):
        coordinator, broker, compiled = runtime()
        service = OperatorActionService(
            runtime=coordinator,
            packet_materializer=StaticMaterializer(compiled),
        )
        action = service.enqueue(service_action(compiled=compiled))
        service.claim_next(
            helper_instance_id="helper",
            claim_id="claim",
            claimed_at="T1",
            expires_at="T2",
        )

        broker.invalidate(
            slot_id=SLOT_ID,
            expected_session_generation=0,
            reason="auth_lost",
        )

        stale = coordinator.snapshot().graph.operator_actions[action.action_id]
        self.assertEqual(stale.status, OperatorActionState.STALE)
        self.assertFalse(
            service.revalidate(
                action_id=action.action_id,
                generation=0,
                worker_slot_id=SLOT_ID,
                session_generation=0,
            )
        )

    def test_packet_text_is_ephemeral_not_durable_operator_state(self):
        coordinator, _broker, compiled = runtime()
        service = OperatorActionService(
            runtime=coordinator,
            packet_materializer=StaticMaterializer(compiled),
        )
        action = service.enqueue(service_action(compiled=compiled))
        claimed = service.claim_next(
            helper_instance_id="helper",
            claim_id="claim",
            claimed_at="T1",
            expires_at="T2",
        )
        assert claimed is not None
        self.assertEqual(claimed.packet_text, compiled.text)

        durable = coordinator.snapshot().graph.operator_actions[action.action_id]
        self.assertFalse(
            any(field.name == "packet_text" for field in fields(durable))
        )
        encoded = dumps_work_graph(coordinator.snapshot().graph)
        self.assertNotIn(compiled.text, encoded)
        self.assertEqual(
            loads_work_graph(encoded),
            coordinator.snapshot().graph,
        )

    def test_mismatched_packet_hash_fails_closed_before_helper_receives_packet(self):
        coordinator, _broker, compiled = runtime()
        wrong = replace(compiled, packet_sha256="f" * 64)
        service = OperatorActionService(
            runtime=coordinator,
            packet_materializer=StaticMaterializer(wrong),
        )
        service.enqueue(service_action(compiled=compiled))

        with self.assertRaisesRegex(
            Exception,
            "materialized_packet_hash_mismatch",
        ):
            service.claim_next(
                helper_instance_id="helper",
                claim_id="claim",
                claimed_at="T1",
                expires_at="T2",
            )

    def test_local_only_actions_do_not_inflate_manual_cycle_count(self):
        coordinator = RuntimeCoordinator(
            state_store=InMemoryStateStore(),
            event_ledger=InMemoryEventLedger(),
            telemetry=RecordingTelemetry(),
            clock=FakeClock(),
        )
        coordinator.initialize(
            DomainKernel.create_graph(
                [DomainKernel.create_process("local")]
            )
        )
        service = OperatorActionService(runtime=coordinator)
        local = OperatorAction(
            action_id="discard",
            generation=0,
            action_type=OperatorActionType.DISCARD_SESSION,
            status=OperatorActionState.QUEUED,
            priority_rank=1,
            queue_sequence=1,
            created_at="T0",
            task_id="task",
            reasoning_process_id="local",
            process_generation=0,
            worker_slot_id=None,
            session_generation=None,
            executor_id=None,
            payload_ref=None,
            payload_sha256=None,
            human_requirement=OperatorHumanRequirement.NONE,
            ack_mode=OperatorAckMode.NONE,
            post_local_success=OperatorPostLocalSuccess.COMPLETE_AND_REQUERY,
        )
        service.enqueue(local)
        self.assertEqual(service.workload_status().ready_manual_cycles, 0)


if __name__ == "__main__":
    unittest.main()
