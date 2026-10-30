import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


compiler = load(
    "lambda_ci_policy_compiler_offline_runtime",
    SCRIPTS / "lambda_ci_policy_compiler.py",
)
v3spec = load(
    "lambda_ci_v3_spec_offline_runtime",
    SCRIPTS / "lambda_ci_v3_spec.py",
)
runtime = load(
    "lambda_ci_runtime_offline_runtime",
    SCRIPTS / "lambda_ci_runtime.py",
)


class V3OfflineRuntimeBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiled = compiler.compile_policy(ROOT)
        cls.root = compiled["root_projection"]
        cls.request_id = "11111111-2222-3333-4444-555555555555"

    def build(self, class_id):
        cls = self.root["runner_classes"][class_id]
        _, spec = v3spec.build_launch_spec(
            root_projection=self.root,
            runner_class_id=class_id,
            request_id=self.request_id,
            runner_name=cls["runner_prefix"] + "offline-runtime-test",
            jit_config="ZmFrZS1qaXQ=",
        )
        return spec

    def assignment(self, spec):
        uuids = list(spec["resources"]["gpu_uuids"])
        devices = [f"/dev/nvidia{i}" for i in range(len(uuids))]
        denied = ["/dev/nvidia1"] if len(uuids) == 1 else []
        return {
            "target_uuid": uuids[0],
            "selected_device": devices[0],
            "selected_minor": 0,
            "target_uuids": uuids,
            "selected_devices": devices,
            "selected_minors": list(range(len(uuids))),
            "denied_devices": denied,
            "support_devices": ["/dev/nvidia-uvm", "/dev/nvidia-uvm-tools"],
            "inventory": [],
        }

    @staticmethod
    def props(command):
        return [
            command[index + 1]
            for index, value in enumerate(command[:-1])
            if value == "-p"
        ]

    def paths(self, spec):
        job = pathlib.Path(spec["paths"]["job_root"]) / f"p5-{self.request_id}"
        staging = (
            pathlib.Path(spec["paths"]["staging_cache"]) / f"p5-{self.request_id}"
        )
        socket_dir = pathlib.Path(spec["offline_payload_broker"]["socket_root"]) / self.request_id
        return job, staging, socket_dir, socket_dir / "exec.sock"

    def test_online_runner_has_github_plane_but_no_gpu_or_model_runtime_mount(self):
        for class_id in (
            "research-model-single-offline-v1",
            "research-model-dual-offline-v1",
        ):
            spec = self.build(class_id)
            assignment = self.assignment(spec)
            job, staging, _socket_dir, socket_path = self.paths(spec)
            command = runtime.build_gpu_systemd_command(
                spec,
                job / "runner",
                staging,
                "192.0.2.0/24",
                assignment,
                payload_socket_path=socket_path,
            )
            props = self.props(command)
            self.assertIn("DevicePolicy=closed", props)
            self.assertFalse(
                any(value.startswith("DeviceAllow=/dev/nvidia") for value in props),
                class_id,
            )
            self.assertIn(f"InaccessiblePaths={spec['runtime_binding']['canonical_path']}", props)
            self.assertIn(f"InaccessiblePaths={spec['model_binding']['object_path']}", props)
            self.assertNotIn(
                f"BindReadOnlyPaths={spec['runtime_binding']['canonical_path']}",
                props,
            )
            self.assertNotIn(
                f"ReadOnlyPaths={spec['model_binding']['object_path']}",
                props,
            )
            self.assertIn(f"Environment=P5_PAYLOAD_EXEC_SOCKET={socket_path}", props)
            self.assertIn(
                f"Environment=P5_PAYLOAD_EXEC_CLIENT={spec['offline_payload_broker']['client_path']}",
                props,
            )
            self.assertIn("Environment=P5_PAYLOAD_EXEC_REQUIRED=1", props)
            self.assertIn("CPUQuota=200%", props)
            self.assertIn(f"MemoryMax={4 * 1024**3}", props)
            self.assertIn("TasksMax=1024", props)
            self.assertIn("Environment=CUDA_VISIBLE_DEVICES=", props)
            self.assertIn("ProcSubset=pid", props)
            self.assertIn(
                "RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6",
                props,
            )
            self.assertNotIn(
                "RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6 AF_NETLINK",
                props,
            )

    def test_broker_is_private_network_gpu_holder_with_clean_environment(self):
        for class_id in (
            "research-model-single-offline-v1",
            "research-model-dual-offline-v1",
        ):
            spec = self.build(class_id)
            assignment = self.assignment(spec)
            job, staging, socket_dir, socket_path = self.paths(spec)
            command = runtime.build_offline_payload_broker_systemd_command(
                spec,
                job,
                staging,
                socket_dir,
                socket_path,
                assignment,
                43210,
            )
            props = self.props(command)
            self.assertIn("PrivateNetwork=yes", props)
            self.assertIn("IPAddressDeny=any", props)
            self.assertIn(
                "RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6 AF_NETLINK",
                props,
            )
            self.assertIn("IPAddressAllow=127.0.0.0/8", props)
            self.assertIn("IPAddressAllow=::1/128", props)
            self.assertIn("DeviceAllow=/dev/nvidiactl rw", props)
            for device in assignment["selected_devices"] + assignment["support_devices"]:
                self.assertIn(f"DeviceAllow={device} rw", props)
            self.assertIn(
                f"BindReadOnlyPaths={spec['runtime_binding']['canonical_path']}",
                props,
            )
            self.assertIn(
                f"ReadOnlyPaths={spec['model_binding']['object_path']}",
                props,
            )
            env_index = command.index("/usr/bin/env")
            self.assertEqual(command[env_index + 1], "-i")
            self.assertNotIn("GH_TOKEN", " ".join(command))
            self.assertNotIn("GITHUB_TOKEN", " ".join(command))
            self.assertNotIn("ACTIONS_RUNTIME_TOKEN", " ".join(command))
            self.assertIn("--expected-runner-unit", command)
            self.assertIn(spec["unit_name"], command)

    def test_runner_plus_broker_never_exceeds_root_granted_job_envelope(self):
        for class_id in (
            "research-model-single-offline-v1",
            "research-model-dual-offline-v1",
        ):
            spec = self.build(class_id)
            split = runtime._offline_payload_resource_split(spec["resources"])
            self.assertEqual(
                split["runner_cpu_quota_percent"] + split["broker_cpu_quota_percent"],
                spec["resources"]["cpu_quota_percent"],
            )
            self.assertEqual(
                split["runner_memory_max_bytes"] + split["broker_memory_max_bytes"],
                spec["resources"]["memory_max_bytes"],
            )
            self.assertEqual(
                split["runner_tasks_max"] + split["broker_tasks_max"],
                spec["resources"]["tasks_max"],
            )

    def test_public_gpu_runner_keeps_direct_gpu_and_has_no_broker_socket(self):
        spec = self.build("padataset-gpu-single-public-v1")
        assignment = self.assignment(spec)
        job = pathlib.Path(spec["paths"]["job_root"]) / f"p5-{self.request_id}"
        staging = pathlib.Path(spec["paths"]["staging_cache"]) / f"p5-{self.request_id}"
        command = runtime.build_gpu_systemd_command(
            spec,
            job / "runner",
            staging,
            "192.0.2.0/24",
            assignment,
        )
        props = self.props(command)
        self.assertIn("DeviceAllow=/dev/nvidiactl rw", props)
        self.assertIn("DeviceAllow=/dev/nvidia0 rw", props)
        self.assertFalse(any("P5_PAYLOAD_EXEC_SOCKET" in value for value in props))
        self.assertIn(
            f"CPUQuota={spec['resources']['cpu_quota_percent']}%",
            props,
        )


if __name__ == "__main__":
    unittest.main()
