"""Subscription-only Codex auth and execution tests."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.adapters import (  # noqa: E402
    CodexProcessResult,
    CodexSubscriptionAuthGuard,
    CodexSubscriptionError,
    CodexSubscriptionExecutionFailed,
    CodexSubscriptionExecutor,
    build_read_only_exec_command,
    parse_account_read_response,
)
from workspace_semantic_execution.domain import (  # noqa: E402
    CommunicationMode,
    ContextMode,
    ReasoningProfile,
    TokenBudget,
)
from workspace_semantic_execution.ports import (  # noqa: E402
    AccountTokenUsageSummary,
    UsageSnapshot,
)


def usage_snapshot(captured_at: str, lifetime: int) -> UsageSnapshot:
    return UsageSnapshot(
        captured_at=captured_at,
        ordinary_usage_allowed=True,
        rate_limit_buckets=(),
        token_summary=AccountTokenUsageSummary(
            lifetime_tokens=lifetime,
            peak_daily_tokens=None,
            longest_running_turn_sec=None,
            current_streak_days=None,
            longest_streak_days=None,
        ),
        daily_usage_buckets=None,
        thread_usage=None,
    )


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []
        self.closed = False

    def request(self, method, params=None):
        self.calls.append((method, params))
        return self.response

    def close(self):
        self.closed = True


class FakeUsage:
    def __init__(self, snapshots):
        self.snapshots = list(snapshots)
        self.calls = 0

    def read_snapshot(self, *, thread_id=None):
        self.calls += 1
        return self.snapshots.pop(0)


class FakeRunner:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def run(self, **kwargs):
        self.calls.append(kwargs)
        return self.result


SUCCESS_JSONL = "\n".join(
    [
        json.dumps({"type": "thread.started", "thread_id": "thread-1"}),
        json.dumps({"type": "turn.started"}),
        json.dumps(
            {
                "type": "item.completed",
                "item": {"type": "command_execution", "command": "git status"},
            }
        ),
        json.dumps(
            {
                "type": "item.completed",
                "item": {
                    "type": "agent_message",
                    "text": json.dumps(
                        {
                            "result_kind": "RESULT",
                            "summary": "validated answer",
                            "evidence_refs": ["test://evidence"],
                        },
                        sort_keys=True,
                    ),
                },
            }
        ),
        json.dumps(
            {
                "type": "turn.completed",
                "usage": {
                    "input_tokens": 100,
                    "cached_input_tokens": 80,
                    "cache_write_input_tokens": 5,
                    "output_tokens": 20,
                    "reasoning_output_tokens": 7,
                },
            }
        ),
    ]
)


def economy_budget(*, max_output_tokens: int = 300) -> TokenBudget:
    return TokenBudget(
        context_mode=ContextMode.REF_ONLY,
        reasoning_profile=ReasoningProfile.ECONOMY,
        communication_mode=CommunicationMode.MACHINE_MINIMAL,
        max_inline_tokens=3000,
        max_retrieved_tokens=12000,
        max_output_tokens=max_output_tokens,
        allow_model_call=True,
    )


def no_model_budget() -> TokenBudget:
    return TokenBudget(
        context_mode=ContextMode.REF_ONLY,
        reasoning_profile=ReasoningProfile.NO_MODEL,
        communication_mode=CommunicationMode.MACHINE_MINIMAL,
        max_inline_tokens=0,
        max_retrieved_tokens=0,
        max_output_tokens=0,
        allow_model_call=False,
    )


class AuthTests(unittest.TestCase):
    def test_chatgpt_plus_is_authorized_even_when_provider_requires_openai_auth(self):
        response = {
            "result": {
                "account": {
                    "type": "chatgpt",
                    "email": "must-not-be-retained@example.com",
                    "planType": "plus",
                    "workspaceName": None,
                },
                "requiresOpenaiAuth": True,
                "userId": "must-not-be-retained",
            }
        }
        fake = FakeSession(response)
        guard = CodexSubscriptionAuthGuard(
            session_factory=lambda: fake,
        )

        info = guard.require_authorized()

        self.assertEqual(info.account_type, "chatgpt")
        self.assertEqual(info.plan_type, "plus")
        self.assertTrue(info.requires_openai_auth)
        self.assertFalse(hasattr(info, "email"))
        self.assertFalse(hasattr(info, "user_id"))
        self.assertEqual(fake.calls, [("account/read", {})])
        self.assertTrue(fake.closed)

    def test_api_key_auth_is_denied(self):
        fake = FakeSession(
            {
                "result": {
                    "account": {"type": "apiKey"},
                    "requiresOpenaiAuth": False,
                }
            }
        )
        guard = CodexSubscriptionAuthGuard(
            session_factory=lambda: fake,
        )
        with self.assertRaisesRegex(
            CodexSubscriptionError,
            "subscription_auth_required",
        ):
            guard.require_authorized()

    def test_other_provider_auth_is_denied(self):
        for account in (
            {"type": "amazonBedrock", "usesCodexManagedCredentials": True},
            {"type": "gcp"},
        ):
            with self.subTest(account=account):
                fake = FakeSession(
                    {
                        "result": {
                            "account": account,
                            "requiresOpenaiAuth": False,
                        }
                    }
                )
                guard = CodexSubscriptionAuthGuard(
                    session_factory=lambda: fake,
                )
                with self.assertRaises(CodexSubscriptionError):
                    guard.require_authorized()

    def test_signed_out_or_unknown_account_fails_closed(self):
        with self.assertRaises(CodexSubscriptionError):
            parse_account_read_response(
                {
                    "result": {
                        "account": None,
                        "requiresOpenaiAuth": True,
                    }
                }
            )

    def test_default_policy_denies_non_plus_chatgpt_plan(self):
        fake = FakeSession(
            {
                "result": {
                    "account": {
                        "type": "chatgpt",
                        "email": None,
                        "planType": "pro",
                        "workspaceName": None,
                    },
                    "requiresOpenaiAuth": True,
                }
            }
        )
        guard = CodexSubscriptionAuthGuard(
            session_factory=lambda: fake,
        )
        with self.assertRaisesRegex(
            CodexSubscriptionError,
            "subscription_plan_not_authorized:pro",
        ):
            guard.require_authorized()


class CommandTests(unittest.TestCase):
    def test_read_only_command_uses_json_ephemeral_sandbox_and_stdin_sentinel(self):
        command = build_read_only_exec_command(
            executable="/usr/bin/codex",
            model_id="gpt-6-luna",
            reasoning_profile=ReasoningProfile.ECONOMY,
        )
        self.assertEqual(command[:8], (
            "/usr/bin/codex",
            "exec",
            "--json",
            "--ephemeral",
            "--sandbox",
            "read-only",
            "-m",
            "gpt-6-luna",
        ))
        self.assertIn("--config", command)
        self.assertIn("model_reasoning_effort=low", command)
        self.assertEqual(command[-1], "-")

    def test_standard_and_deep_map_to_real_codex_reasoning_effort(self):
        standard = build_read_only_exec_command(
            executable="/usr/bin/codex",
            model_id="gpt-6-luna",
            reasoning_profile=ReasoningProfile.STANDARD,
        )
        deep = build_read_only_exec_command(
            executable="/usr/bin/codex",
            model_id="gpt-6-luna",
            reasoning_profile=ReasoningProfile.DEEP,
        )
        self.assertIn("model_reasoning_effort=medium", standard)
        self.assertIn("model_reasoning_effort=high", deep)

    def test_no_model_profile_cannot_build_codex_command(self):
        with self.assertRaisesRegex(
            CodexSubscriptionError,
            "codex_no_model_budget_forbids_execution",
        ):
            build_read_only_exec_command(
                executable="/usr/bin/codex",
                model_id="gpt-6-luna",
                reasoning_profile=ReasoningProfile.NO_MODEL,
            )


class ExecutorTests(unittest.TestCase):
    def _guard(self):
        fake = FakeSession(
            {
                "result": {
                    "account": {
                        "type": "chatgpt",
                        "email": None,
                        "planType": "plus",
                        "workspaceName": None,
                    },
                    "requiresOpenaiAuth": True,
                }
            }
        )
        return CodexSubscriptionAuthGuard(
            session_factory=lambda: fake,
        )

    def test_prompt_is_stdin_only_api_key_is_removed_and_usage_is_snapshotted(self):
        usage = FakeUsage(
            [
                usage_snapshot("2026-11-15T12:00:00+00:00", 1000),
                usage_snapshot("2026-11-15T12:01:00+00:00", 1120),
            ]
        )
        runner = FakeRunner(
            CodexProcessResult(
                returncode=0,
                stdout=SUCCESS_JSONL,
                stderr="",
            )
        )
        times = iter(
            [
                datetime(2026, 11, 15, 12, 0, tzinfo=timezone.utc),
                datetime(2026, 11, 15, 12, 1, tzinfo=timezone.utc),
            ]
        )
        executor = CodexSubscriptionExecutor(
            usage=usage,
            auth_guard=self._guard(),
            process_runner=runner,
            executable="/usr/bin/codex",
            clock=lambda: next(times),
            environment={
                "PATH": "/usr/bin",
                "OPENAI_API_KEY": "must-not-propagate",
            },
        )

        with tempfile.TemporaryDirectory() as tmp:
            observation = executor.run_read_only(
                prompt="inspect this repository",
                model_id="gpt-6-luna",
                cwd=Path(tmp),
                budget=economy_budget(),
            )

        self.assertEqual(usage.calls, 2)
        self.assertEqual(len(runner.calls), 1)
        call = runner.calls[0]
        self.assertEqual(call["prompt"], "inspect this repository")
        self.assertNotIn("inspect this repository", call["command"])
        self.assertEqual(call["command"][-1], "-")
        self.assertNotIn("OPENAI_API_KEY", call["environment"])
        self.assertEqual(observation.trace.token_usage.input_tokens, 100)
        self.assertEqual(observation.trace.token_usage.reasoning_output_tokens, 7)
        self.assertEqual(observation.trace.command_executions, 1)
        self.assertEqual(
            json.loads(observation.final_agent_message)["summary"],
            "validated answer",
        )
        self.assertEqual(
            observation.token_budget.reasoning_profile,
            ReasoningProfile.ECONOMY,
        )
        self.assertEqual(observation.budget_violations, ())
        self.assertIn("model_reasoning_effort=low", call["command"])
        self.assertIn("--output-schema", call["command"])

    def test_auth_failure_occurs_before_usage_snapshot_or_process(self):
        fake = FakeSession(
            {
                "result": {
                    "account": {"type": "apiKey"},
                    "requiresOpenaiAuth": False,
                }
            }
        )
        usage = FakeUsage([])
        runner = FakeRunner(
            CodexProcessResult(returncode=0, stdout="", stderr="")
        )
        executor = CodexSubscriptionExecutor(
            usage=usage,
            auth_guard=CodexSubscriptionAuthGuard(
                session_factory=lambda: fake,
            ),
            process_runner=runner,
            executable="/usr/bin/codex",
        )
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(CodexSubscriptionError):
                executor.run_read_only(
                    prompt="do not run",
                    model_id="gpt-6-luna",
                    cwd=Path(tmp),
                    budget=economy_budget(),
                )
        self.assertEqual(usage.calls, 0)
        self.assertEqual(runner.calls, [])

    def test_no_model_budget_fails_before_auth_usage_or_process(self):
        usage = FakeUsage([])
        runner = FakeRunner(
            CodexProcessResult(returncode=0, stdout=SUCCESS_JSONL, stderr="")
        )
        executor = CodexSubscriptionExecutor(
            usage=usage,
            auth_guard=self._guard(),
            process_runner=runner,
            executable="/usr/bin/codex",
        )
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(
                CodexSubscriptionError,
                "codex_no_model_budget_forbids_execution",
            ):
                executor.run_read_only(
                    prompt="must not run",
                    model_id="gpt-6-luna",
                    cwd=Path(tmp),
                    budget=no_model_budget(),
                )
        self.assertEqual(usage.calls, 0)
        self.assertEqual(runner.calls, [])

    def test_observed_output_overrun_is_preserved_and_fails_closed(self):
        usage = FakeUsage(
            [
                usage_snapshot("2026-11-15T12:00:00+00:00", 1000),
                usage_snapshot("2026-11-15T12:01:00+00:00", 1120),
            ]
        )
        runner = FakeRunner(
            CodexProcessResult(returncode=0, stdout=SUCCESS_JSONL, stderr="")
        )
        executor = CodexSubscriptionExecutor(
            usage=usage,
            auth_guard=self._guard(),
            process_runner=runner,
            executable="/usr/bin/codex",
        )
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(
                CodexSubscriptionExecutionFailed,
                "codex_token_budget_violation",
            ) as caught:
                executor.run_read_only(
                    prompt="bounded task",
                    model_id="gpt-6-luna",
                    cwd=Path(tmp),
                    budget=economy_budget(max_output_tokens=10),
                )
        self.assertIn(
            "visible_output_tokens_exceeded:20>10",
            caught.exception.observation.budget_violations,
        )

    def test_failed_turn_preserves_measurable_observation(self):
        failed_jsonl = "\n".join(
            [
                json.dumps({"type": "thread.started", "thread_id": "t"}),
                json.dumps({"type": "turn.started"}),
                json.dumps({"type": "turn.failed", "error": {"message": "x"}}),
            ]
        )
        usage = FakeUsage(
            [
                usage_snapshot("2026-11-15T12:00:00+00:00", 1000),
                usage_snapshot("2026-11-15T12:00:10+00:00", 1030),
            ]
        )
        runner = FakeRunner(
            CodexProcessResult(
                returncode=1,
                stdout=failed_jsonl,
                stderr="failure detail",
            )
        )
        times = iter(
            [
                datetime(2026, 11, 15, 12, 0, tzinfo=timezone.utc),
                datetime(2026, 11, 15, 12, 0, 10, tzinfo=timezone.utc),
            ]
        )
        executor = CodexSubscriptionExecutor(
            usage=usage,
            auth_guard=self._guard(),
            process_runner=runner,
            executable="/usr/bin/codex",
            clock=lambda: next(times),
        )
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(CodexSubscriptionExecutionFailed) as caught:
                executor.run_read_only(
                    prompt="bounded task",
                    model_id="gpt-6-luna",
                    cwd=Path(tmp),
                    budget=economy_budget(),
                )
        observation = caught.exception.observation
        self.assertEqual(observation.returncode, 1)
        self.assertEqual(observation.trace.turns_failed, 1)
        self.assertIsNone(observation.trace.token_usage.total_tokens)
        self.assertIsNone(
            observation.trace.token_usage.reasoning_output_tokens
        )
        self.assertEqual(
            observation.usage_before.token_summary.lifetime_tokens,
            1000,
        )
        self.assertEqual(
            observation.usage_after.token_summary.lifetime_tokens,
            1030,
        )


if __name__ == "__main__":
    unittest.main()
