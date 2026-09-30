#!/usr/bin/env python3
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
FIXTURES = ROOT / "tests" / "fixtures"

class SchemaScaffoldingTests(unittest.TestCase):
    def load_json(self, path):
        with Path(path).open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def test_v1_schema_copy_is_byte_identical_to_legacy_schema(self):
        self.assertEqual(
            (SCHEMAS / "task_capsule.schema.json").read_bytes(),
            (SCHEMAS / "task_capsule.v1.schema.json").read_bytes(),
        )

    def test_schema_versions_are_explicit(self):
        self.assertEqual(self.load_json(SCHEMAS / "task_capsule.v1.schema.json")["properties"]["schema_version"]["const"], 1)
        self.assertEqual(self.load_json(SCHEMAS / "task_capsule.v2.schema.json")["properties"]["schema_version"]["const"], 2)
        self.assertEqual(self.load_json(SCHEMAS / "workflow_descriptor.v1.schema.json")["properties"]["schema_version"]["const"], 1)

    def test_fixture_json_parses(self):
        expected = {
            "task_capsule_v1_minimal.json": 1,
            "task_capsule_v2_remote.json": 2,
            "task_capsule_v2_local.json": 2,
            "task_capsule_v2_composed.json": 2,
            "workflow_descriptor_v1.json": 1,
        }
        for name, version in expected.items():
            with self.subTest(name=name):
                self.assertEqual(self.load_json(FIXTURES / name)["schema_version"], version)

    def test_v2_fixtures_cover_topologies(self):
        names = ["task_capsule_v2_remote.json","task_capsule_v2_local.json","task_capsule_v2_composed.json"]
        self.assertEqual(
            {self.load_json(FIXTURES / name)["execution_topology"] for name in names},
            {"remote_only","local","composed"},
        )

    def test_workflow_fixture_contains_no_live_task_state(self):
        workflow = self.load_json(FIXTURES / "workflow_descriptor_v1.json")
        forbidden = {"current_stage","remaining_work","next_safe_action","checkpoint_sha","last_executor"}
        self.assertTrue(forbidden.isdisjoint(workflow))

if __name__ == "__main__":
    unittest.main()
