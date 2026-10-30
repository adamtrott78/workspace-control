import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


compiler = load(
    "lambda_ci_policy_compiler",
    ROOT / "scripts" / "lambda_ci_policy_compiler.py",
)
v3spec = load(
    "lambda_ci_v3_spec",
    ROOT / "scripts" / "lambda_ci_v3_spec.py",
)


class V3LaunchSpecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compiled = compiler.compile_policy(ROOT)
        cls.root = cls.compiled["root_projection"]

    def build(self, class_id, *, suffix="spec"):
        cls = self.root["runner_classes"][class_id]
        return v3spec.build_launch_spec(
            root_projection=self.root,
            runner_class_id=class_id,
            request_id="11111111-2222-3333-4444-555555555555",
            runner_name=cls["runner_prefix"] + suffix,
            jit_config="ZmFrZS1qaXQ=",
        )

    def test_all_nine_runner_classes_build(self):
        self.assertEqual(len(self.root["runner_classes"]), 9)
        for class_id in sorted(self.root["runner_classes"]):
            request, spec = self.build(class_id)
            cls = self.root["runner_classes"][class_id]
            self.assertEqual(spec["runner_class_id"], class_id)
            self.assertEqual(spec["profile"], cls["execution_contract"]["execution_profile"])
            self.assertEqual(spec["execution_contract"], cls["execution_contract"])
            self.assertEqual(spec["model_binding"], cls["bindings"]["model"])
            self.assertEqual(spec["runtime_binding"], cls["bindings"]["runtime"])
            self.assertEqual(spec["root_policy_sha256"], self.root["root_policy_sha256"])
            self.assertEqual(spec["root_envelope_sha256"], cls["root_envelope_sha256"])
            self.assertEqual(request.jit_config, "ZmFrZS1qaXQ=")

    def test_control_small_remains_exact_control_small(self):
        _, spec = self.build("workspace-control-control-small-v1")
        self.assertEqual(spec["profile"], "control-small")
        self.assertEqual(spec["execution_contract"]["execution_profile"], "control-small")
        self.assertEqual(spec["resources"]["gpu_uuids"], [])

    def test_gpu_cardinality_matches_contract_for_every_class(self):
        for class_id in self.root["runner_classes"]:
            _, spec = self.build(class_id)
            self.assertEqual(
                len(spec["resources"]["gpu_uuids"]),
                spec["execution_contract"]["gpu_count"],
                class_id,
            )
            self.assertEqual(
                spec["resources"]["gpu_indices"],
                list(range(spec["execution_contract"]["gpu_count"])),
                class_id,
            )

    def test_dual_gpu_class_uses_exact_two_uuid_set(self):
        _, spec = self.build("research-model-dual-public-v1")
        self.assertEqual(
            spec["resources"]["gpu_uuids"],
            [
                "GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea",
                "GPU-cfed3394-a935-63aa-9325-c4cae7b568b6",
            ],
        )
        self.assertIsNone(spec["resources"]["gpu_uuid"])

    def test_single_gpu_class_uses_singular_and_plural_same_uuid(self):
        _, spec = self.build("padataset-gpu-single-public-v1")
        self.assertEqual(len(spec["resources"]["gpu_uuids"]), 1)
        self.assertEqual(
            spec["resources"]["gpu_uuid"],
            spec["resources"]["gpu_uuids"][0],
        )

    def test_runner_release_is_bound_from_root_projection(self):
        _, spec = self.build("padataset-cpu-public-v1")
        pin = self.root["upstream_pins"]["actions_runner"]
        self.assertEqual(spec["runner"]["version"], pin["version"])
        self.assertEqual(spec["runner"]["asset_name"], pin["asset_name"])
        self.assertEqual(spec["runner"]["sha256"], pin["linux_x64_sha256"])

    def test_root_spec_has_no_job_or_ingress_semantics(self):
        _, spec = self.build("research-model-dual-public-v1")
        text = repr(spec)
        for forbidden in [
            "job_display_name",
            "candidate_sha",
            "pull_request",
            "workflow_path",
            "/lambda-ci-",
            "/workspace-control-validate",
        ]:
            self.assertNotIn(forbidden, text)

    def test_wrong_runner_prefix_fails(self):
        with self.assertRaisesRegex(v3spec.V3SpecError, "immutable class prefix"):
            v3spec.build_launch_spec(
                root_projection=self.root,
                runner_class_id="workspace-control-control-small-v1",
                request_id="11111111-2222-3333-4444-555555555555",
                runner_name="lambda-research-engine-evil",
                jit_config="ZmFrZS1qaXQ=",
            )

    def test_unknown_class_fails(self):
        with self.assertRaisesRegex(v3spec.V3SpecError, "unknown runner class"):
            v3spec.build_launch_spec(
                root_projection=self.root,
                runner_class_id="infinite-gpu-v1",
                request_id="11111111-2222-3333-4444-555555555555",
                runner_name="lambda-infinite-gpu-v1-x",
                jit_config="ZmFrZS1qaXQ=",
            )

    def test_systemd_profile_and_resource_ceiling_are_root_owned(self):
        for class_id in sorted(self.root["runner_classes"]):
            _, spec = self.build(class_id)
            cls = self.root["runner_classes"][class_id]
            self.assertEqual(spec["systemd_profile"], cls["systemd_profile"], class_id)
            self.assertEqual(
                spec["resources"]["tasks_max"],
                int(cls["systemd_profile"]["TasksMax"]),
                class_id,
            )
            self.assertEqual(
                spec["resources"]["runtime_max_seconds"],
                min(
                    v3spec._parse_runtime_seconds(
                        cls["systemd_profile"]["RuntimeMaxSec"]
                    ),
                    int(cls["resource_class"]["max_runtime_seconds"]),
                ),
                class_id,
            )

    def test_runtime_and_model_bindings_are_exact_materialized_project_objects(self):
        manifests = compiler.load_inputs(ROOT)["project_manifests"]
        research = manifests["research-engine"]
        for class_id, cls in self.root["runner_classes"].items():
            if cls["project_id"] != "research-engine":
                continue
            model = cls["bindings"]["model"]
            runtime = cls["bindings"]["runtime"]
            catalog_class = self.compiled["root_projection"]["runner_classes"][class_id]
            if model is not None:
                self.assertIn(model["model_id"], research["bindings"]["models"])
                self.assertEqual(
                    model,
                    research["bindings"]["models"][model["model_id"]],
                    class_id,
                )
                self.assertIn("object_path", model)
                self.assertIn("descriptor_sha256", model)
            if runtime is not None:
                self.assertIn(runtime["runtime_id"], research["bindings"]["runtimes"])
                self.assertEqual(
                    runtime,
                    research["bindings"]["runtimes"][runtime["runtime_id"]],
                    class_id,
                )
                self.assertEqual(
                    runtime["python_path"],
                    runtime["canonical_path"] + "/bin/python",
                )
                self.assertIn("source_trusted_runtime_object", runtime)
                self.assertTrue(runtime["required_controls"])
            self.assertEqual(catalog_class["bindings"], cls["bindings"])

    def test_only_offline_model_classes_receive_payload_broker(self):
        offline = {
            "research-model-single-offline-v1",
            "research-model-dual-offline-v1",
        }
        observed = set()
        for class_id in self.root["runner_classes"]:
            _, spec = self.build(class_id)
            broker = spec["offline_payload_broker"]
            if class_id in offline:
                observed.add(class_id)
                self.assertIsInstance(broker, dict)
                self.assertEqual(
                    broker["network_class"],
                    "GITHUB_CONTROL_PLANE_ONLY_PAYLOAD_OFFLINE",
                )
                self.assertEqual(
                    broker["runtime_python"],
                    spec["runtime_binding"]["python_path"],
                )
                self.assertEqual(
                    broker["run_as"],
                    self.root["runner_classes"][class_id][
                        "payload_broker_identity"
                    ],
                )
                self.assertNotEqual(
                    broker["run_as"]["user"],
                    spec["run_as"]["user"],
                )
                self.assertEqual(
                    broker["run_as"]["group"],
                    spec["run_as"]["group"],
                )
                self.assertTrue(
                    broker["broker_path"].startswith("/opt/workspace-ci/v3/payload/")
                )
                self.assertTrue(
                    broker["client_path"].startswith("/opt/workspace-ci/v3/payload/")
                )
                self.assertEqual(
                    broker["socket_root"],
                    "/run/workspace-ci-v3-payload",
                )
                socket_root = pathlib.PurePosixPath(broker["socket_root"])
                for forbidden_raw in spec["forbidden_paths"]:
                    forbidden = pathlib.PurePosixPath(forbidden_raw)
                    with self.subTest(class_id=class_id, forbidden=forbidden_raw):
                        try:
                            socket_root.relative_to(forbidden)
                        except ValueError:
                            pass
                        else:
                            self.fail(
                                "payload socket root nested under forbidden path "
                                f"{forbidden_raw}"
                            )
            else:
                self.assertIsNone(broker, class_id)
        self.assertEqual(observed, offline)

    def test_no_production_service_authority(self):
        for class_id in self.root["runner_classes"]:
            _, spec = self.build(class_id)
            self.assertFalse(spec["allow_production_services"])


if __name__ == "__main__":
    unittest.main()
