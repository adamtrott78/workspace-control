"""Reasoning Economy execution-ledger tests."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.economics import (  # noqa: E402
    EconomicsInvariantError,
    ExecutionTokenUsage,
    WasteClass,
    build_execution_economics,
    compute_usage_delta,
)
from workspace_semantic_execution.ports import (  # noqa: E402
    AccountTokenUsageSummary,
    RateLimitBucketSnapshot,
    RateLimitWindowClass,
    RateLimitWindowSnapshot,
    UsageSnapshot,
)


def snapshot(
    *,
    used: int | None = 10,
    resets_at: int | None = 2000,
    lifetime: int | None = 1000,
    limit_id: str = "codex",
    extra_weekly: bool = False,
) -> UsageSnapshot:
    windows = ()
    if used is not None:
        windows = (
            RateLimitWindowSnapshot(
                source_role="primary",
                used_percent=used,
                window_duration_mins=10080,
                resets_at=resets_at,
                window_class=RateLimitWindowClass.WEEKLY,
            ),
        )
    buckets = [
        RateLimitBucketSnapshot(
            limit_id=limit_id,
            limit_name="Codex",
            normal_model_slug="gpt-6-luna",
            plan_type="plus",
            windows=windows,
        )
    ]
    if extra_weekly:
        buckets.append(
            RateLimitBucketSnapshot(
                limit_id="another-limit",
                limit_name="Other",
                normal_model_slug=None,
                plan_type="plus",
                windows=(
                    RateLimitWindowSnapshot(
                        source_role="secondary",
                        used_percent=4,
                        window_duration_mins=10080,
                        resets_at=resets_at,
                        window_class=RateLimitWindowClass.WEEKLY,
                    ),
                ),
            )
        )
    return UsageSnapshot(
        captured_at="2026-11-15T12:00:00+00:00",
        ordinary_usage_allowed=True,
        rate_limit_buckets=tuple(buckets),
        token_summary=AccountTokenUsageSummary(
            lifetime_tokens=lifetime,
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
    before: UsageSnapshot | None = None,
    after: UsageSnapshot | None = None,
    token_usage: ExecutionTokenUsage | None = None,
    model_invocations: int = 1,
    waste_class: WasteClass = WasteClass.PRODUCTIVE_REASONING,
    validator_passed: bool | None = True,
    validator_score: float | None = 1.0,
):
    return build_execution_economics(
        execution_id="exec-1",
        work_item_id="work-1",
        parent_execution_id=None,
        executor_id="codex-luna",
        model_id="gpt-6-luna",
        surface_id="codex-cli",
        started_at="2026-11-15T12:00:00+00:00",
        ended_at="2026-11-15T12:01:00+00:00",
        token_usage=token_usage or ExecutionTokenUsage(
            input_tokens=100,
            cached_input_tokens=80,
            output_tokens=20,
            reasoning_output_tokens=5,
            total_tokens=120,
        ),
        model_invocations=model_invocations,
        tool_calls=2,
        retries=0,
        decomposition_depth=0,
        children_spawned=0,
        validator_passed=validator_passed,
        validator_score=validator_score,
        waste_class=waste_class,
        usage_before=before or snapshot(used=10, lifetime=1000),
        usage_after=after or snapshot(used=12, lifetime=1120),
    )


class UsageDeltaTests(unittest.TestCase):
    def test_weekly_delta_is_known_only_with_same_window_identity(self):
        delta = compute_usage_delta(
            snapshot(used=10, resets_at=2000, lifetime=1000),
            snapshot(used=13, resets_at=2000, lifetime=1200),
        )
        self.assertEqual(delta.account_lifetime_token_delta, 200)
        self.assertEqual(
            delta.known_weekly_delta_points(limit_id="codex"),
            3,
        )

    def test_reset_boundary_is_unknown_not_negative_consumption(self):
        delta = compute_usage_delta(
            snapshot(used=97, resets_at=2000),
            snapshot(used=2, resets_at=3000),
        )
        item = delta.allowance_windows[0]
        self.assertEqual(item.comparison_state, "RESET_BOUNDARY")
        self.assertIsNone(item.delta_used_percent)
        self.assertIsNone(
            delta.known_weekly_delta_points(limit_id="codex")
        )

    def test_nonmonotonic_same_reset_is_fail_closed_unknown(self):
        delta = compute_usage_delta(
            snapshot(used=50, resets_at=2000),
            snapshot(used=40, resets_at=2000),
        )
        self.assertEqual(
            delta.allowance_windows[0].comparison_state,
            "NON_MONOTONIC",
        )
        self.assertIsNone(
            delta.known_weekly_delta_points(limit_id="codex")
        )

    def test_missing_account_token_total_remains_unknown(self):
        delta = compute_usage_delta(
            snapshot(lifetime=None),
            snapshot(lifetime=1200),
        )
        self.assertIsNone(delta.account_lifetime_token_delta)

    def test_decreasing_account_token_total_remains_unknown(self):
        delta = compute_usage_delta(
            snapshot(lifetime=2000),
            snapshot(lifetime=1000),
        )
        self.assertIsNone(delta.account_lifetime_token_delta)

    def test_multiple_weekly_buckets_are_ambiguous_without_limit_id(self):
        before = snapshot(used=10, extra_weekly=True)
        after = snapshot(used=12, extra_weekly=True)
        delta = compute_usage_delta(before, after)
        self.assertIsNone(delta.known_weekly_delta_points())
        self.assertEqual(
            delta.known_weekly_delta_points(limit_id="codex"),
            2,
        )


class EconomicsInvariantTests(unittest.TestCase):
    def test_waiting_external_must_use_zero_model_tokens(self):
        for waste_class in (
            WasteClass.WAITING_EXTERNAL,
            WasteClass.POLLING,
            WasteClass.IDLE,
        ):
            with self.subTest(waste_class=waste_class):
                with self.assertRaises(EconomicsInvariantError):
                    economics(
                        token_usage=ExecutionTokenUsage(total_tokens=1),
                        model_invocations=1,
                        waste_class=waste_class,
                    )

    def test_waiting_external_zero_token_record_is_allowed(self):
        record = economics(
            token_usage=ExecutionTokenUsage(
                input_tokens=0,
                cached_input_tokens=0,
                output_tokens=0,
                reasoning_output_tokens=0,
                total_tokens=0,
            ),
            model_invocations=0,
            waste_class=WasteClass.WAITING_EXTERNAL,
            validator_passed=None,
            validator_score=None,
        )
        self.assertEqual(record.model_invocations, 0)

    def test_deterministic_work_can_have_tools_but_no_model_tokens(self):
        record = build_execution_economics(
            execution_id="exec-det",
            work_item_id="work-det",
            parent_execution_id=None,
            executor_id="python",
            model_id="none",
            surface_id="deterministic",
            started_at="2026-11-15T12:00:00+00:00",
            ended_at="2026-11-15T12:00:01+00:00",
            token_usage=ExecutionTokenUsage(total_tokens=0),
            model_invocations=0,
            tool_calls=9,
            retries=0,
            decomposition_depth=0,
            children_spawned=0,
            validator_passed=True,
            validator_score=1.0,
            waste_class=WasteClass.DETERMINISTIC,
            usage_before=snapshot(used=10),
            usage_after=snapshot(used=10),
        )
        self.assertEqual(record.tool_calls, 9)

    def test_negative_counters_fail_closed(self):
        with self.assertRaises(EconomicsInvariantError):
            build_execution_economics(
                execution_id="e",
                work_item_id="w",
                parent_execution_id=None,
                executor_id="x",
                model_id="m",
                surface_id="s",
                started_at="t1",
                ended_at="t2",
                token_usage=ExecutionTokenUsage(total_tokens=0),
                model_invocations=-1,
                tool_calls=0,
                retries=0,
                decomposition_depth=0,
                children_spawned=0,
                validator_passed=None,
                validator_score=None,
                waste_class=WasteClass.PRODUCTIVE_REASONING,
                usage_before=snapshot(),
                usage_after=snapshot(),
            )


class EfficiencyMetricTests(unittest.TestCase):
    def test_verified_progress_per_allowance_point(self):
        record = economics(
            before=snapshot(used=10),
            after=snapshot(used=12),
            validator_passed=True,
            validator_score=0.8,
        )
        self.assertAlmostEqual(
            record.verified_progress_per_weekly_allowance_point(
                limit_id="codex"
            ),
            0.4,
        )

    def test_zero_observed_allowance_delta_is_not_infinite_efficiency(self):
        record = economics(
            before=snapshot(used=10),
            after=snapshot(used=10),
        )
        self.assertIsNone(
            record.verified_progress_per_weekly_allowance_point(
                limit_id="codex"
            )
        )

    def test_failed_validator_produces_zero_verified_progress(self):
        record = economics(
            validator_passed=False,
            validator_score=0.0,
        )
        self.assertEqual(
            record.verified_progress_per_weekly_allowance_point(
                limit_id="codex"
            ),
            0.0,
        )

    def test_unknown_validator_is_unknown_efficiency(self):
        record = economics(
            validator_passed=None,
            validator_score=None,
        )
        self.assertIsNone(
            record.verified_progress_per_weekly_allowance_point(
                limit_id="codex"
            )
        )


if __name__ == "__main__":
    unittest.main()
