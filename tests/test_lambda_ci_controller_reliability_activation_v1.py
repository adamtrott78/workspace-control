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

    def test_activation_scope_preserves_both_research_lanes_nonrunning(self):
        self.assertNotIn(activation.RESEARCH_CPU, activation.ACTIVE_AFTER_INSTALL)
        self.assertNotIn(activation.RESEARCH_GPU, activation.ACTIVE_AFTER_INSTALL)
        self.assertEqual(
            activation.ACTIVE_AFTER_INSTALL,
            [
                activation.PAD_CPU,
                activation.PAD_GPU,
                activation.WORKSPACE_CPU,
            ],
        )

    def test_healthy_controller_baselines_match_frozen_preflight(self):
        self.assertEqual(
            activation.EXPECTED_HEALTHY_BASELINES[activation.PAD_CPU],
            {"Result": "success", "NRestarts": "0"},
        )
        self.assertEqual(
            activation.EXPECTED_HEALTHY_BASELINES[activation.PAD_GPU],
            {"Result": "success", "NRestarts": "0"},
        )
        self.assertEqual(
            activation.EXPECTED_HEALTHY_BASELINES[activation.WORKSPACE_CPU],
            {"Result": "success", "NRestarts": "14140"},
        )

    def test_gpu_stop_failure_is_reissued_and_containment_proved(self):
        calls = []

        def fake_run(argv, check=True, user=None, env=None):
            calls.append((tuple(argv), check))
            if (
                argv[:3]
                == ["systemctl", "stop", activation.RESEARCH_GPU]
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

    def test_first_containment_failure_enters_rollback_guard(self):
        with tempfile.NamedTemporaryFile() as built:
            backup = {"files": {}}
            rollback = {"gpu": "inactive"}
            with (
                mock.patch.object(
                    activation,
                    "build_controller",
                    return_value=pathlib.Path(built.name),
                ),
                mock.patch.object(activation, "git_text", return_value="payload"),
                mock.patch.object(activation, "save_backups", return_value=backup),
                mock.patch.object(
                    activation,
                    "contain_gpu_fail_closed",
                    side_effect=activation.ActivationError("stop failure"),
                ),
                mock.patch.object(
                    activation,
                    "rollback_activation",
                    return_value=rollback,
                ) as rollback_call,
            ):
                with self.assertRaisesRegex(
                    activation.ActivationError,
                    "activation failed; old files restored",
                ):
                    activation.activate(
                        pathlib.Path("/tmp/repo"),
                        "head",
                        "operator",
                        {},
                    )
            rollback_call.assert_called_once_with(backup)

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

    def test_rollback_invalidates_retry_before_restoring_old_bytes(self):
        order = []

        def mark(name, value):
            def inner(*args, **kwargs):
                order.append(name)
                return value
            return inner

        with (
            mock.patch.object(
                activation,
                "contain_gpu_fail_closed",
                side_effect=mark("contain", {"proof": inactive_gpu_snapshot()}),
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
                "restore_frozen_quarantine",
                side_effect=mark(
                    "quarantine",
                    dict(activation.EXPECTED_QUARANTINE),
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

        self.assertLess(order.index("contain"), order.index("invalidate"))
        self.assertLess(order.index("invalidate"), order.index("restore_bytes"))

    def test_certification_never_starts_gpu_even_if_work_arrives(self):
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotIn(
            'run(["systemctl", "start", RESEARCH_GPU])',
            source,
        )
        self.assertNotIn(
            'run(["systemctl", "restart", RESEARCH_GPU])',
            source,
        )
        self.assertNotIn(activation.RESEARCH_GPU, activation.ACTIVE_AFTER_INSTALL)

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
