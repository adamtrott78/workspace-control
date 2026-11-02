import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
LIVE_UPDATE = SCRIPTS / "lambda_ci_maintenance_controller_live_update_v1.py"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import lambda_ci_maintenance_controller as controller


FAKE_POLICY_DIGESTS = {
    "registry_sha256": "a" * 64,
    "manifest_sha256": "b" * 64,
}


class FakeNoReplacementRuns:
    def get_json(self, _path):
        return {"workflow_runs": []}


ZERO_STATS = {
    "totalAvailableJobs": 0,
    "totalAcquiredJobs": 0,
    "totalAssignedJobs": 0,
    "totalRunningJobs": 0,
    "totalRegisteredRunners": 0,
    "totalBusyRunners": 0,
    "totalIdleRunners": 0,
}


def reset_command():
    return {
        "action": "reset-stale",
        "project_id": "workspace-control",
        "lane": "cpu",
        "quarantine_receipt_id": "11111111-2222-4333-8444-555555555555",
    }


class MaintenanceControllerTests(unittest.TestCase):
    def test_command_grammar_is_exact_and_owner_surface_is_narrow(self):
        self.assertEqual(
            controller.parse_command(
                "/workspace-ci-maintain diagnose workspace-control cpu"
            ),
            {
                "action": "diagnose",
                "project_id": "workspace-control",
                "lane": "cpu",
                "quarantine_receipt_id": None,
            },
        )
        self.assertEqual(
            controller.parse_command(
                "/workspace-ci-maintain reset-stale workspace-control cpu "
                "11111111-2222-4333-8444-555555555555"
            )["action"],
            "reset-stale",
        )
        for body in (
            "/workspace-ci-maintain diagnose workspace-control cpu extra",
            "/workspace-ci-maintain shell workspace-control cpu",
            "/workspace-ci-maintain restart workspace-control gpu --now",
            "/workspace-ci-maintain diagnose workspace-control CPU",
            "/workspace-ci-maintain diagnose ../root cpu",
        ):
            with self.assertRaises(controller.MaintenanceControllerError):
                controller.parse_command(body)
        self.assertIsNone(
            controller.parse_command(
                "/workspace-ci-maintain diagnose workspace-control cpu\necho pwned"
            )
        )
        self.assertIsNone(controller.parse_command("ordinary issue discussion"))

    def test_reset_recovery_identity_differs_from_initial_quiesce(self):
        command = reset_command()
        initial = controller.maintenance_request_id(
            123, command, "QUIESCE_LANE_FOR_RECOVERY"
        )
        generation = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
        recovery = controller.maintenance_request_id(
            123,
            command,
            "QUIESCE_LANE_FOR_RECOVERY",
            generation,
        )
        self.assertNotEqual(initial, recovery)


    def test_root_request_only_carries_recovery_ids_for_recovery_verbs(self):
        command = reset_command()
        diagnose = controller.build_root_request(
            comment_id=123,
            command=command,
            operation="DIAGNOSE_LANE",
        )
        self.assertIsNone(diagnose["quarantine_receipt_id"])
        self.assertIsNone(diagnose["reset_generation"])
        self.assertEqual(
            diagnose["source_attestation"],
            {
                "repository": "adamtrott78/workspace-control",
                "actor_login": "adamtrott78",
                "comment_id": 123,
                "command_sha256": controller._sha256(command),
                "maintenance_policy_generation":
                    "workspace-ci-maintenance-p1-v1",
            },
        )

        generation = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
        requiesce = controller.build_root_request(
            comment_id=123,
            command=command,
            operation="QUIESCE_LANE_FOR_RECOVERY",
            reset_generation=generation,
        )
        self.assertEqual(
            requiesce["quarantine_receipt_id"],
            command["quarantine_receipt_id"],
        )
        self.assertEqual(requiesce["reset_generation"], generation)

    def test_live_update_is_single_file_transactional_and_fail_closed(self):
        text = LIVE_UPDATE.read_text(encoding="utf-8")
        compile(text, str(LIVE_UPDATE), "exec")

        self.assertIn(
            'EXPECTED_OLD_GIT_BLOB = "4b5ec97754c83e4b01103dea9c2f84112b3d6110"',
            text,
        )
        self.assertIn(
            'EXPECTED_CANDIDATE_GIT_BLOB = "f994992cb3e4713c1e0a165c18de459fa44dac74"',
            text,
        )
        self.assertIn(
            '"/opt/workspace-ci/maintenance-controller/lambda_ci_maintenance_controller.py"',
            text,
        )
        self.assertIn('SERVICE = "workspace-ci-maintenance-controller.service"', text)
        self.assertIn('"status": "ROLLED_BACK"', text)
        self.assertIn("maintenance controller PID changed during stability window", text)
        self.assertIn('f"safe.directory={repo_hint}"', text)
        self.assertIn('f"safe.directory={repo}"', text)
        self.assertNotIn("git config --global", text)

        # The hotfix is not a migration transaction and must not operate on
        # project controllers, v3 services, scale sets, credentials, or
        # quarantine/retry state.
        self.assertNotIn("workspace-ci-controller@", text)
        self.assertNotIn("workspace-ci-v3-", text)
        self.assertNotIn("--scale-set-maintenance", text)
        self.assertNotIn("quarantine.json", text)
        self.assertNotIn("ready-for-single-retry.json", text)
        self.assertNotIn("github-read-token", text)
        self.assertNotIn("runner-token", text)

    def test_github_time_normalizer_truncates_go_rfc3339_nanoseconds(self):
        self.assertEqual(
            controller._normalize_github_time(
                "2026-11-01T22:20:58.365802851Z"
            ),
            "2026-11-01T22:20:58.365802+00:00",
        )
        self.assertEqual(
            controller._normalize_github_time(
                "2026-11-01T22:20:58.123456789-05:00"
            ),
            "2026-11-01T22:20:58.123456-05:00",
        )

    def test_github_time_parser_accepts_go_rfc3339_nanoseconds(self):
        observed = controller._parse_github_time(
            "2026-11-01T22:20:58.365802851Z",
            "quarantine observed_at",
        )
        self.assertEqual(
            observed.isoformat(),
            "2026-11-01T22:20:58.365802+00:00",
        )

        offset = controller._parse_github_time(
            "2026-11-01T22:20:58.123456789-05:00",
            "quarantine observed_at",
        )
        self.assertEqual(
            offset.isoformat(),
            "2026-11-01T22:20:58.123456-05:00",
        )

        with self.assertRaisesRegex(
            controller.MaintenanceControllerError,
            "timestamp is invalid",
        ):
            controller._parse_github_time(
                "2026-11-01T22:20:58.not-a-fractionZ",
                "quarantine observed_at",
            )

    def test_replacement_run_gate_blocks_only_live_runner_demand(self):
        command = reset_command()
        cutoff = "2026-10-27T01:00:00Z"

        class Client:
            def __init__(self, runs, jobs=None):
                self.runs = runs
                self.jobs = jobs or {}

            def get_json(self, path):
                if "/actions/runs/" in path and "/jobs" in path:
                    run_id = int(path.split("/actions/runs/", 1)[1].split("/", 1)[0])
                    return {"jobs": self.jobs.get(run_id, [])}
                return {"workflow_runs": self.runs}

        controller.assert_no_replacement_runs(
            Client(
                [
                    {
                        "id": 1,
                        "status": "in_progress",
                        "created_at": "2026-10-27T00:59:00Z",
                        "updated_at": "2026-10-27T00:59:30Z",
                        "run_attempt": 1,
                    }
                ]
            ),
            command,
            cutoff,
        )

        # A maintenance comment triggers the same issue_comment workflow, but
        # its job-level condition is false and GitHub finalizes it as skipped.
        # That self-trigger must not block reset-stale.
        controller.assert_no_replacement_runs(
            Client(
                [
                    {
                        "id": 2,
                        "status": "in_progress",
                        "created_at": "2026-10-27T01:00:01Z",
                        "updated_at": "2026-10-27T01:00:01Z",
                        "run_attempt": 1,
                    }
                ],
                {
                    2: [
                        {
                            "name": (
                                "wc-admission-v1|workload=control-validation|"
                                "pr=${{ github.event.issue.number }}|"
                                "request=${{ github.event.comment.body }}"
                            ),
                            "status": "completed",
                            "conclusion": "skipped",
                        }
                    ]
                },
            ),
            command,
            cutoff,
        )

        with self.assertRaisesRegex(
            controller.MaintenanceControllerError,
            "replacement pilot workflow run",
        ):
            controller.assert_no_replacement_runs(
                Client(
                    [
                        {
                            "id": 3,
                            "status": "queued",
                            "created_at": "2026-10-27T01:00:01Z",
                            "updated_at": "2026-10-27T01:00:01Z",
                            "run_attempt": 1,
                        }
                    ],
                    {
                        3: [
                            {
                                "name": (
                                    "wc-admission-v1|workload=control-validation|"
                                    "pr=590|request=/workspace-control-validate "
                                    "cbc71b51b28c96b7b08b92a5e8e17b8566803d73"
                                ),
                                "status": "queued",
                                "conclusion": None,
                            }
                        ]
                    },
                ),
                command,
                cutoff,
            )

        with self.assertRaisesRegex(
            controller.MaintenanceControllerError,
            "replacement pilot workflow run",
        ):
            controller.assert_no_replacement_runs(
                Client(
                    [
                        {
                            "id": 4,
                            "status": "in_progress",
                            "created_at": "2026-10-27T00:58:00Z",
                            "updated_at": "2026-10-27T01:00:05Z",
                            "run_attempt": 2,
                        }
                    ],
                    {
                        4: [
                            {
                                "name": (
                                    "wc-admission-v1|workload=control-validation|"
                                    "pr=590|request=/workspace-control-validate "
                                    "cbc71b51b28c96b7b08b92a5e8e17b8566803d73"
                                ),
                                "status": "in_progress",
                                "conclusion": None,
                            }
                        ]
                    },
                ),
                command,
                cutoff,
            )

    def test_replacement_run_gate_fails_closed_when_jobs_cannot_be_classified(self):
        command = reset_command()

        class Client:
            def get_json(self, path):
                if "/actions/runs/" in path and "/jobs" in path:
                    return {"jobs": []}
                return {
                    "workflow_runs": [
                        {
                            "id": 5,
                            "status": "in_progress",
                            "created_at": "2026-10-27T01:00:01Z",
                            "updated_at": "2026-10-27T01:00:01Z",
                            "run_attempt": 1,
                        }
                    ]
                }

        with self.assertRaisesRegex(
            controller.MaintenanceControllerError,
            "no classifiable job",
        ):
            controller.assert_no_replacement_runs(
                Client(),
                command,
                "2026-10-27T01:00:00Z",
            )

    def test_stale_busy_ghost_requires_exact_shape_and_quarantine_evidence(self):
        ghost = {
            "totalAvailableJobs": 0,
            "totalAcquiredJobs": 0,
            "totalAssignedJobs": 1,
            "totalRunningJobs": 0,
            "totalRegisteredRunners": 0,
            "totalBusyRunners": 1,
            "totalIdleRunners": 0,
        }
        self.assertTrue(controller._stale_busy_ghost_shape(ghost))
        for key in ghost:
            bad = dict(ghost)
            bad[key] = 2 if key in {"totalAssignedJobs", "totalBusyRunners"} else 1
            self.assertFalse(controller._stale_busy_ghost_shape(bad), key)

        command = reset_command()
        root_diag = {
            "status": "COMPLETED",
            "result": {
                "service_active": False,
                "active_project_units": [],
                "quarantine": {
                    "receipt_id": command["quarantine_receipt_id"],
                    "status": "ASSIGNMENT_DIVERGENCE_QUARANTINED",
                    "project_id": "workspace-control",
                    "lane": "cpu",
                    "reconstructable_jobs": 0,
                    "active_count": 0,
                    "pending_count": 0,
                },
            },
        }
        controller.require_stale_quarantine_delete_evidence(root_diag, command)

        for key in (
            "receipt_id",
            "status",
            "project_id",
            "lane",
            "reconstructable_jobs",
            "active_count",
            "pending_count",
        ):
            bad = json.loads(json.dumps(root_diag))
            current = bad["result"]["quarantine"][key]
            bad["result"]["quarantine"][key] = (
                "wrong" if isinstance(current, str) else current + 1
            )
            with self.assertRaises(controller.MaintenanceControllerError):
                controller.require_stale_quarantine_delete_evidence(bad, command)

    def test_stale_busy_delete_requires_no_nonterminal_pilot_demand(self):
        class Client:
            def __init__(self, runs, jobs):
                self.runs = runs
                self.jobs = jobs

            def get_json(self, path):
                if "/actions/runs/" in path and "/jobs" in path:
                    run_id = int(path.split("/actions/runs/", 1)[1].split("/", 1)[0])
                    return {"jobs": self.jobs.get(run_id, [])}
                return {"workflow_runs": self.runs}

        completed = {
            "id": 10,
            "status": "completed",
            "created_at": "2026-11-02T02:40:02Z",
            "updated_at": "2026-11-02T06:33:34Z",
            "run_attempt": 1,
        }
        controller.assert_no_nonterminal_pilot_runs(Client([completed], {}))

        maintenance_self_trigger = {
            "id": 11,
            "status": "in_progress",
            "created_at": "2026-11-02T06:34:00Z",
            "updated_at": "2026-11-02T06:34:00Z",
            "run_attempt": 1,
        }
        controller.assert_no_nonterminal_pilot_runs(
            Client(
                [maintenance_self_trigger],
                {
                    11: [
                        {
                            "name": (
                                "wc-admission-v1|workload=control-validation|"
                                "pr=${{ github.event.issue.number }}|"
                                "request=${{ github.event.comment.body }}"
                            ),
                            "status": "completed",
                            "conclusion": "skipped",
                        }
                    ]
                },
            )
        )

        live = {
            "id": 12,
            "status": "queued",
            "created_at": "2026-11-02T06:34:00Z",
            "updated_at": "2026-11-02T06:34:00Z",
            "run_attempt": 1,
        }
        with self.assertRaisesRegex(
            controller.MaintenanceControllerError,
            "non-terminal runner demand",
        ):
            controller.assert_no_nonterminal_pilot_runs(
                Client(
                    [live],
                    {
                        12: [
                            {
                                "name": (
                                    "wc-admission-v1|workload=control-validation|"
                                    "pr=590|request=/workspace-control-validate "
                                    "cbc71b51b28c96b7b08b92a5e8e17b8566803d73"
                                ),
                                "status": "queued",
                                "conclusion": None,
                            }
                        ]
                    },
                )
            )

    def test_p1_reset_is_limited_to_workspace_control_cpu(self):
        command = dict(reset_command())
        command["project_id"] = "research-engine"
        with self.assertRaisesRegex(
            controller.MaintenanceControllerError,
            "limited to workspace-control/cpu",
        ):
            controller.assert_no_replacement_runs(
                FakeNoReplacementRuns(),
                command,
                "2026-10-27T01:00:00Z",
            )

    def test_load_controller_env_derives_path_and_overrides_runner_credential(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            env_path = root / "workspace-control-cpu.env"
            env_path.write_text(
                "\n".join(
                    [
                        "WORKSPACE_CI_ADMISSION_V2_ENABLED=YES",
                        "WORKSPACE_CI_GITHUB_URL=https://github.com/adamtrott78/workspace-control",
                        "WORKSPACE_CI_LANE=cpu",
                        "WORKSPACE_CI_PAT_FILE=/var/lib/workspace-ci/controller/github-token",
                        "WORKSPACE_CI_PROJECT_ID=workspace-control",
                        "WORKSPACE_CI_PROVISIONER_SOCKET=/run/workspace-ci/provisioner.sock",
                        "WORKSPACE_CI_RUNNER_PREFIX=lambda-workspace-control-",
                        "WORKSPACE_CI_SCALESET_NAME=lambda-workspace-control",
                        "WORKSPACE_CI_CONTROLLER_STATE_ROOT=/var/lib/workspace-ci/controller/state",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            token = pathlib.Path("/var/lib/workspace-ci/maintenance-controller/runner-token")
            values = controller.load_controller_env(
                root,
                "workspace-control",
                "cpu",
                runner_token_file=token,
            )
            self.assertEqual(values["WORKSPACE_CI_PAT_FILE"], str(token))
            self.assertEqual(
                values["WORKSPACE_CI_SCALESET_NAME"], "lambda-workspace-control"
            )
            with self.assertRaises(controller.MaintenanceControllerError):
                controller.load_controller_env(
                    root,
                    "workspace-control",
                    "gpu",
                    runner_token_file=token,
                )

    def test_reset_requires_fresh_scale_set_and_two_zero_observations(self):
        command = reset_command()
        root_calls = []
        helper_calls = []
        sleeps = []

        generation_seen = {"value": None}
        diag_count = {"value": 0}

        def root(_socket, *, comment_id, command, operation, reset_generation=None):
            root_calls.append((operation, reset_generation))
            if operation == "QUIESCE_LANE_FOR_RECOVERY":
                return {
                    "status": "COMPLETED",
                    "identity": {
                        "installed_policy_digests": dict(FAKE_POLICY_DIGESTS),
                    },
                    "result": {
                        "local_execution_absent": True,
                        "quarantine_scale_set_id": 77,
                        "quarantine_observed_at": "2026-10-27T01:00:00Z",
                    },
                }
            if operation == "RESUME_LANE_AFTER_RESET":
                generation_seen["value"] = reset_generation
                return {"status": "COMPLETED", "result": {"service_active": True}}
            if operation == "DIAGNOSE_LANE":
                diag_count["value"] += 1
                response = {
                    "status": "PASS",
                    "service_active": True,
                    "active_project_units": [],
                    "installed_policy_digests": dict(FAKE_POLICY_DIGESTS),
                    "ready_for_single_retry": None,
                }
                if diag_count["value"] >= 3:
                    response["ready_for_single_retry"] = {
                        "status": "READY_FOR_SINGLE_RETRY",
                        "receipt_id": command["quarantine_receipt_id"],
                        "reset_generation": generation_seen["value"],
                        "old_scale_set_id": 77,
                        "new_scale_set_id": 88,
                        "automatic_workflow_triggered": False,
                    }
                return response
            raise AssertionError(operation)

        def helper(_binary, _env, operation, expected):
            helper_calls.append((operation, expected))
            if operation == "INSPECT" and expected == 77:
                return {
                    "status": "PRESENT",
                    "scale_set_id": 77,
                    "scale_set_name": "lambda-workspace-control",
                    "statistics": dict(ZERO_STATS),
                }
            if operation == "DELETE" and expected == 77:
                return {
                    "status": "DELETED",
                    "scale_set_id": 77,
                    "scale_set_name": "lambda-workspace-control",
                    "statistics": dict(ZERO_STATS),
                }
            if operation == "INSPECT" and expected in {0, 88}:
                return {
                    "status": "PRESENT",
                    "scale_set_id": 88,
                    "scale_set_name": "lambda-workspace-control",
                    "statistics": dict(ZERO_STATS),
                }
            raise AssertionError((operation, expected))

        with (
            mock.patch.object(controller, "submit_root", side_effect=root),
            mock.patch.object(
                controller,
                "load_controller_env",
                return_value={"WORKSPACE_CI_SCALESET_NAME": "lambda-workspace-control"},
            ),
            mock.patch.object(controller, "invoke_scale_set_helper", side_effect=helper),
        ):
            result = controller.execute_reset(
                comment_id=123,
                command=command,
                root_socket=pathlib.Path("/run/workspace-ci/maintenance.sock"),
                controller_binary=pathlib.Path("/opt/workspace-ci/controller/lambda-ci-controller"),
                controllers_dir=pathlib.Path("/etc/workspace-ci/controllers"),
                runner_token_file=pathlib.Path("/run/test-token"),
                sleep_fn=sleeps.append,
                github_client=FakeNoReplacementRuns(),
            )

        self.assertEqual(result["status"], "READY_FOR_SINGLE_RETRY")
        self.assertEqual(result["old_scale_set_id"], 77)
        self.assertEqual(result["new_scale_set_id"], 88)
        self.assertFalse(result["automatic_workflow_triggered"])
        self.assertEqual(
            result["installed_policy_digests"],
            FAKE_POLICY_DIGESTS,
        )
        self.assertEqual(
            result["quarantine_receipt_id"],
            command["quarantine_receipt_id"],
        )
        self.assertEqual(result["source_comment_id"], 123)
        self.assertEqual(
            result["controller_ready_receipt"]["status"],
            "READY_FOR_SINGLE_RETRY",
        )
        self.assertEqual(
            [op for op, _ in root_calls],
            [
                "QUIESCE_LANE_FOR_RECOVERY",
                "RESUME_LANE_AFTER_RESET",
                "DIAGNOSE_LANE",
                "DIAGNOSE_LANE",
                "DIAGNOSE_LANE",
            ],
        )
        self.assertEqual(
            helper_calls,
            [
                ("INSPECT", 77),
                ("DELETE", 77),
                ("INSPECT", 0),
                ("INSPECT", 88),
                ("INSPECT", 88),
            ],
        )
        self.assertIn(controller.ZERO_SETTLE_SECONDS, sleeps)

    def test_reset_failure_after_resume_requiesces_lane(self):
        command = reset_command()
        root_calls = []
        inspect_count = 0

        def root(_socket, *, comment_id, command, operation, reset_generation=None):
            root_calls.append((operation, reset_generation))
            if operation == "QUIESCE_LANE_FOR_RECOVERY":
                return {
                    "status": "COMPLETED",
                    "identity": {
                        "installed_policy_digests": dict(FAKE_POLICY_DIGESTS),
                    },
                    "result": {
                        "local_execution_absent": True,
                        "quarantine_scale_set_id": 77,
                        "quarantine_observed_at": "2026-10-27T01:00:00Z",
                    },
                }
            if operation == "RESUME_LANE_AFTER_RESET":
                return {"status": "COMPLETED", "result": {"service_active": True}}
            if operation == "DIAGNOSE_LANE":
                return {
                    "status": "PASS",
                    "service_active": True,
                    "active_project_units": [],
                    "installed_policy_digests": dict(FAKE_POLICY_DIGESTS),
                }
            raise AssertionError(operation)

        def helper(_binary, _env, operation, expected):
            nonlocal inspect_count
            if operation == "DELETE":
                return {"status": "DELETED", "scale_set_id": 77, "statistics": dict(ZERO_STATS)}
            inspect_count += 1
            if expected == 77:
                return {"status": "PRESENT", "scale_set_id": 77, "statistics": dict(ZERO_STATS)}
            stats = dict(ZERO_STATS)
            if inspect_count >= 3:
                stats["totalAssignedJobs"] = 1
            return {"status": "PRESENT", "scale_set_id": 88, "statistics": stats}

        with (
            mock.patch.object(controller, "submit_root", side_effect=root),
            mock.patch.object(controller, "load_controller_env", return_value={}),
            mock.patch.object(controller, "invoke_scale_set_helper", side_effect=helper),
        ):
            with self.assertRaisesRegex(
                controller.MaintenanceControllerError,
                "second zero-state observation failed",
            ):
                controller.execute_reset(
                    comment_id=321,
                    command=command,
                    root_socket=pathlib.Path("/run/workspace-ci/maintenance.sock"),
                    controller_binary=pathlib.Path("/opt/workspace-ci/controller/lambda-ci-controller"),
                    controllers_dir=pathlib.Path("/etc/workspace-ci/controllers"),
                    runner_token_file=pathlib.Path("/run/test-token"),
                    sleep_fn=lambda _seconds: None,
                    github_client=FakeNoReplacementRuns(),
                )

        self.assertEqual(root_calls[-1][0], "QUIESCE_LANE_FOR_RECOVERY")
        self.assertIsNotNone(root_calls[-1][1])

    def test_processed_comment_replay_never_repeats_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            state = pathlib.Path(td)
            comment = {
                "id": 999,
                "user": {"login": controller.OWNER_LOGIN},
                "author_association": "OWNER",
                "body": "/workspace-ci-maintain restart workspace-control cpu",
            }
            calls = []

            def root(*args, **kwargs):
                calls.append(kwargs["operation"])
                return {
                    "status": "COMPLETED",
                    "result": {"service_active": True},
                }

            with mock.patch.object(controller, "submit_root", side_effect=root):
                first = controller.process_comment(
                    comment,
                    state_dir=state,
                    root_socket=pathlib.Path("/run/test.sock"),
                    controller_binary=pathlib.Path("/bin/false"),
                    controllers_dir=pathlib.Path("/etc/workspace-ci/controllers"),
                    runner_token_file=pathlib.Path("/run/test-token"),
                )
                second = controller.process_comment(
                    comment,
                    state_dir=state,
                    root_socket=pathlib.Path("/run/test.sock"),
                    controller_binary=pathlib.Path("/bin/false"),
                    controllers_dir=pathlib.Path("/etc/workspace-ci/controllers"),
                    runner_token_file=pathlib.Path("/run/test-token"),
                )
            self.assertEqual(first, second)
            self.assertEqual(calls, ["RESTART_CONTROLLER"])

    def test_non_owner_comment_is_ignored(self):
        with tempfile.TemporaryDirectory() as td:
            comment = {
                "id": 1001,
                "user": {"login": "someone-else"},
                "author_association": "CONTRIBUTOR",
                "body": "/workspace-ci-maintain restart workspace-control cpu",
            }
            self.assertIsNone(
                controller.process_comment(
                    comment,
                    state_dir=pathlib.Path(td),
                    root_socket=pathlib.Path("/run/test.sock"),
                    controller_binary=pathlib.Path("/bin/false"),
                    controllers_dir=pathlib.Path("/etc/workspace-ci/controllers"),
                    runner_token_file=pathlib.Path("/run/test-token"),
                )
            )


    def test_first_poll_establishes_watermark_without_executing_old_commands(self):
        with tempfile.TemporaryDirectory() as td:
            state = pathlib.Path(td)
            token = state / "token"
            token.write_text("test-token", encoding="utf-8")
            token.chmod(0o600)

            class FakeGitHub:
                def __init__(self, _token):
                    pass

                def get_json(self, path):
                    if path.endswith("/issues/42"):
                        return {"state": "open"}
                    if "/issues/42/comments?" in path:
                        return [
                            {
                                "id": 10,
                                "updated_at": "2026-10-27T01:00:00Z",
                                "user": {"login": controller.OWNER_LOGIN},
                                "author_association": "OWNER",
                                "body": "/workspace-ci-maintain restart workspace-control cpu",
                            }
                        ]
                    raise AssertionError(path)

            with (
                mock.patch.object(controller, "GitHubClient", FakeGitHub),
                mock.patch.object(controller, "process_comment") as process,
            ):
                result = controller.run_once(
                    token_file=token,
                    issue_number=42,
                    state_dir=state,
                    root_socket=pathlib.Path("/run/test.sock"),
                    controller_binary=pathlib.Path("/bin/false"),
                    controllers_dir=pathlib.Path("/etc/workspace-ci/controllers"),
                    runner_token_file=pathlib.Path("/run/test-token"),
                )
            self.assertEqual(result["status"], "INITIALIZED_NO_COMMANDS_EXECUTED")
            self.assertEqual(result["watermark_comment_id"], 10)
            process.assert_not_called()

    def test_subsequent_poll_executes_only_new_comment_ids(self):
        with tempfile.TemporaryDirectory() as td:
            state = pathlib.Path(td)
            token = state / "token"
            token.write_text("test-token", encoding="utf-8")
            token.chmod(0o600)
            (state / "cursor.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "initialized_at": "2026-10-27T01:00:00Z",
                        "last_seen_comment_id": 10,
                        "last_seen_updated_at": "2026-10-27T01:00:00Z",
                    }
                ),
                encoding="utf-8",
            )

            class FakeGitHub:
                def __init__(self, _token):
                    pass

                def get_json(self, path):
                    if path.endswith("/issues/42"):
                        return {"state": "open"}
                    if "/issues/42/comments?" in path:
                        return [
                            {
                                "id": 10,
                                "updated_at": "2026-10-27T01:00:00Z",
                                "user": {"login": controller.OWNER_LOGIN},
                                "author_association": "OWNER",
                                "body": "/workspace-ci-maintain restart workspace-control cpu",
                            },
                            {
                                "id": 11,
                                "updated_at": "2026-10-27T01:01:00Z",
                                "user": {"login": controller.OWNER_LOGIN},
                                "author_association": "OWNER",
                                "body": "/workspace-ci-maintain restart workspace-control cpu",
                            },
                        ]
                    raise AssertionError(path)

            calls = []

            def fake_process(comment, **_kwargs):
                calls.append(comment["id"])
                return {"status": "COMPLETED"}

            with (
                mock.patch.object(controller, "GitHubClient", FakeGitHub),
                mock.patch.object(controller, "process_comment", side_effect=fake_process),
            ):
                result = controller.run_once(
                    token_file=token,
                    issue_number=42,
                    state_dir=state,
                    root_socket=pathlib.Path("/run/test.sock"),
                    controller_binary=pathlib.Path("/bin/false"),
                    controllers_dir=pathlib.Path("/etc/workspace-ci/controllers"),
                    runner_token_file=pathlib.Path("/run/test-token"),
                )
            self.assertEqual(calls, [11])
            self.assertEqual(result["last_seen_comment_id"], 11)


if __name__ == "__main__":
    unittest.main()
