import importlib.util
import json
import os
import pathlib
import stat
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "lambda_ci_v3_workspace_control_terminal_revival_live.py"


def load_module():
    spec = importlib.util.spec_from_file_location("terminal_revival_live", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


live = load_module()


class TerminalRevivalLiveTests(unittest.TestCase):
    def old_record(self):
        return {
            "schema_version": 1,
            "controller_policy_sha256": "c" * 64,
            "runner_request_id": live.GITHUB_JOB_ID,
            "github_job_id": live.GITHUB_JOB_ID,
            "authority_source": "REST_ACTIVE_JOB_SET",
            "workflow_run_id": live.WORKFLOW_RUN_ID,
            "workflow_path": live.WORKFLOW_PATH,
            "workflow_blob_sha": live.WORKFLOW_BLOB,
            "request_id": live.EXPECTED_OLD_REQUEST_ID,
            "runner_name": live.EXPECTED_OLD_RUNNER_NAME,
            "provision_attempt": 0,
            "state": "COMPLETED",
            "scheduler_state": "COMPLETED",
            "last_root_status": "COMPLETED",
        }

    def test_review_block_parser_requires_exact_single_block(self):
        body = """x
WORKSPACE_CONTROL_REVIEW_DISPOSITION_V1
request_comment_id=1
disposition=NO_BLOCKING_FINDING
END_WORKSPACE_CONTROL_REVIEW_DISPOSITION_V1
"""
        got = live.exact_block(body, live.DISP_START, live.DISP_END)
        self.assertEqual(got["request_comment_id"], "1")
        self.assertEqual(got["disposition"], "NO_BLOCKING_FINDING")
        with self.assertRaises(live.LiveRevivalError):
            live.exact_block(body + body, live.DISP_START, live.DISP_END)

    def test_request_binding_parser_reads_exact_blob_lines(self):
        body = "- scripts/a.py -> " + "a" * 40 + "\n- tests/t.py -> " + "b" * 40 + "\n"
        self.assertEqual(
            live.request_bindings(body),
            {"scripts/a.py": "a" * 40, "tests/t.py": "b" * 40},
        )

    def test_dropin_overrides_only_target_execstart(self):
        text = live.dropin_bytes().decode()
        self.assertEqual(
            text,
            "[Service]\nExecStart=\n"
            f"ExecStart={live.OVERRIDE_BINARY}\n",
        )
        self.assertNotIn("padataset", text.lower())
        self.assertNotIn("research-engine", text.lower())

    def test_ledger_preflight_binds_exact_incident_record(self):
        with tempfile.TemporaryDirectory() as raw:
            path = pathlib.Path(raw) / "scheduler.json"
            record = self.old_record()
            content = (json.dumps(record, sort_keys=True) + "\n").encode()
            path.write_bytes(content)
            path.chmod(0o600)
            fake_user = types.SimpleNamespace(pw_uid=os.getuid())
            with (
                mock.patch.object(live, "LEDGER_PATH", path),
                mock.patch.object(live, "EXPECTED_LEDGER_SHA256", live.sha256(content)),
                mock.patch.object(live.pwd, "getpwnam", return_value=fake_user),
            ):
                returned_raw, returned = live.verify_ledger(
                    {"controller_policy_sha256": "c" * 64}
                )
            self.assertEqual(returned_raw, content)
            self.assertEqual(returned, record)

    def test_ledger_preflight_rejects_durable_github_job_drift(self):
        with tempfile.TemporaryDirectory() as raw:
            path = pathlib.Path(raw) / "scheduler.json"
            record = self.old_record()
            record["github_job_id"] += 1
            content = (json.dumps(record, sort_keys=True) + "\n").encode()
            path.write_bytes(content)
            path.chmod(0o600)
            fake_user = types.SimpleNamespace(pw_uid=os.getuid())
            with (
                mock.patch.object(live, "LEDGER_PATH", path),
                mock.patch.object(live, "EXPECTED_LEDGER_SHA256", live.sha256(content)),
                mock.patch.object(live.pwd, "getpwnam", return_value=fake_user),
            ):
                with self.assertRaisesRegex(
                    live.LiveRevivalError,
                    "github_job_id",
                ):
                    live.verify_ledger({"controller_policy_sha256": "c" * 64})

    def test_first_revival_requires_exact_single_increment_and_fresh_identity(self):
        old = self.old_record()
        old_raw = (json.dumps(old, sort_keys=True) + "\n").encode()
        new = dict(old)
        new.update(
            {
                "provision_attempt": 1,
                "request_id": "fresh-request",
                "runner_name": live.TARGET_RUNNER_PREFIX + "fresh",
                "state": "ACQUIRED",
                "scheduler_state": "REST_ATTESTED_QUEUED_RETRY",
                "last_root_status": "",
            }
        )
        with tempfile.TemporaryDirectory() as raw:
            path = pathlib.Path(raw) / "scheduler.json"
            path.write_text(json.dumps(new) + "\n")
            with mock.patch.object(live, "LEDGER_PATH", path):
                result = live.observe_first_revival(old_raw, old)
        self.assertEqual(result["provision_attempt"], 1)
        self.assertEqual(result["scheduler_state"], "REST_ATTESTED_QUEUED_RETRY")
        self.assertEqual(result["request_id"], "fresh-request")

    def test_first_revival_rejects_provenance_change(self):
        old = self.old_record()
        old_raw = (json.dumps(old, sort_keys=True) + "\n").encode()
        new = dict(old)
        new.update(
            {
                "provision_attempt": 1,
                "request_id": "fresh-request",
                "runner_name": live.TARGET_RUNNER_PREFIX + "fresh",
                "workflow_run_id": old["workflow_run_id"] + 1,
                "scheduler_state": "REST_ATTESTED_QUEUED_RETRY",
            }
        )
        with tempfile.TemporaryDirectory() as raw:
            path = pathlib.Path(raw) / "scheduler.json"
            path.write_text(json.dumps(new) + "\n")
            with mock.patch.object(live, "LEDGER_PATH", path):
                with self.assertRaisesRegex(live.LiveRevivalError, "workflow_run_id"):
                    live.observe_first_revival(old_raw, old)

    def test_sibling_generation_change_is_rejected(self):
        target = live.TARGET_SERVICE
        sibling = "workspace-ci-v3-controller@padataset-cpu-public-v1.service"
        before = {
            target: {"MainPID": "1"},
            sibling: {"MainPID": "2", "InvocationID": "a"},
        }
        after = {
            target: {"MainPID": "3"},
            sibling: {"MainPID": "2", "InvocationID": "b"},
        }
        with self.assertRaisesRegex(live.LiveRevivalError, "sibling"):
            live.verify_siblings_unchanged(before, after)

    def test_operator_source_has_no_workflow_mutation_endpoint(self):
        source = SCRIPT.read_text()
        for forbidden in (
            "/cancel",
            "/rerun",
            "/dispatches",
            "rerun_workflow",
            "cancel_workflow",
        ):
            self.assertNotIn(forbidden, source)

    def test_operator_never_writes_scheduler_ledger(self):
        source = SCRIPT.read_text()
        self.assertIn("script_mutates_scheduler_ledger", source)
        self.assertNotIn("atomic_write(LEDGER_PATH", source)
        self.assertNotIn("LEDGER_PATH.write_", source)
        self.assertNotIn("os.replace(tmp, LEDGER_PATH", source)

    def test_only_target_service_is_restarted(self):
        source = SCRIPT.read_text()
        restart_lines = [
            line.strip()
            for line in source.splitlines()
            if '["systemctl", "restart"' in line
        ]
        self.assertEqual(
            restart_lines,
            [
                'subprocess.run(["systemctl", "restart", TARGET_SERVICE], check=True)',
                'subprocess.run(["systemctl", "restart", TARGET_SERVICE], check=True)',
            ],
        )
        self.assertNotIn('restart", LEGACY_V2_SERVICE', source)

    def test_review_binding_paths_cover_executable_surface(self):
        self.assertEqual(
            set(live.REVIEW_BINDING_PATHS),
            {
                "scripts/lambda_ci_v3_workspace_control_terminal_revival_live.py",
                "scripts/lambda_ci_v3_workspace_control_terminal_revival_live.sh",
                "tests/test_lambda_ci_v3_workspace_control_terminal_revival_live.py",
                "architecture/lambda-ci-v3-workspace-control-terminal-revival-live.v1.md",
            },
        )


if __name__ == "__main__":
    unittest.main()
