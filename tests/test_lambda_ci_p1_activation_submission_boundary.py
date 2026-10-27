import importlib.util
import pathlib
import tempfile
import types
import unittest
from unittest import mock

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

    def _assert_fault_after_forward_write_rolls_back(self, fail_write_number):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            installed_root = root / "reconciler.py"
            installed_controller = root / "reconcile-controller.py"
            installed_unit = root / "workspace-ci-reconcile-controller-once.service"
            old_root = b"OLD_ROOT\n"
            old_controller = b"OLD_CONTROLLER\n"
            installed_root.write_bytes(old_root)
            installed_controller.write_bytes(old_controller)

            service_base = {
                "LoadState": "loaded",
                "ActiveState": "active",
                "SubState": "running",
                "UnitFileState": "enabled",
                "NRestarts": "0",
                "ExecMainStatus": "0",
                "MainPID": "100",
                "InvocationID": "stable",
            }
            auto_before = {
                **service_base,
                "ActiveState": "inactive",
                "SubState": "dead",
                "MainPID": "0",
                "InvocationID": "auto-frozen",
            }
            workspace_before = {
                **service_base,
                "ActiveState": "inactive",
                "SubState": "dead",
                "UnitFileState": "disabled",
                "MainPID": "0",
                "InvocationID": "",
            }
            siblings_before = {
                service: {
                    **service_base,
                    "InvocationID": f"stable-{index}",
                }
                for index, service in enumerate(module.PRESERVED)
            }
            root_before = {
                **service_base,
                "InvocationID": "root-before",
            }

            snapshots = {
                module.AUTO_CONTROLLER: auto_before,
                module.WORKSPACE_CPU: workspace_before,
                module.ROOT_SERVICE: {
                    **service_base,
                    "InvocationID": "root-after-rollback",
                },
                **siblings_before,
            }

            real_atomic_write = module.atomic_write
            write_count = 0

            def fault_after_replace(path, raw, mode):
                nonlocal write_count
                write_count += 1
                real_atomic_write(path, raw, mode)
                if write_count == fail_write_number:
                    raise OSError(
                        f"synthetic fault after forward write {fail_write_number}"
                    )

            systemctl_calls = []

            def fake_run(argv, check=True):
                systemctl_calls.append(list(argv))
                return types.SimpleNamespace(
                    returncode=0,
                    stdout="",
                    stderr="",
                )

            with (
                mock.patch.object(module, "INSTALLED_ROOT", installed_root),
                mock.patch.object(
                    module,
                    "INSTALLED_CONTROLLER",
                    installed_controller,
                ),
                mock.patch.object(module, "INSTALLED_ONCE_UNIT", installed_unit),
                mock.patch.object(module, "atomic_write", side_effect=fault_after_replace),
                mock.patch.object(module.os, "chown"),
                mock.patch.object(module, "run", side_effect=fake_run),
                mock.patch.object(module, "wait_socket"),
                mock.patch.object(
                    module,
                    "snapshot",
                    side_effect=lambda service: dict(snapshots[service]),
                ),
            ):
                with self.assertRaisesRegex(
                    module.BoundaryInstallError,
                    "rollback completed",
                ):
                    module.install_boundary(
                        src_root=b"NEW_ROOT\n",
                        src_controller=b"NEW_CONTROLLER\n",
                        src_unit=b"NEW_UNIT\n",
                        root_before=root_before,
                        auto_before=auto_before,
                        workspace_before=workspace_before,
                        siblings_before=siblings_before,
                    )

            self.assertEqual(installed_root.read_bytes(), old_root)
            self.assertEqual(installed_controller.read_bytes(), old_controller)
            self.assertFalse(installed_unit.exists())
            self.assertGreaterEqual(write_count, fail_write_number + 2)
            self.assertFalse(
                any(
                    call[:2] == ["systemctl", "start"]
                    and call[-1] in {module.AUTO_CONTROLLER, module.ONCE_SERVICE}
                    for call in systemctl_calls
                )
            )
            self.assertFalse(
                any(
                    call[:2] == ["systemctl", "restart"]
                    and call[-1] in {module.AUTO_CONTROLLER, module.ONCE_SERVICE}
                    for call in systemctl_calls
                )
            )
            self.assertIn(["systemctl", "daemon-reload"], systemctl_calls)
            self.assertIn(
                [
                    "systemctl",
                    "--job-mode=ignore-dependencies",
                    "restart",
                    module.ROOT_SERVICE,
                ],
                systemctl_calls,
            )

    def test_fault_after_first_install_write_restores_exact_prior_state(self):
        self._assert_fault_after_forward_write_rolls_back(1)

    def test_fault_after_second_install_write_restores_exact_prior_state(self):
        self._assert_fault_after_forward_write_rolls_back(2)

    def test_fault_after_third_install_write_restores_exact_prior_state(self):
        self._assert_fault_after_forward_write_rolls_back(3)

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
