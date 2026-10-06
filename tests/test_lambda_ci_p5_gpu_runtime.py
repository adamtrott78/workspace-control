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


if __name__ == "__main__":
    unittest.main()
