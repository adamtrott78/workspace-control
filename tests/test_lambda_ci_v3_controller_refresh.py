import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


refresh = load(
    "lambda_ci_v3_controller_refresh",
    ROOT / "scripts" / "lambda_ci_v3_controller_refresh.py",
)


class V3ControllerRefreshTests(unittest.TestCase):
    def manifest(self, controller_sha="old", other_sha="same"):
        return {
            "schema_version": 1,
            "mode": "V3_SUBSTRATE_INSTALL_INACTIVE",
            "source_head": "a" * 40,
            "catalog_generation_sha256": "b" * 64,
            "root_policy_sha256": "c" * 64,
            "runner_class_count": 9,
            "controller_state": "INACTIVE",
            "route_state": "DISABLED",
            "entries": [
                {
                    "destination": str(refresh.CONTROLLER_BINARY),
                    "sha256": controller_sha,
                    "mode": "0755",
                },
                {
                    "destination": "/etc/workspace-ci/v3/root-policy.json",
                    "sha256": other_sha,
                    "mode": "0644",
                },
            ],
        }

    def test_controller_only_manifest_change_is_allowed(self):
        base = self.manifest(controller_sha="old")
        candidate = self.manifest(controller_sha="new")
        candidate["source_head"] = "d" * 40
        refresh.compare_manifests_for_controller_only_refresh(base, candidate)

    def test_non_controller_manifest_change_is_rejected(self):
        base = self.manifest(controller_sha="old", other_sha="same")
        candidate = self.manifest(controller_sha="new", other_sha="drift")
        with self.assertRaises(refresh.ControllerRefreshError):
            refresh.compare_manifests_for_controller_only_refresh(base, candidate)

    def test_policy_generation_change_is_rejected(self):
        base = self.manifest()
        candidate = self.manifest(controller_sha="new")
        candidate["root_policy_sha256"] = "d" * 64
        with self.assertRaises(refresh.ControllerRefreshError):
            refresh.compare_manifests_for_controller_only_refresh(base, candidate)

    def test_prior_rolled_back_canary_history_is_accepted(self):
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            tx = root / "one"
            tx.mkdir()
            (tx / "transaction.json").write_text(
                json.dumps(
                    {
                        "mode": "V3_ONE_CLASS_CANARY_GENERATION_EXCLUSION",
                        "phase": "ROLLED_BACK_LEGACY_RESTORED",
                    }
                )
            )
            receipts = refresh.assert_migration_history_rolled_back(root)
            self.assertEqual(receipts, [tx / "transaction.json"])

    def test_nonterminal_canary_history_blocks_refresh(self):
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            tx = root / "one"
            tx.mkdir()
            (tx / "transaction.json").write_text(
                json.dumps(
                    {
                        "mode": "V3_ONE_CLASS_CANARY_GENERATION_EXCLUSION",
                        "phase": "CANARY_ACTIVE",
                    }
                )
            )
            with self.assertRaises(refresh.ControllerRefreshError):
                refresh.assert_migration_history_rolled_back(root)


if __name__ == "__main__":
    unittest.main()
