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
SPEC = importlib.util.spec_from_file_location("controller_reliability_activation", MODULE_PATH)
activation = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(activation)


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

    def test_activation_scope_preserves_inactive_research_cpu(self):
        self.assertNotIn(activation.RESEARCH_CPU, activation.ACTIVE_AFTER_INSTALL)
        self.assertEqual(
            activation.ACTIVE_AFTER_INSTALL,
            [
                activation.PAD_CPU,
                activation.PAD_GPU,
                activation.WORKSPACE_CPU,
                activation.RESEARCH_GPU,
            ],
        )

    def test_post_activation_recovery_requires_terminal_invalidation(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            quarantine = dict(activation.EXPECTED_QUARANTINE)
            quarantine["observed_at"] = "2026-10-28T07:50:25.858984434Z"
            ready = dict(activation.EXPECTED_READY)
            ready.update(
                {
                    "status": "RECOVERY_RETRY_INVALIDATED",
                    "previous_status": "READY_FOR_SINGLE_RETRY",
                    "invalidated_by_quarantine_receipt_id":
                        activation.EXPECTED_QUARANTINE["receipt_id"],
                    "invalidated_at": "2026-10-29T00:00:00Z",
                    "first_zero_observed_at": "2026-10-28T07:33:45.411383063Z",
                    "second_zero_observed_at": "2026-10-28T07:40:36.29291935Z",
                }
            )
            (root / "quarantine.json").write_text(json.dumps(quarantine))
            (root / "ready-for-single-retry.json").write_text(json.dumps(ready))
            with mock.patch.object(activation, "GPU_STATE", root):
                result = activation.require_post_activation_recovery()
            self.assertEqual(
                result["retry_gate"]["status"],
                "RECOVERY_RETRY_INVALIDATED",
            )

    def test_post_activation_recovery_rejects_ready_authority(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            quarantine = dict(activation.EXPECTED_QUARANTINE)
            quarantine["observed_at"] = "2026-10-28T07:50:25.858984434Z"
            ready = dict(activation.EXPECTED_READY)
            (root / "quarantine.json").write_text(json.dumps(quarantine))
            (root / "ready-for-single-retry.json").write_text(json.dumps(ready))
            with mock.patch.object(activation, "GPU_STATE", root):
                with self.assertRaisesRegex(
                    activation.ActivationError,
                    "post-activation retry gate mismatch",
                ):
                    activation.require_post_activation_recovery()

    def test_gpu_preflight_accepts_only_existing_crash_loop_shape(self):
        snap = {
            "LoadState": "loaded",
            "UnitFileState": "enabled",
            "ActiveState": "activating",
            "SubState": "auto-restart",
            "Result": "exit-code",
            "ExecMainCode": "1",
            "ExecMainStatus": "1",
            "NRestarts": "14299",
            "MainPID": "0",
            "InvocationID": "abc",
            "Restart": "on-failure",
        }
        with mock.patch.object(activation, "service_snapshot", return_value=snap):
            self.assertEqual(
                activation.require_old_gpu_loop()["NRestarts"],
                "14299",
            )

    def test_source_payload_is_read_from_git_objects(self):
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertIn("def git_text(", source)
        self.assertNotIn("shutil.copytree(", source)
        self.assertIn('git_text(repo, invoker, rel)', source)


if __name__ == "__main__":
    unittest.main()
