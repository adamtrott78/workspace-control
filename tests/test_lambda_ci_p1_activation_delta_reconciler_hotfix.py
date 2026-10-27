import contextlib
import hashlib
import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import lambda_ci_p1_install_activation_delta_reconciler_hotfix as hotfix


class ActivationDeltaReconcilerHotfixTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.repo = self.root / "repo"
        (self.repo / "scripts").mkdir(parents=True)
        self.source = self.repo / hotfix.SOURCE_SERVICE
        self.source.write_bytes(b"new-reviewed-reconciler\n")
        self.installed = self.root / "installed.py"
        self.installed.write_bytes(b"old-reviewed-reconciler\n")
        self.old = self.installed.read_bytes()

        self.receipt = self.root / "6438723476.json"
        self.cursor = self.root / "cursor.json"
        self.receipt.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "status": "COMPLETED",
                    "automatic_workflow_triggered": False,
                    "identity": {
                        "repository": "adamtrott78/workspace-control",
                        "actor": "adamtrott78",
                        "comment_id": hotfix.EXPECTED_COMMENT_ID,
                        "command_sha256": hotfix.EXPECTED_COMMAND_SHA256,
                        "command": {
                            "action": "diagnose",
                            "lane": "cpu",
                            "project_id": "workspace-control",
                            "quarantine_receipt_id": None,
                        },
                    },
                    "result": {
                        "status": "PASS",
                        "operation": "DIAGNOSE_LANE",
                        "observation_only": True,
                        "service_active": False,
                        "active_project_units": [],
                    },
                }
            ),
            encoding="utf-8",
        )
        self.cursor.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "last_seen_comment_id": hotfix.EXPECTED_COMMENT_ID,
                }
            ),
            encoding="utf-8",
        )

        self.running = {
            "LoadState": "loaded",
            "ActiveState": "active",
            "SubState": "running",
            "UnitFileState": "enabled",
            "NRestarts": "0",
            "ExecMainStatus": "0",
            "MainPID": "4000",
            "InvocationID": "root-generation",
        }
        self.frozen = {
            "LoadState": "loaded",
            "ActiveState": "inactive",
            "SubState": "dead",
            "UnitFileState": "enabled",
            "NRestarts": "0",
            "ExecMainStatus": "0",
            "MainPID": "0",
            "InvocationID": "frozen-generation",
        }
        self.controllers = {"sentinel": {"state": "preserved"}}
        self.workspace_dormant = {
            "LoadState": "loaded",
            "ActiveState": "inactive",
            "SubState": "dead",
            "UnitFileState": "disabled",
            "NRestarts": "0",
            "ExecMainStatus": "0",
            "MainPID": "0",
            "InvocationID": "workspace-dormant-generation",
        }
        self.candidate = {
            "registry_state": "MIGRATION_CANDIDATE_NOT_INSTALLED",
            "manifest_state": "MIGRATION_CANDIDATE_NOT_INSTALLED",
            "route_state": "PLANNED_NOT_BOUND",
        }
        self.binding = ("a" * 64, "b" * 64)

    def base_stack(self, fake_run):
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(mock.patch.object(hotfix, "INSTALLED_SERVICE", self.installed))
        stack.enter_context(
            mock.patch.object(
                hotfix,
                "EXPECTED_OLD_SERVICE_SHA256",
                hashlib.sha256(self.old).hexdigest(),
            )
        )
        stack.enter_context(mock.patch.object(hotfix, "attest_source", return_value=self.repo))
        stack.enter_context(mock.patch.object(hotfix.os, "geteuid", return_value=0))
        stack.enter_context(
            mock.patch.dict(hotfix.os.environ, {"SUDO_USER": "atrott"}, clear=False)
        )
        stack.enter_context(mock.patch.object(hotfix.pwd, "getpwnam", return_value=mock.Mock()))
        stack.enter_context(mock.patch.object(hotfix.os, "chown", return_value=None))
        stack.enter_context(mock.patch.object(hotfix, "run", side_effect=fake_run))
        stack.enter_context(
            mock.patch.object(hotfix, "require_service_running", return_value=self.running)
        )
        stack.enter_context(
            mock.patch.object(
                hotfix,
                "require_reconcile_controller_frozen",
                return_value=self.frozen,
            )
        )
        stack.enter_context(
            mock.patch.object(
                hotfix,
                "require_controller_dependency_graph",
                return_value=[hotfix.ROOT_SERVICE],
            )
        )
        stack.enter_context(
            mock.patch.object(
                hotfix,
                "require_controller_baseline",
                return_value=self.controllers,
            )
        )
        stack.enter_context(
            mock.patch.object(
                hotfix,
                "require_workspace_controller_dormant",
                return_value=self.workspace_dormant,
            )
        )
        stack.enter_context(
            mock.patch.object(
                hotfix,
                "require_candidate_dormant",
                return_value=self.candidate,
            )
        )
        stack.enter_context(
            mock.patch.object(
                hotfix,
                "require_successful_diagnose_and_cursor",
                return_value=self.binding,
            )
        )
        stack.enter_context(
            mock.patch.object(
                sys,
                "argv",
                ["hotfix", "--expected-head", "deadbeef"],
            )
        )
        return stack

    def test_successful_diagnose_receipt_and_cursor_are_exactly_bound(self):
        with (
            mock.patch.object(hotfix, "DIAGNOSE_RECEIPT", self.receipt),
            mock.patch.object(hotfix, "CURSOR", self.cursor),
        ):
            receipt_hash, cursor_hash = hotfix.require_successful_diagnose_and_cursor()
        self.assertEqual(receipt_hash, hashlib.sha256(self.receipt.read_bytes()).hexdigest())
        self.assertEqual(len(cursor_hash), 64)

        value = json.loads(self.receipt.read_text(encoding="utf-8"))
        value["result"]["observation_only"] = False
        self.receipt.write_text(json.dumps(value), encoding="utf-8")
        with (
            mock.patch.object(hotfix, "DIAGNOSE_RECEIPT", self.receipt),
            mock.patch.object(hotfix, "CURSOR", self.cursor),
        ):
            with self.assertRaisesRegex(hotfix.HotfixError, "clean observation-only PASS"):
                hotfix.require_successful_diagnose_and_cursor()

    def test_frozen_reconcile_controller_rejects_active_state(self):
        active = dict(self.frozen)
        active.update(
            {
                "ActiveState": "active",
                "SubState": "running",
                "MainPID": "5000",
            }
        )
        with mock.patch.object(hotfix, "service_snapshot", return_value=active):
            with self.assertRaisesRegex(hotfix.HotfixError, "not frozen"):
                hotfix.require_reconcile_controller_frozen()

    def test_workspace_controller_dormancy_rejects_active_state(self):
        active = dict(self.workspace_dormant)
        active.update(
            {
                "ActiveState": "active",
                "SubState": "running",
                "MainPID": "6000",
                "InvocationID": "workspace-active-generation",
            }
        )
        with mock.patch.object(hotfix, "service_snapshot", return_value=active):
            with self.assertRaisesRegex(
                hotfix.HotfixError,
                "workspace-control CPU controller is not dormant",
            ):
                hotfix.require_workspace_controller_dormant()

    def test_active_workspace_controller_blocks_before_mutation(self):
        calls = []

        def fake_run(argv, check=True, user=None):
            calls.append(list(argv))
            return mock.Mock(returncode=0, stdout="", stderr="")

        stack = self.base_stack(fake_run)
        stack.enter_context(
            mock.patch.object(
                hotfix,
                "require_workspace_controller_dormant",
                side_effect=hotfix.HotfixError(
                    "workspace-control CPU controller is not dormant"
                ),
            )
        )
        atomic = stack.enter_context(mock.patch.object(hotfix, "atomic_write"))

        with self.assertRaisesRegex(
            hotfix.HotfixError,
            "workspace-control CPU controller is not dormant",
        ):
            hotfix.main()

        atomic.assert_not_called()
        self.assertEqual(calls, [])

    def test_forward_workspace_controller_generation_drift_fails_closed(self):
        calls = []

        def fake_run(argv, check=True, user=None):
            calls.append(list(argv))
            return mock.Mock(returncode=0, stdout="", stderr="")

        drift = dict(self.workspace_dormant)
        drift["InvocationID"] = "workspace-drifted-generation"

        stack = self.base_stack(fake_run)
        stack.enter_context(mock.patch.object(hotfix, "wait_socket", return_value=None))
        stack.enter_context(
            mock.patch.object(
                hotfix,
                "require_workspace_controller_dormant",
                side_effect=[
                    self.workspace_dormant,
                    drift,
                    self.workspace_dormant,
                ],
            )
        )

        with self.assertRaisesRegex(
            hotfix.HotfixError,
            "workspace-control CPU controller state/generation changed during hotfix",
        ):
            hotfix.main()

        self.assertEqual(self.installed.read_bytes(), self.old)
        self.assertEqual(
            calls,
            [
                [
                    "systemctl",
                    "--job-mode=ignore-dependencies",
                    "restart",
                    hotfix.ROOT_SERVICE,
                ],
                [
                    "systemctl",
                    "--job-mode=ignore-dependencies",
                    "restart",
                    hotfix.ROOT_SERVICE,
                ],
            ],
        )

    def test_rollback_workspace_controller_generation_drift_is_incomplete(self):
        calls = []
        waits = 0

        def fake_run(argv, check=True, user=None):
            calls.append(list(argv))
            return mock.Mock(returncode=0, stdout="", stderr="")

        def fake_wait():
            nonlocal waits
            waits += 1
            if waits == 1:
                raise hotfix.HotfixError("synthetic reconciler readiness failure")

        drift = dict(self.workspace_dormant)
        drift["InvocationID"] = "workspace-rollback-drift"

        stack = self.base_stack(fake_run)
        stack.enter_context(mock.patch.object(hotfix, "wait_socket", side_effect=fake_wait))
        stack.enter_context(
            mock.patch.object(
                hotfix,
                "require_workspace_controller_dormant",
                side_effect=[
                    self.workspace_dormant,
                    drift,
                ],
            )
        )

        with self.assertRaisesRegex(
            hotfix.HotfixError,
            "rollback was incomplete.*rollback changed workspace-control CPU controller state/generation",
        ):
            hotfix.main()

        self.assertEqual(self.installed.read_bytes(), self.old)
        self.assertEqual(waits, 2)
        self.assertEqual(
            calls,
            [
                [
                    "systemctl",
                    "--job-mode=ignore-dependencies",
                    "restart",
                    hotfix.ROOT_SERVICE,
                ],
                [
                    "systemctl",
                    "--job-mode=ignore-dependencies",
                    "restart",
                    hotfix.ROOT_SERVICE,
                ],
            ],
        )

    def test_success_mutates_only_reconciler_and_restarts_root_nonpropagating(self):
        calls = []

        def fake_run(argv, check=True, user=None):
            calls.append(list(argv))
            return mock.Mock(returncode=0, stdout="", stderr="")

        stack = self.base_stack(fake_run)
        stack.enter_context(mock.patch.object(hotfix, "wait_socket", return_value=None))

        rc = hotfix.main()

        self.assertEqual(rc, 0)
        self.assertEqual(self.installed.read_bytes(), self.source.read_bytes())
        self.assertEqual(
            calls,
            [[
                "systemctl",
                "--job-mode=ignore-dependencies",
                "restart",
                hotfix.ROOT_SERVICE,
            ]],
        )

    def test_readiness_failure_restores_prior_bytes_with_same_bounded_restart(self):
        calls = []
        waits = 0

        def fake_run(argv, check=True, user=None):
            calls.append(list(argv))
            return mock.Mock(returncode=0, stdout="", stderr="")

        def fake_wait():
            nonlocal waits
            waits += 1
            if waits == 1:
                raise hotfix.HotfixError("synthetic reconciler readiness failure")

        stack = self.base_stack(fake_run)
        stack.enter_context(mock.patch.object(hotfix, "wait_socket", side_effect=fake_wait))

        with self.assertRaisesRegex(hotfix.HotfixError, "synthetic reconciler readiness"):
            hotfix.main()

        self.assertEqual(self.installed.read_bytes(), self.old)
        expected = [
            [
                "systemctl",
                "--job-mode=ignore-dependencies",
                "restart",
                hotfix.ROOT_SERVICE,
            ],
            [
                "systemctl",
                "--job-mode=ignore-dependencies",
                "restart",
                hotfix.ROOT_SERVICE,
            ],
        ]
        self.assertEqual(calls, expected)
        self.assertEqual(waits, 2)

    def test_source_attestation_rejects_copied_helper_before_git(self):
        external = self.root / "copied.py"
        external.write_text("# copied\n", encoding="utf-8")
        with (
            mock.patch.object(hotfix, "__file__", str(external)),
            mock.patch.object(hotfix, "run") as run_mock,
        ):
            with self.assertRaisesRegex(hotfix.HotfixError, "outside reviewed"):
                hotfix.attest_source("a" * 40, "atrott")
        run_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
