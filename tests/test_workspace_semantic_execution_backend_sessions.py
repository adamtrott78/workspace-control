"""Persistent executor-session broker and generation-fencing tests."""
from __future__ import annotations

from dataclasses import fields
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.adapters import (  # noqa: E402
    FakeClock, InMemoryEventLedger, InMemoryStateStore, RecordingTelemetry,
    dumps_work_graph, loads_work_graph,
)
from workspace_semantic_execution.application import (  # noqa: E402
    PacketCompilationInput, PersistentExecutorSessionBroker, RuntimeCoordinator,
    SemanticPacketCompiler, machine_llm_profile,
    openai_chat_instant_current_profile,
)
from workspace_semantic_execution.domain import (  # noqa: E402
    DomainKernel, ExecutorAvailability, ExecutorLifecycle, ExecutorLocality,
    ExecutorSession, ExecutorSessionState, MemoryResetPolicy, PrivacyClass,
    SessionMode,
)
from workspace_semantic_execution.domain.kernel import KernelError  # noqa: E402


def runtime():
    c = RuntimeCoordinator(
        state_store=InMemoryStateStore(),
        event_ledger=InMemoryEventLedger(),
        telemetry=RecordingTelemetry(),
        clock=FakeClock(),
    )
    c.initialize(DomainKernel.create_graph([
        DomainKernel.create_process("P1"),
        DomainKernel.create_process("P2"),
    ]))
    return c


def packet_hash(process_id: str) -> str:
    packet = SemanticPacketCompiler().compile(
        PacketCompilationInput(
            process_id=process_id,
            source_checkpoint="checkpoint:1",
            objective=f"Execute bounded work for {process_id}.",
            constraints=("resume from durable state",),
            evidence_refs=("evidence:1",),
            authority_refs=("scope:none",),
            allowed_actions=("report-result",),
            validator_contract="validator:1",
            next_safe_boundary="return typed result",
        ),
        executor=openai_chat_instant_current_profile(),
    )
    return packet.packet_sha256


