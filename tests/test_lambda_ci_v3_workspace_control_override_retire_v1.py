import importlib.util
import json
import pathlib
import tempfile
import unittest

MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "lambda_ci_v3_workspace_control_override_retire_v1.py"
SPEC = importlib.util.spec_from_file_location("override_retire", MODULE_PATH)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)


class OverrideRetireTests(unittest.TestCase):
    def test_stale_dropin_bytes_are_exact(self):
        self.assertEqual(
            mod.STALE_DROPIN_BYTES,
            (
                "[Service]\n"
                "ExecStart=\n"
                "ExecStart=/opt/workspace-ci/v3/controller-overrides/"
                "workspace-control-control-small-v1/lambda-ci-controller-v3\n"
            ).encode(),
        )

    def test_nonterminal_current_policy_records_only(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            rows = {
                "scheduler-1.json": {
                    "controller_policy_sha256": mod.EXPECTED_POLICY_SHA256,
                    "state": "COMPLETED",
                },
                "scheduler-2.json": {
                    "controller_policy_sha256": mod.EXPECTED_POLICY_SHA256,
                    "state": "ACQUIRED",
                },
                "scheduler-3.json": {
                    "controller_policy_sha256": "0" * 64,
                    "state": "RUNNING",
                },
            }
            for name, value in rows.items():
                (root / name).write_text(json.dumps(value))
            found = mod.current_policy_nonterminal_records(root)
            self.assertEqual(found, [root / "scheduler-2.json"])

    def test_approved_shared_controller_binding_is_frozen(self):
        self.assertEqual(
            mod.SHARED_SOURCE_HEAD,
            "e0911a56a8e0088d7b90728b7d603dc1f73f824a",
        )
        self.assertEqual(
            mod.SHARED_SHA256,
            "644d34b02e2166a1c24ffba48e71302f8519a807c872b45a367285146e407918",
        )
        self.assertEqual(
            mod.STALE_OVERRIDE_SHA256,
            "9db8161340baacd7d7aad48ad47e013651158748bfd61b13c41ab29539a35af3",
        )

    def test_target_scope_is_workspace_control_only(self):
        self.assertEqual(mod.TARGET_CLASS, "workspace-control-control-small-v1")
        self.assertIn("workspace-control-control-small-v1", str(mod.STALE_OVERRIDE_BINARY))
        self.assertIn("workspace-control-control-small-v1", str(mod.STALE_DROPIN))


if __name__ == "__main__":
    unittest.main()
