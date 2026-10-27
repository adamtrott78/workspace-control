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

import lambda_ci_p1_install_preactivation_diagnose_hotfix as hotfix


class PreactivationDiagnoseHotfixInstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.repo = self.root / "repo"
        (self.repo / "scripts").mkdir(parents=True)
        self.source = self.repo / hotfix.SOURCE_SERVICE
        self.source.write_bytes(b"new-reviewed-service\n")
        self.installed = self.root / "installed.py"
        self.installed.write_bytes(b"old-reviewed-service\n")
        self.registry = self.root / "registry.json"
        self.manifest = self.root / "workspace-control.json"
        self.receipt = self.root / "6437389584.json"
        self.cursor = self.root / "cursor.json"

        self.registry.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "projects": {
                        "workspace-control": {
                            "activation_state": "MIGRATION_CANDIDATE_NOT_INSTALLED",
                            "lanes": ["cpu"],
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        self.manifest.write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "project_id": "workspace-control",
                    "status": "MIGRATION_CANDIDATE_NOT_INSTALLED",
                    "routes": {
                        "control-validation": {
                            "activation_state": "PLANNED_NOT_BOUND",
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        self.receipt.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "status": "FAILED_CLOSED",
                    "automatic_workflow_triggered": False,
                    "error": "root maintenance request rejected: maintenance target project is not active",
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
                }
            ),
            encoding="utf-8",
        )
        self.cursor.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "last_seen_comment_id": hotfix.EXPECTED_COMMENT_ID,
                    "last_seen_updated_at": "2026-10-27T08:41:38Z",
                    "initialized_at": "2026-10-27T08:38:06Z",
                }
            ),
            encoding="utf-8",
        )

    def patched_paths(self):
        return (
            mock.patch.object(hotfix, "INSTALLED_SERVICE", self.installed),
            mock.patch.object(hotfix, "REGISTRY", self.registry),
            mock.patch.object(hotfix, "MANIFEST", self.manifest),
            mock.patch.object(hotfix, "FAILED_RECEIPT", self.receipt),
            mock.patch.object(hotfix, "CURSOR", self.cursor),
            mock.patch.object(
                hotfix,
                "EXPECTED_OLD_SERVICE_SHA256",
                hashlib.sha256(self.installed.read_bytes()).hexdigest(),
            ),
        )

    def test_candidate_dormant_requires_exact_dual_candidate_state(self):
        with (
            mock.patch.object(hotfix, "REGISTRY", self.registry),
            mock.patch.object(hotfix, "MANIFEST", self.manifest),
            mock.patch.object(
                hotfix,
                "run",
                return_value=mock.Mock(returncode=0, stdout="", stderr=""),
            ),
        ):
            result = hotfix.require_candidate_dormant()
        self.assertEqual(
            result,
            {
                "registry_state": "MIGRATION_CANDIDATE_NOT_INSTALLED",
                "manifest_state": "MIGRATION_CANDIDATE_NOT_INSTALLED",
                "route_state": "PLANNED_NOT_BOUND",
            },
        )

        manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
        manifest["status"] = "ACTIVE"
        self.manifest.write_text(json.dumps(manifest), encoding="utf-8")
        with (
            mock.patch.object(hotfix, "REGISTRY", self.registry),
            mock.patch.object(hotfix, "MANIFEST", self.manifest),
            mock.patch.object(
                hotfix,
                "run",
                return_value=mock.Mock(returncode=0, stdout="", stderr=""),
            ),
        ):
            with self.assertRaisesRegex(hotfix.HotfixError, "manifest state"):
                hotfix.require_candidate_dormant()

    def test_failed_receipt_and_cursor_are_exactly_bound(self):
        with (
            mock.patch.object(hotfix, "FAILED_RECEIPT", self.receipt),
            mock.patch.object(hotfix, "CURSOR", self.cursor),
        ):
            receipt_hash, cursor_hash = hotfix.require_failed_receipt_and_cursor()
        self.assertEqual(receipt_hash, hashlib.sha256(self.receipt.read_bytes()).hexdigest())
        self.assertEqual(len(cursor_hash), 64)

        receipt = json.loads(self.receipt.read_text(encoding="utf-8"))
        receipt["identity"]["comment_id"] += 1
        self.receipt.write_text(json.dumps(receipt), encoding="utf-8")
        with (
            mock.patch.object(hotfix, "FAILED_RECEIPT", self.receipt),
            mock.patch.object(hotfix, "CURSOR", self.cursor),
        ):
            with self.assertRaisesRegex(hotfix.HotfixError, "comment identity"):
                hotfix.require_failed_receipt_and_cursor()

    def test_success_mutates_only_installed_service_and_restarts_root_service(self):
        calls = []
        running = {
            "LoadState": "loaded",
            "ActiveState": "active",
            "SubState": "running",
            "UnitFileState": "enabled",
            "NRestarts": "0",
            "ExecMainStatus": "0",
        }
        controllers = {
            "sentinel": {
                "LoadState": "loaded",
                "ActiveState": "active",
                "SubState": "running",
                "UnitFileState": "enabled",
                "NRestarts": "0",
                "ExecMainStatus": "0",
            }
        }
        candidate = {
            "registry_state": "MIGRATION_CANDIDATE_NOT_INSTALLED",
            "manifest_state": "MIGRATION_CANDIDATE_NOT_INSTALLED",
            "route_state": "PLANNED_NOT_BOUND",
        }
        receipt_binding = ("a" * 64, "b" * 64)

        def fake_run(argv, check=True, user=None):
            calls.append(list(argv))
            return mock.Mock(returncode=0, stdout="", stderr="")

        patches = self.patched_paths()
        with (
            *patches,
            mock.patch.object(hotfix, "attest_source", return_value=self.repo),
            mock.patch.object(hotfix.os, "geteuid", return_value=0),
            mock.patch.dict(hotfix.os.environ, {"SUDO_USER": "atrott"}, clear=False),
            mock.patch.object(hotfix.pwd, "getpwnam", return_value=mock.Mock()),
            mock.patch.object(hotfix, "run", side_effect=fake_run),
            mock.patch.object(hotfix, "require_service_running", return_value=running),
            mock.patch.object(hotfix, "require_controller_baseline", return_value=controllers),
            mock.patch.object(hotfix, "require_candidate_dormant", return_value=candidate),
            mock.patch.object(hotfix, "require_failed_receipt_and_cursor", return_value=receipt_binding),
            mock.patch.object(hotfix, "wait_socket", return_value=None),
            mock.patch.object(
                sys,
                "argv",
                ["hotfix", "--expected-head", "deadbeef"],
            ),
        ):
            rc = hotfix.main()

        self.assertEqual(rc, 0)
        self.assertEqual(self.installed.read_bytes(), self.source.read_bytes())
        self.assertEqual(
            calls,
            [["systemctl", "restart", hotfix.ROOT_SERVICE]],
        )

    def test_restart_failure_restores_prior_bytes_and_restarts_root_again(self):
        calls = []
        old = self.installed.read_bytes()
        running = {
            "LoadState": "loaded",
            "ActiveState": "active",
            "SubState": "running",
            "UnitFileState": "enabled",
            "NRestarts": "0",
            "ExecMainStatus": "0",
        }
        controllers = {"sentinel": running}
        candidate = {
            "registry_state": "MIGRATION_CANDIDATE_NOT_INSTALLED",
            "manifest_state": "MIGRATION_CANDIDATE_NOT_INSTALLED",
            "route_state": "PLANNED_NOT_BOUND",
        }
        receipt_binding = ("a" * 64, "b" * 64)
        socket_calls = 0

        def fake_run(argv, check=True, user=None):
            calls.append(list(argv))
            return mock.Mock(returncode=0, stdout="", stderr="")

        def fake_wait():
            nonlocal socket_calls
            socket_calls += 1
            if socket_calls == 1:
                raise hotfix.HotfixError("synthetic readiness failure")

        patches = self.patched_paths()
        with (
            *patches,
            mock.patch.object(hotfix, "attest_source", return_value=self.repo),
            mock.patch.object(hotfix.os, "geteuid", return_value=0),
            mock.patch.dict(hotfix.os.environ, {"SUDO_USER": "atrott"}, clear=False),
            mock.patch.object(hotfix.pwd, "getpwnam", return_value=mock.Mock()),
            mock.patch.object(hotfix, "run", side_effect=fake_run),
            mock.patch.object(hotfix, "require_service_running", return_value=running),
            mock.patch.object(hotfix, "require_controller_baseline", return_value=controllers),
            mock.patch.object(hotfix, "require_candidate_dormant", return_value=candidate),
            mock.patch.object(hotfix, "require_failed_receipt_and_cursor", return_value=receipt_binding),
            mock.patch.object(hotfix, "wait_socket", side_effect=fake_wait),
            mock.patch.object(
                sys,
                "argv",
                ["hotfix", "--expected-head", "deadbeef"],
            ),
        ):
            with self.assertRaisesRegex(hotfix.HotfixError, "synthetic"):
                hotfix.main()

        self.assertEqual(self.installed.read_bytes(), old)
        self.assertEqual(
            calls,
            [
                ["systemctl", "restart", hotfix.ROOT_SERVICE],
                ["systemctl", "restart", hotfix.ROOT_SERVICE],
            ],
        )


if __name__ == "__main__":
    unittest.main()
