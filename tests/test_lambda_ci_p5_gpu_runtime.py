import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "lambda_ci_runtime.py"

spec = importlib.util.spec_from_file_location("lambda_ci_runtime_gpu_test", MODULE_PATH)
runtime = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = runtime
spec.loader.exec_module(runtime)


class LambdaCIP5GPURuntimeTests(unittest.TestCase):
    def gpu_spec(self):
        return {
            "unit_name": "workspace-ci-research-engine-test.service",
            "project_id": "research-engine",
            "profile": "gpu-small",
            "runner_name": "lambda-research-engine-gpu-test",
            "run_as": {
                "user": "ci-research-engine",
                "group": "ci-research-engine",
            },
            "paths": {
                "job_root": "/srv/workspace-ci/research-engine/jobs",
                "staging_cache": "/srv/workspace-ci/research-engine/staging-cache",
                "trusted_cache": "/srv/workspace-ci/research-engine/trusted-cache",
                "home": "/srv/workspace-ci/research-engine/home",
                "logs": "/srv/workspace-ci/research-engine/logs",
            },
            "resources": {
                "cpu_quota_percent": 1200,
                "memory_max_bytes": 68719476736,
                "tasks_max": 8192,
                "runtime_max_seconds": 1200,
                "gpu_indices": [0],
                "gpu_uuid": "GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea",
            },
            "allow_production_services": False,
            "runtime_binding": {
                "runtime_id": "qwen35-vllm-cu129-image-native-sampler-v3",
                "canonical_path": (
                    "/srv/workspace-ci/research-engine/expanded-runtimes/"
                    "qwen35-vllm-cu129-image-native-sampler-v3/"
                    "f67ff9a26690c55930232c915e59e826e3cca2dd89012de9e35a852032b38f74"
                ),
                "python_path": (
                    "/srv/workspace-ci/research-engine/expanded-runtimes/"
                    "qwen35-vllm-cu129-image-native-sampler-v3/"
                    "f67ff9a26690c55930232c915e59e826e3cca2dd89012de9e35a852032b38f74/"
                    "bin/python"
                ),
                "receipt_path": (
                    "/var/lib/workspace-ci/expanded-runtime-receipts/"
                    "f67ff9a26690c55930232c915e59e826e3cca2dd89012de9e35a852032b38f74.json"
                ),
                "tree_digest_sha256": (
                    "b0cbb4efbe8673bdb421bad8036d29864bffe0687a9a654bbd95f54544659e63"
                ),
                "manifest_identity_sha256": (
                    "f67ff9a26690c55930232c915e59e826e3cca2dd89012de9e35a852032b38f74"
                ),
                "source_trusted_runtime_object": (
                    "/srv/workspace-ci/research-engine/trusted-cache/objects/runtime/sha256/"
                    "23a47f27bdb6bec63955b901080fc0926cffee8cf081d010195613789bc5bbf4"
                ),
                "required_controls": [
                    "root_owned_no_write_bits",
                    "private_systemd_mount_namespace",
                    "read_only_bind",
                    "no_new_privileges",
                    "restrict_suid_sgid",
                    "device_policy_closed",
                    "job_local_mutable_caches",
                ],
            },
        }

    def assignment(self):
        return {
            "target_uuid": "GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea",
            "selected_device": "/dev/nvidia1",
            "selected_minor": 1,
            "denied_devices": ["/dev/nvidia0"],
            "support_devices": ["/dev/nvidia-uvm", "/dev/nvidia-uvm-tools"],
            "inventory": [],
        }

    def test_gpu_systemd_command_preserves_p4_device_and_network_boundary(self):
        command = runtime.build_gpu_systemd_command(
            self.gpu_spec(),
            pathlib.Path("/srv/workspace-ci/research-engine/jobs/p5-test/runner"),
            pathlib.Path("/srv/workspace-ci/research-engine/staging-cache/p5-test"),
            "134.88.12.0/22",
            self.assignment(),
        )

        self.assertIn("DevicePolicy=closed", command)
        self.assertIn("DeviceAllow=/dev/nvidiactl rw", command)
        self.assertIn("DeviceAllow=/dev/nvidia1 rw", command)
        self.assertIn("DeviceAllow=/dev/nvidia-uvm rw", command)
        self.assertIn("DeviceAllow=/dev/nvidia-uvm-tools rw", command)
        self.assertNotIn("DeviceAllow=/dev/nvidia0 rw", command)
        self.assertNotIn("DeviceAllow=/dev/nvidia-modeset rw", command)
        self.assertIn(
            "Environment=CUDA_VISIBLE_DEVICES=GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea",
            command,
        )
        self.assertIn(
            "Environment=P5_GPU_SELECTED_DEVICE=/dev/nvidia1",
            command,
        )
        self.assertIn(
            "Environment=P5_GPU_DENIED_DEVICES=/dev/nvidia0",
            command,
        )
        self.assertIn("RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6", command)
        self.assertIn("IPAddressDeny=127.0.0.0/8", command)
        self.assertIn("IPAddressDeny=10.0.0.0/8", command)
        self.assertIn("IPAddressDeny=134.88.12.0/22", command)
        self.assertIn("RuntimeMaxSec=1200s", command)

    def test_dispatch_rejects_gpu_heavy(self):
        class Req:
            pass

        original_cpu = runtime.launch_cpu_runner
        original_gpu = runtime.launch_gpu_runner
        try:
            runtime.launch_cpu_runner = lambda req, spec: {"profile": "cpu"}
            runtime.launch_gpu_runner = lambda req, spec: {"profile": "gpu"}
            self.assertEqual(
                runtime.launch_runner(Req(), {"profile": "cpu-test"}),
                {"profile": "cpu"},
            )
            self.assertEqual(
                runtime.launch_runner(Req(), {"profile": "gpu-small"}),
                {"profile": "gpu"},
            )
            with self.assertRaises(runtime.RuntimeLaunchError):
                runtime.launch_runner(Req(), {"profile": "gpu-heavy"})
        finally:
            runtime.launch_cpu_runner = original_cpu
            runtime.launch_gpu_runner = original_gpu

    def test_runtime_contains_no_github_credential_client(self):
        source = MODULE_PATH.read_text()
        for forbidden in (
            "Authorization: Bearer",
            "api.github.com",
            "getpass",
            "GITHUB_TOKEN",
            "GH_TOKEN",
        ):
            self.assertNotIn(forbidden, source)


    def test_v2_admission_identity_is_bound_into_runtime_receipt(self):
        spec = self.gpu_spec()
        spec["admission"] = {
            "admission_id": "11111111-2222-4333-8444-555555555555",
            "request_digest_sha256": "1" * 64,
            "candidate_sha": "a" * 40,
            "workload_class": "gpu-small",
            "execution_profile": "gpu-small",
            "resource_class": "gpu_small_v1",
            "policy": {
                "policy_id": "lambda-ci-workload-policy-v1",
                "policy_epoch": 1,
                "policy_sha256": "2" * 64,
                "project_profile_sha256": "3" * 64,
                "kill_switch_epoch": 0,
            },
            "trusted_workflow": {
                "path": ".github/workflows/lambda-ci-p5-gpu-autonomous.yml",
                "default_branch_commit_sha": "b" * 40,
                "workflow_blob_sha": "c" * 40,
            },
            "lifecycle": {
                "consumed_at": "2026-10-06T20:00:00Z",
            },
        }
        identity = runtime.admission_receipt_identity(spec)["admission_identity"]
        self.assertEqual(
            identity["admission_id"],
            "11111111-2222-4333-8444-555555555555",
        )
        self.assertEqual(identity["candidate_sha"], "a" * 40)
        self.assertEqual(identity["policy_sha256"], "2" * 64)
        self.assertEqual(
            identity["workflow_blob_sha"],
            "c" * 40,
        )
        self.assertEqual(identity["workload_class"], "gpu-small")

    def test_v2_unconsumed_admission_is_rejected_by_runtime_identity_binding(self):
        spec = self.gpu_spec()
        spec["admission"] = {
            "policy": {},
            "trusted_workflow": {},
            "lifecycle": {"consumed_at": None},
        }
        with self.assertRaises(runtime.RuntimeLaunchError):
            runtime.admission_receipt_identity(spec)


if __name__ == "__main__":
    unittest.main()
