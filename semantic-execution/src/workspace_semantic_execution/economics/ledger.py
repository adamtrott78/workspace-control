"""Pure reasoning-economy accounting over observed usage snapshots."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable

from ..ports import (
    RateLimitWindowClass,
    RateLimitWindowSnapshot,
    UsageSnapshot,
)


class EconomicsInvariantError(RuntimeError):
    """Fail-closed economics accounting invariant."""


class WasteClass(StrEnum):
    PRODUCTIVE_REASONING = "PRODUCTIVE_REASONING"
    DECOMPOSITION = "DECOMPOSITION"
    VALIDATION = "VALIDATION"
    REPAIR = "REPAIR"
    CONTEXT_RECONSTRUCTION = "CONTEXT_RECONSTRUCTION"
    DUPLICATION = "DUPLICATION"
    OVER_ROUTING = "OVER_ROUTING"
    FAILED_BRANCH = "FAILED_BRANCH"
    WAITING_EXTERNAL = "WAITING_EXTERNAL"
    POLLING = "POLLING"
    IDLE = "IDLE"
    DETERMINISTIC = "DETERMINISTIC"


ZERO_MODEL_TOKEN_CLASSES = {
    WasteClass.WAITING_EXTERNAL,
    WasteClass.POLLING,
    WasteClass.IDLE,
    WasteClass.DETERMINISTIC,
}


@dataclass(frozen=True)
class ExecutionTokenUsage:
    input_tokens: int | None = None
    cached_input_tokens: int | None = None
    output_tokens: int | None = None
    reasoning_output_tokens: int | None = None
    total_tokens: int | None = None

    def known_total(self) -> int | None:
        if self.total_tokens is not None:
            return self.total_tokens
        parts = (
            self.input_tokens,
            self.output_tokens,
        )
        if any(value is None for value in parts):
            return None
        return int(self.input_tokens or 0) + int(self.output_tokens or 0)

    def any_positive(self) -> bool:
        return any(
            value is not None and value > 0
            for value in (
                self.input_tokens,
                self.cached_input_tokens,
                self.output_tokens,
                self.reasoning_output_tokens,
                self.total_tokens,
            )
        )


@dataclass(frozen=True)
class AllowanceWindowDelta:
    limit_id: str | None
    window_class: RateLimitWindowClass
    window_duration_mins: int | None
    before_used_percent: int | None
    after_used_percent: int | None
    before_resets_at: int | None
    after_resets_at: int | None
    delta_used_percent: int | None
    comparison_state: str


@dataclass(frozen=True)
class UsageDelta:
    account_lifetime_token_delta: int | None
    allowance_windows: tuple[AllowanceWindowDelta, ...]

    def known_allowance_delta_points(
        self,
        *,
        window_class: RateLimitWindowClass,
        limit_id: str | None = None,
    ) -> int | None:
        matches = [
            item
            for item in self.allowance_windows
            if item.window_class == window_class
            and (limit_id is None or item.limit_id == limit_id)
        ]
        if len(matches) != 1:
            return None
        item = matches[0]
        if (
            item.comparison_state != "COMPARABLE"
            or item.delta_used_percent is None
        ):
            return None
        return item.delta_used_percent

    def known_weekly_delta_points(
        self,
        *,
        limit_id: str | None = None,
    ) -> int | None:
        return self.known_allowance_delta_points(
            window_class=RateLimitWindowClass.WEEKLY,
            limit_id=limit_id,
        )


@dataclass(frozen=True)
class ExecutionEconomics:
    execution_id: str
    work_item_id: str
    parent_execution_id: str | None
    executor_id: str
    model_id: str
    surface_id: str
    started_at: str
    ended_at: str
    token_usage: ExecutionTokenUsage
    model_invocations: int
    tool_calls: int
    retries: int
    decomposition_depth: int
    children_spawned: int
    validator_passed: bool | None
    validator_score: float | None
    waste_class: WasteClass
    usage_before: UsageSnapshot
    usage_after: UsageSnapshot
    usage_delta: UsageDelta

    def verified_progress_per_weekly_allowance_point(
        self,
        *,
        limit_id: str | None = None,
    ) -> float | None:
        if self.validator_passed is not True:
            return 0.0 if self.validator_passed is False else None
        progress = (
            self.validator_score
            if self.validator_score is not None
            else 1.0
        )
        delta = self.usage_delta.known_weekly_delta_points(
            limit_id=limit_id,
        )
        # A zero observed percent-point delta is below meter resolution or
        # genuinely unmetered; neither justifies claiming infinite efficiency.
        if delta is None or delta <= 0:
            return None
        return progress / delta


def _window_identity(
    limit_id: str | None,
    window: RateLimitWindowSnapshot,
) -> tuple[str | None, RateLimitWindowClass, int | None]:
    return (
        limit_id,
        window.window_class,
        window.window_duration_mins,
    )


def _index_windows(
    snapshot: UsageSnapshot,
) -> dict[
    tuple[str | None, RateLimitWindowClass, int | None],
    list[RateLimitWindowSnapshot],
]:
    indexed: dict[
        tuple[str | None, RateLimitWindowClass, int | None],
        list[RateLimitWindowSnapshot],
    ] = {}
    for bucket in snapshot.rate_limit_buckets:
        for window in bucket.windows:
            key = _window_identity(bucket.limit_id, window)
            indexed.setdefault(key, []).append(window)
    return indexed


def _compare_window(
    key: tuple[str | None, RateLimitWindowClass, int | None],
    before: list[RateLimitWindowSnapshot] | None,
    after: list[RateLimitWindowSnapshot] | None,
) -> AllowanceWindowDelta:
    limit_id, window_class, duration = key
    if before is None or after is None:
        return AllowanceWindowDelta(
            limit_id=limit_id,
            window_class=window_class,
            window_duration_mins=duration,
            before_used_percent=(
                before[0].used_percent
                if before is not None and len(before) == 1
                else None
            ),
            after_used_percent=(
                after[0].used_percent
                if after is not None and len(after) == 1
                else None
            ),
            before_resets_at=(
                before[0].resets_at
                if before is not None and len(before) == 1
                else None
            ),
            after_resets_at=(
                after[0].resets_at
                if after is not None and len(after) == 1
                else None
            ),
            delta_used_percent=None,
            comparison_state="MISSING_SIDE",
        )
    if len(before) != 1 or len(after) != 1:
        return AllowanceWindowDelta(
            limit_id=limit_id,
            window_class=window_class,
            window_duration_mins=duration,
            before_used_percent=None,
            after_used_percent=None,
            before_resets_at=None,
            after_resets_at=None,
            delta_used_percent=None,
            comparison_state="AMBIGUOUS",
        )

    left = before[0]
    right = after[0]
    if (
        left.resets_at is not None
        and right.resets_at is not None
        and left.resets_at != right.resets_at
    ):
        return AllowanceWindowDelta(
            limit_id=limit_id,
            window_class=window_class,
            window_duration_mins=duration,
            before_used_percent=left.used_percent,
            after_used_percent=right.used_percent,
            before_resets_at=left.resets_at,
            after_resets_at=right.resets_at,
            delta_used_percent=None,
            comparison_state="RESET_BOUNDARY",
        )
    if right.used_percent < left.used_percent:
        return AllowanceWindowDelta(
            limit_id=limit_id,
            window_class=window_class,
            window_duration_mins=duration,
            before_used_percent=left.used_percent,
            after_used_percent=right.used_percent,
            before_resets_at=left.resets_at,
            after_resets_at=right.resets_at,
            delta_used_percent=None,
            comparison_state="NON_MONOTONIC",
        )

    return AllowanceWindowDelta(
        limit_id=limit_id,
        window_class=window_class,
        window_duration_mins=duration,
        before_used_percent=left.used_percent,
        after_used_percent=right.used_percent,
        before_resets_at=left.resets_at,
        after_resets_at=right.resets_at,
        delta_used_percent=right.used_percent - left.used_percent,
        comparison_state="COMPARABLE",
    )


def compute_usage_delta(
    before: UsageSnapshot,
    after: UsageSnapshot,
) -> UsageDelta:
    before_lifetime = before.token_summary.lifetime_tokens
    after_lifetime = after.token_summary.lifetime_tokens
    token_delta: int | None = None
    if before_lifetime is not None and after_lifetime is not None:
        if after_lifetime >= before_lifetime:
            token_delta = after_lifetime - before_lifetime

    before_windows = _index_windows(before)
    after_windows = _index_windows(after)
    keys = sorted(
        set(before_windows) | set(after_windows),
        key=lambda key: (
            "" if key[0] is None else key[0],
            key[1].value,
            -1 if key[2] is None else key[2],
        ),
    )
    deltas = tuple(
        _compare_window(
            key,
            before_windows.get(key),
            after_windows.get(key),
        )
        for key in keys
    )
    return UsageDelta(
        account_lifetime_token_delta=token_delta,
        allowance_windows=deltas,
    )


def _require_nonnegative(values: Iterable[tuple[str, int]]) -> None:
    for name, value in values:
        if value < 0:
            raise EconomicsInvariantError(f"{name}:must_be_nonnegative")


def build_execution_economics(
    *,
    execution_id: str,
    work_item_id: str,
    parent_execution_id: str | None,
    executor_id: str,
    model_id: str,
    surface_id: str,
    started_at: str,
    ended_at: str,
    token_usage: ExecutionTokenUsage,
    model_invocations: int,
    tool_calls: int,
    retries: int,
    decomposition_depth: int,
    children_spawned: int,
    validator_passed: bool | None,
    validator_score: float | None,
    waste_class: WasteClass,
    usage_before: UsageSnapshot,
    usage_after: UsageSnapshot,
) -> ExecutionEconomics:
    required = (
        execution_id,
        work_item_id,
        executor_id,
        model_id,
        surface_id,
        started_at,
        ended_at,
    )
    if not all(required):
        raise EconomicsInvariantError("execution_identity_fields_required")
    _require_nonnegative(
        (
            ("model_invocations", model_invocations),
            ("tool_calls", tool_calls),
            ("retries", retries),
            ("decomposition_depth", decomposition_depth),
            ("children_spawned", children_spawned),
        )
    )
    for name, value in (
        ("input_tokens", token_usage.input_tokens),
        ("cached_input_tokens", token_usage.cached_input_tokens),
        ("output_tokens", token_usage.output_tokens),
        ("reasoning_output_tokens", token_usage.reasoning_output_tokens),
        ("total_tokens", token_usage.total_tokens),
    ):
        if value is not None and value < 0:
            raise EconomicsInvariantError(f"{name}:must_be_nonnegative")

    if waste_class in ZERO_MODEL_TOKEN_CLASSES:
        if model_invocations != 0 or token_usage.any_positive():
            raise EconomicsInvariantError(
                f"{waste_class.value}:must_consume_zero_model_tokens"
            )

    if validator_score is not None and not 0.0 <= validator_score <= 1.0:
        raise EconomicsInvariantError(
            "validator_score:must_be_between_zero_and_one"
        )

    return ExecutionEconomics(
        execution_id=execution_id,
        work_item_id=work_item_id,
        parent_execution_id=parent_execution_id,
        executor_id=executor_id,
        model_id=model_id,
        surface_id=surface_id,
        started_at=started_at,
        ended_at=ended_at,
        token_usage=token_usage,
        model_invocations=model_invocations,
        tool_calls=tool_calls,
        retries=retries,
        decomposition_depth=decomposition_depth,
        children_spawned=children_spawned,
        validator_passed=validator_passed,
        validator_score=validator_score,
        waste_class=waste_class,
        usage_before=usage_before,
        usage_after=usage_after,
        usage_delta=compute_usage_delta(usage_before, usage_after),
    )