class PersistentExecutorSessionBrokerTests(unittest.TestCase):
    def test_healthy_persistent_session_is_reused_across_work(self):
        c = runtime(); broker = PersistentExecutorSessionBroker(c)
        profile = openai_chat_instant_current_profile()
        session = broker.ensure_session(profile=profile, slot_id="instant-slot-1", session_id="chat-session-a")
        self.assertIsNotNone(session); assert session is not None
        self.assertEqual(session.state, ExecutorSessionState.READY)
        binding = broker.bind(profile=profile, slot_id="instant-slot-1", expected_session_generation=0, process_id="P1", process_generation=0, packet_sha256=packet_hash("P1"))
        self.assertEqual(binding.session_id, "chat-session-a")
        acknowledged = broker.acknowledge(slot_id="instant-slot-1", expected_session_generation=0, process_id="P1", process_generation=0, ack_id="ack:P1")
        self.assertEqual(acknowledged.state, ExecutorSessionState.READY)
        rebound = broker.bind(profile=profile, slot_id="instant-slot-1", expected_session_generation=0, process_id="P2", process_generation=0, packet_sha256=packet_hash("P2"))
        self.assertEqual(rebound.session_id, "chat-session-a")
        self.assertEqual(rebound.session_generation, 0)

    def test_loss_advances_generation_and_stale_ack_is_rejected(self):
        c=runtime(); broker=PersistentExecutorSessionBroker(c); profile=openai_chat_instant_current_profile()
        broker.ensure_session(profile=profile, slot_id="slot", session_id="session-old")
        broker.bind(profile=profile, slot_id="slot", expected_session_generation=0, process_id="P1", process_generation=0, packet_sha256=packet_hash("P1"))
        invalidated=broker.invalidate(slot_id="slot", expected_session_generation=0, reason="transport_lost")
        self.assertEqual(invalidated.state, ExecutorSessionState.NEEDS_REPLACEMENT)
        self.assertEqual(invalidated.session_generation, 1)
        with self.assertRaisesRegex(KernelError, "stale_session_generation"):
            broker.acknowledge(slot_id="slot", expected_session_generation=0, process_id="P1", process_generation=0, ack_id="late-old-ack")
        replacement=broker.replace(slot_id="slot", expected_session_generation=1, session_id="session-new")
        self.assertEqual(replacement.state, ExecutorSessionState.READY)
        rebound=broker.bind(profile=profile, slot_id="slot", expected_session_generation=1, process_id="P1", process_generation=0, packet_sha256=packet_hash("P1"))
        self.assertEqual(rebound.session_id, "session-new")

    def test_process_recovery_fences_bound_session_automatically(self):
        c=runtime(); broker=PersistentExecutorSessionBroker(c); profile=openai_chat_instant_current_profile()
        broker.ensure_session(profile=profile, slot_id="slot", session_id="session-a")
        broker.bind(profile=profile, slot_id="slot", expected_session_generation=0, process_id="P1", process_generation=0, packet_sha256=packet_hash("P1"))
        recovered=c.recover("P1", expected_generation=0, reason="worker_lost")
        session=recovered.graph.executor_sessions["slot"]
        self.assertEqual(session.state, ExecutorSessionState.NEEDS_REPLACEMENT)
        self.assertEqual(session.session_generation, 1)
        self.assertIsNone(session.bound_process_id)
        with self.assertRaisesRegex(KernelError, "stale_session_generation"):
            broker.acknowledge(slot_id="slot", expected_session_generation=0, process_id="P1", process_generation=0, ack_id="stale-after-recovery")

    def test_context_rotation_reconstructs_same_packet_from_durable_state(self):
        c=runtime(); broker=PersistentExecutorSessionBroker(c); profile=openai_chat_instant_current_profile()
        original=packet_hash("P1")
        broker.ensure_session(profile=profile, slot_id="slot", session_id="session-a")
        broker.bind(profile=profile, slot_id="slot", expected_session_generation=0, process_id="P1", process_generation=0, packet_sha256=original)
        broker.invalidate(slot_id="slot", expected_session_generation=0, reason="context_threshold")
        broker.replace(slot_id="slot", expected_session_generation=1, session_id="session-b")
        reconstructed=packet_hash("P1")
        self.assertEqual(reconstructed, original)
        rebound=broker.bind(profile=profile, slot_id="slot", expected_session_generation=1, process_id="P1", process_generation=0, packet_sha256=reconstructed)
        self.assertEqual(rebound.session_id, "session-b")

    def test_stateless_machine_executor_does_not_allocate_session(self):
        c=runtime(); broker=PersistentExecutorSessionBroker(c)
        profile=machine_llm_profile(
            executor_id="machine-stateless", provider_id="test", model_id="test-model",
            harness_id="test-harness", toolset_id="none",
            capabilities=frozenset({"reasoning.bounded"}),
            session_mode=SessionMode.STATELESS,
            lifecycle=ExecutorLifecycle.EPHEMERAL_INVOCATION,
            memory_reset_policy=MemoryResetPolicy.EVERY_INVOCATION,
            availability=ExecutorAvailability.AVAILABLE,
            locality=ExecutorLocality.LOCAL_HOST,
            privacy_classes=frozenset({PrivacyClass.PUBLIC}),
            resource_classes=frozenset({"CPU"}), context_capacity=4096,
        )
        self.assertIsNone(broker.ensure_session(profile=profile, slot_id="must-not-exist", session_id="irrelevant"))
        self.assertEqual(c.snapshot().graph.executor_sessions, {})

    def test_session_state_round_trips_durably_and_contains_no_authority(self):
        c=runtime(); broker=PersistentExecutorSessionBroker(c); profile=openai_chat_instant_current_profile()
        broker.ensure_session(profile=profile, slot_id="slot", session_id="session-a")
        broker.bind(profile=profile, slot_id="slot", expected_session_generation=0, process_id="P1", process_generation=0, packet_sha256=packet_hash("P1"))
        graph=c.snapshot().graph
        self.assertEqual(loads_work_graph(dumps_work_graph(graph)), graph)
        self.assertFalse(any("authority" in field.name for field in fields(ExecutorSession)))


if __name__ == "__main__":
    unittest.main()
