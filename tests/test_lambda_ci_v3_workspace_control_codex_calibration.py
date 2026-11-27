from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = (
    ROOT / "scripts" / "lambda_ci_v3_workspace_control_codex_calibration_v1.py"
)

spec = importlib.util.spec_from_file_location(
    "workspace_control_codex_calibration_v1",
    HELPER_PATH,
)
calibration = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["workspace_control_codex_calibration_v1"] = calibration
spec.loader.exec_module(calibration)


def event(payload: dict) -> str:
    return json.dumps(payload, separators=(",", ":"))


def successful_trace() -> str:
    return "\n".join(
        [
            event({"type": "thread.started", "thread_id": "thread-1"}),
            event({"type": "turn.started"}),
            event(
                {
                    "type": "item.started",
                    "item": {"id": "r1", "type": "reasoning"},
                }
            ),
            event(
                {
                    "type": "item.completed",
                    "item": {"id": "r1", "type": "reasoning"},
                }
            ),
            event(
                {
                    "type": "item.started",
                    "item": {"id": "m1", "type": "agent_message"},
                }
            ),
            event(
                {
                    "type": "item.updated",
                    "item": {"id": "m1", "type": "agent_message"},
                }
            ),
            event(
                {
                    "type": "item.completed",
                    "item": {
                        "id": "m1",
                        "type": "agent_message",
                        "text": json.dumps(
                            {
                                "result_kind": "RESULT",
                                "summary": "CALIBRATION_OK",
                                "evidence_refs": [],
                            },
                            separators=(",", ":"),
                        ),
                    },
                }
            ),
            event(
                {
                    "type": "turn.completed",
                    "usage": {
                        "input_tokens": 12,
                        "cached_input_tokens": 4,
                        "cache_write_input_tokens": None,
                        "output_tokens": 7,
                        "reasoning_output_tokens": 2,
                    },
                }
            ),
        ]
    )


def usage_snapshot(label: str) -> dict:
    return {
        "captured_at": f"2026-11-27T22:00:0{label}+00:00",
        "ordinary_usage_allowed": True,
        "rate_limits": [
            {
                "limit_id": "codex",
                "limit_name": "Codex",
                "normal_model_slug": None,
                "plan_type": "plus",
                "primary": {
                    "used_percent": int(label),
                    "window_duration_mins": 300,
                    "resets_at": 1,
                },
                "secondary": {
                    "used_percent": int(label),
                    "window_duration_mins": 10080,
                    "resets_at": 2,
                },
            }
        ],
        "token_summary": {
            "lifetime_tokens": None,
            "peak_daily_tokens": None,
            "longest_running_turn_sec": None,
            "current_streak_days": None,
            "longest_streak_days": None,
        },
        "daily_usage_bucket_count": None,
    }


