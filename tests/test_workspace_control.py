#!/usr/bin/env python3
"""workspace-control compatibility and v2 validation/render tests."""

import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
FIXTURES = ROOT / "tests" / "fixtures"
SCRIPT = ROOT / "scripts" / "workspace_control.py"

spec = importlib.util.spec_from_file_location("workspace_control", SCRIPT)
workspace_control = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workspace_control)

REPOS = json.loads((ROOT / "repos.json").read_text())["repositories"]


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def git_blob_sha(data):
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


class SchemaScaffoldingTests(unittest.TestCase):
    def test_v1_schema_frozen_blob_identity(self):
        data = (SCHEMAS / "task_capsule.v1.schema.json").read_bytes()
        self.assertEqual(
            git_blob_sha(data),
            "40fa76125f61c0ad8e11a10a45347dbb36c63a84",
        )

    def test_dispatch_schema_references_v1_and_v2(self):
        dispatch = load_json(SCHEMAS / "task_capsule.schema.json")
        refs = [entry["$ref"] for entry in dispatch["oneOf"]]
        self.assertEqual(
            refs,
            [
                "task_capsule.v1.schema.json",
                "task_capsule.v2.schema.json",
            ],
        )

    def test_schema_versions_are_explicit(self):
        self.assertEqual(
            load_json(SCHEMAS / "task_capsule.v1.schema.json")
            ["properties"]["schema_version"]["const"],
            1,
        )
        self.assertEqual(
            load_json(SCHEMAS / "task_capsule.v2.schema.json")
            ["properties"]["schema_version"]["const"],
            2,
        )


class TaskValidationTests(unittest.TestCase):
    def validate_fixture(self, name):
        data = load_json(FIXTURES / name)
        virtual_path = Path(f"{data['task_id']}.json")
        return workspace_control.validate_task_capsule_data(
            data,
            virtual_path,
            REPOS,
        )

    def test_v1_fixture_validates(self):
        self.assertEqual(
            self.validate_fixture("task_capsule_v1_minimal.json"),
            [],
        )

    def test_v2_remote_fixture_validates(self):
        self.assertEqual(
            self.validate_fixture("task_capsule_v2_remote.json"),
            [],
        )

    def test_v2_local_fixture_validates(self):
        self.assertEqual(
            self.validate_fixture("task_capsule_v2_local.json"),
            [],
        )

    def test_v2_composed_fixture_validates(self):
        self.assertEqual(
            self.validate_fixture("task_capsule_v2_composed.json"),
            [],
        )

    def test_unknown_schema_version_fails_explicitly(self):
        data = load_json(FIXTURES / "task_capsule_v2_remote.json")
        data["schema_version"] = 99
        errors = workspace_control.validate_task_capsule_data(
            data,
            Path(f"{data['task_id']}.json"),
            REPOS,
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("unsupported value 99", errors[0])

    def test_remote_only_rejects_local_state(self):
        data = load_json(FIXTURES / "task_capsule_v2_remote.json")
        data["repositories"][0]["local"] = {
            "checkout_path": "/tmp/example",
            "branch": "example",
            "head_sha": "0" * 40,
            "clean": True,
        }
        errors = workspace_control.validate_task_capsule_data(
            data,
            Path(f"{data['task_id']}.json"),
            REPOS,
        )
        self.assertIn(
            "execution_topology: remote_only must not require "
            "local repository state",
            errors,
        )


class TaskRenderTests(unittest.TestCase):
    def test_render_is_deterministic_and_derived(self):
        path = FIXTURES / "task_capsule_v2_remote.json"
        data = load_json(path)
        first = workspace_control.render_task_handoff(
            path,
            data,
            ROOT,
        )
        second = workspace_control.render_task_handoff(
            path,
            data,
            ROOT,
        )
        self.assertEqual(first, second)
        self.assertTrue(
            first.startswith(
                workspace_control.DERIVED_HANDOFF_MARKER
            )
        )
        self.assertIn(data["next_safe_action"], first)
        self.assertIn(
            "tests/fixtures/task_capsule_v2_remote.json",
            first,
        )


if __name__ == "__main__":
    unittest.main()
