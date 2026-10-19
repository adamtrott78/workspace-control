import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "architecture" / "lambda-ci-workload-policy.v1.json"
POLICY_SCHEMA_PATH = ROOT / "schemas" / "lambda-ci-workload-policy.v1.schema.json"
ADMISSION_SCHEMA_PATH = ROOT / "schemas" / "lambda-ci-admission-manifest.v1.schema.json"
RECEIPT_SCHEMA_PATH = ROOT / "schemas" / "lambda-ci-execution-receipt.v1.schema.json"

QWEN_REVISION = "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"
QWEN_RUNTIME = "qwen35-vllm-cu129-image-native-sampler-v3"
GPU_UUID = "GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea"
GPU_UUID_2 = "GPU-cfed3394-a935-63aa-9325-c4cae7b568b6"


class LambdaCIWorkloadPolicyContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = json.loads(POLICY_PATH.read_text())
        cls.policy_schema = json.loads(POLICY_SCHEMA_PATH.read_text())
        cls.admission_schema = json.loads(ADMISSION_SCHEMA_PATH.read_text())
        cls.receipt_schema = json.loads(RECEIPT_SCHEMA_PATH.read_text())

    def test_contract_is_non_live_and_root_authoritative(self):
        self.assertEqual(self.policy["schema_version"], 1)
        self.assertEqual(self.policy["status"], "CONTRACT_ONLY_NOT_LIVE_ENFORCEMENT")
        self.assertEqual(self.policy["authority"]["owner"], "workspace-control")
        self.assertFalse(self.policy["authority"]["live_lambda_mutation_authorized_by_this_contract"])
        self.assertTrue(self.policy["admission_semantics"]["root_issued_manifest_required"])
        self.assertTrue(self.policy["admission_semantics"]["single_use"])

    def test_exact_workload_taxonomy_and_gpu_heavy_denial(self):
        expected = {
            "cpu-test", "gpu-small", "model-acquire", "cache-promote",
            "model-eval-single-gpu", "model-eval-dual-gpu", "gpu-heavy",
        }
        self.assertEqual(set(self.policy["workload_classes"]), expected)
        heavy = self.policy["workload_classes"]["gpu-heavy"]
        self.assertEqual(heavy["policy_decision"], "DENY")
        self.assertFalse(heavy["admission_enabled_after_enforcement"])
        self.assertFalse(heavy["candidate_payload_allowed"])
        admitted = self.admission_schema["properties"]["workload_class"]["enum"]
        self.assertNotIn("gpu-heavy", admitted)

    def test_existing_p5_profiles_preserve_model_denial_and_bounded_runtime_authority(self):
        cpu = self.policy["workload_classes"]["cpu-test"]
        self.assertEqual(cpu["policy_decision"], "EXISTING_P5_CAPABILITY")
        self.assertEqual(cpu["model_binding"], "FORBIDDEN")
        self.assertEqual(cpu["cache_access_class"], "NO_PERSISTENT_CACHE_AUTHORITY")
        self.assertEqual(cpu["state_effect_class"], "CI_VALIDATION_ONLY")

        gpu = self.policy["workload_classes"]["gpu-small"]
        self.assertEqual(gpu["policy_decision"], "EXISTING_P5_CAPABILITY")
        self.assertEqual(gpu["model_binding"], "FORBIDDEN")
        self.assertEqual(gpu["cache_access_class"], "TRUSTED_RUNTIME_READONLY")
        self.assertEqual(gpu["runtime_binding"], "REQUIRED_EXPANDED_RUNTIME_EXACT")
        self.assertEqual(gpu["state_effect_class"], "CI_VALIDATION_ONLY")

        runtime_cache = self.policy["cache_access_classes"]["TRUSTED_RUNTIME_READONLY"]
        self.assertEqual(runtime_cache["trusted_runtime"], "read_only")
        self.assertEqual(runtime_cache["trusted_model"], "none")
        self.assertFalse(runtime_cache["candidate_persistent_write"])
        self.assertTrue(runtime_cache["digest_verify_before_execution"])
        self.assertTrue(runtime_cache["post_execution_digest_verify"])

    def test_acquisition_is_trusted_quarantine_only_and_no_inference(self):
        acquire = self.policy["workload_classes"]["model-acquire"]
        self.assertEqual(acquire["execution_plane"], "trusted_acquisition")
        self.assertFalse(acquire["candidate_payload_allowed"])
        self.assertTrue(acquire["inference_forbidden"])
        self.assertEqual(acquire["payload_network_class"], "TRUSTED_ARTIFACT_ACQUISITION_ONLY")
        self.assertEqual(acquire["cache_access_class"], "QUARANTINE_WRITE_TRUSTED_ONLY")
        self.assertEqual(acquire["state_effect_class"], "QUARANTINE_ARTIFACTS_ONLY")
        model_cache_binding = self.admission_schema["properties"]["models"]["items"]["properties"]["cache_object"]
        self.assertIn({"type": "null"}, model_cache_binding["oneOf"])

    def test_promotion_is_candidate_inaccessible_offline_and_quarantine_bound(self):
        promote = self.policy["workload_classes"]["cache-promote"]
        self.assertEqual(promote["execution_plane"], "trusted_cache_manager")
        self.assertFalse(promote["candidate_payload_allowed"])
        self.assertFalse(promote["candidate_invocable"])
        self.assertTrue(promote["inference_forbidden"])
        self.assertEqual(promote["payload_network_class"], "NO_NETWORK")
        self.assertEqual(promote["cache_access_class"], "TRUSTED_CACHE_PROMOTION_ONLY")
        self.assertEqual(promote["model_binding"], "REQUIRED_QUARANTINE_EXACT")
        self.assertEqual(promote["runtime_binding"], "OPTIONAL_QUARANTINE_EXACT")

    def test_model_eval_is_offline_read_only_secret_free_and_single_gpu(self):
        model_eval = self.policy["workload_classes"]["model-eval-single-gpu"]
        self.assertEqual(model_eval["resource_class"], "model_eval_single_gpu_v1")
        self.assertEqual(model_eval["payload_network_class"], "GITHUB_CONTROL_PLANE_ONLY_PAYLOAD_OFFLINE")
        self.assertTrue(model_eval["model_registry_credential_forbidden"])
        self.assertEqual(model_eval["filesystem_class"], "EPHEMERAL_JOB_PLUS_TRUSTED_CACHE_READONLY")
        self.assertEqual(model_eval["cache_access_class"], "TRUSTED_MODEL_RUNTIME_READONLY")
        resources = self.policy["resource_classes"]["model_eval_single_gpu_v1"]
        self.assertEqual(resources["execution_profile"], "gpu-small")
        self.assertEqual(resources["gpu_count"], 1)
        self.assertEqual(resources["gpu_uuids"], [GPU_UUID])
        self.assertEqual(resources["staging_max_bytes"], 0)

    def test_dual_model_eval_is_exact_two_gpu_and_bounded_live(self):
        dual = self.policy["workload_classes"]["model-eval-dual-gpu"]
        self.assertEqual(dual["policy_decision"], "EXISTING_P5_CAPABILITY")
        self.assertTrue(dual["admission_enabled_after_enforcement"])
        self.assertEqual(dual["resource_class"], "model_eval_dual_gpu_v1")
        self.assertEqual(dual["model_binding"], "REQUIRED_PROMOTED_EXACT")
        self.assertEqual(dual["runtime_binding"], "REQUIRED_EXPANDED_RUNTIME_EXACT")
        self.assertTrue(dual["model_registry_credential_forbidden"])

        resources = self.policy["resource_classes"]["model_eval_dual_gpu_v1"]
        self.assertEqual(resources["execution_profile"], "gpu-heavy")
        self.assertEqual(resources["gpu_count"], 2)
        self.assertEqual(resources["gpu_uuids"], [GPU_UUID, GPU_UUID_2])
        self.assertEqual(resources["max_runtime_seconds"], 1800)

        binding = self.policy["project_bindings"]["research-engine"]
        self.assertIn("model-eval-dual-gpu", binding["allowed_workload_classes"])
        self.assertEqual(binding["denied_workload_classes"], ["gpu-heavy"])
        self.assertEqual(
            binding["dual_gpu_model_eval"]["gpu_uuids"],
            [GPU_UUID, GPU_UUID_2],
        )
        self.assertEqual(binding["dual_gpu_model_eval"]["tensor_parallel_size"], 2)
        self.assertEqual(
            binding["dual_gpu_model_eval"]["activation_status"],
            "LIVE_BOUNDED_AFTER_HOST_ACCEPTANCE",
        )

    def test_local_extract_wave1_is_exact_public_payload_model_eval(self):
        wave1 = self.policy["workload_classes"][
            "model-eval-local-extract-wave1"
        ]
        self.assertEqual(
            wave1["policy_decision"],
            "EXISTING_P5_CAPABILITY",
        )
        self.assertTrue(wave1["admission_enabled_after_enforcement"])
        self.assertEqual(wave1["resource_class"], "model_eval_dual_gpu_v1")
        self.assertEqual(
            wave1["payload_network_class"],
            "GITHUB_CONTROL_PLANE_PLUS_PUBLIC_PAYLOAD",
        )
        self.assertEqual(
            wave1["model_binding"],
            "REQUIRED_PROMOTED_EXACT",
        )
        self.assertEqual(
            wave1["runtime_binding"],
            "REQUIRED_EXPANDED_RUNTIME_EXACT",
        )
        self.assertEqual(
            wave1["activation_gate"],
            "EXACT_LOCAL_EXTRACT_WAVE1_WORKFLOW_ONLY",
        )

        binding = self.policy["project_bindings"]["research-engine"]
        self.assertIn(
            "model-eval-local-extract-wave1",
            binding["allowed_workload_classes"],
        )
        self.assertEqual(
            binding["local_extract_wave1"]["workflow_blob_sha"],
            "a5be693f750c481db21d86d239a505083aae40aa",
        )
        self.assertFalse(
            binding["local_extract_wave1"][
                "scientific_state_materialized"
            ]
        )
        self.assertFalse(
            binding["local_extract_wave1"]["production_routing_change"]
        )
        self.assertEqual(
            binding["denied_workload_classes"],
            ["gpu-heavy"],
        )

    def test_qwen_first_pilot_is_exact_and_non_scientific(self):
        binding = self.policy["project_bindings"]["research-engine"]
        self.assertEqual(binding["denied_workload_classes"], ["gpu-heavy"])
        qwen = binding["allowed_models"][0]
        self.assertEqual(qwen["repository"], "Qwen/Qwen3.5-4B")
        self.assertEqual(qwen["revision"], QWEN_REVISION)
        self.assertEqual(qwen["serialization_requirement"], "SAFE_ONLY")
        self.assertTrue(qwen["promotion_required_before_eval"])
        runtime = binding["allowed_runtimes"][0]
        self.assertEqual(runtime["runtime_id"], QWEN_RUNTIME)
        pilot = binding["first_model_pilot"]
        self.assertEqual(pilot["workload_class"], "model-eval-single-gpu")
        self.assertFalse(pilot["scientific"])
        self.assertFalse(pilot["production_routing_change"])

    def test_unsafe_serialization_and_custom_code_fail_closed(self):
        serialization = self.policy["serialization_policy"]
        self.assertEqual(serialization["default_model_serialization"], "SAFE_ONLY")
        self.assertFalse(serialization["trust_remote_code_default"])
        self.assertEqual(serialization["approved_exceptions"], [])
        denied = set(serialization["deny_without_exception"])
        self.assertIn("pickle", denied)
        self.assertIn("custom_remote_code", denied)
        self.assertIn("mixed_or_unknown_executable_model_material", denied)

    def test_replay_and_cleanup_semantics_fail_closed(self):
        admission = self.policy["admission_semantics"]
        self.assertEqual(admission["request_id_conflict_behavior"], "REJECT")
        self.assertEqual(admission["identical_consumed_terminal_request_behavior"], "RETURN_EXISTING_RECEIPT_NO_REEXECUTION")
        self.assertEqual(admission["consumed_without_terminal_receipt_behavior"], "ABORT_INDETERMINATE_REQUIRE_FRESH_REQUEST")
        failure = self.policy["failure_semantics"]
        self.assertFalse(failure["automatic_retry_after_timeout"])
        self.assertFalse(failure["automatic_retry_after_cuda_oom"])
        self.assertEqual(failure["cleanup_failure_action"], "QUARANTINE_LANE_AND_BLOCK_NEW_ADMISSIONS")

    def test_policy_schema_requires_all_capability_dimensions(self):
        required = set(self.policy_schema["required"])
        for key in (
            "payload_network_classes", "payload_secret_classes", "filesystem_classes",
            "cache_access_classes", "state_effect_classes", "serialization_policy",
            "failure_semantics", "resource_classes", "workload_classes",
        ):
            self.assertIn(key, required)

    def test_admission_schema_binds_exact_identity_and_capabilities(self):
        required = set(self.admission_schema["required"])
        for key in (
            "request_digest_sha256", "policy", "trusted_workflow", "candidate_sha",
            "workload_class", "execution_profile", "resource_class", "capability_classes",
            "resource_ceiling", "models", "runtime", "exception_ids",
        ):
            self.assertIn(key, required)
        capability_required = set(self.admission_schema["properties"]["capability_classes"]["required"])
        self.assertEqual(
            capability_required,
            {"payload_network", "payload_secrets", "filesystem", "cache_access", "state_effect"},
        )
        self.assertTrue(self.admission_schema["properties"]["lifecycle"]["properties"]["single_use"]["const"])

    def test_receipt_schema_supports_jit_and_trusted_executors(self):
        executor = self.receipt_schema["properties"]["executor"]
        self.assertEqual(len(executor["oneOf"]), 2)
        jit = executor["oneOf"][0]["properties"]
        trusted = executor["oneOf"][1]["properties"]
        self.assertEqual(jit["kind"]["const"], "jit_runner")
        self.assertTrue(jit["jit_single_job"]["const"])
        self.assertEqual(set(trusted["kind"]["enum"]), {"trusted_acquisition", "trusted_cache_manager"})
        self.assertFalse(trusted["jit_single_job"]["const"])

    def test_receipt_schema_tracks_object_state_resource_state_and_cleanup(self):
        required = set(self.receipt_schema["required"])
        for key in (
            "terminal_status", "executor", "hardware", "resource_usage",
            "network_evidence", "state_effect_evidence", "cleanup", "evidence",
        ):
            self.assertIn(key, required)
        object_states = self.receipt_schema["properties"]["models"]["items"]["properties"]["object_state"]["enum"]
        self.assertEqual(set(object_states), {"QUARANTINE", "PROMOTED"})
        cleanup_required = set(self.receipt_schema["properties"]["cleanup"]["required"])
        for key in (
            "cgroup_empty", "project_uid_processes_zero", "gpu_compute_processes_zero",
            "model_servers_zero", "job_workspace_removed", "ephemeral_staging_removed",
            "jit_config_absent", "github_credential_absent", "lane_quarantined",
        ):
            self.assertIn(key, cleanup_required)


if __name__ == "__main__":
    unittest.main()
