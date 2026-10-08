import hashlib
import importlib.util
import os
import pathlib
import stat
import sys
import tempfile
import unittest
from types import SimpleNamespace

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

    def test_expanded_runtime_tree_digest_uses_binary_separators(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            sub = root / "pkg"
            sub.mkdir()
            payload = sub / "module.py"
            payload.write_bytes(b"print('ok')\n")
            link = root / "python"
            link.symlink_to("/usr/bin/python3.12")

            os.chmod(root, 0o555)
            os.chmod(sub, 0o555)
            os.chmod(payload, 0o444)

            expected = hashlib.sha256()

            entries = sorted(
                root.rglob("*"),
                key=lambda item: item.relative_to(root).as_posix(),
            )
            for path in entries:
                rel = path.relative_to(root).as_posix().encode()
                st = path.lstat()
                mode = format(stat.S_IMODE(st.st_mode), "o").encode()

                if stat.S_ISDIR(st.st_mode):
                    expected.update(b"D\x00" + rel + b"\x00" + mode + b"\n")
                    continue

                if stat.S_ISLNK(st.st_mode):
                    expected.update(
                        b"L\x00"
                        + rel
                        + b"\x00"
                        + os.readlink(path).encode()
                        + b"\n"
                    )
                    continue

                self.assertTrue(stat.S_ISREG(st.st_mode))
                digest = hashlib.sha256(path.read_bytes()).hexdigest().encode()
                expected.update(
                    b"F\x00"
                    + rel
                    + b"\x00"
                    + mode
                    + b"\x00"
                    + str(st.st_size).encode()
                    + b"\x00"
                    + digest
                    + b"\n"
                )

            self.assertEqual(
                runtime.expanded_runtime_tree_digest(root),
                expected.hexdigest(),
            )


    def test_project_uid_cleanup_rechecks_after_kill(self):
        calls = []
        responses = [
            SimpleNamespace(returncode=0, stdout="1234 python\n", stderr=""),
            SimpleNamespace(returncode=0, stdout="", stderr=""),
            SimpleNamespace(returncode=1, stdout="", stderr=""),
        ]
        original = runtime.run

        def fake_run(argv, check=True):
            calls.append(argv)
            return responses.pop(0)

        runtime.run = fake_run
        try:
            detected, clean = runtime.cleanup_project_uid_processes(997)
        finally:
            runtime.run = original

        self.assertTrue(detected)
        self.assertTrue(clean)
        self.assertEqual(calls[0], ["pgrep", "-u", "997"])
        self.assertEqual(calls[1], ["pkill", "-KILL", "-u", "997"])
        self.assertEqual(calls[2], ["pgrep", "-u", "997"])

    def test_project_uid_cleanup_fails_if_residue_survives_kill(self):
        responses = [
            SimpleNamespace(returncode=0, stdout="1234 python\n", stderr=""),
            SimpleNamespace(returncode=0, stdout="", stderr=""),
            SimpleNamespace(returncode=0, stdout="1234 python\n", stderr=""),
        ]
        original = runtime.run
        runtime.run = lambda argv, check=True: responses.pop(0)
        try:
            detected, clean = runtime.cleanup_project_uid_processes(997)
        finally:
            runtime.run = original

        self.assertTrue(detected)
        self.assertFalse(clean)

    def test_remove_tree_and_verify_reports_real_postcondition(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / "job"
            root.mkdir()
            (root / "payload").write_text("x", encoding="utf-8")
            self.assertTrue(runtime.remove_tree_and_verify(root))
            self.assertFalse(root.exists())


    def test_transient_unit_evidence_classifies_systemd_oom(self):
        responses = [
            SimpleNamespace(
                returncode=0,
                stdout=(
                    "Result=oom-kill\n"
                    "ExecMainCode=2\n"
                    "ExecMainStatus=9\n"
                ),
                stderr="",
            ),
            SimpleNamespace(returncode=0, stdout="", stderr=""),
        ]
        commands = []
        original = runtime.run

        def fake_run(argv, check=True):
            commands.append(argv)
            return responses.pop(0)

        runtime.run = fake_run
        try:
            evidence = runtime.transient_unit_terminal_evidence(
                "workspace-ci-test.service"
            )
        finally:
            runtime.run = original

        self.assertTrue(evidence["available"])
        self.assertEqual(evidence["result"], "oom-kill")
        self.assertEqual(evidence["exec_main_code"], "2")
        self.assertEqual(evidence["exec_main_status"], "9")
        self.assertTrue(
            runtime.systemd_proves_cpu_or_ram_exhaustion(evidence)
        )
        self.assertEqual(
            commands[-1],
            ["systemctl", "reset-failed", "workspace-ci-test.service"],
        )

    def test_non_oom_systemd_failure_is_not_resource_exhaustion(self):
        evidence = {
            "available": True,
            "result": "exit-code",
            "exec_main_code": "1",
            "exec_main_status": "42",
        }
        self.assertFalse(
            runtime.systemd_proves_cpu_or_ram_exhaustion(evidence)
        )

    def test_systemd_commands_preserve_failed_unit_for_terminal_evidence(self):
        cpu = runtime.build_cpu_systemd_command(
            {
                **self.gpu_spec(),
                "profile": "cpu-test",
                "resources": {
                    **self.gpu_spec()["resources"],
                    "gpu_indices": [],
                    "gpu_uuid": None,
                },
            },
            pathlib.Path("/tmp/runner"),
            pathlib.Path("/tmp/staging"),
            "134.88.12.0/22",
        )
        gpu = runtime.build_gpu_systemd_command(
            self.gpu_spec(),
            pathlib.Path("/tmp/runner"),
            pathlib.Path("/tmp/staging"),
            "134.88.12.0/22",
            self.assignment(),
        )
        self.assertNotIn("--collect", cpu)
        self.assertNotIn("--collect", gpu)

    def test_wrapper_timeout_stops_unit_and_reaps_systemd_run(self):
        class FakeProc:
            def __init__(self):
                self.returncode = None
                self.wait_calls = []
                self.terminate_called = False
                self.kill_called = False

            def wait(self, timeout=None):
                self.wait_calls.append(timeout)
                if len(self.wait_calls) == 1:
                    raise runtime.subprocess.TimeoutExpired(
                        cmd="systemd-run",
                        timeout=timeout,
                    )
                self.returncode = 143
                return self.returncode

            def poll(self):
                return self.returncode

            def terminate(self):
                self.terminate_called = True

            def kill(self):
                self.kill_called = True

        proc = FakeProc()
        commands = []
        responses = [
            SimpleNamespace(returncode=0, stdout="", stderr=""),
            SimpleNamespace(returncode=3, stdout="inactive\n", stderr=""),
            SimpleNamespace(returncode=0, stdout="", stderr=""),
        ]
        original = runtime.run

        def fake_run(argv, check=True):
            commands.append(argv)
            return responses.pop(0)

        runtime.run = fake_run
        try:
            rc, timed_out, cleanup_pass = runtime.wait_for_transient_runner(
                proc,
                "workspace-ci-test.service",
                1,
            )
        finally:
            runtime.run = original

        self.assertEqual(rc, 143)
        self.assertTrue(timed_out)
        self.assertTrue(cleanup_pass)
        self.assertFalse(proc.terminate_called)
        self.assertFalse(proc.kill_called)
        self.assertEqual(
            commands,
            [
                ["systemctl", "stop", "workspace-ci-test.service"],
                ["systemctl", "is-active", "workspace-ci-test.service"],
                ["systemctl", "reset-failed", "workspace-ci-test.service"],
            ],
        )

    def test_wrapper_timeout_cleanup_fails_if_wrapper_or_unit_survives(self):
        class StuckProc:
            def wait(self, timeout=None):
                raise runtime.subprocess.TimeoutExpired(
                    cmd="systemd-run",
                    timeout=timeout,
                )

            def poll(self):
                return None

            def terminate(self):
                pass

            def kill(self):
                pass

        proc = StuckProc()
        responses = [
            SimpleNamespace(returncode=0, stdout="", stderr=""),
            SimpleNamespace(returncode=0, stdout="active\n", stderr=""),
            SimpleNamespace(returncode=0, stdout="", stderr=""),
        ]
        original = runtime.run
        runtime.run = lambda argv, check=True: responses.pop(0)
        try:
            rc, timed_out, cleanup_pass = runtime.wait_for_transient_runner(
                proc,
                "workspace-ci-test.service",
                1,
            )
        finally:
            runtime.run = original

        self.assertIsNone(rc)
        self.assertTrue(timed_out)
        self.assertFalse(cleanup_pass)

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
