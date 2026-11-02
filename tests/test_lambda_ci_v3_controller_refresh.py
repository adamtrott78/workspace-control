import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

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

    def test_authorized_effective_non_controller_override_is_allowed(self):
        base = self.manifest(controller_sha="old", other_sha="base")
        candidate = self.manifest(controller_sha="new", other_sha="effective")
        effective = {
            entry["destination"]: entry["sha256"]
            for entry in base["entries"]
        }
        effective["/etc/workspace-ci/v3/root-policy.json"] = "effective"
        refresh.compare_manifests_for_controller_only_refresh(
            base,
            candidate,
            effective_sha256=effective,
        )

    def test_candidate_non_controller_drift_beyond_effective_state_is_rejected(self):
        base = self.manifest(controller_sha="old", other_sha="base")
        candidate = self.manifest(controller_sha="new", other_sha="candidate-drift")
        effective = {
            entry["destination"]: entry["sha256"]
            for entry in base["entries"]
        }
        effective["/etc/workspace-ci/v3/root-policy.json"] = "effective"
        with self.assertRaises(refresh.ControllerRefreshError):
            refresh.compare_manifests_for_controller_only_refresh(
                base,
                candidate,
                effective_sha256=effective,
            )

    def test_effective_digest_set_must_cover_exact_managed_destinations(self):
        base = self.manifest(controller_sha="old", other_sha="same")
        candidate = self.manifest(controller_sha="new", other_sha="same")
        with self.assertRaisesRegex(
            refresh.ControllerRefreshError,
            "effective installed digest set",
        ):
            refresh.compare_manifests_for_controller_only_refresh(
                base,
                candidate,
                effective_sha256={
                    str(refresh.CONTROLLER_BINARY): "old",
                },
            )

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

    def test_base_manifest_delegates_effective_generation_to_reconciler(self):
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            manifest_path = root / "install-manifest.json"
            manifest = self.manifest(controller_sha="base-controller")
            manifest["entries"].append(
                {
                    "destination": "/opt/workspace-ci/v3/reconciler/lambda_ci_v3_reconciler.py",
                    "sha256": "base-reconciler",
                    "mode": "0755",
                }
            )
            manifest_path.write_text(json.dumps(manifest))
            with (
                mock.patch.object(refresh, "BASE_MANIFEST", manifest_path),
                mock.patch.object(refresh.reconciler, "verify_installed") as verify,
            ):
                loaded, _, controller = refresh._base_manifest("a" * 40)
            verify.assert_called_once_with(manifest_path)
            self.assertEqual(controller["sha256"], "base-controller")
            self.assertEqual(loaded["source_head"], "a" * 40)

    def test_base_manifest_fails_closed_when_shared_verifier_rejects(self):
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            manifest_path = root / "install-manifest.json"
            manifest_path.write_text(json.dumps(self.manifest()))
            with (
                mock.patch.object(refresh, "BASE_MANIFEST", manifest_path),
                mock.patch.object(
                    refresh.reconciler,
                    "verify_installed",
                    side_effect=refresh.reconciler.ReconcileError(
                        "active reconciler override binding mismatch"
                    ),
                ),
            ):
                with self.assertRaisesRegex(
                    refresh.ControllerRefreshError,
                    "effective installed generation invalid",
                ):
                    refresh._base_manifest("a" * 40)


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

    def test_retry_history_matches_rolled_back_transaction_and_marker(self):
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            migrations = root / "migration"
            authorities = root / "authority"
            tx = migrations / "one"
            tx.mkdir(parents=True)
            authorities.mkdir()
            auth_id = "11111111-1111-4111-8111-111111111111"
            target = "workspace-control-control-small-v1"
            (tx / "transaction.json").write_text(
                json.dumps(
                    {
                        "mode": "V3_ONE_CLASS_CANARY_GENERATION_EXCLUSION",
                        "phase": "ROLLED_BACK_LEGACY_RESTORED",
                        "target_runner_class_id": target,
                        "authorization_id": auth_id,
                    }
                )
            )
            (authorities / f"{auth_id}.json").write_text(
                json.dumps(
                    {
                        "authorization_id": auth_id,
                        "target_runner_class_id": target,
                    }
                )
            )
            result = refresh.assert_canary_retry_history(
                target,
                migration_root=migrations,
                authority_root=authorities,
            )
            self.assertEqual(result["rolled_back_transactions"], 1)
            self.assertEqual(result["matched_authority_markers"], 1)

    def test_retry_history_rejects_unmatched_consumed_authority(self):
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            migrations = root / "migration"
            authorities = root / "authority"
            migrations.mkdir()
            authorities.mkdir()
            auth_id = "22222222-2222-4222-8222-222222222222"
            target = "workspace-control-control-small-v1"
            (authorities / f"{auth_id}.json").write_text(
                json.dumps(
                    {
                        "authorization_id": auth_id,
                        "target_runner_class_id": target,
                    }
                )
            )
            with self.assertRaises(refresh.ControllerRefreshError):
                refresh.assert_canary_retry_history(
                    target,
                    migration_root=migrations,
                    authority_root=authorities,
                )

    def test_retry_history_rejects_nonterminal_target_transaction(self):
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            migrations = root / "migration"
            authorities = root / "authority"
            tx = migrations / "one"
            tx.mkdir(parents=True)
            authorities.mkdir()
            auth_id = "33333333-3333-4333-8333-333333333333"
            target = "workspace-control-control-small-v1"
            (tx / "transaction.json").write_text(
                json.dumps(
                    {
                        "mode": "V3_ONE_CLASS_CANARY_GENERATION_EXCLUSION",
                        "phase": "CANARY_ACTIVE",
                        "target_runner_class_id": target,
                        "authorization_id": auth_id,
                    }
                )
            )
            (authorities / f"{auth_id}.json").write_text(
                json.dumps(
                    {
                        "authorization_id": auth_id,
                        "target_runner_class_id": target,
                    }
                )
            )
            with self.assertRaises(refresh.ControllerRefreshError):
                refresh.assert_canary_retry_history(
                    target,
                    migration_root=migrations,
                    authority_root=authorities,
                )


if __name__ == "__main__":
    unittest.main()
