"""Read-only account-usage telemetry contracts for reasoning economy."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping, Protocol


class RateLimitWindowClass(StrEnum):
    FIVE_HOUR = "FIVE_HOUR"
    WEEKLY = "WEEKLY"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class RateLimitWindowSnapshot:
    source_role: str
    used_percent: int
    window_duration_mins: int | None
    resets_at: int | None
    window_class: RateLimitWindowClass


@dataclass(frozen=True)
class RateLimitBucketSnapshot:
    limit_id: str | None
    limit_name: str | None
    normal_model_slug: str | None
    plan_type: str | None
    windows: tuple[RateLimitWindowSnapshot, ...] = ()


@dataclass(frozen=True)
class AccountTokenUsageSummary:
    lifetime_tokens: int | None
    peak_daily_tokens: int | None
    longest_running_turn_sec: int | None
    current_streak_days: int | None
    longest_streak_days: int | None


@dataclass(frozen=True)
class DailyTokenUsageBucket:
    start_date: str
    tokens: int


@dataclass(frozen=True)
class UsageSnapshot:
    captured_at: str
    ordinary_usage_allowed: bool | None
    rate_limit_buckets: tuple[RateLimitBucketSnapshot, ...]
    token_summary: AccountTokenUsageSummary
    daily_usage_buckets: tuple[DailyTokenUsageBucket, ...] | None
    thread_usage: Mapping[str, Any] | None = field(default=None)

    def windows_by_class(
        self,
        window_class: RateLimitWindowClass,
    ) -> tuple[RateLimitWindowSnapshot, ...]:
        return tuple(
            window
            for bucket in self.rate_limit_buckets
            for window in bucket.windows
            if window.window_class == window_class
        )


class UsageTelemetryPort(Protocol):
    """Read-only subscription/account usage telemetry."""

    def read_snapshot(
        self,
        *,
        thread_id: str | None = None,
    ) -> UsageSnapshot: ...
