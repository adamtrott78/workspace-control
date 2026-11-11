import importlib.util
import json
import os
import pathlib
import stat
import subprocess
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

    def _root_service_states(self):
        provisioner = {
            "Id": live.PROVISIONER_SERVICE,
            "LoadState": "loaded",
            "ActiveState": "active",
            "SubState": "running",
            "MainPID": "305379",
            "NRestarts": "0",
            "InvocationID": "p" * 32,
            "User": "root",
            "Group": "root",
            "Type": "simple",
            "RemainAfterExit": "no",
            "Result": "success",
            "ExecMainStatus": "0",
        }
        reconciler = {
            "Id": live.RECONCILER_SERVICE,
            "LoadState": "loaded",
            "ActiveState": "active",
            "SubState": "exited",
            "MainPID": "0",
            "NRestarts": "0",
            "InvocationID": "r" * 32,
            "User": "root",
            "Group": "root",
            "Type": "oneshot",
            "RemainAfterExit": "yes",
            "Result": "success",
            "ExecMainStatus": "0",
        }
        target = {
            "Id": live.TARGET_SERVICE,
            "LoadState": "loaded",
            "ActiveState": "active",
            "SubState": "running",
            "MainPID": "1066315",
            "NRestarts": "0",
            "InvocationID": "t" * 32,
            "User": live.TARGET_USER,
            "Group": live.TARGET_GROUP,
            "Type": "simple",
            "RemainAfterExit": "no",
            "Result": "success",
            "ExecMainStatus": "0",
        }
        legacy = {
            "Id": live.LEGACY_V2_SERVICE,
            "LoadState": "loaded",
            "ActiveState": "inactive",
            "SubState": "dead",
            "MainPID": "0",
            "NRestarts": "0",
            "InvocationID": "",
            "User": "",
            "Group": "",
            "Type": "simple",
            "RemainAfterExit": "no",
            "Result": "success",
            "ExecMainStatus": "0",
        }
        return provisioner, reconciler, target, legacy

    def test_repository_reconciler_unit_declares_healthy_oneshot_semantics(self):
        unit = (ROOT / "systemd/workspace-ci-v3-reconciler.service").read_text()
        self.assertIn("Type=oneshot", unit)
        self.assertIn("RemainAfterExit=yes", unit)
        self.assertIn("--verify-installed", unit)

    def test_repository_provisioner_unit_declares_long_running_simple_semantics(self):
        unit = (ROOT / "systemd/workspace-ci-v3-provisioner.service").read_text()
        self.assertIn("Type=simple", unit)
        self.assertIn("Restart=on-failure", unit)

    def test_service_boundary_accepts_actual_root_service_steady_states(self):
        provisioner, reconciler, target, legacy = self._root_service_states()
        states = {
            live.PROVISIONER_SERVICE: provisioner,
            live.RECONCILER_SERVICE: reconciler,
            live.TARGET_SERVICE: target,
            live.LEGACY_V2_SERVICE: legacy,
        }
        with (
            mock.patch.object(live, "systemctl_show", side_effect=lambda unit: states[unit]),
            mock.patch.object(live, "snapshot_services", return_value={live.TARGET_SERVICE: target}),
        ):
            result = live.verify_service_boundary()
        self.assertEqual(result, {live.TARGET_SERVICE: target})

    def test_service_boundary_rejects_reconciler_states_outside_oneshot_contract(self):
        provisioner, reconciler, target, legacy = self._root_service_states()
        mutations = {
            "running-with-pid": {"SubState": "running", "MainPID": "99"},
            "inactive": {"ActiveState": "inactive", "SubState": "dead"},
            "wrong-type": {"Type": "simple"},
            "no-remain-after-exit": {"RemainAfterExit": "no"},
            "failed-result": {"Result": "failed"},
            "failed-exec-status": {"ExecMainStatus": "1"},
            "unexpected-mainpid": {"MainPID": "44"},
        }
        for name, delta in mutations.items():
            with self.subTest(name=name):
                bad = dict(reconciler)
                bad.update(delta)
                states = {
                    live.PROVISIONER_SERVICE: provisioner,
                    live.RECONCILER_SERVICE: bad,
                    live.TARGET_SERVICE: target,
                    live.LEGACY_V2_SERVICE: legacy,
                }
                with (
                    mock.patch.object(live, "systemctl_show", side_effect=lambda unit, states=states: states[unit]),
                    mock.patch.object(live, "snapshot_services", return_value={live.TARGET_SERVICE: target}),
                ):
                    with self.assertRaises(live.LiveRevivalError):
                        live.verify_service_boundary()

    def test_service_boundary_still_requires_running_provisioner_with_pid(self):
        provisioner, reconciler, target, legacy = self._root_service_states()
        provisioner["SubState"] = "exited"
        provisioner["MainPID"] = "0"
        states = {
            live.PROVISIONER_SERVICE: provisioner,
            live.RECONCILER_SERVICE: reconciler,
            live.TARGET_SERVICE: target,
            live.LEGACY_V2_SERVICE: legacy,
        }
        with (
            mock.patch.object(live, "systemctl_show", side_effect=lambda unit: states[unit]),
            mock.patch.object(live, "snapshot_services", return_value={live.TARGET_SERVICE: target}),
        ):
            with self.assertRaisesRegex(live.LiveRevivalError, "long-running"):
                live.verify_service_boundary()

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

    def test_only_target_service_is_mutated_by_systemctl(self):
        source = SCRIPT.read_text()
        self.assertEqual(
            source.count('subprocess.run(["systemctl", "restart", TARGET_SERVICE], check=True)'),
            1,
        )
        self.assertEqual(
            source.count('subprocess.run(["systemctl", "stop", TARGET_SERVICE], check=True)'),
            1,
        )
        self.assertEqual(
            source.count('subprocess.run(["systemctl", "start", TARGET_SERVICE], check=True)'),
            1,
        )
        self.assertNotIn('restart", LEGACY_V2_SERVICE', source)
        self.assertNotIn('start", LEGACY_V2_SERVICE', source)
        self.assertNotIn('stop", LEGACY_V2_SERVICE', source)

    def _review_request_fields(self):
        fields = {
            "task_id": live.TASK_ID,
            "pr_number": "604",
            "head_sha": "a" * 40,
            "base_sha": "b" * 40,
            "tree_sha": "c" * 40,
            "review_kind": live.LIVE_REVIEW_KIND,
            "sensitivity": "authority_sensitive",
            "bindings_sha256": "d" * 64,
            "request_copilot": "false",
        }
        fields["request_digest"] = live.sha256(live.compact_json(fields))
        return fields

    def _accepted_review_rows(self, request_fields):
        request_id = 123
        common = {
            "task_id": live.TASK_ID,
            "pr_number": "604",
            "head_sha": request_fields["head_sha"],
            "review_kind": live.LIVE_REVIEW_KIND,
            "sensitivity": "authority_sensitive",
        }
        disposition = {
            "request_comment_id": str(request_id),
            "request_digest": request_fields["request_digest"],
            **common,
            "reviewer_attestation": "fresh_independent_session",
            "disposition": "NO_BLOCKING_FINDING",
        }
        consumption = {
            "request_comment_id": str(request_id),
            "request_digest": request_fields["request_digest"],
            **common,
            "backend": "comment",
            "disposition_id": "456",
            "disposition": "NO_BLOCKING_FINDING",
        }
        return request_id, common, (456, disposition, "reviewer"), (789, consumption, "github-actions[bot]")

    def test_review_authority_exact_chain_is_accepted(self):
        request = self._review_request_fields()
        request_id, common, disposition, consumption = self._accepted_review_rows(request)
        result = live.validate_bound_review_state(
            request_fields=request,
            request_comment_id=request_id,
            expected_common=common,
            dispositions=[disposition],
            consumptions=[consumption],
        )
        self.assertEqual(result["review_disposition_comment_id"], 456)
        self.assertEqual(result["review_consumption_comment_id"], 789)

    def test_review_authority_rejects_wrong_or_missing_request_digest(self):
        for mode in ("wrong", "missing"):
            with self.subTest(mode=mode):
                request = self._review_request_fields()
                request_id, common, disposition, consumption = self._accepted_review_rows(request)
                if mode == "wrong":
                    request["request_digest"] = "0" * 64
                else:
                    request.pop("request_digest")
                with self.assertRaises(live.LiveRevivalError):
                    live.validate_bound_review_state(
                        request_fields=request,
                        request_comment_id=request_id,
                        expected_common=common,
                        dispositions=[disposition],
                        consumptions=[consumption],
                    )

    def test_review_authority_rejects_conflicting_blocking_disposition(self):
        request = self._review_request_fields()
        request_id, common, disposition, consumption = self._accepted_review_rows(request)
        blocking = dict(disposition[1])
        blocking["disposition"] = "BLOCKING_FINDINGS"
        with self.assertRaisesRegex(live.LiveRevivalError, "exactly one bound disposition"):
            live.validate_bound_review_state(
                request_fields=request,
                request_comment_id=request_id,
                expected_common=common,
                dispositions=[disposition, (457, blocking, "reviewer-2")],
                consumptions=[consumption],
            )

    def test_review_authority_rejects_duplicate_acceptance(self):
        request = self._review_request_fields()
        request_id, common, disposition, consumption = self._accepted_review_rows(request)
        duplicate = (457, dict(disposition[1]), "reviewer-2")
        with self.assertRaisesRegex(live.LiveRevivalError, "exactly one bound disposition"):
            live.validate_bound_review_state(
                request_fields=request,
                request_comment_id=request_id,
                expected_common=common,
                dispositions=[disposition, duplicate],
                consumptions=[consumption],
            )

    def test_review_authority_rejects_stale_head_or_digest_reuse(self):
        for mode in ("stale-head", "stale-digest", "consumption-digest"):
            with self.subTest(mode=mode):
                request = self._review_request_fields()
                request_id, common, disposition, consumption = self._accepted_review_rows(request)
                disp = (disposition[0], dict(disposition[1]), disposition[2])
                used = (consumption[0], dict(consumption[1]), consumption[2])
                if mode == "stale-head":
                    disp[1]["head_sha"] = "f" * 40
                elif mode == "stale-digest":
                    disp[1]["request_digest"] = "e" * 64
                else:
                    used[1]["request_digest"] = "e" * 64
                with self.assertRaises(live.LiveRevivalError):
                    live.validate_bound_review_state(
                        request_fields=request,
                        request_comment_id=request_id,
                        expected_common=common,
                        dispositions=[disp],
                        consumptions=[used],
                    )

    def test_review_authority_rejects_duplicate_consumption(self):
        request = self._review_request_fields()
        request_id, common, disposition, consumption = self._accepted_review_rows(request)
        duplicate = (790, dict(consumption[1]), "github-actions[bot]")
        with self.assertRaisesRegex(live.LiveRevivalError, "exactly one bound consumption"):
            live.validate_bound_review_state(
                request_fields=request,
                request_comment_id=request_id,
                expected_common=common,
                dispositions=[disposition],
                consumptions=[consumption, duplicate],
            )

    def test_untracked_go_source_or_workspace_blocks_source_preflight(self):
        for relative in (
            "controller/lambda-ci-controller/v3/unreviewed.go",
            "go.work",
        ):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as raw:
                root = pathlib.Path(raw)
                subprocess.run(["git", "init", "-q", str(root)], check=True)
                subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.com"], check=True)
                subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
                (root / "tracked.txt").write_text("tracked\n")
                subprocess.run(["git", "-C", str(root), "add", "tracked.txt"], check=True)
                subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "base"], check=True)
                subprocess.run(["git", "-C", str(root), "checkout", "-q", "--detach", "HEAD"], check=True)
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("unreviewed\n")
                with mock.patch.object(live, "git_blob") as blob:
                    blob.side_effect = lambda _root, _head, path: (
                        live.REVIEWED_CONTROLLER_GO_BLOB
                        if path.endswith("controller.go")
                        else live.REVIEWED_CONTROLLER_TEST_BLOB
                    )
                    with self.assertRaisesRegex(live.LiveRevivalError, "including untracked"):
                        live.assert_source(root)

    def test_controller_build_uses_reviewed_git_archive_and_disables_workspace(self):
        source = SCRIPT.read_text()
        self.assertIn('"archive", "--format=tar"', source)
        self.assertIn("REVIEWED_CONTROLLER_HEAD", source)
        self.assertIn('build_env["GOWORK"] = "off"', source)
        self.assertIn('build_env["GOENV"] = "off"', source)
        self.assertIn('build_env["GOFLAGS"] = ""', source)
        self.assertNotIn('cwd=repo_root / "controller/lambda-ci-controller"', source)

    def test_rollback_quiesces_before_ledger_decision_and_retains_override_on_race(self):
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            ledger = root / "ledger.json"
            old_raw = b"old-ledger\n"
            ledger.write_bytes(old_raw)
            override_root = root / "override"
            override_root.mkdir()
            override_binary = override_root / "controller"
            override_binary.write_bytes(b"accepted-controller")
            dropin = root / "dropin.conf"
            dropin.write_text("[Service]\n")
            receipt_path = root / "receipt.json"
            receipt = {}

            calls = []
            def fake_run(args, check=False, **kwargs):
                calls.append(args)
                if args == ["systemctl", "stop", live.TARGET_SERVICE]:
                    ledger.write_bytes(b"revived-ledger\n")
                return subprocess.CompletedProcess(args, 0)

            with (
                mock.patch.object(live, "LEDGER_PATH", ledger),
                mock.patch.object(live, "OVERRIDE_ROOT", override_root),
                mock.patch.object(live, "OVERRIDE_BINARY", override_binary),
                mock.patch.object(live, "DROPIN_PATH", dropin),
                mock.patch.object(live.subprocess, "run", side_effect=fake_run),
                mock.patch.object(
                    live,
                    "wait_target_stopped",
                    return_value={"ActiveState": "inactive", "SubState": "dead", "MainPID": "0"},
                ),
            ):
                with self.assertRaisesRegex(live.LiveRevivalError, "ledger changed"):
                    live.rollback_before_revival(receipt, receipt_path, old_raw)

            saved = json.loads(receipt_path.read_text())
            self.assertEqual(saved["phase"], "POST_REVIVAL_FAIL_CLOSED_NO_ROLLBACK")
            self.assertTrue(saved["accepted_override_retained"])
            self.assertTrue(saved["target_controller_left_quiesced"])
            self.assertTrue(override_binary.exists())
            self.assertTrue(dropin.exists())
            self.assertEqual(calls, [["systemctl", "stop", live.TARGET_SERVICE]])

    def test_pre_revival_rollback_stops_then_rechecks_then_restores_original(self):
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            ledger = root / "ledger.json"
            old_raw = b"old-ledger\n"
            ledger.write_bytes(old_raw)
            override_root = root / "override"
            override_root.mkdir()
            override_binary = override_root / "controller"
            override_binary.write_bytes(b"accepted-controller")
            dropin = root / "dropin.conf"
            dropin.write_text("[Service]\n")
            receipt_path = root / "receipt.json"
            receipt = {}
            calls = []

            def fake_run(args, check=False, **kwargs):
                calls.append(args)
                return subprocess.CompletedProcess(args, 0)

            with (
                mock.patch.object(live, "LEDGER_PATH", ledger),
                mock.patch.object(live, "OVERRIDE_ROOT", override_root),
                mock.patch.object(live, "OVERRIDE_BINARY", override_binary),
                mock.patch.object(live, "DROPIN_PATH", dropin),
                mock.patch.object(live.subprocess, "run", side_effect=fake_run),
                mock.patch.object(
                    live,
                    "wait_target_stopped",
                    return_value={"ActiveState": "inactive", "SubState": "dead", "MainPID": "0"},
                ),
                mock.patch.object(
                    live,
                    "wait_target_active",
                    return_value={"ActiveState": "active", "SubState": "running", "MainPID": "99"},
                ),
            ):
                live.rollback_before_revival(receipt, receipt_path, old_raw)

            self.assertFalse(override_binary.exists())
            self.assertFalse(dropin.exists())
            self.assertEqual(
                calls,
                [
                    ["systemctl", "stop", live.TARGET_SERVICE],
                    ["systemctl", "daemon-reload"],
                    ["systemctl", "start", live.TARGET_SERVICE],
                ],
            )
            saved = json.loads(receipt_path.read_text())
            self.assertEqual(saved["phase"], "ROLLED_BACK_BEFORE_REVIVAL")

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
