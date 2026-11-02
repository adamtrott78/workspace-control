"""Open-world unseen-extension proof for the semantic execution core."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CORE_PATH = ROOT / "architecture/workspace-semantic-execution-core.v0.1.json"
EXT_PATH = ROOT / "architecture/workspace-semantic-execution-extension-media-localization.v0.1.json"
VALIDATOR_PATH = ROOT / "benchmarks/workspace-semantic-execution/extension_contract_v1.py"

spec = importlib.util.spec_from_file_location("extension_contract_v1", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(validator)

CORE = json.loads(CORE_PATH.read_text())
EXT = json.loads(EXT_PATH.read_text())


class UnseenExtensionTests(unittest.TestCase):
    def test_extension_is_unseen_to_core_examples(self):
        self.assertNotIn(EXT["extension_id"], CORE["example_extensions"])

    def test_extension_validates_without_core_change(self):
        result = validator.validate_extension(CORE, EXT)
        self.assertTrue(result["valid"])
        self.assertFalse(result["core_kernel_change_required"])
        self.assertFalse(result["closed_domain_enum_change_required"])
        self.assertFalse(result["authority_widened"])
        self.assertEqual(
            result["unknown_extension_behavior"],
            "UNSUPPORTED_EXTENSION_FAIL_CLOSED",
        )

    def test_domain_types_and_relations_are_namespaced(self):
        prefix = EXT["extension_id"] + ":"
        self.assertTrue(all(x["name"].startswith(prefix) for x in EXT["type_definitions"]))
        self.assertTrue(all(x["name"].startswith(prefix) for x in EXT["relation_definitions"]))

    def test_workflow_uses_all_generic_projection_fields(self):
        required = set(CORE["workflow_projection_contract"]["required_generic_fields"])
        self.assertTrue(required.issubset(EXT["workflow_projection"]))

    def test_source_truth_is_not_migrated_into_core(self):
        boundary = EXT["source_of_truth_boundary"]
        self.assertEqual(boundary["projection_authority"], "NON_AUTHORITATIVE_REBUILDABLE")
        self.assertFalse(EXT["migration_policy"]["core_kernel_change_allowed"])

    def test_authority_widening_mutation_fails_closed(self):
        bad = json.loads(json.dumps(EXT))
        bad["authority_effects"]["creates_permission"] = True
        with self.assertRaises(validator.ExtensionContractError):
            validator.validate_extension(CORE, bad)

    def test_missing_generic_field_fails_closed(self):
        bad = json.loads(json.dumps(EXT))
        del bad["workflow_projection"]["validators"]
        with self.assertRaises(validator.ExtensionContractError):
            validator.validate_extension(CORE, bad)

    def test_existing_core_file_does_not_need_media_localization_branch(self):
        serialized = json.dumps(CORE, sort_keys=True)
        self.assertNotIn("media_localization", serialized)


if __name__ == "__main__":
    unittest.main()
