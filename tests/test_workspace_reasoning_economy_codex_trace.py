"""Codex JSONL trace accounting tests for Reasoning Economy."""
from __future__ import annotations

from pathlib import Path
import json
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.economics import (  # noqa: E402
    CodexTraceError,
    parse_codex_exec_jsonl,
)


def line(payload):
    return json.dumps(payload, separators=(",", ":"))


class CodexTraceTests(unittest.TestCase):
    def test_current_trace_aggregates_all_token_and_tool_fields(self):
        trace = "\n".join(
            [
                line({"type": "thread.started", "thread_id": "thread-1"}),
                line({"type": "turn.started"}),
                line(
                    {
                        "type": "item.completed",
                        "item": {"type": "reasoning", "text": "private"},
                    }
                ),
                line(
                    {
                        "type": "item.completed",
                        "item": {"type": "command_execution", "command": "pytest"},
                    }
                ),
                line(
                    {
                        "type": "item.completed",
                        "item": {"type": "mcp_tool_call", "server": "github"},
                    }
                ),
                line(
                    {
                        "type": "item.completed",
                        "item": {"type": "web_search", "query": "x"},
                    }
                ),
                line(
                    {
                        "type": "item.completed",
                        "item": {"type": "file_change", "path": "x.py"},
                    }
                ),
                line(
                    {
                        "type": "item.completed",
                        "item": {"type": "agent_message", "text": "answer"},
                    }
                ),
                line(
                    {
                        "type": "turn.completed",
                        "usage": {
                            "input_tokens": 100,
                            "cached_input_tokens": 70,
                            "cache_write_input_tokens": 9,
                            "output_tokens": 30,
                            "reasoning_output_tokens": 12,
                        },
                    }
                ),
                line({"type": "turn.started"}),
                line(
                    {
                        "type": "turn.completed",
                        "usage": {
                            "input_tokens": 50,
                            "cached_input_tokens": 10,
                            "cache_write_input_tokens": 3,
                            "output_tokens": 20,
                            "reasoning_output_tokens": 8,
                        },
                    }
                ),
            ]
        )

        summary = parse_codex_exec_jsonl(trace)

        self.assertEqual(summary.thread_id, "thread-1")
        self.assertEqual(summary.turns_started, 2)
        self.assertEqual(summary.turns_completed, 2)
        self.assertEqual(summary.turns_failed, 0)
        self.assertEqual(summary.token_usage.input_tokens, 150)
        self.assertEqual(summary.token_usage.cached_input_tokens, 80)
        self.assertEqual(summary.token_usage.cache_write_input_tokens, 12)
        self.assertEqual(summary.token_usage.output_tokens, 50)
        self.assertEqual(summary.token_usage.reasoning_output_tokens, 20)
        self.assertEqual(summary.token_usage.total_tokens, 200)
        self.assertEqual(summary.command_executions, 1)
        self.assertEqual(summary.mcp_tool_calls, 1)
        self.assertEqual(summary.web_searches, 1)
        self.assertEqual(summary.file_changes, 1)
        self.assertEqual(summary.agent_messages, 1)
        self.assertEqual(summary.reasoning_items, 1)
        self.assertEqual(summary.tool_calls, 3)

    def test_missing_newer_token_fields_remain_unknown_not_zero(self):
        trace = line(
            {
                "type": "turn.completed",
                "usage": {
                    "input_tokens": 10,
                    "cached_input_tokens": 5,
                    "output_tokens": 4,
                },
            }
        )
        summary = parse_codex_exec_jsonl(trace)
        self.assertIsNone(summary.token_usage.cache_write_input_tokens)
        self.assertIsNone(summary.token_usage.reasoning_output_tokens)

    def test_item_updates_do_not_double_count_tools(self):
        item = {"type": "command_execution", "command": "pytest"}
        trace = "\n".join(
            [
                line({"type": "item.started", "item": item}),
                line({"type": "item.updated", "item": item}),
                line({"type": "item.completed", "item": item}),
            ]
        )
        summary = parse_codex_exec_jsonl(trace)
        self.assertEqual(summary.command_executions, 1)

    def test_failed_and_fatal_events_are_counted_without_content_retention(self):
        trace = "\n".join(
            [
                line({"type": "turn.failed", "error": {"message": "secret detail"}}),
                line({"type": "error", "message": "another secret"}),
                line(
                    {
                        "type": "item.completed",
                        "item": {"type": "error", "message": "item secret"},
                    }
                ),
            ]
        )
        summary = parse_codex_exec_jsonl(trace)
        self.assertEqual(summary.turns_failed, 1)
        self.assertEqual(summary.fatal_errors, 1)
        self.assertEqual(summary.item_errors, 1)
        self.assertFalse(hasattr(summary, "messages"))
        self.assertFalse(hasattr(summary, "raw_events"))

    def test_malformed_json_fails_closed(self):
        with self.assertRaises(CodexTraceError):
            parse_codex_exec_jsonl("{bad")

    def test_multiple_thread_ids_fail_closed(self):
        trace = "\n".join(
            [
                line({"type": "thread.started", "thread_id": "a"}),
                line({"type": "thread.started", "thread_id": "b"}),
            ]
        )
        with self.assertRaises(CodexTraceError):
            parse_codex_exec_jsonl(trace)

    def test_negative_usage_fails_closed(self):
        trace = line(
            {
                "type": "turn.completed",
                "usage": {
                    "input_tokens": -1,
                    "cached_input_tokens": 0,
                    "output_tokens": 0,
                },
            }
        )
        with self.assertRaises(CodexTraceError):
            parse_codex_exec_jsonl(trace)


if __name__ == "__main__":
    unittest.main()
