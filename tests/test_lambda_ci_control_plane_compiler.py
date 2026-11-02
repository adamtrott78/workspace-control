import copy
import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "lambda_ci_policy_compiler.py"
spec = importlib.util.spec_from_file_location("lambda_ci_policy_compiler", MODULE_PATH)
compiler = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(compiler)


def recursive_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from recursive_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from recursive_keys(child)


class ControlPlanePolicyCompilerTests(unittest.TestCase):
    def setUp(self):
        self.inputs = compiler.load_inputs(ROOT)

    def compile(self, inputs=None):
        return compiler.compile_from_inputs(copy.deepcopy(inputs or self.inputs))

    def test_compiles_entire_registered_fleet(self):
        result = self.compile()
        self.assertEqual(len(result["root_projection"]["runner_classes"]), 9)
        self.assertEqual(len(result["controller_projections"]), 9)
        self.assertEqual(len(result["compatibility_matrix"]), 23)
        self.assertEqual(
            len(result["executor_projection"]["execution_actions"]),
            23,
        )
        self.assertEqual(
            len(result["executor_projection"]["maintenance_actions"]),
            4,
        )
        self.assertRegex(result["catalog_generation_sha256"], r"^[0-9a-f]{64}$")

    def test_root_projection_contains_no_ingress_or_job_parser_fields(self):
        result = self.compile()
        root = result["root_projection"]
        keys = set(recursive_keys(root))
        for forbidden in {
            "command",
            "candidate_sha",
            "pull_request_number",
            "job_display_name",
            "workload_class",
            "route_id",
            "parameter_schema_id",
            "jit_config",
        }:
            self.assertNotIn(forbidden, keys)
        text = json.dumps(root, sort_keys=True)
        self.assertNotIn("wc-admission-v1", text)
        self.assertNotIn("/workspace-control-validate", text)

    def test_controller_projection_has_no_root_selector_or_command_grammar(self):
        result = self.compile()
        for class_id, projection in result["controller_projections"].items():
            keys = set(recursive_keys(projection))
            self.assertNotIn("execution_contract_id", keys, class_id)
            self.assertNotIn("resource_class", keys, class_id)
            self.assertNotIn("command", keys, class_id)
            self.assertNotIn("candidate_sha", keys, class_id)
            self.assertNotIn("job_display_name", keys, class_id)

    def test_every_route_in_one_class_has_same_root_envelope_digest(self):
        result = self.compile()
        by_class = {}
        for row in result["compatibility_matrix"]:
            by_class.setdefault(row["target_runner_class_id"], set()).add(
                row["root_envelope_sha256"]
            )
        self.assertEqual(set(by_class), set(result["root_projection"]["runner_classes"]))
        for class_id, digests in by_class.items():
            self.assertEqual(len(digests), 1, class_id)

    def test_controller_unix_users_scale_sets_and_prefixes_are_unique(self):
        result = self.compile()
        classes = result["root_projection"]["runner_classes"].values()
        users = [x["controller_peer"]["unix_user"] for x in classes]
        scale_sets = [x["scale_set_name"] for x in classes]
        prefixes = [x["runner_prefix"] for x in classes]
        self.assertEqual(len(users), len(set(users)))
        self.assertEqual(len(scale_sets), len(set(scale_sets)))
        self.assertEqual(len(prefixes), len(set(prefixes)))

    def test_offline_payload_broker_identity_is_distinct_and_root_owned(self):
        result = self.compile()
        classes = result["root_projection"]["runner_classes"]
        offline = {
            "research-model-single-offline-v1",
            "research-model-dual-offline-v1",
        }
        broker_users = set()
        for class_id, cls in classes.items():
            identity = cls["payload_broker_identity"]
            if class_id in offline:
                self.assertTrue(identity["user"].startswith("ci-payload-"))
                self.assertLessEqual(len(identity["user"]), 32)
                self.assertEqual(identity["group"], cls["project_runner_identity"]["group"])
                self.assertNotEqual(
                    identity["user"],
                    cls["project_runner_identity"]["user"],
                )
                self.assertNotEqual(
                    identity["user"],
                    cls["controller_peer"]["unix_user"],
                )
                broker_users.add(identity["user"])
            else:
                self.assertIsNone(identity, class_id)
        self.assertEqual(len(broker_users), 2)

    def test_duplicate_controller_peer_fails_compile(self):
        inputs = copy.deepcopy(self.inputs)
        projects = inputs["catalog"]["projects"]
        wc = projects["workspace-control"]["runner_classes"]["workspace-control-control-small-v1"]
        pad = projects["padataset"]["runner_classes"]["padataset-cpu-public-v1"]
        pad["controller_peer"]["unix_user"] = wc["controller_peer"]["unix_user"]
        with self.assertRaisesRegex(compiler.CompileError, "duplicate controller unix user"):
            self.compile(inputs)

    def test_workflow_blob_drift_fails_compile(self):
        inputs = copy.deepcopy(self.inputs)
        entry = inputs["workflow_evidence"]["entries"][0]
        entry["workflow_blob_sha"] = "0" * 40
        with self.assertRaisesRegex(compiler.CompileError, "workflow blob mismatch"):
            self.compile(inputs)

    def test_workflow_shape_drift_fails_compile(self):
        inputs = copy.deepcopy(self.inputs)
        inputs["workflow_evidence"]["entries"][0]["top_level_job_count"] = 2
        with self.assertRaisesRegex(compiler.CompileError, "must have one top-level job"):
            self.compile(inputs)

    def test_target_scale_set_mismatch_fails_compile(self):
        inputs = copy.deepcopy(self.inputs)
        inputs["workflow_evidence"]["entries"][0]["target_scale_set_name"] = "lambda-wrong"
        with self.assertRaisesRegex(compiler.CompileError, "target scale set differs"):
            self.compile(inputs)

    def test_missing_ingress_parameter_schema_fails_compile(self):
        inputs = copy.deepcopy(self.inputs)
        route = inputs["catalog"]["projects"]["workspace-control"]["routes"]["control-validation"]
        route["ingress"]["parameter_schema_id"] = "not-a-schema"
        with self.assertRaisesRegex(compiler.CompileError, "missing parameter schema"):
            self.compile(inputs)

    def test_gpu_claims_are_derived_from_resource_policy_not_executor_input(self):
        result = self.compile()
        classes = result["root_projection"]["runner_classes"]
        self.assertEqual(
            classes["research-model-dual-public-v1"]["exclusive_resource_claims"],
            [
                "gpu:GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea",
                "gpu:GPU-cfed3394-a935-63aa-9325-c4cae7b568b6",
            ],
        )
        self.assertEqual(
            classes["research-cpu-public-v1"]["exclusive_resource_claims"],
            [],
        )

    def test_execution_parameter_schema_cannot_select_runner_class(self):
        inputs = copy.deepcopy(self.inputs)
        schema = inputs["parameter_schemas"]["schemas"]["candidate-sha-v1"]
        schema["arguments"].append({
            "name": "runner_class_id",
            "type": "catalog_runner_class_id",
            "required": True,
        })
        with self.assertRaisesRegex(
            compiler.CompileError,
            "execution ingress cannot select infrastructure identity",
        ):
            self.compile(inputs)

    def test_execution_parameter_schema_rejects_root_authority_names(self):
        inputs = copy.deepcopy(self.inputs)
        schema = inputs["parameter_schemas"]["schemas"]["candidate-sha-v1"]
        schema["arguments"].append({
            "name": "gpu_profile",
            "type": "enum",
            "required": True,
            "values": ["small", "heavy"],
        })
        with self.assertRaisesRegex(
            compiler.CompileError,
            "argument name implies root authority",
        ):
            self.compile(inputs)

    def test_actions_runner_pin_is_root_authority(self):
        baseline = self.compile()
        inputs = copy.deepcopy(self.inputs)
        runner = inputs["upstream_pins"]["actions_runner"]
        runner["linux_x64_sha256"] = "f" * 64
        changed = self.compile(inputs)
        self.assertNotEqual(
            baseline["root_projection"]["root_policy_sha256"],
            changed["root_projection"]["root_policy_sha256"],
        )
        self.assertEqual(
            baseline["controller_policy_digests"],
            changed["controller_policy_digests"],
        )
        self.assertEqual(
            baseline["executor_projection"]["executor_policy_sha256"],
            changed["executor_projection"]["executor_policy_sha256"],
        )

    def test_ingress_command_change_does_not_change_root_or_controller_policy(self):
        baseline = self.compile()
        inputs = copy.deepcopy(self.inputs)
        route = inputs["catalog"]["projects"]["workspace-control"]["routes"]["control-validation"]
        route["ingress"]["command"] = "/workspace-control-validate-v3"
        changed = self.compile(inputs)

        self.assertNotEqual(
            baseline["catalog_generation_sha256"],
            changed["catalog_generation_sha256"],
        )
        self.assertEqual(
            baseline["root_projection"]["root_policy_sha256"],
            changed["root_projection"]["root_policy_sha256"],
        )
        self.assertEqual(
            baseline["controller_policy_digests"],
            changed["controller_policy_digests"],
        )
        self.assertNotEqual(
            baseline["executor_projection"]["executor_policy_sha256"],
            changed["executor_projection"]["executor_policy_sha256"],
        )

    def test_executor_enum_change_does_not_change_root_or_controller_policy(self):
        baseline = self.compile()
        inputs = copy.deepcopy(self.inputs)
        schema = inputs["parameter_schemas"]["schemas"]["candidate-sha-reasoner-probe-v1"]
        enum_arg = next(arg for arg in schema["arguments"] if arg["name"] == "candidate_id")
        enum_arg["values"] = [
            "qwen35-9b-q6-resource",
            "qwythos-9b-v2-q6-resource",
            "future-diagnostic-only",
        ]
        changed = self.compile(inputs)
        self.assertEqual(
            baseline["root_projection"]["root_policy_sha256"],
            changed["root_projection"]["root_policy_sha256"],
        )
        self.assertEqual(
            baseline["controller_policy_digests"],
            changed["controller_policy_digests"],
        )
        self.assertNotEqual(
            baseline["executor_projection"]["executor_policy_sha256"],
            changed["executor_projection"]["executor_policy_sha256"],
        )

    def test_reasoner_selector_is_executor_only(self):
        result = self.compile()
        action = result["executor_projection"]["execution_actions"][
            "research_engine.gpu_experiment_public"
        ]
        candidate = next(x for x in action["arguments"] if x["name"] == "candidate_id")
        self.assertEqual(
            candidate["values"],
            ["qwen35-9b-q6-resource", "qwythos-9b-v2-q6-resource"],
        )
        root = json.dumps(result["root_projection"], sort_keys=True)
        self.assertNotIn("qwen35-9b-q6-resource", root)
        self.assertNotIn("qwythos-9b-v2-q6-resource", root)

    def test_exact_provenance_cpu_route_moves_off_legacy_gpu_pool_without_gpu_claim(self):
        result = self.compile()
        row = next(
            x for x in result["compatibility_matrix"]
            if x["project_id"] == "research-engine"
            and x["route_id"] == "cpu-validation-exact-provenance"
        )
        self.assertEqual(row["legacy_scale_set_name"], "lambda-research-engine-gpu")
        self.assertEqual(row["target_runner_class_id"], "research-cpu-public-v1")
        target = result["root_projection"]["runner_classes"][row["target_runner_class_id"]]
        self.assertEqual(target["exclusive_resource_claims"], [])
        self.assertEqual(target["execution_contract"]["gpu_count"], 0)

    def test_emitted_projection_schema_drift_fails_compile(self):
        inputs = copy.deepcopy(self.inputs)
        inputs["controller_projection_schema"]["required"].append("invented_required_field")
        with self.assertRaisesRegex(
            compiler.CompileError,
            "missing required keys",
        ):
            self.compile(inputs)

    def test_compiler_output_is_deterministic(self):
        first = self.compile()
        second = self.compile()
        self.assertEqual(first, second)

    def test_output_writer_emits_nonsecret_projection_files(self):
        compiled = self.compile()
        with tempfile.TemporaryDirectory() as td:
            out = pathlib.Path(td)
            compiler._write_outputs(compiled, out)
            receipt = json.loads((out / "compilation-receipt.json").read_text())
            self.assertEqual(receipt["decision"], "PASS")
            self.assertEqual(receipt["runner_class_count"], 9)
            self.assertEqual(receipt["route_count"], 23)
            root_text = (out / "root-policy.json").read_text()
            self.assertNotIn("jit_config", root_text)
            self.assertNotIn("candidate_sha", root_text)


if __name__ == "__main__":
    unittest.main()
