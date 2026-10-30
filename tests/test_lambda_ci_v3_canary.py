import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


compiler = load(
    "lambda_ci_policy_compiler_v3_canary_tests",
    ROOT / "scripts" / "lambda_ci_policy_compiler.py",
)
generator = load(
    "lambda_ci_v3_canary",
    ROOT / "scripts" / "lambda_ci_v3_canary.py",
)
probe = load(
    "lambda_ci_v3_canary_probe",
    ROOT / "scripts" / "lambda_ci_v3_canary_probe.py",
)


class V3MigrationCanaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = pathlib.Path(self.temp.name) / "generated"
        self.manifest = generator.generate(ROOT, self.output)
        self.compiled = compiler.compile_policy(ROOT)

    def test_exactly_nine_inert_owner_repo_workflows_and_policies(self):
        self.assertEqual(len(self.manifest["classes"]), 9)
        self.assertEqual(self.manifest["status"], "STAGED_NOT_INSTALLED_NOT_AUTHORIZED")
        self.assertFalse(self.manifest["ordinary_executor_action_catalog_modified"])
        for class_id, entry in self.manifest["classes"].items():
            owner, repo = entry["repository"].split("/", 1)
            workflow = (
                self.output
                / "repositories"
                / owner
                / repo
                / entry["workflow_path"]
            )
            policy = self.output / entry["controller_policy_path"]
            self.assertTrue(workflow.is_file(), class_id)
            self.assertTrue(policy.is_file(), class_id)
            self.assertEqual(
                generator.git_blob_sha(workflow.read_bytes()),
                entry["workflow_blob_sha"],
            )

    def test_workflows_have_no_inputs_checkout_or_candidate_authority(self):
        forbidden = (
            "actions/checkout",
            "candidate",
            "pull_request",
            "github.event.inputs",
            "inputs.",
            "workflow_call",
            "repository_dispatch",
        )
        for class_id, entry in self.manifest["classes"].items():
            owner, repo = entry["repository"].split("/", 1)
            raw = (
                self.output
                / "repositories"
                / owner
                / repo
                / entry["workflow_path"]
            ).read_text()
            self.assertIn("workflow_dispatch:", raw)
            self.assertIn("github.actor == 'adamtrott78'", raw)
            self.assertIn(f'runs-on: {entry["scale_set_name"]}', raw)
            self.assertIn(f'--expected-class "{class_id}"', raw)
            for token in forbidden:
                self.assertNotIn(token, raw.lower(), (class_id, token))

    def test_canary_controller_policy_replaces_not_extends_production_trust(self):
        for class_id, entry in self.manifest["classes"].items():
            policy = json.loads(
                (self.output / entry["controller_policy_path"]).read_text()
            )
            self.assertEqual(len(policy["trusted_workflows"]), 1)
            workflow = policy["trusted_workflows"][0]
            self.assertEqual(workflow["route_id"], f"migration-canary:{class_id}")
            self.assertEqual(workflow["allowed_events"], ["workflow_dispatch"])
            self.assertEqual(workflow["allowed_actor_logins"], ["adamtrott78"])
            self.assertEqual(workflow["blob_sha"], entry["workflow_blob_sha"])
            self.assertEqual(workflow["compile_time_top_level_job_count"], 1)
            expected_digest = compiler.sha256_object({
                key: value
                for key, value in policy.items()
                if key not in {
                    "control_plane_generation_sha256",
                    "controller_policy_sha256",
                }
            })
            self.assertEqual(policy["controller_policy_sha256"], expected_digest)

    def test_canaries_never_enter_ordinary_executor_catalog(self):
        executor = self.compiled["executor_projection"]
        encoded = json.dumps(executor, sort_keys=True)
        for class_id, entry in self.manifest["classes"].items():
            self.assertNotIn(f"migration-canary:{class_id}", encoded)
            self.assertNotIn(entry["workflow_path"], encoded)

    def test_migration_order_and_inherited_containment_are_preserved(self):
        ordered = sorted(
            self.manifest["classes"].items(),
            key=lambda item: item[1]["order"],
        )
        self.assertEqual(
            [entry["order"] for _, entry in ordered],
            list(range(1, 10)),
        )
        for class_id, entry in ordered[:4]:
            self.assertNotIn(
                "INHERITED_CONTAINMENT_REQUIRES_SEPARATE_AUTHORITY",
                entry["blockers"],
                class_id,
            )
        for class_id, entry in ordered[4:]:
            self.assertIn(
                "INHERITED_CONTAINMENT_REQUIRES_SEPARATE_AUTHORITY",
                entry["blockers"],
                class_id,
            )
            self.assertEqual(entry["authorization_state"], "BLOCKED")

    def _snapshot_for(self, cls):
        profile = cls["systemd_profile"]
        quota = int(str(profile["CPUQuota"])[:-1])
        period = 100000
        cpu_max = f"{quota * period // 100} {period}"
        resource = cls["resource_class"]
        gpu_uuids = list(resource.get("gpu_uuids", []))
        if resource.get("gpu_uuid") is not None:
            gpu_uuids = [resource["gpu_uuid"]]
        gpu_csv = ",".join(gpu_uuids)
        selected = [f"/dev/nvidia{index}" for index in range(len(gpu_uuids))]
        denied = ["/dev/nvidia7", "/dev/nvidia8"] if gpu_uuids else []
        roots = cls["project_roots"]
        rw = " ".join(str(roots[key]) for key in ("jobs", "staging_cache", "logs", "home"))
        ro = str(roots["trusted_cache"])
        inaccessible = " ".join(cls["forbidden_paths"])
        bind_ro = ""
        env = {
            "CUDA_VISIBLE_DEVICES": gpu_csv,
            "P5_GPU_TARGET_UUIDS": gpu_csv,
            "P5_GPU_SELECTED_DEVICES": ",".join(selected),
            "P5_GPU_DENIED_DEVICES": ",".join(denied),
        }
        runtime = cls["bindings"].get("runtime")
        if runtime is not None:
            env["P5_EXPANDED_RUNTIME"] = runtime["canonical_path"]
            bind_ro = runtime["canonical_path"]
        model = cls["bindings"].get("model")
        if model is not None:
            env["P5_MODEL_OBJECT_ROOT"] = model["object_path"]
            ro += " " + model["object_path"]
        return env, {
            "cpu.max": cpu_max,
            "memory.max": str(probe._memory_bytes(profile["MemoryMax"])),
            "pids.max": str(profile["TasksMax"]),
        }, {
            "RuntimeMaxUSec": (
                f"{min(probe._runtime_seconds(profile['RuntimeMaxSec']), int(resource['max_runtime_seconds']))}s"
            ),
            "ReadWritePaths": rw,
            "ReadOnlyPaths": ro,
            "InaccessiblePaths": inaccessible,
            "BindReadOnlyPaths": bind_ro,
            "DevicePolicy": "closed",
            "DeviceAllow": (
                " ".join(["/dev/nvidiactl", *selected])
                if gpu_uuids else ""
            ),
            "RestrictAddressFamilies": "AF_UNIX AF_INET AF_INET6 AF_NETLINK",
            "IPAddressAllow": "127.0.0.53/32",
            "IPAddressDeny": " ".join(probe.BASE_DENIES) + " 192.0.2.0/24",
        }

    def test_probe_accepts_all_public_network_class_snapshots(self):
        for class_id, cls in self.compiled["root_projection"]["runner_classes"].items():
            network = cls["execution_contract"]["payload_network_class"]
            if network != probe.PUBLIC_NETWORK:
                continue
            env, cgroup, unit = self._snapshot_for(cls)
            result = probe._verify_snapshot(
                cls,
                runner_name=cls["runner_prefix"] + "canary",
                env=env,
                cgroup=cgroup,
                unit=unit,
            )
            self.assertEqual(result["status"], "PASS", (class_id, result))

    def test_probe_fails_closed_for_offline_contract_until_network_isolation_exists(self):
        offline = []
        for class_id, cls in self.compiled["root_projection"]["runner_classes"].items():
            if cls["execution_contract"]["payload_network_class"] != probe.OFFLINE_NETWORK:
                continue
            offline.append(class_id)
            env, cgroup, unit = self._snapshot_for(cls)
            result = probe._verify_snapshot(
                cls,
                runner_name=cls["runner_prefix"] + "canary",
                env=env,
                cgroup=cgroup,
                unit=unit,
            )
            self.assertEqual(result["status"], "FAIL")
            self.assertIn(
                "offline_payload_network_isolation_implemented",
                result["failures"],
            )
            self.assertIn(
                "PAYLOAD_NETWORK_ISOLATION_UNIMPLEMENTED",
                self.manifest["classes"][class_id]["blockers"],
            )
        self.assertEqual(
            set(offline),
            {
                "research-model-single-offline-v1",
                "research-model-dual-offline-v1",
            },
        )


if __name__ == "__main__":
    unittest.main()
