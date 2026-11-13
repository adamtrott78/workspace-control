"""Tests for deterministic packet compilation and executor routing."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.application import (  # noqa: E402
    DecisionRecord,
    ExecutorRegistry,
    FindingRecord,
    PacketCompilationInput,
    QuestionRecord,
    SemanticPacketCompiler,
    initial_executor_profiles,
    machine_llm_profile,
    openai_chat_instant_current_profile,
    route_executor,
    unprovisioned_institutional_llm_profile,
)
from workspace_semantic_execution.domain import (  # noqa: E402
    ExecutionRequirement,
    ExecutorAvailability,
    ExecutorLocality,
    InvocationMode,
    PrivacyClass,
    SessionMode,
)


def packet_input() -> PacketCompilationInput:
    return PacketCompilationInput(
        process_id="research:retry-cause",
        source_checkpoint="workspace-control@abc123",
        objective="Determine which retry-state hypothesis is still supported.",
        findings=(
            FindingRecord(
                finding_id="F1",
                text="Queue expansion did not eliminate retries.",
                evidence_refs=("experiment:E_queue_4x",),
            ),
        ),
        decisions=(
            DecisionRecord(
                decision_id="D1",
                decision="Retain retry-state hypothesis.",
                rationale="Observed queue intervention was non-discriminating.",
                evidence_refs=("experiment:E_queue_4x",),
                alternatives=("queue saturation",),
            ),
        ),
        unresolved_questions=(
            QuestionRecord(
                question_id="Q1",
                text="Does request-boundary reset eliminate amplification?",
            ),
        ),
        constraints=(
            "Do not widen execution authority.",
            "Use objective validator evidence.",
        ),
        evidence_refs=("experiment:E_queue_4x",),
        authority_refs=("policy:read-only-research",),
        allowed_actions=("reason", "propose_experiment"),
        validator_contract="validator:research-retry-v1",
        output_schema="WORKSPACE_REASONING_RESULT_V1",
        next_safe_boundary="Propose the next discriminating experiment.",
    )


class PacketCompilerTests(unittest.TestCase):
    def test_same_durable_state_produces_identical_clipboard_packet(self):
        compiler = SemanticPacketCompiler()
        executor = openai_chat_instant_current_profile()
        source = packet_input()

        first = compiler.compile(source, executor=executor)
        second = compiler.compile(source, executor=executor)

        self.assertEqual(first, second)
        self.assertEqual(first.text, second.text)
        self.assertEqual(
            first.packet_sha256,
            hashlib.sha256(
                first.canonical_payload_json.encode("utf-8")
            ).hexdigest(),
        )
        self.assertTrue(first.text.startswith("WORKSPACE_REASONING_PACKET_V1\n"))
        self.assertIn("BEGIN_PAYLOAD\n", first.text)
        self.assertTrue(first.text.endswith("END_PAYLOAD\n"))

    def test_packet_is_compiled_from_typed_state_not_chat_transcript(self):
        packet = SemanticPacketCompiler().compile(
            packet_input(),
            executor=openai_chat_instant_current_profile(),
        )
        payload = json.loads(packet.canonical_payload_json)
        process = payload["process"]

        self.assertEqual(process["process_id"], "research:retry-cause")
        self.assertEqual(process["findings"][0]["finding_id"], "F1")
        self.assertEqual(process["decisions"][0]["decision_id"], "D1")
        self.assertEqual(
            process["unresolved_questions"][0]["question_id"],
            "Q1",
        )
        self.assertNotIn("chat_transcript", packet.canonical_payload_json)
        self.assertNotIn("full_prior_chat", packet.canonical_payload_json)

    def test_executor_switch_changes_envelope_not_underlying_process_state(self):
        compiler = SemanticPacketCompiler()
        source = packet_input()
        chat = openai_chat_instant_current_profile()
        machine = machine_llm_profile(
            executor_id="lab-h100-test",
            provider_id="umassd-lab",
            model_id="test-model",
            harness_id="vllm-openai-compatible-v1",
            toolset_id="workspace-machine-tools-v1",
            capabilities=frozenset({"reasoning.bounded"}),
            session_mode=SessionMode.STATELESS,
            availability=ExecutorAvailability.AVAILABLE,
            locality=ExecutorLocality.INSTITUTIONAL_REMOTE,
            privacy_classes=frozenset({PrivacyClass.INTERNAL}),
            resource_classes=frozenset({"GPU_REMOTE"}),
            context_capacity=131072,
            calibration_ref="test:measured",
        )

        chat_packet = compiler.compile(source, executor=chat)
        machine_packet = compiler.compile(source, executor=machine)
        chat_payload = json.loads(chat_packet.canonical_payload_json)
        machine_payload = json.loads(machine_packet.canonical_payload_json)

        self.assertEqual(chat_payload["process"], machine_payload["process"])
        self.assertNotEqual(chat_payload["executor"], machine_payload["executor"])
        self.assertNotEqual(chat_packet.packet_sha256, machine_packet.packet_sha256)
        self.assertIn(
            "Conversation context may be used as a cache",
            chat_payload["execution_contract"]["continuity_rule"],
        )
        self.assertIn(
            "Assume no prior conversational memory",
            machine_payload["execution_contract"]["continuity_rule"],
        )

    def test_missing_durable_fields_fail_closed(self):
        compiler = SemanticPacketCompiler()
        invalid = PacketCompilationInput(
            process_id="P",
            source_checkpoint="",
            objective="Objective",
            validator_contract="V",
            next_safe_boundary="N",
        )
        with self.assertRaises(ValueError):
            compiler.compile(
                invalid,
                executor=openai_chat_instant_current_profile(),
            )


class ExecutorRouterTests(unittest.TestCase):
    def test_initial_registry_contains_instant_and_unknown_machine_placeholder(self):
        profiles = initial_executor_profiles()
        ids = {profile.executor_id for profile in profiles}
        self.assertEqual(
            ids,
            {
                "openai-chat-instant-current",
                "institutional-llm-unprovisioned",
            },
        )
        placeholder = next(
            profile
            for profile in profiles
            if profile.executor_id == "institutional-llm-unprovisioned"
        )
        self.assertEqual(
            placeholder.availability,
            ExecutorAvailability.UNKNOWN,
        )
        self.assertEqual(placeholder.capabilities, frozenset())

    def test_human_assisted_persistent_requirement_selects_chat_instant(self):
        registry = ExecutorRegistry(initial_executor_profiles())
        requirement = ExecutionRequirement(
            required_capabilities=frozenset({"reasoning.bounded", "github.read"}),
            allowed_invocation_modes=frozenset(
                {InvocationMode.HUMAN_ASSISTED}
            ),
            allowed_session_modes=frozenset(
                {SessionMode.PERSISTENT_CHAT}
            ),
            allowed_localities=frozenset(
                {ExecutorLocality.PROVIDER_REMOTE}
            ),
            privacy_class=PrivacyClass.INTERNAL,
            required_resource_classes=frozenset(
                {"REMOTE_MODEL_INFERENCE"}
            ),
            require_human_launch=True,
        )

        decision = route_executor(
            registry,
            requirement_id="req:instant",
            requirement=requirement,
        )

        self.assertEqual(decision.outcome, "SELECTED")
        self.assertEqual(
            decision.selected_executor_id,
            "openai-chat-instant-current",
        )
        exclusions = {
            item.executor_id: item.reasons
            for item in decision.exclusions
        }
        self.assertIn(
            "AVAILABILITY_UNKNOWN",
            exclusions["institutional-llm-unprovisioned"],
        )

    def test_unknown_hardware_never_becomes_optimistic_capacity(self):
        registry = ExecutorRegistry(
            (unprovisioned_institutional_llm_profile(),)
        )
        requirement = ExecutionRequirement(
            allowed_invocation_modes=frozenset(
                {InvocationMode.PROGRAMMATIC}
            ),
            privacy_class=PrivacyClass.PUBLIC,
        )

        decision = route_executor(
            registry,
            requirement_id="req:unknown-hardware",
            requirement=requirement,
        )

        self.assertEqual(decision.outcome, "NO_ELIGIBLE_EXECUTOR")
        self.assertIsNone(decision.selected_executor_id)
        self.assertIn(
            "AVAILABILITY_UNKNOWN",
            decision.exclusions[0].reasons,
        )

    def test_calibrated_stateless_institutional_model_can_be_slotted_in(self):
        machine = machine_llm_profile(
            executor_id="dept-h100-kimi-quantized",
            provider_id="umassd-department",
            model_id="candidate-quantized-model",
            harness_id="vllm-openai-compatible-v1",
            toolset_id="workspace-machine-tools-v1",
            capabilities=frozenset(
                {"reasoning.bounded", "code.read"}
            ),
            session_mode=SessionMode.STATELESS,
            availability=ExecutorAvailability.AVAILABLE,
            locality=ExecutorLocality.INSTITUTIONAL_REMOTE,
            privacy_classes=frozenset(
                {PrivacyClass.PUBLIC, PrivacyClass.INTERNAL}
            ),
            resource_classes=frozenset({"GPU_REMOTE", "H100"}),
            context_capacity=131072,
            scarcity_rank=5,
            calibration_ref="benchmark:dept-h100-v1",
        )
        registry = ExecutorRegistry(
            (
                openai_chat_instant_current_profile(),
                machine,
            )
        )
        requirement = ExecutionRequirement(
            required_capabilities=frozenset(
                {"reasoning.bounded", "code.read"}
            ),
            allowed_invocation_modes=frozenset(
                {InvocationMode.PROGRAMMATIC}
            ),
            allowed_session_modes=frozenset({SessionMode.STATELESS}),
            allowed_localities=frozenset(
                {ExecutorLocality.INSTITUTIONAL_REMOTE}
            ),
            privacy_class=PrivacyClass.INTERNAL,
            minimum_context_capacity=65536,
            required_resource_classes=frozenset({"H100"}),
            require_human_launch=False,
        )

        decision = route_executor(
            registry,
            requirement_id="req:h100",
            requirement=requirement,
        )

        self.assertEqual(decision.outcome, "SELECTED")
        self.assertEqual(
            decision.selected_executor_id,
            "dept-h100-kimi-quantized",
        )

    def test_context_requirement_excludes_unknown_context_capacity(self):
        chat = openai_chat_instant_current_profile()
        registry = ExecutorRegistry((chat,))
        decision = route_executor(
            registry,
            requirement_id="req:known-context",
            requirement=ExecutionRequirement(
                required_capabilities=frozenset({"reasoning.bounded"}),
                privacy_class=PrivacyClass.PUBLIC,
                minimum_context_capacity=100000,
            ),
        )
        self.assertEqual(decision.outcome, "NO_ELIGIBLE_EXECUTOR")
        self.assertIn(
            "CONTEXT_CAPACITY_UNKNOWN",
            decision.exclusions[0].reasons,
        )

    def test_lowest_scarcity_known_eligible_executor_wins(self):
        first = machine_llm_profile(
            executor_id="machine-a",
            provider_id="lab",
            model_id="model-a",
            harness_id="h",
            toolset_id="t",
            capabilities=frozenset({"reasoning.bounded"}),
            session_mode=SessionMode.STATELESS,
            availability=ExecutorAvailability.AVAILABLE,
            locality=ExecutorLocality.INSTITUTIONAL_REMOTE,
            privacy_classes=frozenset({PrivacyClass.PUBLIC}),
            resource_classes=frozenset({"GPU_REMOTE"}),
            context_capacity=32768,
            scarcity_rank=20,
        )
        second = machine_llm_profile(
            executor_id="machine-b",
            provider_id="lab",
            model_id="model-b",
            harness_id="h",
            toolset_id="t",
            capabilities=frozenset({"reasoning.bounded"}),
            session_mode=SessionMode.STATELESS,
            availability=ExecutorAvailability.AVAILABLE,
            locality=ExecutorLocality.INSTITUTIONAL_REMOTE,
            privacy_classes=frozenset({PrivacyClass.PUBLIC}),
            resource_classes=frozenset({"GPU_REMOTE"}),
            context_capacity=32768,
            scarcity_rank=5,
        )
        decision = route_executor(
            ExecutorRegistry((first, second)),
            requirement_id="req:scarcity",
            requirement=ExecutionRequirement(
                required_capabilities=frozenset({"reasoning.bounded"}),
                privacy_class=PrivacyClass.PUBLIC,
            ),
        )
        self.assertEqual(decision.selected_executor_id, "machine-b")
        self.assertEqual(
            decision.eligible_executor_ids,
            ("machine-b", "machine-a"),
        )


if __name__ == "__main__":
    unittest.main()
