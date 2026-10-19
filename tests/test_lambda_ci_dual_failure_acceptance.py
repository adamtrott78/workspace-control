import pathlib
import sys
import unittest

SCRIPTS = pathlib.Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import lambda_ci_dual_failure_acceptance as acceptance


class DualFailureAcceptanceReceiptTests(unittest.TestCase):
    def common(self):
        return {
            "decision": "FAIL",
            "automatic_retry_eligible": False,
            "profile": "gpu-heavy",
            "gpu_target_uuids": list(acceptance.EXPECTED_UUIDS),
            "gpu_selected_devices": list(acceptance.EXPECTED_DEVICES),
            "cuda_visible_devices": ",".join(acceptance.EXPECTED_UUIDS),
            "gpu_prelaunch_idle_verified": True,
            "gpu_prelaunch_processes": [],
            "project_uid_process_cleanup": True,
            "project_uid_gpu_process_cleanup": True,
            "leaked_gpu_processes": [],
            "runner_workspace_destroyed": True,
            "staging_workspace_destroyed": True,
            "expanded_runtime_preverified": True,
            "expanded_runtime_postverified": True,
            "promoted_model_preverified": True,
            "promoted_model_postverified": True,
            "jit_config_persisted": False,
            "github_credential_present": False,
            "expanded_runtime": {
                "tree_digest_sha256": acceptance.EXPECTED_RUNTIME_DIGEST,
            },
            "expanded_runtime_post": {
                "tree_digest_sha256": acceptance.EXPECTED_RUNTIME_DIGEST,
            },
            "promoted_model": {
                "object_id": acceptance.EXPECTED_MODEL_OBJECT,
            },
            "promoted_model_post": {
                "object_id": acceptance.EXPECTED_MODEL_OBJECT,
            },
        }

    def test_timeout_receipt_accepts_exact_contract(self):
        value = self.common()
        value.update({
            "terminal_status": "TIMED_OUT",
            "timed_out": True,
            "wrapper_timeout_cleanup": True,
            "resource_exhausted": False,
            "disk_pressure": False,
            "cuda_oom": False,
            "systemd_terminal_evidence": {
                "available": True,
                "result": "timeout",
                "exec_main_code": "2",
                "exec_main_status": "9",
            },
        })
        acceptance.assert_timeout_receipt(value)

    def test_oom_receipt_accepts_exact_exit_86_contract(self):
        value = self.common()
        value.update({
            "terminal_status": "CUDA_OOM",
            "timed_out": False,
            "resource_exhausted": False,
            "disk_pressure": False,
            "cuda_oom": True,
            "systemd_terminal_evidence": {
                "available": True,
                "result": "exit-code",
                "exec_main_code": "1",
                "exec_main_status": "86",
            },
            "cuda_oom_evidence": {
                "available": True,
                "matched": True,
                "kind": "dual_gpu_cuda_oom_acceptance_v1",
                "source_blob_sha": acceptance.OOM_PROBE_BLOB,
                "expected_exit_code": 86,
                "systemd_result": "exit-code",
                "systemd_exec_main_code": "1",
                "systemd_exec_main_status": "86",
            },
        })
        acceptance.assert_oom_receipt(value)

    def test_oom_receipt_rejects_wrong_exit(self):
        value = self.common()
        value.update({
            "terminal_status": "CUDA_OOM",
            "timed_out": False,
            "resource_exhausted": False,
            "disk_pressure": False,
            "cuda_oom": True,
            "systemd_terminal_evidence": {
                "available": True,
                "result": "exit-code",
                "exec_main_code": "1",
                "exec_main_status": "87",
            },
            "cuda_oom_evidence": {
                "available": True,
                "matched": False,
                "kind": "dual_gpu_cuda_oom_acceptance_v1",
                "source_blob_sha": acceptance.OOM_PROBE_BLOB,
                "expected_exit_code": 86,
                "systemd_result": "exit-code",
                "systemd_exec_main_code": "1",
                "systemd_exec_main_status": "87",
            },
        })
        with self.assertRaises(AssertionError):
            acceptance.assert_oom_receipt(value)

    def test_dormant_policy_reads_activation_from_workload_policy(self):
        manifest = {
            "admission_v2": {
                "live_enabled_workload_classes": [
                    "cpu-test",
                    "gpu-small",
                    "model-eval-single-gpu",
                ],
                "routes": {
                    "model-eval-dual-gpu": {
                        "execution_profile": "gpu-heavy",
                        "model_binding_id": "qwen3.5-4b",
                    },
                },
            },
        }
        policy = {
            "workload_classes": {
                "model-eval-dual-gpu": {
                    "policy_decision": "DESIGNED_NOT_LIVE",
                    "admission_enabled_after_enforcement": False,
                    "resource_class": "model_eval_dual_gpu_v1",
                    "activation_gate": "EXACT_TWO_GPU_HOST_ACCEPTANCE_REQUIRED",
                },
                "gpu-heavy": {
                    "policy_decision": "DENY",
                    "admission_enabled_after_enforcement": False,
                },
            },
        }

        acceptance.assert_dormant_policy(manifest, policy)

        policy["workload_classes"]["model-eval-dual-gpu"][
            "admission_enabled_after_enforcement"
        ] = True
        with self.assertRaises(AssertionError):
            acceptance.assert_dormant_policy(manifest, policy)


if __name__ == "__main__":
    unittest.main()
