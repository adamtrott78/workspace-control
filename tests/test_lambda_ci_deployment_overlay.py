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

overlay_spec = importlib.util.spec_from_file_location(
    "lambda_ci_deployment_overlay",
    ROOT / "scripts" / "lambda_ci_deployment_overlay.py",
)
overlay_model = importlib.util.module_from_spec(overlay_spec)
assert overlay_spec.loader is not None
sys.modules["lambda_ci_deployment_overlay"] = overlay_model
overlay_spec.loader.exec_module(overlay_model)


class DeploymentOverlayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compiled = compiler.compile_policy(ROOT)
        cls.schema = overlay_model.load_schema(ROOT)

    def overlay(self):
        return overlay_model.load_overlay(ROOT)

    def verify(self, overlay, *, allow_zero=True):
        return overlay_model.verify_overlay(
            overlay,
            self.compiled,
            schema=self.schema,
            allow_template_zero_digest=allow_zero,
        )

    def test_initial_template_has_zero_implicit_activation(self):
        result = self.verify(self.overlay())
        self.assertEqual(result["installed_classes"], [])
        self.assertEqual(result["active_classes"], [])
        self.assertEqual(result["enabled_routes"], [])
        self.assertIn("research-model-dual-public-v1", result["contained_classes"])
        self.assertTrue(result["legacy_research_gpu_quarantine_preserved"])
        self.assertTrue(result["legacy_research_gpu_retry_invalidated_preserved"])

    def test_generation_binding_changes_only_digest(self):
        overlay = self.overlay()
        before = copy.deepcopy(overlay)
        bound = overlay_model.bind_generation(
            overlay,
            generation_sha256=self.compiled["catalog_generation_sha256"],
        )
        self.assertEqual(
            bound["catalog_generation_sha256"],
            self.compiled["catalog_generation_sha256"],
        )
        self.assertEqual(bound["classes"], before["classes"])
        self.assertEqual(bound["routes"], before["routes"])
        self.assertEqual(bound["legacy"], before["legacy"])
        result = self.verify(bound, allow_zero=False)
        self.assertEqual(result["active_classes"], [])
        self.assertEqual(result["enabled_routes"], [])

    def test_wrong_generation_digest_fails(self):
        overlay = self.overlay()
        overlay["catalog_generation_sha256"] = "f" * 64
        with self.assertRaisesRegex(
            overlay_model.OverlayError,
            "catalog generation mismatch",
        ):
            self.verify(overlay, allow_zero=False)

    def test_overlay_schema_rejects_unknown_fields(self):
        overlay = self.overlay()
        overlay["invented_activation_switch"] = True
        with self.assertRaisesRegex(
            overlay_model.OverlayError,
            "unexpected keys",
        ):
            self.verify(overlay)

    def test_enabled_route_requires_installed_active_clear_class(self):
        overlay = self.overlay()
        route = "workspace-control:control-validation"
        overlay["routes"][route]["admission_state"] = "ENABLED"
        with self.assertRaisesRegex(
            overlay_model.OverlayError,
            "class is not installed",
        ):
            self.verify(overlay)

        class_id = "workspace-control-control-small-v1"
        overlay["classes"][class_id]["install_state"] = "INSTALLED"
        with self.assertRaisesRegex(
            overlay_model.OverlayError,
            "controller is not active",
        ):
            self.verify(overlay)

        overlay["classes"][class_id]["controller_state"] = "ACTIVE"
        result = self.verify(overlay)
        self.assertEqual(result["active_classes"], [class_id])
        self.assertEqual(result["enabled_routes"], [route])

    def test_contained_class_cannot_be_active(self):
        overlay = self.overlay()
        class_id = "research-model-dual-public-v1"
        overlay["classes"][class_id]["install_state"] = "INSTALLED"
        overlay["classes"][class_id]["controller_state"] = "ACTIVE"
        with self.assertRaisesRegex(
            overlay_model.OverlayError,
            "contained/quarantined class cannot be ACTIVE",
        ):
            self.verify(overlay)

    def test_route_cannot_enable_while_class_is_contained(self):
        overlay = self.overlay()
        class_id = "research-model-dual-public-v1"
        route = "research-engine:model-eval-local-extract-wave7a3"
        overlay["classes"][class_id]["install_state"] = "INSTALLED"
        overlay["routes"][route]["admission_state"] = "ENABLED"
        with self.assertRaises(overlay_model.OverlayError):
            self.verify(overlay)

    def test_exact_provenance_cpu_route_does_not_bypass_legacy_gpu_containment(self):
        overlay = self.overlay()
        class_id = "research-cpu-public-v1"
        route = "research-engine:cpu-validation-exact-provenance"
        overlay["classes"][class_id]["install_state"] = "INSTALLED"
        overlay["classes"][class_id]["controller_state"] = "ACTIVE"
        overlay["routes"][route]["admission_state"] = "ENABLED"
        with self.assertRaisesRegex(
            overlay_model.OverlayError,
            "bypassed legacy GPU containment",
        ):
            self.verify(overlay)

    def test_exact_provenance_route_can_only_enable_after_legacy_gpu_retirement(self):
        overlay = self.overlay()
        class_id = "research-cpu-public-v1"
        route = "research-engine:cpu-validation-exact-provenance"
        overlay["legacy"]["controllers"]["research-engine-gpu"] = "RETIRED"
        overlay["classes"][class_id]["install_state"] = "INSTALLED"
        overlay["classes"][class_id]["controller_state"] = "ACTIVE"
        overlay["routes"][route]["admission_state"] = "ENABLED"
        result = self.verify(overlay)
        self.assertIn(route, result["enabled_routes"])

    def test_missing_legacy_quarantine_receipt_fails(self):
        overlay = self.overlay()
        overlay["legacy"]["quarantine_receipts"] = []
        with self.assertRaisesRegex(
            overlay_model.OverlayError,
            "quarantine receipt",
        ):
            self.verify(overlay)

    def test_retry_receipt_must_remain_invalidated(self):
        overlay = self.overlay()
        overlay["legacy"]["retry_receipts"] = [
            "research-engine-gpu:3eeffae8-2bd0-4344-b89f-02afbf1a445b:READY_FOR_SINGLE_RETRY"
        ]
        with self.assertRaisesRegex(
            overlay_model.OverlayError,
            "retry-invalidated",
        ):
            self.verify(overlay)

    def test_overlay_class_and_route_sets_must_exactly_match_compiled_policy(self):
        overlay = self.overlay()
        del overlay["classes"]["padataset-cpu-public-v1"]
        with self.assertRaisesRegex(
            overlay_model.OverlayError,
            "class set differs",
        ):
            self.verify(overlay)

        overlay = self.overlay()
        del overlay["routes"]["padataset:cpu-ci"]
        with self.assertRaisesRegex(
            overlay_model.OverlayError,
            "route set differs",
        ):
            self.verify(overlay)


if __name__ == "__main__":
    unittest.main()
