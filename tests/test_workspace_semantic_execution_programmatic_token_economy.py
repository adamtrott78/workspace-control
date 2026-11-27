"""Programmatic model dispatch must pass through Token Economy."""
from __future__ import annotations

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
    StaticAuthorityEvaluator,
)
from workspace_semantic_execution.application import (  # noqa: E402
    ExecutorDispatchCoordinator,
    ExecutorDispatchError,
    ExecutorDispatchRequest,
    ExecutorRegistry,
    PacketCompilationInput,
    RuntimeCoordinator,
    SemanticPacketCompiler,
)
from workspace_semantic_execution.domain import (  # noqa: E402
    CommunicationMode,
    ContextMode,
    DomainKernel,
    ExecutionRequirement,
    ExecutorAvailability,
    ExecutorLifecycle,
    ExecutorLocality,
    ExecutorProfile,
    InvocationMode,
    MemoryResetPolicy,
    PrivacyClass,
    ReasoningProfile,
    SessionMode,
)

PROCESS_ID = "programmatic:e4-0:test"


def profile() -> ExecutorProfile:
    return ExecutorProfile(
        executor_id="codex-subscription-test",
        provider_id="openai",
        model_id="gpt-6-luna",
        surface_id="codex-cli",
        harness_id="codex-subscription-v1",
        toolset_id="read-only",
        capabilities=frozenset({"reasoning.bounded", "repository.read"}),
        invocation_mode=InvocationMode.PROGRAMMATIC,
        session_mode=SessionMode.STATELESS,
        lifecycle=ExecutorLifecycle.EPHEMERAL_INVOCATION,
        memory_reset_policy=MemoryResetPolicy.EVERY_INVOCATION,
        availability=ExecutorAvailability.AVAILABLE,
        locality=ExecutorLocality.PROVIDER_REMOTE,
        privacy_classes=frozenset({PrivacyClass.INTERNAL}),
        resource_classes=frozenset({"REMOTE_MODEL_INFERENCE"}),
        usage_pool_ids=("codex-subscription",),
        scarcity_rank=30,
    )


def requirement() -> ExecutionRequirement:
    return ExecutionRequirement(
        required_capabilities=frozenset({"reasoning.bounded"}),
        allowed_invocation_modes=frozenset({InvocationMode.PROGRAMMATIC}),
        allowed_session_modes=frozenset({SessionMode.STATELESS}),
        allowed_lifecycles=frozenset(
            {ExecutorLifecycle.EPHEMERAL_INVOCATION}
        ),
        allowed_memory_reset_policies=frozenset(
            {MemoryResetPolicy.EVERY_INVOCATION}
        ),
        allowed_localities=frozenset({ExecutorLocality.PROVIDER_REMOTE}),
        privacy_class=PrivacyClass.INTERNAL,
        required_resource_classes=frozenset({"REMOTE_MODEL_INFERENCE"}),
        require_human_launch=False,
    )


def packet_input() -> PacketCompilationInput:
    return PacketCompilationInput(
        process_id=PROCESS_ID,
        source_checkpoint="checkpoint:e4-0",
        objective="Inspect the bounded source and return only structured evidence.",
        constraints=("read only", "do not widen authority"),
        evidence_refs=("git://repo@sha/path",),
        authority_refs=("authority://bounded-read",),
        allowed_actions=("read",),
        validator_contract="validator:bounded-result",
        output_schema="RESULT_V1",
        next_safe_boundary="return structured result only",
    )


def runtime() -> RuntimeCoordinator:
    rt = RuntimeCoordinator(
        state_store=InMemoryStateStore(),
        event_ledger=InMemoryEventLedger(),
        telemetry=RecordingTelemetry(),
        clock=FakeClock(),
    )
    rt.initialize(
        DomainKernel.create_graph(
            [DomainKernel.create_process(PROCESS_ID)]
        )
    )
    return rt


class RecordingProgrammaticPort:
    def __init__(self):
        self.calls = []

    def execute(self, **kwargs):
        self.calls.append(kwargs)
        return {"result_kind": "RESULT", "summary": "ok", "evidence_refs": []}


class ProgrammaticTokenEconomyDispatchTests(unittest.TestCase):
    def test_programmatic_model_is_budgeted_and_compact_before_port_call(self):
        rt = runtime()
        p = profile()
        port = RecordingProgrammaticPort()
        coordinator = ExecutorDispatchCoordinator(
            runtime=rt,
            registry=ExecutorRegistry((p,)),
            packet_compiler=SemanticPacketCompiler(),
            authority_evaluator=StaticAuthorityEvaluator({}),
            executor_ports={},
            validators={},
            programmatic_ports={p.executor_id: port},
        )

        result = coordinator.dispatch(
            ExecutorDispatchRequest(
                process_id=PROCESS_ID,
                expected_generation=0,
                requirement_id="programmatic:e4-0",
                requirement=requirement(),
                packet_input=packet_input(),
            )
        )

        self.assertEqual(result.dispatch_mode, "PROGRAMMATIC_MODEL")
        self.assertIsNotNone(result.programmatic_dispatch)
        assert result.programmatic_dispatch is not None
        economy = result.programmatic_dispatch.token_economy
        self.assertEqual(economy.context.context_mode, ContextMode.REF_ONLY)
        self.assertEqual(
            economy.budget.reasoning_profile,
            ReasoningProfile.ECONOMY,
        )
        self.assertEqual(
            economy.budget.communication_mode,
            CommunicationMode.MACHINE_MINIMAL,
        )
        self.assertTrue(economy.budget.allow_model_call)
        self.assertEqual(len(port.calls), 1)
        call = port.calls[0]
        self.assertEqual(call["budget"], economy.budget)
        self.assertNotIn("BEGIN_PAYLOAD", call["packet"].text)
        self.assertIn("AUTHORITY=PROPOSAL_ONLY", call["packet"].text)
        self.assertIn("max_output_tokens=", call["packet"].text)

    def test_programmatic_route_without_registered_port_fails_closed(self):
        rt = runtime()
        p = profile()
        coordinator = ExecutorDispatchCoordinator(
            runtime=rt,
            registry=ExecutorRegistry((p,)),
            packet_compiler=SemanticPacketCompiler(),
            authority_evaluator=StaticAuthorityEvaluator({}),
            executor_ports={},
            validators={},
            programmatic_ports={},
        )
        with self.assertRaisesRegex(
            ExecutorDispatchError,
            "programmatic_executor_port_missing",
        ):
            coordinator.dispatch(
                ExecutorDispatchRequest(
                    process_id=PROCESS_ID,
                    expected_generation=0,
                    requirement_id="programmatic:e4-0",
                    requirement=requirement(),
                    packet_input=packet_input(),
                )
            )


if __name__ == "__main__":
    unittest.main()
