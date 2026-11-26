"""Token-economy and Instant front-door contracts."""
from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.application import (  # noqa: E402
    InstantFrontDoorIntake,
    TokenEconomyPlanner,
    TokenEconomyRequest,
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


if __name__ == "__main__":
    unittest.main()
