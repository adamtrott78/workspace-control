"""Reasoning Economy usage telemetry tests."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.adapters import (  # noqa: E402
    CodexAppServerStdioSession,
    CodexUsageCollector,
    CodexUsageError,
    classify_window,
    parse_rate_limits_response,
    parse_usage_response,
)
from workspace_semantic_execution.adapters.codex_usage import (  # noqa: E402
    sanitized_codex_environment,
)
from workspace_semantic_execution.ports import (  # noqa: E402
    RateLimitWindowClass,
)


class FakeSession:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []
        self.closed = False

    def request(self, method, params=None):
        self.calls.append((method, params))
        return self.responses[method]

    def close(self):
        self.closed = True


RATE_LIMIT_RESPONSE = {
    "id": 2,
    "result": {
        "ordinaryUsageAllowed": True,
        "rateLimits": {
            "limitId": "codex",
            "limitName": "Codex",
            "normalModelSlug": "gpt-6-luna",
            "planType": "plus",
            # Deliberately invert the common primary/secondary assumption.
            "primary": {
                "usedPercent": 21,
                "windowDurationMins": 10080,
                "resetsAt": 2000,
            },
            "secondary": {
                "usedPercent": 8,
                "windowDurationMins": 300,
                "resetsAt": 1000,
            },
        },
        "rateLimitsByLimitId": {
            "codex": {
                "limitId": "codex",
                "limitName": "Codex",
                "normalModelSlug": "gpt-6-luna",
                "planType": "plus",
                "primary": {
                    "usedPercent": 21,
                    "windowDurationMins": 10080,
                    "resetsAt": 2000,
                },
                "secondary": {
                    "usedPercent": 8,
                    "windowDurationMins": 300,
                    "resetsAt": 1000,
                },
            },
            "codex_other": {
                "limitId": "codex_other",
                "limitName": None,
                "normalModelSlug": None,
                "planType": "plus",
                "primary": {
                    "usedPercent": 50,
                    "windowDurationMins": 60,
                    "resetsAt": None,
                },
                "secondary": None,
            },
        },
        # Identity and upsell fields exist upstream but must not enter our
        # normalized reasoning-economy snapshot.
        "accountId": "secret-account-id",
        "rateLimitUpsell": {"title": "Buy more"},
        "rateLimitResetCredits": {
            "availableCount": 99,
            "credits": [{"id": "credit-secret"}],
        },
    },
}

USAGE_RESPONSE = {
    "id": 3,
    "result": {
        "summary": {
            "lifetimeTokens": 123456789,
            "peakDailyTokens": 4567890,
            "longestRunningTurnSec": 321,
            "currentStreakDays": None,
            "longestStreakDays": 17,
        },
        "dailyUsageBuckets": [
            {"startDate": "2026-11-14", "tokens": 1000},
            {"startDate": "2026-11-15", "tokens": 2500},
        ],
        "threadUsage": {
            "inputTokens": 700,
            "cachedInputTokens": 600,
            "outputTokens": 42,
            "reasoningOutputTokens": 13,
        },
    },
}


class ParserTests(unittest.TestCase):
    def test_window_classification_uses_duration_not_primary_secondary(self):
        ordinary, buckets = parse_rate_limits_response(RATE_LIMIT_RESPONSE)

        self.assertTrue(ordinary)
        codex = next(bucket for bucket in buckets if bucket.limit_id == "codex")
        classes = {window.source_role: window.window_class for window in codex.windows}
        self.assertEqual(classes["primary"], RateLimitWindowClass.WEEKLY)
        self.assertEqual(classes["secondary"], RateLimitWindowClass.FIVE_HOUR)

    def test_other_and_unknown_window_classes_are_preserved(self):
        self.assertEqual(classify_window(60), RateLimitWindowClass.OTHER)
        self.assertEqual(classify_window(None), RateLimitWindowClass.UNKNOWN)

    def test_multi_bucket_limits_are_retained_without_identity_or_credit_data(self):
        _ordinary, buckets = parse_rate_limits_response(RATE_LIMIT_RESPONSE)

        self.assertEqual({bucket.limit_id for bucket in buckets}, {"codex", "codex_other"})
        self.assertFalse(any(hasattr(bucket, "account_id") for bucket in buckets))
        self.assertFalse(any(hasattr(bucket, "credits") for bucket in buckets))

    def test_usage_nulls_are_not_converted_to_zero(self):
        summary, daily, thread = parse_usage_response(USAGE_RESPONSE)

        self.assertEqual(summary.lifetime_tokens, 123456789)
        self.assertIsNone(summary.current_streak_days)
        self.assertIsNotNone(daily)
        self.assertEqual(daily[1].tokens, 2500)
        self.assertEqual(thread["reasoningOutputTokens"], 13)

    def test_null_daily_and_thread_usage_remain_unknown(self):
        summary, daily, thread = parse_usage_response(
            {
                "result": {
                    "summary": {
                        "lifetimeTokens": None,
                        "peakDailyTokens": None,
                        "longestRunningTurnSec": None,
                        "currentStreakDays": None,
                        "longestStreakDays": None,
                    },
                    "dailyUsageBuckets": None,
                    "threadUsage": None,
                }
            }
        )
        self.assertIsNone(summary.lifetime_tokens)
        self.assertIsNone(daily)
        self.assertIsNone(thread)


class CollectorTests(unittest.TestCase):
    def test_collector_uses_only_two_read_only_methods_and_closes_session(self):
        fake = FakeSession(
            {
                "account/rateLimits/read": RATE_LIMIT_RESPONSE,
                "account/usage/read": USAGE_RESPONSE,
            }
        )
        collector = CodexUsageCollector(
            session_factory=lambda: fake,
            clock=lambda: datetime(2026, 11, 15, 14, 30, tzinfo=timezone.utc),
        )

        snapshot = collector.read_snapshot(thread_id="thread-123")

        self.assertEqual(
            fake.calls,
            [
                ("account/rateLimits/read", None),
                ("account/usage/read", {"threadId": "thread-123"}),
            ],
        )
        self.assertTrue(fake.closed)
        self.assertEqual(
            snapshot.captured_at,
            "2026-11-15T14:30:00+00:00",
        )
        self.assertEqual(
            len(snapshot.windows_by_class(RateLimitWindowClass.WEEKLY)),
            1,
        )
        self.assertEqual(
            len(snapshot.windows_by_class(RateLimitWindowClass.FIVE_HOUR)),
            1,
        )

    def test_unauthorized_rpc_is_rejected_before_process_access(self):
        session = object.__new__(CodexAppServerStdioSession)
        with self.assertRaises(CodexUsageError):
            session.request(
                "account/rateLimitResetCredit/consume",
                {"idempotencyKey": "NOPE"},
            )

    def test_api_key_is_removed_from_child_environment(self):
        env = sanitized_codex_environment(
            {
                "PATH": "/bin",
                "OPENAI_API_KEY": "paid-secret",
                "KEEP": "yes",
            }
        )
        self.assertNotIn("OPENAI_API_KEY", env)
        self.assertEqual(env["KEEP"], "yes")

    def test_naive_clock_fails_closed(self):
        fake = FakeSession(
            {
                "account/rateLimits/read": RATE_LIMIT_RESPONSE,
                "account/usage/read": USAGE_RESPONSE,
            }
        )
        collector = CodexUsageCollector(
            session_factory=lambda: fake,
            clock=lambda: datetime(2026, 11, 15, 14, 30),
        )
        with self.assertRaises(CodexUsageError):
            collector.read_snapshot()


if __name__ == "__main__":
    unittest.main()
