import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/lambda_ci_p1_install_activation_submission_boundary.py"
ONCE_UNIT = ROOT / "systemd/workspace-ci-reconcile-controller-once.service"
DAEMON_UNIT = ROOT / "systemd/workspace-ci-reconcile-controller.service"


def load_module():
    spec = importlib.util.spec_from_file_location("activation_boundary", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ActivationSubmissionBoundaryTests(unittest.TestCase):
    def test_installer_is_bound_to_exact_pre_activation_baselines(self):
        module = load_module()
        self.assertEqual(
            module.EXPECTED_OLD_ROOT_SHA256,
            "5e3c56c84f8e9755334ca4f0db7bdd7036f70b3e4cd404ebb02e8aa6b97185a9",
        )
        self.assertEqual(
            module.EXPECTED_OLD_CONTROLLER_GIT_BLOB_SHA,
            "cdb38af360676abb053c1d171cc4dc3ef39e977a",
        )
        self.assertEqual(
            module.INSTALLED_ROOT,
            pathlib.Path("/opt/workspace-ci/reconciler/lambda_ci_reconciler.py"),
        )
        self.assertEqual(
            module.INSTALLED_CONTROLLER,
            pathlib.Path(
                "/opt/workspace-ci/reconcile-controller/lambda_ci_reconcile_controller.py"
            ),
        )
        self.assertEqual(
            module.INSTALLED_ONCE_UNIT,
            pathlib.Path(
                "/etc/systemd/system/workspace-ci-reconcile-controller-once.service"
            ),
        )

    def test_installer_never_starts_automatic_or_one_shot_controller(self):
        raw = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn(
            'run(["systemctl", "start", AUTO_CONTROLLER])',
            raw,
        )
        self.assertNotIn(
            'run(["systemctl", "restart", AUTO_CONTROLLER])',
            raw,
        )
        self.assertNotIn(
            'run(["systemctl", "start", ONCE_SERVICE])',
            raw,
        )
        self.assertNotIn(
            'run(["systemctl", "restart", ONCE_SERVICE])',
            raw,
        )
        self.assertIn(
            '"restart", ROOT_SERVICE',
            raw,
        )
        self.assertIn(
            '"--job-mode=ignore-dependencies"',
            raw,
        )

    def test_installer_requires_automatic_and_workspace_controllers_frozen(self):
        raw = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("require_frozen_auto()", raw)
        self.assertIn("require_workspace_dormant()", raw)
        self.assertIn("certify_preserved(", raw)
        self.assertIn("INSTALLED_ONCE_UNIT.unlink()", raw)
        self.assertIn('"activation_performed": False', raw)
        self.assertIn('"automatic_workflow_triggered": False', raw)

    def test_one_shot_unit_is_static_non_polling_and_sandbox_equivalent(self):
        once = ONCE_UNIT.read_text(encoding="utf-8")
        daemon = DAEMON_UNIT.read_text(encoding="utf-8")

        self.assertIn("Type=oneshot", once)
        self.assertIn("--once", once)
        self.assertNotIn("Restart=", once)
        self.assertNotIn("[Install]", once)
        self.assertIn("Type=simple", daemon)
        self.assertIn("Restart=on-failure", daemon)
        self.assertNotIn("--once", daemon)

        for directive in (
            "User=ci-reconciler",
            "Group=workspace-ci-reconciler",
            "NoNewPrivileges=yes",
            "CapabilityBoundingSet=",
            "PrivateDevices=yes",
            "ProtectSystem=strict",
            "ProtectHome=yes",
            "ProtectKernelTunables=yes",
            "ProtectKernelModules=yes",
            "ProtectKernelLogs=yes",
            "ProtectControlGroups=yes",
            "RestrictSUIDSGID=yes",
            "RestrictRealtime=yes",
            "LockPersonality=yes",
            "ProtectProc=invisible",
            "ProcSubset=pid",
            "RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6",
            "DevicePolicy=closed",
            "TasksMax=128",
            "MemoryMax=256M",
            "CPUQuota=100%",
        ):
            self.assertIn(directive, once)
            self.assertIn(directive, daemon)

    def test_one_shot_unit_pins_exact_reviewed_controller_transaction(self):
        once = ONCE_UNIT.read_text(encoding="utf-8")
        self.assertIn(
            "--expect-restart-service "
            "workspace-ci-controller@workspace-control-cpu.service",
            once,
        )
        self.assertIn(
            "--expect-enable-service "
            "workspace-ci-controller@workspace-control-cpu.service",
            once,
        )
        expected_preserved = (
            "workspace-ci-controller@padataset-cpu.service",
            "workspace-ci-controller@padataset-gpu.service",
            "workspace-ci-controller@research-engine-cpu.service",
            "workspace-ci-controller@research-engine-gpu.service",
        )
        for service in expected_preserved:
            self.assertIn(f"--expect-preserve-service {service}", once)


if __name__ == "__main__":
    unittest.main()