class WorkspaceControlCodexCalibrationTests(unittest.TestCase):
    def test_execute_calibration_runs_exactly_one_exec_in_order_and_redacts(self):
        calls: list[str] = []
        snapshots = [usage_snapshot("0"), usage_snapshot("1")]

        def auth_reader():
            calls.append("auth")
            return {
                "account_type": "chatgpt",
                "plan_type": "plus",
                "requires_openai_auth": True,
            }

        def usage_reader():
            calls.append("usage")
            return snapshots.pop(0)

        def exec_runner():
            calls.append("exec")
            return calibration.ExecResult(
                returncode=0,
                stdout=successful_trace(),
            )

        receipt = calibration.execute_calibration(
            expected_sha="a" * 40,
            trusted_workflow_sha="b" * 40,
            trusted_helper_blob="c" * 40,
            pr_number=590,
            actor="owner",
            runner_name="lambda-workspace-control-control-small-test",
            runner_user="ci-workspace-control",
            project_home="/srv/workspace-ci/workspace-control/home",
            codex_home="/srv/workspace-ci/workspace-control/home/.codex-reasoning-economy",
            codex_version="0.155.1",
            auth_reader=auth_reader,
            usage_reader=usage_reader,
            exec_runner=exec_runner,
        )

        self.assertEqual(calls, ["auth", "usage", "exec", "usage"])
        self.assertEqual(calls.count("exec"), 1)
        self.assertEqual(receipt["decision"], "PASS")
        self.assertEqual(receipt["model_actions"], 1)
        self.assertTrue(receipt["strict_trace_passed"])
        self.assertTrue(receipt["output_contract_passed"])
        self.assertEqual(receipt["usage_before"]["captured_at"], snapshots_before := "2026-11-27T22:00:00+00:00")
        self.assertEqual(receipt["usage_after"]["captured_at"], "2026-11-27T22:00:01+00:00")
        self.assertEqual(receipt["token_usage"]["total_tokens"], 19)

        serialized = json.dumps(receipt, sort_keys=True)
        self.assertNotIn("CALIBRATION_OK", serialized)
        self.assertNotIn("thread-1", serialized)
        for forbidden in (
            "email",
            "user_id",
            "account_id",
            "access_token",
            "refresh_token",
            "device_code",
            "auth.json",
            "final_agent_message",
            "thread-1",
            "CALIBRATION_OK",
        ):
            self.assertNotIn(forbidden.lower(), serialized.lower())
        self.assertFalse(receipt["prompt_material_in_receipt"])
        self.assertFalse(receipt["model_output_material_in_receipt"])
        self.assertFalse(receipt["credential_material_in_receipt"])
        self.assertEqual(snapshots_before, "2026-11-27T22:00:00+00:00")

    def test_trace_rejects_forbidden_activity_on_every_item_stage(self):
        for stage in ("item.started", "item.updated", "item.completed"):
            for item_type in (
                "command_execution",
                "mcp_tool_call",
                "collab_tool_call",
                "web_search",
                "file_change",
                "error",
                "todo_list",
            ):
                with self.subTest(stage=stage, item_type=item_type):
                    trace = "\n".join(
                        [
                            event({"type": "thread.started", "thread_id": "t"}),
                            event({"type": "turn.started"}),
                            event(
                                {
                                    "type": stage,
                                    "item": {
                                        "id": "x",
                                        "type": item_type,
                                    },
                                }
                            ),
                        ]
                    )
                    with self.assertRaisesRegex(
                        calibration.CalibrationError,
                        "forbidden_item_activity",
                    ):
                        calibration.parse_strict_calibration_trace(trace)

    def test_trace_rejects_unknown_error_and_incomplete_events(self):
        cases = {
            "unknown_top_level": "\n".join(
                [
                    event({"type": "thread.started", "thread_id": "t"}),
                    event({"type": "turn.started"}),
                    event({"type": "future.event"}),
                ]
            ),
            "unknown_item": "\n".join(
                [
                    event({"type": "thread.started", "thread_id": "t"}),
                    event({"type": "turn.started"}),
                    event(
                        {
                            "type": "item.started",
                            "item": {"id": "x", "type": "future_tool"},
                        }
                    ),
                ]
            ),
            "fatal_error": "\n".join(
                [
                    event({"type": "thread.started", "thread_id": "t"}),
                    event({"type": "turn.started"}),
                    event({"type": "error", "message": "secret"}),
                ]
            ),
            "turn_failed": "\n".join(
                [
                    event({"type": "thread.started", "thread_id": "t"}),
                    event({"type": "turn.started"}),
                    event({"type": "turn.failed"}),
                ]
            ),
            "incomplete_allowed_item": "\n".join(
                [
                    event({"type": "thread.started", "thread_id": "t"}),
                    event({"type": "turn.started"}),
                    event(
                        {
                            "type": "item.started",
                            "item": {"id": "r", "type": "reasoning"},
                        }
                    ),
                    event(
                        {
                            "type": "turn.completed",
                            "usage": {
                                "input_tokens": 1,
                                "cached_input_tokens": 0,
                                "output_tokens": 1,
                            },
                        }
                    ),
                ]
            ),
        }
        for name, trace in cases.items():
            with self.subTest(name=name):
                with self.assertRaises(calibration.CalibrationError):
                    calibration.parse_strict_calibration_trace(trace)

    def test_failed_trace_produces_fail_receipt_after_after_snapshot(self):
        calls: list[str] = []
        snapshots = [usage_snapshot("0"), usage_snapshot("1")]

        def usage_reader():
            calls.append("usage")
            return snapshots.pop(0)

        receipt = calibration.execute_calibration(
            expected_sha="a" * 40,
            trusted_workflow_sha="b" * 40,
            trusted_helper_blob="c" * 40,
            pr_number=590,
            actor="owner",
            runner_name=None,
            runner_user=None,
            project_home="/project",
            codex_home="/codex",
            codex_version="0.155.1",
            auth_reader=lambda: {
                "account_type": "chatgpt",
                "plan_type": "plus",
                "requires_openai_auth": True,
            },
            usage_reader=usage_reader,
            exec_runner=lambda: calibration.ExecResult(
                returncode=0,
                stdout="{}",
            ),
        )

        self.assertEqual(calls, ["usage", "usage"])
        self.assertEqual(receipt["decision"], "FAIL")
        self.assertFalse(receipt["strict_trace_passed"])
        self.assertIsNotNone(receipt["trace_error"])
        self.assertEqual(
            receipt["usage_after"]["captured_at"],
            "2026-11-27T22:00:01+00:00",
        )

    def test_python_isolated_mode_does_not_execute_candidate_sitecustomize(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            marker = root / "candidate-executed"
            (root / "sitecustomize.py").write_text(
                "from pathlib import Path\n"
                f"Path({str(marker)!r}).write_text('BAD', encoding='utf-8')\n",
                encoding="utf-8",
            )
            env = dict(os.environ)
            env["PYTHONPATH"] = str(root)
            completed = subprocess.run(
                [sys.executable, "-I", str(HELPER_PATH), "--self-test"],
                cwd=root,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn(
                "WORKSPACE_CONTROL_CODEX_CALIBRATION_HELPER_SELF_TEST=PASS",
                completed.stdout,
            )
            self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main()
