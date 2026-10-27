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


class HotfixReviewCorrectionTests(unittest.TestCase):
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
        self.old = self.installed.read_bytes()
        self.registry = self.root / "registry.json"
        self.manifest = self.root / "workspace-control.json"
        self.receipt = self.root / "6437389584.json"
        self.cursor = self.root / "cursor.json"
        self.registry.write_text(json.dumps({"schema_version": 1}), encoding="utf-8")
        self.manifest.write_text(json.dumps({"schema_version": 2}), encoding="utf-8")
        self.receipt.write_text("{}", encoding="utf-8")
        self.cursor.write_text("{}", encoding="utf-8")
        self.running = {
            "LoadState": "loaded",
            "ActiveState": "active",
            "SubState": "running",
            "UnitFileState": "enabled",
            "NRestarts": "0",
            "ExecMainStatus": "0",
        }
        self.controllers = {"sentinel": dict(self.running)}
        self.candidate = {
            "registry_state": "MIGRATION_CANDIDATE_NOT_INSTALLED",
            "manifest_state": "MIGRATION_CANDIDATE_NOT_INSTALLED",
            "route_state": "PLANNED_NOT_BOUND",
        }
        self.receipt_binding = ("a" * 64, "b" * 64)

    def base_stack(self, run_side_effect):
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(mock.patch.object(hotfix, "INSTALLED_SERVICE", self.installed))
        stack.enter_context(mock.patch.object(hotfix, "REGISTRY", self.registry))
        stack.enter_context(mock.patch.object(hotfix, "MANIFEST", self.manifest))
        stack.enter_context(mock.patch.object(hotfix, "FAILED_RECEIPT", self.receipt))
        stack.enter_context(mock.patch.object(hotfix, "CURSOR", self.cursor))
        stack.enter_context(
            mock.patch.object(
                hotfix,
                "EXPECTED_OLD_SERVICE_SHA256",
                hashlib.sha256(self.old).hexdigest(),
            )
        )
        stack.enter_context(mock.patch.object(hotfix, "attest_source", return_value=self.repo))
        stack.enter_context(mock.patch.object(hotfix.os, "geteuid", return_value=0))
        stack.enter_context(mock.patch.dict(hotfix.os.environ, {"SUDO_USER": "atrott"}, clear=False))
        stack.enter_context(mock.patch.object(hotfix.pwd, "getpwnam", return_value=mock.Mock()))
        stack.enter_context(mock.patch.object(hotfix.os, "chown", return_value=None))
        stack.enter_context(mock.patch.object(hotfix, "run", side_effect=run_side_effect))
        stack.enter_context(mock.patch.object(hotfix, "require_service_running", return_value=self.running))
        stack.enter_context(mock.patch.object(hotfix, "require_controller_baseline", return_value=self.controllers))
        stack.enter_context(
            mock.patch.object(
                hotfix,
                "require_failed_receipt_and_cursor",
                return_value=self.receipt_binding,
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

    def test_post_install_dormancy_failure_rolls_back_instead_of_certifying(self):
        calls = []
        candidate_calls = 0

        def fake_run(argv, check=True, user=None):
            calls.append(list(argv))
            return mock.Mock(returncode=0, stdout="", stderr="")

        def candidate_check():
            nonlocal candidate_calls
            candidate_calls += 1
            if candidate_calls == 2:
                raise hotfix.HotfixError(
                    "unable to inspect workspace-control execution units: "
                    "rc=1 stderr=synthetic post-install inspection failure"
                )
            return self.candidate

        stack = self.base_stack(fake_run)
        stack.enter_context(
            mock.patch.object(
                hotfix,
                "require_candidate_dormant",
                side_effect=candidate_check,
            )
        )
        stack.enter_context(mock.patch.object(hotfix, "wait_socket", return_value=None))

        with self.assertRaisesRegex(
            hotfix.HotfixError,
            "synthetic post-install inspection failure",
        ):
            hotfix.main()

        self.assertEqual(self.installed.read_bytes(), self.old)
        self.assertEqual(candidate_calls, 3)
        self.assertEqual(
            calls,
            [
                ["systemctl", "restart", hotfix.ROOT_SERVICE],
                ["systemctl", "restart", hotfix.ROOT_SERVICE],
            ],
        )

    def test_rollback_dormancy_failure_is_reported_incomplete(self):
        calls = []
        candidate_calls = 0
        wait_calls = 0

        def fake_run(argv, check=True, user=None):
            calls.append(list(argv))
            return mock.Mock(returncode=0, stdout="", stderr="")

        def candidate_check():
            nonlocal candidate_calls
            candidate_calls += 1
            if candidate_calls == 2:
                raise hotfix.HotfixError(
                    "unable to inspect workspace-control execution units: "
                    "rc=1 stderr=synthetic rollback inspection failure"
                )
            return self.candidate

        def wait_check():
            nonlocal wait_calls
            wait_calls += 1
            if wait_calls == 1:
                raise hotfix.HotfixError("synthetic forward readiness failure")

        stack = self.base_stack(fake_run)
        stack.enter_context(
            mock.patch.object(
                hotfix,
                "require_candidate_dormant",
                side_effect=candidate_check,
            )
        )
        stack.enter_context(mock.patch.object(hotfix, "wait_socket", side_effect=wait_check))

        with self.assertRaisesRegex(
            hotfix.HotfixError,
            "rollback was incomplete",
        ):
            hotfix.main()

        self.assertEqual(self.installed.read_bytes(), self.old)
        self.assertEqual(candidate_calls, 2)
        self.assertEqual(wait_calls, 2)
        self.assertEqual(
            calls,
            [
                ["systemctl", "restart", hotfix.ROOT_SERVICE],
                ["systemctl", "restart", hotfix.ROOT_SERVICE],
            ],
        )


if __name__ == "__main__":
    unittest.main()
