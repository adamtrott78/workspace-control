from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


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
                    "item": {"id": "r1", "type": "reasoning", "text": ""},
                }
            ),
            event(
                {
                    "type": "item.completed",
                    "item": {"id": "r1", "type": "reasoning", "text": ""},
                }
            ),
            event(
                {
                    "type": "item.started",
                    "item": {"id": "m1", "type": "agent_message", "text": ""},
                }
            ),
            event(
                {
                    "type": "item.updated",
                    "item": {"id": "m1", "type": "agent_message", "text": ""},
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
                        "cache_write_input_tokens": 0,
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

    def test_trace_rejects_unknown_fields_in_known_shapes(self):
        base = [json.loads(line) for line in successful_trace().splitlines()]
        mutations = {}

        thread_extra = json.loads(json.dumps(base))
        thread_extra[0]["future_field"] = True
        mutations["thread_extra"] = thread_extra

        turn_extra = json.loads(json.dumps(base))
        turn_extra[1]["future_field"] = True
        mutations["turn_extra"] = turn_extra

        event_extra = json.loads(json.dumps(base))
        event_extra[2]["future_field"] = True
        mutations["item_event_extra"] = event_extra

        item_extra = json.loads(json.dumps(base))
        item_extra[2]["item"]["future_field"] = True
        mutations["item_payload_extra"] = item_extra

        usage_extra = json.loads(json.dumps(base))
        usage_extra[-1]["usage"]["future_tokens"] = 1
        mutations["usage_extra"] = usage_extra

        item_missing = json.loads(json.dumps(base))
        del item_missing[2]["item"]["text"]
        mutations["item_missing_text"] = item_missing

        for name, rows in mutations.items():
            with self.subTest(name=name):
                trace = "\n".join(event(row) for row in rows)
                with self.assertRaisesRegex(
                    calibration.CalibrationError,
                    "shape_mismatch",
                ):
                    calibration.parse_strict_calibration_trace(trace)

    def test_native_exec_runner_removes_model_visible_tool_surfaces(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            completed = subprocess.CompletedProcess(
                args=["codex"],
                returncode=0,
                stdout=successful_trace(),
            )
            with mock.patch.object(
                calibration.subprocess,
                "run",
                side_effect=[
                    subprocess.CompletedProcess(args=["git"], returncode=0),
                    completed,
                ],
            ) as run:
                result = calibration.native_exec_runner(
                    codex_bin="/trusted/codex",
                    environment={
                        "CODEX_HOME": "/trusted/codex-home",
                        "OPENAI_API_KEY": "must-not-propagate",
                        "PYTHONPATH": "/candidate",
                        "PYTHONHOME": "/candidate-python",
                    },
                    temp_root=temp_root,
                )

            self.assertEqual(result.returncode, 0)
            self.assertEqual(run.call_count, 2)
            command = run.call_args_list[1].args[0]
            self.assertEqual(command[0:3], ["/trusted/codex", "exec", "--json"])
            self.assertIn("--ephemeral", command)
            self.assertIn("--sandbox", command)
            self.assertEqual(
                command[command.index("--model") + 1],
                calibration.CALIBRATION_MODEL,
            )
            model_config = next(
                value
                for value in command
                if value.startswith("model_catalog_json=")
            )
            catalog_path = Path(json.loads(model_config.split("=", 1)[1]))
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            self.assertEqual(len(catalog["models"]), 1)
            model = catalog["models"][0]
            self.assertEqual(model["slug"], calibration.CALIBRATION_MODEL)
            self.assertEqual(model["shell_type"], "disabled")
            self.assertIsNone(model["apply_patch_tool_type"])
            self.assertFalse(model["supports_search_tool"])
            self.assertEqual(model["experimental_supported_tools"], [])
            self.assertEqual(model["input_modalities"], ["text"])
            self.assertEqual(model["tool_mode"], "direct")
            self.assertEqual(model["multi_agent_version"], "disabled")
            self.assertTrue(model["node_repl_disabled"])

            child_env = run.call_args_list[1].kwargs["env"]
            self.assertNotIn("OPENAI_API_KEY", child_env)
            self.assertNotIn("PYTHONPATH", child_env)
            self.assertNotIn("PYTHONHOME", child_env)
            self.assertEqual(child_env["CODEX_HOME"], "/trusted/codex-home")

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
