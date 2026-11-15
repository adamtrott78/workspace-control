"""Subscription-only Codex execution for Reasoning Economy.

This adapter refuses API-key and non-ChatGPT authentication. Initial execution
is intentionally ephemeral and read-only; prompt text is delivered on stdin so
it never appears in the process argument list.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import shutil
import subprocess
from typing import Any, Callable, Mapping, Protocol, Sequence

from .codex_usage import (
    CodexAppServerStdioSession,
    CodexUsageError,
    JsonRpcSession,
    sanitized_codex_environment,
)
from ..economics.codex_trace import (
    CodexExecTraceSummary,
    CodexTraceError,
    parse_codex_exec_jsonl,
)
from ..ports import UsageSnapshot, UsageTelemetryPort


class CodexSubscriptionError(RuntimeError):
    """Fail-closed subscription executor error."""


@dataclass(frozen=True)
class CodexSubscriptionAuthInfo:
    account_type: str
    plan_type: str
    requires_openai_auth: bool


@dataclass(frozen=True)
class CodexProcessResult:
    returncode: int
    stdout: str
    stderr: str


class CodexProcessRunner(Protocol):
    def run(
        self,
        *,
        command: Sequence[str],
        prompt: str,
        cwd: Path,
        environment: Mapping[str, str],
        timeout_sec: float,
    ) -> CodexProcessResult: ...


@dataclass(frozen=True)
class CodexSubscriptionRunObservation:
    model_id: str
    started_at: str
    ended_at: str
    usage_before: UsageSnapshot
    usage_after: UsageSnapshot
    trace: CodexExecTraceSummary
    returncode: int
    final_agent_message: str | None


def parse_account_read_response(
    response: Mapping[str, Any],
) -> CodexSubscriptionAuthInfo:
    result = response.get("result")
    if not isinstance(result, Mapping):
        raise CodexSubscriptionError("account_read:missing_result")

    requires = result.get("requiresOpenAIAuth")
    if not isinstance(requires, bool):
        raise CodexSubscriptionError(
            "account_read.requiresOpenAIAuth:expected_boolean"
        )

    account = result.get("account")
    if not isinstance(account, Mapping):
        raise CodexSubscriptionError("account_read:account_required")

    account_type = account.get("type")
    if not isinstance(account_type, str):
        raise CodexSubscriptionError("account_read:account_type_required")

    if account_type != "chatgpt":
        # Deliberately do not expose provider-specific identity or credentials.
        return CodexSubscriptionAuthInfo(
            account_type=account_type,
            plan_type="",
            requires_openai_auth=requires,
        )

    plan_type = account.get("planType")
    if not isinstance(plan_type, str) or not plan_type:
        raise CodexSubscriptionError(
            "account_read.chatgpt.planType:expected_string"
        )
    return CodexSubscriptionAuthInfo(
        account_type="chatgpt",
        plan_type=plan_type.lower(),
        requires_openai_auth=requires,
    )


class CodexSubscriptionAuthGuard:
    """Read-only account inspector that authorizes ChatGPT subscription use."""

    def __init__(
        self,
        *,
        session_factory: Callable[[], JsonRpcSession] | None = None,
        allowed_plans: frozenset[str] = frozenset({"plus"}),
    ) -> None:
        self._session_factory = (
            session_factory
            if session_factory is not None
            else lambda: CodexAppServerStdioSession(
                allowed_methods=frozenset({"account/read"})
            )
        )
        self._allowed_plans = frozenset(
            plan.lower() for plan in allowed_plans
        )

    def inspect(self) -> CodexSubscriptionAuthInfo:
        session = self._session_factory()
        try:
            response = session.request("account/read", params={})
        finally:
            session.close()
        return parse_account_read_response(response)

    def require_authorized(self) -> CodexSubscriptionAuthInfo:
        info = self.inspect()
        if info.requires_openai_auth:
            raise CodexSubscriptionError("chatgpt_auth_required")
        if info.account_type != "chatgpt":
            raise CodexSubscriptionError(
                f"subscription_auth_required:found={info.account_type}"
            )
        if info.plan_type not in self._allowed_plans:
            raise CodexSubscriptionError(
                f"subscription_plan_not_authorized:{info.plan_type}"
            )
        return info


class NativeCodexProcessRunner:
    """Native subprocess implementation with no shell and stdin-only prompt."""

    def run(
        self,
        *,
        command: Sequence[str],
        prompt: str,
        cwd: Path,
        environment: Mapping[str, str],
        timeout_sec: float,
    ) -> CodexProcessResult:
        completed = subprocess.run(
            tuple(command),
            input=prompt,
            text=True,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(cwd),
            env=dict(environment),
            timeout=timeout_sec,
            check=False,
            shell=False,
        )
        return CodexProcessResult(
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )


def resolve_codex_executable() -> str:
    for name in ("codex", "codex.exe"):
        path = shutil.which(name)
        if path and not path.lower().endswith((".cmd", ".bat")):
            return path
    raise CodexSubscriptionError("native_codex_executable_not_found")


def build_read_only_exec_command(
    *,
    executable: str,
    model_id: str,
) -> tuple[str, ...]:
    if not executable or not model_id:
        raise CodexSubscriptionError("codex_exec_identity_required")
    return (
        executable,
        "exec",
        "--json",
        "--ephemeral",
        "--sandbox",
        "read-only",
        "-m",
        model_id,
        "-",
    )


def extract_last_agent_message(jsonl: str) -> str | None:
    """Return only the final completed agent message for transient validation."""
    import json

    final: str | None = None
    for line_number, line in enumerate(jsonl.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CodexTraceError(
                f"line_{line_number}:invalid_json"
            ) from exc
        if not isinstance(raw, Mapping):
            continue
        if raw.get("type") != "item.completed":
            continue
        item = raw.get("item")
        if not isinstance(item, Mapping):
            continue
        if item.get("type") != "agent_message":
            continue
        text = item.get("text")
        if isinstance(text, str):
            final = text
    return final


class CodexSubscriptionExecutor:
    """One bounded subscription-backed Codex execution."""

    def __init__(
        self,
        *,
        usage: UsageTelemetryPort,
        auth_guard: CodexSubscriptionAuthGuard,
        process_runner: CodexProcessRunner | None = None,
        executable: str | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        timeout_sec: float = 600.0,
        environment: Mapping[str, str] | None = None,
    ) -> None:
        self._usage = usage
        self._auth_guard = auth_guard
        self._process_runner = process_runner or NativeCodexProcessRunner()
        self._executable = executable
        self._clock = clock
        self._timeout_sec = timeout_sec
        self._environment = environment

    def run_read_only(
        self,
        *,
        prompt: str,
        model_id: str,
        cwd: Path,
    ) -> CodexSubscriptionRunObservation:
        if not prompt.strip():
            raise CodexSubscriptionError("prompt_required")
        if not cwd.is_dir():
            raise CodexSubscriptionError("cwd_must_exist")

        # Hard billing gate before any model call.
        self._auth_guard.require_authorized()

        usage_before = self._usage.read_snapshot()
        started = self._now()
        command = build_read_only_exec_command(
            executable=self._executable or resolve_codex_executable(),
            model_id=model_id,
        )
        environment = sanitized_codex_environment(self._environment)
        result = self._process_runner.run(
            command=command,
            prompt=prompt,
            cwd=cwd,
            environment=environment,
            timeout_sec=self._timeout_sec,
        )
        ended = self._now()

        # Snapshot even on failed turns: failed work still consumes allowance.
        usage_after = self._usage.read_snapshot()
        trace = parse_codex_exec_jsonl(result.stdout)
        final_message = extract_last_agent_message(result.stdout)

        if result.returncode != 0 or trace.turns_failed or trace.fatal_errors:
            raise CodexSubscriptionError(
                "codex_exec_failed:"
                f"returncode={result.returncode}:"
                f"turn_failures={trace.turns_failed}:"
                f"fatal_errors={trace.fatal_errors}"
            )
        if trace.turns_completed < 1:
            raise CodexSubscriptionError("codex_exec_missing_completed_turn")

        return CodexSubscriptionRunObservation(
            model_id=model_id,
            started_at=started,
            ended_at=ended,
            usage_before=usage_before,
            usage_after=usage_after,
            trace=trace,
            returncode=result.returncode,
            final_agent_message=final_message,
        )

    def _now(self) -> str:
        value = self._clock()
        if not isinstance(value, datetime) or value.tzinfo is None:
            raise CodexSubscriptionError(
                "clock_must_return_timezone_aware_datetime"
            )
        return value.isoformat()
