"""Reasoning Economy admission-policy integration tests."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
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
    OperatorDispatchParameters,
    PacketCompilationInput,
    PersistentExecutorSessionBroker,
    RuntimeCoordinator,
    SemanticPacketCompiler,
    openai_chat_instant_current_profile,
)
from workspace_semantic_execution.domain import (  # noqa: E402
    DomainKernel,
    ExecutionRequirement,
    ExecutorAvailability,
    ExecutorLifecycle,
    ExecutorLocality,
    ExecutorProfile,
    InvocationMode,
    MemoryResetPolicy,
    PrivacyClass,
    ProcessState,
    SessionMode,
)
from workspace_semantic_execution.economics import (  # noqa: E402
    BillingMode,
    ExecutionTokenUsage,
    ExecutorEconomicsBinding,
    ReasoningEconomyAdmissionPolicy,
    WasteClass,
    WeeklyBudgetPolicy,
    build_execution_economics,
)
from workspace_semantic_execution.ports import (  # noqa: E402
    AccountTokenUsageSummary,
    RateLimitBucketSnapshot,
    RateLimitWindowClass,
    RateLimitWindowSnapshot,
    UsageSnapshot,
)


PROCESS_ID = "economy-admission-process"
SLOT_ID = "economy-admission-slot"
LIMIT_ID = "chat-weekly"
RESET = int(
    datetime(2026, 11, 22, 12, tzinfo=timezone.utc).timestamp()
)
POLICY = WeeklyBudgetPolicy(
    limit_id=LIMIT_ID,
    reserve_percent_points=20,
    max_single_action_percent_points=10,
    min_calibration_samples=3,
    minimum_validator_pass_rate=1.0,
    minimum_validator_score=0.80,
)


def usage(used: int) -> UsageSnapshot:
    return UsageSnapshot(
        captured_at="2026-11-15T12:00:00+00:00",
        ordinary_usage_allowed=True,
        rate_limit_buckets=(
            RateLimitBucketSnapshot(
                limit_id=LIMIT_ID,
                limit_name="Chat",
                normal_model_slug="gpt-test",
                plan_type="plus",
                windows=(
                    RateLimitWindowSnapshot(
                        source_role="weekly",
                        used_percent=used,
                        window_duration_mins=10080,
                        resets_at=RESET,
                        window_class=RateLimitWindowClass.WEEKLY,
                    ),
                ),
            ),
        ),
        token_summary=AccountTokenUsageSummary(
            lifetime_tokens=None,
            peak_daily_tokens=None,
            longest_running_turn_sec=None,
            current_streak_days=None,
            longest_streak_days=None,
        ),
        daily_usage_buckets=None,
        thread_usage=None,
    )


def economics(
    *,
    execution_id: str,
    executor_id: str,
    before: int,
    cost: int,
    score: float,
):
    return build_execution_economics(
        execution_id=execution_id,
        work_item_id=f"work:{execution_id}",
        parent_execution_id=None,
        executor_id=executor_id,
        model_id=executor_id,
        surface_id="chat",
        started_at="2026-11-15T12:00:00+00:00",
        ended_at="2026-11-15T12:01:00+00:00",
        token_usage=ExecutionTokenUsage(
            input_tokens=100,
            output_tokens=20,
            total_tokens=120,
        ),
        model_invocations=1,
        tool_calls=0,
        retries=0,
        decomposition_depth=0,
        children_spawned=0,
        validator_passed=True,
        validator_score=score,
        waste_class=WasteClass.PRODUCTIVE_REASONING,
        usage_before=usage(before),
        usage_after=usage(before + cost),
    )


def runtime() -> RuntimeCoordinator:
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
    return coordinator


def instant_profiles():
    base = openai_chat_instant_current_profile()
    cheap = replace(
        base,
        executor_id="instant-cheap",
        model_id="instant-cheap-model",
        scarcity_rank=1,
        usage_pool_ids=(LIMIT_ID,),
    )
    strong = replace(
        base,
        executor_id="instant-strong",
        model_id="instant-strong-model",
        scarcity_rank=5,
        usage_pool_ids=(LIMIT_ID,),
    )
    return cheap, strong


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


def packet() -> PacketCompilationInput:
    return PacketCompilationInput(
        process_id=PROCESS_ID,
        source_checkpoint="economy-admission@checkpoint",
        objective="Complete the bounded reasoning leaf.",
        constraints=("respect weekly allowance admission",),
        evidence_refs=("evidence:economy-admission",),
        authority_refs=("scope:proposal-only",),
        allowed_actions=("publish-candidate-result",),
        validator_contract="validator:economy-admission",
        output_schema="WORKER_RESULT_V1",
        next_safe_boundary="publish immutable candidate",
    )


def operator_params() -> OperatorDispatchParameters:
    return OperatorDispatchParameters(
        task_id="economy-admission",
        action_id="action:economy-admission",
        action_generation=0,
        worker_slot_id=SLOT_ID,
        session_generation=0,
        priority_rank=10,
        queue_sequence=1,
        created_at="T0",
        result_publication_target_ref=(
            "github-candidate://adamtrott78/workspace-control/"
            "ref/refs%2Fheads%2Fworker-result-candidates-v1/"
            "path/worker-results/candidates/economy-admission.json"
        ),
    )


def dispatcher(
    coordinator: RuntimeCoordinator,
    profiles,
    admission,
):
    return ExecutorDispatchCoordinator(
        runtime=coordinator,
        registry=ExecutorRegistry(tuple(profiles)),
        packet_compiler=SemanticPacketCompiler(),
        authority_evaluator=StaticAuthorityEvaluator(),
        executor_ports={},
        validators={},
        selection_policy=admission,
    )


class AdmissionIntegrationTests(unittest.TestCase):
    def test_quality_gate_can_override_base_scarcity_with_already_eligible_stronger_executor(self):
        coordinator = runtime()
        cheap, strong = instant_profiles()
        PersistentExecutorSessionBroker(coordinator).ensure_session(
            profile=strong,
            slot_id=SLOT_ID,
            session_id="strong-session",
        )
        rows = []
        for i in range(3):
            rows.append(
                economics(
                    execution_id=f"cheap-{i}",
                    executor_id=cheap.executor_id,
                    before=5 + i * 3,
                    cost=2,
                    score=0.70,
                )
            )
            rows.append(
                economics(
                    execution_id=f"strong-{i}",
                    executor_id=strong.executor_id,
                    before=30 + i * 5,
                    cost=4,
                    score=0.95,
                )
            )
        admission = ReasoningEconomyAdmissionPolicy(
            budget_policy=POLICY,
            bindings=(
                ExecutorEconomicsBinding(
                    executor_id=cheap.executor_id,
                    billing_mode=BillingMode.INCLUDED_SUBSCRIPTION,
                    weekly_limit_id=LIMIT_ID,
                ),
                ExecutorEconomicsBinding(
                    executor_id=strong.executor_id,
                    billing_mode=BillingMode.INCLUDED_SUBSCRIPTION,
                    weekly_limit_id=LIMIT_ID,
                ),
            ),
            current_usage=usage(20),
            usage_history=(usage(20),),
            economics_records=rows,
        )

        result = dispatcher(
            coordinator,
            (cheap, strong),
            admission,
        ).dispatch(
            ExecutorDispatchRequest(
                process_id=PROCESS_ID,
                expected_generation=0,
                requirement_id="requirement:economy-admission",
                requirement=requirement(),
                packet_input=packet(),
                operator=operator_params(),
            )
        )

        self.assertEqual(
            result.routing.selected_executor_id,
            strong.executor_id,
        )
        self.assertEqual(
            result.selection_policy.outcome,
            "SELECTED",
        )
        action = coordinator.snapshot().graph.operator_actions[
            "action:economy-admission"
        ]
        self.assertEqual(action.executor_id, strong.executor_id)
        self.assertEqual(
            coordinator.snapshot().graph.processes[
                PROCESS_ID
            ].state,
            ProcessState.RUNNING,
        )

    def test_budget_rejection_occurs_before_process_session_or_action_mutation(self):
        coordinator = runtime()
        cheap, _ = instant_profiles()
        PersistentExecutorSessionBroker(coordinator).ensure_session(
            profile=cheap,
            slot_id=SLOT_ID,
            session_id="cheap-session",
        )
        rows = tuple(
            economics(
                execution_id=f"cheap-{i}",
                executor_id=cheap.executor_id,
                before=5 + i * 8,
                cost=6,
                score=0.95,
            )
            for i in range(3)
        )
        admission = ReasoningEconomyAdmissionPolicy(
            budget_policy=POLICY,
            bindings=(
                ExecutorEconomicsBinding(
                    executor_id=cheap.executor_id,
                    billing_mode=BillingMode.INCLUDED_SUBSCRIPTION,
                    weekly_limit_id=LIMIT_ID,
                ),
            ),
            current_usage=usage(75),
            usage_history=(usage(75),),
            economics_records=rows,
        )
        before = coordinator.snapshot()

        with self.assertRaisesRegex(
            ExecutorDispatchError,
            "selection_policy_denied:REJECT_BUDGET",
        ):
            dispatcher(
                coordinator,
                (cheap,),
                admission,
            ).dispatch(
                ExecutorDispatchRequest(
                    process_id=PROCESS_ID,
                    expected_generation=0,
                    requirement_id="requirement:budget-block",
                    requirement=requirement(),
                    packet_input=packet(),
                    operator=operator_params(),
                )
            )

        after = coordinator.snapshot()
        self.assertEqual(after.version, before.version)
        self.assertEqual(
            after.graph.processes[PROCESS_ID].state,
            ProcessState.READY,
        )
        self.assertEqual(after.graph.operator_actions, {})
        self.assertEqual(
            after.graph.executor_sessions[SLOT_ID].state.value,
            "READY",
        )

    def test_metered_executor_without_economics_binding_fails_closed_pre_mutation(self):
        coordinator = runtime()
        cheap, _ = instant_profiles()
        PersistentExecutorSessionBroker(coordinator).ensure_session(
            profile=cheap,
            slot_id=SLOT_ID,
            session_id="cheap-session",
        )
        admission = ReasoningEconomyAdmissionPolicy(
            budget_policy=POLICY,
            bindings=(),
            current_usage=usage(20),
            usage_history=(usage(20),),
            economics_records=(),
        )
        before = coordinator.snapshot()

        with self.assertRaisesRegex(
            ExecutorDispatchError,
            "selection_policy_denied:MISSING_ECONOMICS_BINDING",
        ):
            dispatcher(
                coordinator,
                (cheap,),
                admission,
            ).dispatch(
                ExecutorDispatchRequest(
                    process_id=PROCESS_ID,
                    expected_generation=0,
                    requirement_id="requirement:missing-binding",
                    requirement=requirement(),
                    packet_input=packet(),
                    operator=operator_params(),
                )
            )

        self.assertEqual(
            coordinator.snapshot().version,
            before.version,
        )
        self.assertEqual(
            coordinator.snapshot().graph.operator_actions,
            {},
        )

    def test_unmetered_deterministic_base_path_is_not_forced_into_subscription_meter(self):
        profile = ExecutorProfile(
            executor_id="deterministic-local",
            provider_id="workspace-control",
            model_id="none",
            surface_id="machine",
            harness_id="deterministic-v1",
            toolset_id="deterministic",
            capabilities=frozenset({"deterministic.test"}),
            invocation_mode=InvocationMode.DETERMINISTIC,
            session_mode=SessionMode.NONE,
            lifecycle=ExecutorLifecycle.DETERMINISTIC_PROCESS,
            memory_reset_policy=MemoryResetPolicy.NONE,
            availability=ExecutorAvailability.AVAILABLE,
            locality=ExecutorLocality.LOCAL_HOST,
            privacy_classes=frozenset({PrivacyClass.INTERNAL}),
            resource_classes=frozenset({"CPU"}),
            usage_pool_ids=(),
            scarcity_rank=0,
        )
        from workspace_semantic_execution.application import route_executor
        registry = ExecutorRegistry((profile,))
        base = route_executor(
            registry,
            requirement_id="requirement:deterministic",
            requirement=ExecutionRequirement(
                required_capabilities=frozenset(
                    {"deterministic.test"}
                ),
                allowed_invocation_modes=frozenset(
                    {InvocationMode.DETERMINISTIC}
                ),
                allowed_session_modes=frozenset(
                    {SessionMode.NONE}
                ),
                privacy_class=PrivacyClass.INTERNAL,
            ),
        )
        admission = ReasoningEconomyAdmissionPolicy(
            budget_policy=POLICY,
            bindings=(),
            current_usage=usage(99),
            usage_history=(usage(99),),
            economics_records=(),
        )

        decision = admission.select(
            requirement_id="requirement:deterministic",
            eligible_profiles=(profile,),
            base_routing=base,
            disposition=(
                DomainKernel.create_process("x").disposition
            ),
        )

        self.assertEqual(
            decision.selected_executor_id,
            profile.executor_id,
        )
        self.assertEqual(
            decision.outcome,
            "BASE_UNMETERED_PATH",
        )


if __name__ == "__main__":
    unittest.main()
