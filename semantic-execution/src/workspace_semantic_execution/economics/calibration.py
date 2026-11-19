"""Controlled subscription-meter calibration observations.

Calibration is deliberately conservative:
- only isolated, single-action observations are eligible;
- weekly deltas must be comparable within one reset window;
- positive movement is evidence that a surface affects a meter;
- zero movement is only "not observed" because percent meters have finite
  resolution and can never be interpreted as free usage;
- raw token totals are never converted into weighted allowance cost.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from .._compat import StrEnum
from ..ports import RateLimitWindowClass, UsageSnapshot
from .ledger import compute_usage_delta


class CalibrationInvariantError(RuntimeError):
    """Fail-closed controlled-calibration invariant."""


class CalibrationSurface(StrEnum):
    CODEX = "CODEX"
    REGULAR_CHAT = "REGULAR_CHAT"
    INSTANT_CHAT = "INSTANT_CHAT"


class SurfaceMeterState(StrEnum):
    MOVEMENT_OBSERVED = "MOVEMENT_OBSERVED"
    NO_MOVEMENT_OBSERVED = "NO_MOVEMENT_OBSERVED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    INELIGIBLE = "INELIGIBLE"


class SharedMeterState(StrEnum):
    SHARED_MOVEMENT_OBSERVED = "SHARED_MOVEMENT_OBSERVED"
    PARTIAL_MOVEMENT_OBSERVED = "PARTIAL_MOVEMENT_OBSERVED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class CalibrationObservation:
    observation_id: str
    surface: CalibrationSurface
    before: UsageSnapshot
    after: UsageSnapshot
    isolation_verified: bool
    model_actions: int = 1


@dataclass(frozen=True)
class SurfaceCalibrationSummary:
    surface: CalibrationSurface
    eligible_observations: int
    comparable_observations: int
    positive_movement_observations: int
    zero_movement_observations: int
    unknown_observations: int
    state: SurfaceMeterState


@dataclass(frozen=True)
class MeterCalibrationReport:
    limit_id: str
    summaries: tuple[SurfaceCalibrationSummary, ...]
    shared_state: SharedMeterState
    exact_weight_mapping_known: bool
    notes: tuple[str, ...]


def _snapshot_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise CalibrationInvariantError(
            "calibration_snapshot_time_invalid"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise CalibrationInvariantError(
            "calibration_snapshot_timezone_required"
        )
    return parsed.astimezone(timezone.utc)


def _validate_observation(
    observation: CalibrationObservation,
) -> None:
    if not observation.observation_id:
        raise CalibrationInvariantError(
            "calibration_observation_id_required"
        )
    if type(observation.isolation_verified) is not bool:
        raise CalibrationInvariantError(
            "calibration_isolation_flag_invalid"
        )
    if (
        type(observation.model_actions) is not int
        or observation.model_actions < 0
    ):
        raise CalibrationInvariantError(
            "calibration_model_actions_invalid"
        )
    before_time = _snapshot_time(
        observation.before.captured_at
    )
    after_time = _snapshot_time(
        observation.after.captured_at
    )
    if after_time <= before_time:
        raise CalibrationInvariantError(
            "calibration_snapshot_order_invalid"
        )
    if (
        observation.isolation_verified
        and observation.model_actions != 1
    ):
        raise CalibrationInvariantError(
            "isolated_calibration_requires_one_model_action"
        )


def _weekly_delta(
    observation: CalibrationObservation,
    *,
    limit_id: str,
) -> int | None:
    delta = compute_usage_delta(
        observation.before,
        observation.after,
    )
    return delta.known_allowance_delta_points(
        window_class=RateLimitWindowClass.WEEKLY,
        limit_id=limit_id,
    )


def calibrate_shared_weekly_meter(
    observations: Iterable[CalibrationObservation],
    *,
    limit_id: str,
    required_surfaces: Iterable[CalibrationSurface] = (
        CalibrationSurface.CODEX,
        CalibrationSurface.REGULAR_CHAT,
        CalibrationSurface.INSTANT_CHAT,
    ),
    minimum_eligible_observations_per_surface: int = 2,
) -> MeterCalibrationReport:
    if not limit_id:
        raise CalibrationInvariantError(
            "calibration_limit_id_required"
        )
    if minimum_eligible_observations_per_surface < 1:
        raise CalibrationInvariantError(
            "calibration_minimum_observations_invalid"
        )

    rows = tuple(observations)
    seen_ids: set[str] = set()
    for row in rows:
        _validate_observation(row)
        if row.observation_id in seen_ids:
            raise CalibrationInvariantError(
                "duplicate_calibration_observation_id"
            )
        seen_ids.add(row.observation_id)

    surfaces = tuple(dict.fromkeys(required_surfaces))
    if not surfaces:
        raise CalibrationInvariantError(
            "calibration_required_surfaces_empty"
        )

    summaries: list[SurfaceCalibrationSummary] = []
    for surface in surfaces:
        surface_rows = tuple(
            row for row in rows
            if row.surface == surface
        )
        eligible = tuple(
            row for row in surface_rows
            if row.isolation_verified
            and row.model_actions == 1
        )
        comparable = 0
        positive = 0
        zero = 0
        unknown = 0
        for row in eligible:
            value = _weekly_delta(
                row,
                limit_id=limit_id,
            )
            if value is None:
                unknown += 1
                continue
            comparable += 1
            if value > 0:
                positive += 1
            else:
                # Zero is below meter resolution, never evidence of free use.
                zero += 1

        if not eligible:
            state = SurfaceMeterState.INELIGIBLE
        elif (
            len(eligible)
            < minimum_eligible_observations_per_surface
        ):
            state = SurfaceMeterState.INSUFFICIENT_EVIDENCE
        elif positive > 0:
            state = SurfaceMeterState.MOVEMENT_OBSERVED
        elif comparable == len(eligible) and zero == len(eligible):
            state = SurfaceMeterState.NO_MOVEMENT_OBSERVED
        else:
            state = SurfaceMeterState.INSUFFICIENT_EVIDENCE

        summaries.append(
            SurfaceCalibrationSummary(
                surface=surface,
                eligible_observations=len(eligible),
                comparable_observations=comparable,
                positive_movement_observations=positive,
                zero_movement_observations=zero,
                unknown_observations=unknown,
                state=state,
            )
        )

    states = {item.surface: item.state for item in summaries}
    if all(
        states[surface]
        == SurfaceMeterState.MOVEMENT_OBSERVED
        for surface in surfaces
    ):
        shared = SharedMeterState.SHARED_MOVEMENT_OBSERVED
    elif any(
        states[surface]
        == SurfaceMeterState.MOVEMENT_OBSERVED
        for surface in surfaces
    ):
        shared = SharedMeterState.PARTIAL_MOVEMENT_OBSERVED
    else:
        shared = SharedMeterState.UNKNOWN

    notes = (
        "Positive comparable percent-point movement is evidence that the "
        "surface affects the selected weekly meter.",
        "Zero movement is not evidence of zero cost because meter resolution "
        "may hide small allowance consumption.",
        "This calibration does not infer weighted allowance cost from raw "
        "token totals.",
    )
    return MeterCalibrationReport(
        limit_id=limit_id,
        summaries=tuple(summaries),
        shared_state=shared,
        exact_weight_mapping_known=False,
        notes=notes,
    )
