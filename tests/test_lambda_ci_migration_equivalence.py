import copy
import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

compiler_spec = importlib.util.spec_from_file_location(
    "lambda_ci_policy_compiler",
    ROOT / "scripts" / "lambda_ci_policy_compiler.py",
)
compiler = importlib.util.module_from_spec(compiler_spec)
assert compiler_spec.loader is not None
sys.modules["lambda_ci_policy_compiler"] = compiler
compiler_spec.loader.exec_module(compiler)

eq_spec = importlib.util.spec_from_file_location(
    "lambda_ci_migration_equivalence",
    ROOT / "scripts" / "lambda_ci_migration_equivalence.py",
)
equivalence = importlib.util.module_from_spec(eq_spec)
assert eq_spec.loader is not None
sys.modules["lambda_ci_migration_equivalence"] = equivalence
eq_spec.loader.exec_module(equivalence)


class MigrationEquivalenceTests(unittest.TestCase):
    def test_all_23_routes_preserve_exact_root_launch_semantics(self):
        result = equivalence.verify_migration(ROOT)
        self.assertEqual(result["decision"], "PASS")
        self.assertEqual(result["route_count"], 23)
        self.assertEqual(result["exact_equivalence_count"], 23)

    def test_padataset_cpu_and_gpu_preserve_contracts(self):
        rows = equivalence.verify_migration(ROOT)["rows"]
        cpu = next(x for x in rows if x["project_id"] == "padataset" and x["route_id"] == "cpu-ci")
        gpu = next(x for x in rows if x["project_id"] == "padataset" and x["route_id"] == "gpu-ci")
        self.assertEqual(cpu["execution_contract_id"], "cpu-public-ci-v1")
        self.assertEqual(cpu["gpu_count"], 0)
        self.assertEqual(gpu["execution_contract_id"], "gpu-single-public-ci-v1")
        self.assertEqual(gpu["gpu_count"], 1)

    def test_workspace_control_preserves_control_small(self):
        row = next(
            x for x in equivalence.verify_migration(ROOT)["rows"]
            if x["project_id"] == "workspace-control"
        )
        self.assertEqual(row["execution_contract_id"], "control-small-ci-v1")
        self.assertEqual(row["gpu_count"], 0)

    def test_exact_provenance_moves_scale_set_without_gaining_gpu(self):
        row = next(
            x for x in equivalence.verify_migration(ROOT)["rows"]
            if x["project_id"] == "research-engine"
            and x["route_id"] == "cpu-validation-exact-provenance"
        )
        self.assertEqual(row["legacy_lane"], "gpu")
        self.assertEqual(row["legacy_scale_set_name"], "lambda-research-engine-gpu")
        self.assertEqual(row["target_runner_class_id"], "research-cpu-public-v1")
        self.assertEqual(row["gpu_count"], 0)

    def test_research_dual_public_routes_remain_dual_public(self):
        rows = [
            x for x in equivalence.verify_migration(ROOT)["rows"]
            if x["target_runner_class_id"] == "research-model-dual-public-v1"
        ]
        self.assertGreaterEqual(len(rows), 1)
        for row in rows:
            self.assertEqual(row["gpu_count"], 2)
            self.assertEqual(row["payload_network_class"], "PUBLIC")

    def test_semantic_drift_is_detected(self):
        data = compiler.load_inputs(ROOT)
        compiled = compiler.compile_from_inputs(copy.deepcopy(data))
        class_id = "padataset-gpu-single-public-v1"
        compiled["root_projection"]["runner_classes"][class_id][
            "execution_contract"
        ]["gpu_count"] = 2

        current = equivalence._current_route_envelope(
            data,
            project_id="padataset",
            route_id="gpu-ci",
        )
        target = equivalence._target_route_envelope(
            compiled,
            class_id=class_id,
        )
        self.assertNotEqual(current, target)

    def test_network_drift_is_detectable_as_authority_change(self):
        data = compiler.load_inputs(ROOT)
        compiled = compiler.compile_from_inputs(copy.deepcopy(data))
        class_id = "research-model-single-offline-v1"
        target = compiled["root_projection"]["runner_classes"][class_id]
        self.assertEqual(
            target["execution_contract"]["payload_network_class"],
            "OFFLINE",
        )
        target["execution_contract"]["payload_network_class"] = "PUBLIC"

        current = equivalence._current_route_envelope(
            data,
            project_id="research-engine",
            route_id="model-eval-single-gpu",
        )
        changed = equivalence._target_route_envelope(
            compiled,
            class_id=class_id,
        )
        self.assertNotEqual(current, changed)
        self.assertEqual(
            current["execution_contract"]["payload_network_class"],
            "OFFLINE",
        )
        self.assertEqual(
            changed["execution_contract"]["payload_network_class"],
            "PUBLIC",
        )


if __name__ == "__main__":
    unittest.main()
