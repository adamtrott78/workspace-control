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
        "source_attestation": {
            "repository": "adamtrott78/workspace-control",
            "actor_login": "adamtrott78",
            "comment_id": 12345,
            "command_sha256": "a" * 64,
            "maintenance_policy_generation": "workspace-ci-maintenance-p1-v1",
        },
    }


class MaintenanceServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.registry_path = self.root / "registry.json"
        self.projects_dir = self.root / "projects"
        self.projects_dir.mkdir()
        self.state_root = self.root / "controller-state"
        self.receipts = self.root / "maintenance-receipts"
        self.registry_path.write_text(json.dumps(registry()), encoding="utf-8")
        (self.projects_dir / "workspace-control.json").write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "status": "ACTIVE",
                    "project_id": "workspace-control",
                    "derived_identity": {
                        "lanes": {
                            "cpu": {
                                "scale_set_name": "lambda-workspace-control",
                                "runner_prefix": "lambda-workspace-control-",
                            }
                        }
                    },
                }
            ),
            encoding="utf-8",
        )

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
                    "observed_at": "2026-10-27T01:00:00Z",
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

    def test_source_attestation_is_exact_and_owner_bound(self):
        req = request("RESTART_CONTROLLER")
        req["source_attestation"]["actor_login"] = "someone-else"
        with self.assertRaisesRegex(
            maintenance.MaintenanceError,
            "source actor is unauthorized",
        ):
            maintenance._validate_request(req)

        req = request("RESTART_CONTROLLER")
        req["source_attestation"]["maintenance_policy_generation"] = "future-v2"
        with self.assertRaisesRegex(
            maintenance.MaintenanceError,
            "policy generation mismatch",
        ):
            maintenance._validate_request(req)

    def test_target_service_is_derived_from_installed_registry(self):
        target = maintenance.derive_target(
            registry(),
            "workspace-control",
            "cpu",
            controller_state_root=self.state_root,
            projects_dir=self.projects_dir,
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
                projects_dir=self.projects_dir,
            )
        with self.assertRaises(maintenance.MaintenanceError):
            maintenance.derive_target(
                registry(),
                "workspace-control",
                "gpu",
                controller_state_root=self.state_root,
                projects_dir=self.projects_dir,
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
                projects_dir=self.projects_dir,
                receipts_dir=self.receipts,
            )
        self.assertEqual(receipt["status"], "COMPLETED")
        self.assertEqual(
            set(receipt["identity"]["installed_policy_digests"]),
            {"registry_sha256", "manifest_sha256"},
        )
        self.assertEqual(
            receipt["identity"]["source_attestation"]["actor_login"],
            "adamtrott78",
        )
        self.assertIsNotNone(receipt["rollback"])
        self.assertEqual(
            receipt["result"]["quarantine_observed_at"],
            "2026-10-27T01:00:00Z",
        )
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
                    projects_dir=self.projects_dir,
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
                projects_dir=self.projects_dir,
                receipts_dir=self.receipts,
            )
        pending = self.lane_state() / f"reset-pending-{generation}.json"
        self.assertFalse(qpath.exists())
        self.assertTrue(pending.exists())
        pending_state = json.loads(pending.read_text(encoding="utf-8"))
        self.assertEqual(
            pending_state["status"],
            "RECOVERY_SCALESET_RESET_PENDING",
        )
        self.assertEqual(pending_state["reset_generation"], generation)
        self.assertEqual(pending_state["old_scale_set_id"], 91)
        self.assertEqual(receipt["result"]["old_scale_set_id"], 91)
        self.assertTrue(
            receipt["result"]["controller_remains_recovery_quarantined"]
        )
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
                projects_dir=self.projects_dir,
                receipts_dir=self.receipts,
            )
            second = maintenance.apply_request(
                request("RESTART_CONTROLLER"),
                registry_path=self.registry_path,
                controller_state_root=self.state_root,
                projects_dir=self.projects_dir,
                receipts_dir=self.receipts,
            )
        self.assertEqual(first, second)
        restarts = [
            argv
            for argv in calls
            if argv[:2] == ["systemctl", "restart"]
        ]
        self.assertEqual(len(restarts), 1)


    def test_resume_replay_after_quarantine_archive_does_not_restart_twice(self):
        qid, _ = self.quarantine(scale_set_id=92)
        generation = "bbbbbbbb-cccc-4ddd-8eee-ffffffffffff"
        calls = []

        def fake_run(argv, check=True):
            calls.append(argv)
            return mock.Mock(returncode=0, stdout="", stderr="")

        req = request(
            "RESUME_LANE_AFTER_RESET",
            quarantine=qid,
            generation=generation,
        )
        with (
            mock.patch.object(maintenance, "_run", side_effect=fake_run),
            mock.patch.object(maintenance, "_service_active", return_value=True),
        ):
            first = maintenance.apply_request(
                req,
                registry_path=self.registry_path,
                controller_state_root=self.state_root,
                projects_dir=self.projects_dir,
                receipts_dir=self.receipts,
            )
            second = maintenance.apply_request(
                req,
                registry_path=self.registry_path,
                controller_state_root=self.state_root,
                projects_dir=self.projects_dir,
                receipts_dir=self.receipts,
            )

        self.assertEqual(first, second)
        starts = [
            argv
            for argv in calls
            if argv[:2] == ["systemctl", "start"]
        ]
        self.assertEqual(len(starts), 1)


    def test_diagnose_reports_reset_pending_and_ready_state(self):
        lane = self.lane_state()
        generation = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
        pending = lane / f"reset-pending-{generation}.json"
        pending.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "receipt_id": "11111111-2222-4333-8444-555555555555",
                    "status": "RECOVERY_SCALESET_RESET_PENDING",
                    "project_id": "workspace-control",
                    "lane": "cpu",
                    "scale_set_name": "lambda-workspace-control",
                    "old_scale_set_id": 77,
                    "reset_generation": generation,
                }
            ),
            encoding="utf-8",
        )
        ready = lane / "ready-for-single-retry.json"
        ready.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "receipt_id": "11111111-2222-4333-8444-555555555555",
                    "status": "READY_FOR_SINGLE_RETRY",
                    "project_id": "workspace-control",
                    "lane": "cpu",
                    "scale_set_name": "lambda-workspace-control",
                    "old_scale_set_id": 77,
                    "new_scale_set_id": 88,
                    "reset_generation": generation,
                    "automatic_workflow_triggered": False,
                }
            ),
            encoding="utf-8",
        )
        with (
            mock.patch.object(maintenance, "_service_active", return_value=True),
            mock.patch.object(maintenance, "_active_project_units", return_value=[]),
        ):
            result = maintenance.apply_request(
                request("DIAGNOSE_LANE"),
                registry_path=self.registry_path,
                controller_state_root=self.state_root,
                projects_dir=self.projects_dir,
                receipts_dir=self.receipts,
            )
        self.assertEqual(len(result["reset_pending"]), 1)
        self.assertEqual(
            result["ready_for_single_retry"]["new_scale_set_id"],
            88,
        )

    def test_requiesce_from_ready_state_restores_reset_pending(self):
        lane = self.lane_state()
        generation = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
        qid = "11111111-2222-4333-8444-555555555555"
        ready = lane / "ready-for-single-retry.json"
        ready.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "receipt_id": qid,
                    "status": "READY_FOR_SINGLE_RETRY",
                    "project_id": "workspace-control",
                    "lane": "cpu",
                    "scale_set_name": "lambda-workspace-control",
                    "old_scale_set_id": 77,
                    "new_scale_set_id": 88,
                    "reset_generation": generation,
                    "automatic_workflow_triggered": False,
                }
            ),
            encoding="utf-8",
        )
        with (
            mock.patch.object(
                maintenance,
                "_run",
                return_value=mock.Mock(returncode=0, stdout="", stderr=""),
            ),
            mock.patch.object(maintenance, "_service_inactive", return_value=True),
            mock.patch.object(maintenance, "_active_project_units", return_value=[]),
        ):
            result = maintenance.apply_request(
                request(
                    "QUIESCE_LANE_FOR_RECOVERY",
                    quarantine=qid,
                    generation=generation,
                    request_id="22222222-3333-4444-8555-666666666666",
                ),
                registry_path=self.registry_path,
                controller_state_root=self.state_root,
                projects_dir=self.projects_dir,
                receipts_dir=self.receipts,
            )
        pending = lane / f"reset-pending-{generation}.json"
        self.assertFalse(ready.exists())
        self.assertTrue(pending.exists())
        state = json.loads(pending.read_text(encoding="utf-8"))
        self.assertEqual(state["status"], "RECOVERY_SCALESET_RESET_PENDING")
        self.assertEqual(state["old_scale_set_id"], 77)
        self.assertEqual(
            result["result"]["quarantine_scale_set_id"],
            88,
        )


    def test_new_reset_archives_prior_completed_recovery_receipt(self):
        qid, _ = self.quarantine(scale_set_id=93)
        lane = self.lane_state()
        prior_generation = "cccccccc-dddd-4eee-8fff-aaaaaaaaaaaa"
        ready = lane / "ready-for-single-retry.json"
        prior = {
            "schema_version": 1,
            "receipt_id": "99999999-8888-4777-8666-555555555555",
            "status": "RECOVERY_RETRY_COMPLETED",
            "project_id": "workspace-control",
            "lane": "cpu",
            "scale_set_name": "lambda-workspace-control",
            "old_scale_set_id": 70,
            "new_scale_set_id": 80,
            "reset_generation": prior_generation,
            "automatic_workflow_triggered": False,
            "job_id": "prior-job",
            "result": "Succeeded",
        }
        ready.write_text(json.dumps(prior), encoding="utf-8")
        generation = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"

        with (
            mock.patch.object(
                maintenance,
                "_run",
                return_value=mock.Mock(returncode=0, stdout="", stderr=""),
            ),
            mock.patch.object(maintenance, "_service_active", return_value=True),
        ):
            receipt = maintenance.apply_request(
                request(
                    "RESUME_LANE_AFTER_RESET",
                    quarantine=qid,
                    generation=generation,
                    request_id="33333333-4444-4555-8666-777777777777",
                ),
                registry_path=self.registry_path,
                controller_state_root=self.state_root,
                projects_dir=self.projects_dir,
                receipts_dir=self.receipts,
            )

        history = lane / f"recovery-history-{prior_generation}.json"
        self.assertFalse(ready.exists())
        self.assertTrue(history.exists())
        self.assertEqual(
            json.loads(history.read_text(encoding="utf-8")),
            prior,
        )
        self.assertEqual(
            receipt["result"]["archived_previous_recovery"],
            str(history),
        )

    def test_new_reset_rejects_nonterminal_prior_recovery_generation(self):
        qid, _ = self.quarantine(scale_set_id=94)
        lane = self.lane_state()
        ready = lane / "ready-for-single-retry.json"
        ready.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "receipt_id": "99999999-8888-4777-8666-555555555555",
                    "status": "RECOVERY_RETRY_ACQUIRED",
                    "project_id": "workspace-control",
                    "lane": "cpu",
                    "scale_set_name": "lambda-workspace-control",
                    "old_scale_set_id": 70,
                    "new_scale_set_id": 80,
                    "reset_generation": "cccccccc-dddd-4eee-8fff-aaaaaaaaaaaa",
                    "automatic_workflow_triggered": False,
                    "job_id": "prior-job",
                }
            ),
            encoding="utf-8",
        )
        calls = []

        def fake_run(argv, check=True):
            calls.append(argv)
            return mock.Mock(returncode=0, stdout="", stderr="")

        with (
            mock.patch.object(maintenance, "_run", side_effect=fake_run),
            mock.patch.object(maintenance, "_service_active", return_value=True),
        ):
            with self.assertRaisesRegex(
                maintenance.MaintenanceError,
                "previous recovery generation is not terminal",
            ):
                maintenance.apply_request(
                    request(
                        "RESUME_LANE_AFTER_RESET",
                        quarantine=qid,
                        generation="aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
                        request_id="44444444-5555-4666-8777-888888888888",
                    ),
                    registry_path=self.registry_path,
                    controller_state_root=self.state_root,
                    projects_dir=self.projects_dir,
                    receipts_dir=self.receipts,
                )
        starts = [argv for argv in calls if argv[:2] == ["systemctl", "start"]]
        self.assertEqual(starts, [])


if __name__ == "__main__":
    unittest.main()
