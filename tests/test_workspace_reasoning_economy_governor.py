"""Reasoning Economy weekly governor and holdout-promotion tests."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.domain import WorkDisposition  # noqa: E402
from workspace_semantic_execution.economics import (  # noqa: E402
    BillingMode,
    ExecutionTokenUsage,
    GovernorCandidate,
    GovernorOutcome,
    HoldoutTaskResult,
    WasteClass,
    WeeklyBudgetPolicy,
    build_execution_economics,
    decide_weekly_route,
    evaluate_holdout_promotion,
    project_weekly_burn,
)
from workspace_semantic_execution.ports import (  # noqa: E402
    AccountTokenUsageSummary,
    RateLimitBucketSnapshot,
    RateLimitWindowClass,
    RateLimitWindowSnapshot,
    UsageSnapshot,
)


LIMIT_ID = "codex"
RESET = int(
    datetime(2026, 11, 22, 12, 0, tzinfo=timezone.utc).timestamp()
)


def usage(
    used: int,
    *,
    captured_at: str = "2026-11-15T12:00:00+00:00",
    limit_id: str = LIMIT_ID,
    ordinary: bool | None = True,
    include_weekly: bool = True,
) -> UsageSnapshot:
    windows = ()
    if include_weekly:
        windows = (
            RateLimitWindowSnapshot(
                source_role="weekly",
                used_percent=used,
                window_duration_mins=10080,
                resets_at=RESET,
                window_class=RateLimitWindowClass.WEEKLY,
            ),
        )
    return UsageSnapshot(
        captured_at=captured_at,
        ordinary_usage_allowed=ordinary,
        rate_limit_buckets=(
            RateLimitBucketSnapshot(
                limit_id=limit_id,
                limit_name="Codex",
                normal_model_slug="gpt-test",
                plan_type="plus",
                windows=windows,
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


def record(
    *,
    execution_id: str,
    executor_id: str,
    before_used: int,
    cost: int,
    passed: bool = True,
    score: float = 0.95,
):
    return build_execution_economics(
        execution_id=execution_id,
        work_item_id=f"work:{execution_id}",
        parent_execution_id=None,
        executor_id=executor_id,
        model_id="model",
        surface_id="subscription",
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
        validator_passed=passed,
        validator_score=score,
        waste_class=WasteClass.PRODUCTIVE_REASONING,
        usage_before=usage(before_used),
        usage_after=usage(before_used + cost),
    )


def candidate(
    executor_id: str,
    *,
    scarcity_rank: int,
    billing_mode: BillingMode = BillingMode.INCLUDED_SUBSCRIPTION,
    limit_id: str | None = LIMIT_ID,
) -> GovernorCandidate:
    return GovernorCandidate(
        executor_id=executor_id,
        scarcity_rank=scarcity_rank,
        billing_mode=billing_mode,
        weekly_limit_id=limit_id,
    )


POLICY = WeeklyBudgetPolicy(
    limit_id=LIMIT_ID,
    reserve_percent_points=20,
    max_single_action_percent_points=10,
    min_calibration_samples=3,
    minimum_validator_pass_rate=1.0,
    minimum_validator_score=0.80,
)


class BurnProjectionTests(unittest.TestCase):
    def test_projects_end_of_week_from_observed_burn(self):
        projection = project_weekly_burn(
            (
                usage(
                    20,
                    captured_at="2026-11-15T12:00:00+00:00",
                ),
                usage(
                    22,
                    captured_at="2026-11-16T12:00:00+00:00",
                ),
            ),
            policy=POLICY,
        )

        self.assertEqual(projection.state.value, "PROJECTED")
        self.assertAlmostEqual(
            projection.observed_points_per_day,
            2.0,
        )
        self.assertAlmostEqual(
            projection.projected_end_used_percent,
            34.0,
        )

    def test_insufficient_history_remains_unknown(self):
        projection = project_weekly_burn(
            (usage(20),),
            policy=POLICY,
        )
        self.assertEqual(
            projection.state.value,
            "INSUFFICIENT_HISTORY",
        )
        self.assertIsNone(
            projection.projected_end_used_percent
        )


class GovernorTests(unittest.TestCase):
    def test_too_large_decomposes_before_any_allowance_decision(self):
        decision = decide_weekly_route(
            disposition=WorkDisposition.TOO_LARGE,
            current_usage=usage(90, include_weekly=False),
            usage_history=(),
            candidates=(
                candidate(
                    "forbidden-api",
                    scarcity_rank=0,
                    billing_mode=BillingMode.API_BILLED,
                    limit_id=None,
                ),
            ),
            economics_records=(),
            policy=POLICY,
        )
        self.assertEqual(
            decision.outcome,
            GovernorOutcome.DECOMPOSE_FIRST,
        )

    def test_api_billed_only_candidate_is_rejected(self):
        decision = decide_weekly_route(
            disposition=WorkDisposition.INTRINSICALLY_DIFFICULT,
            current_usage=usage(10),
            usage_history=(usage(10),),
            candidates=(
                candidate(
                    "api",
                    scarcity_rank=0,
                    billing_mode=BillingMode.API_BILLED,
                    limit_id=None,
                ),
            ),
            economics_records=(),
            policy=POLICY,
        )
        self.assertEqual(
            decision.outcome,
            GovernorOutcome.REJECT_BILLING,
        )

    def test_missing_weekly_telemetry_defers_instead_of_guessing(self):
        decision = decide_weekly_route(
            disposition=WorkDisposition.EXECUTABLE,
            current_usage=usage(10, include_weekly=False),
            usage_history=(),
            candidates=(candidate("cheap", scarcity_rank=0),),
            economics_records=(),
            policy=POLICY,
        )
        self.assertEqual(
            decision.outcome,
            GovernorOutcome.DEFER_TELEMETRY,
        )

    def test_insufficient_calibration_defers(self):
        decision = decide_weekly_route(
            disposition=WorkDisposition.EXECUTABLE,
            current_usage=usage(20),
            usage_history=(usage(20),),
            candidates=(candidate("cheap", scarcity_rank=0),),
            economics_records=(
                record(
                    execution_id="1",
                    executor_id="cheap",
                    before_used=5,
                    cost=2,
                ),
            ),
            policy=POLICY,
        )
        self.assertEqual(
            decision.outcome,
            GovernorOutcome.DEFER_CALIBRATION,
        )

    def test_least_scarce_quality_qualified_executor_is_selected(self):
        rows = []
        for i in range(3):
            rows.append(
                record(
                    execution_id=f"cheap-{i}",
                    executor_id="cheap",
                    before_used=5 + i * 3,
                    cost=2,
                    score=0.90,
                )
            )
            rows.append(
                record(
                    execution_id=f"strong-{i}",
                    executor_id="strong",
                    before_used=30 + i * 5,
                    cost=4,
                    score=0.98,
                )
            )
        decision = decide_weekly_route(
            disposition=WorkDisposition.EXECUTABLE,
            current_usage=usage(20),
            usage_history=(usage(20),),
            candidates=(
                candidate("cheap", scarcity_rank=0),
                candidate("strong", scarcity_rank=5),
            ),
            economics_records=rows,
            policy=POLICY,
        )
        self.assertEqual(
            decision.outcome,
            GovernorOutcome.SELECTED,
        )
        self.assertEqual(
            decision.selected_executor_id,
            "cheap",
        )
        self.assertEqual(
            decision.projected_used_after_action,
            22,
        )

    def test_cheaper_executor_below_quality_floor_does_not_get_promoted(self):
        rows = []
        for i in range(3):
            rows.append(
                record(
                    execution_id=f"cheap-{i}",
                    executor_id="cheap",
                    before_used=5 + i * 3,
                    cost=2,
                    score=0.70,
                )
            )
            rows.append(
                record(
                    execution_id=f"strong-{i}",
                    executor_id="strong",
                    before_used=30 + i * 5,
                    cost=4,
                    score=0.95,
                )
            )
        decision = decide_weekly_route(
            disposition=WorkDisposition.INTRINSICALLY_DIFFICULT,
            current_usage=usage(20),
            usage_history=(usage(20),),
            candidates=(
                candidate("cheap", scarcity_rank=0),
                candidate("strong", scarcity_rank=5),
            ),
            economics_records=rows,
            policy=POLICY,
        )
        self.assertEqual(
            decision.outcome,
            GovernorOutcome.SELECTED,
        )
        self.assertEqual(
            decision.selected_executor_id,
            "strong",
        )

    def test_reserve_headroom_rejects_action_that_crosses_ceiling(self):
        rows = tuple(
            record(
                execution_id=f"x-{i}",
                executor_id="x",
                before_used=5 + i * 8,
                cost=6,
            )
            for i in range(3)
        )
        decision = decide_weekly_route(
            disposition=WorkDisposition.EXECUTABLE,
            current_usage=usage(75),
            usage_history=(usage(75),),
            candidates=(candidate("x", scarcity_rank=0),),
            economics_records=rows,
            policy=POLICY,
        )
        self.assertEqual(
            decision.outcome,
            GovernorOutcome.REJECT_BUDGET,
        )
        self.assertEqual(
            decision.budget.spend_ceiling_percent,
            80,
        )

    def test_burn_projection_can_protect_future_reserve(self):
        rows = tuple(
            record(
                execution_id=f"x-{i}",
                executor_id="x",
                before_used=5 + i * 5,
                cost=2,
            )
            for i in range(3)
        )
        history = (
            usage(
                40,
                captured_at="2026-11-15T12:00:00+00:00",
            ),
            usage(
                50,
                captured_at="2026-11-16T12:00:00+00:00",
            ),
        )
        decision = decide_weekly_route(
            disposition=WorkDisposition.EXECUTABLE,
            current_usage=history[-1],
            usage_history=history,
            candidates=(candidate("x", scarcity_rank=0),),
            economics_records=rows,
            policy=POLICY,
        )
        self.assertEqual(
            decision.outcome,
            GovernorOutcome.REJECT_BUDGET,
        )
        self.assertGreater(
            decision.burn_projection.projected_end_used_percent,
            decision.budget.spend_ceiling_percent,
        )


class HoldoutPromotionTests(unittest.TestCase):
    def rows(
        self,
        *,
        candidate_score: float = 0.95,
        candidate_cost: int = 2,
        candidate_failure_at: int | None = None,
    ):
        rows = []
        for i in range(5):
            work = f"work-{i}"
            rows.append(
                HoldoutTaskResult(
                    policy_id="baseline",
                    work_item_id=work,
                    validator_passed=True,
                    validator_score=0.95,
                    weekly_allowance_points=3,
                )
            )
            rows.append(
                HoldoutTaskResult(
                    policy_id="candidate",
                    work_item_id=work,
                    validator_passed=(
                        candidate_failure_at != i
                    ),
                    validator_score=candidate_score,
                    weekly_allowance_points=candidate_cost,
                )
            )
        return rows

    def test_promotes_only_on_matched_holdout_quality_and_lower_allowance(self):
        decision = evaluate_holdout_promotion(
            baseline_policy_id="baseline",
            candidate_policy_id="candidate",
            results=self.rows(),
        )
        self.assertTrue(decision.promote)
        self.assertEqual(
            decision.reason,
            "candidate_improves_allowance_without_quality_regression",
        )
        self.assertEqual(decision.baseline_allowance_points, 15)
        self.assertEqual(decision.candidate_allowance_points, 10)

    def test_failed_holdout_task_blocks_promotion(self):
        decision = evaluate_holdout_promotion(
            baseline_policy_id="baseline",
            candidate_policy_id="candidate",
            results=self.rows(candidate_failure_at=2),
        )
        self.assertFalse(decision.promote)
        self.assertEqual(
            decision.reason,
            "candidate_has_failed_holdout_task",
        )

    def test_quality_regression_blocks_promotion_even_when_cheaper(self):
        decision = evaluate_holdout_promotion(
            baseline_policy_id="baseline",
            candidate_policy_id="candidate",
            results=self.rows(candidate_score=0.85),
        )
        self.assertFalse(decision.promote)
        self.assertEqual(
            decision.reason,
            "candidate_quality_regresses_baseline",
        )

    def test_unmatched_holdout_sets_do_not_promote(self):
        rows = self.rows()
        rows = [
            row
            for row in rows
            if not (
                row.policy_id == "candidate"
                and row.work_item_id == "work-4"
            )
        ]
        decision = evaluate_holdout_promotion(
            baseline_policy_id="baseline",
            candidate_policy_id="candidate",
            results=rows,
        )
        self.assertFalse(decision.promote)
        self.assertEqual(
            decision.reason,
            "holdout_task_sets_incomplete_or_unmatched",
        )


if __name__ == "__main__":
    unittest.main()
