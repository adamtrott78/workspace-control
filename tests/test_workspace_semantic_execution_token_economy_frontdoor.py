"""Token-economy and Instant front-door contracts."""
from __future__ import annotations

import sys
import json
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.adapters import (  # noqa: E402
    FileFrontDoorIntakeStore,
    FrontDoorIntakeStoreError,
)
from workspace_semantic_execution.application import (  # noqa: E402
    InstantFrontDoorIntake,
    PacketCompilationInput,
    SemanticPacketCompiler,
    TokenEconomyPlanner,
    TokenEconomyRequest,
    openai_chat_instant_current_profile,
)
from workspace_semantic_execution.domain import (  # noqa: E402
    CommunicationMode,
    ContextMode,
    FrontDoorIntent,
    FrontDoorMessage,
    InvocationMode,
    ReasoningProfile,
    SessionMode,
)


class TokenEconomyPlannerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.planner = TokenEconomyPlanner()

    def test_waiting_external_has_exact_zero_model_budget(self) -> None:
        result = self.planner.plan(
            TokenEconomyRequest(
                required_refs=("task://T1",),
                optional_refs=("repo://large-context",),
                waiting_external=True,
            )
        )
        self.assertFalse(result.budget.allow_model_call)
        self.assertEqual(result.budget.reasoning_profile, ReasoningProfile.NO_MODEL)
        self.assertEqual(result.budget.max_inline_tokens, 0)
        self.assertEqual(result.budget.max_retrieved_tokens, 0)
        self.assertEqual(result.budget.max_output_tokens, 0)
        self.assertEqual(result.context.required_refs, ("task://T1",))
        self.assertEqual(
            result.context.omitted_optional_refs,
            ("repo://large-context",),
        )

    def test_deterministic_execution_has_no_model_budget(self) -> None:
        result = self.planner.plan(
            TokenEconomyRequest(
                invocation_mode=InvocationMode.DETERMINISTIC,
                required_refs=("git://sha/path",),
            )
        )
        self.assertFalse(result.budget.allow_model_call)
        self.assertEqual(result.budget.reasoning_profile, ReasoningProfile.NO_MODEL)

    def test_persistent_session_with_bound_checkpoint_uses_delta(self) -> None:
        result = self.planner.plan(
            TokenEconomyRequest(
                session_mode=SessionMode.PERSISTENT_CHAT,
                base_checkpoint="checkpoint:C42",
                session_has_base_checkpoint=True,
                delta_refs=("evidence://new-1",),
                optional_refs=("evidence://old-bulk",),
            )
        )
        self.assertEqual(result.context.context_mode, ContextMode.DELTA)
        self.assertEqual(result.context.delta_refs, ("evidence://new-1",))
        self.assertEqual(
            result.context.omitted_optional_refs,
            ("evidence://old-bulk",),
        )
        self.assertEqual(
            result.budget.communication_mode,
            CommunicationMode.MACHINE_MINIMAL,
        )

    def test_recovery_requires_full_reconstructable_context(self) -> None:
        result = self.planner.plan(
            TokenEconomyRequest(
                recovery_required=True,
                required_refs=("task://T",),
                optional_refs=("evidence://A", "evidence://B"),
            )
        )
        self.assertEqual(result.context.context_mode, ContextMode.FULL_RECOVERY)
        self.assertEqual(
            result.context.optional_refs,
            ("evidence://A", "evidence://B"),
        )

    def test_user_facing_changes_output_mode_not_authority_or_context(self) -> None:
        result = self.planner.plan(
            TokenEconomyRequest(
                user_facing=True,
                required_refs=("task://T",),
            )
        )
        self.assertEqual(
            result.budget.communication_mode,
            CommunicationMode.USER_FACING,
        )
        self.assertEqual(result.context.context_mode, ContextMode.REF_ONLY)


