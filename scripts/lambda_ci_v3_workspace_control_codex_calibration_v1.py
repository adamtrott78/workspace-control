#!/usr/bin/env python3
"""Trusted single-action Codex allowance calibration helper.

This module is stdlib-only by design. It must be executed from the trusted
workflow checkout with Python isolated mode (-I). The requested PR SHA is data
only; candidate repository code is never imported or executed.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import argparse
import json
import os
from pathlib import Path
import queue
import subprocess
import tempfile
import threading
from typing import Any, Callable, Mapping, Sequence


class CalibrationError(RuntimeError):
    pass


FORBIDDEN_ITEM_TYPES = frozenset(
    {
        "command_execution",
        "mcp_tool_call",
        "collab_tool_call",
        "web_search",
        "file_change",
        "error",
        "todo_list",
    }
)
ALLOWED_ITEM_TYPES = frozenset({"reasoning", "agent_message"})
ALLOWED_EVENT_TYPES = frozenset(
    {
        "thread.started",
        "turn.started",
        "item.started",
        "item.updated",
        "item.completed",
        "turn.completed",
    }
)


@dataclass(frozen=True)
class ExecResult:
    returncode: int
    stdout: str


@dataclass(frozen=True)
class StrictTrace:
    input_tokens: int
    cached_input_tokens: int
    cache_write_input_tokens: int | None
    output_tokens: int
    reasoning_output_tokens: int | None
    total_tokens: int
    final_agent_message: str


def _nonnegative_int(raw: Mapping[str, Any], key: str) -> int:
    value = raw.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CalibrationError(f"usage.{key}:expected_nonnegative_integer")
    return value


def _optional_nonnegative_int(raw: Mapping[str, Any], key: str) -> int | None:
    value = raw.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CalibrationError(
            f"usage.{key}:expected_nonnegative_integer_or_null"
        )
    return value


def parse_strict_calibration_trace(text: str) -> StrictTrace:
    """Accept only one successful, tool-free Codex turn.

    Every item event stage is inspected. Forbidden or unknown item types are
    rejected even if an item never reaches item.completed.
    """
    seen_thread = False
    seen_turn_start = False
    seen_turn_complete = False
    thread_id: str | None = None
    item_states: dict[str, str] = {}
    item_types: dict[str, str] = {}
    final_messages: list[str] = []
    usage: Mapping[str, Any] | None = None

    nonempty = [line for line in text.splitlines() if line.strip()]
    if not nonempty:
        raise CalibrationError("trace_empty")

    for line_number, line in enumerate(nonempty, start=1):
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CalibrationError(
                f"line_{line_number}:invalid_json"
            ) from exc
        if not isinstance(raw, Mapping):
            raise CalibrationError(
                f"line_{line_number}:event_must_be_object"
            )
        event_type = raw.get("type")
        if not isinstance(event_type, str):
            raise CalibrationError(
                f"line_{line_number}:event_type_required"
            )
        if event_type not in ALLOWED_EVENT_TYPES:
            raise CalibrationError(
                f"line_{line_number}:event_type_not_allowed:{event_type}"
            )
        if seen_turn_complete:
            raise CalibrationError("event_after_turn_completed")

        if event_type == "thread.started":
            if seen_thread or seen_turn_start:
                raise CalibrationError("thread_started_out_of_order")
            candidate = raw.get("thread_id")
            if not isinstance(candidate, str) or not candidate:
                raise CalibrationError("thread_id_required")
            seen_thread = True
            thread_id = candidate
            continue

        if event_type == "turn.started":
            if not seen_thread or seen_turn_start:
                raise CalibrationError("turn_started_out_of_order")
            seen_turn_start = True
            continue

        if event_type in {"item.started", "item.updated", "item.completed"}:
            if not seen_turn_start:
                raise CalibrationError("item_before_turn_start")
            item = raw.get("item")
            if not isinstance(item, Mapping):
                raise CalibrationError(
                    f"line_{line_number}:item_object_required"
                )
            item_type = item.get("type")
            if not isinstance(item_type, str):
                raise CalibrationError(
                    f"line_{line_number}:item_type_required"
                )
            if item_type in FORBIDDEN_ITEM_TYPES:
                raise CalibrationError(
                    f"forbidden_item_activity:{event_type}:{item_type}"
                )
            if item_type not in ALLOWED_ITEM_TYPES:
                raise CalibrationError(
                    f"unknown_item_type:{event_type}:{item_type}"
                )
            item_id = item.get("id")
            if not isinstance(item_id, str) or not item_id:
                raise CalibrationError(
                    f"line_{line_number}:item_id_required"
                )
            prior_type = item_types.get(item_id)
            if prior_type is not None and prior_type != item_type:
                raise CalibrationError("item_type_changed")
            item_types[item_id] = item_type

            prior_state = item_states.get(item_id)
            if event_type == "item.started":
                if prior_state is not None:
                    raise CalibrationError("duplicate_item_started")
                item_states[item_id] = "started"
            elif event_type == "item.updated":
                if prior_state not in {"started", "updated"}:
                    raise CalibrationError("item_updated_without_start")
                item_states[item_id] = "updated"
            else:
                if prior_state not in {None, "started", "updated"}:
                    raise CalibrationError("duplicate_item_completed")
                item_states[item_id] = "completed"
                if item_type == "agent_message":
                    message = item.get("text")
                    if not isinstance(message, str):
                        raise CalibrationError("agent_message_text_required")
                    final_messages.append(message)
            continue

        if event_type == "turn.completed":
            if not seen_turn_start:
                raise CalibrationError("turn_completed_without_start")
            incomplete = sorted(
                item_id
                for item_id, state in item_states.items()
                if state != "completed"
            )
            if incomplete:
                raise CalibrationError("incomplete_item_events")
            candidate_usage = raw.get("usage")
            if not isinstance(candidate_usage, Mapping):
                raise CalibrationError("turn_usage_required")
            usage = candidate_usage
            seen_turn_complete = True
            continue

    if not seen_thread or thread_id is None:
        raise CalibrationError("thread_started_missing")
    if not seen_turn_start or not seen_turn_complete or usage is None:
        raise CalibrationError("single_completed_turn_required")
    if len(final_messages) != 1:
        raise CalibrationError("exactly_one_agent_message_required")

    input_tokens = _nonnegative_int(usage, "input_tokens")
    cached_input_tokens = _nonnegative_int(usage, "cached_input_tokens")
    output_tokens = _nonnegative_int(usage, "output_tokens")
    cache_write = _optional_nonnegative_int(
        usage, "cache_write_input_tokens"
    )
    reasoning = _optional_nonnegative_int(
        usage, "reasoning_output_tokens"
    )
    return StrictTrace(
        input_tokens=input_tokens,
        cached_input_tokens=cached_input_tokens,
        cache_write_input_tokens=cache_write,
        output_tokens=output_tokens,
        reasoning_output_tokens=reasoning,
        total_tokens=input_tokens + output_tokens,
        final_agent_message=final_messages[0],
    )


class AppServerSession:
    def __init__(
        self,
        *,
        command: Sequence[str],
        environment: Mapping[str, str],
        allowed_methods: frozenset[str],
        timeout_sec: float = 8.0,
    ) -> None:
        self._allowed_methods = allowed_methods
        self._timeout = timeout_sec
        self._proc = subprocess.Popen(
            list(command),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            bufsize=1,
            env=dict(environment),
            shell=False,
        )
        if self._proc.stdin is None or self._proc.stdout is None:
            raise CalibrationError("app_server_stdio_unavailable")
        self._queue: queue.Queue[object] = queue.Queue()
        self._next_id = 1

        def read_stdout() -> None:
            try:
                for row in self._proc.stdout:
                    self._queue.put(row)
            finally:
                self._queue.put(None)

        threading.Thread(target=read_stdout, daemon=True).start()
        self.request(
            "initialize",
            {
                "clientInfo": {
                    "name": "workspace-control-codex-calibration",
                    "version": "1.0",
                }
            },
            initialization=True,
        )
        self._write({"method": "initialized", "params": {}})

    def _write(self, payload: Mapping[str, Any]) -> None:
        assert self._proc.stdin is not None
        self._proc.stdin.write(
            json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
            + "\n"
        )
        self._proc.stdin.flush()

    def request(
        self,
        method: str,
        params: Mapping[str, Any] | None = None,
        *,
        initialization: bool = False,
    ) -> Mapping[str, Any]:
        if not initialization and method not in self._allowed_methods:
            raise CalibrationError(f"rpc_method_not_allowed:{method}")
        request_id = self._next_id
        self._next_id += 1
        payload: dict[str, Any] = {"method": method, "id": request_id}
        if params is not None:
            payload["params"] = dict(params)
        self._write(payload)
        while True:
            try:
                row = self._queue.get(timeout=self._timeout)
            except queue.Empty as exc:
                raise CalibrationError(
                    f"rpc_timeout:{method}"
                ) from exc
            if row is None:
                raise CalibrationError(f"rpc_closed:{method}")
            try:
                response = json.loads(str(row))
            except json.JSONDecodeError:
                continue
            if not isinstance(response, Mapping):
                continue
            if response.get("id") != request_id:
                continue
            if response.get("error") is not None:
                error = response.get("error")
                code = error.get("code") if isinstance(error, Mapping) else "unknown"
                raise CalibrationError(f"rpc_error:{method}:code={code}")
            return response

    def close(self) -> None:
        try:
            if self._proc.stdin is not None:
                self._proc.stdin.close()
        except OSError:
            pass
        if self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                self._proc.kill()
                self._proc.wait(timeout=1.0)


def _child_environment(environment: Mapping[str, str]) -> dict[str, str]:
    child = dict(environment)
    child.pop("OPENAI_API_KEY", None)
    child.pop("PYTHONPATH", None)
    child.pop("PYTHONHOME", None)
    return child


def read_authorized_account(
    *,
    codex_bin: str,
    environment: Mapping[str, str],
) -> dict[str, Any]:
    session = AppServerSession(
        command=(codex_bin, "app-server", "--listen", "stdio://"),
        environment=_child_environment(environment),
        allowed_methods=frozenset({"account/read"}),
    )
    try:
        response = session.request("account/read", {})
    finally:
        session.close()
    result = response.get("result")
    if not isinstance(result, Mapping):
        raise CalibrationError("account_read_result_required")
    account = result.get("account")
    if not isinstance(account, Mapping):
        raise CalibrationError("account_required")
    account_type = account.get("type")
    plan_type = account.get("planType")
    requires = result.get("requiresOpenaiAuth")
    if account_type != "chatgpt":
        raise CalibrationError("chatgpt_subscription_required")
    if not isinstance(plan_type, str) or plan_type.lower() != "plus":
        raise CalibrationError("chatgpt_plus_required")
    if not isinstance(requires, bool):
        raise CalibrationError("requiresOpenaiAuth_boolean_required")
    return {
        "account_type": "chatgpt",
        "plan_type": "plus",
        "requires_openai_auth": requires,
    }


def _optional_int(value: object, label: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise CalibrationError(f"{label}:integer_or_null_required")
    return value


def _optional_str(value: object, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise CalibrationError(f"{label}:string_or_null_required")
    return value


def _clean_window(raw: object) -> dict[str, Any] | None:
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        raise CalibrationError("rate_window_object_required")
    used = raw.get("usedPercent")
    if isinstance(used, bool) or not isinstance(used, int):
        raise CalibrationError("rate_window_used_percent_integer_required")
    return {
        "used_percent": used,
        "window_duration_mins": _optional_int(
            raw.get("windowDurationMins"),
            "windowDurationMins",
        ),
        "resets_at": _optional_int(raw.get("resetsAt"), "resetsAt"),
    }


def _clean_bucket(
    raw: object,
    fallback_id: str | None = None,
) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise CalibrationError("rate_bucket_object_required")
    return {
        "limit_id": _optional_str(raw.get("limitId"), "limitId") or fallback_id,
        "limit_name": _optional_str(raw.get("limitName"), "limitName"),
        "normal_model_slug": _optional_str(
            raw.get("normalModelSlug"), "normalModelSlug"
        ),
        "plan_type": _optional_str(raw.get("planType"), "rateLimit.planType"),
        "primary": _clean_window(raw.get("primary")),
        "secondary": _clean_window(raw.get("secondary")),
    }


def read_usage_snapshot(
    *,
    codex_bin: str,
    environment: Mapping[str, str],
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> dict[str, Any]:
    session = AppServerSession(
        command=(codex_bin, "app-server", "--listen", "stdio://"),
        environment=_child_environment(environment),
        allowed_methods=frozenset(
            {"account/rateLimits/read", "account/usage/read"}
        ),
    )
    try:
        rate_response = session.request("account/rateLimits/read")
        usage_response = session.request("account/usage/read")
    finally:
        session.close()

    rate_result = rate_response.get("result")
    if not isinstance(rate_result, Mapping):
        raise CalibrationError("rate_limits_result_required")
    ordinary = rate_result.get("ordinaryUsageAllowed")
    if ordinary is not None and not isinstance(ordinary, bool):
        raise CalibrationError("ordinary_usage_boolean_or_null_required")
    buckets: list[dict[str, Any]] = []
    direct = rate_result.get("rateLimits")
    if direct is not None:
        buckets.append(_clean_bucket(direct))
    by_id = rate_result.get("rateLimitsByLimitId")
    if by_id is not None:
        if not isinstance(by_id, Mapping):
            raise CalibrationError("rate_limits_by_id_object_or_null_required")
        for limit_id in sorted(by_id):
            if not isinstance(limit_id, str):
                raise CalibrationError("rate_limit_id_string_required")
            cleaned = _clean_bucket(by_id[limit_id], limit_id)
            if cleaned not in buckets:
                buckets.append(cleaned)

    usage_result = usage_response.get("result")
    if not isinstance(usage_result, Mapping):
        raise CalibrationError("usage_result_required")
    summary = usage_result.get("summary")
    if not isinstance(summary, Mapping):
        raise CalibrationError("usage_summary_object_required")
    daily = usage_result.get("dailyUsageBuckets")
    if daily is not None and not isinstance(daily, list):
        raise CalibrationError("daily_usage_array_or_null_required")

    captured = clock()
    if not isinstance(captured, datetime) or captured.tzinfo is None:
        raise CalibrationError("timezone_aware_clock_required")
    return {
        "captured_at": captured.isoformat(),
        "ordinary_usage_allowed": ordinary,
        "rate_limits": buckets,
        "token_summary": {
            "lifetime_tokens": _optional_int(
                summary.get("lifetimeTokens"), "lifetimeTokens"
            ),
            "peak_daily_tokens": _optional_int(
                summary.get("peakDailyTokens"), "peakDailyTokens"
            ),
            "longest_running_turn_sec": _optional_int(
                summary.get("longestRunningTurnSec"),
                "longestRunningTurnSec",
            ),
            "current_streak_days": _optional_int(
                summary.get("currentStreakDays"), "currentStreakDays"
            ),
            "longest_streak_days": _optional_int(
                summary.get("longestStreakDays"), "longestStreakDays"
            ),
        },
        "daily_usage_bucket_count": len(daily) if isinstance(daily, list) else None,
    }


def native_exec_runner(
    *,
    codex_bin: str,
    environment: Mapping[str, str],
    temp_root: Path,
) -> ExecResult:
    work = temp_root / "codex-calibration-empty"
    work.mkdir(mode=0o700, parents=True, exist_ok=False)
    subprocess.run(
        ["git", "init", "-q", str(work)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    schema = temp_root / "codex-calibration.schema.json"
    schema.write_text(
        json.dumps(
            {
                "type": "object",
                "additionalProperties": False,
                "required": ["result_kind", "summary", "evidence_refs"],
                "properties": {
                    "result_kind": {"type": "string", "enum": ["RESULT"]},
                    "summary": {
                        "type": "string",
                        "enum": ["CALIBRATION_OK"],
                    },
                    "evidence_refs": {
                        "type": "array",
                        "maxItems": 0,
                        "items": {"type": "string"},
                    },
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    command = [
        codex_bin,
        "exec",
        "--json",
        "--ephemeral",
        "--sandbox",
        "read-only",
        "--config",
        "model_reasoning_effort=low",
        "--output-schema",
        str(schema),
        "-",
    ]
    prompt = (
        "Perform exactly one bounded calibration response. "
        "Do not inspect files, run commands, browse, call tools, or modify state. "
        "Return only the requested machine-minimal JSON with summary CALIBRATION_OK."
    )
    completed = subprocess.run(
        command,
        input=prompt,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        cwd=work,
        env=_child_environment(environment),
        timeout=180,
        check=False,
    )
    return ExecResult(
        returncode=completed.returncode,
        stdout=completed.stdout,
    )


def execute_calibration(
    *,
    expected_sha: str,
    trusted_workflow_sha: str,
    trusted_helper_blob: str,
    pr_number: int,
    actor: str,
    runner_name: str | None,
    runner_user: str | None,
    project_home: str,
    codex_home: str,
    codex_version: str,
    auth_reader: Callable[[], Mapping[str, Any]],
    usage_reader: Callable[[], Mapping[str, Any]],
    exec_runner: Callable[[], ExecResult],
) -> dict[str, Any]:
    events: list[str] = []
    auth = dict(auth_reader())
    events.append("auth")
    before = dict(usage_reader())
    events.append("usage_before")
    result = exec_runner()
    events.append("codex_exec")
    after = dict(usage_reader())
    events.append("usage_after")
    if events != ["auth", "usage_before", "codex_exec", "usage_after"]:
        raise CalibrationError("calibration_order_violation")

    trace_error: str | None = None
    trace: StrictTrace | None = None
    try:
        trace = parse_strict_calibration_trace(result.stdout)
    except CalibrationError as exc:
        trace_error = str(exc)

    output_contract_passed = False
    if trace is not None:
        try:
            output = json.loads(trace.final_agent_message)
        except json.JSONDecodeError:
            output = None
        output_contract_passed = output == {
            "result_kind": "RESULT",
            "summary": "CALIBRATION_OK",
            "evidence_refs": [],
        }

    decision = (
        "PASS"
        if result.returncode == 0
        and trace is not None
        and output_contract_passed
        else "FAIL"
    )
    token_usage = None
    if trace is not None:
        token_usage = {
            "input_tokens": trace.input_tokens,
            "cached_input_tokens": trace.cached_input_tokens,
            "cache_write_input_tokens": trace.cache_write_input_tokens,
            "output_tokens": trace.output_tokens,
            "reasoning_output_tokens": trace.reasoning_output_tokens,
            "total_tokens": trace.total_tokens,
        }

    return {
        "schema_version": 1,
        "mode": "WORKSPACE_CONTROL_CODEX_CALIBRATION_V1",
        "decision": decision,
        "expected_sha": expected_sha,
        "trusted_workflow_sha": trusted_workflow_sha,
        "trusted_helper_blob": trusted_helper_blob,
        "pr_number": pr_number,
        "actor": actor,
        "runner_name": runner_name,
        "runner_user": runner_user,
        "runner_class": "workspace-control-control-small-v1",
        "project_home": project_home,
        "codex_home": codex_home,
        "codex_version": codex_version,
        "surface": "CODEX",
        "isolation_verified": True,
        "model_actions": 1,
        "model_selector": "codex_cli_default",
        "reasoning_effort": "low",
        "sandbox": "read-only",
        "ephemeral": True,
        "account_type": auth.get("account_type"),
        "plan_type": auth.get("plan_type"),
        "requires_openai_auth": auth.get("requires_openai_auth"),
        "api_key_present": False,
        "model_inference_performed": True,
        "credential_material_in_receipt": False,
        "prompt_material_in_receipt": False,
        "model_output_material_in_receipt": False,
        "returncode": result.returncode,
        "strict_trace_passed": trace is not None,
        "output_contract_passed": output_contract_passed,
        "trace_error": trace_error,
        "token_usage": token_usage,
        "usage_before": before,
        "usage_after": after,
    }


def _self_test() -> int:
    print("WORKSPACE_CONTROL_CODEX_CALIBRATION_HELPER_SELF_TEST=PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--expected-sha")
    parser.add_argument("--trusted-workflow-sha")
    parser.add_argument("--trusted-helper-blob")
    parser.add_argument("--pr-number", type=int)
    parser.add_argument("--actor")
    parser.add_argument("--receipt-path")
    args = parser.parse_args()
    if args.self_test:
        return _self_test()

    required = {
        "expected_sha": args.expected_sha,
        "trusted_workflow_sha": args.trusted_workflow_sha,
        "trusted_helper_blob": args.trusted_helper_blob,
        "pr_number": args.pr_number,
        "actor": args.actor,
        "receipt_path": args.receipt_path,
    }
    if any(value is None for value in required.values()):
        raise CalibrationError("required_cli_argument_missing")
    if not isinstance(args.expected_sha, str) or len(args.expected_sha) != 40:
        raise CalibrationError("expected_sha_invalid")
    if (
        not isinstance(args.trusted_workflow_sha, str)
        or len(args.trusted_workflow_sha) != 40
    ):
        raise CalibrationError("trusted_workflow_sha_invalid")
    if (
        not isinstance(args.trusted_helper_blob, str)
        or len(args.trusted_helper_blob) != 40
    ):
        raise CalibrationError("trusted_helper_blob_invalid")
    if "OPENAI_API_KEY" in os.environ:
        raise CalibrationError("OPENAI_API_KEY_must_be_absent")

    codex_bin = os.environ["CODEX_BIN"]
    env = _child_environment(os.environ)
    receipt = execute_calibration(
        expected_sha=args.expected_sha,
        trusted_workflow_sha=args.trusted_workflow_sha,
        trusted_helper_blob=args.trusted_helper_blob,
        pr_number=args.pr_number,
        actor=args.actor,
        runner_name=os.environ.get("RUNNER_NAME"),
        runner_user=os.environ.get("USER"),
        project_home=os.environ["PROJECT_HOME"],
        codex_home=os.environ["CODEX_HOME"],
        codex_version=os.environ["CODEX_VERSION"],
        auth_reader=lambda: read_authorized_account(
            codex_bin=codex_bin,
            environment=env,
        ),
        usage_reader=lambda: read_usage_snapshot(
            codex_bin=codex_bin,
            environment=env,
        ),
        exec_runner=lambda: native_exec_runner(
            codex_bin=codex_bin,
            environment=env,
            temp_root=Path(os.environ["RUNNER_TEMP"]),
        ),
    )
    Path(args.receipt_path).write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    if receipt["decision"] != "PASS":
        raise CalibrationError("calibration_quantum_failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
