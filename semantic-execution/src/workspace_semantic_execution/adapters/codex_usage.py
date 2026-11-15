"""Read-only Codex app-server account telemetry adapter.

The adapter delegates authentication to the installed Codex process and never
reads auth files, browser cookies, OAuth tokens, or API keys. OPENAI_API_KEY is
removed from the child environment to prevent accidental API-key routing.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
import queue
import shutil
import subprocess
import threading
from typing import Any, Mapping, Protocol, Sequence

from ..ports.usage import (
    AccountTokenUsageSummary,
    DailyTokenUsageBucket,
    RateLimitBucketSnapshot,
    RateLimitWindowClass,
    RateLimitWindowSnapshot,
    UsageSnapshot,
)


class CodexUsageError(RuntimeError):
    """Fail-closed Codex usage telemetry error."""


class JsonRpcSession(Protocol):
    def request(
        self,
        method: str,
        params: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]: ...

    def close(self) -> None: ...


def classify_window(
    window_duration_mins: int | None,
) -> RateLimitWindowClass:
    if window_duration_mins is None:
        return RateLimitWindowClass.UNKNOWN
    if window_duration_mins == 300:
        return RateLimitWindowClass.FIVE_HOUR
    if window_duration_mins == 7 * 24 * 60:
        return RateLimitWindowClass.WEEKLY
    return RateLimitWindowClass.OTHER


def _optional_int(value: Any, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise CodexUsageError(f"{field}:expected_integer_or_null")
    return value


def _optional_str(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise CodexUsageError(f"{field}:expected_string_or_null")
    return value


def _parse_window(
    source_role: str,
    raw: Any,
) -> RateLimitWindowSnapshot | None:
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        raise CodexUsageError(f"{source_role}:expected_object_or_null")
    used_percent = raw.get("usedPercent")
    if isinstance(used_percent, bool) or not isinstance(used_percent, int):
        raise CodexUsageError(f"{source_role}.usedPercent:expected_integer")
    duration = _optional_int(
        raw.get("windowDurationMins"),
        f"{source_role}.windowDurationMins",
    )
    resets_at = _optional_int(
        raw.get("resetsAt"),
        f"{source_role}.resetsAt",
    )
    return RateLimitWindowSnapshot(
        source_role=source_role,
        used_percent=used_percent,
        window_duration_mins=duration,
        resets_at=resets_at,
        window_class=classify_window(duration),
    )


def _parse_rate_limit_bucket(
    raw: Any,
    *,
    fallback_limit_id: str | None = None,
) -> RateLimitBucketSnapshot:
    if not isinstance(raw, Mapping):
        raise CodexUsageError("rate_limit_bucket:expected_object")
    windows: list[RateLimitWindowSnapshot] = []
    for role in ("primary", "secondary"):
        parsed = _parse_window(role, raw.get(role))
        if parsed is not None:
            windows.append(parsed)
    limit_id = _optional_str(raw.get("limitId"), "limitId")
    if limit_id is None:
        limit_id = fallback_limit_id
    return RateLimitBucketSnapshot(
        limit_id=limit_id,
        limit_name=_optional_str(raw.get("limitName"), "limitName"),
        normal_model_slug=_optional_str(
            raw.get("normalModelSlug"),
            "normalModelSlug",
        ),
        plan_type=_optional_str(raw.get("planType"), "planType"),
        windows=tuple(windows),
    )


def parse_rate_limits_response(
    response: Mapping[str, Any],
) -> tuple[bool | None, tuple[RateLimitBucketSnapshot, ...]]:
    result = response.get("result")
    if not isinstance(result, Mapping):
        raise CodexUsageError("rate_limits:missing_result")

    ordinary = result.get("ordinaryUsageAllowed")
    if ordinary is not None and not isinstance(ordinary, bool):
        raise CodexUsageError(
            "ordinaryUsageAllowed:expected_boolean_or_null"
        )

    buckets: list[RateLimitBucketSnapshot] = []
    canonical = result.get("rateLimits")
    if canonical is not None:
        buckets.append(_parse_rate_limit_bucket(canonical))

    by_id = result.get("rateLimitsByLimitId")
    if by_id is not None:
        if not isinstance(by_id, Mapping):
            raise CodexUsageError(
                "rateLimitsByLimitId:expected_object_or_null"
            )
        for limit_id in sorted(by_id):
            raw = by_id[limit_id]
            if not isinstance(limit_id, str):
                raise CodexUsageError(
                    "rateLimitsByLimitId:key_must_be_string"
                )
            parsed = _parse_rate_limit_bucket(
                raw,
                fallback_limit_id=limit_id,
            )
            if parsed not in buckets:
                buckets.append(parsed)

    return ordinary, tuple(buckets)


def parse_usage_response(
    response: Mapping[str, Any],
) -> tuple[
    AccountTokenUsageSummary,
    tuple[DailyTokenUsageBucket, ...] | None,
    Mapping[str, Any] | None,
]:
    result = response.get("result")
    if not isinstance(result, Mapping):
        raise CodexUsageError("usage:missing_result")
    summary = result.get("summary")
    if not isinstance(summary, Mapping):
        raise CodexUsageError("usage.summary:expected_object")

    parsed_summary = AccountTokenUsageSummary(
        lifetime_tokens=_optional_int(
            summary.get("lifetimeTokens"),
            "summary.lifetimeTokens",
        ),
        peak_daily_tokens=_optional_int(
            summary.get("peakDailyTokens"),
            "summary.peakDailyTokens",
        ),
        longest_running_turn_sec=_optional_int(
            summary.get("longestRunningTurnSec"),
            "summary.longestRunningTurnSec",
        ),
        current_streak_days=_optional_int(
            summary.get("currentStreakDays"),
            "summary.currentStreakDays",
        ),
        longest_streak_days=_optional_int(
            summary.get("longestStreakDays"),
            "summary.longestStreakDays",
        ),
    )

    raw_daily = result.get("dailyUsageBuckets")
    daily: tuple[DailyTokenUsageBucket, ...] | None
    if raw_daily is None:
        daily = None
    else:
        if not isinstance(raw_daily, list):
            raise CodexUsageError(
                "dailyUsageBuckets:expected_array_or_null"
            )
        parsed_daily: list[DailyTokenUsageBucket] = []
        for index, raw in enumerate(raw_daily):
            if not isinstance(raw, Mapping):
                raise CodexUsageError(
                    f"dailyUsageBuckets[{index}]:expected_object"
                )
            start_date = raw.get("startDate")
            tokens = raw.get("tokens")
            if not isinstance(start_date, str):
                raise CodexUsageError(
                    f"dailyUsageBuckets[{index}].startDate:"
                    "expected_string"
                )
            if isinstance(tokens, bool) or not isinstance(tokens, int):
                raise CodexUsageError(
                    f"dailyUsageBuckets[{index}].tokens:"
                    "expected_integer"
                )
            parsed_daily.append(
                DailyTokenUsageBucket(
                    start_date=start_date,
                    tokens=tokens,
                )
            )
        daily = tuple(parsed_daily)

    raw_thread = result.get("threadUsage")
    if raw_thread is not None and not isinstance(raw_thread, Mapping):
        raise CodexUsageError("threadUsage:expected_object_or_null")
    thread_usage = (
        dict(raw_thread)
        if isinstance(raw_thread, Mapping)
        else None
    )
    return parsed_summary, daily, thread_usage


@dataclass
class CodexUsageCollector:
    session_factory: callable
    clock: callable = lambda: datetime.now(timezone.utc)

    def read_snapshot(
        self,
        *,
        thread_id: str | None = None,
    ) -> UsageSnapshot:
        session = self.session_factory()
        try:
            rate_response = session.request(
                "account/rateLimits/read",
                params=None,
            )
            usage_params = (
                {"threadId": thread_id}
                if thread_id is not None
                else None
            )
            usage_response = session.request(
                "account/usage/read",
                params=usage_params,
            )
        finally:
            session.close()

        ordinary, buckets = parse_rate_limits_response(rate_response)
        summary, daily, thread_usage = parse_usage_response(
            usage_response
        )
        captured = self.clock()
        if not isinstance(captured, datetime):
            raise CodexUsageError("clock_must_return_datetime")
        if captured.tzinfo is None:
            raise CodexUsageError("clock_must_be_timezone_aware")
        return UsageSnapshot(
            captured_at=captured.isoformat(),
            ordinary_usage_allowed=ordinary,
            rate_limit_buckets=buckets,
            token_summary=summary,
            daily_usage_buckets=daily,
            thread_usage=thread_usage,
        )


class CodexAppServerStdioSession:
    """Minimal newline-delimited JSON-RPC client for one Codex app-server."""

    def __init__(
        self,
        command: Sequence[str] | None = None,
        *,
        timeout_sec: float = 5.0,
        environment: Mapping[str, str] | None = None,
    ) -> None:
        self._timeout_sec = timeout_sec
        self._next_id = 1
        self._closed = False
        self._line_queue: queue.Queue[str | BaseException | None] = (
            queue.Queue()
        )

        resolved = tuple(command or self.resolve_default_command())
        if not resolved:
            raise CodexUsageError("codex_command_required")

        child_env = dict(environment or os.environ)
        # A ChatGPT-plan collector must never accidentally inherit API billing.
        child_env.pop("OPENAI_API_KEY", None)

        self._process = subprocess.Popen(
            resolved,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
            env=child_env,
            shell=False,
        )
        if self._process.stdin is None or self._process.stdout is None:
            self.close()
            raise CodexUsageError("codex_stdio_unavailable")

        self._reader = threading.Thread(
            target=self._read_stdout,
            daemon=True,
        )
        self._reader.start()

        initialize_id = self._send_request(
            "initialize",
            {
                "clientInfo": {
                    "name": "workspace-reasoning-economy",
                    "version": "0.1.0",
                }
            },
        )
        self._await_response(initialize_id)
        self._send_notification("initialized", {})

    @staticmethod
    def resolve_default_command() -> tuple[str, ...]:
        candidates = (
            "codex",
            "codex.exe",
        )
        for name in candidates:
            path = shutil.which(name)
            if path and not path.lower().endswith((".cmd", ".bat")):
                return (
                    path,
                    "app-server",
                    "--listen",
                    "stdio://",
                )
        raise CodexUsageError(
            "native_codex_executable_not_found:"
            "install Codex CLI/app or provide an explicit command"
        )

    def _read_stdout(self) -> None:
        assert self._process.stdout is not None
        try:
            for line in self._process.stdout:
                self._line_queue.put(line)
        except BaseException as exc:
            self._line_queue.put(exc)
        finally:
            self._line_queue.put(None)

    def _write(self, payload: Mapping[str, Any]) -> None:
        if self._closed or self._process.stdin is None:
            raise CodexUsageError("codex_session_closed")
        encoded = json.dumps(
            payload,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        self._process.stdin.write(encoded + "\n")
        self._process.stdin.flush()

    def _send_request(
        self,
        method: str,
        params: Mapping[str, Any] | None,
    ) -> int:
        request_id = self._next_id
        self._next_id += 1
        payload: dict[str, Any] = {
            "method": method,
            "id": request_id,
        }
        if params is not None:
            payload["params"] = dict(params)
        self._write(payload)
        return request_id

    def _send_notification(
        self,
        method: str,
        params: Mapping[str, Any],
    ) -> None:
        self._write({"method": method, "params": dict(params)})

    def _await_response(self, request_id: int) -> Mapping[str, Any]:
        while True:
            try:
                item = self._line_queue.get(timeout=self._timeout_sec)
            except queue.Empty as exc:
                raise CodexUsageError(
                    f"codex_rpc_timeout:id={request_id}"
                ) from exc
            if item is None:
                raise CodexUsageError(
                    f"codex_app_server_closed:id={request_id}"
                )
            if isinstance(item, BaseException):
                raise CodexUsageError(
                    "codex_app_server_reader_failed"
                ) from item
            try:
                payload = json.loads(item)
            except json.JSONDecodeError:
                # Ignore non-JSON stdout chatter; never log it because it may
                # contain environment-specific account information.
                continue
            if not isinstance(payload, Mapping):
                continue
            if payload.get("id") != request_id:
                # Rolling notifications and other responses are ignored by this
                # one-request-at-a-time read-only client.
                continue
            if payload.get("error") is not None:
                error = payload.get("error")
                code = (
                    error.get("code")
                    if isinstance(error, Mapping)
                    else "unknown"
                )
                raise CodexUsageError(
                    f"codex_rpc_error:id={request_id}:code={code}"
                )
            return dict(payload)

    def request(
        self,
        method: str,
        params: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        if method not in {
            "account/rateLimits/read",
            "account/usage/read",
        }:
            raise CodexUsageError(
                f"method_not_authorized:{method}"
            )
        request_id = self._send_request(method, params)
        return self._await_response(request_id)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        process = getattr(self, "_process", None)
        if process is None:
            return
        if process.stdin is not None:
            try:
                process.stdin.close()
            except OSError:
                pass
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=1.0)


def default_codex_usage_collector() -> CodexUsageCollector:
    return CodexUsageCollector(
        session_factory=CodexAppServerStdioSession,
    )
