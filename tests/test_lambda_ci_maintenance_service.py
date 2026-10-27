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

import lambda_ci_maintenance_service as maintenance


def registry(active=True):
    return {
        "schema_version": 1,
        "projects": {
            "workspace-control": {
                "repository": "adamtrott78/workspace-control",
                "activation_state": "ACTIVE" if active else "MIGRATION_CANDIDATE_NOT_INSTALLED",
                "lanes": ["cpu"],
            }
        },
    }


def request(operation, *, quarantine=None, generation=None, request_id="01234567-89ab-4cde-8fab-0123456789ab"):
    return {
        "schema_version": 1,
        "request_id": request_id,
        "operation": operation,
        "project_id": "workspace-control",
        "lane": "cpu",
        "quarantine_receipt_id": quarantine,
        "reset_generation": generation,
    }


class MaintenanceServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.registry_path = self.root / "registry.json"
        self.state_root = self.root / "controller-state"
        self.receipts = self.root / "maintenance-receipts"
        self.registry_path.write_text(json.dumps(registry()), encoding="utf-8")

    def lane_state(self):
        path = self.state_root / "workspace-control-cpu"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def quarantine(self, receipt_id="11111111-2222-4333-8444-555555555555", scale_set_id=77):
        path = self.lane_state() / "quarantine.json"
        path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "receipt_id": receipt_id,
                    "status": "ASSIGNMENT_DIVERGENCE_QUARANTINED",
                    "project_id": "workspace-control",
                    "lane": "cpu",
                    "scale_set_name": "lambda-workspace-control",
                    "scale_set_id": scale_set_id,
                }
            ),
            encoding="utf-8",
        )
        return receipt_id, path

    def test_request_surface_rejects_arbitrary_fields_and_operations(self):
        req = request("RESTART_CONTROLLER")
        req["unit"] = "ssh.service"
        with self.assertRaisesRegex(maintenance.MaintenanceError, "keys mismatch"):
            maintenance._validate_request(req)

        req = request("RUN_SHELL")
        with self.assertRaisesRegex(maintenance.MaintenanceError, "unsupported"):
            maintenance._validate_request(req)

    def test_target_service_is_derived_from_installed_registry(self):
        target = maintenance.derive_target(
            registry(),
            "workspace-control",
            "cpu",
            controller_state_root=self.state_root,
        )
        self.assertEqual(
            target["service"],
            "workspace-ci-controller@workspace-control-cpu.service",
        )
        with self.assertRaisesRegex(maintenance.MaintenanceError, "not active"):
            maintenance.derive_target(
                registry(active=False),
                "workspace-control",
                "cpu",
                controller_state_root=self.state_root,
            )
        with self.assertRaises(maintenance.MaintenanceError):
            maintenance.derive_target(
                registry(),
                "workspace-control",
                "gpu",
                controller_state_root=self.state_root,
            )

    def test_quiesce_requires_exact_quarantine_and_local_execution_absence(self):
        qid, _ = self.quarantine()
        calls = []

        def fake_run(argv, check=True):
            calls.append(argv)
            return mock.Mock(returncode=0, stdout="", stderr="")

        with (
            mock.patch.object(maintenance, "_run", side_effect=fake_run),
            mock.patch.object(maintenance, "_service_inactive", return_value=True),
            mock.patch.object(maintenance, "_active_project_units", return_value=[]),
        ):
            receipt = maintenance.apply_request(
                request("QUIESCE_LANE_FOR_RECOVERY", quarantine=qid),
                registry_path=self.registry_path,
                controller_state_root=self.state_root,
                receipts_dir=self.receipts,
            )
        self.assertEqual(receipt["status"], "COMPLETED")
        self.assertIn(
            ["systemctl", "stop", "workspace-ci-controller@workspace-control-cpu.service"],
            calls,
        )
        self.assertTrue(receipt["result"]["local_execution_absent"])

    def test_quiesce_fails_closed_when_execution_is_still_active(self):
        qid, _ = self.quarantine()
        with (
            mock.patch.object(maintenance, "_run", return_value=mock.Mock(returncode=0, stdout="", stderr="")),
            mock.patch.object(maintenance, "_service_inactive", return_value=True),
            mock.patch.object(
                maintenance,
                "_active_project_units",
                return_value=["workspace-ci-workspace-control-deadbeef.service:active:running"],
            ),
        ):
            with self.assertRaisesRegex(maintenance.MaintenanceError, "execution still active"):
                maintenance.apply_request(
                    request("QUIESCE_LANE_FOR_RECOVERY", quarantine=qid),
                    registry_path=self.registry_path,
                    controller_state_root=self.state_root,
                    receipts_dir=self.receipts,
                )

    def test_resume_archives_quarantine_before_exact_controller_start(self):
        qid, qpath = self.quarantine(scale_set_id=91)
        generation = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
        calls = []

        def fake_run(argv, check=True):
            calls.append(argv)
            return mock.Mock(returncode=0, stdout="", stderr="")

        with (
            mock.patch.object(maintenance, "_run", side_effect=fake_run),
            mock.patch.object(maintenance, "_service_active", return_value=True),
        ):
            receipt = maintenance.apply_request(
                request(
                    "RESUME_LANE_AFTER_RESET",
                    quarantine=qid,
                    generation=generation,
                ),
                registry_path=self.registry_path,
                controller_state_root=self.state_root,
                receipts_dir=self.receipts,
            )
        pending = self.lane_state() / f"reset-pending-{generation}.json"
        self.assertFalse(qpath.exists())
        self.assertTrue(pending.exists())
        self.assertEqual(receipt["result"]["old_scale_set_id"], 91)
        self.assertIn(
            ["systemctl", "start", "workspace-ci-controller@workspace-control-cpu.service"],
            calls,
        )

    def test_mutating_request_is_replay_safe(self):
        calls = []
        with (
            mock.patch.object(
                maintenance,
                "_run",
                side_effect=lambda argv, check=True: (
                    calls.append(argv) or mock.Mock(returncode=0, stdout="", stderr="")
                ),
            ),
            mock.patch.object(maintenance, "_service_active", return_value=True),
        ):
            first = maintenance.apply_request(
                request("RESTART_CONTROLLER"),
                registry_path=self.registry_path,
                controller_state_root=self.state_root,
                receipts_dir=self.receipts,
            )
            second = maintenance.apply_request(
                request("RESTART_CONTROLLER"),
                registry_path=self.registry_path,
                controller_state_root=self.state_root,
                receipts_dir=self.receipts,
            )
        self.assertEqual(first, second)
        restarts = [
            argv
            for argv in calls
            if argv[:2] == ["systemctl", "restart"]
        ]
        self.assertEqual(len(restarts), 1)


if __name__ == "__main__":
    unittest.main()