class EconomicalPacketRenderingTests(unittest.TestCase):
    def test_compact_projection_preserves_canonical_hash_and_mandatory_contract(self) -> None:
        compiler = SemanticPacketCompiler()
        executor = openai_chat_instant_current_profile()
        source = PacketCompilationInput(
            process_id="P1",
            source_checkpoint="checkpoint:abc",
            objective="Inspect the exact bounded source and report the result.",
            findings=(),
            decisions=(),
            constraints=("do not widen authority", "read only exact source"),
            evidence_refs=("evidence://one",),
            authority_refs=("authority://scope",),
            allowed_actions=("read",),
            validator_contract="validator:exact-source",
            output_schema="RESULT_V1",
            next_safe_boundary="return candidate only",
        )
        full = compiler.compile(source, executor=executor)
        decision = TokenEconomyPlanner().plan(
            TokenEconomyRequest(
                required_refs=source.evidence_refs + source.authority_refs,
                base_checkpoint=source.source_checkpoint,
                invocation_mode=executor.invocation_mode,
                session_mode=executor.session_mode,
            )
        )
        compact = compiler.compile(
            source,
            executor=executor,
            token_economy=decision,
        )

        self.assertEqual(compact.packet_sha256, full.packet_sha256)
        self.assertEqual(
            compact.canonical_payload_json,
            full.canonical_payload_json,
        )
        self.assertLess(len(compact.text), len(full.text))
        self.assertIn("AUTHORITY=PROPOSAL_ONLY", compact.text)
        self.assertIn("COMPLETION=VALIDATOR_REQUIRED", compact.text)
        self.assertIn("CONSTRAINTS=do not widen authority|read only exact source", compact.text)
        self.assertIn("AUTHORITY_REFS=authority://scope", compact.text)
        self.assertIn("VALIDATOR=validator:exact-source", compact.text)
        self.assertIn("OUTPUT_SCHEMA=RESULT_V1", compact.text)
        self.assertNotIn('"execution_contract"', compact.text)

    def test_full_recovery_keeps_complete_payload_rendering(self) -> None:
        compiler = SemanticPacketCompiler()
        executor = openai_chat_instant_current_profile()
        source = PacketCompilationInput(
            process_id="P2",
            source_checkpoint="checkpoint:recovery",
            objective="Recover from durable state.",
            constraints=("preserve authority",),
            validator_contract="validator:recovery",
            output_schema="RESULT_V1",
            next_safe_boundary="resume",
        )
        baseline = compiler.compile(source, executor=executor)
        decision = TokenEconomyPlanner().plan(
            TokenEconomyRequest(
                recovery_required=True,
                base_checkpoint=source.source_checkpoint,
                invocation_mode=executor.invocation_mode,
                session_mode=executor.session_mode,
            )
        )
        recovery = compiler.compile(
            source,
            executor=executor,
            token_economy=decision,
        )
        self.assertEqual(recovery.text, baseline.text)
        self.assertIn("BEGIN_PAYLOAD", recovery.text)
        self.assertIn('"execution_contract"', recovery.text)


class InstantFrontDoorTests(unittest.TestCase):
    def test_task_submission_is_non_authoritative_candidate(self) -> None:
        result = InstantFrontDoorIntake().ingest(
            FrontDoorMessage(
                message_id="m1",
                conversation_id="frontdoor-main",
                text="Run the next bounded reliability task.",
                submitted_at="2026-11-26T12:00:00-05:00",
                intent=FrontDoorIntent.SUBMIT_TASK,
            )
        )
        self.assertIsNotNone(result.candidate)
        assert result.candidate is not None
        self.assertEqual(result.candidate.authorization_state, "UNDECIDED")
        self.assertEqual(
            result.candidate.source_ref,
            "chatgpt-instant://frontdoor-main/m1",
        )
        self.assertFalse(result.requires_existing_task_lookup)

    def test_status_and_decision_messages_require_durable_task_lookup(self) -> None:
        for intent in (
            FrontDoorIntent.QUERY_STATUS,
            FrontDoorIntent.PROVIDE_DECISION,
            FrontDoorIntent.CANCEL_REQUEST,
        ):
            with self.subTest(intent=intent):
                result = InstantFrontDoorIntake().ingest(
                    FrontDoorMessage(
                        message_id=f"m-{intent.value}",
                        conversation_id="frontdoor-main",
                        text="status",
                        submitted_at="2026-11-26T12:00:00-05:00",
                        intent=intent,
                    )
                )
                self.assertIsNone(result.candidate)
                self.assertTrue(result.requires_existing_task_lookup)


class FrontDoorDurableStoreTests(unittest.TestCase):
    def test_round_trip_is_candidate_only_and_duplicate_fails(self) -> None:
        intake = InstantFrontDoorIntake().ingest(
            FrontDoorMessage(
                message_id="m-store",
                conversation_id="frontdoor-main",
                text="Implement the next bounded task.",
                submitted_at="2026-11-26T12:00:00-05:00",
                intent=FrontDoorIntent.SUBMIT_TASK,
            )
        )
        assert intake.candidate is not None
        with tempfile.TemporaryDirectory() as tmp:
            store = FileFrontDoorIntakeStore(Path(tmp))
            path = store.persist(
                intake.candidate,
                submitted_at=intake.message.submitted_at,
            )
            loaded = store.load(path)
            self.assertEqual(loaded, intake.candidate)
            self.assertEqual(loaded.authorization_state, "UNDECIDED")
            with self.assertRaises(FrontDoorIntakeStoreError):
                store.persist(
                    intake.candidate,
                    submitted_at=intake.message.submitted_at,
                )

    def test_tampered_authority_record_is_rejected(self) -> None:
        intake = InstantFrontDoorIntake().ingest(
            FrontDoorMessage(
                message_id="m-tamper",
                conversation_id="frontdoor-main",
                text="Run a task.",
                submitted_at="2026-11-26T12:00:00-05:00",
            )
        )
        assert intake.candidate is not None
        with tempfile.TemporaryDirectory() as tmp:
            store = FileFrontDoorIntakeStore(Path(tmp))
            path = store.persist(
                intake.candidate,
                submitted_at=intake.message.submitted_at,
            )
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["candidate"]["authorization_state"] = "ALLOW"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(FrontDoorIntakeStoreError):
                store.load(path)


if __name__ == "__main__":
    unittest.main()
