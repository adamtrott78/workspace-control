import importlib.util
import pathlib
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "lambda_ci_p1_restore_rollback_failed_controllers.py"


def load_module():
    spec = importlib.util.spec_from_file_location("rollback_failed_recovery", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class P1RollbackFailedControllerRecoveryTests(unittest.TestCase):
    def test_exact_failed_incident_state_is_restored_boundedly(self):
        module = load_module()
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
        completed = module.subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )

        with mock.patch.object(
            module, "validate_pre_recovery_state", return_value=before
        ), mock.patch.object(
            module, "snapshot", side_effect=snapshots
        ), mock.patch.object(
            module, "no_active_project_execution"
        ), mock.patch.object(
            module.time, "sleep"
        ) as sleep, mock.patch.object(
            module, "run", return_value=completed
        ) as run_call:
            receipt = module.recover()

        self.assertEqual(receipt["status"], "ROLLBACK_FAILED_CONTROLLERS_RESTORED")
        self.assertEqual(
            [call.args[0] for call in run_call.call_args_list],
            [["systemctl", "start", *module.TARGETS]],
        )
        self.assertNotIn(module.RESEARCH_CPU, run_call.call_args.args[0])
        sleep.assert_called_once_with(module.START_STABILITY_SECONDS)

    def test_pre_recovery_rejects_nonmatching_target_state(self):
        module = load_module()
        shared = {
            "LoadState": "loaded",
            "ActiveState": "active",
            "SubState": "running",
            "UnitFileState": "enabled",
            "NRestarts": "0",
            "ExecMainStatus": "0",
        }
        wrong = dict(module.EXPECTED_TARGET)
        wrong["ActiveState"] = "inactive"
        wrong["SubState"] = "dead"
        snapshots = [
            *[dict(shared) for _ in module.SHARED_REQUIRED],
            dict(module.EXPECTED_CPU),
            wrong,
        ]
        with mock.patch.object(
            module, "no_active_project_execution"
        ), mock.patch.object(
            module, "snapshot", side_effect=snapshots
        ):
            with self.assertRaisesRegex(
                module.RecoveryError,
                "changed from the accepted incident state",
            ):
                module.validate_pre_recovery_state()

    def test_source_binding_rejects_external_copy(self):
        module = load_module()
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
        module = load_module()
        failed = module.subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="inspection failed"
        )
        with mock.patch.object(module, "run", return_value=failed):
            with self.assertRaisesRegex(
                module.RecoveryError,
                "unable to inspect project execution units: rc=1",
            ):
                module.no_active_project_execution()


if __name__ == "__main__":
    unittest.main()
