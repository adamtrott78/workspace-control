"""Deterministic subscription-allowance governor and policy promotion.

The governor never prices work in API dollars. It uses only observed
subscription allowance windows plus validator-backed historical evidence.
Unknown meter relationships, missing quality evidence, and API-billed
candidates fail closed.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import mean
from typing import Iterable

from .._compat import StrEnum
from ..domain import WorkDisposition
from ..ports import (
    RateLimitWindowClass,
    RateLimitWindowSnapshot,
    UsageSnapshot,
)
from .ledger import ExecutionEconomics


class GovernorInvariantError(RuntimeError):
    """Fail-closed reasoning-economy governor invariant."""


class BillingMode(StrEnum):
    INCLUDED_SUBSCRIPTION = "INCLUDED_SUBSCRIPTION"
    API_BILLED = "API_BILLED"
    UNKNOWN = "UNKNOWN"


class GovernorOutcome(StrEnum):
    SELECTED = "SELECTED"
    DECOMPOSE_FIRST = "DECOMPOSE_FIRST"
    DEFER_TELEMETRY = "DEFER_TELEMETRY"
    DEFER_CALIBRATION = "DEFER_CALIBRATION"
    REJECT_BUDGET = "REJECT_BUDGET"
    REJECT_BILLING = "REJECT_BILLING"
    NO_QUALIFIED_EXECUTOR = "NO_QUALIFIED_EXECUTOR"


class BurnProjectionState(StrEnum):
    PROJECTED = "PROJECTED"
    INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"
    RESET_BOUNDARY = "RESET_BOUNDARY"
    INVALID_HISTORY = "INVALID_HISTORY"
    RESET_UNKNOWN = "RESET_UNKNOWN"


@dataclass(frozen=True)
class WeeklyBudgetPolicy:
    limit_id: str
    reserve_percent_points: int = 20
    max_single_action_percent_points: int = 10
    min_calibration_samples: int = 3
    minimum_validator_pass_rate: float = 1.0
    minimum_validator_score: float = 0.80
    minimum_projection_interval_seconds: int = 60

    def validate(self) -> None:
        if not self.limit_id:
            raise GovernorInvariantError("limit_id_required")
        if not 0 <= self.reserve_percent_points < 100:
            raise GovernorInvariantError("reserve_percent_points_invalid")
        if not 1 <= self.max_single_action_percent_points <= 100:
            raise GovernorInvariantError(
                "max_single_action_percent_points_invalid"
            )
        if self.min_calibration_samples < 1:
            raise GovernorInvariantError(
                "min_calibration_samples_invalid"
            )
        if not 0.0 <= self.minimum_validator_pass_rate <= 1.0:
            raise GovernorInvariantError(
                "minimum_validator_pass_rate_invalid"
            )
        if not 0.0 <= self.minimum_validator_score <= 1.0:
            raise GovernorInvariantError(
                "minimum_validator_score_invalid"
            )
        if self.minimum_projection_interval_seconds < 1:
            raise GovernorInvariantError(
                "minimum_projection_interval_seconds_invalid"
            )


@dataclass(frozen=True)
class GovernorCandidate:
    executor_id: str
    scarcity_rank: int
    billing_mode: BillingMode
    weekly_limit_id: str | None

    def validate(self) -> None:
        if not self.executor_id:
            raise GovernorInvariantError(
                "candidate_executor_id_required"
            )
        if self.scarcity_rank < 0:
            raise GovernorInvariantError(
                "candidate_scarcity_rank_invalid"
            )
        if (
            self.billing_mode == BillingMode.INCLUDED_SUBSCRIPTION
            and not self.weekly_limit_id
        ):
            raise GovernorInvariantError(
                "subscription_candidate_limit_id_required"
            )


@dataclass(frozen=True)
class WeeklyBudgetState:
    limit_id: str
    used_percent: int
    reserve_percent_points: int
    spend_ceiling_percent: int
    spendable_remaining_points: int
    resets_at: int | None
    ordinary_usage_allowed: bool | None


@dataclass(frozen=True)
class WeeklyBurnProjection:
    state: BurnProjectionState
    limit_id: str
    observed_points_per_day: float | None
    projected_end_used_percent: float | None
    elapsed_seconds: float | None
    remaining_seconds: float | None


@dataclass(frozen=True)
class ExecutorCalibrationEvidence:
    executor_id: str
    total_records: int
    calibrated_samples: int
    validator_samples: int
    validator_pass_rate: float | None
    minimum_observed_validator_score: float | None
    conservative_weekly_cost_points: int | None
    mean_verified_progress_per_point: float | None

    @property
    def quality_known(self) -> bool:
        return (
            self.validator_pass_rate is not None
            and self.minimum_observed_validator_score is not None
        )


@dataclass(frozen=True)
class GovernorDecision:
    outcome: GovernorOutcome
    reason: str
    selected_executor_id: str | None
    budget: WeeklyBudgetState | None
    burn_projection: WeeklyBurnProjection | None
    projected_used_after_action: float | None
    evidence: tuple[ExecutorCalibrationEvidence, ...]


@dataclass(frozen=True)
class HoldoutTaskResult:
    policy_id: str
    work_item_id: str
    validator_passed: bool
    validator_score: float
    weekly_allowance_points: int


@dataclass(frozen=True)
class PolicyPromotionDecision:
    promote: bool
    reason: str
    baseline_policy_id: str
    candidate_policy_id: str
    task_count: int
    baseline_mean_score: float | None
    candidate_mean_score: float | None
    baseline_allowance_points: int | None
    candidate_allowance_points: int | None


def _parse_captured_at(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise GovernorInvariantError(
            "usage_snapshot_captured_at_invalid"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise GovernorInvariantError(
            "usage_snapshot_captured_at_timezone_required"
        )
    return parsed.astimezone(timezone.utc)


def _unique_weekly_window(
    snapshot: UsageSnapshot,
    *,
    limit_id: str,
) -> RateLimitWindowSnapshot | None:
    matches = [
        window
        for bucket in snapshot.rate_limit_buckets
        if bucket.limit_id == limit_id
        for window in bucket.windows
        if window.window_class == RateLimitWindowClass.WEEKLY
    ]
    if len(matches) != 1:
        return None
    window = matches[0]
    if not 0 <= window.used_percent <= 100:
        raise GovernorInvariantError(
            "weekly_used_percent_out_of_range"
        )
    return window


def weekly_budget_state(
    snapshot: UsageSnapshot,
    *,
    policy: WeeklyBudgetPolicy,
) -> WeeklyBudgetState | None:
    policy.validate()
    window = _unique_weekly_window(
        snapshot,
        limit_id=policy.limit_id,
    )
    if window is None:
        return None
    ceiling = 100 - policy.reserve_percent_points
    return WeeklyBudgetState(
        limit_id=policy.limit_id,
        used_percent=window.used_percent,
        reserve_percent_points=policy.reserve_percent_points,
        spend_ceiling_percent=ceiling,
        spendable_remaining_points=max(
            0,
            ceiling - window.used_percent,
        ),
        resets_at=window.resets_at,
        ordinary_usage_allowed=snapshot.ordinary_usage_allowed,
    )


def project_weekly_burn(
    history: Iterable[UsageSnapshot],
    *,
    policy: WeeklyBudgetPolicy,
) -> WeeklyBurnProjection:
    policy.validate()
    samples = tuple(history)
    if len(samples) < 2:
        return WeeklyBurnProjection(
            state=BurnProjectionState.INSUFFICIENT_HISTORY,
            limit_id=policy.limit_id,
            observed_points_per_day=None,
            projected_end_used_percent=None,
            elapsed_seconds=None,
            remaining_seconds=None,
        )

    left = samples[-2]
    right = samples[-1]
    left_window = _unique_weekly_window(
        left,
        limit_id=policy.limit_id,
    )
    right_window = _unique_weekly_window(
        right,
        limit_id=policy.limit_id,
    )
    if left_window is None or right_window is None:
        return WeeklyBurnProjection(
            state=BurnProjectionState.INVALID_HISTORY,
            limit_id=policy.limit_id,
            observed_points_per_day=None,
            projected_end_used_percent=None,
            elapsed_seconds=None,
            remaining_seconds=None,
        )
    if (
        left_window.resets_at is not None
        and right_window.resets_at is not None
        and left_window.resets_at != right_window.resets_at
    ):
        return WeeklyBurnProjection(
            state=BurnProjectionState.RESET_BOUNDARY,
            limit_id=policy.limit_id,
            observed_points_per_day=None,
            projected_end_used_percent=None,
            elapsed_seconds=None,
            remaining_seconds=None,
        )
    if right_window.resets_at is None:
        return WeeklyBurnProjection(
            state=BurnProjectionState.RESET_UNKNOWN,
            limit_id=policy.limit_id,
            observed_points_per_day=None,
            projected_end_used_percent=None,
            elapsed_seconds=None,
            remaining_seconds=None,
        )

    left_time = _parse_captured_at(left.captured_at)
    right_time = _parse_captured_at(right.captured_at)
    elapsed = (right_time - left_time).total_seconds()
    delta = right_window.used_percent - left_window.used_percent
    if (
        elapsed < policy.minimum_projection_interval_seconds
        or delta < 0
    ):
        return WeeklyBurnProjection(
            state=BurnProjectionState.INVALID_HISTORY,
            limit_id=policy.limit_id,
            observed_points_per_day=None,
            projected_end_used_percent=None,
            elapsed_seconds=elapsed,
            remaining_seconds=None,
        )

    reset_time = datetime.fromtimestamp(
        right_window.resets_at,
        tz=timezone.utc,
    )
    remaining = max(
        0.0,
        (reset_time - right_time).total_seconds(),
    )
    points_per_second = delta / elapsed
    points_per_day = points_per_second * 86400.0
    projected = (
        right_window.used_percent
        + points_per_second * remaining
    )
    return WeeklyBurnProjection(
        state=BurnProjectionState.PROJECTED,
        limit_id=policy.limit_id,
        observed_points_per_day=points_per_day,
        projected_end_used_percent=projected,
        elapsed_seconds=elapsed,
        remaining_seconds=remaining,
    )


def summarize_executor_evidence(
    records: Iterable[ExecutionEconomics],
    *,
    executor_id: str,
    limit_id: str,
) -> ExecutorCalibrationEvidence:
    matched = tuple(
        item
        for item in records
        if item.executor_id == executor_id
    )
    validator_records = tuple(
        item
        for item in matched
        if item.validator_passed is not None
    )
    pass_rate = None
    if validator_records:
        pass_rate = sum(
            1
            for item in validator_records
            if item.validator_passed is True
        ) / len(validator_records)

    scored = tuple(
        item.validator_score
        for item in validator_records
        if item.validator_score is not None
    )
    minimum_score = min(scored) if scored else None

    calibrated = []
    efficiencies = []
    for item in matched:
        delta = item.usage_delta.known_weekly_delta_points(
            limit_id=limit_id,
        )
        # Zero is below meter resolution and cannot calibrate action cost.
        if delta is None or delta <= 0:
            continue
        if (
            item.validator_passed is None
            or item.validator_score is None
        ):
            continue
        calibrated.append((item, delta))
        efficiency = (
            item.verified_progress_per_weekly_allowance_point(
                limit_id=limit_id,
            )
        )
        if efficiency is not None:
            efficiencies.append(efficiency)

    conservative_cost = (
        max(delta for _, delta in calibrated)
        if calibrated
        else None
    )
    return ExecutorCalibrationEvidence(
        executor_id=executor_id,
        total_records=len(matched),
        calibrated_samples=len(calibrated),
        validator_samples=len(validator_records),
        validator_pass_rate=pass_rate,
        minimum_observed_validator_score=minimum_score,
        conservative_weekly_cost_points=conservative_cost,
        mean_verified_progress_per_point=(
            mean(efficiencies)
            if efficiencies
            else None
        ),
    )


def decide_weekly_route(
    *,
    disposition: WorkDisposition,
    current_usage: UsageSnapshot,
    usage_history: Iterable[UsageSnapshot],
    candidates: Iterable[GovernorCandidate],
    economics_records: Iterable[ExecutionEconomics],
    policy: WeeklyBudgetPolicy,
) -> GovernorDecision:
    policy.validate()
    candidate_list = tuple(candidates)
    if not candidate_list:
        raise GovernorInvariantError("candidates_required")
    for candidate in candidate_list:
        candidate.validate()

    if disposition == WorkDisposition.TOO_LARGE:
        return GovernorDecision(
            outcome=GovernorOutcome.DECOMPOSE_FIRST,
            reason="work_is_decomposable_before_escalation",
            selected_executor_id=None,
            budget=None,
            burn_projection=None,
            projected_used_after_action=None,
            evidence=(),
        )

    subscription = tuple(
        item
        for item in candidate_list
        if item.billing_mode
        == BillingMode.INCLUDED_SUBSCRIPTION
    )
    if not subscription:
        if any(
            item.billing_mode == BillingMode.API_BILLED
            for item in candidate_list
        ):
            return GovernorDecision(
                outcome=GovernorOutcome.REJECT_BILLING,
                reason="api_billing_is_not_authorized",
                selected_executor_id=None,
                budget=None,
                burn_projection=None,
                projected_used_after_action=None,
                evidence=(),
            )
        return GovernorDecision(
            outcome=GovernorOutcome.DEFER_CALIBRATION,
            reason="no_included_subscription_candidate",
            selected_executor_id=None,
            budget=None,
            burn_projection=None,
            projected_used_after_action=None,
            evidence=(),
        )

    budget = weekly_budget_state(
        current_usage,
        policy=policy,
    )
    if budget is None:
        return GovernorDecision(
            outcome=GovernorOutcome.DEFER_TELEMETRY,
            reason="unique_weekly_allowance_window_unavailable",
            selected_executor_id=None,
            budget=None,
            burn_projection=None,
            projected_used_after_action=None,
            evidence=(),
        )
    burn = project_weekly_burn(
        usage_history,
        policy=policy,
    )
    if budget.ordinary_usage_allowed is False:
        return GovernorDecision(
            outcome=GovernorOutcome.REJECT_BUDGET,
            reason="ordinary_subscription_usage_not_allowed",
            selected_executor_id=None,
            budget=budget,
            burn_projection=burn,
            projected_used_after_action=None,
            evidence=(),
        )

    records = tuple(economics_records)
    evidence = tuple(
        summarize_executor_evidence(
            records,
            executor_id=candidate.executor_id,
            limit_id=policy.limit_id,
        )
        for candidate in sorted(
            subscription,
            key=lambda item: (
                item.scarcity_rank,
                item.executor_id,
            ),
        )
    )
    by_executor = {
        item.executor_id: item
        for item in evidence
    }

    calibrated = []
    quality_rejected = []
    budget_rejected = []
    for candidate in sorted(
        subscription,
        key=lambda item: (
            item.scarcity_rank,
            item.executor_id,
        ),
    ):
        if candidate.weekly_limit_id != policy.limit_id:
            continue
        item = by_executor[candidate.executor_id]
        if (
            item.calibrated_samples
            < policy.min_calibration_samples
            or not item.quality_known
            or item.conservative_weekly_cost_points is None
        ):
            continue
        if (
            item.validator_pass_rate
            < policy.minimum_validator_pass_rate
            or item.minimum_observed_validator_score
            < policy.minimum_validator_score
        ):
            quality_rejected.append(candidate.executor_id)
            continue

        cost = item.conservative_weekly_cost_points
        projected_after = budget.used_percent + cost
        if (
            burn.state == BurnProjectionState.PROJECTED
            and burn.projected_end_used_percent is not None
        ):
            projected_after = max(
                projected_after,
                burn.projected_end_used_percent + cost,
            )
        if (
            cost > policy.max_single_action_percent_points
            or projected_after > budget.spend_ceiling_percent
        ):
            budget_rejected.append(candidate.executor_id)
            continue
        calibrated.append(
            (
                candidate,
                item,
                projected_after,
            )
        )

    if calibrated:
        candidate, item, projected_after = calibrated[0]
        return GovernorDecision(
            outcome=GovernorOutcome.SELECTED,
            reason=(
                "least_scarce_calibrated_executor_within_"
                "quality_and_weekly_reserve"
            ),
            selected_executor_id=candidate.executor_id,
            budget=budget,
            burn_projection=burn,
            projected_used_after_action=projected_after,
            evidence=evidence,
        )
    if budget_rejected:
        return GovernorDecision(
            outcome=GovernorOutcome.REJECT_BUDGET,
            reason=(
                "qualified_subscription_executors_exceed_"
                "weekly_reserve_or_single_action_cap"
            ),
            selected_executor_id=None,
            budget=budget,
            burn_projection=burn,
            projected_used_after_action=None,
            evidence=evidence,
        )
    if quality_rejected:
        return GovernorDecision(
            outcome=GovernorOutcome.NO_QUALIFIED_EXECUTOR,
            reason="calibrated_executors_below_quality_floor",
            selected_executor_id=None,
            budget=budget,
            burn_projection=burn,
            projected_used_after_action=None,
            evidence=evidence,
        )
    return GovernorDecision(
        outcome=GovernorOutcome.DEFER_CALIBRATION,
        reason="insufficient_comparable_validator_backed_cost_samples",
        selected_executor_id=None,
        budget=budget,
        burn_projection=burn,
        projected_used_after_action=None,
        evidence=evidence,
    )


def evaluate_holdout_promotion(
    *,
    baseline_policy_id: str,
    candidate_policy_id: str,
    results: Iterable[HoldoutTaskResult],
    minimum_tasks: int = 5,
    minimum_candidate_score: float = 0.80,
    maximum_score_regression: float = 0.0,
) -> PolicyPromotionDecision:
    if (
        not baseline_policy_id
        or not candidate_policy_id
        or baseline_policy_id == candidate_policy_id
    ):
        raise GovernorInvariantError("holdout_policy_ids_invalid")
    if minimum_tasks < 1:
        raise GovernorInvariantError("holdout_minimum_tasks_invalid")
    if not 0.0 <= minimum_candidate_score <= 1.0:
        raise GovernorInvariantError(
            "holdout_minimum_candidate_score_invalid"
        )
    if maximum_score_regression < 0:
        raise GovernorInvariantError(
            "holdout_maximum_score_regression_invalid"
        )

    rows = tuple(results)
    grouped: dict[str, dict[str, HoldoutTaskResult]] = {
        baseline_policy_id: {},
        candidate_policy_id: {},
    }
    for row in rows:
        if not row.work_item_id:
            raise GovernorInvariantError(
                "holdout_work_item_id_required"
            )
        if not 0.0 <= row.validator_score <= 1.0:
            raise GovernorInvariantError(
                "holdout_validator_score_invalid"
            )
        if row.weekly_allowance_points < 0:
            raise GovernorInvariantError(
                "holdout_allowance_points_invalid"
            )
        if row.policy_id not in grouped:
            continue
        bucket = grouped[row.policy_id]
        if row.work_item_id in bucket:
            raise GovernorInvariantError(
                "holdout_duplicate_policy_work_item"
            )
        bucket[row.work_item_id] = row

    baseline = grouped[baseline_policy_id]
    candidate = grouped[candidate_policy_id]
    task_ids = set(baseline)
    if task_ids != set(candidate) or len(task_ids) < minimum_tasks:
        return PolicyPromotionDecision(
            promote=False,
            reason="holdout_task_sets_incomplete_or_unmatched",
            baseline_policy_id=baseline_policy_id,
            candidate_policy_id=candidate_policy_id,
            task_count=len(task_ids & set(candidate)),
            baseline_mean_score=None,
            candidate_mean_score=None,
            baseline_allowance_points=None,
            candidate_allowance_points=None,
        )

    baseline_rows = tuple(
        baseline[item]
        for item in sorted(task_ids)
    )
    candidate_rows = tuple(
        candidate[item]
        for item in sorted(task_ids)
    )
    baseline_score = mean(
        row.validator_score if row.validator_passed else 0.0
        for row in baseline_rows
    )
    candidate_score = mean(
        row.validator_score if row.validator_passed else 0.0
        for row in candidate_rows
    )
    baseline_cost = sum(
        row.weekly_allowance_points
        for row in baseline_rows
    )
    candidate_cost = sum(
        row.weekly_allowance_points
        for row in candidate_rows
    )

    if any(not row.validator_passed for row in candidate_rows):
        reason = "candidate_has_failed_holdout_task"
        promote = False
    elif candidate_score < minimum_candidate_score:
        reason = "candidate_below_absolute_quality_floor"
        promote = False
    elif (
        candidate_score
        < baseline_score - maximum_score_regression
    ):
        reason = "candidate_quality_regresses_baseline"
        promote = False
    elif candidate_cost >= baseline_cost:
        reason = "candidate_does_not_reduce_scarce_allowance"
        promote = False
    else:
        reason = "candidate_improves_allowance_without_quality_regression"
        promote = True

    return PolicyPromotionDecision(
        promote=promote,
        reason=reason,
        baseline_policy_id=baseline_policy_id,
        candidate_policy_id=candidate_policy_id,
        task_count=len(task_ids),
        baseline_mean_score=baseline_score,
        candidate_mean_score=candidate_score,
        baseline_allowance_points=baseline_cost,
        candidate_allowance_points=candidate_cost,
    )
