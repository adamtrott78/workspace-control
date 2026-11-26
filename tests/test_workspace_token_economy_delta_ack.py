"""Durable session-ACK gate for Token Economy DELTA context."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.application import (  # noqa: E402
    PacketCompilationInput,
    PersistentExecutorSessionBroker,
    RuntimeCoordinator,
    TokenEconomyPlanner,
    openai_chat_instant_current_profile,
)
from workspace_semantic_execution.application.operator_packets import (  # noqa: E402
    _operator_token_economy_decision,
)
from workspace_semantic_execution.adapters import (  # noqa: E402
    FakeClock,
    InMemoryEventLedger,
    InMemoryStateStore,
    RecordingTelemetry,
)
from workspace_semantic_execution.domain import (  # noqa: E402
    ContextMode,
    DomainKernel,
)


def _runtime() -> RuntimeCoordinator:
    runtime = RuntimeCoordinator(
        state_store=InMemoryStateStore(),
        event_ledger=InMemoryEventLedger(),
        telemetry=RecordingTelemetry(),
        clock=FakeClock(),
    )
    runtime.initialize(
        DomainKernel.create_graph(
            [
                DomainKernel.create_process("P1"),
                DomainKernel.create_process("P2"),
            ]
        )
    )
    return runtime


def _packet_input(process_id: str) -> PacketCompilationInput:
    return PacketCompilationInput(
        process_id=process_id,
        source_checkpoint=f"checkpoint:{process_id}",
        objective=f"Perform bounded work for {process_id}.",
        constraints=("preserve exact authority",),
        evidence_refs=(f"evidence:{process_id}",),
        authority_refs=("scope:none",),
        allowed_actions=("report-result",),
        validator_contract="validator:delta-ack",
        output_schema="RESULT_V1",
        next_safe_boundary="publish candidate and stop",
    )


class DeltaAckTests(unittest.TestCase):
    def test_ack_binds_exact_packet_and_current_session_generation(self) -> None:
        runtime = _runtime()
        broker = PersistentExecutorSessionBroker(runtime)
        profile = openai_chat_instant_current_profile()
        broker.ensure_session(
            profile=profile,
            slot_id="slot",
            session_id="chat-a",
        )
        packet_sha = "a" * 64
        broker.bind(
            profile=profile,
            slot_id="slot",
            expected_session_generation=0,
            process_id="P1",
            process_generation=0,
            packet_sha256=packet_sha,
        )
        acknowledged = broker.acknowledge(
            slot_id="slot",
            expected_session_generation=0,
            process_id="P1",
            process_generation=0,
            ack_id="ack:P1",
        )
        self.assertEqual(acknowledged.last_ack_packet_sha256, packet_sha)
        self.assertEqual(acknowledged.last_ack_session_generation, 0)
        self.assertEqual(acknowledged.last_ack_process_id, "P1")

    def test_exact_current_ack_enables_delta_for_next_packet(self) -> None:
        runtime = _runtime()
        broker = PersistentExecutorSessionBroker(runtime)
        profile = openai_chat_instant_current_profile()
        broker.ensure_session(
            profile=profile,
            slot_id="slot",
            session_id="chat-a",
        )
        previous_sha = "b" * 64
        broker.bind(
            profile=profile,
            slot_id="slot",
            expected_session_generation=0,
            process_id="P1",
            process_generation=0,
            packet_sha256=previous_sha,
        )
        session = broker.acknowledge(
            slot_id="slot",
            expected_session_generation=0,
            process_id="P1",
            process_generation=0,
            ack_id="ack:P1",
        )
        decision = _operator_token_economy_decision(
            packet_input=_packet_input("P2"),
            executor=profile,
            planner=TokenEconomyPlanner(),
            session=session,
            expected_session_generation=0,
        )
        self.assertEqual(decision.context.context_mode, ContextMode.DELTA)
        self.assertEqual(
            decision.context.base_checkpoint,
            f"packet:{previous_sha}",
        )
        self.assertEqual(
            decision.context.delta_refs,
            ("evidence:P2", "scope:none"),
        )

    def test_no_ack_uses_ref_only(self) -> None:
        runtime = _runtime()
        broker = PersistentExecutorSessionBroker(runtime)
        profile = openai_chat_instant_current_profile()
        session = broker.ensure_session(
            profile=profile,
            slot_id="slot",
            session_id="chat-a",
        )
        decision = _operator_token_economy_decision(
            packet_input=_packet_input("P1"),
            executor=profile,
            planner=TokenEconomyPlanner(),
            session=session,
            expected_session_generation=0,
        )
        self.assertEqual(decision.context.context_mode, ContextMode.REF_ONLY)

    def test_session_loss_clears_ack_and_replacement_cannot_use_delta(self) -> None:
        runtime = _runtime()
        broker = PersistentExecutorSessionBroker(runtime)
        profile = openai_chat_instant_current_profile()
        broker.ensure_session(
            profile=profile,
            slot_id="slot",
            session_id="chat-a",
        )
        broker.bind(
            profile=profile,
            slot_id="slot",
            expected_session_generation=0,
            process_id="P1",
            process_generation=0,
            packet_sha256="c" * 64,
        )
        broker.acknowledge(
            slot_id="slot",
            expected_session_generation=0,
            process_id="P1",
            process_generation=0,
            ack_id="ack:P1",
        )
        invalidated = broker.invalidate(
            slot_id="slot",
            expected_session_generation=0,
            reason="context_lost",
        )
        self.assertIsNone(invalidated.last_ack_packet_sha256)
        self.assertIsNone(invalidated.last_ack_session_generation)
        replacement = broker.replace(
            slot_id="slot",
            expected_session_generation=1,
            session_id="chat-b",
        )
        decision = _operator_token_economy_decision(
            packet_input=_packet_input("P2"),
            executor=profile,
            planner=TokenEconomyPlanner(),
            session=replacement,
            expected_session_generation=1,
        )
        self.assertEqual(decision.context.context_mode, ContextMode.REF_ONLY)

    def test_stale_generation_ack_never_enables_delta(self) -> None:
        runtime = _runtime()
        broker = PersistentExecutorSessionBroker(runtime)
        profile = openai_chat_instant_current_profile()
        broker.ensure_session(
            profile=profile,
            slot_id="slot",
            session_id="chat-a",
        )
        broker.bind(
            profile=profile,
            slot_id="slot",
            expected_session_generation=0,
            process_id="P1",
            process_generation=0,
            packet_sha256="d" * 64,
        )
        session = broker.acknowledge(
            slot_id="slot",
            expected_session_generation=0,
            process_id="P1",
            process_generation=0,
            ack_id="ack:P1",
        )
        decision = _operator_token_economy_decision(
            packet_input=_packet_input("P2"),
            executor=profile,
            planner=TokenEconomyPlanner(),
            session=session,
            expected_session_generation=1,
        )
        self.assertEqual(decision.context.context_mode, ContextMode.REF_ONLY)


if __name__ == "__main__":
    unittest.main()
