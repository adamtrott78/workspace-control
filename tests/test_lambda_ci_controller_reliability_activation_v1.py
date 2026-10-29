import importlib.util
import json
import pathlib
import tempfile
import unittest
from unittest import mock


MODULE_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "scripts"
    / "lambda_ci_controller_reliability_activation_v1.py"
)
SPEC = importlib.util.spec_from_file_location(
    "controller_reliability_activation",
    MODULE_PATH,
)
activation = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(activation)


def inactive_gpu_snapshot():
    return {
        "LoadState": "loaded",
        "UnitFileState": "enabled",
        "ActiveState": "inactive",
        "SubState": "dead",
        "Result": "success",
        "ExecMainCode": "0",
        "ExecMainStatus": "0",
        "NRestarts": "14276",
        "MainPID": "0",
        "InvocationID": "inactive",
        "Restart": "on-failure",
    }


def inactive_workspace_snapshot():
    value = inactive_gpu_snapshot()
    value["NRestarts"] = str(activation.WORKSPACE_CPU_MIN_RESTARTS)
    return value


def prepared_payload(path: pathlib.Path):
    return {
        "built": path,
        "candidate_sha256": activation.sha256_path(path),
        "controller_unit": b"unit",
        "maintenance_service": b"maintenance",
    }


class ControllerReliabilityActivationTests(unittest.TestCase):
    def test_payload_is_bound_to_reviewed_source_blobs(self):
        self.assertEqual(
            activation.PAYLOAD_SOURCE_HEAD,
            "7524612dfb96e24f45a969b761858b2f71409fc4",
        )
        self.assertEqual(
            activation.EXPECTED_SOURCE_BLOBS[
                "controller/lambda-ci-controller/main.go"
            ],
            "7ed009e3602460650909ce1e7b713d8c3b84b66b",
        )
        self.assertEqual(
            activation.EXPECTED_SOURCE_BLOBS[
                "controller/lambda-ci-controller/attestation.go"
            ],
            "4d16f9668173c2ac04e30bf09ea6814e09dd9c51",
        )

    def test_live_baseline_hashes_match_frozen_preflight(self):
        self.assertEqual(
            activation.EXPECTED_OLD_SHA256[
                "/opt/workspace-ci/controller/lambda-ci-controller"
            ],
            "6acd290f2312f0908d17443a2f5ee8d31711fbdb3f0bf9318171e9edd0ddee12",
        )
        self.assertEqual(
            activation.EXPECTED_OLD_SHA256[
                "/etc/systemd/system/workspace-ci-controller@.service"
            ],
            "3b77df48549a0972ca4b1f207b09067808cb8f1eed1ca9d967511df74d7be16f",
        )
        self.assertEqual(
            activation.EXPECTED_OLD_SHA256[
                "/opt/workspace-ci/maintenance/lambda_ci_maintenance_service.py"
            ],
            "59395404e8a174fefbde32657e6215c87a4170f539c85fc8aa5e2295883f6e6d",
        )

    def test_activation_scope_holds_both_broken_lanes_nonrunning(self):
        self.assertNotIn(activation.RESEARCH_CPU, activation.ACTIVE_AFTER_INSTALL)
        self.assertNotIn(activation.RESEARCH_GPU, activation.ACTIVE_AFTER_INSTALL)
        self.assertNotIn(activation.WORKSPACE_CPU, activation.ACTIVE_AFTER_INSTALL)
        self.assertEqual(
            activation.ACTIVE_AFTER_INSTALL,
            [
                activation.PAD_CPU,
                activation.PAD_GPU,
            ],
        )
        self.assertEqual(
            activation.BROKEN_LANES_HELD,
            [activation.RESEARCH_GPU, activation.WORKSPACE_CPU],
        )

    def test_workspace_cpu_preflight_requires_old_crash_loop_signature(self):
        crash = inactive_workspace_snapshot()
        crash.update(
            {
                "ActiveState": "activating",
                "SubState": "auto-restart",
                "Result": "exit-code",
                "ExecMainCode": "1",
                "ExecMainStatus": "1",
            }
        )
        with mock.patch.object(activation, "service_snapshot", return_value=crash):
            observed = activation.require_old_workspace_cpu_loop()
        self.assertEqual(
            int(observed["NRestarts"]),
            activation.WORKSPACE_CPU_MIN_RESTARTS,
        )

        regressed = dict(crash)
        regressed["NRestarts"] = str(activation.WORKSPACE_CPU_MIN_RESTARTS - 1)
        with (
            mock.patch.object(activation, "service_snapshot", return_value=regressed),
            self.assertRaisesRegex(
                activation.ActivationError,
                "workspace-control cpu restart count regressed",
            ),
        ):
            activation.require_old_workspace_cpu_loop()

    def test_immutable_candidate_is_prepared_before_live_preflight(self):
        source = MODULE_PATH.read_text(encoding="utf-8")
        prepare_at = source.index("prepared = prepare_payload(repo, invoker)")
        preflight_at = source.index("before = preflight(repo)", prepare_at)
        activate_at = source.index(
            "receipt = activate(args.expected_head, before, prepared)",
            preflight_at,
        )
        self.assertLess(prepare_at, preflight_at)
        self.assertLess(preflight_at, activate_at)
        activate_body = source[
            source.index("def activate("):
            source.index("\ndef main() -> int:")
        ]
        self.assertNotIn("build_controller(", activate_body)
        self.assertNotIn("git_text(", activate_body)

    def test_gpu_stop_failure_is_reissued_and_containment_proved(self):
        calls = []

        def fake_run(argv, check=True, user=None, env=None):
            calls.append((tuple(argv), check))
            if (
                argv[:3] == ["systemctl", "stop", activation.RESEARCH_GPU]
                and len(
                    [
                        item
                        for item in calls
                        if item[0][:3]
                        == ("systemctl", "stop", activation.RESEARCH_GPU)
                    ]
                )
                == 1
            ):
                raise activation.ActivationError(
                    "synthetic stop returned failure after changing state"
                )
            return mock.Mock(returncode=0, stdout="", stderr="")

        with (
            mock.patch.object(activation, "run", side_effect=fake_run),
            mock.patch.object(
                activation,
                "service_snapshot",
                return_value=inactive_gpu_snapshot(),
            ),
        ):
            with self.assertRaisesRegex(
                activation.ActivationError,
                "initial research-engine gpu stop failed after containment was proved",
            ):
                activation.contain_gpu_fail_closed()

        stop_calls = [
            item
            for item in calls
            if item[0][:3] == ("systemctl", "stop", activation.RESEARCH_GPU)
        ]
        self.assertGreaterEqual(len(stop_calls), 2)

    def test_dual_containment_first_action_targets_both_broken_lanes(self):
        calls = []

        def fake_run(argv, check=True, user=None, env=None):
            calls.append((tuple(argv), check))
            return mock.Mock(returncode=0, stdout="", stderr="")

        def fake_snapshot(service):
            if service == activation.RESEARCH_GPU:
                return inactive_gpu_snapshot()
            if service == activation.WORKSPACE_CPU:
                return inactive_workspace_snapshot()
            raise AssertionError(service)

        with (
            mock.patch.object(activation, "run", side_effect=fake_run),
            mock.patch.object(activation, "service_snapshot", side_effect=fake_snapshot),
        ):
            result = activation.contain_broken_lanes_fail_closed()

        self.assertEqual(
            calls[0][0],
            (
                "systemctl",
                "stop",
                activation.RESEARCH_GPU,
                activation.WORKSPACE_CPU,
            ),
        )
        self.assertEqual(
            set(result["proofs"]),
            {activation.RESEARCH_GPU, activation.WORKSPACE_CPU},
        )

    def test_dual_containment_reissues_both_stops_after_joint_stop_error(self):
        calls = []

        def fake_run(argv, check=True, user=None, env=None):
            calls.append((tuple(argv), check))
            if argv == [
                "systemctl",
                "stop",
                activation.RESEARCH_GPU,
                activation.WORKSPACE_CPU,
            ]:
                raise activation.ActivationError(
                    "synthetic joint stop failed after partial transition"
                )
            return mock.Mock(returncode=0, stdout="", stderr="")

        def fake_snapshot(service):
            if service == activation.RESEARCH_GPU:
                return inactive_gpu_snapshot()
            if service == activation.WORKSPACE_CPU:
                return inactive_workspace_snapshot()
            raise AssertionError(service)

        with (
            mock.patch.object(activation, "run", side_effect=fake_run),
            mock.patch.object(activation, "service_snapshot", side_effect=fake_snapshot),
        ):
            with self.assertRaisesRegex(
                activation.ActivationError,
                "initial dual-lane stop failed after containment was proved",
            ):
                activation.contain_broken_lanes_fail_closed()

        self.assertIn(
            (("systemctl", "stop", activation.RESEARCH_GPU), False),
            calls,
        )
        self.assertIn(
            (("systemctl", "stop", activation.WORKSPACE_CPU), False),
            calls,
        )

    def test_first_containment_failure_enters_rollback_before_backups(self):
        with tempfile.NamedTemporaryFile() as built:
            payload = prepared_payload(pathlib.Path(built.name))
            rollback = {"gpu": "inactive"}
            with (
                mock.patch.object(
                    activation,
                    "contain_broken_lanes_fail_closed",
                    side_effect=activation.ActivationError("stop failure"),
                ),
                mock.patch.object(
                    activation,
                    "rollback_activation",
                    return_value=rollback,
                ) as rollback_call,
                mock.patch.object(activation, "save_backups") as backups,
            ):
                with self.assertRaisesRegex(
                    activation.ActivationError,
                    "old files preserved/restored",
                ):
                    activation.activate("head", {}, payload)
            rollback_call.assert_called_once_with(None)
            backups.assert_not_called()

    def _write_recovery_state(self, root: pathlib.Path, status: str):
        quarantine = dict(activation.EXPECTED_QUARANTINE)
        ready = dict(activation.EXPECTED_READY)
        ready["status"] = status
        if status == "RECOVERY_RETRY_ACQUIRED":
            ready.update(
                {
                    "job_id": "777",
                    "workflow_run_id": 999,
                    "acquired_at": "2026-10-29T00:00:00Z",
                }
            )
        (root / "quarantine.json").write_text(
            json.dumps(quarantine),
            encoding="utf-8",
        )
        (root / "ready-for-single-retry.json").write_text(
            json.dumps(ready),
            encoding="utf-8",
        )

    def test_retry_authority_is_terminally_invalidated_for_ready_or_acquired(self):
        for status in ("READY_FOR_SINGLE_RETRY", "RECOVERY_RETRY_ACQUIRED"):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as td:
                root = pathlib.Path(td)
                self._write_recovery_state(root, status)
                with (
                    mock.patch.object(activation, "GPU_STATE", root),
                    mock.patch.object(activation.os, "chown"),
                ):
                    result = activation.ensure_retry_invalidated()
                self.assertEqual(
                    result["status"],
                    "RECOVERY_RETRY_INVALIDATED",
                )
                self.assertEqual(result["previous_status"], status)
                self.assertEqual(
                    result["invalidated_by_quarantine_receipt_id"],
                    activation.EXPECTED_QUARANTINE["receipt_id"],
                )

    def test_acquisition_between_preflight_and_containment_aborts_before_backup(self):
        with tempfile.TemporaryDirectory() as td, tempfile.NamedTemporaryFile() as built:
            root = pathlib.Path(td)
            self._write_recovery_state(root, "RECOVERY_RETRY_ACQUIRED")
            payload = prepared_payload(pathlib.Path(built.name))

            def rollback_probe(backup):
                self.assertIsNone(backup)
                gate = json.loads(
                    (root / "ready-for-single-retry.json").read_text()
                )
                self.assertEqual(
                    gate["status"],
                    "RECOVERY_RETRY_INVALIDATED",
                )
                self.assertEqual(
                    gate["previous_status"],
                    "RECOVERY_RETRY_ACQUIRED",
                )
                return {"gpu": "inactive"}

            with (
                mock.patch.object(activation, "GPU_STATE", root),
                mock.patch.object(activation.os, "chown"),
                mock.patch.object(
                    activation,
                    "contain_broken_lanes_fail_closed",
                    return_value={
                        "proofs": {
                            activation.RESEARCH_GPU: inactive_gpu_snapshot(),
                            activation.WORKSPACE_CPU: inactive_workspace_snapshot(),
                        }
                    },
                ),
                mock.patch.object(activation, "require_no_active_execution"),
                mock.patch.object(
                    activation,
                    "rollback_activation",
                    side_effect=rollback_probe,
                ) as rollback_call,
                mock.patch.object(activation, "save_backups") as backups,
                mock.patch.object(activation, "atomic_install") as install,
            ):
                with self.assertRaisesRegex(
                    activation.ActivationError,
                    "retry authority changed between live preflight and containment",
                ):
                    activation.activate("head", {}, payload)

            rollback_call.assert_called_once_with(None)
            backups.assert_not_called()
            install.assert_not_called()

    def test_rollback_orders_quarantine_before_invalidation_before_old_bytes(self):
        order = []

        def mark(name, value):
            def inner(*args, **kwargs):
                order.append(name)
                return value
            return inner

        with (
            mock.patch.object(
                activation,
                "contain_broken_lanes_fail_closed",
                side_effect=mark("contain", {"proof": inactive_gpu_snapshot()}),
            ),
            mock.patch.object(
                activation,
                "restore_frozen_quarantine",
                side_effect=mark(
                    "quarantine",
                    dict(activation.EXPECTED_QUARANTINE),
                ),
            ),
            mock.patch.object(
                activation,
                "ensure_retry_invalidated",
                side_effect=mark(
                    "invalidate",
                    {"status": "RECOVERY_RETRY_INVALIDATED"},
                ),
            ),
            mock.patch.object(
                activation,
                "restore_backups",
                side_effect=mark("restore_bytes", None),
            ),
            mock.patch.object(activation, "run", return_value=mock.Mock(returncode=0)),
            mock.patch.object(activation, "wait_socket"),
            mock.patch.object(
                activation,
                "stable_running",
                return_value={
                    "first": {"NRestarts": "0"},
                    "second": {"NRestarts": "0"},
                },
            ),
            mock.patch.object(
                activation,
                "require_inactive_research_cpu",
                return_value={"ActiveState": "inactive"},
            ),
            mock.patch.object(
                activation,
                "require_gpu_inactive",
                return_value=inactive_gpu_snapshot(),
            ),
            mock.patch.object(
                activation,
                "require_workspace_cpu_inactive",
                return_value=inactive_workspace_snapshot(),
            ),
            mock.patch.object(activation, "require_no_active_execution"),
            mock.patch.object(
                activation,
                "require_post_activation_recovery",
                return_value={
                    "quarantine": dict(activation.EXPECTED_QUARANTINE),
                    "retry_gate": {"status": "RECOVERY_RETRY_INVALIDATED"},
                },
            ),
        ):
            activation.rollback_activation({"files": {}})

        self.assertLess(order.index("contain"), order.index("quarantine"))
        self.assertLess(order.index("quarantine"), order.index("invalidate"))
        self.assertLess(order.index("invalidate"), order.index("restore_bytes"))

    def test_rollback_repairs_missing_or_drifted_quarantine_then_invalidates(self):
        for condition in ("missing", "drifted"):
            with self.subTest(condition=condition), tempfile.TemporaryDirectory() as td:
                root = pathlib.Path(td)
                self._write_recovery_state(root, "READY_FOR_SINGLE_RETRY")
                qpath = root / "quarantine.json"
                if condition == "missing":
                    qpath.unlink()
                else:
                    drifted = dict(activation.EXPECTED_QUARANTINE)
                    drifted["receipt_id"] = "drifted"
                    qpath.write_text(json.dumps(drifted), encoding="utf-8")

                with (
                    mock.patch.object(activation, "GPU_STATE", root),
                    mock.patch.object(activation.os, "chown"),
                    mock.patch.object(
                        activation,
                        "contain_broken_lanes_fail_closed",
                        return_value={"proof": inactive_gpu_snapshot()},
                    ),
                    mock.patch.object(activation, "restore_backups"),
                    mock.patch.object(
                        activation,
                        "run",
                        return_value=mock.Mock(returncode=0),
                    ),
                    mock.patch.object(activation, "wait_socket"),
                    mock.patch.object(
                        activation,
                        "stable_running",
                        return_value={
                            "first": {"NRestarts": "0"},
                            "second": {"NRestarts": "0"},
                        },
                    ),
                    mock.patch.object(
                        activation,
                        "require_inactive_research_cpu",
                        return_value={"ActiveState": "inactive"},
                    ),
                    mock.patch.object(
                        activation,
                        "require_gpu_inactive",
                        return_value=inactive_gpu_snapshot(),
                    ),
                    mock.patch.object(
                        activation,
                        "require_workspace_cpu_inactive",
                        return_value=inactive_workspace_snapshot(),
                    ),
                    mock.patch.object(activation, "require_no_active_execution"),
                ):
                    result = activation.rollback_activation({"files": {}})

                restored = json.loads(qpath.read_text())
                gate = json.loads(
                    (root / "ready-for-single-retry.json").read_text()
                )
                self.assertEqual(restored, activation.EXPECTED_QUARANTINE)
                self.assertEqual(
                    gate["status"],
                    "RECOVERY_RETRY_INVALIDATED",
                )
                self.assertEqual(
                    gate["invalidated_by_quarantine_receipt_id"],
                    activation.EXPECTED_QUARANTINE["receipt_id"],
                )
                self.assertEqual(
                    result["gpu"]["ActiveState"],
                    "inactive",
                )

    def test_certification_never_starts_broken_lanes_even_if_work_arrives(self):
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotIn(
            'run(["systemctl", "start", RESEARCH_GPU])',
            source,
        )
        self.assertNotIn(
            'run(["systemctl", "restart", RESEARCH_GPU])',
            source,
        )
        self.assertNotIn(
            'run(["systemctl", "start", WORKSPACE_CPU])',
            source,
        )
        self.assertNotIn(
            'run(["systemctl", "restart", WORKSPACE_CPU])',
            source,
        )
        self.assertNotIn(activation.RESEARCH_GPU, activation.ACTIVE_AFTER_INSTALL)
        self.assertNotIn(activation.WORKSPACE_CPU, activation.ACTIVE_AFTER_INSTALL)

    def test_quarantine_restore_preserves_invalidated_retry_authority(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            self._write_recovery_state(root, "READY_FOR_SINGLE_RETRY")
            with (
                mock.patch.object(activation, "GPU_STATE", root),
                mock.patch.object(activation.os, "chown"),
            ):
                invalidated = activation.ensure_retry_invalidated()
                (root / "quarantine.json").unlink()
                restored = activation.restore_frozen_quarantine()
                reread = json.loads(
                    (root / "ready-for-single-retry.json").read_text()
                )
            self.assertEqual(restored, activation.EXPECTED_QUARANTINE)
            self.assertEqual(
                reread["status"],
                "RECOVERY_RETRY_INVALIDATED",
            )
            self.assertEqual(
                reread["invalidated_at"],
                invalidated["invalidated_at"],
            )

    def test_post_activation_recovery_requires_quarantine_and_invalidation(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            self._write_recovery_state(root, "READY_FOR_SINGLE_RETRY")
            with (
                mock.patch.object(activation, "GPU_STATE", root),
                mock.patch.object(activation.os, "chown"),
            ):
                activation.ensure_retry_invalidated()
                result = activation.require_post_activation_recovery()
            self.assertEqual(
                result["quarantine"],
                activation.EXPECTED_QUARANTINE,
            )
            self.assertEqual(
                result["retry_gate"]["status"],
                "RECOVERY_RETRY_INVALIDATED",
            )

    def test_source_payload_is_read_from_git_objects(self):
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertIn("def git_text(", source)
        self.assertNotIn("shutil.copytree(", source)
        self.assertIn('git_text(repo, invoker, rel)', source)


if __name__ == "__main__":
    unittest.main()
