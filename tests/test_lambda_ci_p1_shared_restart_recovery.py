import importlib.util
import pathlib
import types
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "scripts" / "lambda_ci_p1_bootstrap_install.py"
RECOVERY = ROOT / "scripts" / "lambda_ci_p1_restore_dependency_stopped_controllers.py"


def load(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class P1SharedRestartRecoveryTests(unittest.TestCase):
    def test_maintenance_membership_accepts_supplementary_group(self):
        module = load(BOOTSTRAP, "bootstrap_group_membership")
        maint = types.SimpleNamespace(pw_gid=111)
        group = types.SimpleNamespace(gr_gid=222)
        with mock.patch.object(
            module.os, "getgrouplist", return_value=[111, 222]
        ):
            module._validate_maintenance_identity_membership(maint, group)

    def test_maintenance_membership_rejects_missing_group(self):
        module = load(BOOTSTRAP, "bootstrap_group_missing")
        maint = types.SimpleNamespace(pw_gid=111)
        group = types.SimpleNamespace(gr_gid=222)
        with mock.patch.object(
            module.os, "getgrouplist", return_value=[111]
        ):
            with self.assertRaisesRegex(
                module.BootstrapError,
                "is not a member",
            ):
                module._validate_maintenance_identity_membership(maint, group)

    def test_dependency_stopped_non_cpu_controllers_are_started_boundedly(self):
        module = load(BOOTSTRAP, "bootstrap_dependency_restore")
        cpu = {
            "LoadState": "loaded",
            "ActiveState": "inactive",
            "SubState": "dead",
            "UnitFileState": "enabled",
            "NRestarts": "12411",
            "ExecMainStatus": "1",
        }
        before = {
            "LoadState": "loaded",
            "ActiveState": "active",
            "SubState": "running",
            "UnitFileState": "enabled",
            "NRestarts": "0",
            "ExecMainStatus": "0",
        }
        stopped = {
            "LoadState": "loaded",
            "ActiveState": "inactive",
            "SubState": "dead",
            "UnitFileState": "enabled",
            "NRestarts": "0",
            "ExecMainStatus": "0",
        }
        active = dict(before)
        preserved = {
            module.RESEARCH_CPU: cpu,
            **{service: dict(before) for service in module.REQUIRED_ACTIVE_CONTROLLERS},
        }

        snapshots = []
        for _service in module.REQUIRED_ACTIVE_CONTROLLERS:
            snapshots.extend([dict(stopped), dict(active)])

        completed = module.subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        with mock.patch.object(
            module, "service_snapshot", side_effect=snapshots
        ), mock.patch.object(
            module.time, "sleep"
        ) as sleep, mock.patch.object(
            module, "run", return_value=completed
        ) as run_call:
            module._restore_dependency_stopped_preserved_controllers(preserved)

        self.assertEqual(
            sleep.call_args_list,
            [
                mock.call(module.PRESERVED_CONTROLLER_START_STABILITY_SECONDS)
                for _ in module.REQUIRED_ACTIVE_CONTROLLERS
            ],
        )
        starts = [call.args[0] for call in run_call.call_args_list]
        self.assertEqual(
            starts,
            [["systemctl", "start", service] for service in module.REQUIRED_ACTIVE_CONTROLLERS],
        )
        self.assertFalse(any(module.RESEARCH_CPU in command for command in starts))

    def test_dependency_restore_rejects_unexpected_failed_state(self):
        module = load(BOOTSTRAP, "bootstrap_dependency_failed")
        cpu = {
            "LoadState": "loaded",
            "ActiveState": "inactive",
            "SubState": "dead",
            "UnitFileState": "enabled",
            "NRestarts": "12411",
            "ExecMainStatus": "1",
        }
        before = {
            "LoadState": "loaded",
            "ActiveState": "active",
            "SubState": "running",
            "UnitFileState": "enabled",
            "NRestarts": "0",
            "ExecMainStatus": "0",
        }
        failed = {
            "LoadState": "loaded",
            "ActiveState": "failed",
            "SubState": "failed",
            "UnitFileState": "enabled",
            "NRestarts": "0",
            "ExecMainStatus": "1",
        }
        preserved = {
            module.RESEARCH_CPU: cpu,
            **{service: dict(before) for service in module.REQUIRED_ACTIVE_CONTROLLERS},
        }
        with mock.patch.object(
            module, "service_snapshot", return_value=failed
        ), mock.patch.object(module, "run") as run_call:
            with self.assertRaisesRegex(
                module.BootstrapError,
                "not in the reviewed dependency-stop state",
            ):
                module._restore_dependency_stopped_preserved_controllers(preserved)
        run_call.assert_not_called()

    def test_rollback_restores_dependency_stopped_controllers_before_verify(self):
        raw = BOOTSTRAP.read_text(encoding="utf-8")
        restore = raw.index(
            "_restore_dependency_stopped_preserved_controllers(\n"
            '        manifest["preserved_services"]\n'
            "    )"
        )
        verify = raw.index(
            '_verify_preserved_services(manifest["preserved_services"])',
            restore,
        )
        self.assertLess(restore, verify)

    def test_forward_defers_controller_restore_until_l0_is_ready(self):
        raw = BOOTSTRAP.read_text(encoding="utf-8")
        restart = raw.index('run(["systemctl", "restart", PROVISIONER])')
        maintenance_start = raw.index(
            'run(["systemctl", "enable", "--now", MAINTENANCE_ROOT])',
            restart,
        )
        socket_wait = raw.index("wait_for_socket_ready(", maintenance_start)
        maintenance_controller_gate = raw.index(
            'if not service_active(MAINTENANCE_CONTROLLER):',
            socket_wait,
        )
        restore = raw.index(
            "_restore_dependency_stopped_preserved_controllers(\n"
            '            manifest["preserved_services"]\n'
            "        )",
            maintenance_controller_gate,
        )
        self.assertLess(restart, maintenance_start)
        self.assertLess(maintenance_start, socket_wait)
        self.assertLess(socket_wait, maintenance_controller_gate)
        self.assertLess(maintenance_controller_gate, restore)

    def test_incident_recovery_source_binding_rejects_external_copy(self):
        module = load(RECOVERY, "recovery_source_binding")
        with mock.patch.object(
            module.os, "geteuid", return_value=0
        ), mock.patch.dict(
            module.os.environ, {"SUDO_USER": "atrott"}, clear=False
        ), mock.patch.object(
            module.sys,
            "argv",
            ["copied-recovery.py", "--expected-head", "deadbeef"],
        ), mock.patch.object(
            module, "__file__", "/tmp/copied-recovery.py"
        ), mock.patch.object(module, "recover") as recover:
            with self.assertRaisesRegex(
                module.RecoveryError,
                "outside the reviewed tracked helper path",
            ):
                module.main()
        recover.assert_not_called()

    def test_execution_inspection_nonzero_fails_closed(self):
        module = load(RECOVERY, "recovery_execution_inspection_rc")
        failed = module.subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="inspection failed"
        )
        with mock.patch.object(module, "run", return_value=failed):
            with self.assertRaisesRegex(
                module.RecoveryError,
                "unable to inspect project execution units: rc=1",
            ):
                module.no_active_project_execution()

    def test_pre_recovery_inspection_failure_aborts_before_start(self):
        module = load(RECOVERY, "recovery_pre_inspection_failure")
        failed = module.subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="inspection failed"
        )
        with mock.patch.object(module, "run", return_value=failed) as run_call:
            with self.assertRaisesRegex(
                module.RecoveryError,
                "unable to inspect project execution units: rc=1",
            ):
                module.recover()

        commands = [call.args[0] for call in run_call.call_args_list]
        self.assertFalse(
            any(
                command[:2] == ["systemctl", "start"]
                for command in commands
            )
        )

    def test_post_start_inspection_failure_rejects_final_certification(self):
        module = load(RECOVERY, "recovery_post_inspection_failure")
        before = {
            "shared": {},
            "cpu": dict(module.EXPECTED_CPU),
            "targets": {
                service: dict(module.EXPECTED_TARGET)
                for service in module.TARGETS
            },
        }
        active = {
            "LoadState": "loaded",
            "ActiveState": "active",
            "SubState": "running",
            "UnitFileState": "enabled",
            "NRestarts": "0",
            "ExecMainStatus": "0",
        }
        snapshots = [dict(active) for _ in module.TARGETS]
        snapshots.append(dict(module.EXPECTED_CPU))
        snapshots.extend([dict(active) for _ in module.SHARED_REQUIRED])

        def fake_run(argv, **kwargs):
            if argv[:2] == ["systemctl", "start"]:
                return module.subprocess.CompletedProcess(
                    args=argv, returncode=0, stdout="", stderr=""
                )
            if argv[:2] == ["systemctl", "list-units"]:
                return module.subprocess.CompletedProcess(
                    args=argv,
                    returncode=1,
                    stdout="",
                    stderr="final inspection failed",
                )
            raise AssertionError(f"unexpected command: {argv!r}")

        with mock.patch.object(
            module, "validate_pre_recovery_state", return_value=before
        ), mock.patch.object(
            module, "snapshot", side_effect=snapshots
        ), mock.patch.object(
            module, "run", side_effect=fake_run
        ):
            with self.assertRaisesRegex(
                module.RecoveryError,
                "unable to inspect project execution units: rc=1",
            ):
                module.recover()

    def test_incident_recovery_mutates_only_exact_three_controller_starts(self):
        module = load(RECOVERY, "recovery_mutation_scope")
        before = {
            "shared": {},
            "cpu": dict(module.EXPECTED_CPU),
            "targets": {service: dict(module.EXPECTED_TARGET) for service in module.TARGETS},
        }
        active = {
            "LoadState": "loaded",
            "ActiveState": "active",
            "SubState": "running",
            "UnitFileState": "enabled",
            "NRestarts": "0",
            "ExecMainStatus": "0",
        }
        shared = dict(active)
        snapshots = [dict(active) for _ in module.TARGETS]
        snapshots.append(dict(module.EXPECTED_CPU))
        snapshots.extend([dict(shared) for _ in module.SHARED_REQUIRED])
        completed = module.subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )

        with mock.patch.object(
            module, "validate_pre_recovery_state", return_value=before
        ), mock.patch.object(
            module, "snapshot", side_effect=snapshots
        ), mock.patch.object(
            module, "no_active_project_execution"
        ), mock.patch.object(module, "run", return_value=completed) as run_call:
            receipt = module.recover()

        self.assertEqual(receipt["status"], "DEPENDENCY_STOPPED_CONTROLLERS_RESTORED")
        self.assertEqual(
            [call.args[0] for call in run_call.call_args_list],
            [["systemctl", "start", *module.TARGETS]],
        )
        self.assertNotIn(module.RESEARCH_CPU, run_call.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
