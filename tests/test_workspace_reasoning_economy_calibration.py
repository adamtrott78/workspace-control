"""Controlled ChatGPT/Codex allowance-meter calibration tests."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.economics import (  # noqa: E402
    CalibrationInvariantError,
    CalibrationObservation,
    CalibrationSurface,
    SharedMeterState,
    SurfaceMeterState,
    calibrate_shared_weekly_meter,
)
from workspace_semantic_execution.ports import (  # noqa: E402
    AccountTokenUsageSummary,
    RateLimitBucketSnapshot,
    RateLimitWindowClass,
    RateLimitWindowSnapshot,
    UsageSnapshot,
)


LIMIT_ID = "shared-weekly"
RESET = int(
    datetime(2026, 11, 22, 12, tzinfo=timezone.utc).timestamp()
)


def usage(
    used: int,
    *,
    reset: int = RESET,
    captured_at: str = "2026-11-15T12:00:00+00:00",
) -> UsageSnapshot:
    return UsageSnapshot(
        captured_at=captured_at,
        ordinary_usage_allowed=True,
        rate_limit_buckets=(
            RateLimitBucketSnapshot(
                limit_id=LIMIT_ID,
                limit_name="Shared",
                normal_model_slug=None,
                plan_type="plus",
                windows=(
                    RateLimitWindowSnapshot(
                        source_role="weekly",
                        used_percent=used,
                        window_duration_mins=10080,
                        resets_at=reset,
                        window_class=(
                            RateLimitWindowClass.WEEKLY
                        ),
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


def observation(
    observation_id: str,
    surface: CalibrationSurface,
    *,
    before: int,
    after: int,
    reset_before: int = RESET,
    reset_after: int = RESET,
    isolated: bool = True,
) -> CalibrationObservation:
    return CalibrationObservation(
        observation_id=observation_id,
        surface=surface,
        before=usage(
            before,
            reset=reset_before,
            captured_at="2026-11-15T12:00:00+00:00",
        ),
        after=usage(
            after,
            reset=reset_after,
            captured_at="2026-11-15T12:01:00+00:00",
        ),
        isolation_verified=isolated,
        model_actions=1,
    )


class CalibrationTests(unittest.TestCase):
    def test_shared_positive_movement_across_all_surfaces_is_observed(self):
        rows = []
        for surface in CalibrationSurface:
            rows.extend(
                (
                    observation(
                        f"{surface.value}-1",
                        surface,
                        before=10,
                        after=11,
                    ),
                    observation(
                        f"{surface.value}-2",
                        surface,
                        before=20,
                        after=22,
                    ),
                )
            )

        report = calibrate_shared_weekly_meter(
            rows,
            limit_id=LIMIT_ID,
        )

        self.assertEqual(
            report.shared_state,
            SharedMeterState.SHARED_MOVEMENT_OBSERVED,
        )
        self.assertFalse(report.exact_weight_mapping_known)
        self.assertTrue(
            all(
                item.state
                == SurfaceMeterState.MOVEMENT_OBSERVED
                for item in report.summaries
            )
        )

    def test_zero_percent_movement_is_not_interpreted_as_free(self):
        rows = [
            observation(
                "codex-1",
                CalibrationSurface.CODEX,
                before=10,
                after=11,
            ),
            observation(
                "codex-2",
                CalibrationSurface.CODEX,
                before=20,
                after=21,
            ),
            observation(
                "regular-1",
                CalibrationSurface.REGULAR_CHAT,
                before=30,
                after=31,
            ),
            observation(
                "regular-2",
                CalibrationSurface.REGULAR_CHAT,
                before=40,
                after=41,
            ),
            observation(
                "instant-1",
                CalibrationSurface.INSTANT_CHAT,
                before=50,
                after=50,
            ),
            observation(
                "instant-2",
                CalibrationSurface.INSTANT_CHAT,
                before=60,
                after=60,
            ),
        ]

        report = calibrate_shared_weekly_meter(
            rows,
            limit_id=LIMIT_ID,
        )
        instant = next(
            item
            for item in report.summaries
            if item.surface == CalibrationSurface.INSTANT_CHAT
        )

        self.assertEqual(
            instant.state,
            SurfaceMeterState.NO_MOVEMENT_OBSERVED,
        )
        self.assertEqual(
            instant.zero_movement_observations,
            2,
        )
        self.assertEqual(
            report.shared_state,
            SharedMeterState.PARTIAL_MOVEMENT_OBSERVED,
        )
        self.assertIn(
            "Zero movement is not evidence of zero cost",
            report.notes[1],
        )

    def test_reset_boundary_is_unknown_not_negative_or_zero_cost(self):
        rows = [
            observation(
                "codex-reset-1",
                CalibrationSurface.CODEX,
                before=95,
                after=2,
                reset_after=RESET + 604800,
            ),
            observation(
                "codex-reset-2",
                CalibrationSurface.CODEX,
                before=94,
                after=3,
                reset_after=RESET + 604800,
            ),
        ]

        report = calibrate_shared_weekly_meter(
            rows,
            limit_id=LIMIT_ID,
            required_surfaces=(CalibrationSurface.CODEX,),
        )
        summary = report.summaries[0]
        self.assertEqual(
            summary.state,
            SurfaceMeterState.INSUFFICIENT_EVIDENCE,
        )
        self.assertEqual(summary.unknown_observations, 2)
        self.assertEqual(
            report.shared_state,
            SharedMeterState.UNKNOWN,
        )

    def test_unisolated_observation_is_ineligible(self):
        report = calibrate_shared_weekly_meter(
            (
                observation(
                    "instant-unisolated",
                    CalibrationSurface.INSTANT_CHAT,
                    before=10,
                    after=15,
                    isolated=False,
                ),
            ),
            limit_id=LIMIT_ID,
            required_surfaces=(
                CalibrationSurface.INSTANT_CHAT,
            ),
            minimum_eligible_observations_per_surface=1,
        )
        self.assertEqual(
            report.summaries[0].state,
            SurfaceMeterState.INELIGIBLE,
        )
        self.assertEqual(
            report.summaries[0].eligible_observations,
            0,
        )

    def test_same_or_reversed_snapshot_time_fails_closed(self):
        row = CalibrationObservation(
            observation_id="bad-order",
            surface=CalibrationSurface.CODEX,
            before=usage(
                10,
                captured_at="2026-11-15T12:01:00+00:00",
            ),
            after=usage(
                11,
                captured_at="2026-11-15T12:00:00+00:00",
            ),
            isolation_verified=True,
            model_actions=1,
        )
        with self.assertRaisesRegex(
            CalibrationInvariantError,
            "calibration_snapshot_order_invalid",
        ):
            calibrate_shared_weekly_meter(
                (row,),
                limit_id=LIMIT_ID,
                required_surfaces=(CalibrationSurface.CODEX,),
                minimum_eligible_observations_per_surface=1,
            )

    def test_duplicate_observation_id_fails_closed(self):
        row = observation(
            "duplicate",
            CalibrationSurface.CODEX,
            before=10,
            after=11,
        )
        with self.assertRaisesRegex(
            CalibrationInvariantError,
            "duplicate_calibration_observation_id",
        ):
            calibrate_shared_weekly_meter(
                (row, row),
                limit_id=LIMIT_ID,
                required_surfaces=(CalibrationSurface.CODEX,),
            )


if __name__ == "__main__":
    unittest.main()
