"""Privacy-minimal parser for Codex exec JSON event streams."""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Iterable, Mapping

from .ledger import ExecutionTokenUsage


class CodexTraceError(RuntimeError):
    """Fail-closed malformed Codex JSONL trace."""


@dataclass(frozen=True)
class CodexExecTraceSummary:
    thread_id: str | None
    turns_started: int
    turns_completed: int
    turns_failed: int
    token_usage: ExecutionTokenUsage
    command_executions: int
    mcp_tool_calls: int
    collab_tool_calls: int
    web_searches: int
    file_changes: int
    agent_messages: int
    reasoning_items: int
    todo_lists: int
    item_errors: int
    fatal_errors: int
    unknown_events: int

    @property
    def tool_calls(self) -> int:
        return (
            self.command_executions
            + self.mcp_tool_calls
            + self.collab_tool_calls
            + self.web_searches
        )


def _required_nonnegative_int(
    raw: Mapping[str, Any],
    key: str,
) -> int:
    value = raw.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CodexTraceError(f"usage.{key}:expected_nonnegative_integer")
    return value


def _optional_nonnegative_int(
    raw: Mapping[str, Any],
    key: str,
) -> int | None:
    value = raw.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CodexTraceError(
            f"usage.{key}:expected_nonnegative_integer_or_missing"
        )
    return value


def _sum_optional(values: Iterable[int | None]) -> int | None:
    materialized = tuple(values)
    if any(value is None for value in materialized):
        return None
    return sum(int(value) for value in materialized if value is not None)


def parse_codex_exec_jsonl(text: str) -> CodexExecTraceSummary:
    thread_id: str | None = None
    turns_started = 0
    turns_completed = 0
    turns_failed = 0
    input_tokens: list[int] = []
    cached_input_tokens: list[int] = []
    cache_write_input_tokens: list[int | None] = []
    output_tokens: list[int] = []
    reasoning_output_tokens: list[int | None] = []

    counts = {
        "command_execution": 0,
        "mcp_tool_call": 0,
        "collab_tool_call": 0,
        "web_search": 0,
        "file_change": 0,
        "agent_message": 0,
        "reasoning": 0,
        "todo_list": 0,
        "error": 0,
    }
    fatal_errors = 0
    unknown_events = 0

    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CodexTraceError(
                f"line_{line_number}:invalid_json"
            ) from exc
        if not isinstance(raw, Mapping):
            raise CodexTraceError(
                f"line_{line_number}:event_must_be_object"
            )
        event_type = raw.get("type")
        if not isinstance(event_type, str):
            raise CodexTraceError(
                f"line_{line_number}:event_type_required"
            )

        if event_type == "thread.started":
            candidate = raw.get("thread_id")
            if not isinstance(candidate, str) or not candidate:
                raise CodexTraceError(
                    f"line_{line_number}:thread_id_required"
                )
            if thread_id is not None and thread_id != candidate:
                raise CodexTraceError("multiple_thread_ids_in_one_trace")
            thread_id = candidate
            continue

        if event_type == "turn.started":
            turns_started += 1
            continue

        if event_type == "turn.completed":
            usage = raw.get("usage")
            if not isinstance(usage, Mapping):
                raise CodexTraceError(
                    f"line_{line_number}:turn_usage_required"
                )
            turns_completed += 1
            input_tokens.append(
                _required_nonnegative_int(usage, "input_tokens")
            )
            cached_input_tokens.append(
                _required_nonnegative_int(
                    usage,
                    "cached_input_tokens",
                )
            )
            cache_write_input_tokens.append(
                _optional_nonnegative_int(
                    usage,
                    "cache_write_input_tokens",
                )
            )
            output_tokens.append(
                _required_nonnegative_int(usage, "output_tokens")
            )
            reasoning_output_tokens.append(
                _optional_nonnegative_int(
                    usage,
                    "reasoning_output_tokens",
                )
            )
            continue

        if event_type == "turn.failed":
            turns_failed += 1
            continue

        if event_type == "error":
            fatal_errors += 1
            continue

        if event_type in {"item.started", "item.updated"}:
            continue

        if event_type == "item.completed":
            item = raw.get("item")
            if not isinstance(item, Mapping):
                raise CodexTraceError(
                    f"line_{line_number}:completed_item_required"
                )
            item_type = item.get("type")
            if isinstance(item_type, str) and item_type in counts:
                counts[item_type] += 1
            else:
                unknown_events += 1
            continue

        unknown_events += 1

    total_input = sum(input_tokens)
    total_cached = sum(cached_input_tokens)
    total_output = sum(output_tokens)
    total_cache_write = _sum_optional(cache_write_input_tokens)
    total_reasoning = _sum_optional(reasoning_output_tokens)

    return CodexExecTraceSummary(
        thread_id=thread_id,
        turns_started=turns_started,
        turns_completed=turns_completed,
        turns_failed=turns_failed,
        token_usage=ExecutionTokenUsage(
            input_tokens=total_input,
            cached_input_tokens=total_cached,
            cache_write_input_tokens=total_cache_write,
            output_tokens=total_output,
            reasoning_output_tokens=total_reasoning,
            total_tokens=total_input + total_output,
        ),
        command_executions=counts["command_execution"],
        mcp_tool_calls=counts["mcp_tool_call"],
        collab_tool_calls=counts["collab_tool_call"],
        web_searches=counts["web_search"],
        file_changes=counts["file_change"],
        agent_messages=counts["agent_message"],
        reasoning_items=counts["reasoning"],
        todo_lists=counts["todo_list"],
        item_errors=counts["error"],
        fatal_errors=fatal_errors,
        unknown_events=unknown_events,
    )
