import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

compiler_spec = importlib.util.spec_from_file_location(
    "lambda_ci_policy_compiler",
    ROOT / "scripts" / "lambda_ci_policy_compiler.py",
)
compiler = importlib.util.module_from_spec(compiler_spec)
assert compiler_spec.loader is not None
compiler_spec.loader.exec_module(compiler)

builder_spec = importlib.util.spec_from_file_location(
    "lambda_ci_executor_builder",
    ROOT / "scripts" / "lambda_ci_executor_builder.py",
)
builder = importlib.util.module_from_spec(builder_spec)
assert builder_spec.loader is not None
# Make the compiler module importable by the builder's normal import statement.
import sys
sys.modules["lambda_ci_policy_compiler"] = compiler
builder_spec.loader.exec_module(builder)


class ExecutorBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compiled = compiler.compile_policy(ROOT)

    def test_catalog_exposes_every_compiled_action(self):
        actions = builder.list_actions(compiled=self.compiled)
        self.assertEqual(len(actions), 27)
        self.assertEqual(len(set(actions)), 27)
        self.assertIn("workspace_control.control_validation", actions)
        self.assertIn("padataset.cpu_ci", actions)
        self.assertIn("padataset.gpu_ci", actions)
        self.assertIn("research_engine.model_eval_local_extract_wave7a3", actions)
        self.assertIn("maintenance.host_attest", actions)

    def test_standard_execution_action_renders_exact_two_token_ingress(self):
        sha = "a" * 40
        result = builder.build_action(
            "workspace_control.control_validation",
            {"candidate_sha": sha},
            compiled=self.compiled,
        )
        self.assertEqual(result["kind"], "EXECUTION_TRIGGER")
        self.assertEqual(
            result["rendered_comment"],
            f"/workspace-control-validate {sha}",
        )
        self.assertNotIn("runner_class_id", result["arguments"])
        self.assertNotIn("root_operation", result)

    def test_padataset_actions_are_typed_first_class_actions(self):
        sha = "b" * 40
        cpu = builder.build_action(
            "padataset.cpu_ci",
            {"candidate_sha": sha},
            compiled=self.compiled,
        )
        gpu = builder.build_action(
            "padataset.gpu_ci",
            {"candidate_sha": sha},
            compiled=self.compiled,
        )
        self.assertEqual(cpu["rendered_comment"], f"/lambda-ci-cpu {sha}")
        self.assertEqual(gpu["rendered_comment"], f"/lambda-ci-gpu {sha}")

    def test_reasoner_probe_accepts_only_frozen_enum(self):
        sha = "c" * 40
        good = builder.build_action(
            "research_engine.gpu_experiment_public",
            {
                "candidate_sha": sha,
                "candidate_id": "qwen35-9b-q6-resource",
            },
            compiled=self.compiled,
        )
        self.assertEqual(
            good["rendered_comment"],
            f"/lambda-reasoner-probe {sha} qwen35-9b-q6-resource",
        )
        with self.assertRaisesRegex(builder.BuilderError, "allowed enum"):
            builder.build_action(
                "research_engine.gpu_experiment_public",
                {"candidate_sha": sha, "candidate_id": "gpu-heavy-please"},
                compiled=self.compiled,
            )

    def test_host_attest_exists_only_as_maintenance_action(self):
        class_id = "workspace-control-control-small-v1"
        result = builder.build_action(
            "maintenance.host_attest",
            {"runner_class_id": class_id},
            compiled=self.compiled,
        )
        self.assertEqual(result["kind"], "MAINTENANCE")
        self.assertEqual(result["authority"], "READ_ONLY")
        self.assertEqual(result["root_operation"], "HOST_ATTEST_RUNNER_CLASS")
        self.assertEqual(
            result["rendered_comment"],
            f"/workspace-ci-maintain host-attest {class_id}",
        )
        execution_text = str(self.compiled["executor_projection"]["execution_actions"])
        self.assertNotIn("host-attest", execution_text)

    def test_unknown_action_fails_before_render(self):
        with self.assertRaisesRegex(builder.BuilderError, "unknown action_id"):
            builder.build_action(
                "research_engine.make_up_a_gpu_job",
                {"candidate_sha": "d" * 40},
                compiled=self.compiled,
            )

    def test_unknown_or_missing_arguments_fail(self):
        with self.assertRaisesRegex(builder.BuilderError, "missing required"):
            builder.build_action(
                "padataset.cpu_ci",
                {},
                compiled=self.compiled,
            )
        with self.assertRaisesRegex(builder.BuilderError, "unexpected arguments"):
            builder.build_action(
                "padataset.cpu_ci",
                {"candidate_sha": "e" * 40, "gpu_count": "2"},
                compiled=self.compiled,
            )

    def test_candidate_sha_is_exact_lower_hex_40(self):
        for bad in [
            "A" * 40,
            "f" * 39,
            "f" * 41,
            "g" * 40,
            "f" * 20 + " " + "f" * 19,
        ]:
            with self.assertRaisesRegex(builder.BuilderError, "lowercase 40-hex SHA"):
                builder.build_action(
                    "workspace_control.control_validation",
                    {"candidate_sha": bad},
                    compiled=self.compiled,
                )

    def test_maintenance_class_must_exist_in_compiled_catalog(self):
        with self.assertRaisesRegex(builder.BuilderError, "unknown runner class"):
            builder.build_action(
                "maintenance.diagnose",
                {"runner_class_id": "research-super-gpu-unbounded"},
                compiled=self.compiled,
            )

    def test_reset_stale_requires_canonical_uuid(self):
        class_id = "research-model-dual-public-v1"
        receipt = "a7880e15-b29c-4b2b-bccd-3a34745f9ded"
        good = builder.build_action(
            "maintenance.reset_stale",
            {
                "runner_class_id": class_id,
                "quarantine_receipt_id": receipt,
            },
            compiled=self.compiled,
        )
        self.assertEqual(
            good["rendered_comment"],
            f"/workspace-ci-maintain reset-stale {class_id} {receipt}",
        )
        with self.assertRaisesRegex(builder.BuilderError, "invalid UUID"):
            builder.build_action(
                "maintenance.reset_stale",
                {
                    "runner_class_id": class_id,
                    "quarantine_receipt_id": "not-a-uuid",
                },
                compiled=self.compiled,
            )

    def test_whitespace_in_enum_or_class_identifier_is_rejected(self):
        with self.assertRaises(builder.BuilderError):
            builder.build_action(
                "maintenance.diagnose",
                {"runner_class_id": "workspace-control-control-small-v1 extra"},
                compiled=self.compiled,
            )

    def test_builder_cannot_accept_raw_command_override(self):
        with self.assertRaisesRegex(builder.BuilderError, "unexpected arguments"):
            builder.build_action(
                "workspace_control.control_validation",
                {
                    "candidate_sha": "f" * 40,
                    "command": "/workspace-control-validate anything",
                },
                compiled=self.compiled,
            )


if __name__ == "__main__":
    unittest.main()
