import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "validation_plan.py"
SPEC = importlib.util.spec_from_file_location("validation_plan", SCRIPT)
validation_plan = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validation_plan)


PROFILE = {
    "schema_version": 1,
    "repository": "example",
    "default_tier": "FULL_INTEGRATION",
    "force_full_tier": "FULL_INTEGRATION",
    "tier_checks": {
        "FAST_STATIC": ["structural"],
        "TARGETED_PR": ["targeted"],
        "FULL_INTEGRATION": ["full"],
        "CANONICAL_REGRESSION": ["regression"],
    },
    "rules": [
        {
            "id": "docs",
            "patterns": ["docs/**"],
            "tier": "FAST_STATIC",
            "checks": ["docs-check"],
        },
        {
            "id": "tests",
            "patterns": ["tests/**"],
            "tier": "TARGETED_PR",
            "checks": ["unit-tests"],
        },
        {
            "id": "schemas",
            "patterns": ["schemas/**"],
            "tier": "FULL_INTEGRATION",
            "checks": ["schema-tests"],
        },
    ],
}


class ValidationPlanTests(unittest.TestCase):
    def test_docs_only_selects_fast_static(self):
        plan = validation_plan.build_plan(
            PROFILE,
            ["docs/readme.md", "docs/design/plan.md"],
        )
        self.assertEqual(plan["selected_tier"], "FAST_STATIC")
        self.assertEqual(
            plan["required_checks"],
            ["docs-check", "structural"],
        )

    def test_targeted_change_selects_targeted_pr(self):
        plan = validation_plan.build_plan(
            PROFILE,
            ["tests/test_one.py"],
        )
        self.assertEqual(plan["selected_tier"], "TARGETED_PR")
        self.assertIn("unit-tests", plan["required_checks"])
        self.assertIn("targeted", plan["required_checks"])

    def test_mixed_change_escalates_to_highest_tier(self):
        plan = validation_plan.build_plan(
            PROFILE,
            ["docs/readme.md", "schemas/task.json"],
        )
        self.assertEqual(plan["selected_tier"], "FULL_INTEGRATION")
        self.assertTrue(
            any(
                "mixed-change maximum FULL_INTEGRATION" in reason
                for reason in plan["escalation_reasons"]
            )
        )

    def test_unknown_path_fails_closed_to_default(self):
        plan = validation_plan.build_plan(
            PROFILE,
            ["unknown/new_surface.bin"],
        )
        self.assertEqual(plan["selected_tier"], "FULL_INTEGRATION")
        self.assertTrue(
            any(
                "no lower-risk rule matched" in reason
                for reason in plan["escalation_reasons"]
            )
        )

    def test_force_full_overrides_fast_rule(self):
        plan = validation_plan.build_plan(
            PROFILE,
            ["docs/readme.md"],
            force_full=True,
        )
        self.assertEqual(plan["selected_tier"], "FULL_INTEGRATION")
        self.assertIn("full", plan["required_checks"])

    def test_paths_are_deduplicated_and_normalized(self):
        plan = validation_plan.build_plan(
            PROFILE,
            ["./docs/readme.md", "docs/readme.md"],
        )
        self.assertEqual(plan["changed_paths"], ["docs/readme.md"])

    def test_invalid_force_full_floor_is_rejected(self):
        invalid = dict(PROFILE)
        invalid["force_full_tier"] = "TARGETED_PR"
        with self.assertRaises(validation_plan.ValidationPlanError):
            validation_plan.validate_profile(invalid)

    def test_profile_load_rejects_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profile.json"
            path.write_text("{bad")
            with self.assertRaises(validation_plan.ValidationPlanError):
                validation_plan.load_profile(path)


if __name__ == "__main__":
    unittest.main()
